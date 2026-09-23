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
    password: Optional[str] = Field(default=None, min_length=8)


class UserRead(ORMBase, UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
