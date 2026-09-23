import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import TaskEventType
from app.schemas.base import ORMBase


class TaskEventBase(BaseModel):
    event_type: TaskEventType
    occurred_at: Optional[datetime] = None  # defaults to "now" server-side if omitted
    location_id: Optional[uuid.UUID] = None
    event_metadata: Optional[dict[str, Any]] = None


class TaskEventCreate(TaskEventBase):
    pass


class TaskEventRead(ORMBase, TaskEventBase):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    occurred_at: datetime
    created_at: datetime
