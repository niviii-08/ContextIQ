"""
Aggregate metrics over reconstructed sessions.

All formulas are simple, transparent, and documented in
docs/CONTEXT_INTELLIGENCE.md. No formula here claims psychological
validity; they are descriptive statistics over observed event timing.
"""

from __future__ import annotations

from app.schemas.context import ReconstructedSession, SessionMetrics


def compute_session_metrics(
    sessions: list[ReconstructedSession], scope: str = "all"
) -> SessionMetrics:
    """Compute aggregate metrics across a list of sessions.

    Formulas
    --------
    - average_interruption_duration_seconds =
          sum(all interruption_durations) / count(all interruption_durations)
    - average_resume_delay_seconds =
          sum(all resume_delays) / count(all resume_delays)
    - switches_per_hour =
          total_context_switches / (total_focused_time_seconds / 3600)
    - interruptions_per_session =
          total_interruptions / num_sessions
    - average_session_duration_seconds =
          sum(session_duration_seconds) / num_sessions
    """
    if not sessions:
        return SessionMetrics(
            scope=scope,
            num_sessions=0,
            total_focused_time_seconds=0.0,
            total_interruption_time_seconds=0.0,
            total_interruptions=0,
            total_context_switches=0,
            average_interruption_duration_seconds=0.0,
            average_resume_delay_seconds=0.0,
            switches_per_hour=0.0,
            interruptions_per_session=0.0,
            average_session_duration_seconds=0.0,
        )

    num_sessions = len(sessions)
    total_focused = sum(s.focused_time_seconds for s in sessions)
    total_interruption_time = sum(s.interruption_time_seconds for s in sessions)
    total_interruptions = sum(s.num_interruptions for s in sessions)
    total_switches = sum(s.num_context_switches for s in sessions)
    total_duration = sum(s.session_duration_seconds for s in sessions)

    all_interruption_durations: list[float] = []
    all_resume_delays: list[float] = []
    for s in sessions:
        all_interruption_durations.extend(s.interruption_durations_seconds)
        all_resume_delays.extend(s.resume_delays_seconds)

    avg_interruption_duration = (
        sum(all_interruption_durations) / len(all_interruption_durations)
        if all_interruption_durations
        else 0.0
    )
    avg_resume_delay = (
        sum(all_resume_delays) / len(all_resume_delays) if all_resume_delays else 0.0
    )

    focused_hours = total_focused / 3600.0
    switches_per_hour = (total_switches / focused_hours) if focused_hours > 0 else 0.0

    interruptions_per_session = total_interruptions / num_sessions
    avg_session_duration = total_duration / num_sessions

    return SessionMetrics(
        scope=scope,
        num_sessions=num_sessions,
        total_focused_time_seconds=round(total_focused, 3),
        total_interruption_time_seconds=round(total_interruption_time, 3),
        total_interruptions=total_interruptions,
        total_context_switches=total_switches,
        average_interruption_duration_seconds=round(avg_interruption_duration, 3),
        average_resume_delay_seconds=round(avg_resume_delay, 3),
        switches_per_hour=round(switches_per_hour, 3),
        interruptions_per_session=round(interruptions_per_session, 3),
        average_session_duration_seconds=round(avg_session_duration, 3),
    )
