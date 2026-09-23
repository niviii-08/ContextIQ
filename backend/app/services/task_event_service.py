import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.task_event import TaskEvent
from app.schemas.task_event import TaskEventCreate
from app.services.task_service import apply_task_status_for_event, get_task


def create_task_event(
    db: Session, user_id: uuid.UUID, task_id: uuid.UUID, payload: TaskEventCreate
) -> TaskEvent:
    task = get_task(db, user_id, task_id)  # raises NotFoundError + enforces user isolation

    event = TaskEvent(
        task_id=task.id,
        user_id=user_id,
        event_type=payload.event_type,
        occurred_at=payload.occurred_at or datetime.now(timezone.utc),
        location_id=payload.location_id,
        event_metadata=payload.event_metadata,
    )
    db.add(event)

    # Keep the parent task's status column in sync with the latest event.
    apply_task_status_for_event(task, payload.event_type)
    db.add(task)

    db.commit()
    db.refresh(event)
    return event


def list_task_events(db: Session, user_id: uuid.UUID, task_id: uuid.UUID) -> list[TaskEvent]:
    get_task(db, user_id, task_id)  # enforce isolation / existence
    stmt = (
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id, TaskEvent.user_id == user_id)
        .order_by(TaskEvent.occurred_at.asc())
    )
    return list(db.scalars(stmt).all())


def list_all_events_for_user(db: Session, user_id: uuid.UUID) -> list[TaskEvent]:
    stmt = select(TaskEvent).where(TaskEvent.user_id == user_id).order_by(TaskEvent.occurred_at.desc())
    return list(db.scalars(stmt).all())
