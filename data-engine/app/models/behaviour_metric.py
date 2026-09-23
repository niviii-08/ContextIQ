import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Float, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, new_uuid


class BehaviourMetric(Base):
    """Materialized/cached analytics output.

    Analytics endpoints compute metrics on the fly from raw tables, but
    expensive aggregates (e.g. daily rollups) can be persisted here so
    downstream ML/recommendation modules can query pre-computed values
    instead of recomputing them. `metric_name` + `dimension` + `period_start`
    form a natural composite key for a rollup row.
    """

    __tablename__ = "behaviour_metrics"
    __table_args__ = (
        Index("ix_behaviour_metrics_user_metric", "user_id", "metric_name"),
        UniqueConstraint(
            "user_id", "metric_name", "dimension", "period_start", name="uq_behaviour_metric_row"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    # e.g. "weekday:Monday", "category:deep_work", "location:<uuid>", "overall"
    dimension: Mapped[str] = mapped_column(String(120), nullable=False, default="overall")

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    value: Mapped[float] = mapped_column(Float, nullable=False)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User", back_populates="behaviour_metrics")

    def __repr__(self) -> str:
        return f"<BehaviourMetric {self.metric_name}/{self.dimension}={self.value}>"
