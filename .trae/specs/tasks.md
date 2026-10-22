# ContextIQ - Consistency, Reliability & Test-Portability Improvements (Round 2) - Implementation Plan

## Task 1: Fix verify_wip.py import crash — add DATABASE_URL SQLite override before app imports
- **Status**: `completed`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - In `backend/verify_wip.py`, insert a new line between line 6 (`os.environ.setdefault("APP_ENV", ...)`) and line 7 (`sys.path.insert(...)`) that reads:
    ```python
    os.environ.setdefault("DATABASE_URL", "sqlite:///./_verify_wip.db")
    ```
  - This must come **before** the first `from app.main import app` (line 10) because `app/db/session.py` calls `get_settings()` at import time (line 16) and then `create_engine(settings.DATABASE_URL)` on line 18.
  - Use the path `_verify_wip.db` (distinct from test_health.py's `_test_backend.db`) so the two scripts never share SQLite state on disk.
  - Do not change any other line in verify_wip.py; all check()/TestClient assertions remain identical.
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `rule` TR-1.1: Run `cd backend ; python verify_wip.py` in an environment without psycopg installed (simulate by temporarily renaming the psycopg folder if present, or confirm by inspecting the script path: the new setdefault line is present before any `from app.* import`). Confirm the script progresses past import and prints "=== TR-2 Predictions Route ==="; no `ModuleNotFoundError: No module named 'psycopg'` occurs.
  - `rule` TR-1.2: After the script completes once, re-run it; confirm exit code matches the first run and no `sqlite3.OperationalError: database is locked` appears (idempotency).
- **Notes**: If SQLite files are created by a test run, they are git-ignored sidecars like `_test_backend.db` already is.
- **Completion Evidence**:
  - TR-1.1 PASS: `verify_wip.py` runs to completion with exit code 0 and prints `=== TR-2 Predictions Route ===`; zero occurrences of `ModuleNotFoundError: No module named 'psycopg'` (verified 2026-03-29 via sandbox run)
  - TR-1.2 PASS: Re-run of `verify_wip.py` produced identical `RESULT: 10/10 PASSED, 0 FAILED` with exit code 0; no "database is locked" message appeared (verified 2026-03-29 idempotency run)
  - Source evidence: new line 7 in `verify_wip.py` = `os.environ.setdefault("DATABASE_URL", "sqlite:///./_verify_wip.db")` positioned before first `from app.main import app` on line 10

## Task 2: Add ValidationError domain class (422) to errors.py
- **Status**: `completed`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - In `backend/app/core/errors.py`, after the `ConflictError` class (line 40) and before the `_error_body` helper (line 42), insert a new class:
    ```python
    class ValidationError(ContextIQError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        default_message = "Validation failed."
    ```
  - Do not modify existing `handle_validation_error` (which wraps `RequestValidationError`). The `ValidationError` class is automatically handled by the existing `handle_contextiq_error` handler (first handler registered), which covers all `ContextIQError` subclasses, so no new exception-handler registration is required.
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `rule` TR-2.1: Direct import + instantiation: `from app.core.errors import ValidationError; e = ValidationError("custom"); assert e.status_code == 422; assert e.default_message == "Validation failed."; assert e.message == "custom"`
  - `rule` TR-2.2: Via a minimal FastAPI TestClient app that registers the handlers and a route that raises `ValidationError("bad")`, assert response.status_code == 422 and `body["error"]["type"] == "ValidationError"` and `body["error"]["message"] == "bad"`
- **Notes**: Keep alphabetical ordering of error classes (NotFound → Forbidden → Conflict → Validation); actual order in file doesn't matter to Python but keeping them grouped is clearer.
- **Completion Evidence**:
  - TR-2.1 PASS: In `backend/_self_check.py` section "AC-5", direct instantiation of `ValidationError("custom msg")` asserts `status_code == 422`, `default_message == "Validation failed."`, `message == "custom msg"` — all passed (exit 0, output: "AC-5: ValidationError attrs OK  -> AC-5 PASS")
  - TR-2.2 PASS: `backend/_self_check.py` "AC-3" calls `/api/v1/predictions/forgetting?risk_level=INVALID_LEVEL` (which raises ValidationError inside `list_predictions`); asserts status 422 and `body["error"]["type"] == "ValidationError"` and `body["error"]["message"]` contains "Invalid risk_level" — all passed (output: "AC-3 PASS (ValidationError envelope)")
  - AC-5 PASS: ValidationError correctly routes through `handle_contextiq_error` handler — confirmed because envelope is `{"error": {...}}` shape, NOT raw `{"detail": ...}` Starlette shape
  - Source evidence: errors.py lines 42-44

## Task 3: Use NotFoundError + ValidationError in predictions.py (remove raw HTTPException for 404/422)
- **Status**: `completed`
- **Priority**: high
- **Depends On**: Task 2 (ValidationError must exist to import it)
- **Description**:
  - In `backend/app/api/v1/predictions.py`:
    1. At the imports section (top of file), **remove** `from fastapi import ... HTTPException ...` IF it's only used for the 404/422 cases; check: current imports include `HTTPException` from line 4, `Query` from line 4, `Depends` from line 4. Leave `APIRouter`, `Depends`, `Query` in place.
    2. Add a new import: `from app.core.errors import NotFoundError, ValidationError` after existing imports.
    3. In `list_predictions` around lines 60-63, replace the block that reads:
       ```python
       raise HTTPException(
           status_code=422,
           detail=f"Invalid risk_level: '{effective_risk}'. Allowed values: LOW, MEDIUM, HIGH.",
       )
       ```
       with:
       ```python
       raise ValidationError(f"Invalid risk_level: '{effective_risk}'. Allowed values: LOW, MEDIUM, HIGH.")
       ```
    4. In `get_task_prediction` around lines 107-111, replace:
       ```python
       if not p:
           raise HTTPException(
               status_code=404,
               detail="Prediction not found for task.",
           )
       ```
       with:
       ```python
       if not p:
           raise NotFoundError("Prediction not found for task.")
       ```
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `rule` TR-3.1 (covers AC-2): Via verify_wip.py TR-2.2 (missing UUID → 404 scenario), after fix confirm the response body `r2.json()` has `r2.json()["error"]["type"] == "NotFoundError"` in addition to status 404.
  - `rule` TR-3.2 (covers AC-3): Via verify_wip.py TR-2.3 (`risk_level=INVALID → 422`), confirm the response body has `r3.json()["error"]["type"] == "ValidationError"` in addition to status 422.
  - `rubric` TR-3.3: Dimension = "import cleanliness"; Scale 0-2; Anchors: `0` = raw `HTTPException` still imported AND used in the file, `1` = HTTPException imported but unused (lint warning), `2` = HTTPException removed from imports (no longer needed), replaced with domain errors; Threshold >= 2; Evidence = source of predictions.py import block after edits.
- **Completion Evidence**:
  - TR-3.1 (AC-2) PASS: `_self_check.py` "AC-2" block calls `/predictions/forgetting/task/<missing-uuid>` with MockSession returning None; asserts status=404, `body["error"]["type"] == "NotFoundError"`, message contains "Prediction not found for task." — output: "AC-2 PASS (NotFoundError envelope)"
  - TR-3.2 (AC-3) PASS: `_self_check.py` "AC-3" block calls `/predictions/forgetting?risk_level=INVALID_LEVEL`; asserts status=422, `body["error"]["type"] == "ValidationError"` — output: "AC-3 PASS (ValidationError envelope)"
  - TR-3.3 (Rubric) SCORE: **2/2** (threshold >=2 achieved)
    - Evidence 1: `grep HTTPException backend/app/api/v1/predictions.py` returned 0 matches
    - Evidence 2: predictions.py import block now reads `from fastapi import APIRouter, Depends, Query` (HTTPException fully removed from imports, not lingering as unused lint warning)
    - Evidence 3: domain classes used throughout — `raise ValidationError(...)` at line 61, `raise NotFoundError(...)` at line 107
  - verify_wip.py alignment: TR-2.2, TR-2.3, TR-2.5, TR-2.4 all reported OK in final 10/10 run

## Task 4: Use NotFoundError in recommendations.py (remove raw HTTPException for 404)
- **Status**: `completed`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  - In `backend/app/api/v1/recommendations.py`:
    1. At the top of the file, check current imports. Line 6 imports `HTTPException, status` from FastAPI. `status` is still used on line 88 (`status_code=status.HTTP_201_CREATED`), so only remove `HTTPException` from the import if no other usage remains.
    2. Add import: `from app.core.errors import NotFoundError`
    3. In `post_recommendation_feedback` around lines 101-105, replace:
       ```python
       if recommendation is None:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail="Recommendation not found.",
           )
       ```
       with:
       ```python
       if recommendation is None:
           raise NotFoundError("Recommendation not found.")
       ```
    4. If `HTTPException` is now unused in the import line, remove it (leaving `APIRouter, Depends, status` as needed).
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `rule` TR-4.1 (covers AC-4): Build a TestClient call with dev auth overrides, a MockSession that returns None on recommendation select, and POST to `/recommendations/<uuid>/feedback` with a valid `{action: "ACCEPTED"}` body; assert status 404 and `body["error"]["type"] == "NotFoundError"` and message matches.
  - `rule` TR-4.2: Confirm recommendations.py code inspection check in verify_wip.py section TR-4.4 continues to pass (logger exists, safe_location_id, ownership_select are untouched).
- **Completion Evidence**:
  - TR-4.1 (AC-4) PASS: `_self_check.py` "AC-4" block calls `POST /recommendations/<uuid>/feedback` with MockSession returning None; asserts status=404, `body["error"]["type"] == "NotFoundError"`, `message == "Recommendation not found."` — output: "AC-4 PASS (recommendations NotFoundError envelope)"
  - TR-4.2 PASS: verify_wip.py final run reports: `[OK] TR-4.4 recommendations: logger=True, safe_var=True, ownership_select=True, debug_log_str=True` — all structural checks unchanged; no refactor regressions
  - Import cleanliness: `grep HTTPException backend/app/api/v1/recommendations.py` returned 0 matches (HTTPException fully removed from imports; `status` retained because it is used elsewhere in the file)
  - Supplementary improvement (AC-7 rubric): `users.py` register endpoint also upgraded from raw `HTTPException(404)` to `NotFoundError("Not found")` — see users.py lines 8 and 31

## Task 5: Add mlxtend importorskip to context-engine tests/test_recommender.py
- **Status**: `completed`
- **Priority**: medium
- **Depends On**: None
- **Description**:
  - Read the top of `context-engine/tests/test_association_mining.py` to confirm the exact importorskip pattern used in the other test files (pattern should be: `pytest.importorskip("mlxtend", reason="mlxtend optional dependency not installed")`).
  - Edit `context-engine/tests/test_recommender.py` and place the same `pytest.importorskip(...)` call as the **first module-level executable statement** following the imports block (i.e., after `import pytest` / `from ... import ...` lines but before any `def test_...` functions or any `pytestmark = ...` lines). This causes pytest to skip the ENTIRE module (not individual functions) when mlxtend is missing, matching the behavior of test_association_mining.py and test_acceptance_weights.py.
  - Do not modify any test function bodies or fixture definitions.
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `rule` TR-5.1: In a fresh Python process, simulate missing mlxtend by setting `sys.modules['mlxtend'] = None` before importing, or run in a venv without it; execute `pytest tests/test_recommender.py -q`; confirm output contains "SKIPPED" lines with reason including "mlxtend optional dependency not installed" and exits with code 0 (or 5, "no tests ran"); zero occurrences of "NotImplementedError" and zero "ERROR" collection failures.
  - `rule` TR-5.2: Pattern consistency: the importorskip line in test_recommender.py byte-for-byte matches the lines used in test_association_mining.py and test_acceptance_weights.py (same reason string).
- **Completion Evidence**:
  - TR-5.1 PASS: `cd context-engine ; python -m pytest tests/test_recommender.py -v --no-header` output = `collected 0 items / 1 skipped` + `1 skipped in 0.05s`, exit code 5 (pytest: "no tests collected"). Zero occurrences of "NotImplementedError"; zero "ERROR" lines; zero "FAILED" lines. (The 1 skip is the module-level importorskip preventing collection — identical behaviour to the other two test files.)
  - TR-5.2 PASS: Byte-for-byte comparison of the guard lines across all three files:
    - `test_association_mining.py`: `pytest.importorskip("mlxtend", reason="mlxtend optional dependency not installed")`
    - `test_acceptance_weights.py`: same string
    - `test_recommender.py` (NEW line 3): same string — `diff`-level identical.
  - AC-6 PASS: test_recommender.py no longer crashes on collection in environments where the optional mlxtend extra is absent

---

# Rubric AC-7: API Error-Envelope Uniformity
- **Dimension**: Count of route modules under `app/api/v1/*` that still import or raise raw `HTTPException(status_code=...)` for status codes **that already have a matching ContextIQ domain class** (404=NotFoundError, 403=ForbiddenError, 409=ConflictError, 422=ValidationError, 401=Unauthorized handled centrally). HTTPException for 502 (Bad Gateway, no domain class) or passthrough of `response.status_code` (external service proxy) is excluded from the count.
- **Scale 0-2**: `0` = 3+ modules still have raw domain-code raises; `1` = exactly 1 targeted module has a residual (incomplete cleanup); `2` = all route modules use domain classes where applicable (analytics.py passthrough 502s are allowed)
- **Result SCORE: 2/2** (Threshold >= 2 achieved)
  - Evidence: `grep -n "HTTPException(status_code=" backend/app/api/v1/` returns 4 matches, ALL in `analytics.py`:
    - analytics.py line 57: `raise HTTPException(status_code=response.status_code, ...)` — 4xx/5xx passthrough from external data-engine service (no domain class applicable)
    - analytics.py line 60: `raise HTTPException(status_code=502, ...)` — Bad Gateway, no ContextIQ domain class for 502, correct raw usage
    - analytics.py line 80: same as line 57 (second route)
    - analytics.py line 83: same as line 60 (second route)
  - Zero matches in: `predictions.py`, `recommendations.py`, `users.py`, `tasks.py`, `router.py`
  - `predictions.py`: ValidationError/NotFoundError ✓
  - `recommendations.py`: NotFoundError ✓
  - `users.py` (register 404): upgraded from HTTPException(404) → NotFoundError ✓
