import os

os.environ.setdefault("LLM_PROVIDER", "mock")

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _bundle_payload():
    return {
        "user_id": "user_123",
        "forgetting_predictions": [
            {
                "task": "Lab Record",
                "probability": 0.82,
                "risk_level": "high",
                "model_version": "v1",
                "previous_forgetting_count": 4,
                "weekday_pattern": "Monday",
            }
        ],
        "context_insights": [
            {
                "switch_count": 7,
                "interruption_time_minutes": 22.0,
                "recovery_cost_minutes": 18.0,
                "top_interruption": "Slack",
                "affected_category": "Department tasks",
                "period": "2026-08-18",
            }
        ],
        "associations": [
            {"context": "Department", "task": "Collect Form", "support": 0.4, "confidence": 0.78, "lift": 1.6}
        ],
        "metrics": [],
    }


def test_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "mock"


def test_generate_insights_endpoint():
    resp = client.post(
        "/api/v1/insights/generate",
        json={"bundle": _bundle_payload(), "use_llm_explanations": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "insights" in body
    assert len(body["insights"]) > 0


def test_generate_insights_without_llm():
    resp = client.post(
        "/api/v1/insights/generate",
        json={"bundle": _bundle_payload(), "use_llm_explanations": False},
    )
    assert resp.status_code == 200


def test_daily_summary_endpoint():
    resp = client.post("/api/v1/insights/daily", json={"bundle": _bundle_payload()})
    assert resp.status_code == 200
    body = resp.json()
    assert body["highest_risk_task"] == "Lab Record"


def test_recommendations_endpoint():
    resp = client.post(
        "/api/v1/recommendations/generate",
        json={"bundle": _bundle_payload(), "max_recommendations": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "recommendations" in body


def test_feedback_endpoint():
    resp = client.post(
        "/api/v1/feedback",
        json={
            "entry": {
                "user_id": "user_123",
                "target_type": "insight",
                "target_id": "insight_1",
                "feedback": "useful",
            }
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stored"
    assert body["stored_id"]


def test_invalid_bundle_returns_422():
    resp = client.post(
        "/api/v1/insights/generate",
        json={"bundle": {"user_id": "u1", "forgetting_predictions": [{"task": "X", "probability": 5.0}]}},
    )
    assert resp.status_code == 422
