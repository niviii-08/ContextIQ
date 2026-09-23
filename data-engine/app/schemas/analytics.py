from pydantic import BaseModel
from typing import Dict, List, Any, Optional


class OverviewResponse(BaseModel):
    user_id: str
    period_days: int
    task_completion_rate: float
    task_forgetting_rate: float
    average_task_duration_minutes: float | None
    average_task_delay_minutes: float | None
    tasks_per_day: float
    tasks_per_category: dict[str, int]
    tasks_per_location: dict[str, int]
    total_tasks: int
    total_interruptions: int
    total_context_switches: int


class TaskAnalyticsResponse(BaseModel):
    user_id: str
    period_days: int
    total_tasks: int
    completion_rate: float
    forgetting_rate: float
    average_duration_minutes: float | None
    average_delay_minutes: float | None
    tasks_per_day: float
    tasks_per_category: dict[str, int]
    tasks_per_location: dict[str, int]
    forgetting_by_weekday: dict[str, float]
    forgetting_by_hour: dict[str, float]
    forgetting_by_category: dict[str, float]
    forgetting_by_location: dict[str, float]


class InterruptionAnalyticsResponse(BaseModel):
    user_id: str
    period_days: int
    interruption_count: int
    interruption_duration_minutes_total: float
    interruption_duration_minutes_avg: float | None
    interruption_by_weekday: dict[str, int]
    interruption_by_hour: dict[str, int]
    interruption_by_category: dict[str, int]


class ContextAnalyticsResponse(BaseModel):
    user_id: str
    period_days: int
    total_sessions: int
    average_focus_session_minutes: float | None
    total_context_switches: int
    resume_count: int
    pause_count: int
    average_resume_delay_seconds: float | None
    context_switching_by_task_category: dict[str, int]
    context_switching_by_location: dict[str, int]


class FrictionScoreResponse(BaseModel):
    user_id: str
    period_days: int
    label: str = "Experimental behavioural metric — not scientifically validated."
    overall_score: float
    forgetting_score: float
    interruption_score: float
    context_switch_score: float
    recovery_score: float
    formula_version: str = "1.0"


# New schemas for enhanced analytics

class DerivedMetricsResponse(BaseModel):
    user_id: str
    period_days: int
    forget_risk: Dict[str, float]
    context_switch_rate: Dict[str, float]
    interruption_rate: Dict[str, float]
    recovery_time: Dict[str, float]
    behavioral_friction_score: Dict[str, float]
    completion_reliability: Dict[str, float]
    context_consistency: Dict[str, float]
    repetition_strength: Dict[str, float]
    time_lost_to_interruptions: Dict[str, float]


class InsightResponse(BaseModel):
    insight_type: str
    message: str
    evidence: Dict[str, Any]
    risk_level: str
    recommendation: str
    error: Optional[str] = None


class AllInsightsResponse(BaseModel):
    user_id: str
    period_days: int
    insights: List[InsightResponse]
    generated_at: str


class TrendAnalysisResponse(BaseModel):
    user_id: str
    period_days: int
    metric_name: str
    slope: float
    r_squared: float
    trend_direction: str
    confidence: str
    sample_size: int


class DistributionResponse(BaseModel):
    metric_name: str
    statistics: Dict[str, float]
    sample_confidence: str


class CorrelationResponse(BaseModel):
    correlations: Dict[str, Dict[str, float]]
    sample_size: int
    sample_confidence: str
    method: str


class StoryAnalyticsResponse(BaseModel):
    user_id: str
    period_days: int
    narrative: str
    key_behaviors: List[str]
    patterns: List[str]
    evidence: List[Dict[str, Any]]
    risks: List[str]
    recommendations: List[str]
    data_traceability: Dict[str, str]


class TimelineEntry(BaseModel):
    timestamp: str
    task_id: str
    task_title: str
    location_id: str | None
    location_label: str | None
    context_tag: str | None
    event_type: str
    is_interruption: bool


class ContextSwitchTimelineResponse(BaseModel):
    user_id: str
    period_days: int
    timeline: List[TimelineEntry]


class TaskContextHeatmapResponse(BaseModel):
    user_id: str
    period_days: int
    metric: str
    rows: List[str]
    columns: List[str]
    cells: List[List[float | None]]
    sample_sizes: List[List[int]]
