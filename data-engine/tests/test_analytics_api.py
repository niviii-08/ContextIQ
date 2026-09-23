import uuid
from datetime import datetime, timedelta, timezone


def _seed_basic_activity(client):
    user = client.post("/api/v1/users", json={"email": "analytics@example.com"}).json()
    loc = client.post("/api/v1/locations", json={"user_id": user["id"], "label": "Office"}).json()

    t0 = datetime.now(timezone.utc) - timedelta(days=1)

    # Task 1: completed
    task1 = client.post(
        "/api/v1/tasks",
        json={"user_id": user["id"], "title": "Completed task", "category": "deep_work", "location_id": loc["id"]},
    ).json()
    client.post(
        "/api/v1/task-events",
        json={"user_id": user["id"], "task_id": task1["id"], "event_type": "started", "event_time": t0.isoformat()},
    )
    client.post(
        "/api/v1/task-events",
        json={
            "user_id": user["id"],
            "task_id": task1["id"],
            "event_type": "completed",
            "event_time": (t0 + timedelta(minutes=30)).isoformat(),
        },
    )

    # Task 2: forgotten
    task2 = client.post(
        "/api/v1/tasks",
        json={"user_id": user["id"], "title": "Forgotten task", "category": "email", "location_id": loc["id"]},
    ).json()
    client.post(
        "/api/v1/task-events",
        json={
            "user_id": user["id"],
            "task_id": task2["id"],
            "event_type": "forgotten",
            "event_time": (t0 + timedelta(hours=5)).isoformat(),
        },
    )

    # An interruption on task 1
    client.post(
        "/api/v1/interruptions",
        json={
            "user_id": user["id"],
            "task_id": task1["id"],
            "interruption_type": "phone",
            "start_time": (t0 + timedelta(minutes=10)).isoformat(),
            "duration_seconds": 400,
        },
    )

    client.post("/api/v1/context-sessions/rebuild", params={"user_id": user["id"]})
    return user["id"]


def test_overview_endpoint(client):
    user_id = _seed_basic_activity(client)
    r = client.get("/api/v1/analytics/overview", params={"user_id": user_id, "period_days": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["total_tasks"] == 2
    assert body["task_completion_rate"] == 0.5
    assert body["task_forgetting_rate"] == 0.5


def test_task_analytics_endpoint(client):
    user_id = _seed_basic_activity(client)
    r = client.get("/api/v1/analytics/tasks", params={"user_id": user_id, "period_days": 30})
    assert r.status_code == 200
    body = r.json()
    assert "email" in body["tasks_per_category"]
    assert "deep_work" in body["tasks_per_category"]


def test_interruption_analytics_endpoint(client):
    user_id = _seed_basic_activity(client)
    r = client.get("/api/v1/analytics/interruptions", params={"user_id": user_id, "period_days": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["interruption_count"] == 1


def test_context_analytics_endpoint(client):
    user_id = _seed_basic_activity(client)
    r = client.get("/api/v1/analytics/context", params={"user_id": user_id, "period_days": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["total_sessions"] >= 1


def test_friction_endpoint(client):
    user_id = _seed_basic_activity(client)
    r = client.get("/api/v1/analytics/friction", params={"user_id": user_id, "period_days": 30})
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["overall_score"] <= 100.0
    assert "not scientifically validated" in body["label"]


def test_analytics_endpoints_404_for_unknown_user(client):
    unknown_id = str(uuid.uuid4())
    for path in ["overview", "tasks", "interruptions", "context", "friction"]:
        r = client.get(f"/api/v1/analytics/{path}", params={"user_id": unknown_id})
        assert r.status_code == 404


def test_analytics_endpoints_handle_user_with_no_data(client):
    user = client.post("/api/v1/users", json={"email": "empty@example.com"}).json()
    r = client.get("/api/v1/analytics/overview", params={"user_id": user["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["total_tasks"] == 0
    assert body["task_completion_rate"] == 0.0


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
