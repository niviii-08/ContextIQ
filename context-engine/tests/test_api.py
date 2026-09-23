from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.state import store


def _iso(offset_seconds):
    return (datetime(2026, 1, 1, 9, 0, 0) + timedelta(seconds=offset_seconds)).isoformat()


def _sample_events():
    events = []
    # Several department visits with a strong collect_form -> submit_record association.
    for i in range(8):
        base = i * 10000
        events.append(
            {
                "user_id": "user_001",
                "timestamp": _iso(base),
                "task_id": f"collect_form_{i}",
                "task_category": "admin",
                "context": "department",
                "event_type": "START",
            }
        )
        events.append(
            {
                "user_id": "user_001",
                "timestamp": _iso(base + 60),
                "task_id": f"collect_form_{i}",
                "task_category": "admin",
                "context": "department",
                "event_type": "COMPLETE",
            }
        )
        events.append(
            {
                "user_id": "user_001",
                "timestamp": _iso(base + 90),
                "task_id": f"submit_record_{i}",
                "task_category": "admin",
                "context": "department",
                "event_type": "START",
            }
        )
        events.append(
            {
                "user_id": "user_001",
                "timestamp": _iso(base + 150),
                "task_id": f"submit_record_{i}",
                "task_category": "admin",
                "context": "department",
                "event_type": "COMPLETE",
            }
        )
    return events


def setup_function(_):
    # Ensure a clean in-memory store between tests since it's process-global.
    store.sessions_by_context.clear()
    store.rules_by_context.clear()
    store.dismissal_store.clear()


def test_health_check():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_context_endpoint():
    client = TestClient(app)
    resp = client.post("/api/v1/context/analyze", json={"events": _sample_events()})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["sessions"]) == 16  # 8 collect_form + 8 submit_record sessions
    assert body["metrics"]["num_sessions"] == 16


def test_analyze_context_rejects_empty_batch():
    client = TestClient(app)
    resp = client.post("/api/v1/context/analyze", json={"events": []})
    assert resp.status_code == 400


def test_get_associations_after_analyze():
    client = TestClient(app)
    client.post("/api/v1/context/analyze", json={"events": _sample_events()})
    resp = client.get("/api/v1/context/department/associations")
    assert resp.status_code == 200
    body = resp.json()
    assert body["context"] == "department"
    assert len(body["rules"]) > 0


def test_get_associations_unknown_context_404():
    client = TestClient(app)
    resp = client.get("/api/v1/context/nonexistent_context/associations")
    assert resp.status_code == 404


def test_recommendations_post_endpoint():
    client = TestClient(app)
    client.post("/api/v1/context/analyze", json={"events": _sample_events()})
    resp = client.post(
        "/api/v1/recommendations/context",
        json={"user_id": "user_001", "context": "department", "completed_tasks": []},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["context"] == "department"
    assert isinstance(body["recommendations"], list)


def test_recommendations_get_endpoint():
    client = TestClient(app)
    client.post("/api/v1/context/analyze", json={"events": _sample_events()})
    resp = client.get("/api/v1/recommendations/context/department", params={"user_id": "user_001"})
    assert resp.status_code == 200


def test_recommendations_unknown_context_404():
    client = TestClient(app)
    resp = client.post(
        "/api/v1/recommendations/context",
        json={"user_id": "user_001", "context": "nowhere", "completed_tasks": []},
    )
    assert resp.status_code == 404
