"""
Stage 8 — Analytics Table Population
======================================

Populates the existing `behaviour_metrics` table (which the backend already
reads via app/api/analytics.py) with pre-computed daily rollups so the
dashboard endpoints don't need to scan raw tables on every request.

Metrics persisted
------------------
Per user, per day (period_start = day start, period_end = day end):
  - daily_completion_rate     tasks completed / tasks resolved that day
  - daily_forgetting_rate     tasks forgotten / tasks resolved that day
  - daily_task_count          total tasks created that day
  - daily_interruption_count  total interruptions started that day
  - daily_friction_score      composite behavioural friction score (0-100)

Per user, per category (dimension = "category:<cat>"), overall period:
  - category_completion_rate
  - category_forgetting_rate
  - category_task_count

Per user, per location (dimension = "location:<id>"), overall period:
  - location_completion_rate
  - location_forgetting_rate
  - location_task_count

All writes are idempotent: existing rows for the same
(user_id, metric_name, dimension, period_start) are overwritten via the
unique constraint.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analytics.friction import compute_friction_score
from app.analytics.metrics import (
    task_completion_rate,
    task_forgetting_rate,
)
from app.database.base import Base
from app.database.session import engine, session_scope
from app.models.behaviour_metric import BehaviourMetric
from app.models.location import Location

logger = logging.getLogger(__name__)


RESOLVED_STATUSES = {"completed", "forgotten", "cancelled"}


def _day_bounds(dt: datetime) -> tuple[datetime, datetime]:
    """Return (start, end) of the UTC day containing `dt`."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    start = dt.astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    end = start + timedelta(days=1)
    return start, end


def _upsert_metric(db, user_id, metric_name: str, dimension: str,
                   period_start: datetime, period_end: datetime,
                   value: float, extra: dict | None = None) -> None:
    """Idempotently insert-or-update a BehaviourMetric row."""
    from sqlalchemy import select
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    row = {
        "user_id": user_id,
        "metric_name": metric_name,
        "dimension": dimension,
        "period_start": period_start,
        "period_end": period_end,
        "value": float(value),
        "extra": extra,
        "computed_at": datetime.now(timezone.utc),
    }

    if hasattr(engine.dialect, "name") and engine.dialect.name == "postgresql":
        stmt = pg_insert(BehaviourMetric).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "metric_name", "dimension", "period_start"],
            set_={"value": row["value"], "extra": row["extra"], "computed_at": row["computed_at"]},
        )
        db.execute(stmt)
    else:
        stmt = sqlite_insert(BehaviourMetric).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "metric_name", "dimension", "period_start"],
            set_={"value": row["value"], "extra": row["extra"], "computed_at": row["computed_at"]},
        )
        db.execute(stmt)


# ── daily rollups ────────────────────────────────────────────────────────────

