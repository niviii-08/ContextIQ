import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.interruption import Interruption
from app.schemas.interruption import InterruptionCreate


def create_interruption(db: Session, user_id: uuid.UUID, payload: InterruptionCreate) -> Interruption:
    interruption = Interruption(
        user_id=user_id,
        occurred_at=payload.occurred_at or datetime.now(timezone.utc),
        **payload.model_dump(exclude={"occurred_at"}),
    )
    db.add(interruption)
    db.commit()
    db.refresh(interruption)
    return interruption


def list_interruptions(
    db: Session, user_id: uuid.UUID, task_id: uuid.UUID | None = None
) -> list[Interruption]:
    stmt = select(Interruption).where(Interruption.user_id == user_id)
    if task_id is not None:
        stmt = stmt.where(Interruption.task_id == task_id)
    stmt = stmt.order_by(Interruption.occurred_at.desc())
    return list(db.scalars(stmt).all())


def get_interruption(db: Session, user_id: uuid.UUID, interruption_id: uuid.UUID) -> Interruption:
    interruption = db.scalar(
        select(Interruption).where(Interruption.id == interruption_id, Interruption.user_id == user_id)
    )
    if interruption is None:
        raise NotFoundError("Interruption not found.")
    return interruption


def delete_interruption(db: Session, user_id: uuid.UUID, interruption_id: uuid.UUID) -> None:
    interruption = get_interruption(db, user_id, interruption_id)
    db.delete(interruption)
    db.commit()
