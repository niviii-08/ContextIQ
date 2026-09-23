"""
Recommendation generator ("One More Thing").

`recommend_for_context(user_id, context, ...)` turns mined association
rules into ranked, de-duplicated, quality-filtered task recommendations
for a specific user's current visit to a context. Nothing here is
hardcoded: recommendations are entirely derived from the association
rules passed in (which themselves come from mined transaction data).

Quality controls implemented
-----------------------------
- confidence / support / lift thresholds (re-applied defensively, even
  though `mine_association_rules` already filters — this function may
  receive rules from any source).
- de-duplication of recommended tasks (a task is recommended at most
  once, using its highest-lift supporting rule).
- exclusion of already-completed tasks for this visit.
- cooldown: a task dismissed or already recommended recently for this
  user is suppressed until the cooldown window elapses.
- dismissal support: a simple in-memory dismissal store the API layer
  can call into; a real deployment would back this with a database.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.schemas.associations import AssociationRule
from app.schemas.recommendations import TaskRecommendation, PrioritizedRecommendation


@dataclass
class RecommendationQualityConfig:
    min_confidence: float = 0.5
    min_support: float = 0.05
    min_lift: float = 1.0
    cooldown_seconds: float = 3600.0


class DismissalStore:
    """In-memory store tracking per-user task dismissals/recent recommendations
    for cooldown purposes. Swap for a real persistence layer in production —
    the interface (record_dismissal / record_shown / is_suppressed) is what
    matters for integration.
    """

    def __init__(self) -> None:
        self._dismissed_until: dict[tuple[str, str, str], float] = {}

    def _key(self, user_id: str, context: str, task: str) -> tuple[str, str, str]:
        return (user_id, context, task)

    def record_dismissal(
        self, user_id: str, context: str, task: str, cooldown_seconds: float, now: float | None = None
    ) -> None:
        now = now if now is not None else time.time()
        self._dismissed_until[self._key(user_id, context, task)] = now + cooldown_seconds

    def record_shown(
        self, user_id: str, context: str, task: str, cooldown_seconds: float, now: float | None = None
    ) -> None:
        # Showing a recommendation also starts a short cooldown to avoid spamming
        # the same suggestion every single request.
        now = now if now is not None else time.time()
        key = self._key(user_id, context, task)
        existing = self._dismissed_until.get(key, 0.0)
        self._dismissed_until[key] = max(existing, now + cooldown_seconds)

    def is_suppressed(self, user_id: str, context: str, task: str, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        until = self._dismissed_until.get(self._key(user_id, context, task))
        return until is not None and now < until

    def clear(self) -> None:
        self._dismissed_until.clear()


def recommend_for_context(
    user_id: str,
    context: str,
    rules: list[AssociationRule],
    completed_tasks: list[str] | None = None,
    config: RecommendationQualityConfig | None = None,
    dismissal_store: DismissalStore | None = None,
    max_recommendations: int = 5,
) -> list[TaskRecommendation]:
    """Generate ranked task recommendations for a user's current context visit.

    Parameters
    ----------
    user_id, context : identify the current visit.
    rules : association rules already mined for this `context`
        (see ml.associations.mining.mine_association_rules).
    completed_tasks : tasks already done in this visit; excluded from output.
    config : thresholds for confidence/support/lift and cooldown window.
    dismissal_store : optional store used to suppress recently
        dismissed/shown recommendations (cooldown + dismissal support).
    max_recommendations : cap on the number of recommendations returned.
    """
    config = config or RecommendationQualityConfig()
    completed = set(completed_tasks or [])

    # 1. Filter rules relevant to this context and whose antecedents are
    #    already satisfied by what the user has completed so far (or, if
    #    nothing has been completed yet, consider rules with empty/general
    #    antecedents implicitly satisfied by simply being in this context).
    candidate_rules = [
        r
        for r in rules
        if r.context == context
        and r.confidence >= config.min_confidence
        and r.support >= config.min_support
        and r.lift >= config.min_lift
    ]

    # Only surface rules whose antecedent tasks have all been completed
    # (or the antecedent is empty), so we recommend the *next* logical task.
    applicable_rules = [
        r for r in candidate_rules if set(r.antecedents).issubset(completed) or not r.antecedents
    ]

    # 2. Collect best (highest lift, then weighted_confidence if available, else confidence) rule per consequent task.
    def _rank_key(rule: AssociationRule) -> tuple:
        confidence_for_rank = rule.weighted_confidence if rule.weighted_confidence is not None else rule.confidence
        return (rule.lift, confidence_for_rank)

    best_rule_per_task: dict[str, AssociationRule] = {}
    for r in applicable_rules:
        for task in r.consequents:
            if task in completed:
                continue
            existing = best_rule_per_task.get(task)
            if existing is None or _rank_key(r) > _rank_key(existing):
                best_rule_per_task[task] = r

    # 3. Apply cooldown / dismissal suppression, then rank by weighted_confidence (fallback to confidence).
    ranked_pairs: list[tuple[str, AssociationRule]] = []
    for task, rule in best_rule_per_task.items():
        if dismissal_store is not None and dismissal_store.is_suppressed(user_id, context, task):
            continue
        ranked_pairs.append((task, rule))

    def _sort_key(pair: tuple[str, AssociationRule]) -> tuple:
        _, rule = pair
        confidence_for_sort = rule.weighted_confidence if rule.weighted_confidence is not None else rule.confidence
        return (confidence_for_sort, rule.lift, rule.support)

    ranked_pairs.sort(key=_sort_key, reverse=True)
    ranked_pairs = ranked_pairs[:max_recommendations]

    # 4. Build final recommendations from ranked rules.
    recommendations: list[TaskRecommendation] = []
    for task, rule in ranked_pairs:
        reason = (
            f"Frequently completed together with {', '.join(rule.antecedents) or 'this context'} "
            f"during {context} visits."
            if rule.antecedents
            else f"Frequently completed during {context} visits."
        )
        recommendations.append(
            TaskRecommendation(
                task=task,
                confidence=rule.confidence,
                support=rule.support,
                lift=rule.lift,
                reason=reason,
            )
        )

    # 5. Record as "shown" for cooldown bookkeeping.
    if dismissal_store is not None:
        for rec in recommendations:
            dismissal_store.record_shown(user_id, context, rec.task, config.cooldown_seconds)

    return recommendations


# ---------------------------------------------------------------------------
# Combined intelligence interface: association confidence + forgetting risk
# ---------------------------------------------------------------------------

class ForgettingRiskProvider:
    """Protocol-like base class for a pluggable forgetting-risk model.

    This module does NOT implement the forgetting model itself — it only
    defines the interface a real forgetting model must satisfy, plus a
    mock implementation (`MockForgettingRiskProvider`) for testing the
    combined-intelligence pipeline end-to-end without that dependency.
    """

    def get_forgetting_probability(self, user_id: str, task: str) -> float | None:
        raise NotImplementedError


class MockForgettingRiskProvider(ForgettingRiskProvider):
    """Deterministic mock used for tests and local development. Returns a
    stable pseudo-probability derived from the task name so that outputs
    are reproducible without needing the real forgetting model."""

    def __init__(self, fixed_values: dict[str, float] | None = None, default: float = 0.5) -> None:
        self._fixed_values = fixed_values or {}
        self._default = default

    def get_forgetting_probability(self, user_id: str, task: str) -> float | None:
        if task in self._fixed_values:
            return self._fixed_values[task]
        # Deterministic pseudo-random-ish value in [0.3, 0.9] based on task name hash.
        h = abs(hash((user_id, task))) % 61
        return round(0.3 + (h / 60.0) * 0.6, 3)


def prioritize_recommendations(
    user_id: str,
    recommendations: list[TaskRecommendation],
    forgetting_provider: ForgettingRiskProvider | None = None,
    association_weight: float = 0.5,
    forgetting_weight: float = 0.5,
) -> list[PrioritizedRecommendation]:
    """Combine association confidence with (optional) forgetting-risk
    probability into a single priority score, ranking recommendations.

    priority_score = association_weight * confidence
                    + forgetting_weight * forgetting_probability

    If no forgetting_provider is supplied, forgetting_probability is
    treated as None and the priority score falls back to confidence
    alone (renormalized), so the pipeline works standalone.
    """
    prioritized: list[PrioritizedRecommendation] = []

    for rec in recommendations:
        forgetting_prob = None
        if forgetting_provider is not None:
            forgetting_prob = forgetting_provider.get_forgetting_probability(user_id, rec.task)

        if forgetting_prob is not None:
            score = association_weight * rec.confidence + forgetting_weight * forgetting_prob
            reason = f"{rec.reason} Combined with forgetting risk of {forgetting_prob:.2f}."
        else:
            score = rec.confidence
            reason = rec.reason

        prioritized.append(
            PrioritizedRecommendation(
                task=rec.task,
                association_confidence=rec.confidence,
                forgetting_probability=forgetting_prob,
                priority_score=round(score, 4),
                reason=reason,
            )
        )

    prioritized.sort(key=lambda r: r.priority_score, reverse=True)
    return prioritized
