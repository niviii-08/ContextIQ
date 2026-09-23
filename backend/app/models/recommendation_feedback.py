import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.enums import RecommendationFeedbackAction
from app.models.mixins import UUIDPKMixin, utcnow
from app.db.session import Base


class RecommendationFeedback(Base, UUIDPKMixin):
    """
    Records explicit user feedback on a recommendation — whether the user
    accepted, dismissed, or deferred the suggestion, plus an optional link
    to the task that was ultimately created/used as a result and any free
    text note. This data powers the closed-loop improvement pipeline for
    the recommendation engine.
    """

    __tablename__ = "recommendation_feedback"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[RecommendationFeedbackAction] = mapped_column(
        Enum(RecommendationFeedbackAction, name="recommendation_feedback_action", native_enum=True),
        nullable=False,
        index=True,
    )
    suggested_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    feedback_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RecommendationFeedback action={self.action}>"
