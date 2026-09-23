"""
In-memory application state.

This module centralizes storage of analysis results so that the
POST /context/analyze -> GET /context/{context_id}/associations flow
works within a running process. It is intentionally storage-agnostic
at the interface level: `ContextStore` exposes plain get/set methods
that could be backed by SQLAlchemy models instead, without changing
any caller. Swap this implementation for a real persistence layer when
integrating into ContextIQ.
"""

from __future__ import annotations

from collections import defaultdict

from app.schemas.associations import AssociationRule
from app.schemas.context import ReconstructedSession
from ml.associations.mining import acceptance_rate_from_feedback
from ml.associations.recommender import DismissalStore


class ContextStore:
    def __init__(self) -> None:
        self.sessions_by_context: dict[str, list[ReconstructedSession]] = {}
        self.rules_by_context: dict[str, list[AssociationRule]] = {}
        self.dismissal_store = DismissalStore()
        self._feedback_counts: dict[
            tuple[frozenset, frozenset], dict[str, int]
        ] = defaultdict(lambda: {"accepted": 0, "dismissed": 0, "deferred": 0})
        self._acceptance_weights: dict[tuple[frozenset[str], frozenset[str]], float] = {}

    @property
    def acceptance_weights(self) -> dict[tuple[frozenset[str], frozenset[str]], float]:
        return self._acceptance_weights

    def record_feedback(self, antecedent: list[str], consequent: list[str], action: str) -> None:
        ant = frozenset(antecedent)
        cons = frozenset(consequent)
        key = (ant, cons)
        action_lower = action.lower()
        if action_lower == "accepted":
            self._feedback_counts[key]["accepted"] += 1
        elif action_lower == "dismissed":
            self._feedback_counts[key]["dismissed"] += 1
        elif action_lower == "deferred":
            self._feedback_counts[key]["deferred"] += 1

        rows: list[dict] = []
        for (k_ant, k_cons), counts in self._feedback_counts.items():
            for _ in range(counts["accepted"]):
                rows.append(
                    {
                        "antecedent": list(k_ant),
                        "consequent": list(k_cons),
                        "action": "ACCEPTED",
                    }
                )
            for _ in range(counts["dismissed"]):
                rows.append(
                    {
                        "antecedent": list(k_ant),
                        "consequent": list(k_cons),
                        "action": "DISMISSED",
                    }
                )
            for _ in range(counts["deferred"]):
                rows.append(
                    {
                        "antecedent": list(k_ant),
                        "consequent": list(k_cons),
                        "action": "DEFERRED",
                    }
                )
        self._acceptance_weights = acceptance_rate_from_feedback(rows)

    def save_sessions(self, sessions: list[ReconstructedSession]) -> None:
        for s in sessions:
            self.sessions_by_context.setdefault(s.context, []).append(s)

    def save_rules(self, context: str, rules: list[AssociationRule]) -> None:
        self.rules_by_context[context] = rules

    def get_rules(self, context: str) -> list[AssociationRule]:
        return self.rules_by_context.get(context, [])

    def get_all_rules(self) -> list[AssociationRule]:
        all_rules: list[AssociationRule] = []
        for rules in self.rules_by_context.values():
            all_rules.extend(rules)
        return all_rules


# Process-wide singleton. In a multi-worker deployment this would be
# replaced by a shared database/cache, but the call sites below would
# not need to change.
store = ContextStore()
