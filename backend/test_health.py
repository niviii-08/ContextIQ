import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./_test_backend.db")

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_is_reachable():
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code in {200, 503}
    assert "database" in response.json()