import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.schemas.location import LocationCreate, LocationRead, LocationUpdate
from app.services import location_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return location_service.create_location(db, user_id, payload)


@router.get("", response_model=list[LocationRead])
def list_locations(
    active_only: bool = Query(default=False),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return location_service.list_locations(db, user_id, active_only)


@router.get("/{location_id}", response_model=LocationRead)
def get_location(
    location_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return location_service.get_location(db, user_id, location_id)


@router.patch("/{location_id}", response_model=LocationRead)
def update_location(
    location_id: uuid.UUID,
    payload: LocationUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return location_service.update_location(db, user_id, location_id, payload)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    location_service.delete_location(db, user_id, location_id)
