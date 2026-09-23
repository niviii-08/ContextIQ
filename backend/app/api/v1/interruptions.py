import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.interruption import InterruptionCreate, InterruptionRead
from app.services import interruption_service

router = APIRouter(prefix="/interruptions", tags=["interruptions"])


@router.post("", response_model=InterruptionRead, status_code=status.HTTP_201_CREATED)
def create_interruption(
    payload: InterruptionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return interruption_service.create_interruption(db, user_id, payload)


@router.get("", response_model=list[InterruptionRead])
def list_interruptions(
    task_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return interruption_service.list_interruptions(db, user_id, task_id)


@router.get("/{interruption_id}", response_model=InterruptionRead)
def get_interruption(
    interruption_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return interruption_service.get_interruption(db, user_id, interruption_id)


@router.delete("/{interruption_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interruption(
    interruption_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    interruption_service.delete_interruption(db, user_id, interruption_id)
