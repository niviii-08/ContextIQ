"""
Session reconstruction engine.

Converts a flat, unordered stream of raw events (START, PAUSE, RESUME,
INTERRUPTION, COMPLETE, TASK_SWITCH) into structured `ReconstructedSession`
objects with derived timing metrics.

Design notes
------------
- Events are grouped by (user_id, task_id) and processed in timestamp order.
- A new session begins at a START event (or, defensively, at the first event
  seen for a user/task pair if no START was recorded).
- PAUSE -> RESUME pairs contribute to interruption time only when the RESUME
  is preceded by an INTERRUPTION event; a plain PAUSE/RESUME with no
  INTERRUPTION in between is treated as a voluntary break and is excluded
  from "interruption time" but still ends focused-time accumulation for
  that span (it is simply idle time, not attributed to interruption).
- INTERRUPTION events mark the start of an interruption; the next RESUME
  (or COMPLETE) closes it and its duration is recorded.
- TASK_SWITCH events increment `num_context_switches` and close out the
  current focused-time span without necessarily ending the session.
- COMPLETE ends the session.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd

from app.schemas.events import RawEvent, EventType
from app.schemas.context import ReconstructedSession


@dataclass
class _OpenSession:
    session_id: str
    user_id: str
    task_id: str
    task_category: str
    context: str
    start_time: datetime
    last_activity_time: datetime
    focused_seconds: float = 0.0
    interruption_seconds: float = 0.0
    num_interruptions: int = 0
    num_switches: int = 0
    resume_delays: list[float] = field(default_factory=list)
    interruption_durations: list[float] = field(default_factory=list)
    pending_interruption_start: Optional[datetime] = None
    completed: bool = False
    end_time: Optional[datetime] = None


def _events_to_dataframe(events: list[RawEvent]) -> pd.DataFrame:
    rows = []
    for e in events:
        rows.append(
            {
                "user_id": e.user_id,
                "timestamp": pd.to_datetime(e.timestamp),
                "task_id": e.task_id,
                "task_category": e.task_category,
                "context": e.context,
                "event_type": e.event_type.value if hasattr(e.event_type, "value") else e.event_type,
                "interruption_source": e.interruption_source,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values(["user_id", "task_id", "timestamp"]).reset_index(drop=True)
    return df


def reconstruct_sessions(events: list[RawEvent]) -> list[ReconstructedSession]:
    """Reconstruct sessions from a list of raw events.

    Returns a list of `ReconstructedSession`, one per detected session.
    A single (user_id, task_id) pair may yield multiple sessions if it is
    started, completed, and started again.
    """
    df = _events_to_dataframe(events)
    if df.empty:
        return []

    sessions: list[ReconstructedSession] = []

    for (user_id, task_id), group in df.groupby(["user_id", "task_id"]):
        open_session: Optional[_OpenSession] = None

        for _, row in group.iterrows():
            ts = row["timestamp"]
            etype = row["event_type"]

            if etype == EventType.START.value:
                # Close any dangling previous session defensively.
                if open_session is not None:
                    sessions.append(_finalize(open_session))
                open_session = _OpenSession(
                    session_id=str(uuid.uuid4()),
                    user_id=user_id,
                    task_id=task_id,
                    task_category=row["task_category"],
                    context=row["context"],
                    start_time=ts,
                    last_activity_time=ts,
                )

            elif open_session is None:
                # Defensive: no START seen yet, but activity occurred.
                open_session = _OpenSession(
                    session_id=str(uuid.uuid4()),
                    user_id=user_id,
                    task_id=task_id,
                    task_category=row["task_category"],
                    context=row["context"],
                    start_time=ts,
                    last_activity_time=ts,
                )

            if etype == EventType.INTERRUPTION.value:
                # Accumulate focused time up to this point, then open interruption.
                delta = (ts - open_session.last_activity_time).total_seconds()
                open_session.focused_seconds += max(delta, 0.0)
                open_session.num_interruptions += 1
                open_session.pending_interruption_start = ts
                open_session.last_activity_time = ts

            elif etype == EventType.PAUSE.value:
                delta = (ts - open_session.last_activity_time).total_seconds()
                open_session.focused_seconds += max(delta, 0.0)
                open_session.last_activity_time = ts

            elif etype == EventType.RESUME.value:
                if open_session.pending_interruption_start is not None:
                    duration = (ts - open_session.pending_interruption_start).total_seconds()
                    duration = max(duration, 0.0)
                    open_session.interruption_seconds += duration
                    open_session.interruption_durations.append(duration)
                    open_session.resume_delays.append(duration)
                    open_session.pending_interruption_start = None
                open_session.last_activity_time = ts

            elif etype == EventType.TASK_SWITCH.value:
                delta = (ts - open_session.last_activity_time).total_seconds()
                open_session.focused_seconds += max(delta, 0.0)
                open_session.num_switches += 1
                open_session.last_activity_time = ts

            elif etype == EventType.COMPLETE.value:
                if open_session.pending_interruption_start is not None:
                    duration = (ts - open_session.pending_interruption_start).total_seconds()
                    duration = max(duration, 0.0)
                    open_session.interruption_seconds += duration
                    open_session.interruption_durations.append(duration)
                    open_session.pending_interruption_start = None
                else:
                    delta = (ts - open_session.last_activity_time).total_seconds()
                    open_session.focused_seconds += max(delta, 0.0)
                open_session.last_activity_time = ts
                open_session.completed = True
                open_session.end_time = ts
                sessions.append(_finalize(open_session))
                open_session = None

        if open_session is not None:
            sessions.append(_finalize(open_session))

    return sessions


def _finalize(s: _OpenSession) -> ReconstructedSession:
    end_time = s.end_time or s.last_activity_time
    duration = max((end_time - s.start_time).total_seconds(), 0.0)
    return ReconstructedSession(
        session_id=s.session_id,
        user_id=s.user_id,
        task_id=s.task_id,
        task_category=s.task_category,
        context=s.context,
        start_time=s.start_time,
        end_time=end_time,
        session_duration_seconds=duration,
        focused_time_seconds=round(s.focused_seconds, 3),
        interruption_time_seconds=round(s.interruption_seconds, 3),
        num_interruptions=s.num_interruptions,
        num_context_switches=s.num_switches,
        resume_delays_seconds=[round(x, 3) for x in s.resume_delays],
        interruption_durations_seconds=[round(x, 3) for x in s.interruption_durations],
        completed=s.completed,
    )
