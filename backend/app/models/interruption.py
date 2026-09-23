import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import InterruptionType
from app.models.mixins import UUIDPKMixin, utcnow


class Interruption(Base, UUIDPKMixin):
    """
    A logged interruption event. Interruptions are explicitly logged by the
    user (privacy-first — no background monitoring). They may optionally be
    linked to the task that was interrupted and the location where it
    happened, which lets the ML layer correlate interruption type/location
    with forgotten-task risk and context-switch cost.
    """

    __tablename__ = "interruptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    interruption_type: Mapped[InterruptionType] = mapped_column(
        Enum(InterruptionType, name="interruption_type", native_enum=True), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    task: Mapped[Optional["Task"]] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Interruption {self.interruption_type} user={self.user_id}>"
