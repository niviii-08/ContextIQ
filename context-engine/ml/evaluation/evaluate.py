"""
Evaluation utilities for both System A and System B.

These are lightweight, offline evaluation helpers intended to be run
from scripts/notebooks (see docs/EVALUATION.md) — not part of the live
API request path.
"""

from __future__ import annotations

import pandas as pd

from app.schemas.associations import AssociationRule
from app.schemas.context import ReconstructedSession


def rule_quality_report(rules: list[AssociationRule]) -> pd.DataFrame:
    """Summarize mined rules into a DataFrame for inspection/plotting."""
    if not rules:
        return pd.DataFrame(
            columns=["context", "antecedents", "consequents", "support", "confidence", "lift"]
        )
    return pd.DataFrame(
        [
            {
                "context": r.context,
                "antecedents": " + ".join(r.antecedents),
                "consequents": " + ".join(r.consequents),
                "support": r.support,
                "confidence": r.confidence,
                "lift": r.lift,
            }
            for r in rules
        ]
    ).sort_values(["lift", "confidence"], ascending=False)


def session_summary_report(sessions: list[ReconstructedSession]) -> pd.DataFrame:
    """Summarize sessions into a DataFrame for inspection/plotting."""
    if not sessions:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "task_category": s.task_category,
                "context": s.context,
                "duration_s": s.session_duration_seconds,
                "focused_s": s.focused_time_seconds,
                "interruption_s": s.interruption_time_seconds,
                "num_interruptions": s.num_interruptions,
                "num_switches": s.num_context_switches,
                "completed": s.completed,
            }
            for s in sessions
        ]
    )


def precision_at_k(recommended: list[str], relevant: list[str], k: int = 5) -> float:
    """Standard precision@k for offline evaluation of recommendation quality,
    given a held-out set of tasks actually completed (`relevant`) versus
    what was recommended, ordered by rank."""
    if k <= 0 or not recommended:
        return 0.0
    top_k = recommended[:k]
    relevant_set = set(relevant)
    hits = sum(1 for t in top_k if t in relevant_set)
    return hits / len(top_k)


def recall_at_k(recommended: list[str], relevant: list[str], k: int = 5) -> float:
    if not relevant:
        return 0.0
    top_k = set(recommended[:k])
    relevant_set = set(relevant)
    hits = len(top_k & relevant_set)
    return hits / len(relevant_set)
