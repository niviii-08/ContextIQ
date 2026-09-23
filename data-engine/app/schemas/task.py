from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.task import TaskStatus
from app.models.task_event import TaskEventType
from app.schemas.common import ORMModel


class TaskCreate(BaseModel):
    user_id: UUID
    title: str = Field(min_length=1, max_length=255)
    category: str = Field(default="general", max_length=80)
    priority: int = Field(default=3, ge=1, le=5)
    location_id: UUID | None = None
    deadline_at: datetime | None = None
    # Optional explicit created_at, useful for synthetic/backfilled data.
    # Defaults to "now" server-side if omitted.
    created_at: datetime | None = None


class TaskRead(ORMModel):
    id: UUID
    user_id: UUID
    location_id: UUID | None
    title: str
    category: str
    priority: int
    status: TaskStatus
    deadline_at: datetime | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    forgotten_at: datetime | None
    cancelled_at: datetime | None
    updated_at: datetime


class TaskEventCreate(BaseModel):
    user_id: UUID
    task_id: UUID
    event_type: TaskEventType  # created/started/paused/resumed/completed/forgotten/cancelled
    event_time: datetime
    location_id: UUID | None = None
    event_metadata: dict | None = None

    @field_validator("event_type", mode="before")
    @classmethod
    def _normalize_event_type(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class TaskEventRead(ORMModel):
    id: UUID
    user_id: UUID
    task_id: UUID
    location_id: UUID | None
    event_type: TaskEventType
    event_time: datetime
    event_metadata: dict | None
    created_at: datetime
