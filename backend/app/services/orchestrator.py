"""
Backend Orchestrator — triggers downstream service processing after task events.

Flow:
    Task Created/Updated/Completed
        → Orchestrator
            → POST forgetting-ml:8000/api/v1/predictions/forgetting  (update forget risks)
            → [expandable: data-engine / context-engine / intelligence endpoints]
        → Write results to Prediction / BehaviourMetric / Recommendation tables
        → Frontend sees live data via poll/WebSocket (Phase 2)

All orchestrator calls are best-effort: a failure in any downstream service is
logged as a warning but never raises into the user-facing HTTP path (the
orchestrator runs inside FastAPI BackgroundTasks after the response is sent).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import PredictionType, TaskEventType, TaskStatus
from app.models.location import Location
from app.models.prediction import Prediction
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.models.interruption import Interruption
from app.models.context_session import ContextSession

logger = logging.getLogger(__name__)

settings = get_settings()

# Heuristic mapping from free-form user context_tag strings to the ML
# model's CATEGORY_DOMAIN. Unknown tags fall back to "Personal".
_TAG_TO_CATEGORY: dict[str, str] = {
    "academic": "Academic",
    "study": "Academic",
    "homework": "Academic",
    "school": "Academic",
    "work": "Work",
    "office": "Work",
    "job": "Work",
    "personal": "Personal",
    "errand": "Personal",
    "errands": "Personal",
    "health": "Health",
    "gym": "Health",
    "medical": "Health",
    "doctor": "Health",
    "workout": "Health",
    "household": "Household",
    "home": "Household",
    "chore": "Household",
    "chores": "Household",
    "cleaning": "Household",
    "social": "Social",
    "friend": "Social",
    "family": "Social",
    "finance": "Finance",
    "bill": "Finance",
    "bills": "Finance",
    "money": "Finance",
    "tax": "Finance",
}

# Map from backend LocationType enum → ML LOCATION_DOMAIN
_LOCATION_TYPE_TO_ML: dict[str, str] = {
    "HOME": "Home",
    "WORK": "Office",
    "GYM": "Gym",
    "COMMUTE": "Commute",
    "STUDY": "Campus",
    "OTHER": "Other",
}


def _map_task_category(task: Task) -> str:
    tag = (task.context_tag or "").strip().lower()
    if tag in _TAG_TO_CATEGORY:
        return _TAG_TO_CATEGORY[tag]
    for key, value in _TAG_TO_CATEGORY.items():
        if key in tag:
            return value
    return "Personal"


def _map_priority(priority: Any) -> str:
    raw = str(priority).upper()
    if raw in {"LOW", "MEDIUM", "HIGH"}:
        return raw
    return "MEDIUM"


def _map_location(db: Session, task: Task) -> str:
    if task.context_location_id:
        loc = db.get(Location, task.context_location_id)
        if loc is not None:
            return _LOCATION_TYPE_TO_ML.get(str(loc.location_type), "Other")
    tag = (task.context_tag or "").strip().lower()
    if "home" in tag:
        return "Home"
    if "work" in tag or "office" in tag:
        return "Office"
    if "gym" in tag or "workout" in tag:
        return "Gym"
    if "commute" in tag or "travel" in tag:
        return "Commute"
    if "study" in tag or "school" in tag or "campus" in tag:
        return "Campus"
    return "Other"


def _count_tasks_since(db: Session, user_id: uuid.UUID, since: datetime, status: TaskStatus | None = None) -> int:
    stmt = select(Task).where(Task.user_id == user_id, Task.created_at >= since)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    return len(list(db.scalars(stmt).all()))


def _build_task_features(db: Session, task: Task) -> dict[str, Any]:
    """Best-effort construction of a TaskFeatures dict for the forgetting-ML endpoint.

    Falls back to sensible defaults when the user has no history yet, so the
    prediction call still succeeds even for a brand-new user's very first task.
    """
    now = datetime.now(timezone.utc)
    created = task.created_at or now

    weekday = created.weekday()  # 0=Monday ... 6=Sunday
    hour = created.hour

    if task.due_at is not None:
        delta = task.due_at - now
        deadline_distance_hours = max(0.0, delta.total_seconds() / 3600.0)
    else:
        deadline_distance_hours = 72.0  # default: ~3 days away

    # Historical aggregates for the user
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)

    prev_completed = _count_tasks_since(db, task.user_id, thirty_days_ago, TaskStatus.COMPLETED)
    prev_forgotten = _count_tasks_since(db, task.user_id, thirty_days_ago, TaskStatus.FORGOTTEN)
    prev_total = prev_completed + prev_forgotten
    if prev_total > 0:
        historical_completion_rate = prev_completed / prev_total
        historical_forgetting_rate = prev_forgotten / prev_total
    else:
        historical_completion_rate = 0.6
        historical_forgetting_rate = 0.2

    # How many other tasks share this task's (approximate) category in the last 30d?
    same_tag_count_stmt = (
        select(Task)
        .where(Task.user_id == task.user_id, Task.created_at >= thirty_days_ago)
    )
    same_tag = [t for t in db.scalars(same_tag_count_stmt).all() if t.context_tag == task.context_tag and task.context_tag]
    if prev_total > 0:
        task_frequency = min(1.0, len(same_tag) / prev_total)
    else:
        task_frequency = 0.0

    tasks_today = _count_tasks_since(db, task.user_id, start_of_day)

    interruptions_today = len(list(db.scalars(
        select(Interruption).where(
            Interruption.user_id == task.user_id,
            Interruption.occurred_at >= start_of_day,
        )
    ).all()))

    recent_switches_stmt = (
        select(ContextSession)
        .where(
            ContextSession.user_id == task.user_id,
            ContextSession.started_at >= now - timedelta(hours=6),
        )
    )
    recent_context_switches = sum(
        int(getattr(s, "context_switch_count", 0) or 0)
        for s in db.scalars(recent_switches_stmt).all()
    )

    # Averages over last 30 sessions
    sessions_stmt = (
        select(ContextSession)
        .where(ContextSession.user_id == task.user_id)
        .order_by(ContextSession.started_at.desc())
        .limit(30)
    )
    recent_sessions = list(db.scalars(sessions_stmt).all())
    session_focused_seconds = [
        float(getattr(s, "focused_time_seconds", 0) or 0)
        for s in recent_sessions
        if (getattr(s, "focused_time_seconds", 0) or 0) > 0
    ]
    avg_session_duration = (
        (sum(session_focused_seconds) / len(session_focused_seconds)) / 60.0
        if session_focused_seconds
        else 20.0
    )

    avg_interruption_duration_minutes: float = 10.0
    if recent_sessions:
        total_int_secs = sum(float(getattr(s, "interruption_time_seconds", 0) or 0) for s in recent_sessions)
        total_int_count = max(1, sum(int(getattr(s, "interruption_count", 0) or 0) for s in recent_sessions))
        if total_int_count > 0:
            avg_interruption_duration_minutes = max(0.0, (total_int_secs / total_int_count) / 60.0)

    return {
        "task_id": str(task.id),
        "task_category": _map_task_category(task),
        "priority": _map_priority(task.priority),
        "location": _map_location(db, task),
        "weekday": weekday,
        "hour": hour,
        "deadline_distance_hours": deadline_distance_hours,
        "previous_completion_count": prev_completed,
        "previous_forgetting_count": prev_forgotten,
        "historical_completion_rate": historical_completion_rate,
        "historical_forgetting_rate": historical_forgetting_rate,
        "task_frequency": task_frequency,
        "tasks_today": tasks_today,
        "interruptions_today": interruptions_today,
        "recent_context_switches": recent_context_switches,
        "avg_interruption_duration": avg_interruption_duration_minutes,
        "avg_session_duration": avg_session_duration,
    }


def _expire_previous_predictions(db: Session, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(Prediction)
        .where(
            Prediction.task_id == task_id,
            Prediction.user_id == user_id,
            Prediction.prediction_type == PredictionType.FORGET_RISK,
            Prediction.valid_until.is_(None),
        )
    )
    for prior in db.scalars(stmt).all():
        prior.valid_until = now
        db.add(prior)


def _store_prediction(
    db: Session,
    *,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    ml_response: dict[str, Any],
    raw_features: dict[str, Any],
) -> Prediction:
    """Persist a single prediction response, keeping the append-only contract.

    Expires any currently-valid prior FORGET_RISK prediction for the same task
    so that the "latest valid" view over predictions is a row with
    valid_until IS NULL.
    """
    probability = float(ml_response.get("prediction_probability", 0.0))
    probability = max(0.0, min(1.0, probability))
    risk_level = str(ml_response.get("risk_level", "LOW"))
    model_version = str(ml_response.get("model_version", "unknown"))
    top_features = list(ml_response.get("top_features", []) or [])

    _expire_previous_predictions(db, task_id, user_id)

    predicted_value: dict[str, Any] = {
        "taskTitle": raw_features.get("task_id"),
        "risk_probability": probability,
        "risk_level": risk_level,
        "reasons": [
            {
                "feature": feat,
                "impact": 0.1,
                "description": f"Contributing factor: {feat}",
            }
            for feat in top_features[:3]
        ],
        "features_used": raw_features,
    }

    prediction = Prediction(
        user_id=user_id,
        task_id=task_id,
        prediction_type=PredictionType.FORGET_RISK,
        predicted_value=predicted_value,
        confidence=probability,
        model_version=model_version,
        valid_from=datetime.now(timezone.utc),
        valid_until=None,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    logger.info(
        "orchestrator: forget-risk prediction stored task_id=%s p=%.2f model=%s",
        task_id,
        probability,
        model_version,
    )
    return prediction


class Orchestrator:
    """Coordinates downstream service calls after task lifecycle events.

    Intended usage:
        orchestrator = Orchestrator()
        # ... inside a request handler after task_service.create_task(...) ...
        background_tasks.add_task(orchestrator.compute_forget_risk_for_task_bg, task.id, user_id)
    """

    def __init__(self) -> None:
        self._timeout = settings.ORCHESTRATOR_TIMEOUT_SECONDS
        self._retry_attempts = max(1, int(settings.ORCHESTRATOR_RETRY_ATTEMPTS))
        self._ml_base = settings.FORGETTING_ML_URL.rstrip("/")
        self._data_engine_base = settings.DATA_ENGINE_URL.rstrip("/")
        self._context_engine_base = settings.CONTEXT_ENGINE_URL.rstrip("/")
        self._intelligence_base = settings.INTELLIGENCE_URL.rstrip("/")

    # ---------- Public async entry points ----------

    async def compute_forget_risk_for_task(self, task_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> None:
        """Compute + persist a forget-risk prediction for a single task.

        Any HTTP / ML / DB errors are swallowed and logged as warnings so this
        never breaks the call site.
        """
        try:
            task = db.get(Task, task_id)
            if task is None:
                logger.warning("orchestrator: task %s not found, skipping forget-risk compute", task_id)
                return
            if task.user_id != user_id:
                logger.warning(
                    "orchestrator: user_id mismatch task=%s user=%s owner=%s",
                    task_id,
                    user_id,
                    task.user_id,
                )
                return

            features = _build_task_features(db, task)
            prediction_payload = await self._call_forgetting_ml(features)
            if prediction_payload is None:
                return

            _store_prediction(
                db,
                task_id=task_id,
                user_id=user_id,
                ml_response=prediction_payload,
                raw_features=features,
            )
        except Exception as exc:  # pragma: no cover - best-effort catch-all
            logger.warning(
                "orchestrator: forget-risk prediction failed task_id=%s error=%s",
                task_id,
                exc,
                exc_info=True,
            )

    async def on_task_created(self, task_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> None:
        await self.compute_forget_risk_for_task(task_id, user_id, db)

    async def on_task_updated(self, task_id: uuid.UUID, user_id: uuid.UUID, db: Session, *, new_status: Any = None) -> None:
        terminal = {TaskStatus.COMPLETED, TaskStatus.FORGOTTEN, TaskStatus.CANCELLED}
        if new_status in terminal:
            await self.compute_forget_risk_for_task(task_id, user_id, db)

    async def on_task_event(
        self,
        event_id: uuid.UUID,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        db: Session,
        *,
        event_type: Any = None,
    ) -> None:
        terminal_events = {TaskEventType.COMPLETED, TaskEventType.FORGOTTEN, TaskEventType.CANCELLED}
        if event_type in terminal_events:
            await self.compute_forget_risk_for_task(task_id, user_id, db)

    # ---------- Background-task wrappers (open a fresh DB session) ----------

    def compute_forget_risk_for_task_bg(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Sync wrapper suitable for FastAPI BackgroundTasks.

        Opens its own DB session (the request-scoped session may be closed
        after the HTTP response finishes) and drives the async orchestrator
        using asyncio.run().
        """
        import asyncio

        db = SessionLocal()
        try:
            asyncio.run(self.compute_forget_risk_for_task(task_id, user_id, db))
        finally:
            db.close()

    def on_task_updated_bg(self, task_id: uuid.UUID, user_id: uuid.UUID, *, new_status: Any = None) -> None:
        import asyncio

        db = SessionLocal()
        try:
            asyncio.run(self.on_task_updated(task_id, user_id, db, new_status=new_status))
        finally:
            db.close()

    def on_task_event_bg(
        self,
        event_id: uuid.UUID,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        event_type: Any = None,
    ) -> None:
        import asyncio

        db = SessionLocal()
        try:
            asyncio.run(self.on_task_event(event_id, task_id, user_id, db, event_type=event_type))
        finally:
            db.close()

    # ---------- Downstream HTTP calls ----------

    async def _call_forgetting_ml(self, features: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self._ml_base}/api/v1/predictions/forgetting"
        last_error: Exception | None = None
        for attempt in range(1, self._retry_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=features)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(
                            "orchestrator: forgetting-ml response attempt=%s p=%s level=%s",
                            attempt,
                            data.get("prediction_probability"),
                            data.get("risk_level"),
                        )
                        return data
                    logger.warning(
                        "orchestrator: forgetting-ml attempt=%s non-200 status=%s body=%s",
                        attempt,
                        response.status_code,
                        response.text[:500],
                    )
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                logger.warning(
                    "orchestrator: forgetting-ml attempt=%s transport error: %s",
                    attempt,
                    exc,
                )
        logger.warning(
            "orchestrator: forgetting-ml failed after %s attempts url=%s last_error=%s",
            self._retry_attempts,
            url,
            last_error,
        )
        return None


# Convenience singleton so callers don't need to manage their own instance.
_orchestrator_instance: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator()
    return _orchestrator_instance
