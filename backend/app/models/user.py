import uuid
from typing import List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, TimestampMixin):
    """
    Application user.

    In production, auth is delegated to Supabase Auth — this table's `id`
    is expected to match the Supabase `auth.users.id` (see database/migrations
    for the RLS policy that enforces this). `hashed_password` is retained only
    for local/dev environments that are not using Supabase Auth directly.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tasks: Mapped[List["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    locations: Mapped[List["Location"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"
