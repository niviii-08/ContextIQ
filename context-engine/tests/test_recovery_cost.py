from datetime import datetime

from app.schemas.context import ReconstructedSession
from ml.context.recovery_cost import estimate_recovery_costs


def _session(session_id, num_interruptions, interruption_durations, resume_delays, switches, duration):
    return ReconstructedSession(
        session_id=session_id,
        user_id="u1",
        task_id="t1",
        task_category="programming",
        context="home_office",
        start_time=datetime(2026, 1, 1, 9, 0, 0),
        end_time=datetime(2026, 1, 1, 9, 10, 0),
        session_duration_seconds=duration,
        focused_time_seconds=duration * 0.8,
        interruption_time_seconds=duration * 0.2,
        num_interruptions=num_interruptions,
        num_context_switches=switches,
        resume_delays_seconds=resume_delays,
        interruption_durations_seconds=interruption_durations,
        completed=True,
    )


def test_recovery_cost_scores_in_bounds():
    sessions = [
        _session("s1", 0, [], [], 0, 100),
        _session("s2", 5, [30, 40, 50, 20, 10], [60, 70, 80, 20, 10], 4, 600),
        _session("s3", 2, [10, 10], [15, 15], 1, 200),
    ]
    estimates = estimate_recovery_costs(sessions)
    assert len(estimates) == 3
    for e in estimates:
        assert 0.0 <= e.recovery_cost_score <= 1.0


def test_recovery_cost_ranks_worse_session_higher():
    calm = _session("calm", 0, [], [], 0, 300)
    chaotic = _session("chaotic", 6, [30, 40, 50, 60, 20, 10], [90, 80, 70, 60, 50, 40], 5, 900)
    estimates = estimate_recovery_costs([calm, chaotic])
    by_id = {e.session_id: e.recovery_cost_score for e in estimates}
    assert by_id["chaotic"] > by_id["calm"]


def test_recovery_cost_single_session_population_is_zero():
    # With a population of 1, min == max, so normalization collapses to 0
    # for every feature -- this is documented, expected behaviour.
    s = _session("solo", 3, [10, 20, 30], [15, 25, 35], 2, 400)
    estimates = estimate_recovery_costs([s])
    assert estimates[0].recovery_cost_score == 0.0
