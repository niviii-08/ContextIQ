"""
recommendations.py
===================
Builds "One More Thing?" style recommendations purely from structured
Association + ForgettingPrediction data. No invented content.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import List, Optional

from app.schemas import (
    Association,
    Evidence,
    ForgettingPrediction,
    IntelligenceBundle,
    Priority,
    Recommendation,
)

MIN_RECOMMENDATION_CONFIDENCE = 0.5
HIGH_IMPACT_FORGETTING_PROBABILITY = 0.75


def _recommendation_id(bundle_user_id: str, recommendation_type: str, context: str, task: str) -> str:
    key = "|".join((bundle_user_id, recommendation_type, context, task))
    return f"rec-{hashlib.sha256(key.encode()).hexdigest()[:12]}"


def _matching_prediction(
    task: str, predictions: List[ForgettingPrediction]
) -> Optional[ForgettingPrediction]:
    for p in predictions:
        if p.task == task:
            return p
    return None


def _priority_for(assoc_confidence: float, forgetting_probability: Optional[float]) -> Priority:
    score = assoc_confidence if forgetting_probability is None else max(assoc_confidence, forgetting_probability)
    if score >= 0.75:
        return Priority.HIGH
    if score >= 0.5:
        return Priority.MEDIUM
    return Priority.LOW


def _build_explanation(assoc: Association, prediction: Optional[ForgettingPrediction]) -> str:
    base = (
        f"You're often in the context '{assoc.context}'. You complete '{assoc.task}' "
        f"here with {assoc.confidence:.0%} confidence"
    )
    if prediction is not None:
        base += f" and it currently has a {prediction.probability:.0%} predicted forgetting risk."
    else:
        base += "."
    return base


def generate_recommendations(
    bundle: IntelligenceBundle, max_recommendations: int = 5
) -> List[Recommendation]:
    """Rank associations (optionally paired with forgetting risk) into
    concrete, evidence-backed recommendations."""
    candidates: List[Recommendation] = []

    generated_at = bundle.generated_at or datetime.now(timezone.utc)

    for assoc in bundle.associations:
        if assoc.confidence < MIN_RECOMMENDATION_CONFIDENCE:
            continue

        prediction = _matching_prediction(assoc.task, bundle.forgetting_predictions)
        forgetting_probability = prediction.probability if prediction else None
        recommendation_type = (
            "recurring_forgotten_task_prevention"
            if forgetting_probability is not None and forgetting_probability >= 0.5
            else "context_based_reminder"
        )
        evidence = [
            Evidence(field="association_confidence", value=f"{assoc.confidence:.2f}", source=f"Association:{assoc.context}->{assoc.task}"),
            Evidence(field="association_support", value=f"{assoc.support:.2f}", source=f"Association:{assoc.context}->{assoc.task}"),
            Evidence(field="association_lift", value=f"{assoc.lift:.2f}", source=f"Association:{assoc.context}->{assoc.task}"),
        ]
        if prediction is not None:
            evidence.extend([
                Evidence(field="forgetting_probability", value=f"{prediction.probability:.2f}", source=f"ForgettingPrediction:{prediction.task}"),
                Evidence(field="risk_level", value=prediction.risk_level.value, source=f"ForgettingPrediction:{prediction.task}"),
            ])

        rank_score = 0.6 * assoc.confidence + 0.4 * (forgetting_probability or 0.0)

        candidates.append(
            Recommendation(
                id=_recommendation_id(bundle.user_id, recommendation_type, assoc.context, assoc.task),
                user_id=bundle.user_id,
                recommendation_type=recommendation_type,
                triggering_behaviour=(
                    f"{assoc.task} is strongly associated with the '{assoc.context}' context"
                    + (f" and has a {prediction.probability:.0%} predicted forgetting probability" if prediction else "")
                ),
                evidence=evidence,
                evidence_strength=round(assoc.confidence if prediction is None else max(assoc.confidence, prediction.probability), 4),
                impact_score=round(forgetting_probability or assoc.confidence, 4),
                risk_level=_priority_for(assoc.confidence, forgetting_probability),
                expected_benefit=(
                    "Reduce exposure to the observed forgetting risk by prompting this task in its associated context."
                    if prediction else
                    "Make use of a reliably observed context-task association when planning the next action."
                ),
                generated_at=generated_at,
                context=assoc.context,
                associated_task=assoc.task,
                association_confidence=assoc.confidence,
                forgetting_probability=forgetting_probability,
                headline="One More Thing?",
                explanation=_build_explanation(assoc, prediction),
                priority=_priority_for(assoc.confidence, forgetting_probability),
                rank_score=round(rank_score, 4),
            )
        )

    candidates.sort(key=lambda r: r.rank_score, reverse=True)
    return candidates[:max_recommendations]
