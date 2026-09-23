import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.enums import TaskEventType, TaskStatus
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.schemas.task import TaskCreate, TaskUpdate

# Event types that transition a task into a terminal status
_TERMINAL_EVENT_STATUS = {
    TaskEventType.COMPLETED: TaskStatus.COMPLETED,
    TaskEventType.FORGOTTEN: TaskStatus.FORGOTTEN,
    TaskEventType.CANCELLED: TaskStatus.CANCELLED,
}
# Event types that transition a task into an active/paused status
_STATUS_FOR_EVENT = {
    TaskEventType.STARTED: TaskStatus.IN_PROGRESS,
    TaskEventType.PAUSED: TaskStatus.PAUSED,
    TaskEventType.RESUMED: TaskStatus.IN_PROGRESS,
    **_TERMINAL_EVENT_STATUS,
}


def create_task(db: Session, user_id: uuid.UUID, payload: TaskCreate) -> Task:
    task = Task(user_id=user_id, **payload.model_dump())
    db.add(task)
    db.flush()  # get task.id without committing yet

    # Every task starts life with a CREATED event, per the event model spec.
    db.add(
        TaskEvent(
            task_id=task.id,
            user_id=user_id,
            event_type=TaskEventType.CREATED,
            occurred_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    user_id: uuid.UUID,
    status_filter: TaskStatus | None = None,
    context_tag: str | None = None,
) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user_id)
    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)
    if context_tag is not None:
        stmt = stmt.where(Task.context_tag == context_tag)
    stmt = stmt.order_by(Task.created_at.desc())
    return list(db.scalars(stmt).all())


def get_task(db: Session, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user_id))
    if task is None:
        raise NotFoundError("Task not found.")
    return task


def update_task(db: Session, user_id: uuid.UUID, task_id: uuid.UUID, payload: TaskUpdate) -> Task:
    task = get_task(db, user_id, task_id)
    updates = payload.model_dump(exclude_unset=True)
    new_status = updates.pop("status", None)
    for field, value in updates.items():
        setattr(task, field, value)
    if new_status is not None:
        task.status = new_status
        if new_status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, user_id: uuid.UUID, task_id: uuid.UUID) -> None:
    task = get_task(db, user_id, task_id)
    db.delete(task)
    db.commit()


def apply_task_status_for_event(task: Task, event_type: TaskEventType) -> None:
    """Keep Task.status in sync whenever a new lifecycle TaskEvent is logged."""
    new_status = _STATUS_FOR_EVENT.get(event_type)
    if new_status is not None:
        task.status = new_status
        if event_type in _TERMINAL_EVENT_STATUS and event_type == TaskEventType.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
