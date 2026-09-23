import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import TaskEventType
from app.models.mixins import TimestampMixin, UUIDPKMixin, utcnow


class TaskEvent(Base, UUIDPKMixin):
    """
    Immutable log of everything that happens to a task. This is the
    primary training signal for the ML layer (forget prediction,
    context-switch modelling, etc.) — events are never mutated after
    creation, only appended.
    """

    __tablename__ = "task_events"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[TaskEventType] = mapped_column(
        Enum(TaskEventType, name="task_event_type", native_enum=True), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="events")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TaskEvent {self.event_type} task={self.task_id}>"