def _populate_daily_metrics(db, tasks_df: pd.DataFrame, events_df: pd.DataFrame,
                            interruptions_df: pd.DataFrame, sessions_df: pd.DataFrame) -> int:
    """Compute and persist per-day metrics for every user."""
    written = 0
    if tasks_df.empty:
        return written

    if "user_id" not in tasks_df.columns:
        return written

    for user_id, user_tasks in tasks_df.groupby("user_id"):
        user_events = events_df[events_df["user_id"] == user_id] if not events_df.empty and "user_id" in events_df.columns else pd.DataFrame()
        user_interruptions = interruptions_df[interruptions_df["user_id"] == user_id] if not interruptions_df.empty and "user_id" in interruptions_df.columns else pd.DataFrame()
        user_sessions = sessions_df[sessions_df["user_id"] == user_id] if not sessions_df.empty and "user_id" in sessions_df.columns else pd.DataFrame()

        if "created_at" in user_tasks.columns:
            user_tasks = user_tasks.copy()
            user_tasks["_day"] = pd.to_datetime(user_tasks["created_at"], utc=True).dt.floor("D")
        else:
            continue

        for day_start, day_tasks in user_tasks.groupby("_day"):
            ps = day_start.to_pydatetime() if hasattr(day_start, "to_pydatetime") else day_start
            if ps.tzinfo is None:
                ps = ps.replace(tzinfo=timezone.utc)
            pe = ps + timedelta(days=1)

            day_created_count = len(day_tasks)
            day_resolved = day_tasks[day_tasks["status"].isin(RESOLVED_STATUSES)]
            day_completion = task_completion_rate(day_tasks) * 100.0 if len(day_resolved) > 0 else 0.0
            day_forgetting = task_forgetting_rate(day_tasks) * 100.0 if len(day_resolved) > 0 else 0.0

            day_start_ts = pd.Timestamp(ps)
            day_end_ts = pd.Timestamp(pe)
            day_int_count = 0
            if not user_interruptions.empty and "start_time" in user_interruptions.columns:
                int_start = pd.to_datetime(user_interruptions["start_time"], utc=True)
                day_int_count = int(((int_start >= day_start_ts) & (int_start < day_end_ts)).sum())

            day_sessions = pd.DataFrame()
            if not user_sessions.empty and "session_start" in user_sessions.columns:
                ss = pd.to_datetime(user_sessions["session_start"], utc=True)
                day_mask = (ss >= day_start_ts) & (ss < day_end_ts)
                day_sessions = user_sessions[day_mask]

            n_sessions = len(day_sessions)
            total_active_s = 0
            n_context_switches = 0
            avg_resume_delay = None
            if n_sessions > 0:
                total_active_s = float(
                    day_sessions["focused_time_seconds"].sum() + day_sessions["interruption_time_seconds"].sum()
                ) if "focused_time_seconds" in day_sessions.columns else 0.0
                n_context_switches = int(day_sessions["context_switch_count"].sum()) if "context_switch_count" in day_sessions.columns else 0
                if "resume_delay_seconds" in day_sessions.columns:
                    delays = day_sessions["resume_delay_seconds"].dropna()
                    if not delays.empty:
                        avg_resume_delay = float(delays.mean())

            friction = compute_friction_score(
                task_forgetting_rate=day_forgetting / 100.0,
                interruption_count=day_int_count,
                total_active_seconds=total_active_s,
                total_context_switches=n_context_switches,
                total_sessions=n_sessions,
                average_resume_delay_seconds=avg_resume_delay,
            )

            _upsert_metric(db, user_id, "daily_task_count", "overall", ps, pe, float(day_created_count))
            _upsert_metric(db, user_id, "daily_completion_rate", "overall", ps, pe, day_completion)
            _upsert_metric(db, user_id, "daily_forgetting_rate", "overall", ps, pe, day_forgetting)
            _upsert_metric(db, user_id, "daily_interruption_count", "overall", ps, pe, float(day_int_count))
            _upsert_metric(db, user_id, "daily_friction_score", "overall", ps, pe, friction["overall_score"], {
                "forgetting_score": friction["forgetting_score"],
                "interruption_score": friction["interruption_score"],
                "context_switch_score": friction["context_switch_score"],
                "recovery_score": friction["recovery_score"],
            })
            written += 5

    logger.info("populate_daily_metrics: wrote %d daily metric rows", written)
    return written


# ── category rollups ─────────────────────────────────────────────────────────

def _populate_category_metrics(db, tasks_df: pd.DataFrame, overall_start: datetime, overall_end: datetime) -> int:
    written = 0
    if tasks_df.empty or "user_id" not in tasks_df.columns or "category" not in tasks_df.columns:
        return written

    for user_id, user_tasks in tasks_df.groupby("user_id"):
        for category, cat_tasks in user_tasks.groupby("category"):
            cat_resolved = cat_tasks[cat_tasks["status"].isin(RESOLVED_STATUSES)]
            completion = task_completion_rate(cat_tasks) * 100.0 if len(cat_resolved) > 0 else 0.0
            forgetting = task_forgetting_rate(cat_tasks) * 100.0 if len(cat_resolved) > 0 else 0.0
            dimension = f"category:{category}"
            _upsert_metric(db, user_id, "category_completion_rate", dimension, overall_start, overall_end, completion, {"category": category, "task_count": len(cat_tasks)})
            _upsert_metric(db, user_id, "category_forgetting_rate", dimension, overall_start, overall_end, forgetting, {"category": category, "task_count": len(cat_resolved)})
            _upsert_metric(db, user_id, "category_task_count", dimension, overall_start, overall_end, float(len(cat_tasks)), {"category": category})
            written += 3

    logger.info("populate_category_metrics: wrote %d category metric rows", written)
    return written


