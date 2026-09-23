import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import LocationType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Location(Base, UUIDPKMixin, TimestampMixin):
    """
    A user-defined place that can act as a behavioural context trigger
    (e.g. "Home", "Office desk", "Gym"). Coordinates are optional — a
    location can be purely a manual tag with no GPS attached, in line with
    the project's privacy-first design (no background GPS tracking).
    """

    __tablename__ = "locations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location_type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="location_type", native_enum=True), nullable=False, default=LocationType.OTHER
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    radius_meters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="locations")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Location {self.name}>"
