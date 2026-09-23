import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


def create_location(db: Session, user_id: uuid.UUID, payload: LocationCreate) -> Location:
    location = Location(user_id=user_id, **payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def list_locations(db: Session, user_id: uuid.UUID, active_only: bool = False) -> list[Location]:
    stmt = select(Location).where(Location.user_id == user_id)
    if active_only:
        stmt = stmt.where(Location.is_active.is_(True))
    stmt = stmt.order_by(Location.created_at.desc())
    return list(db.scalars(stmt).all())


def get_location(db: Session, user_id: uuid.UUID, location_id: uuid.UUID) -> Location:
    location = db.scalar(
        select(Location).where(Location.id == location_id, Location.user_id == user_id)
    )
    if location is None:
        raise NotFoundError("Location not found.")
    return location


def update_location(
    db: Session, user_id: uuid.UUID, location_id: uuid.UUID, payload: LocationUpdate
) -> Location:
    location = get_location(db, user_id, location_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, user_id: uuid.UUID, location_id: uuid.UUID) -> None:
    location = get_location(db, user_id, location_id)
    db.delete(location)
    db.commit()