# ── location rollups ─────────────────────────────────────────────────────────

def _populate_location_metrics(db, tasks_df: pd.DataFrame, locations_df: pd.DataFrame,
                               overall_start: datetime, overall_end: datetime) -> int:
    written = 0
    if tasks_df.empty or "user_id" not in tasks_df.columns or "location_id" not in tasks_df.columns:
        return written

    loc_label_map: dict = {}
    if not locations_df.empty and "id" in locations_df.columns:
        if "name" in locations_df.columns:
            loc_label_map = locations_df.set_index("id")["name"].to_dict()

    with_loc = tasks_df.dropna(subset=["location_id"])
    if with_loc.empty:
        return written

    for user_id, user_tasks in with_loc.groupby("user_id"):
        for location_id, loc_tasks in user_tasks.groupby("location_id"):
            loc_resolved = loc_tasks[loc_tasks["status"].isin(RESOLVED_STATUSES)]
            completion = task_completion_rate(loc_tasks) * 100.0 if len(loc_resolved) > 0 else 0.0
            forgetting = task_forgetting_rate(loc_tasks) * 100.0 if len(loc_resolved) > 0 else 0.0
            dimension = f"location:{location_id}"
            label = loc_label_map.get(location_id, str(location_id))
            extra = {"location_id": str(location_id), "location_name": label, "task_count": len(loc_tasks)}
            _upsert_metric(db, user_id, "location_completion_rate", dimension, overall_start, overall_end, completion, extra)
            _upsert_metric(db, user_id, "location_forgetting_rate", dimension, overall_start, overall_end, forgetting, extra)
            _upsert_metric(db, user_id, "location_task_count", dimension, overall_start, overall_end, float(len(loc_tasks)), extra)
            written += 3

    logger.info("populate_location_metrics: wrote %d location metric rows", written)
    return written


# ── public entrypoint ────────────────────────────────────────────────────────

def populate_analytics_tables(
    tasks_df: pd.DataFrame,
    events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    locations_df: pd.DataFrame | None = None,
) -> dict:
    """
    Compute + persist all analytics rollups into behaviour_metrics.

    Returns a dict with counts of rows written per dimension type.
    """
    locations_df = locations_df if locations_df is not None else pd.DataFrame()

    Base.metadata.create_all(bind=engine)

    overall_start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    overall_end = datetime.now(timezone.utc) + timedelta(days=1)
    if not tasks_df.empty and "created_at" in tasks_df.columns:
        ts = pd.to_datetime(tasks_df["created_at"], utc=True)
        overall_start = ts.min().to_pydatetime().replace(tzinfo=timezone.utc)
        overall_end = (ts.max() + pd.Timedelta(days=1)).to_pydatetime().replace(tzinfo=timezone.utc)

    with session_scope() as db:
        daily_written = _populate_daily_metrics(db, tasks_df, events_df, interruptions_df, sessions_df)
        cat_written = _populate_category_metrics(db, tasks_df, overall_start, overall_end)
        loc_written = _populate_location_metrics(db, tasks_df, locations_df, overall_start, overall_end)

    total = daily_written + cat_written + loc_written
    logger.info(
        "populate_analytics_tables: %d total rows written (daily=%d, category=%d, location=%d)",
        total, daily_written, cat_written, loc_written,
    )
    return {
        "daily_rows": daily_written,
        "category_rows": cat_written,
        "location_rows": loc_written,
        "total_rows": total,
    }
