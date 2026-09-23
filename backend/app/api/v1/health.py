from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Liveness + DB connectivity check."""
    settings = get_settings()
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
        logger.exception("Health database probe failed")

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "time": datetime.now(timezone.utc).isoformat(),
        "database": {"connected": db_ok},
    }


@router.get("/live")
def liveness():
    return {"status": "ok"}
