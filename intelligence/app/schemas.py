"""
schemas.py
==========
Pydantic data contracts for the Behaviour Intelligence + LLM Explanation module.

These schemas define the ONLY way structured data enters and leaves this module.
Nothing in this module invents data outside of what validates against these models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, confloat, conint


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class InsightType(str, Enum):
    FREQUENT_FORGETTING = "frequent_forgetting"
    REPEATED_CONTEXT_SWITCHING = "repeated_context_switching"
    LOCATION_DEPENDENT_FORGETTING = "location_dependent_forgetting"
    HIGH_INTERRUPTION_COST = "high_interruption_cost"
    REPEATED_CONTEXTUAL_ASSOCIATION = "repeated_contextual_association"
    INCREASING_FRICTION = "increasing_friction"
    DECREASING_FRICTION = "decreasing_friction"


class FeedbackType(str, Enum):
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"
    INCORRECT = "incorrect"
    DISMISSED = "dismissed"


# ---------------------------------------------------------------------------
# 1. INPUT CONTRACT — outputs of upstream ML systems
# ---------------------------------------------------------------------------

class ForgettingPrediction(BaseModel):
    """Output of the (external) forgetting-prediction model."""

    task: str
    probability: confloat(ge=0.0, le=1.0)
    risk_level: RiskLevel
    model_version: str
    contributing_features: List[str] = Field(default_factory=list)
    previous_forgetting_count: Optional[conint(ge=0)] = None
    weekday_pattern: Optional[str] = None
    timestamp: Optional[datetime] = None

    model_config = {'protected_namespaces': ()}


class ContextInsight(BaseModel):
    """Output of the (external) context-switch analysis system."""

    switch_count: conint(ge=0)
    interruption_time_minutes: confloat(ge=0.0)
    recovery_cost_minutes: confloat(ge=0.0)
    top_interruption: Optional[str] = None
    affected_category: Optional[str] = None
    period: Optional[str] = None


class Association(BaseModel):
    """Output of the (external) association-mining system."""

    context: str
    task: str
    support: confloat(ge=0.0, le=1.0)
    confidence: confloat(ge=0.0, le=1.0)
    lift: confloat(ge=0.0)


class BehaviourMetric(BaseModel):
    """A single named/valued behavioural metric over a period."""

    metric_name: str
    value: float
    period: str


class IntelligenceBundle(BaseModel):
    """The full set of structured inputs the engine operates on for a user/day."""

    user_id: str
    forgetting_predictions: List[ForgettingPrediction] = Field(default_factory=list)
    context_insights: List[ContextInsight] = Field(default_factory=list)
    associations: List[Association] = Field(default_factory=list)
    metrics: List[BehaviourMetric] = Field(default_factory=list)
    generated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 2. OUTPUT CONTRACT — insights
# ---------------------------------------------------------------------------

class Evidence(BaseModel):
    """A single traceable evidence item pulled directly from structured input.

    `field` + `value` must be traceable back to a source input object so the
    insight can never rely on invented statistics.
    """

    field: str
    value: str
    source: str  # e.g. "ForgettingPrediction:Lab Record"


class Insight(BaseModel):
    type: InsightType
    title: str
    description: str
    evidence: List[Evidence]
    priority: Priority
    confidence: Optional[confloat(ge=0.0, le=1.0)] = None
    source: str  # which upstream system(s) this was derived from


class RankedInsight(Insight):
    rank_score: float
    rank_position: int


# ---------------------------------------------------------------------------
# 3/4. Daily summary
# ---------------------------------------------------------------------------

class DailySummary(BaseModel):
    biggest_friction: Optional[str] = None
    highest_risk_task: Optional[str] = None
    highest_risk_probability: Optional[confloat(ge=0.0, le=1.0)] = None
    context_reminder: Optional[str] = None
    estimated_avoidable_friction_minutes: Optional[float] = None
    top_insights: List[Insight] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 5. LLM explanation contract
# ---------------------------------------------------------------------------

class LLMExplanationRequest(BaseModel):
    """Structured, minimal JSON handed to the LLM for a single explanation."""

    type: str
    payload: dict  # must contain ONLY values traceable to structured inputs


class LLMExplanationResult(BaseModel):
    text: str
    used_fallback: bool = False
    validation_passed: bool
    rejected_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# 6. Recommendations
# ---------------------------------------------------------------------------

class Recommendation(BaseModel):
    id: str
    user_id: str
    recommendation_type: str
    triggering_behaviour: str
    evidence: List[Evidence] = Field(default_factory=list)
    evidence_strength: confloat(ge=0.0, le=1.0)
    impact_score: confloat(ge=0.0, le=1.0)
    risk_level: Priority
    expected_benefit: str
    generated_at: datetime
    context: str
    associated_task: str
    association_confidence: confloat(ge=0.0, le=1.0)
    forgetting_probability: Optional[confloat(ge=0.0, le=1.0)] = None
    headline: str
    explanation: str
    priority: Priority
    rank_score: float
    feedback: List[FeedbackType] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 7. Feedback
# ---------------------------------------------------------------------------

class FeedbackEntry(BaseModel):
    user_id: str
    target_type: str  # "insight" | "recommendation" | "summary"
    target_id: str
    feedback: FeedbackType
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeedbackAck(BaseModel):
    status: str
    stored_id: str


# ---------------------------------------------------------------------------
# API request/response wrappers
# ---------------------------------------------------------------------------

class GenerateInsightsRequest(BaseModel):
    bundle: IntelligenceBundle
    use_llm_explanations: bool = True


class GenerateInsightsResponse(BaseModel):
    insights: List[RankedInsight]


class DailySummaryRequest(BaseModel):
    bundle: IntelligenceBundle
    use_llm_explanations: bool = True


class RecommendationsRequest(BaseModel):
    bundle: IntelligenceBundle
    max_recommendations: conint(ge=1, le=50) = 5


class RecommendationsResponse(BaseModel):
    recommendations: List[Recommendation]


class FeedbackRequest(BaseModel):
    entry: FeedbackEntry


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    version: str
