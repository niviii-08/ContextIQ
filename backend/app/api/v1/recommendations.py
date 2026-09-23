import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db
from app.models.recommendation import Recommendation, RecommendationStatus, RecommendationType
from app.models.recommendation_feedback import RecommendationFeedback
from app.models.enums import RecommendationFeedbackAction, TaskPriority
from app.schemas.task import TaskCreate
from app.services import task_service
from app.schemas.analytics import (
    RecommendationRead,
    RecommendationFeedbackCreate,
    RecommendationFeedbackRead,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class EnrichedRecommendationRead(RecommendationRead):
    acceptance_stats: dict[str, int]


class RecommendationFeedbackWithPrefill(RecommendationFeedbackCreate):
    prefill_context_tag: Optional[str] = None
    prefill_location_id: Optional[uuid.UUID] = None


@router.get("", response_model=list[EnrichedRecommendationRead])
def list_recommendations(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Recommendation)
        .where(Recommendation.user_id == user_id)
        .order_by(Recommendation.priority.desc(), Recommendation.created_at.desc())
    )
    recommendations = list(db.scalars(stmt).all())

    rec_ids = [rec.id for rec in recommendations]
    if rec_ids:
        feedback_stmt = select(RecommendationFeedback).where(
            RecommendationFeedback.recommendation_id.in_(rec_ids)
        )
        all_feedback = list(db.scalars(feedback_stmt).all())
    else:
        all_feedback = []

    stats_map: dict[uuid.UUID, dict[str, int]] = {}
    for fb in all_feedback:
        if fb.recommendation_id not in stats_map:
            stats_map[fb.recommendation_id] = {
                "accepted": 0,
                "dismissed": 0,
                "deferred": 0,
            }
        action_key = fb.action.value.lower()
        stats_map[fb.recommendation_id][action_key] = (
            stats_map[fb.recommendation_id].get(action_key, 0) + 1
        )

    result: list[EnrichedRecommendationRead] = []
    for rec in recommendations:
        rec_stats = stats_map.get(
            rec.id, {"accepted": 0, "dismissed": 0, "deferred": 0}
        )
        rec_data = RecommendationRead.model_validate(rec)
        enriched = EnrichedRecommendationRead(
            **rec_data.model_dump(),
            acceptance_stats=rec_stats,
        )
        result.append(enriched)

    return result


@router.post(
    "/{recommendation_id}/feedback",
    status_code=status.HTTP_201_CREATED,
)
def post_recommendation_feedback(
    recommendation_id: uuid.UUID,
    body: RecommendationFeedbackWithPrefill,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = select(Recommendation).where(
        Recommendation.id == recommendation_id,
        Recommendation.user_id == user_id,
    )
    recommendation = db.scalar(stmt)
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found.",
        )

    feedback = RecommendationFeedback(
        user_id=user_id,
        recommendation_id=recommendation_id,
        action=body.action,
        feedback_note=body.feedback_note,
    )
    db.add(feedback)
    db.flush()

    created_task = None
    if body.action == RecommendationFeedbackAction.ACCEPTED:
        title = recommendation.title or f"Accepted suggestion: {str(recommendation.id)[:8]}"
        context_tag = body.prefill_context_tag
        if context_tag is None and recommendation.title:
            context_tag = (
                recommendation.title
                if len(recommendation.title) <= 64
                else None
            )

        task_create_payload = TaskCreate(
            title=title,
            description=recommendation.message,
            priority=TaskPriority.MEDIUM,
            due_at=datetime.now(timezone.utc) + timedelta(hours=24),
            context_tag=context_tag,
            context_location_id=body.prefill_location_id,
        )
        created_task = task_service.create_task(db, user_id, task_create_payload)
        feedback.suggested_task_id = created_task.id

    now = datetime.now(timezone.utc)
    if body.action == RecommendationFeedbackAction.ACCEPTED:
        recommendation.status = RecommendationStatus.ACCEPTED
        if recommendation.shown_at is None:
            recommendation.shown_at = now
    elif body.action == RecommendationFeedbackAction.DISMISSED:
        recommendation.status = RecommendationStatus.DISMISSED

    recommendation.responded_at = now

    db.commit()
    db.refresh(feedback)

    return {
        "feedback": RecommendationFeedbackRead.model_validate(feedback),
        "created_task_id": (str(created_task.id) if created_task else None),
    }
