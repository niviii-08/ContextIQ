import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.enums import BehaviourMetricType
from app.models.mixins import UUIDPKMixin, utcnow
from app.db.session import Base


class BehaviourMetric(Base, UUIDPKMixin):
    """
    Daily aggregated behavioural metric per user (e.g. forgotten-task rate
    on 2026-08-17). This is the primary feature table the ML layer reads
    from for trend analysis and model input, and what the dashboard's
    Recharts visualizations are driven by.
    """

    __tablename__ = "behaviour_metrics"
    __table_args__ = (
        UniqueConstraint("user_id", "metric_date", "metric_type", name="uq_behaviour_metric_per_day"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    metric_type: Mapped[BehaviourMetricType] = mapped_column(
        Enum(BehaviourMetricType, name="behaviour_metric_type", native_enum=True), nullable=False, index=True
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BehaviourMetric {self.metric_type} {self.metric_date}={self.value}>"
