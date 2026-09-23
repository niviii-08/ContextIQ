import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import TaskPriority, TaskStatus
from app.schemas.base import ORMBase


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = Field(default=None, gt=0)
    context_location_id: Optional[uuid.UUID] = None
    context_tag: Optional[str] = Field(default=None, max_length=64)
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    parent_task_id: Optional[uuid.UUID] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = Field(default=None, gt=0)
    context_location_id: Optional[uuid.UUID] = None
    context_tag: Optional[str] = Field(default=None, max_length=64)
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    parent_task_id: Optional[uuid.UUID] = None


class TaskRead(ORMBase, TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: TaskStatus
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
