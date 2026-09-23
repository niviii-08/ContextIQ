"""
API routes for System B ("One More Thing" recommendations).

    POST /api/v1/recommendations/context
    GET  /api/v1/recommendations/context/{context_id}
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.recommendations import RecommendationRequest, RecommendationResponse
from app.state import store

import httpx
from pydantic import BaseModel

from ml.associations.recommender import RecommendationQualityConfig, recommend_for_context, prioritize_recommendations, ForgettingRiskProvider

router = APIRouter()

class ApiForgettingRiskProvider(ForgettingRiskProvider):
    def __init__(self, backend_url: str = "http://backend:8000"):
        self.backend_url = backend_url
        self.client = httpx.Client(timeout=2.0)

    def get_forgetting_probability(self, user_id: str, task: str) -> float | None:
        try:
            # We assume task is the UUID here since recommend_for_context works with tasks.
            # If task is a string name, we might need a different lookup.
            resp = self.client.get(f"{self.backend_url}/api/v1/predictions/forgetting/task/{task}", params={"user_id": user_id})
            if resp.status_code == 200:
                data = resp.json()
                if data and "riskScore" in data:
                    return data["riskScore"] / 100.0  # normalize back to 0-1
            return None
        except Exception:
            return None

@router.post("/context", response_model=RecommendationResponse)
def post_context_recommendations(req: RecommendationRequest) -> RecommendationResponse:
    """Generate ranked task recommendations for a user's current context visit."""
    rules = store.get_rules(req.context)
    if not rules:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No association rules available for context '{req.context}'. "
                "Submit events via POST /api/v1/context/analyze first."
            ),
        )

    recommendations = recommend_for_context(
        user_id=req.user_id,
        context=req.context,
        rules=rules,
        completed_tasks=req.completed_tasks,
        config=RecommendationQualityConfig(),
        dismissal_store=store.dismissal_store,
    )
    
    provider = ApiForgettingRiskProvider()
    prioritized = prioritize_recommendations(req.user_id, recommendations, forgetting_provider=provider)

    return RecommendationResponse(
        user_id=req.user_id, context=req.context, recommendations=prioritized
    )


@router.get("/context/{context_id}", response_model=RecommendationResponse)
def get_context_recommendations(context_id: str, user_id: str) -> RecommendationResponse:
    """Convenience GET variant: same as POST but with no completed_tasks filter,
    for quick polling/refresh use cases (e.g. a client re-fetching the current
    'one more thing' suggestion for a context)."""
    rules = store.get_rules(context_id)
    if not rules:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No association rules available for context '{context_id}'. "
                "Submit events via POST /api/v1/context/analyze first."
            ),
        )

    recommendations = recommend_for_context(
        user_id=user_id,
        context=context_id,
        rules=rules,
        completed_tasks=[],
        config=RecommendationQualityConfig(),
        dismissal_store=store.dismissal_store,
    )
    
    provider = ApiForgettingRiskProvider()
    prioritized = prioritize_recommendations(user_id, recommendations, forgetting_provider=provider)

    return RecommendationResponse(
        user_id=user_id, context=context_id, recommendations=prioritized
    )
