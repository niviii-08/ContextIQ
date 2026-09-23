import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.enums import PredictionType

router = APIRouter(prefix="/predictions", tags=["predictions"])

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
    riskLevel: Optional[str] = None
):
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
        if riskLevel and level != riskLevel:
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

@router.get("/forgetting/task/{task_id}", response_model=Optional[ForgettingPrediction])
def get_task_prediction(
    task_id: str,
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
        return None
        
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
