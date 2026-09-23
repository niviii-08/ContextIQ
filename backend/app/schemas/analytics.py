"""
Schemas for the "derived/analytical" tables: context_sessions, predictions,
recommendations, behaviour_metrics, task_associations.

These are primarily written by backend services / the ML pipeline rather
than directly by end users, so most only expose Read schemas plus narrow
Create schemas for internal use.
"""
import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    AssociationType,
    BehaviourMetricType,
    PredictionType,
    RecommendationFeedbackAction,
    RecommendationStatus,
    RecommendationType,
)
from app.schemas.base import ORMBase


# --- Context Sessions ---

class ContextSessionRead(ORMBase):
    id: uuid.UUID
    user_id: uuid.UUID
    location_id: Optional[uuid.UUID] = None
    context_tag: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    task_count: int
    interruption_count: int
    created_at: datetime


# --- Predictions ---

class PredictionCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    task_id: Optional[uuid.UUID] = None
    prediction_type: PredictionType
    predicted_value: dict[str, Any]
    confidence: float = Field(..., ge=0, le=1)
    model_version: str
    valid_until: Optional[datetime] = None


class PredictionRead(ORMBase):
    model_config = ORMBase.model_config | {"protected_namespaces": ()}

    id: uuid.UUID
    user_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    prediction_type: PredictionType
    predicted_value: dict[str, Any]
    confidence: float
    model_version: str
    valid_from: datetime
    valid_until: Optional[datetime] = None
    created_at: datetime


# --- Recommendations ---

class RecommendationRead(ORMBase):
    id: uuid.UUID
    user_id: uuid.UUID
    task_id: Optional[uuid.UUID] = None
    recommendation_type: RecommendationType
    title: str
    message: str
    status: RecommendationStatus
    priority: int
    shown_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RecommendationStatusUpdate(BaseModel):
    status: RecommendationStatus


# --- Behaviour Metrics ---

class BehaviourMetricRead(ORMBase):
    id: uuid.UUID
    user_id: uuid.UUID
    metric_date: date
    metric_type: BehaviourMetricType
    value: float
    metric_metadata: Optional[dict[str, Any]] = None
    created_at: datetime


# --- Task Associations ---

class TaskAssociationRead(ORMBase):
    id: uuid.UUID
    user_id: uuid.UUID
    task_id: uuid.UUID
    associated_task_id: uuid.UUID
    association_type: AssociationType
    confidence_score: float
    support: Optional[float] = None
    lift: Optional[float] = None
    created_at: datetime


# --- Recommendation Feedback ---

class RecommendationFeedbackCreate(BaseModel):
    action: RecommendationFeedbackAction
    suggested_task_id: Optional[uuid.UUID] = None
    feedback_note: Optional[str] = None


class RecommendationFeedbackRead(ORMBase):
    id: uuid.UUID
    user_id: uuid.UUID
    recommendation_id: uuid.UUID
    action: RecommendationFeedbackAction
    suggested_task_id: Optional[uuid.UUID] = None
    feedback_note: Optional[str] = None
    created_at: datetime
