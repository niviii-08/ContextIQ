"""
schemas.py

Pydantic models defining the API contract. These mirror ml/features/feature_spec.py
exactly so that API validation and model feature construction never drift apart.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from ml.features.feature_spec import CATEGORY_DOMAIN, PRIORITY_DOMAIN, LOCATION_DOMAIN


class TaskFeatures(BaseModel):
    """Single task observation / prediction point."""

    task_id: Optional[str] = Field(None, description="Optional client-supplied task identifier")
    task_category: str = Field(..., description=f"One of {CATEGORY_DOMAIN}")
    priority: str = Field(..., description=f"One of {PRIORITY_DOMAIN}")
    location: str = Field(..., description=f"One of {LOCATION_DOMAIN}")

    weekday: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    hour: int = Field(..., ge=0, le=23)
    deadline_distance_hours: float = Field(..., ge=0, description="Hours until deadline")

    previous_completion_count: int = Field(..., ge=0)
    previous_forgetting_count: int = Field(..., ge=0)
    historical_completion_rate: float = Field(..., ge=0, le=1)
    historical_forgetting_rate: float = Field(..., ge=0, le=1)
    task_frequency: float = Field(..., ge=0, le=1)

    tasks_today: int = Field(..., ge=0)
    interruptions_today: int = Field(..., ge=0)
    recent_context_switches: int = Field(..., ge=0)
    avg_interruption_duration: float = Field(..., ge=0)
    avg_session_duration: float = Field(..., ge=0)

    @field_validator("task_category")
    @classmethod
    def validate_category(cls, v):
        if v not in CATEGORY_DOMAIN:
            raise ValueError(f"task_category must be one of {CATEGORY_DOMAIN}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v not in PRIORITY_DOMAIN:
            raise ValueError(f"priority must be one of {PRIORITY_DOMAIN}")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v):
        if v not in LOCATION_DOMAIN:
            raise ValueError(f"location must be one of {LOCATION_DOMAIN}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "Lab Record",
                "task_category": "Academic",
                "priority": "HIGH",
                "location": "Campus",
                "weekday": 2,
                "hour": 14,
                "deadline_distance_hours": 18.0,
                "previous_completion_count": 12,
                "previous_forgetting_count": 8,
                "historical_completion_rate": 0.4,
                "historical_forgetting_rate": 0.55,
                "task_frequency": 0.3,
                "tasks_today": 5,
                "interruptions_today": 4,
                "recent_context_switches": 6,
                "avg_interruption_duration": 8.5,
                "avg_session_duration": 22.0,
            }
        }
    )


class PredictionResponse(BaseModel):
    task: Optional[str] = None
    prediction_probability: float
    risk_level: str
    model_version: str
    top_features: List[str]

    model_config = {'protected_namespaces': ()}


class BatchPredictionRequest(BaseModel):
    tasks: List[TaskFeatures]


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_version: str
    model_name: str

    model_config = {'protected_namespaces': ()}
