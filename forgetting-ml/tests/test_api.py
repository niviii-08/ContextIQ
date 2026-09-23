from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    r = client.get("/")
    assert r.status_code == 200
    assert "predict_endpoint" in r.json()


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "model_version" in body


def test_predict_endpoint_valid(sample_task_payload):
    r = client.post("/api/v1/predictions/forgetting", json=sample_task_payload)
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["prediction_probability"] <= 1.0
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert len(body["top_features"]) > 0


def test_predict_endpoint_invalid_category(sample_task_payload):
    payload = dict(sample_task_payload)
    payload["task_category"] = "NotReal"
    r = client.post("/api/v1/predictions/forgetting", json=payload)
    assert r.status_code == 422


def test_predict_endpoint_missing_field(sample_task_payload):
    payload = dict(sample_task_payload)
    del payload["deadline_distance_hours"]
    r = client.post("/api/v1/predictions/forgetting", json=payload)
    assert r.status_code == 422


def test_batch_predict_endpoint(sample_task_payload):
    r = client.post(
        "/api/v1/predictions/forgetting/batch",
        json={"tasks": [sample_task_payload, sample_task_payload]},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["predictions"]) == 2


def test_batch_predict_empty_list():
    r = client.post("/api/v1/predictions/forgetting/batch", json={"tasks": []})
    assert r.status_code == 200
    assert r.json()["predictions"] == []
