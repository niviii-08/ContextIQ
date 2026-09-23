import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.models.enums import TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.schemas.task_event import TaskEventCreate, TaskEventRead
from app.services import task_event_service, task_service
from app.services.orchestrator import get_orchestrator

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    task = task_service.create_task(db, user_id, payload)
    orchestrator = get_orchestrator()
    background_tasks.add_task(
        orchestrator.compute_forget_risk_for_task_bg,
        task.id,
        user_id,
    )
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    context_tag: str | None = Query(default=None),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return task_service.list_tasks(db, user_id, status_filter, context_tag)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return task_service.get_task(db, user_id, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    background_tasks: BackgroundTasks,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    task = task_service.update_task(db, user_id, task_id, payload)
    orchestrator = get_orchestrator()
    new_status = payload.model_dump(exclude_unset=True).get("status")
    if new_status is not None:
        background_tasks.add_task(
            orchestrator.on_task_updated_bg,
            task.id,
            user_id,
            new_status=new_status,
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    task_service.delete_task(db, user_id, task_id)


# --- Nested: task events ---


@router.post("/{task_id}/events", response_model=TaskEventRead, status_code=status.HTTP_201_CREATED)
def create_task_event(
    task_id: uuid.UUID,
    payload: TaskEventCreate,
    background_tasks: BackgroundTasks,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    event = task_event_service.create_task_event(db, user_id, task_id, payload)
    orchestrator = get_orchestrator()
    background_tasks.add_task(
        orchestrator.on_task_event_bg,
        event.id,
        task_id,
        user_id,
        event_type=payload.event_type,
    )
    return event


@router.get("/{task_id}/events", response_model=list[TaskEventRead])
def list_task_events(
    task_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return task_event_service.list_task_events(db, user_id, task_id)
