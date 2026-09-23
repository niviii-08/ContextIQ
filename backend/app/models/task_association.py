import uuid
from datetime import datetime

from sqlalchemy import Enum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.enums import AssociationType
from app.models.mixins import TimestampMixin, UUIDPKMixin
from app.db.session import Base


class TaskAssociation(Base, UUIDPKMixin, TimestampMixin):
    """
    Learned or declared relationship between two tasks belonging to the same
    user, e.g. discovered via `mlxtend` association-rule mining over
    task-completion baskets ("One More Thing" mining). `confidence_score`,
    `support`, and `lift` mirror standard association-rule-mining metrics so
    the ML pipeline can write results directly into this table.
    """

    __tablename__ = "task_associations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    associated_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    association_type: Mapped[AssociationType] = mapped_column(
        Enum(AssociationType, name="association_type", native_enum=True), nullable=False
    )

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    support: Mapped[float | None] = mapped_column(Float, nullable=True)
    lift: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TaskAssociation {self.task_id} -> {self.associated_task_id}>"
