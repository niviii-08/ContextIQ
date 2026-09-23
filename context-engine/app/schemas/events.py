"""
Event schemas for the Context Intelligence Module.

These schemas define the canonical shape of raw behavioural events
consumed by System A (context switching intelligence) and used to
derive transactions for System B (association mining).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class EventType(str, Enum):
    START = "START"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    INTERRUPTION = "INTERRUPTION"
    COMPLETE = "COMPLETE"
    TASK_SWITCH = "TASK_SWITCH"


class RawEvent(BaseModel):
    """A single raw behavioural event, as it would arrive from a client."""

    model_config = ConfigDict(use_enum_values=True)

    user_id: str = Field(..., description="Stable identifier for the user")
    timestamp: datetime = Field(..., description="UTC timestamp of the event")
    task_id: str = Field(..., description="Identifier for the task the event refers to")
    task_category: str = Field(
        ..., description="Free-form category, e.g. 'programming', 'study', 'admin'"
    )
    context: str = Field(
        ..., description="Contextual location/environment, e.g. 'department', 'library'"
    )
    event_type: EventType = Field(..., description="One of the six supported event types")

    # Optional metadata that helps some downstream computations but is not required.
    interruption_source: Optional[str] = Field(
        default=None,
        description="Optional source of an INTERRUPTION event, e.g. 'social_media', 'phone_call'",
    )


class EventBatch(BaseModel):
    """A batch of raw events submitted for analysis."""

    events: list[RawEvent]
