"""
Schemas for the recommendation generator (System B) and the optional
combined-intelligence interface that blends association confidence
with an external "forgetting risk" signal.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TaskRecommendation(BaseModel):
    """A single recommended task for a given user/context."""

    task: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    support: float = Field(..., ge=0.0, le=1.0)
    lift: float = Field(..., ge=0.0)
    reason: str


class RecommendationRequest(BaseModel):
    user_id: str
    context: str
    completed_tasks: list[str] = Field(
        default_factory=list,
        description="Tasks already completed in this visit; excluded from output.",
    )


class RecommendationResponse(BaseModel):
    user_id: str
    context: str
    recommendations: list[TaskRecommendation]


class PrioritizedRecommendation(BaseModel):
    """Output of the combined-intelligence interface (System A + System B)."""

    task: str
    association_confidence: float = Field(..., ge=0.0, le=1.0)
    forgetting_probability: Optional[float] = Field(
        default=None,
        description="Probability supplied by an external forgetting-risk model. "
        "This module does not implement that model; a mock interface is provided for testing.",
    )
    priority_score: float = Field(
        ..., description="Combined score used to rank recommendations."
    )
    reason: str
