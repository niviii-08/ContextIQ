from datetime import datetime, timezone


def test_create_user(client):
    r = client.post("/api/v1/users", json={"email": "a@example.com", "display_name": "A"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@example.com"


def test_create_user_duplicate_email_conflict(client):
    client.post("/api/v1/users", json={"email": "dup@example.com"})
    r = client.post("/api/v1/users", json={"email": "dup@example.com"})
    assert r.status_code == 409


def test_get_user_not_found(client):
    import uuid

    r = client.get(f"/api/v1/users/{uuid.uuid4()}")
    assert r.status_code == 404


def test_create_location_requires_valid_user(client):
    import uuid

    r = client.post("/api/v1/locations", json={"user_id": str(uuid.uuid4()), "label": "Nowhere"})
    assert r.status_code == 404


def test_create_task_full_flow(client):
    user = client.post("/api/v1/users", json={"email": "flow@example.com"}).json()
    loc = client.post("/api/v1/locations", json={"user_id": user["id"], "label": "Desk"}).json()

    r = client.post(
        "/api/v1/tasks",
        json={
            "user_id": user["id"],
            "title": "Write tests",
            "category": "deep_work",
            "location_id": loc["id"],
            "priority": 4,
        },
    )
    assert r.status_code == 201
    task = r.json()
    assert task["status"] == "created"
    assert task["priority"] == 4


def test_task_event_updates_task_status(client):
    user = client.post("/api/v1/users", json={"email": "events@example.com"}).json()
    task = client.post("/api/v1/tasks", json={"user_id": user["id"], "title": "T1"}).json()

    now = datetime.now(timezone.utc).isoformat()
    r = client.post(
        "/api/v1/task-events",
        json={"user_id": user["id"], "task_id": task["id"], "event_type": "started", "event_time": now},
    )
    assert r.status_code == 201

    updated = client.get(f"/api/v1/tasks/{task['id']}").json()
    assert updated["status"] == "started"
    assert updated["started_at"] is not None


def test_task_event_rejects_mismatched_user(client):
    user1 = client.post("/api/v1/users", json={"email": "u1@example.com"}).json()
    user2 = client.post("/api/v1/users", json={"email": "u2@example.com"}).json()
    task = client.post("/api/v1/tasks", json={"user_id": user1["id"], "title": "T"}).json()

    now = datetime.now(timezone.utc).isoformat()
    r = client.post(
        "/api/v1/task-events",
        json={"user_id": user2["id"], "task_id": task["id"], "event_type": "started", "event_time": now},
    )
    assert r.status_code == 400


def test_create_interruption(client):
    user = client.post("/api/v1/users", json={"email": "interrupt@example.com"}).json()
    task = client.post("/api/v1/tasks", json={"user_id": user["id"], "title": "T"}).json()

    now = datetime.now(timezone.utc).isoformat()
    r = client.post(
        "/api/v1/interruptions",
        json={
            "user_id": user["id"],
            "task_id": task["id"],
            "interruption_type": "phone",
            "start_time": now,
            "duration_seconds": 30,
        },
    )
    assert r.status_code == 201
    assert r.json()["duration_seconds"] == 30


def test_interruption_duration_derived_from_start_end(client):
    user = client.post("/api/v1/users", json={"email": "dur@example.com"}).json()
    start = datetime.now(timezone.utc)
    end = start.replace(microsecond=0)
    from datetime import timedelta

    end = start + timedelta(seconds=90)

    r = client.post(
        "/api/v1/interruptions",
        json={
            "user_id": user["id"],
            "interruption_type": "message",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )
    assert r.status_code == 201
    assert r.json()["duration_seconds"] == 90
