"""
Schemas for transactions and association-rule mining results
used by System B ("One More Thing" contextual task discovery).
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ContextTransaction(BaseModel):
    """One 'basket' of tasks completed together within a single context visit."""

    transaction_id: str
    user_id: str
    context: str
    tasks: list[str]
    timestamp: Optional[str] = None


class AssociationRule(BaseModel):
    """A single mined association rule: antecedent(s) -> consequent(s)."""

    context: str
    antecedents: list[str]
    consequents: list[str]
    support: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    weighted_confidence: Optional[float] = Field(default=None, ge=0.0)
    lift: float = Field(..., ge=0.0)
    leverage: Optional[float] = None
    conviction: Optional[float] = None


class ContextAssociationResult(BaseModel):
    """Response payload for GET /api/v1/context/{context_id}/associations."""

    context: str
    num_transactions: int
    frequent_itemsets_count: int
    rules: list[AssociationRule]
    algorithm: str = Field(..., description="'apriori' or 'fpgrowth'")
    thresholds: dict
