from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.location import Location
from app.models.task import Task, TaskStatus
from app.models.task_event import TaskEvent, TaskEventType
from app.models.interruption import Interruption
from app.models.user import User
from app.schemas.common import UserCreate, UserRead, LocationCreate, LocationRead
from app.schemas.task import TaskCreate, TaskRead, TaskEventCreate, TaskEventRead
from app.schemas.interruption import InterruptionCreate, InterruptionRead

router = APIRouter(tags=["ingestion"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- Users -------------------------------------------------------------

@router.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists.")
    user = User(email=payload.email, display_name=payload.display_name, timezone=payload.timezone)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# --- Locations -----------------------------------------------------------

@router.post("/locations", response_model=LocationRead, status_code=201)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    location = Location(
        user_id=payload.user_id, label=payload.label, latitude=payload.latitude, longitude=payload.longitude
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


# --- Tasks -----------------------------------------------------------------

@router.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    created_at = payload.created_at or _now()
    task = Task(
        user_id=payload.user_id,
        title=payload.title,
        category=payload.category,
        priority=payload.priority,
        location_id=payload.location_id,
        deadline_at=payload.deadline_at,
        status=TaskStatus.CREATED,
        created_at=created_at,
    )
    db.add(task)
    db.flush()  # get task.id before creating the event

    event = TaskEvent(
        user_id=payload.user_id,
        task_id=task.id,
        location_id=payload.location_id,
        event_type=TaskEventType.CREATED,
        event_time=created_at,
    )
    db.add(event)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# --- Task events -------------------------------------------------------

_EVENT_TO_STATUS = {
    TaskEventType.CREATED: TaskStatus.CREATED,
    TaskEventType.STARTED: TaskStatus.STARTED,
    TaskEventType.PAUSED: TaskStatus.PAUSED,
    TaskEventType.RESUMED: TaskStatus.RESUMED,
    TaskEventType.COMPLETED: TaskStatus.COMPLETED,
    TaskEventType.FORGOTTEN: TaskStatus.FORGOTTEN,
    TaskEventType.CANCELLED: TaskStatus.CANCELLED,
}


@router.post("/task-events", response_model=TaskEventRead, status_code=201)
def create_task_event(payload: TaskEventCreate, db: Session = Depends(get_db)):
    task = db.get(Task, payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != payload.user_id:
        raise HTTPException(status_code=400, detail="task_id does not belong to user_id")

    event = TaskEvent(
        user_id=payload.user_id,
        task_id=payload.task_id,
        location_id=payload.location_id,
        event_type=payload.event_type,
        event_time=payload.event_time,
        event_metadata=payload.event_metadata,
    )
    db.add(event)

    # Update denormalized task status/timestamps for fast reads.
    new_status = _EVENT_TO_STATUS.get(payload.event_type)
    if new_status:
        task.status = new_status
    if payload.event_type == TaskEventType.STARTED and not task.started_at:
        task.started_at = payload.event_time
    elif payload.event_type == TaskEventType.COMPLETED:
        task.completed_at = payload.event_time
    elif payload.event_type == TaskEventType.FORGOTTEN:
        task.forgotten_at = payload.event_time
    elif payload.event_type == TaskEventType.CANCELLED:
        task.cancelled_at = payload.event_time

    db.commit()
    db.refresh(event)
    return event


# --- Interruptions -------------------------------------------------------

@router.post("/interruptions", response_model=InterruptionRead, status_code=201)
def create_interruption(payload: InterruptionCreate, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if payload.task_id and not db.get(Task, payload.task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    interruption = Interruption(
        user_id=payload.user_id,
        task_id=payload.task_id,
        location_id=payload.location_id,
        interruption_type=payload.interruption_type,
        source_label=payload.source_label,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_seconds=payload.duration_seconds,
    )
    db.add(interruption)
    db.commit()
    db.refresh(interruption)
    return interruption
