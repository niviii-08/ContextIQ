"""
api/routes.py
==============
FastAPI routes. Thin layer: validates input via schemas, delegates to the
deterministic engines / LLM explanation service, returns validated output.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.daily_summary import generate_daily_summary as build_daily_summary
from app.feedback_store import default_store
from app.insight_engine import generate_insights
from app.llm.explanation_service import generate_explanation
from app.llm.provider import get_provider
from app.ranking import rank_insights
from app.recommendations import generate_recommendations as build_recommendations
from app.schemas import (
    DailySummaryRequest,
    FeedbackAck,
    FeedbackRequest,
    GenerateInsightsRequest,
    GenerateInsightsResponse,
    HealthResponse,
    LLMExplanationRequest,
    RecommendationsRequest,
    RecommendationsResponse,
)

router = APIRouter()


def _get_llm_provider():
    try:
        return get_provider(settings.llm_provider, settings.llm_api_key or None)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Requested explanation provider is unavailable.") from exc


@router.post("/api/v1/insights/generate", response_model=GenerateInsightsResponse)
def generate_insights_endpoint(request: GenerateInsightsRequest) -> GenerateInsightsResponse:
    insights = generate_insights(request.bundle)
    ranked = rank_insights(insights)

    if request.use_llm_explanations:
        provider = _get_llm_provider()
        for insight in ranked:
            explanation_request = LLMExplanationRequest(
                type=insight.type.value,
                payload={
                    "title": insight.title,
                    "description": insight.description,
                    "evidence": [e.model_dump() for e in insight.evidence],
                },
            )
            result = generate_explanation(explanation_request, provider)
            insight.description = result.text

    return GenerateInsightsResponse(insights=ranked)


@router.post("/api/v1/insights/daily")
def generate_daily_summary_endpoint(request: DailySummaryRequest):
    summary = build_daily_summary(request.bundle)
    return summary


@router.post("/api/v1/recommendations/generate", response_model=RecommendationsResponse)
def generate_recommendations_endpoint(request: RecommendationsRequest) -> RecommendationsResponse:
    recs = build_recommendations(request.bundle, max_recommendations=request.max_recommendations)
    return RecommendationsResponse(recommendations=recs)


@router.post("/api/v1/feedback", response_model=FeedbackAck)
def submit_feedback(request: FeedbackRequest) -> FeedbackAck:
    stored_id = default_store.save(request.entry)
    return FeedbackAck(status="stored", stored_id=stored_id)


@router.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", llm_provider=settings.llm_provider, version=settings.app_version)
