from datetime import datetime

from app.schemas.context import ReconstructedSession
from ml.context.metrics import compute_session_metrics


def _session(**overrides):
    base = dict(
        session_id="s1",
        user_id="u1",
        task_id="t1",
        task_category="programming",
        context="home_office",
        start_time=datetime(2026, 1, 1, 9, 0, 0),
        end_time=datetime(2026, 1, 1, 9, 10, 0),
        session_duration_seconds=600.0,
        focused_time_seconds=500.0,
        interruption_time_seconds=100.0,
        num_interruptions=2,
        num_context_switches=1,
        resume_delays_seconds=[20.0, 30.0],
        interruption_durations_seconds=[20.0, 30.0],
        completed=True,
    )
    base.update(overrides)
    return ReconstructedSession(**base)


def test_metrics_empty_sessions():
    m = compute_session_metrics([])
    assert m.num_sessions == 0
    assert m.average_session_duration_seconds == 0.0


def test_metrics_basic_aggregation():
    sessions = [_session(session_id="s1"), _session(session_id="s2")]
    m = compute_session_metrics(sessions, scope="test")
    assert m.num_sessions == 2
    assert m.total_focused_time_seconds == 1000.0
    assert m.total_interruptions == 4
    assert m.total_context_switches == 2
    assert m.average_interruption_duration_seconds == 25.0
    assert m.average_resume_delay_seconds == 25.0
    assert m.interruptions_per_session == 2.0
    assert m.average_session_duration_seconds == 600.0


def test_switches_per_hour_formula():
    # 1 switch, 3600 focused seconds -> 1 switch/hour
    s = _session(num_context_switches=1, focused_time_seconds=3600.0)
    m = compute_session_metrics([s])
    assert m.switches_per_hour == 1.0


def test_switches_per_hour_zero_when_no_focus_time():
    s = _session(focused_time_seconds=0.0, num_context_switches=3)
    m = compute_session_metrics([s])
    assert m.switches_per_hour == 0.0
