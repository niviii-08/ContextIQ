"""
Feature Engine
===============

ML-ready feature generation, designed to be consumed by an independent
downstream ML module (forgetting-prediction model, association-rule
mining, recommendations, etc.) — see the INTEGRATION CONTRACT in the
README for the exact interface contract.

CRITICAL — TEMPORAL LEAKAGE PREVENTION
----------------------------------------
Every function in this module takes an explicit `as_of` timestamp
(the "prediction time") and MUST only use rows whose relevant timestamp
is strictly BEFORE `as_of`. This is enforced consistently:

  - Task rows are filtered on `created_at < as_of`.
  - Event rows are filtered on `event_time < as_of`.
  - Interruption rows are filtered on `start_time < as_of`.

This guarantees that features computed "as of" a given task's creation
time can be safely used to predict what happens to THAT task, without
peeking at its own outcome or at any data that only exists in the future
relative to the prediction point. Callers building a training dataset
should call `generate_task_features(..., as_of=task.created_at)` for
each historical task, which naturally reproduces the exact information
horizon a live/production prediction would have.

All functions are pure: given a DataFrame of historical data and an
`as_of` cutoff, they return a plain dict of scalar features. No function
in this module performs I/O; callers (e.g. app/api/analytics or a
training script) are responsible for loading DataFrames via
app/analytics/metrics.py's `load_*_df` helpers first.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from app.models.task import TaskStatus


def _align_tz(df: pd.DataFrame, col: str, as_of: datetime) -> datetime:
    """SQLite (used for local dev) does not round-trip timezone-aware
    datetimes — SQLAlchemy reads them back as naive. PostgreSQL does
    preserve tz-awareness. To keep this module correct on BOTH backends,
    normalize `as_of` to match whatever tz-awareness the loaded column
    actually has, rather than assuming one or the other.
    """
    if df.empty or col not in df.columns:
        return as_of
    series = df[col]
    if not pd.api.types.is_datetime64_any_dtype(series):
        return as_of
    column_is_aware = getattr(series.dt, "tz", None) is not None
    as_of_is_aware = as_of.tzinfo is not None
    if column_is_aware and not as_of_is_aware:
        return as_of.replace(tzinfo=timezone.utc)
    if not column_is_aware and as_of_is_aware:
        return as_of.astimezone(timezone.utc).replace(tzinfo=None)
    return as_of


def _before(df: pd.DataFrame, col: str, as_of: datetime) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df
    aligned = _align_tz(df, col, as_of)
    return df[df[col] < aligned]


# ---------------------------------------------------------------------------
# Task-level features
# ---------------------------------------------------------------------------

def generate_task_features(
    *,
    task_row: dict,
    tasks_df: pd.DataFrame,
    events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    as_of: datetime,
) -> dict:
    """Generate features for a single task, as of `as_of` (typically the
    task's own `created_at`, so the model sees only what was knowable at
    the moment the task was created).

    `task_row` is a dict-like with at least: category, location_id,
    priority, deadline_at, created_at.
    """
    history = _before(tasks_df, "created_at", as_of)
    resolved_history = history[history["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )]

    category = task_row.get("category")
    location_id = task_row.get("location_id")
    weekday = as_of.strftime("%A")
    hour = as_of.hour

    features = {
        "previous_forgetting_count": _count_status(resolved_history, TaskStatus.FORGOTTEN.value),
        "previous_completion_count": _count_status(resolved_history, TaskStatus.COMPLETED.value),
        "completion_rate": _rate_status(resolved_history, TaskStatus.COMPLETED.value),
        "category_forgetting_rate": _rate_status(
            resolved_history[resolved_history["category"] == category], TaskStatus.FORGOTTEN.value
        ),
        "location_forgetting_rate": (
            _rate_status(resolved_history[resolved_history["location_id"] == location_id], TaskStatus.FORGOTTEN.value)
            if location_id is not None
            else None
        ),
        "weekday_forgetting_rate": _rate_status_by_time_bucket(resolved_history, "weekday", weekday),
        "hour_forgetting_rate": _rate_status_by_time_bucket(resolved_history, "hour", hour),
        "task_frequency": _task_frequency(history, category),
        "days_since_last_similar_task": _days_since_last_similar(history, category, as_of),
        "deadline_distance_hours": _deadline_distance_hours(task_row, as_of),
        "priority": task_row.get("priority"),
        "tasks_today": _tasks_in_window(history, as_of, timedelta(hours=24)),
        "interruptions_today": _interruptions_in_window(interruptions_df, as_of, timedelta(hours=24)),
        "recent_context_switches": _recent_context_switches(events_df, as_of, timedelta(hours=24)),
        "average_interruption_duration_seconds": _average_interruption_duration(interruptions_df, as_of),
    }
    return features


def _count_status(df: pd.DataFrame, status_value: str) -> int:
    if df.empty:
        return 0
    return int((df["status"] == status_value).sum())


def _rate_status(df: pd.DataFrame, status_value: str) -> float | None:
    if df.empty:
        return None
    return round(float((df["status"] == status_value).sum() / len(df)), 4)


def _rate_status_by_time_bucket(df: pd.DataFrame, bucket_type: str, bucket_value) -> float | None:
    if df.empty:
        return None
    d = df.copy()
    if bucket_type == "weekday":
        d["bucket"] = d["created_at"].dt.day_name()
    else:
        d["bucket"] = d["created_at"].dt.hour
    subset = d[d["bucket"] == bucket_value]
    if subset.empty:
        return None
    return round(float((subset["status"] == TaskStatus.FORGOTTEN.value).sum() / len(subset)), 4)


def _task_frequency(df: pd.DataFrame, category: str) -> int:
    if df.empty:
        return 0
    return int((df["category"] == category).sum())


def _days_since_last_similar(df: pd.DataFrame, category: str, as_of: datetime) -> float | None:
    if df.empty:
        return None
    same_cat = df[df["category"] == category]
    if same_cat.empty:
        return None
    last = same_cat["created_at"].max()
    aligned_as_of = as_of
    last_is_aware = getattr(last, "tzinfo", None) is not None
    as_of_is_aware = as_of.tzinfo is not None
    if last_is_aware and not as_of_is_aware:
        aligned_as_of = as_of.replace(tzinfo=timezone.utc)
    elif not last_is_aware and as_of_is_aware:
        aligned_as_of = as_of.astimezone(timezone.utc).replace(tzinfo=None)
    return round((aligned_as_of - last).total_seconds() / 86400.0, 3)


def _deadline_distance_hours(task_row: dict, as_of: datetime) -> float | None:
    deadline = task_row.get("deadline_at")
    if deadline is None or pd.isna(deadline):
        return None
    deadline_aware = getattr(deadline, "tzinfo", None) is not None
    as_of_aware = as_of.tzinfo is not None
    if deadline_aware and not as_of_aware:
        as_of = as_of.replace(tzinfo=timezone.utc)
    elif not deadline_aware and as_of_aware:
        as_of = as_of.astimezone(timezone.utc).replace(tzinfo=None)
    return round((deadline - as_of).total_seconds() / 3600.0, 3)


def _tasks_in_window(df: pd.DataFrame, as_of: datetime, window: timedelta) -> int:
    if df.empty:
        return 0
    aligned = _align_tz(df, "created_at", as_of)
    window_start = aligned - window
    return int(((df["created_at"] >= window_start) & (df["created_at"] < aligned)).sum())


def _interruptions_in_window(interruptions_df: pd.DataFrame, as_of: datetime, window: timedelta) -> int:
    before = _before(interruptions_df, "start_time", as_of)
    if before.empty:
        return 0
    aligned = _align_tz(interruptions_df, "start_time", as_of)
    window_start = aligned - window
    return int((before["start_time"] >= window_start).sum())


def _recent_context_switches(events_df: pd.DataFrame, as_of: datetime, window: timedelta) -> int:
    """Proxy count based on raw events (paused->resumed pairs) within the
    window, for use where a full ContextSession rebuild hasn't run yet.
    """
    before = _before(events_df, "event_time", as_of)
    if before.empty:
        return 0
    aligned = _align_tz(events_df, "event_time", as_of)
    window_start = aligned - window
    recent = before[before["event_time"] >= window_start]
    return int((recent["event_type"] == "resumed").sum())


def _average_interruption_duration(interruptions_df: pd.DataFrame, as_of: datetime) -> float | None:
    before = _before(interruptions_df, "start_time", as_of)
    if before.empty:
        return None
    return round(float(before["duration_seconds"].mean()), 2)


# ---------------------------------------------------------------------------
# User-level features
# ---------------------------------------------------------------------------

def generate_user_features(
    *,
    tasks_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    as_of: datetime,
) -> dict:
    """Aggregate, user-level behavioural features as of `as_of`."""
    hist_tasks = _before(tasks_df, "created_at", as_of)
    hist_interruptions = _before(interruptions_df, "start_time", as_of)
    hist_sessions = _before(sessions_df, "session_start", as_of)

    resolved = hist_tasks[hist_tasks["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )]

    return {
        "completion_rate": _rate_status(resolved, TaskStatus.COMPLETED.value),
        "forgetting_rate": _rate_status(resolved, TaskStatus.FORGOTTEN.value),
        "total_tasks": int(len(hist_tasks)),
        "total_interruptions": int(len(hist_interruptions)),
        "average_session_duration_seconds": (
            round(float(hist_sessions["focused_time_seconds"].mean()), 2) if not hist_sessions.empty else None
        ),
        "average_interruption_duration_seconds": _average_interruption_duration(interruptions_df, as_of),
        "total_context_switches": (
            int(hist_sessions["context_switch_count"].sum()) if not hist_sessions.empty else 0
        ),
    }


# ---------------------------------------------------------------------------
# Context-level features
# ---------------------------------------------------------------------------

def generate_context_features(
    *,
    location_id,
    tasks_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    as_of: datetime,
) -> dict:
    """Features scoped to a single location/context, as of `as_of`."""
    hist_tasks = _before(tasks_df, "created_at", as_of)
    hist_interruptions = _before(interruptions_df, "start_time", as_of)

    loc_tasks = hist_tasks[hist_tasks["location_id"] == location_id]
    loc_interruptions = hist_interruptions[hist_interruptions["location_id"] == location_id]

    resolved = loc_tasks[loc_tasks["status"].isin(
        [TaskStatus.COMPLETED.value, TaskStatus.FORGOTTEN.value, TaskStatus.CANCELLED.value]
    )]

    return {
        "location_task_count": int(len(loc_tasks)),
        "location_forgetting_rate": _rate_status(resolved, TaskStatus.FORGOTTEN.value),
        "location_interruption_count": int(len(loc_interruptions)),
        "location_average_interruption_duration_seconds": (
            round(float(loc_interruptions["duration_seconds"].mean()), 2) if not loc_interruptions.empty else None
        ),
    }
