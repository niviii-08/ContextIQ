import uuid
import warnings
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_current_user_id
from app.core.errors import NotFoundError, ValidationError
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.enums import PredictionType

router = APIRouter(prefix="/predictions", tags=["predictions"])

_ALLOWED_RISK_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH"})

class PredictionReason(BaseModel):
    feature: str
    impact: float
    description: str

class ForgettingPrediction(BaseModel):
    id: str
    taskId: str
    taskTitle: str
    riskScore: float
    riskLevel: str
    reasons: List[PredictionReason]
    generatedAt: str
    modelVersion: str

@router.get("/forgetting", response_model=List[ForgettingPrediction])
def list_predictions(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    risk_level: Optional[str] = Query(default=None, max_length=16),
    risk_level_deprecated: Optional[str] = Query(
        default=None,
        alias="riskLevel",
        max_length=16,
        description="Deprecated alias for risk_level; will be removed in a future release.",
    ),
):
    effective_risk: Optional[str] = None
    if risk_level_deprecated is not None:
        warnings.warn(
            "The 'riskLevel' query parameter is deprecated; use 'risk_level' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        effective_risk = risk_level_deprecated
    if risk_level is not None:
        effective_risk = risk_level

    normalized_risk: Optional[str] = None
    if effective_risk is not None:
        normalized_risk = effective_risk.strip().upper()
        if normalized_risk not in _ALLOWED_RISK_LEVELS:
            raise ValidationError(f"Invalid risk_level: '{effective_risk}'. Allowed values: LOW, MEDIUM, HIGH.")

    stmt = (
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .where(Prediction.prediction_type == PredictionType.FORGET_RISK)
        .order_by(Prediction.created_at.desc())
    )
    predictions = db.scalars(stmt).all()

    result = []
    for p in predictions:
        val = p.predicted_value
        level = val.get("risk_level", "LOW")
        if normalized_risk and level != normalized_risk:
            continue

        result.append(ForgettingPrediction(
            id=str(p.id),
            taskId=str(p.task_id) if p.task_id else "",
            taskTitle=val.get("taskTitle", "Unknown Task"),
            riskScore=p.confidence * 100,
            riskLevel=level,
            reasons=[PredictionReason(**r) for r in val.get("reasons", [])],
            generatedAt=p.created_at.isoformat(),
            modelVersion=p.model_version
        ))
    return result

@router.get("/forgetting/task/{task_id}", response_model=ForgettingPrediction)
def get_task_prediction(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    stmt = (
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .where(Prediction.task_id == task_id)
        .where(Prediction.prediction_type == PredictionType.FORGET_RISK)
        .order_by(Prediction.created_at.desc())
        .limit(1)
    )
    p = db.scalar(stmt)
    if not p:
        raise NotFoundError("Prediction not found for task.")

    val = p.predicted_value
    return ForgettingPrediction(
        id=str(p.id),
        taskId=str(p.task_id) if p.task_id else "",
        taskTitle=val.get("taskTitle", "Unknown Task"),
        riskScore=p.confidence * 100,
        riskLevel=val.get("risk_level", "LOW"),
        reasons=[PredictionReason(**r) for r in val.get("reasons", [])],
        generatedAt=p.created_at.isoformat(),
        modelVersion=p.model_version
    )
