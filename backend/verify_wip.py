import os
import sys
import uuid
import warnings

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./_verify_wip.db")
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.core import deps
from app.core.config import get_settings

FAKE_UID = uuid.UUID("11111111-1111-1111-1111-111111111111")
FAKE_UID_STR = str(FAKE_UID)

class FakeUserRow:
    id = FAKE_UID
    email = "fake@example.com"

class MockScalarList:
    def all(self): return []

class MockSession:
    """Minimal SQLAlchemy Session mock that returns empty/None queries,
    plus an optional row-store for specific scalars via ._stub_rows."""
    def __init__(self):
        self._stub_rows = {}  # key => value for .scalar() on specific stmts
        self._last_added = []
    def scalar(self, stmt):
        key = str(stmt)[:80]
        return self._stub_rows.get(key, None)
    def scalars(self, stmt):
        return MockScalarList()
    def get(self, cls, pk):
        if cls.__name__ == "User":
            return FakeUserRow()
        return None
    def add(self, obj): self._last_added.append(obj)
    def commit(self): pass
    def refresh(self, obj): pass
    def flush(self): pass

results = []
def check(label, cond):
    status = "OK" if cond else "FAIL"
    results.append((label, status))
    print(f"  [{status}] {label}")

def mock_db_factory():
    def inner():
        yield MockSession()
    return inner

FAKE_USER = FakeUserRow()

def fake_uid():
    return FAKE_UID

def fake_user():
    return FAKE_USER

# =========================================================================
# TR-2 Predictions Route (APP_ENV=development)
# =========================================================================
os.environ["APP_ENV"] = "development"
get_settings.cache_clear()
assert get_settings().APP_ENV == "development"
app.dependency_overrides.clear()
app.dependency_overrides[deps.get_current_user_id] = fake_uid
app.dependency_overrides[deps.get_current_user] = fake_user
app.dependency_overrides[deps.get_db] = mock_db_factory()
c = TestClient(app, raise_server_exceptions=False)

print("=== TR-2 Predictions Route ===")

r = c.get("/api/v1/predictions/forgetting/task/not-a-uuid")
check(f"TR-2.1 invalid UUID -> 422 (got {r.status_code})", r.status_code == 422)

missing = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
r2 = c.get(f"/api/v1/predictions/forgetting/task/{missing}")
# MockSession.scalar returns None => route raises HTTPException(404)
check(f"TR-2.2 missing UUID -> 404 (got {r2.status_code})", r2.status_code == 404)

r3 = c.get("/api/v1/predictions/forgetting?risk_level=NOT_A_LEVEL")
check(f"TR-2.3 risk_level=INVALID -> 422 (got {r3.status_code})", r3.status_code == 422)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    r5 = c.get("/api/v1/predictions/forgetting?risk_level=low")
    check(f"TR-2.5 risk_level=low case-insensitive ok (got {r5.status_code})", r5.status_code != 422)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    r4 = c.get("/api/v1/predictions/forgetting?riskLevel=LOW")
    has_dep = any(issubclass(x.category, DeprecationWarning) for x in w)
    check(f"TR-2.4 riskLevel alias status={r4.status_code}, deprecation={has_dep}", r4.status_code != 422 and has_dep)

# =========================================================================
# TR-3.5 Tasks query context_tag bound
# =========================================================================
print()
print("=== TR-3.5 Tasks query context_tag bound ===")
tag_65 = "x" * 65
tag_64 = "x" * 64
r_long = c.get(f"/api/v1/tasks?context_tag={tag_65}")
r_ok = c.get(f"/api/v1/tasks?context_tag={tag_64}")
check(f"TR-3.5 tag=65 chars -> 422 (got {r_long.status_code})", r_long.status_code == 422)
check(f"TR-3.5 tag=64 chars -> ok (got {r_ok.status_code}, != 422)", r_ok.status_code != 422)

# =========================================================================
# TR-4.1 TR-4.2 Staging env gating (APP_ENV=staging, NO deps overrides)
# =========================================================================
print()
print("=== TR-4 Security env-gated routes (APP_ENV=staging) ===")
app.dependency_overrides.clear()
# For staging: get_current_user / get_current_user_id should NOT be overridden
# — we want the real staging-only gating to fire. We still need a real DB though.
os.environ["APP_ENV"] = "staging"
get_settings.cache_clear()
stg_settings = get_settings()
assert stg_settings.APP_ENV == "staging", f"Settings not staging: {stg_settings.APP_ENV}"
print(f"  (Settings.APP_ENV={stg_settings.APP_ENV})")

# Provide a minimal Session mock (not user override) for staging tests
# — /register doesn't use user dep, but db.get(User, ...) is called inside create_user
# — /tasks uses get_current_user_id which 401s before hitting DB
app.dependency_overrides[deps.get_db] = mock_db_factory()

c2 = TestClient(app, raise_server_exceptions=False)
r_41 = c2.get("/api/v1/tasks", headers={"X-User-Id": FAKE_UID_STR})
check(f"TR-4.1 staging + X-User-Id /tasks -> 401 (got {r_41.status_code})", r_41.status_code == 401)

r_42 = c2.post("/api/v1/users/register", json={"email": "x@y.z", "password": "pw123456", "display_name": "Test User"})
check(f"TR-4.2 staging /register -> 404 (got {r_42.status_code})", r_42.status_code == 404)

# =========================================================================
# TR-4.4 recommendations cross-user prefill_location_id code presence check
# =========================================================================
print()
print("=== TR-4.4 prefill_location_id ownership guard ===")
try:
    import inspect
    from app.api.v1 import recommendations as rec_mod
    src = inspect.getsource(rec_mod)
    has_logger = hasattr(rec_mod, 'logger') and rec_mod.logger is not None
    has_safe_var = 'safe_location_id' in src
    has_ownership_select = 'Location.id' in src and 'Location.user_id' in src
    debug_log = "dropping" in src or "does not belong" in src or "prefill_location_id" in src
    check(
        f"TR-4.4 recommendations: logger={has_logger}, safe_var={has_safe_var}, ownership_select={has_ownership_select}, debug_log_str={debug_log}",
        has_logger and has_safe_var and has_ownership_select,
    )
except Exception as e:
    check(f"TR-4.4 code inspection (exception: {type(e).__name__}: {e})", False)

# =========================================================================
# Summary
# =========================================================================
print()
print("=" * 60)
fail_count = sum(1 for _, s in results if s == "FAIL")
for label, status in results:
    print(f"  [{status}] {label}")
print()
print(f"RESULT: {len(results)-fail_count}/{len(results)} PASSED, {fail_count} FAILED")
sys.exit(0 if fail_count == 0 else 1)
