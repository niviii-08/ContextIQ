import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, new_uuid


class InterruptionType(str, enum.Enum):
    PHONE = "phone"
    SOCIAL_MEDIA = "social_media"
    MESSAGE = "message"
    CALL = "call"
    SEARCH = "search"
    PERSON = "person"
    FOOD = "food"
    OTHER = "other"


class Interruption(Base):
    __tablename__ = "interruptions"
    __table_args__ = (
        Index("ix_interruptions_user_time", "user_id", "start_time"),
        Index("ix_interruptions_task", "task_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Nullable: an interruption can happen while the user is not tied to any
    # specific task (idle browsing between tasks, for example).
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    interruption_type: Mapped[InterruptionType] = mapped_column(
        Enum(InterruptionType, native_enum=False, length=20), nullable=False
    )
    source_label: Mapped[str | None] = mapped_column(String(120), nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    task = relationship("Task", back_populates="interruptions")

    def __repr__(self) -> str:
        return f"<Interruption id={self.id} type={self.interruption_type} task_id={self.task_id}>"
