import os, sys, uuid
os.environ.setdefault("DATABASE_URL", "sqlite:///./_env_check.db")
os.environ["APP_ENV"] = "development"
sys.path.insert(0, ".")

from app.core.config import get_settings
get_settings.cache_clear()

from fastapi.testclient import TestClient
from app.main import app
from app.core import deps

class MockScalarList:
    def all(self): return []

class MockSession:
    def __init__(self): self._stub = {}
    def scalar(self, stmt): return None
    def scalars(self, stmt): return MockScalarList()
    def get(self, cls, pk):
        if cls.__name__ == "User":
            class FR: id = FUID; email = "f@e.com"
            return FR()
        return None
    def add(self, o): pass
    def commit(self): pass
    def refresh(self, o): pass
    def flush(self): pass

def mock_db_factory():
    def inner(): yield MockSession()
    return inner

FUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
app.dependency_overrides.clear()
app.dependency_overrides[deps.get_current_user_id] = lambda: FUID
app.dependency_overrides[deps.get_current_user] = lambda: type("U", (), {"id": FUID, "email": "f@e.com"})()
app.dependency_overrides[deps.get_db] = mock_db_factory()
c = TestClient(app, raise_server_exceptions=False)

r = c.get("/api/v1/predictions/forgetting/task/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
print(f"AC-2 404 status={r.status_code} body={r.json()}")
assert r.status_code == 404
j = r.json()
assert "error" in j, f"Expected 'error' envelope key, got keys: {j.keys()}"
assert j["error"]["type"] == "NotFoundError", f"Got type: {j['error']['type']}"
assert "Prediction not found" in j["error"]["message"]
print("  -> AC-2 PASS (NotFoundError envelope)\n")

r2 = c.get("/api/v1/predictions/forgetting?risk_level=INVALID_LEVEL")
print(f"AC-3 422 status={r2.status_code} body={r2.json()}")
assert r2.status_code == 422
j2 = r2.json()
assert "error" in j2
assert j2["error"]["type"] == "ValidationError", f"Got type: {j2['error']['type']}"
assert "Invalid risk_level" in j2["error"]["message"]
print("  -> AC-3 PASS (ValidationError envelope)\n")

r3 = c.post("/api/v1/recommendations/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/feedback", json={"action": "ACCEPTED"})
print(f"AC-4 404 status={r3.status_code} body={r3.json()}")
assert r3.status_code == 404
j3 = r3.json()
assert "error" in j3
assert j3["error"]["type"] == "NotFoundError"
assert j3["error"]["message"] == "Recommendation not found."
print("  -> AC-4 PASS (recommendations NotFoundError envelope)\n")

from app.core.errors import ValidationError
e = ValidationError("custom msg")
assert e.status_code == 422
assert e.default_message == "Validation failed."
assert e.message == "custom msg"
print("AC-5: ValidationError attrs OK")
print("  -> AC-5 PASS\n")

import pathlib
f = pathlib.Path("../context-engine/tests/test_recommender.py").read_text()
assert 'pytest.importorskip("mlxtend", reason="mlxtend optional dependency not installed")' in f
print("AC-6: test_recommender.py has importorskip")
print("  -> AC-6 PASS\n")

print("=== ALL ACCEPTANCE CRITERIA SELF-VERIFIED ===")
