# ContextIQ Tiered Improvements (Phase 1) - Implementation Plan

## Task 1: Build Backend Orchestrator Service with forget-risk prediction pipeline
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Create `backend/app/services/orchestrator.py` exposing an async `Orchestrator` class with:
    - `compute_forget_risk_for_task(task_id: UUID, user_id: UUID, db: Session)` — reads the task row, builds task features compatible with `forgetting-ml/app/schemas.py:TaskFeatures`, POSTs to `{FORGETTING_ML_URL}/api/v1/predictions/forgetting`, then inserts a new Prediction row (invalidating any prior prediction for the same task_id by setting its `valid_until=now`). Uses `httpx.AsyncClient` with config timeout. Logs warnings on HTTP errors but never raises.
    - `on_task_created(task_id, user_id, db)` — schedules forget-risk compute.
    - `on_task_updated(task_id, user_id, db)` — recomputes when status changes.
    - `on_task_event(event_id, task_id, user_id, db)` — placeholder that triggers a recompute only for terminal events (COMPLETED / FORGOTTEN / CANCELLED).
  - Add or confirm a backend write path for Predictions (a service function `prediction_service.create_prediction()` or inline ORM create). Keep append-only semantics; on insert expire any prior prediction for the same `task_id + FORGET_RISK` type.
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `rule` TR-1.1: `from app.services.orchestrator import Orchestrator` imports without error. A unit test patches `httpx.AsyncClient.post` to return a fixed prediction response and asserts exactly one `Prediction` row is created with `valid_from` set, confidence in [0,1], and `prediction_type=FORGET_RISK`. If a prior prediction existed for the same task, the prior row has non-null `valid_until` after the call.
  - `rule` TR-1.2: When the ML service POST raises a network error (patched with an httpx exception), the orchestrator call returns normally (no exception raised) and a `logging.warning` is emitted containing the substring "orchestrator" and "forget".
