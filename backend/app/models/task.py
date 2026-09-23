import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import TaskPriority, TaskStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Task(Base, UUIDPKMixin, TimestampMixin):
    """
    A user task. Tasks carry lightweight "context" metadata (a free-text tag
    and/or a linked Location) so the ML layer can later learn which contexts
    a task is associated with, and which tasks are repeatedly forgotten in
    the same context ("One More Thing" pattern).

    `parent_task_id` self-references another task to represent tasks that
    are behaviourally linked (e.g. "take out trash" often forgotten
    alongside "leave for work").
    """

    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", native_enum=True), nullable=False, default=TaskStatus.PENDING, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority", native_enum=True), nullable=False, default=TaskPriority.MEDIUM
    )

    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    context_location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    context_tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # simple RRULE-like string

    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )

    user: Mapped["User"] = relationship(back_populates="tasks")
    location: Mapped[Optional["Location"]] = relationship(foreign_keys=[context_location_id])
    events: Mapped[List["TaskEvent"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", order_by="TaskEvent.occurred_at"
    )
    parent: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side="Task.id", foreign_keys=[parent_task_id], back_populates="children"
    )
    children: Mapped[List["Task"]] = relationship(
        "Task", foreign_keys=[parent_task_id], back_populates="parent"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task {self.title!r} status={self.status}>"
