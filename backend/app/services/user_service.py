import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.user import User
from app.schemas.user import UserCreate

try:
    import bcrypt
except ImportError:  # pragma: no cover - bcrypt is a declared dependency; guard for partial installs
    bcrypt = None


def _hash_password(password: str) -> str:
    if bcrypt is None:
        raise RuntimeError("bcrypt is not installed — add it to requirements.txt")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_user(db: Session, payload: UserCreate) -> User:
    """
    Dev-mode user creation. In production this is superseded by Supabase Auth
    (see app/core/deps.py) — this endpoint exists so the stack is runnable
    and testable end-to-end without Supabase configured.
    """
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise ConflictError("A user with this email already exists.")

    user = User(
        email=payload.email,
        display_name=payload.display_name,
        timezone=payload.timezone,
        hashed_password=_hash_password(payload.password) if payload.password else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    return user
