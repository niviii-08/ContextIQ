from datetime import datetime, timedelta

from app.schemas.events import RawEvent, EventType
from ml.context.session_reconstruction import reconstruct_sessions


def _e(user_id, task_id, offset_seconds, event_type, category="programming", context="home_office", source=None):
    return RawEvent(
        user_id=user_id,
        timestamp=datetime(2026, 1, 1, 9, 0, 0) + timedelta(seconds=offset_seconds),
        task_id=task_id,
        task_category=category,
        context=context,
        event_type=event_type,
        interruption_source=source,
    )


def test_simple_start_complete_session():
    events = [
        _e("u1", "t1", 0, EventType.START),
        _e("u1", "t1", 100, EventType.COMPLETE),
    ]
    sessions = reconstruct_sessions(events)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.completed is True
    assert s.session_duration_seconds == 100
    assert s.focused_time_seconds == 100
    assert s.num_interruptions == 0


def test_interruption_and_resume_tracked():
    events = [
        _e("u1", "t1", 0, EventType.START),
        _e("u1", "t1", 50, EventType.INTERRUPTION, source="phone_call"),
        _e("u1", "t1", 80, EventType.RESUME),
        _e("u1", "t1", 130, EventType.COMPLETE),
    ]
    sessions = reconstruct_sessions(events)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.num_interruptions == 1
    assert s.interruption_time_seconds == 30
    assert s.focused_time_seconds == 100  # 50 before + 50 after
    assert s.resume_delays_seconds == [30]


def test_task_switch_increments_counter():
    events = [
        _e("u1", "t1", 0, EventType.START),
        _e("u1", "t1", 20, EventType.TASK_SWITCH),
        _e("u1", "t1", 60, EventType.COMPLETE),
    ]
    sessions = reconstruct_sessions(events)
    s = sessions[0]
    assert s.num_context_switches == 1
    assert s.focused_time_seconds == 60


def test_multiple_sessions_same_task_id_reused():
    events = [
        _e("u1", "t1", 0, EventType.START),
        _e("u1", "t1", 50, EventType.COMPLETE),
        _e("u1", "t1", 200, EventType.START),
        _e("u1", "t1", 260, EventType.COMPLETE),
    ]
    sessions = reconstruct_sessions(events)
    assert len(sessions) == 2
    assert all(s.completed for s in sessions)


def test_missing_start_handled_defensively():
    events = [
        _e("u1", "t1", 0, EventType.INTERRUPTION),
        _e("u1", "t1", 30, EventType.RESUME),
        _e("u1", "t1", 60, EventType.COMPLETE),
    ]
    sessions = reconstruct_sessions(events)
    assert len(sessions) == 1
    assert sessions[0].completed is True


def test_empty_events_returns_empty_list():
    assert reconstruct_sessions([]) == []


def test_dangling_session_without_complete_is_still_returned():
    events = [
        _e("u1", "t1", 0, EventType.START),
        _e("u1", "t1", 30, EventType.PAUSE),
    ]
    sessions = reconstruct_sessions(events)
    assert len(sessions) == 1
    assert sessions[0].completed is False
