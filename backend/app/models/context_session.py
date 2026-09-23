import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import UUIDPKMixin, utcnow


class ContextSession(Base, UUIDPKMixin):
    """
    A continuous window of activity within one behavioural context
    (e.g. "at desk, 9:03am-10:47am"). Sessions are derived/aggregated
    (by the backend or an ML batch job) from task_events + interruptions,
    and serve as the primary unit for behaviour_metrics aggregation and
    context-switch-cost modelling.
    """

    __tablename__ = "context_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    context_tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interruption_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContextSession user={self.user_id} started_at={self.started_at}>"
