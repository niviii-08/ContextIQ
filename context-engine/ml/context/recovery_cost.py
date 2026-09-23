"""
Context recovery cost estimation.

IMPORTANT: This produces a transparent, feature-based *score*, not a
validated psychological measurement of actual cognitive recovery cost.
The formula is documented here and in docs/CONTEXT_INTELLIGENCE.md so
that any consumer of this module understands exactly what is being
computed and can recalibrate weights for their own use case.

Formula
-------
recovery_cost_score = weighted, min-max normalized combination of:
  - num_interruptions            (more interruptions -> harder to recover)
  - avg_interruption_duration    (longer interruptions -> harder to recover)
  - avg_resume_delay             (slower resumes -> harder to recover)
  - num_context_switches         (more switching -> harder to recover)
  - interruption_time_ratio      (interruption_time / session_duration)

Each raw feature is min-max normalized across the provided session
population (or against fixed reference bounds, if supplied), then
combined with configurable weights that sum to 1.0. The result is
clipped to [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.context import ReconstructedSession, RecoveryCostEstimate

DEFAULT_WEIGHTS = {
    "num_interruptions": 0.25,
    "avg_interruption_duration": 0.2,
    "avg_resume_delay": 0.25,
    "num_context_switches": 0.15,
    "interruption_time_ratio": 0.15,
}


@dataclass
class _Bounds:
    min_val: float
    max_val: float

    def normalize(self, value: float) -> float:
        if self.max_val - self.min_val <= 1e-9:
            return 0.0
        return max(0.0, min(1.0, (value - self.min_val) / (self.max_val - self.min_val)))


def _extract_raw_features(session: ReconstructedSession) -> dict:
    avg_interruption_duration = (
        sum(session.interruption_durations_seconds) / len(session.interruption_durations_seconds)
        if session.interruption_durations_seconds
        else 0.0
    )
    avg_resume_delay = (
        sum(session.resume_delays_seconds) / len(session.resume_delays_seconds)
        if session.resume_delays_seconds
        else 0.0
    )
    interruption_time_ratio = (
        session.interruption_time_seconds / session.session_duration_seconds
        if session.session_duration_seconds > 0
        else 0.0
    )
    return {
        "num_interruptions": float(session.num_interruptions),
        "avg_interruption_duration": avg_interruption_duration,
        "avg_resume_delay": avg_resume_delay,
        "num_context_switches": float(session.num_context_switches),
        "interruption_time_ratio": interruption_time_ratio,
    }


def _compute_bounds(sessions: list[ReconstructedSession]) -> dict[str, _Bounds]:
    all_features = [_extract_raw_features(s) for s in sessions]
    bounds: dict[str, _Bounds] = {}
    for key in DEFAULT_WEIGHTS:
        values = [f[key] for f in all_features] or [0.0]
        bounds[key] = _Bounds(min_val=min(values), max_val=max(values))
    return bounds


def estimate_recovery_cost(
    session: ReconstructedSession,
    bounds: dict[str, _Bounds],
    weights: dict[str, float] | None = None,
) -> RecoveryCostEstimate:
    weights = weights or DEFAULT_WEIGHTS
    raw = _extract_raw_features(session)
    normalized = {k: bounds[k].normalize(v) for k, v in raw.items()}

    score = sum(normalized[k] * weights.get(k, 0.0) for k in normalized)
    score = max(0.0, min(1.0, score))

    return RecoveryCostEstimate(
        session_id=session.session_id,
        recovery_cost_score=round(score, 4),
        contributing_features={
            "raw": {k: round(v, 4) for k, v in raw.items()},
            "normalized": {k: round(v, 4) for k, v in normalized.items()},
            "weights": weights,
        },
    )


def estimate_recovery_costs(
    sessions: list[ReconstructedSession], weights: dict[str, float] | None = None
) -> list[RecoveryCostEstimate]:
    """Estimate recovery cost for every session, normalized against the
    population of sessions passed in. Pass a single-session list to score
    a session in isolation (bounds will collapse to 0.0 in that case,
    which is expected and documented behaviour for n=1 populations)."""
    if not sessions:
        return []
    bounds = _compute_bounds(sessions)
    return [estimate_recovery_cost(s, bounds, weights) for s in sessions]
