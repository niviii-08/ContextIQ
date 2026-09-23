from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.interruption import InterruptionType
from app.schemas.common import ORMModel


class InterruptionCreate(BaseModel):
    user_id: UUID
    task_id: UUID | None = None
    location_id: UUID | None = None
    interruption_type: InterruptionType
    source_label: str | None = Field(default=None, max_length=120)
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: int | None = None

    @field_validator("interruption_type", mode="before")
    @classmethod
    def _normalize_type(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @model_validator(mode="after")
    def _fill_duration(self):
        if self.duration_seconds is None and self.end_time is not None:
            delta = (self.end_time - self.start_time).total_seconds()
            object.__setattr__(self, "duration_seconds", max(0, int(delta)))
        return self


class InterruptionRead(ORMModel):
    id: UUID
    user_id: UUID
    task_id: UUID | None
    location_id: UUID | None
    interruption_type: InterruptionType
    source_label: str | None
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    created_at: datetime
