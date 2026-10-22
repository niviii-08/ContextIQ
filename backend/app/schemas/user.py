import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import ORMBase


class UserBase(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=120)
    timezone: str = "UTC"


class UserCreate(UserBase):
    password: Optional[str] = Field(default=None, min_length=4)
    role_persona: Optional[str] = "developer"
    custom_title: Optional[str] = "Senior Software Engineer"
    organization: Optional[str] = "Distributed Systems Lab"
    focus_rhythm: Optional[str] = "morning"
    daily_goal_minutes: Optional[int] = 120
    language: Optional[str] = "en"
    distractions: Optional[str] = None


class InitialTaskItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    estimated_minutes: Optional[int] = 45
    category: Optional[str] = "Deep Work"


class UserSignupWithTasks(BaseModel):
    email: EmailStr
    password: Optional[str] = Field(default="password123", min_length=4)
    display_name: str = Field(..., min_length=1, max_length=120)
    role_persona: Optional[str] = "developer"
    custom_title: Optional[str] = "Senior Software Engineer"
    organization: Optional[str] = "Distributed Systems Lab"
    focus_rhythm: Optional[str] = "morning"
    daily_goal_minutes: Optional[int] = 120
    language: Optional[str] = "en"
    distractions: Optional[list[str]] = None
    daily_routine: Optional[str] = None
    daily_chores: Optional[list[str]] = None
    weekend_chores: Optional[list[str]] = None
    frequent_forget_items: Optional[list[str]] = None
    time_delay_triggers: Optional[list[str]] = None
    primary_occupation: Optional[str] = None
    initial_tasks: Optional[list[InitialTaskItem]] = []


class UserRead(ORMBase, UserBase):
    id: uuid.UUID
    is_active: bool
    role_persona: Optional[str] = "developer"
    custom_title: Optional[str] = "Senior Software Engineer"
    organization: Optional[str] = "Distributed Systems Lab"
    focus_rhythm: Optional[str] = "morning"
    daily_goal_minutes: Optional[int] = 120
    language: Optional[str] = "en"
    distractions: Optional[str] = '["phone", "slack", "tab_overload"]'
    daily_routine: Optional[str] = None
    daily_chores: Optional[str] = None
    weekend_chores: Optional[str] = None
    frequent_forget_items: Optional[str] = None
    time_delay_triggers: Optional[str] = None
    primary_occupation: Optional[str] = None
    created_at: datetime
    updated_at: datetime