- **Notes**: The predictions endpoint `GET /predictions/forgetting/task/{task_id}` already exists in [predictions.py](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/backend/app/api/v1/predictions.py#L63-L91). httpx is already in backend requirements.

## Task 2: Wire orchestrator hooks into task creation flow with BackgroundTasks
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - Modify `backend/app/api/v1/tasks.py` `create_task` to accept `background_tasks: BackgroundTasks` from FastAPI. After calling `task_service.create_task`, schedule `orchestrator.compute_forget_risk_for_task(task.id, user_id, db)` using a wrapper function that injects a fresh DB session (do not reuse the request-scoped `db` session, because `background_tasks` run after the response is sent and the session may be closed).
  - Modify `task_service.update_task` — if status is changed to a terminal state (COMPLETED/FORGOTTEN/CANCELLED), schedule an orchestrator recompute via `background_tasks` (the `update_task` API endpoint will need the same BackgroundTasks parameter injection).
  - Modify `task_event_service.create_task_event` — if the event_type is terminal (COMPLETED/FORGOTTEN/CANCELLED), schedule orchestrator recompute.
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `rule` TR-2.1: Calling `POST /tasks` (via TestClient) with auth header returns 201 **before** the background task completes (verify by patching orchestrator with an `await asyncio.sleep(5)` and confirming response arrives under 1 second). The created task row exists in the DB synchronously.
  - `rule` TR-2.2: Patching the task router's background task scheduler and calling create_task verifies `background_tasks.add_task` was called exactly once with the forget-risk function and the new task id.
- **Notes**: For fresh DB sessions in background tasks, import `get_db`'s underlying `SessionLocal` factory or use `with Session(engine)` from db.session. Do not pass the request-scoped Depends `db` into a background task closure.

## Task 3: Add analytics endpoints for context-switch timeline and task/context heatmap
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - In `data-engine/app/api/analytics.py`, add two new endpoints:
    1. `GET /analytics/context-switch-timeline` — params `user_id`, `period_days`. Returns `ContextSwitchTimelineResponse` with `timeline: list[{timestamp: ISO string, task_id: str, task_title: str, location_id: str|null, location_label: str|null, context_tag: str|null, event_type: str, is_interruption: bool}]`. Build the series by concatenating task_events sorted by occurred_at, joining with interruptions table on overlapping time to mark interruption events, and joining location labels.
    2. `GET /analytics/task-context-heatmap` — params `user_id`, `period_days`, `value_metric={"completion_rate"|"forget_rate" default="completion_rate"}`. Returns `TaskContextHeatmapResponse` with `rows: list[str]` (task context_tag/category values), `columns: list[str]` (hour buckets "00".."23" or 4-hour buckets "00-03" etc.), and `cells: list[list[float|null]]` — cell[r][c] is the metric for row r in column c, or null if sample size < 3. Also return `sample_sizes: list[list[int]]` so the frontend can show "n=5" tooltips.
  - In `backend/app/api/v1/analytics.py` (create this proxy router if it does not exist; or add to the existing analytics module), add corresponding proxied endpoints that call the data-engine URLs internally and return the normalized response. This forward-positions the API-gateway pattern without implementing the full refactor yet.
  - In `frontend/lib/api/services/analytics.ts`, add typed methods:
    - `getContextSwitchTimeline(userId, periodDays): Promise<ApiResult<TimelineEntry[]>>`
    - `getTaskContextHeatmap(userId, periodDays, metric?): Promise<ApiResult<HeatmapData>>`
  - Define the matching TypeScript interfaces in analytics.ts (TimelineEntry, HeatmapData).
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `rule` TR-3.1: `GET /analytics/context-switch-timeline` with a seeded test user having ≥ 3 task events returns a timeline array with ≥ 3 entries sorted ascending by timestamp; `is_interruption` is a boolean on every entry.
  - `rule` TR-3.2: `GET /analytics/task-context-heatmap` returns `rows.length × columns.length === cells.flat().length` (rectangular grid shape). Every non-null cell value is in [0, 1] for rate metrics. `sample_sizes` has the same shape as `cells`.
- **Notes**: Confirm the existing backend `analytics.py` router. If it currently hits data-engine directly via internal httpx, match the existing proxy pattern. If it mirrors data-engine code locally, prefer adding the proxied call through backend so the frontend only needs `baseUrl: "analytics"` (already configured in client.ts BASE_URLS).

## Task 4: Implement Context-switch timeline and Task/Context heatmap in enhanced-dashboard
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - In `EnhancedDashboard` component at [enhanced-dashboard.tsx](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/frontend/components/dashboard/enhanced-dashboard.tsx#L89-L90):
    - Add two more `useState` + `loadAnalytics` Promise.all fetches for timeline and heatmap.
    - Replace `<UnavailableVisual title="Context-switch timeline" .../>` with a `ContextSwitchTimelineCard` component. Render a Recharts AreaChart (or ComposedChart) with x = `timestamp`, y = a nominal task id (or 0/1 presence — any encoding that visualizes switches across time). Color areas by `location_label`. Render vertical `ReferenceLine` for each `is_interruption=true` entry, with a tooltip.
    - Replace `<UnavailableVisual title="Task / context heatmap" .../>` with a `TaskContextHeatmapCard` component. Render a CSS-grid or Recharts-based heatmap. Each cell shows the numeric rate as a percentage label; background color intensity follows the rate. Hover tooltip shows `sample_size=n`.
    - Both cards render a small "Insufficient data" inline state (not the full `EmptyState` component) when rows/cells < 3 total valid.
  - Add the new components as inner functions inside enhanced-dashboard.tsx (pattern matches `FrictionSourcesCard`, `ForgettingRiskCard`, etc.).
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-6
- **Test Requirements**:
  - `rule` TR-4.1: Rendering the dashboard with mock timeline data (≥3 entries, ≥1 interruption) produces a card with title "Context-switch timeline" containing exactly one `<svg>` (the Recharts chart). The interruption vertical marker(s) are rendered as `<line>` or `<rect>` elements with an interruption-related class or aria-label.
  - `rule` TR-4.2: Rendering the dashboard with heatmap rows=["A","B","C"], columns=["00-03","04-07"], and valid cells=[[0.1,0.5],[0.9,null],[0.3,0.7]] produces 6 grid cell elements (null rendered as empty cell with "-"); non-null cells have a `style.background` whose channel varies (visually: 0.9 cell should be darker than 0.1 cell when sampled via getComputedStyle).
  - `rubric` TR-4.3 (AC-6 rubric): Chart component completeness. Dimension = label/tooltip/empty-state quality. Scale 1–5; anchors 1=no labels/no tooltip, 3=axis labels but no cell tooltips or empty state, 5=x-axis and y-axis labels visible on both charts, cell hover shows tooltip with value + sample size on heatmap, interruption marker tooltip shows "Interruption at [time]", empty state card shows "Insufficient data for this view — you need ≥ 3 events."; threshold >= 4. Evidence: manual screenshot review + component source code review for `<Tooltip>` wrapper presence and `<Label>`/axis props on Recharts components.
- **Notes**: Import Recharts components already used in the codebase (e.g., check focus-interruption-chart.tsx for the AreaChart/Tooltip/ReferenceLine imports pattern to keep consistency).

## Task 5: Create recommendation_feedback ORM model + Alembic migration
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Create `backend/app/models/recommendation_feedback.py`:
    - Add enum `RecommendationFeedbackAction(str, Enum): ACCEPTED = "ACCEPTED"; DISMISSED = "DISMISSED"; DEFERRED = "DEFERRED"` to `enums.py` if not present, OR inline in the model with Postgres native enum.
    - Model columns: `id` (UUID PK), `recommendation_id` (UUID FK → recommendations.id, CASCADE), `user_id` (UUID FK → users.id, CASCADE), `action` (enum, indexed), `suggested_task_id` (UUID FK → tasks.id, SET NULL, nullable), `feedback_note` (Text, nullable), `created_at` (datetime, default=utcnow).
    - Register the model in `backend/app/models/__init__.py`.
  - Generate an Alembic migration `backend/alembic/versions/XXX_add_recommendation_feedback_table.py` that creates the enum type, the table, and indices on `(recommendation_id)`, `(user_id)`, `(action)`.
  - Create a matching schema `RecommendationFeedbackCreate` / `RecommendationFeedbackRead` in `schemas/` or in the new router module.
- **Acceptance Criteria Addressed**: AC-4 (database schema part)
- **Test Requirements**:
  - `rule` TR-5.1: Applying the Alembic migration against a fresh Postgres DB results in the `recommendation_feedback` table existing with all four FK columns, an `action` enum column, and the three specified DB indices.
  - `rule` TR-5.2: Instantiating `RecommendationFeedback(user_id=..., recommendation_id=..., action="ACCEPTED")` via ORM `db.add + commit` succeeds; selecting it back reads the same values. FK to a non-existent recommendation_id correctly raises an IntegrityError.
- **Notes**: Apply the same `UUIDPKMixin`, `utcnow`, `Base` pattern as `prediction.py` and `recommendation.py`.

## Task 6: Implement recommendation feedback endpoint with auto-task-creation
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 5
- **Description**:
  - Add to backend `api/v1/router.py` (or confirm it is already there) a new router module `recommendations.py` at `backend/app/api/v1/recommendations.py`:
    - `POST /recommendations/{recommendation_id}/feedback` — request body `{action: RecommendationFeedbackAction, prefill_context_tag?: string, prefill_location_id?: UUID}`.
    - Handler validates the recommendation belongs to the current user via `get_current_user_id`, then:
      1. Creates a `RecommendationFeedback` row.
      2. If `action == ACCEPTED`: reads the parent recommendation title/message, calls `task_service.create_task` with a synthesized `TaskCreate` payload (title from rec.title or the suggested task string, description from rec.message, context_tag = prefill_context_tag or rec.message context, priority MEDIUM, due_at = now + 24h default). Stores the new task's UUID into `suggested_task_id` on the feedback row.
      3. Updates the parent `recommendations.status` to ACCEPTED/DISMISSED/EXPIRED (map DEFERRED → keep PENDING or set to DISMISSED per roadmap), sets `responded_at=now`, on ACCEPTED also sets `shown_at` if null.
    - Returns a 201 with the created feedback row plus the synthesized task_id (if any).
  - Also add a simple `GET /recommendations` listing endpoint (proxied through backend to context-engine or returned from the backend recommendations table) so the frontend `recommendationApi.list()` can use `baseUrl: "core"` instead of hitting context-engine:8003 directly — partial API-gateway alignment.
  - Update the frontend `lib/api/services/recommendation.ts` `liveRecommendationApi` methods to call the NEW backend endpoints (not context-engine directly):
    - `accept(id)` → `POST /recommendations/{id}/feedback {action:"ACCEPTED"}` (not `/recommendations/{id}/accept`)
    - `dismiss(id)` → `POST /recommendations/{id}/feedback {action:"DISMISSED"}`
    - `list()` → `GET /recommendations` with `baseUrl: "core"`
- **Acceptance Criteria Addressed**: AC-4 (full endpoint behavior)
- **Test Requirements**:
  - `rule` TR-6.1: POST `/recommendations/{id}/feedback` with `{action:"ACCEPTED"}` against a seed recommendation creates exactly 1 feedback row with `action=ACCEPTED`, exactly 1 new task row, and the feedback's `suggested_task_id` equals the new task UUID. The recommendation row has `status=ACCEPTED` and `responded_at` is non-null.
  - `rule` TR-6.2: Same call with `{action:"DISMISSED"}` creates 1 feedback row, 0 new task rows (suggested_task_id IS NULL), recommendation status = DISMISSED.
- **Notes**: The existing recommendations-panel.tsx already calls `recommendationApi.accept` and `feedbackApi.submitRecommendationOutcome` separately; we can leave feedbackApi as a wrapper or unify it, but the backend truth must be the single `/feedback` call.

## Task 7: Association mining acceptance-rate weighting in context-engine
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 6 (feedback data model exists)
- **Description**:
  - In `context-engine/ml/associations/mining.py`, modify the rule-scoring pipeline to accept an optional `acceptance_weights: dict[tuple[str, str], float]` parameter mapping `(antecedent_itemset_frozenset, consequent_itemset_frozenset)` → a multiplier in [1, 5].
  - When computing the final `confidence` for an association rule, multiply the raw computed confidence by `min(acceptance_weights.get((ant, cons), 1.0), 5.0)` (cap at 5× to avoid runaway). Also add a `weighted_confidence` field in the rule output dict, storing the post-multiplied value alongside the original `confidence`.
  - In `context-engine/ml/associations/recommender.py`, use `weighted_confidence` (falling back to raw `confidence`) for ranking / `prioritize_recommendations`.
  - Add a helper `acceptance_rate_from_feedback(feedback_rows: list[dict]) -> weights` in mining.py that, given flat feedback rows of `{antecedent: [items], consequent: [items], action: ACCEPTED|DISMISSED|DEFERRED}`, computes per-rule `acceptance_rate = accepted / (accepted + dismissed)`, then maps to a multiplier `weight = 1.0 + 4.0 * acceptance_rate` (so 0% = 1×, 100% = 5×).
  - In context-engine `state.py` / `store`, add an in-memory `acceptance_weights` dict and a method `store.record_feedback(antecedent, consequent, action)` that accumulates counts and recomputes weights.
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `rule` TR-7.1 (AC-5): Unit test `test_weighted_confidence_increases_with_feedback` — creates a fixed transaction set, runs mining with zero feedback (baseline confidence C0 for the target rule), runs mining with the same transactions plus injected feedback of 3 ACCEPTED + 0 DISMISSED for exactly the target rule's (ant, cons) pair, asserts `weighted_confidence_with_feedback > C0`.
  - `rule` TR-7.2: The cap at 5× is honored: mining with a synthetic 10× weight manually injected still yields `weighted_confidence <= 5.0 * raw_confidence`.
- **Notes**: Context-engine is standalone (not connected to Postgres feedback table in Phase 1). For this phase, accept feedback counts via an in-memory API — add `POST /api/v1/recommendations/feedback-sync` to context-engine's router that accepts `[{antecedent, consequent, action}]` and calls `store.record_feedback`. The backend orchestrator is not required to call this in Phase 1; the test-only path is sufficient evidence.

## Task 8: Frontend recommendation acceptance-count hint and feedback API wiring
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 6, Task 7
- **Description**:
  - Extend the backend `GET /recommendations` list endpoint response to embed an aggregated `acceptance_stats: {accepted: int, dismissed: int, deferred: int}` field per recommendation row (grouped by the rule's semantic key — recommendation title + triggering pattern, since feedback rows are per-recommendation-instance).
  - In `frontend/lib/api/services/recommendation.ts`, plumb the `acceptance_stats` field through `normalizeRecommendation` into the `Recommendation` type (add field to types).
  - In `RecommendationCard` component at [recommendation-card.tsx](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/frontend/components/recommendations/recommendation-card.tsx), render a small badge under the evidence line: e.g., "Accepted 3/3 times" when total > 0. Color green when acceptance_rate ≥ 0.8, grey otherwise.
  - Verify the full frontend flow: create a recommendation via context-engine or seed data → "Accept" button triggers `POST /feedback` → refetch → new task appears in the tasks list, recommendation status becomes ACCEPTED, acceptance badge updates on next list refresh.
- **Acceptance Criteria Addressed**: AC-4 (UI wiring part), FR-3.5
- **Test Requirements**:
  - `rule` TR-8.1: A recommendation with acceptance_stats={accepted:3, dismissed:0, deferred:0} rendered via `RecommendationCard` includes the text "Accepted 3/3" in its DOM. A recommendation with all-zero stats does not render the badge.
  - `rubric` TR-8.2: End-to-end workflow cohesion. Dimension = click Accept on a card → side effects are immediately visible. Scale 1–5; anchors 1=nothing visible happens, 3=task created but old recommendation still shows as PENDING until manual refresh, 5=after clicking Accept the card animates/badges to status ACCEPTED and a toast banner appears confirming the new task title within 500ms (background optimistic update). Evidence: component-level test with mocked API responses.
- **Notes**: Total count denominator for the N/M display should be `accepted + dismissed` (ignore deferred) per typical conversion-rate conventions.
