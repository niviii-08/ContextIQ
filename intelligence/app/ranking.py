"""
ranking.py
==========
Deterministic priority/ranking engine for insights and recommendations.

RANKING LOGIC (documented, as required)
----------------------------------------
Each insight/recommendation receives a rank_score computed as a weighted sum
of normalized signals:

    rank_score = (
          0.30 * frequency_signal
        + 0.25 * time_cost_signal
        + 0.25 * risk_probability_signal
        + 0.10 * repetition_signal
        + 0.05 * recency_signal
        + 0.05 * user_relevance_signal
    )

All signals are normalized to [0, 1] before weighting:

- frequency_signal: derived from counts present in evidence (e.g. switch_count,
  previous_forgetting_count), scaled against a soft cap (10 -> 1.0).
- time_cost_signal: derived from any *_minutes evidence field, scaled against
  a soft cap (60 minutes -> 1.0).
- risk_probability_signal: the insight's `confidence` field when present
  (already a 0-1 probability/confidence from upstream models), else 0.5.
- repetition_signal: 1.0 if the same insight `type` appears more than once in
  the batch being ranked, else 0.0.
- recency_signal: placeholder fixed at 1.0 (all current-run insights are
  treated as equally recent since no historical timestamps are guaranteed
  present in the input contract). Left as an explicit, documented hook for
  future extension once historical insight timestamps are available.
- user_relevance_signal: fixed at 0.5 (neutral) unless a Priority hint from
  the source model (risk_level == HIGH) boosts it to 1.0. This is a
  documented hook for future personalization signals (e.g. per-user
  dismissal history) without changing the public ranking interface.

The final Priority bucket (HIGH/MEDIUM/LOW) is then derived from rank_score:
    >= 0.66 -> HIGH
    >= 0.33 -> MEDIUM
    else    -> LOW

The engine never overrides an upstream HIGH priority signal downward below
MEDIUM; upstream-declared HIGH priority insights are floored at MEDIUM even
if the computed rank_score is lower, since those already reflect a model's
own risk assessment.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List

from app.schemas import Insight, Priority, RankedInsight

FREQUENCY_SOFT_CAP = 10.0
TIME_COST_SOFT_CAP_MINUTES = 60.0

_NUM_RE = re.compile(r"-?\d+(\.\d+)?")


def _extract_numeric(value: str) -> float:
    m = _NUM_RE.search(value)
    return float(m.group()) if m else 0.0


def _frequency_signal(insight: Insight) -> float:
    candidates = [
        e for e in insight.evidence
        if e.field in ("previous_forgetting_count", "switch_count")
    ]
    if not candidates:
        return 0.0
    raw = max(_extract_numeric(e.value) for e in candidates)
    return min(raw / FREQUENCY_SOFT_CAP, 1.0)


def _time_cost_signal(insight: Insight) -> float:
    candidates = [e for e in insight.evidence if "minutes" in e.field]
    if not candidates:
        return 0.0
    raw = max(_extract_numeric(e.value) for e in candidates)
    return min(raw / TIME_COST_SOFT_CAP_MINUTES, 1.0)


def _risk_probability_signal(insight: Insight) -> float:
    if insight.confidence is not None:
        return float(insight.confidence)
    return 0.5


def _repetition_signal(insight: Insight, type_counts: Counter) -> float:
    return 1.0 if type_counts[insight.type] > 1 else 0.0


def _recency_signal(_insight: Insight) -> float:
    # Documented hook: no per-insight historical timestamp is guaranteed in
    # the input contract today, so all insights in a single generation run
    # are treated as equally recent.
    return 1.0


def _user_relevance_signal(insight: Insight) -> float:
    # Documented hook for future personalization; currently neutral, with a
    # boost when the upstream model already flagged HIGH priority.
    return 1.0 if insight.priority == Priority.HIGH else 0.5


def _bucket_from_score(score: float, upstream_priority: Priority) -> Priority:
    if score >= 0.66:
        computed = Priority.HIGH
    elif score >= 0.33:
        computed = Priority.MEDIUM
    else:
        computed = Priority.LOW

    if upstream_priority == Priority.HIGH:
        # Floor at MEDIUM: never silently downgrade a model-flagged HIGH risk.
        order = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2}
        if order[computed] < order[Priority.MEDIUM]:
            return Priority.MEDIUM
    return computed


def rank_insights(insights: List[Insight]) -> List[RankedInsight]:
    """Score and sort insights, assigning final priority buckets and rank order."""
    type_counts = Counter(i.type for i in insights)

    scored: List[tuple] = []
    for insight in insights:
        score = (
            0.30 * _frequency_signal(insight)
            + 0.25 * _time_cost_signal(insight)
            + 0.25 * _risk_probability_signal(insight)
            + 0.10 * _repetition_signal(insight, type_counts)
            + 0.05 * _recency_signal(insight)
            + 0.05 * _user_relevance_signal(insight)
        )
        scored.append((score, insight))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    ranked: List[RankedInsight] = []
    for position, (score, insight) in enumerate(scored, start=1):
        final_priority = _bucket_from_score(score, insight.priority)
        ranked.append(
            RankedInsight(
                **insight.model_dump(exclude={"priority"}),
                priority=final_priority,
                rank_score=round(score, 4),
                rank_position=position,
            )
        )
    return ranked
