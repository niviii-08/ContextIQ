"""
Behavioural Analytics
======================

Pure(ish) calculation functions over pandas DataFrames built from the raw
tables. Each public function documents exactly what it computes. Functions
degrade gracefully (return 0 / None / empty dict) on empty input rather
than raising, since a brand-new user will have no data yet.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.context_session import ContextSession
from app.models.interruption import Interruption
from app.models.location import Location
from app.models.task import Task, TaskStatus
from app.models.task_event import TaskEvent

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_tasks_df(db: DBSession, user_id, since: datetime | None = None) -> pd.DataFrame:
    stmt = select(Task).where(Task.user_id == user_id)
    if since is not None:
        stmt = stmt.where(Task.created_at >= since)
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return pd.DataFrame(
            columns=[
                "id", "location_id", "title", "category", "priority", "status",
                "deadline_at", "created_at", "started_at", "completed_at",
                "forgotten_at", "cancelled_at",
            ]
        )
    data = [
        {
            "id": t.id,
            "location_id": t.location_id,
            "title": t.title,
            "category": t.category,
            "priority": t.priority,
            "status": t.status.value if hasattr(t.status, "value") else t.status,
            "deadline_at": t.deadline_at,
            "created_at": t.created_at,
            "started_at": t.started_at,
            "completed_at": t.completed_at,
            "forgotten_at": t.forgotten_at,
            "cancelled_at": t.cancelled_at,
        }
        for t in rows
    ]
    return pd.DataFrame(data)


def load_interruptions_df(db: DBSession, user_id, since: datetime | None = None) -> pd.DataFrame:
    stmt = select(Interruption).where(Interruption.user_id == user_id)
    if since is not None:
        stmt = stmt.where(Interruption.start_time >= since)
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return pd.DataFrame(
            columns=["id", "task_id", "location_id", "interruption_type", "start_time", "end_time", "duration_seconds"]
        )
    data = [
        {
            "id": i.id,
            "task_id": i.task_id,
            "location_id": i.location_id,
            "interruption_type": i.interruption_type.value if hasattr(i.interruption_type, "value") else i.interruption_type,
            "start_time": i.start_time,
            "end_time": i.end_time,
            "duration_seconds": i.duration_seconds or 0,
        }
        for i in rows
    ]
    return pd.DataFrame(data)


def load_sessions_df(db: DBSession, user_id, since: datetime | None = None) -> pd.DataFrame:
    stmt = select(ContextSession).where(ContextSession.user_id == user_id)
    if since is not None:
        stmt = stmt.where(ContextSession.session_start >= since)
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return pd.DataFrame(
            columns=[
                "id", "task_id", "location_id", "session_start", "session_end",
                "focused_time_seconds", "interruption_time_seconds", "resume_delay_seconds",
                "context_switch_count", "interruption_count",
            ]
        )
    data = [
        {
            "id": s.id,
            "task_id": s.task_id,
            "location_id": s.location_id,
            "session_start": s.session_start,
            "session_end": s.session_end,
            "focused_time_seconds": s.focused_time_seconds,
            "interruption_time_seconds": s.interruption_time_seconds,
            "resume_delay_seconds": s.resume_delay_seconds,
            "context_switch_count": s.context_switch_count,
            "interruption_count": s.interruption_count,
        }
        for s in rows
    ]
    return pd.DataFrame(data)


def load_location_labels(db: DBSession, user_id) -> dict:
    rows = db.execute(select(Location).where(Location.user_id == user_id)).scalars().all()
    return {loc.id: loc.label for loc in rows}


# ---------------------------------------------------------------------------
# Task-level metrics
# ---------------------------------------------------------------------------

def task_completion_rate(tasks_df: pd.DataFrame) -> float:
    if tasks_df.empty:
        return 0.0
    resolved = tasks_df[tasks_df["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )]
    if resolved.empty:
        return 0.0
    completed = resolved[resolved["status"] == TaskStatus.COMPLETED.value]
    return round(len(completed) / len(resolved), 4)


def task_forgetting_rate(tasks_df: pd.DataFrame) -> float:
    if tasks_df.empty:
        return 0.0
    resolved = tasks_df[tasks_df["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )]
    if resolved.empty:
        return 0.0
    forgotten = resolved[resolved["status"] == TaskStatus.FORGOTTEN.value]
    return round(len(forgotten) / len(resolved), 4)


def average_task_duration_minutes(tasks_df: pd.DataFrame) -> float | None:
    completed = tasks_df[tasks_df["status"] == TaskStatus.COMPLETED.value].copy()
    completed = completed.dropna(subset=["started_at", "completed_at"])
    if completed.empty:
        return None
    durations = (completed["completed_at"] - completed["started_at"]).dt.total_seconds() / 60.0
    return round(float(durations.mean()), 2)


def average_task_delay_minutes(tasks_df: pd.DataFrame) -> float | None:
    """Average delay between a task's deadline and its actual completion
    time, for tasks that had a deadline. Positive = completed late.
    """
    with_deadline = tasks_df.dropna(subset=["deadline_at", "completed_at"]).copy()
    if with_deadline.empty:
        return None
    delays = (with_deadline["completed_at"] - with_deadline["deadline_at"]).dt.total_seconds() / 60.0
    return round(float(delays.mean()), 2)


def tasks_per_day(tasks_df: pd.DataFrame, period_days: int) -> float:
    if tasks_df.empty or period_days <= 0:
        return 0.0
    return round(len(tasks_df) / period_days, 3)


def tasks_per_category(tasks_df: pd.DataFrame) -> dict:
    if tasks_df.empty:
        return {}
    return tasks_df["category"].value_counts().to_dict()


def tasks_per_location(tasks_df: pd.DataFrame, location_labels: dict) -> dict:
    if tasks_df.empty:
        return {}
    counts = tasks_df["location_id"].value_counts(dropna=True)
    return {location_labels.get(loc_id, str(loc_id)): int(c) for loc_id, c in counts.items()}


def _weekday_hour_rate(df: pd.DataFrame, time_col: str, status_col_value: str, status_series: pd.Series, by: str) -> dict:
    """Generic helper: rate of `status_col_value` among tasks resolved,
    grouped by weekday name or hour-of-day, based on `time_col`.
    """
    resolved = df.dropna(subset=[time_col]).copy()
    if resolved.empty:
        return {}
    if by == "weekday":
        resolved["bucket"] = resolved[time_col].dt.day_name()
    else:
        resolved["bucket"] = resolved[time_col].dt.hour.astype(str)

    grouped = resolved.groupby("bucket").apply(
        lambda g: (g["status"] == status_col_value).sum() / len(g) if len(g) else 0.0, include_groups=False
    )
    return {k: round(float(v), 4) for k, v in grouped.to_dict().items()}


def forgetting_by_weekday(tasks_df: pd.DataFrame) -> dict:
    resolved = tasks_df[tasks_df["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )].copy()
    if resolved.empty:
        return {}
    resolved["ref_time"] = resolved["created_at"]
    return _weekday_hour_rate(resolved, "ref_time", TaskStatus.FORGOTTEN.value, resolved["status"], "weekday")


def forgetting_by_hour(tasks_df: pd.DataFrame) -> dict:
    resolved = tasks_df[tasks_df["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )].copy()
    if resolved.empty:
        return {}
    resolved["ref_time"] = resolved["created_at"]
    return _weekday_hour_rate(resolved, "ref_time", TaskStatus.FORGOTTEN.value, resolved["status"], "hour")


def forgetting_by_category(tasks_df: pd.DataFrame) -> dict:
    resolved = tasks_df[tasks_df["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )]
    if resolved.empty:
        return {}
    grouped = resolved.groupby("category").apply(
        lambda g: (g["status"] == TaskStatus.FORGOTTEN.value).sum() / len(g), include_groups=False
    )
    return {k: round(float(v), 4) for k, v in grouped.to_dict().items()}


def forgetting_by_location(tasks_df: pd.DataFrame, location_labels: dict) -> dict:
    resolved = tasks_df[tasks_df["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )].dropna(subset=["location_id"])
    if resolved.empty:
        return {}
    grouped = resolved.groupby("location_id").apply(
        lambda g: (g["status"] == TaskStatus.FORGOTTEN.value).sum() / len(g), include_groups=False
    )
    return {location_labels.get(loc_id, str(loc_id)): round(float(v), 4) for loc_id, v in grouped.to_dict().items()}


# ---------------------------------------------------------------------------
# Interruption-level metrics
# ---------------------------------------------------------------------------

def interruption_count(interruptions_df: pd.DataFrame) -> int:
    return int(len(interruptions_df))


def interruption_duration_minutes_total(interruptions_df: pd.DataFrame) -> float:
    if interruptions_df.empty:
        return 0.0
    return round(float(interruptions_df["duration_seconds"].sum()) / 60.0, 2)


def interruption_duration_minutes_avg(interruptions_df: pd.DataFrame) -> float | None:
    if interruptions_df.empty:
        return None
    return round(float(interruptions_df["duration_seconds"].mean()) / 60.0, 2)


def interruption_by_weekday(interruptions_df: pd.DataFrame) -> dict:
    if interruptions_df.empty:
        return {}
    s = interruptions_df["start_time"].dt.day_name().value_counts()
    return s.to_dict()


def interruption_by_hour(interruptions_df: pd.DataFrame) -> dict:
    if interruptions_df.empty:
        return {}
    s = interruptions_df["start_time"].dt.hour.astype(str).value_counts()
    return s.to_dict()


def interruption_by_category(interruptions_df: pd.DataFrame) -> dict:
    if interruptions_df.empty:
        return {}
    return interruptions_df["interruption_type"].value_counts().to_dict()


# ---------------------------------------------------------------------------
# Context-session-level metrics
# ---------------------------------------------------------------------------

def average_focus_session_minutes(sessions_df: pd.DataFrame) -> float | None:
    if sessions_df.empty:
        return None
    return round(float(sessions_df["focused_time_seconds"].mean()) / 60.0, 2)


def total_context_switches(sessions_df: pd.DataFrame) -> int:
    if sessions_df.empty:
        return 0
    return int(sessions_df["context_switch_count"].sum())


def resume_count(sessions_df: pd.DataFrame) -> int:
    if sessions_df.empty:
        return 0
    return int(sessions_df["resume_delay_seconds"].notna().sum())


def pause_count(db_events_df: pd.DataFrame) -> int:
    if db_events_df.empty:
        return 0
    return int((db_events_df["event_type"] == "paused").sum())


def average_resume_delay_seconds(sessions_df: pd.DataFrame) -> float | None:
    if sessions_df.empty:
        return None
    delays = sessions_df["resume_delay_seconds"].dropna()
    if delays.empty:
        return None
    return round(float(delays.mean()), 2)


def context_switching_by_task_category(sessions_df: pd.DataFrame, tasks_df: pd.DataFrame) -> dict:
    if sessions_df.empty or tasks_df.empty:
        return {}
    merged = sessions_df.merge(tasks_df[["id", "category"]], left_on="task_id", right_on="id", how="left")
    grouped = merged.groupby("category")["context_switch_count"].sum()
    return {k: int(v) for k, v in grouped.to_dict().items()}


def context_switching_by_location(sessions_df: pd.DataFrame, location_labels: dict) -> dict:
    if sessions_df.empty:
        return {}
    grouped = sessions_df.dropna(subset=["location_id"]).groupby("location_id")["context_switch_count"].sum()
    return {location_labels.get(loc_id, str(loc_id)): int(v) for loc_id, v in grouped.to_dict().items()}


def load_events_df(db: DBSession, user_id, since: datetime | None = None) -> pd.DataFrame:
    stmt = select(TaskEvent).where(TaskEvent.user_id == user_id)
    if since is not None:
        stmt = stmt.where(TaskEvent.event_time >= since)
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return pd.DataFrame(columns=["id", "task_id", "event_type", "event_time"])
    data = [
        {
            "id": e.id,
            "task_id": e.task_id,
            "event_type": e.event_type.value if hasattr(e.event_type, "value") else e.event_type,
            "event_time": e.event_time,
        }
        for e in rows
    ]
    return pd.DataFrame(data)
