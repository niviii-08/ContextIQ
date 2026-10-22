# ContextIQ - Consistency, Reliability & Test-Portability Improvements (Round 2)

## Overview
- **Summary**: Close the remaining gaps after the first round of hardening: make the backend verification script runnable without PostgreSQL drivers, unify error-response shapes across every API route by consistently using the centralized domain error classes, add a `ValidationError` domain class for manual 422s, and complete the graceful-mlxtend-missing coverage in the last unprotected context-engine test file.
- **Purpose**: Achieve fully uniform API error semantics (so frontend clients can rely on a single error envelope shape), eliminate the last remaining "you must install psycopg / you must install mlxtend" hard crashes in test/verification entry points, and leave the project with zero "ModuleNotFoundError at import time" entry points for unit-level verification.
- **Target Users**: Anyone running `backend/verify_wip.py` without a local PostgreSQL install, API clients consuming error responses, CI running subset test modules on minimal venvs, and future maintainers adding routes who need a clear, already-used pattern for every error status code.

## Goals
- **Goal 1 (Portability)**: `python verify_wip.py` runs from the `backend/` directory on a stock Python environment that has only the backend `requirements.txt` packages **without** `psycopg[binary]` installed. No `ModuleNotFoundError` during import phase.
- **Goal 2 (Error Consistency)**: Every route in `backend/app/api/v1/*.py` that returns a 4xx status code uses the centralized `ContextIQError` subclass hierarchy (or FastAPI's native `RequestValidationError`), so the JSON error envelope is always `{"error": {"type": "...", "message": "..."}}` — never a mix of that shape and `{"detail": "..."}` from raw `HTTPException`.
- **Goal 3 (Graceful deps)**: Every test file in `context-engine/tests/` that transitively depends on `mlxtend` either (a) passes a `pytest.importorskip` at module load time, or (b) raises `NotImplementedError` with the install message. No test file raises raw `RuntimeError` or crashes during pytest collection.

## Non-Goals
- **Excluded**: Adding new API endpoints, new routers, or new features.
- **Excluded**: Changing any request/response body shape for successful (2xx) responses.
- **Excluded**: Implementing real Supabase Auth / JWT verification — the dev-only `X-User-Id` fallback boundary is preserved.
- **Excluded**: Docker, CI, deployment, or observability-stack changes.
- **Excluded**: Changes to ML model math, metric definitions, or prediction logic.

## Background & Context
- The first round of hardening (see prior spec & tasks in this folder) addressed startup blockers, UUID typing, query-param bounds, security gating, frontend pool-timeout fixes, and time-window test alignment. Code review of the current state shows these items are all in place.
- Remaining gaps found on 2026-09-28 review:
  1. `backend/verify_wip.py` has no `DATABASE_URL` override to SQLite and imports `app.main` directly; import-time `app/db/session.py` calls `create_engine(postgresql+psycopg://...)` → `ModuleNotFoundError: No module named 'psycopg'` on any machine that hasn't installed the binary wheel for psycopg. Compare `backend/test_health.py` which correctly sets `os.environ.setdefault("DATABASE_URL", "sqlite:///./_test_backend.db")` **before** importing `app.main`.
  2. `predictions.py` uses raw `HTTPException(status_code=404, detail="Prediction not found for task.")` and raw `HTTPException(status_code=422, detail=f"Invalid risk_level...")`. Because `errors.py` only installs handlers for `ContextIQError` subclasses and the `RequestValidationError` Pydantic exception, raw `HTTPException` falls through to FastAPI's default handler, producing `{"detail": "..."}` — a different envelope from `task_service.get_task` which raises `NotFoundError("Task not found.")` → `{"error": {"type": "NotFoundError", "message": "Task not found."}}`.
  3. `recommendations.py` feedback endpoint uses raw `HTTPException(status_code=404, detail="Recommendation not found.")` — same envelope inconsistency as above.
  4. `backend/app/core/errors.py` defines `NotFoundError`, `ForbiddenError`, `ConflictError`, but no `ValidationError` domain class. Any route that needs to raise a manual 422 for a custom validation rule (e.g., risk_level membership check) has to fall back to raw `HTTPException(422)`, breaking the envelope contract.
  5. In `context-engine/tests/`, the files `test_acceptance_weights.py` and `test_association_mining.py` correctly use `pytest.importorskip("mlxtend", reason="mlxtend optional dependency not installed")` at module top. But `test_recommender.py` — which imports `recommender.py` that in turn calls `mine_association_rules` → `_encode_transactions` → `TransactionEncoder()` — has no such importorskip. When mlxtend is absent, running `pytest tests/test_recommender.py` crashes during collection/first-call with `NotImplementedError` (better than RuntimeError thanks to Round 1 mining.py guard, but still a test failure rather than a clean skip).

## Functional Requirements
### FR-1: verify_wip.py runs without psycopg
- **FR-1.1**: `verify_wip.py` sets `os.environ.setdefault("DATABASE_URL", "sqlite:///./_verify_wip.db")` **before** any `from app.` import statement. The chosen SQLite path must not collide with `test_health.py`'s `_test_backend.db` to avoid shared state.

### FR-2: Add ValidationError domain class (422)
- **FR-2.1**: `backend/app/core/errors.py` exports a `ValidationError(ContextIQError)` class with `status_code = 422` and `default_message = "Validation failed."` matching the RequestValidationError handler's wording.
- **FR-2.2**: The existing `RequestValidationError` handler remains unchanged — Pydantic's auto-validation still produces `{..., "details": exc.errors()}`. The new `ValidationError` class is for hand-written validation only.

### FR-3: predictions.py uses domain errors
- **FR-3.1**: `get_task_prediction` raises `NotFoundError("Prediction not found for task.")` instead of raw `HTTPException(404)`.
- **FR-3.2**: `list_predictions` risk_level membership check raises `ValidationError(f"Invalid risk_level: '{effective_risk}'. Allowed values: LOW, MEDIUM, HIGH.")` instead of raw `HTTPException(422)`.
- **FR-3.3**: Both error shapes hit the `handle_contextiq_error` handler and return `{"error": {"type": "NotFoundError"|"ValidationError", "message": "..."}}` with matching status codes 404 and 422.

### FR-4: recommendations.py uses domain errors
- **FR-4.1**: `post_recommendation_feedback` raises `NotFoundError("Recommendation not found.")` instead of raw `HTTPException(404)`.

### FR-5: test_recommender.py skips cleanly without mlxtend
- **FR-5.1**: `context-engine/tests/test_recommender.py` adds `pytest.importorskip("mlxtend", reason="mlxtend optional dependency not installed")` as the first executable line after imports (or equivalent `pytestmark = pytest.mark.skipif(not _MLXTEND_AVAILABLE, ...)` module-level guard using the same flag pattern as the other two files).

## Non-Functional Requirements
- **NFR-1 (No API contract breakage for non-error paths)**: 2xx response shapes are untouched. 4xx shapes for routes previously returning `{"detail": "..."}` now return the `{"error": {...}}` envelope — this is the **explicit** purpose of the change; it is a bugfix for an inconsistency, not a gratuitous break.
- **NFR-2 (verify_wip.py assertions preserved)**: Every existing assertion in `verify_wip.py` continues to pass after the DATABASE_URL override is added. The change only affects the import-phase engine creation, not runtime logic.
- **NFR-3 (Zero new runtime dependencies)**: No change to any `requirements.txt` or `package.json`. All changes are internal reorg or config/env defaults.
- **NFR-4 (Idempotent)**: Re-running `verify_wip.py` or any affected pytest file twice in a row produces the same result (no leftover SQLite lock or file that breaks the second run).

## Constraints
- **Technical**: `errors.py` already uses the `|` dict-merge operator (`|`) in the `RequestValidationError` handler; this project targets Python 3.10+ so that syntax is fine.
- **Technical**: The `NotFoundError` and `ValidationError` messages in routes should stay semantically identical to the previous `detail=` strings so existing tests and clients that substring-match on message text continue to work.
- **Technical**: `verify_wip.py` places the `DATABASE_URL` setdefault **after** `os.environ.setdefault("APP_ENV", "development")` and **before** `sys.path.insert(...)` and the first `from app.main import app` — ordering is critical because `from app.core.config import get_settings` runs at the top of `app/db/session.py` and caches.
- **Dependencies**: SQLite backend for SQLAlchemy must work with the `create_engine` options currently hardcoded in `session.py` (`pool_pre_ping`, `pool_size`, `max_overflow`). SQLAlchemy 2.x silently ignores pool options for SQLite, so this is acceptable.

## Assumptions
- `verify_wip.py` is meant to be runnable as a "smoke test" on any dev machine; requiring a live PostgreSQL instance just to verify UUID validation and env gating defeats that purpose. SQLite is sufficient for tests that only mock the DB session anyway and never actually query through the engine.
- Frontend code (and any hypothetical third-party client) should prefer the envelope shape `{"error": {"type": X, "message": Y}}` over `{"detail": Z}` because it carries a machine-readable `type` field. The old `detail` shape from `HTTPException` was an accidental inconsistency, not a documented contract.

## Open Questions
- None. All scope items are directly observable from code review with unambiguous fixes.

## Acceptance Criteria

### AC-1: verify_wip.py imports without ModuleNotFoundError (no psycopg required)
- **Type**: `rule`
- **Given**: A Python environment where `import psycopg` raises `ModuleNotFoundError` (i.e., psycopg package absent or SQLAlchemy's postgresql dialect cannot load it), and all other backend `requirements.txt` packages are installed
- **When**: `cd backend ; python verify_wip.py` is invoked
- **Then**: The script progresses past the import phase (no `ModuleNotFoundError: No module named 'psycopg'` traceback) and prints the `=== TR-2 Predictions Route ===` section (or runs to completion with its results summary)
- **Pass Condition**: Zero occurrences of "ModuleNotFoundError: No module named 'psycopg'" in stdout/stderr AND script exits with either 0 or 1 based on its own check() assertions (not an import crash)
- **Evidence**: Terminal capture of `python verify_wip.py` run beginning up to the first section header

### AC-2: predictions 404 returns NotFoundError envelope
- **Type**: `rule`
- **Given**: Backend TestClient with a valid dev auth override and a DB mock returning `None` for `.scalar()` on the prediction select
- **When**: `GET /api/v1/predictions/forgetting/task/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` is called
- **Then**: Status code is 404, response JSON has key `"error"` which is an object with keys `"type": "NotFoundError"` and `"message": "Prediction not found for task."`
- **Pass Condition**: `response.status_code == 404 AND response.json()["error"]["type"] == "NotFoundError" AND "Prediction not found" in response.json()["error"]["message"]`
- **Evidence**: TestClient test case assertion or REPL capture

### AC-3: predictions risk_level=INVALID returns ValidationError envelope (422)
- **Type**: `rule`
- **Given**: Backend TestClient with valid dev auth and DB mock
- **When**: `GET /api/v1/predictions/forgetting?risk_level=NOT_A_LEVEL` is called
- **Then**: Status code 422, response JSON `"error"."type"` == `"ValidationError"`, message contains `"Invalid risk_level"`
- **Pass Condition**: Status 422 and type = "ValidationError" and message matches
- **Evidence**: TestClient assertion

### AC-4: recommendations feedback 404 returns NotFoundError envelope
- **Type**: `rule`
- **Given**: Backend TestClient with valid dev auth and DB mock returning `None` on recommendation select
- **When**: `POST /api/v1/recommendations/<valid-uuid>/feedback` with a valid `RecommendationFeedbackCreate` body
- **Then**: Status 404, `response.json()["error"]["type"] == "NotFoundError"` and message is "Recommendation not found."
- **Pass Condition**: Status 404, envelope shape as described
- **Evidence**: TestClient assertion

### AC-5: ValidationError class exists and maps to 422
- **Type**: `rule`
- **Given**: Direct import from `app.core.errors`
- **When**: Instantiate `ValidationError("custom msg")` → call `register_exception_handlers`'s `handle_contextiq_error` with it → get JSONResponse
- **Then**: Class attribute `.status_code == 422`, `.default_message == "Validation failed."`, and the resulting JSON body has `error.type = "ValidationError"`
- **Pass Condition**: Direct Python object check + handler response shape check
- **Evidence**: Python REPL or unit test

### AC-6: test_recommender.py skips gracefully without mlxtend
- **Type**: `rule`
- **Given**: A context-engine Python environment where `import mlxtend` raises ImportError (simulated by setting `sys.modules['mlxtend'] = None` before import or running in a venv without it)
- **When**: `cd context-engine ; python -m pytest tests/test_recommender.py -q --tb=short` is invoked
- **Then**: pytest exits 0 or with skipped tests; output contains at least one `SKIPPED` line with reason containing "mlxtend optional dependency not installed"; no `ERROR` collecting the file and no `NotImplementedError` traceback
- **Pass Condition**: pytest.exit_code in {0, 5 (all skipped)} AND "SKIPPED" in output AND zero "NotImplementedError" occurrences
- **Evidence**: pytest output capture

### AC-7: Overall API error envelope uniformity
- **Type**: `rubric`
- **Dimension**: Consistency of 4xx error envelope shapes across the 8 route modules
- **Scale**: 0-2
  - `0` = 2+ routes still return `{"detail": "..."}` from raw `HTTPException` for 404/422 cases
  - `1` = exactly 1 route still uses raw `HTTPException` for a 4xx, or there's a new ValidationError class but it's unused
  - `2` = all 404s in the 8 route modules use `NotFoundError` (service-layer raise), all manual 422s use the new `ValidationError`, and no route module imports or raises raw `HTTPException` for status codes that already have a domain class
- **Pass Threshold**: >= 2
- **Evidence**: Grep of `backend/app/api/v1/` for `HTTPException(status_code=` with comparison against domain error usage per file
