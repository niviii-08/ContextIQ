from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.services.session_engine import rebuild_sessions_for_user

router = APIRouter(prefix="/context-sessions", tags=["context-sessions"])


@router.post("/rebuild")
def rebuild_sessions(user_id: UUID, db: Session = Depends(get_db)):
    """Recompute all ContextSession rows for a user from raw task_events +
    interruptions. Safe to call repeatedly (idempotent full rebuild).

    Call this after ingesting a batch of events/interruptions and before
    querying /analytics/context or /analytics/friction, so those endpoints
    reflect the latest activity.
    """
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    count = rebuild_sessions_for_user(db, user_id)
    return {"user_id": str(user_id), "sessions_created": count}
