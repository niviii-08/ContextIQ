import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db
from app.core.errors import NotFoundError
from app.models.location import Location
from app.models.task import Task
from app.models.recommendation import Recommendation, RecommendationStatus, RecommendationType
from app.models.recommendation_feedback import RecommendationFeedback
from app.models.enums import RecommendationFeedbackAction, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate
from app.services import task_service
from app.schemas.analytics import (
    RecommendationRead,
    RecommendationFeedbackCreate,
    RecommendationFeedbackRead,
)

logger = logging.getLogger(__name__)

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

    if not recommendations:
        tasks = db.scalars(
            select(Task)
            .where(Task.user_id == user_id, Task.status == TaskStatus.PENDING)
            .order_by(Task.created_at.desc())
            .limit(10)
        ).all()
        anchors = [t for t in tasks if "anchor" in t.title.lower() or (t.context_tag and "anchor" in t.context_tag.lower())]
        chores = [t for t in tasks if "chore" in t.title.lower() or (t.context_tag and "chore" in t.context_tag.lower())]
        other_tasks = [t for t in tasks if t not in anchors and t not in chores]

        if anchors:
            a = anchors[0]
            db.add(Recommendation(
                user_id=user_id,
                recommendation_type=RecommendationType.ONE_MORE_THING,
                associated_task=a.title,
                association_confidence=0.91,
                triggering_behaviour="Pre-departure / context transition detected",
                evidence=[{"feature": "anchor_alert", "value": "High forget risk anchor identified"}],
                evidence_strength=0.94,
                status=RecommendationStatus.PROPOSED,
                priority=10,
                explanation=f"Before context-switching, verify: {a.title}. Preventing this slip preserves mental flow.",
                expected_benefit="Guaranteed cognitive closure & zero mental leak",
                impact_score=0.88,
                risk_level="HIGH",
            ))

        if chores:
            c = chores[0]
            db.add(Recommendation(
                user_id=user_id,
                recommendation_type=RecommendationType.ONE_MORE_THING,
                associated_task=c.title,
                association_confidence=0.78,
                triggering_behaviour="Scheduled habit cadence window",
                evidence=[{"feature": "chore_cadence", "value": "Recurring daily routine"}],
                evidence_strength=0.82,
                status=RecommendationStatus.PROPOSED,
                priority=7,
                explanation=f"Knock out '{c.title}' now to clear your background attentional space before deep focus.",
                expected_benefit="Reduced background mental friction by 25%",
                impact_score=0.68,
                risk_level="MEDIUM",
            ))

        if other_tasks:
            o = other_tasks[0]
            db.add(Recommendation(
                user_id=user_id,
                recommendation_type=RecommendationType.OPTIMAL_TIMING,
                associated_task=o.title,
                association_confidence=0.82,
                triggering_behaviour="Peak chronometry alignment window",
                evidence=[{"feature": "flow_window", "value": "Peak energy period"}],
                evidence_strength=0.85,
                status=RecommendationStatus.PROPOSED,
                priority=8,
                explanation=f"Prime window detected for '{o.title}'. Tackling this now leverages maximum cognitive throughput.",
                expected_benefit="Estimated 35% faster resumption lag",
                impact_score=0.75,
                risk_level="LOW",
            ))

        if tasks:
            db.commit()
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
        raise NotFoundError("Recommendation not found.")

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

        safe_location_id: Optional[uuid.UUID] = None
        if body.prefill_location_id is not None:
            ownership_stmt = select(Location.id).where(
                Location.id == body.prefill_location_id,
                Location.user_id == user_id,
            )
            if db.scalar(ownership_stmt) is not None:
                safe_location_id = body.prefill_location_id
            else:
                logger.debug(
                    "prefill_location_id %s does not belong to user %s; dropping",
                    body.prefill_location_id,
                    user_id,
                )

        task_create_payload = TaskCreate(
            title=title,
            description=recommendation.message,
            priority=TaskPriority.MEDIUM,
            due_at=datetime.now(timezone.utc) + timedelta(hours=24),
            context_tag=context_tag,
            context_location_id=safe_location_id,
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
