import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.models.behaviour_metric import BehaviourMetric
from app.models.recommendation import Recommendation
from app.schemas.analytics import BehaviourMetricRead, RecommendationRead

router = APIRouter(tags=["analytics"])


@router.get("/behaviour-metrics", response_model=list[BehaviourMetricRead])
def list_behaviour_metrics(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Read-only feed for dashboard charts. Rows are written by the ML/analytics pipeline."""
    stmt = (
        select(BehaviourMetric)
        .where(BehaviourMetric.user_id == user_id)
        .order_by(BehaviourMetric.metric_date.asc())
    )
    return list(db.scalars(stmt).all())


@router.get("/recommendations", response_model=list[RecommendationRead])
def list_recommendations(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Recommendation)
        .where(Recommendation.user_id == user_id)
        .order_by(Recommendation.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.get("/context-switch-timeline")
async def get_context_switch_timeline(
    user_id: uuid.UUID = Depends(get_current_user_id),
    period_days: int = Query(30, ge=1, le=3650),
):
    settings = get_settings()
    url = f"{settings.DATA_ENGINE_URL.rstrip('/')}/analytics/context-switch-timeline"
    params = {"user_id": str(user_id), "period_days": period_days}
    try:
        async with httpx.AsyncClient(timeout=settings.ORCHESTRATOR_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to contact data engine: {e}")


@router.get("/task-context-heatmap")
async def get_task_context_heatmap(
    user_id: uuid.UUID = Depends(get_current_user_id),
    period_days: int = Query(30, ge=1, le=3650),
    value_metric: str = Query("completion_rate", pattern="^(completion_rate|forget_rate)$"),
):
    settings = get_settings()
    url = f"{settings.DATA_ENGINE_URL.rstrip('/')}/analytics/task-context-heatmap"
    params = {
        "user_id": str(user_id),
        "period_days": period_days,
        "value_metric": value_metric,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ORCHESTRATOR_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to contact data engine: {e}")
