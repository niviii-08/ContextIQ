import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, new_uuid


class TaskEventType(str, enum.Enum):
    CREATED = "created"
    STARTED = "started"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FORGOTTEN = "forgotten"
    CANCELLED = "cancelled"


class TaskEvent(Base):
    """Immutable, append-only log of everything that happens to a task.

    `tasks.status` is a denormalized convenience field; `task_events` is the
    authoritative source of truth and what session reconstruction/analytics
    are computed from.
    """

    __tablename__ = "task_events"
    __table_args__ = (
        Index("ix_task_events_user_time", "user_id", "event_time"),
        Index("ix_task_events_task_time", "task_id", "event_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    event_type: Mapped[TaskEventType] = mapped_column(
        Enum(TaskEventType, native_enum=False, length=20), nullable=False
    )
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    task = relationship("Task", back_populates="events")

    def __repr__(self) -> str:
        return f"<TaskEvent id={self.id} task_id={self.task_id} type={self.event_type} at={self.event_time}>"
