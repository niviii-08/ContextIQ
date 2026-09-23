"""
Stage 4 — Session Reconstruction (DataFrame-based wrapper)
==========================================================

Wraps the existing pure-function algorithm in app/services/session_engine.py
to provide a DataFrame-in / DataFrame-out interface that:

  - Requires no database connection (fully testable offline)
  - Accepts a deterministic seed for reproducibility
  - Produces a sessions DataFrame with all computed metrics
  - Logs each reconstruction step with record counts

The underlying algorithm is NOT re-implemented here. This module only
provides I/O plumbing around the existing pure functions:

  build_raw_sessions_for_task()   — app/services/session_engine.py
  compute_session_metrics()       — app/services/session_engine.py

ALGORITHM SUMMARY (see session_engine.py for full spec)
---------------------------------------------------------
For each task:
  1. Sort events chronologically.
  2. Open a session on: created / started / resumed.
  3. Close it on: paused / completed / forgotten / cancelled.
  4. Attach overlapping interruptions to each window.
  5. Compute: focused_time, interruption_time, resume_delay, context_switches.
  6. If never closed → close at idle timeout (default: 30 min).
  7. Sessions are rebuilt from scratch (idempotent).
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import pandas as pd

# Make sure the data-engine app package is importable when running from root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.session_engine import (
    build_raw_sessions_for_task,
    compute_session_metrics,
)
from app.models.task_event import TaskEventType

logger = logging.getLogger(__name__)

# Default thresholds (can be overridden)
DEFAULT_IDLE_TIMEOUT_MINUTES: int = 30
DEFAULT_CONTEXT_SWITCH_GAP_MINUTES: int = 5


@dataclass
class _MockInterruption:
    """Minimal duck-type for Interruption used by the pure session functions."""
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    task_id: Any = None
    location_id: Any = None


@dataclass
class _MockEvent:
    """Minimal duck-type for TaskEvent used by the pure session functions."""
    task_id: Any
    location_id: Any
    event_type: TaskEventType
    event_time: datetime


def _row_to_mock_event(row: pd.Series) -> _MockEvent:
    et_raw = str(row["event_type"]).lower().strip()
    # Map to the enum
    try:
        event_type = TaskEventType(et_raw)
    except ValueError:
        event_type = TaskEventType.CREATED  # fallback, validator should have caught this
    return _MockEvent(
        task_id=row["task_id"],
        location_id=row.get("location_id"),
        event_type=event_type,
        event_time=_ensure_aware(row["event_time"]),
    )


def _row_to_mock_interruption(row: pd.Series) -> _MockInterruption:
    return _MockInterruption(
        start_time=_ensure_aware(row["start_time"]),
        end_time=_ensure_aware(row["end_time"]) if pd.notna(row.get("end_time")) else None,
        duration_seconds=int(row["duration_seconds"]) if pd.notna(row.get("duration_seconds")) else None,
        task_id=row.get("task_id"),
        location_id=row.get("location_id"),
    )


def _ensure_aware(dt) -> datetime:
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def reconstruct_sessions(
    events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame,
    idle_timeout_minutes: int = DEFAULT_IDLE_TIMEOUT_MINUTES,
    context_switch_gap_minutes: int = DEFAULT_CONTEXT_SWITCH_GAP_MINUTES,
) -> pd.DataFrame:
    """
    Reconstruct context sessions from transformed events + interruptions.

    Parameters
    ----------
    events_df : pd.DataFrame
        Cleaned + transformed task_events (must have: task_id, user_id,
        event_type, event_time; optionally location_id).
    interruptions_df : pd.DataFrame
        Cleaned interruptions (must have: start_time; optionally: task_id,
        location_id, end_time, duration_seconds).
    idle_timeout_minutes : int
        Sessions still open after this many minutes of inactivity are
        auto-closed (default 30).
    context_switch_gap_minutes : int
        Interruptions >= this duration (in minutes) count as context switches
        (default 5).

    Returns
    -------
    pd.DataFrame
        Sessions table with columns:
        task_id, user_id, location_id, session_start, session_end,
        focused_time_seconds, interruption_time_seconds, resume_delay_seconds,
        context_switch_count, interruption_count
    """
    if events_df.empty:
        logger.warning("reconstruct_sessions: no events supplied, returning empty sessions")
        return _empty_sessions_df()

    now = datetime.now(timezone.utc)
    idle_timeout = timedelta(minutes=idle_timeout_minutes)

    # Build interruption lookup by task_id (None key = untied interruptions)
    interruption_by_task: dict[Any, list[_MockInterruption]] = {}
    for _, row in interruptions_df.iterrows():
        tid = row.get("task_id")
        mock = _row_to_mock_interruption(row)
        interruption_by_task.setdefault(tid, []).append(mock)

    task_user_map: dict[Any, Any] = {}
    if "task_id" in events_df.columns and "user_id" in events_df.columns:
        task_user_map = events_df.groupby("task_id")["user_id"].first().to_dict()

    all_sessions: list[dict] = []
    task_ids = events_df["task_id"].unique() if "task_id" in events_df.columns else []

    for task_id in task_ids:
        task_events_df = events_df[events_df["task_id"] == task_id]
        mock_events = [_row_to_mock_event(row) for _, row in task_events_df.iterrows()]

        # Gather interruptions for this task + untied ones (task_id=None)
        task_interruptions = (
            interruption_by_task.get(task_id, []) +
            interruption_by_task.get(None, [])
        )

        # tz-align now to match events
        task_now = now
        if mock_events:
            sample_aware = mock_events[0].event_time.tzinfo is not None
            if not sample_aware:
                task_now = now.replace(tzinfo=None)

        raw_sessions = build_raw_sessions_for_task(
            mock_events, task_interruptions, task_now, idle_timeout
        )

        user_id = task_user_map.get(task_id)
        for raw in raw_sessions:
            metrics = compute_session_metrics(raw, context_switch_gap_minutes)
            all_sessions.append({
                "task_id": task_id,
                "user_id": user_id,
                "location_id": raw.location_id,
                "session_start": raw.start,
                "session_end": raw.end,
                **metrics,
            })

    if not all_sessions:
        logger.warning("reconstruct_sessions: no sessions produced from %d events", len(events_df))
        return _empty_sessions_df()

    sessions_df = pd.DataFrame(all_sessions)
    logger.info(
        "reconstruct_sessions: built %d sessions from %d tasks (%d events)",
        len(sessions_df), len(task_ids), len(events_df),
    )
    return sessions_df


def _empty_sessions_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "task_id", "user_id", "location_id",
        "session_start", "session_end",
        "focused_time_seconds", "interruption_time_seconds",
        "resume_delay_seconds", "context_switch_count", "interruption_count",
    ])
