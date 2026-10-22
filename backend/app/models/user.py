import uuid
from typing import List

from sqlalchemy import Boolean, Integer, String, Text
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

    role_persona: Mapped[str] = mapped_column(String(64), nullable=False, default="developer")
    custom_title: Mapped[str] = mapped_column(String(255), nullable=False, default="Senior Software Engineer")
    organization: Mapped[str] = mapped_column(String(255), nullable=False, default="Distributed Systems Lab")
    focus_rhythm: Mapped[str] = mapped_column(String(64), nullable=False, default="morning")
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    distractions: Mapped[str] = mapped_column(Text, nullable=False, default='["phone", "slack", "tab_overload"]')
    friction_tolerance: Mapped[str] = mapped_column(String(128), nullable=False, default="Sensitive")
    reentry_anchor: Mapped[str] = mapped_column(Text, nullable=False, default="Inspect the last modified function signature or uncommitted diff.")

    daily_routine: Mapped[str | None] = mapped_column(Text, nullable=True)
    daily_chores: Mapped[str | None] = mapped_column(Text, nullable=True)
    weekend_chores: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequent_forget_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_delay_triggers: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tasks: Mapped[List["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    locations: Mapped[List["Location"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"
