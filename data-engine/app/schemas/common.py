from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base class for schemas returned from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str
    display_name: str | None = None
    timezone: str = "UTC"


class UserRead(ORMModel):
    id: UUID
    email: str
    display_name: str | None = None
    timezone: str
    created_at: datetime


class LocationCreate(BaseModel):
    user_id: UUID
    label: str
    latitude: float | None = None
    longitude: float | None = None


class LocationRead(ORMModel):
    id: UUID
    user_id: UUID
    label: str
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime


class MetadataDict(BaseModel):
    """Free-form event metadata envelope, kept as its own type so API
    consumers get clear schema documentation instead of a bare `dict`."""

    data: dict[str, Any] = {}
