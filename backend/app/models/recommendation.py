import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.enums import RecommendationStatus, RecommendationType
from app.models.mixins import TimestampMixin, UUIDPKMixin, utcnow
from app.db.session import Base


class Recommendation(Base, UUIDPKMixin, TimestampMixin):
    """
    A concrete, user-facing suggestion generated from predictions +
    task_associations (e.g. "You usually forget to bring your gym bag when
    you leave in a hurry — want a reminder next time?"). Status tracks the
    recommendation lifecycle so acceptance/dismissal can feed back into
    model evaluation.
    """

    __tablename__ = "recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recommendation_type: Mapped[RecommendationType] = mapped_column(
        Enum(RecommendationType, name="recommendation_type", native_enum=True), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, name="recommendation_status", native_enum=True),
        nullable=False,
        default=RecommendationStatus.PENDING,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    shown_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Recommendation {self.recommendation_type} status={self.status}>"
