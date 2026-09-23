"""
Schemas describing reconstructed sessions, context-switch metrics,
discovered behavioural patterns, and recovery cost estimates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReconstructedSession(BaseModel):
    """A single reconstructed work session for one user/task run."""

    session_id: str
    user_id: str
    task_id: str
    task_category: str
    context: str
    start_time: datetime
    end_time: Optional[datetime] = None

    session_duration_seconds: float = 0.0
    focused_time_seconds: float = 0.0
    interruption_time_seconds: float = 0.0
    num_interruptions: int = 0
    num_context_switches: int = 0
    resume_delays_seconds: list[float] = Field(default_factory=list)
    interruption_durations_seconds: list[float] = Field(default_factory=list)
    completed: bool = False


class SessionMetrics(BaseModel):
    """Aggregate metrics computed across one or more reconstructed sessions."""

    scope: str = Field(..., description="e.g. 'user:123' or 'user:123:task_category:programming'")
    num_sessions: int
    total_focused_time_seconds: float
    total_interruption_time_seconds: float
    total_interruptions: int
    total_context_switches: int
    average_interruption_duration_seconds: float
    average_resume_delay_seconds: float
    switches_per_hour: float
    interruptions_per_session: float
    average_session_duration_seconds: float


class BehaviouralPattern(BaseModel):
    """A single discovered behavioural pattern with supporting evidence."""

    pattern_id: str
    pattern_type: str = Field(
        ..., description="e.g. 'frequency', 'cluster', 'anomaly', 'sequence'"
    )
    description: str
    evidence: dict = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)


class RecoveryCostEstimate(BaseModel):
    """Transparent, feature-based estimate of context recovery cost."""

    session_id: str
    recovery_cost_score: float = Field(
        ..., description="Unitless score in [0, 1]; higher = costlier recovery. "
        "Not a validated psychological measure."
    )
    contributing_features: dict = Field(default_factory=dict)
    formula_version: str = "recovery_cost_v1"


class ContextAnalysisResult(BaseModel):
    """Full response payload for POST /api/v1/context/analyze."""

    sessions: list[ReconstructedSession]
    metrics: SessionMetrics
    patterns: list[BehaviouralPattern]
    recovery_estimates: list[RecoveryCostEstimate]
