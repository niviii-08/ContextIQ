import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Float, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.database.base import Base, GUID, new_uuid


class Location(Base):
    """A named context/location a user works from (Home, Office, Cafe, ...).

    Locations double as generic "context" markers — they don't have to be
    physical GPS points; `label` alone is sufficient (e.g. "Home Office").
    """

    __tablename__ = "locations"
    __table_args__ = (
        Index("ix_locations_user_label", "user_id", "name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    label = synonym("name")
    location_type: Mapped[str] = mapped_column(
        Enum('HOME', 'WORK', 'GYM', 'COMMUTE', 'STUDY', 'OTHER', name='location_type'),
        nullable=False,
        default="OTHER"
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User", back_populates="locations")
    tasks = relationship("Task", back_populates="location")
    context_sessions = relationship("ContextSession", back_populates="location")

    def __repr__(self) -> str:
        return f"<Location id={self.id} label={self.label!r}>"
