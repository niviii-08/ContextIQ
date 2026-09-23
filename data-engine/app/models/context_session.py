import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, new_uuid


class ContextSession(Base):
    """A reconstructed behavioural work session, derived from raw task
    events + interruptions by the Context Session Engine
    (see app/services/session_engine.py).

    A session is NOT the same thing as a task: a single task can span
    multiple sessions (if paused and resumed after a long gap), and a
    single session can, in principle, touch more than one task if the
    events are contiguous in time (tracked via `context_switch_count`).
    """

    __tablename__ = "context_sessions"
    __table_args__ = (
        Index("ix_context_sessions_user_start", "user_id", "session_start"),
        Index("ix_context_sessions_task", "task_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    focused_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interruption_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resume_delay_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    context_switch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interruption_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User", back_populates="context_sessions")
    task = relationship("Task", back_populates="context_sessions")
    location = relationship("Location", back_populates="context_sessions")

    def __repr__(self) -> str:
        return f"<ContextSession id={self.id} user_id={self.user_id} start={self.session_start}>"
