"""
Shared feature-engineering utilities used by both System A (context
switching) and System B (association mining) so that feature logic is
defined once and imported everywhere else.
"""

from __future__ import annotations

import pandas as pd

from app.schemas.context import ReconstructedSession


def sessions_to_feature_frame(sessions: list[ReconstructedSession]) -> pd.DataFrame:
    """Turn reconstructed sessions into a flat feature DataFrame suitable
    for clustering, anomaly detection, or general analysis."""
    rows = []
    for s in sessions:
        avg_resume_delay = (
            sum(s.resume_delays_seconds) / len(s.resume_delays_seconds)
            if s.resume_delays_seconds
            else 0.0
        )
        avg_interruption_duration = (
            sum(s.interruption_durations_seconds) / len(s.interruption_durations_seconds)
            if s.interruption_durations_seconds
            else 0.0
        )
        rows.append(
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "task_id": s.task_id,
                "task_category": s.task_category,
                "context": s.context,
                "start_time": s.start_time,
                "hour_of_day": s.start_time.hour,
                "day_of_week": s.start_time.weekday(),
                "session_duration_seconds": s.session_duration_seconds,
                "focused_time_seconds": s.focused_time_seconds,
                "interruption_time_seconds": s.interruption_time_seconds,
                "num_interruptions": s.num_interruptions,
                "num_context_switches": s.num_context_switches,
                "avg_resume_delay_seconds": avg_resume_delay,
                "avg_interruption_duration_seconds": avg_interruption_duration,
                "completed": s.completed,
            }
        )
    return pd.DataFrame(rows)
