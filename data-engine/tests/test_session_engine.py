import uuid
from datetime import datetime, timedelta, timezone

from app.services.session_engine import (
    build_raw_sessions_for_task,
    compute_session_metrics,
    rebuild_sessions_for_user,
)
from app.models.task_event import TaskEvent, TaskEventType
from app.models.interruption import Interruption, InterruptionType
from app.models.task import Task


def _ev(task_id, event_type, when):
    return TaskEvent(id=uuid.uuid4(), user_id=uuid.uuid4(), task_id=task_id, event_type=event_type, event_time=when)


def _interruption(task_id, start, duration_seconds):
    return Interruption(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        task_id=task_id,
        interruption_type=InterruptionType.PHONE,
        start_time=start,
        end_time=start + timedelta(seconds=duration_seconds),
        duration_seconds=duration_seconds,
    )


def test_simple_started_completed_session():
    task_id = uuid.uuid4()
    t0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    events = [_ev(task_id, TaskEventType.STARTED, t0), _ev(task_id, TaskEventType.COMPLETED, t0 + timedelta(minutes=30))]

    sessions = build_raw_sessions_for_task(events, [], now=t0 + timedelta(hours=2), idle_timeout=timedelta(minutes=30))
    assert len(sessions) == 1
    assert sessions[0].start == t0
    assert sessions[0].end == t0 + timedelta(minutes=30)


def test_paused_resumed_creates_two_sessions_with_resume_delay():
    task_id = uuid.uuid4()
    t0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    events = [
        _ev(task_id, TaskEventType.STARTED, t0),
        _ev(task_id, TaskEventType.PAUSED, t0 + timedelta(minutes=20)),
        _ev(task_id, TaskEventType.RESUMED, t0 + timedelta(hours=3)),
        _ev(task_id, TaskEventType.COMPLETED, t0 + timedelta(hours=3, minutes=15)),
    ]
    sessions = build_raw_sessions_for_task(events, [], now=t0 + timedelta(hours=5), idle_timeout=timedelta(minutes=30))
    assert len(sessions) == 2

    metrics_1 = compute_session_metrics(sessions[0], gap_minutes=5)
    metrics_2 = compute_session_metrics(sessions[1], gap_minutes=5)

    assert metrics_1["resume_delay_seconds"] is None  # first session opened by "started", not "resumed"
    assert metrics_2["resume_delay_seconds"] == pytest_approx((3 * 3600) - (20 * 60))


def pytest_approx(value, tol=1.0):
    class _Approx:
        def __eq__(self, other):
            return abs(other - value) <= tol
    return _Approx()


def test_dangling_open_session_closed_by_idle_timeout():
    task_id = uuid.uuid4()
    t0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    events = [_ev(task_id, TaskEventType.STARTED, t0)]
    now = t0 + timedelta(hours=10)
    idle_timeout = timedelta(minutes=30)

    sessions = build_raw_sessions_for_task(events, [], now=now, idle_timeout=idle_timeout)
    assert len(sessions) == 1
    assert sessions[0].end == t0 + idle_timeout


def test_short_interruption_not_counted_as_context_switch():
    task_id = uuid.uuid4()
    t0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    events = [_ev(task_id, TaskEventType.STARTED, t0), _ev(task_id, TaskEventType.COMPLETED, t0 + timedelta(minutes=30))]
    # 10-second interruption: well below the 5-minute context-switch gap threshold
    interruptions = [_interruption(task_id, t0 + timedelta(minutes=5), duration_seconds=10)]

    sessions = build_raw_sessions_for_task(events, interruptions, now=t0 + timedelta(hours=1), idle_timeout=timedelta(minutes=30))
    metrics = compute_session_metrics(sessions[0], gap_minutes=5)

    assert metrics["interruption_count"] == 1
    assert metrics["context_switch_count"] == 0  # too short to count as a real switch


def test_long_interruption_counted_as_context_switch():
    task_id = uuid.uuid4()
    t0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    events = [_ev(task_id, TaskEventType.STARTED, t0), _ev(task_id, TaskEventType.COMPLETED, t0 + timedelta(minutes=60))]
    # 8-minute interruption: exceeds the 5-minute threshold
    interruptions = [_interruption(task_id, t0 + timedelta(minutes=10), duration_seconds=8 * 60)]

    sessions = build_raw_sessions_for_task(events, interruptions, now=t0 + timedelta(hours=2), idle_timeout=timedelta(minutes=30))
    metrics = compute_session_metrics(sessions[0], gap_minutes=5)

    assert metrics["context_switch_count"] == 1
    assert metrics["interruption_time_seconds"] == 8 * 60
    assert metrics["focused_time_seconds"] == 60 * 60 - 8 * 60


def test_empty_events_produce_no_sessions():
    sessions = build_raw_sessions_for_task([], [], now=datetime.now(timezone.utc), idle_timeout=timedelta(minutes=30))
    assert sessions == []


def test_rebuild_sessions_for_user_end_to_end(db_session, sample_user):
    task = Task(user_id=sample_user.id, title="E2E task")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    t0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    db_session.add_all(
        [
            TaskEvent(user_id=sample_user.id, task_id=task.id, event_type=TaskEventType.STARTED, event_time=t0),
            TaskEvent(
                user_id=sample_user.id,
                task_id=task.id,
                event_type=TaskEventType.COMPLETED,
                event_time=t0 + timedelta(minutes=25),
            ),
        ]
    )
    db_session.commit()

    created = rebuild_sessions_for_user(db_session, sample_user.id, now=t0 + timedelta(hours=1))
    assert created == 1

    # Idempotent: rebuilding again should not duplicate rows.
    created_again = rebuild_sessions_for_user(db_session, sample_user.id, now=t0 + timedelta(hours=1))
    assert created_again == 1
