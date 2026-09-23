"""
daily_summary.py
=================
Builds the DailySummary purely from structured inputs and already-ranked
insights. No invented numbers.
"""

from __future__ import annotations

from typing import List, Optional

from app.insight_engine import generate_insights
from app.ranking import rank_insights
from app.schemas import DailySummary, ForgettingPrediction, IntelligenceBundle, RankedInsight


def _highest_risk_prediction(predictions: List[ForgettingPrediction]) -> Optional[ForgettingPrediction]:
    if not predictions:
        return None
    return max(predictions, key=lambda p: p.probability)


def _biggest_friction_label(bundle: IntelligenceBundle, ranked: List[RankedInsight]) -> Optional[str]:
    if ranked:
        return ranked[0].title
    if bundle.context_insights:
        return "Context switching"
    return None


def _estimate_avoidable_friction_minutes(bundle: IntelligenceBundle) -> Optional[float]:
    total = 0.0
    found = False
    for ci in bundle.context_insights:
        total += ci.recovery_cost_minutes
        found = True
    return round(total, 1) if found else None


def _context_reminder(bundle: IntelligenceBundle) -> Optional[str]:
    strong = [a for a in bundle.associations if a.confidence >= 0.7]
    if not strong:
        return None
    top = max(strong, key=lambda a: a.confidence)
    return f"{top.context} tasks are frequently forgotten" if top.confidence >= 0.7 else None


def generate_daily_summary(bundle: IntelligenceBundle, top_n: int = 3) -> DailySummary:
    insights = generate_insights(bundle)
    ranked = rank_insights(insights)

    highest_risk = _highest_risk_prediction(bundle.forgetting_predictions)

    return DailySummary(
        biggest_friction=_biggest_friction_label(bundle, ranked),
        highest_risk_task=highest_risk.task if highest_risk else None,
        highest_risk_probability=highest_risk.probability if highest_risk else None,
        context_reminder=_context_reminder(bundle),
        estimated_avoidable_friction_minutes=_estimate_avoidable_friction_minutes(bundle),
        top_insights=ranked[:top_n],
    )
