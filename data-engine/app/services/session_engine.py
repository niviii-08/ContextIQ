"""
Context Session Engine
=======================

Converts the raw, append-only stream of `task_events` + `interruptions`
into reconstructed behavioural `context_sessions`.

ALGORITHM (documented, deliberately simple and transparent)
-------------------------------------------------------------
A "context session" is a contiguous block of time in which a user is
engaged with one task, bounded by a start event (created/started/resumed)
and an end event (completed/forgotten/cancelled/paused) OR by an idle
timeout if no closing event ever arrives.

For each task, independently:

1. Sort task_events chronologically.
2. Walk the events pairwise. A session OPENS on: created, started, resumed.
   A session CLOSES on: paused, completed, forgotten, cancelled.
3. Between the session's open and close timestamps, gather all
   `interruptions` for that task (or for that user without a task, that
   fall within the session window) that overlap the session window.
4. `focused_time_seconds` = session duration − total interruption time
   that falls inside the session window (clamped at 0).
5. `interruption_time_seconds` = sum of overlapping interruption durations.
6. `resume_delay_seconds` — only computed for sessions that OPEN on a
   `resumed` event: the gap between the prior `paused` event (session end)
   and this `resumed` event (this session's start). This measures how long
   it took the user to come back to the task after pausing it.
7. `context_switch_count` — NOT every interruption is a context switch.
   We only count an interruption as a context switch if:
     a) its duration exceeds a configurable threshold
        (default: it has *any* measurable duration — i.e. it wasn't a
        sub-second glance), AND
     b) the gap between the interruption and the immediately preceding
        activity on this task exceeds `context_switch_gap_minutes`
        (default 5 minutes) — i.e. it was long/disruptive enough to plausibly
        require re-orientation, not just a passing glance.
   Short interruptions below the gap threshold are recorded (they still
   count toward `interruption_count` / `interruption_time_seconds`) but are
   NOT counted as a context switch, because the user never really lost
   their place.
8. If a task's session never receives a closing event (e.g. it is still
   "started" as of `now`), and the last event is older than
   `session_idle_timeout_minutes`, the engine closes the session at
   `last_event_time + session_idle_timeout_minutes` and marks it complete
   for analytics purposes (the underlying task itself is untouched — this
   only affects the derived context_sessions table).

Sessions are recomputed idempotently: `rebuild_sessions_for_user` deletes
and regenerates every ContextSession row for the user from scratch, so it
is always safe to re-run after new events arrive.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.orm import Session as DBSession

from app.config import get_settings
from app.models.context_session import ContextSession
from app.models.interruption import Interruption
from app.models.task import Task
from app.models.task_event import TaskEvent, TaskEventType

settings = get_settings()

_OPEN_EVENTS = {TaskEventType.CREATED, TaskEventType.STARTED, TaskEventType.RESUMED}
_CLOSE_EVENTS = {
    TaskEventType.PAUSED,
    TaskEventType.COMPLETED,
    TaskEventType.FORGOTTEN,
    TaskEventType.CANCELLED,
}


@dataclass
class _RawSession:
    task_id: UUID
    location_id: UUID | None
    start: datetime
    end: datetime
    opened_by: TaskEventType
    prior_pause_time: datetime | None = None
    interruptions: list[Interruption] = field(default_factory=list)


def _overlaps(interruption: Interruption, start: datetime, end: datetime) -> bool:
    i_start = interruption.start_time
    i_end = interruption.end_time or interruption.start_time
    return i_start < end and i_end > start


def build_raw_sessions_for_task(
    events: list[TaskEvent],
    interruptions: list[Interruption],
    now: datetime,
    idle_timeout: timedelta,
) -> list[_RawSession]:
    """Pure function: turn one task's sorted events + its interruptions
    into a list of raw (start, end) session windows. Kept side-effect free
    so it is trivially unit-testable.
    """
    events = sorted(events, key=lambda e: e.event_time)
    sessions: list[_RawSession] = []

    open_event: TaskEvent | None = None
    last_pause_time: datetime | None = None

    for ev in events:
        if ev.event_type in _OPEN_EVENTS:
            # A new open event while one is already open just replaces it
            # defensively (shouldn't normally happen with clean data).
            open_event = ev
        elif ev.event_type in _CLOSE_EVENTS and open_event is not None:
            raw = _RawSession(
                task_id=open_event.task_id,
                location_id=open_event.location_id,
                start=open_event.event_time,
                end=ev.event_time,
                opened_by=open_event.event_type,
                prior_pause_time=last_pause_time if open_event.event_type == TaskEventType.RESUMED else None,
            )
            sessions.append(raw)
            if ev.event_type == TaskEventType.PAUSED:
                last_pause_time = ev.event_time
            open_event = None

    # Dangling open session (never closed) -> close at idle timeout.
    if open_event is not None:
        implied_end = min(open_event.event_time + idle_timeout, now)
        if implied_end <= open_event.event_time:
            implied_end = open_event.event_time
        raw = _RawSession(
            task_id=open_event.task_id,
            location_id=open_event.location_id,
            start=open_event.event_time,
            end=implied_end,
            opened_by=open_event.event_type,
            prior_pause_time=last_pause_time if open_event.event_type == TaskEventType.RESUMED else None,
        )
        sessions.append(raw)

    # Attach overlapping interruptions to each raw session.
    for raw in sessions:
        raw.interruptions = [i for i in interruptions if _overlaps(i, raw.start, raw.end)]

    return sessions


def _is_context_switch(interruption: Interruption, gap_minutes: int) -> bool:
    duration = interruption.duration_seconds or 0
    if duration <= 0:
        return False
    gap_seconds = gap_minutes * 60
    return duration >= gap_seconds


def compute_session_metrics(raw: _RawSession, gap_minutes: int) -> dict:
    total_seconds = max(0, int((raw.end - raw.start).total_seconds()))

    interruption_seconds = 0
    context_switches = 0
    for interruption in raw.interruptions:
        i_start = max(interruption.start_time, raw.start)
        i_end = min(interruption.end_time or interruption.start_time, raw.end)
        overlap = max(0, int((i_end - i_start).total_seconds()))
        interruption_seconds += overlap
        if _is_context_switch(interruption, gap_minutes):
            context_switches += 1

    focused_seconds = max(0, total_seconds - interruption_seconds)

    resume_delay = None
    if raw.opened_by == TaskEventType.RESUMED and raw.prior_pause_time is not None:
        resume_delay = max(0.0, (raw.start - raw.prior_pause_time).total_seconds())

    return {
        "focused_time_seconds": focused_seconds,
        "interruption_time_seconds": interruption_seconds,
        "resume_delay_seconds": resume_delay,
        "context_switch_count": context_switches,
        "interruption_count": len(raw.interruptions),
    }


def rebuild_sessions_for_user(db: DBSession, user_id: UUID, now: datetime | None = None) -> int:
    """Delete and regenerate all ContextSession rows for a user.

    Returns the number of sessions created.
    """
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    idle_timeout = timedelta(minutes=settings.session_idle_timeout_minutes)
    gap_minutes = settings.context_switch_gap_minutes

    db.execute(delete(ContextSession).where(ContextSession.user_id == user_id))

    task_ids = db.execute(select(Task.id).where(Task.user_id == user_id)).scalars().all()

    created = 0
    for task_id in task_ids:
        events = (
            db.execute(select(TaskEvent).where(TaskEvent.task_id == task_id)).scalars().all()
        )
        interruptions = (
            db.execute(select(Interruption).where(Interruption.task_id == task_id)).scalars().all()
        )
        if not events:
            continue

        # Align `now`'s tz-awareness with the events actually read back from
        # this database backend (SQLite drops tz-awareness on read; Postgres
        # preserves it), so the idle-timeout comparison never raises.
        task_now = now
        sample_time = events[0].event_time
        sample_is_aware = sample_time.tzinfo is not None
        now_is_aware = task_now.tzinfo is not None
        if sample_is_aware and not now_is_aware:
            task_now = task_now.replace(tzinfo=timezone.utc)
        elif not sample_is_aware and now_is_aware:
            task_now = task_now.astimezone(timezone.utc).replace(tzinfo=None)

        raw_sessions = build_raw_sessions_for_task(events, interruptions, task_now, idle_timeout)
        for raw in raw_sessions:
            metrics = compute_session_metrics(raw, gap_minutes)
            db.add(
                ContextSession(
                    user_id=user_id,
                    task_id=raw.task_id,
                    location_id=raw.location_id,
                    session_start=raw.start,
                    session_end=raw.end,
                    **metrics,
                )
            )
            created += 1

    db.commit()
    return created
