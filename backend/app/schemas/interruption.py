import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import InterruptionType
from app.schemas.base import ORMBase


class InterruptionBase(BaseModel):
    task_id: Optional[uuid.UUID] = None
    interruption_type: InterruptionType
    occurred_at: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    location_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class InterruptionCreate(InterruptionBase):
    pass


class InterruptionRead(ORMBase, InterruptionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    occurred_at: datetime
    created_at: datetime
