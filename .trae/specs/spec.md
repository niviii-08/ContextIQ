# ContextIQ Tiered Improvements - Product Requirements Document (Phase 1)

## Overview
- **Summary**: Implement the first 3 highest-impact items from the ContextIQ Tiered Improvement Roadmap: (1) Backend Orchestration Layer with on-demand forget-risk predictions, (2) Two missing dashboard visualizations (Context-switch timeline & Task/Context Heatmap), (3) Recommendation acceptance feedback loop with auto-task-creation.
- **Purpose**: Transform the project from a static demo into a dynamically-feeling product where task creation triggers real ML processing, dashboard shows complete data visualization, and recommendations have actionable outcomes with feedback storage.
- **Target Users**: Portfolio reviewers, demonstration users, and hypothetical end-users of the ContextIQ personal behaviour intelligence system.

## Goals
- **Goal 1**: Creating a task automatically triggers an orchestration pipeline that calls downstream services and persists predictions to the Predictions table. The `predictions/{task_id}` endpoint returns data for newly-created tasks without requiring a manual batch ML pipeline run.
- **Goal 2**: Replace the two `UnavailableVisual` placeholder cards in enhanced-dashboard.tsx with real Recharts visualizations backed by new analytics endpoints (context-switch timeline series + task/context heatmap cells).
- **Goal 3**: Recommendation cards have an Accept button that (a) stores user feedback in a new `recommendation_feedback` table, (b) auto-creates a Task from the suggested task with pre-filled context/location, and (c) surfaces acceptance counts back to the association mining recommender as weighting signals.

## Non-Goals
- **Excluded**: JWT Authentication (Tier 3.8) — deferred to Phase 2.
- **Excluded**: WebSocket real-time dashboard refresh (Tier 1.2) — deferred to Phase 2.
- **Excluded**: Interactive Task→Prediction reveal animation (Tier 2.4) — deferred to Phase 2.
- **Excluded**: Live Session In Progress tracker (Tier 2.7), Notifications (Tier 3.9), Model Monitoring (Tier 3.10), Bulk Actions (Tier 3.11).
- **Excluded**: Daily Briefing, Export Reports, Dark Mode (Tier 4.12–14).
- **Excluded**: Architectural refactors (API Gateway, Retries/Circuit Breaking, Shared Models Package) — deferred to a dedicated architecture phase.

## Background & Context
- The backend `task_service.create_task()` writes to Postgres and adds a CREATED event, but no downstream processing occurs. The config already exposes `FORGETTING_ML_URL`, `DATA_ENGINE_URL`, `CONTEXT_ENGINE_URL`, `INTELLIGENCE_URL` at [config.py](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/backend/app/core/config.py#L97-L100).
- The forgetting-ml service already exposes `POST /api/v1/predictions/forgetting` (single) and `.../batch` at [forgetting-ml/app/api.py](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/forgetting-ml/app/api.py#L31-L56).
- enhanced-dashboard.tsx has explicit `UnavailableVisual` placeholders at line 89 for "Context-switch timeline" and "Task / context heatmap" at [enhanced-dashboard.tsx](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/frontend/components/dashboard/enhanced-dashboard.tsx#L89-L90).
- data-engine exposes `/analytics/derived-metrics` with `context_consistency.category_scores` at [data-engine/analytics.py](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/data-engine/app/api/analytics.py#L211), but no timeline or heatmap-specific endpoints yet.
- Recommendations already have `RecommendationStatus.ACCEPTED | DISMISSED` in the enum at [enums.py](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/backend/app/models/enums.py#L82-L87) but no feedback persistence or auto-create-task action. The context-engine association miner at [mining.py](file:///c:/Users/Neevetha%20N/Downloads/DATAPROJECT/contextiq-complete/context-engine/ml/associations/mining.py) can be extended with acceptance-rate weighting.

## Functional Requirements
### FR-1: Orchestration Service
- **FR-1.1**: New module `backend/app/services/orchestrator.py` with an `Orchestrator` class exposing async methods: `on_task_created(task_id, user_id)`, `on_task_updated(task_id, user_id)`, `on_task_event(event_id, task_id, user_id)`, and `compute_forget_risk_for_task(task_id, user_id)`.
- **FR-1.2**: `compute_forget_risk_for_task` uses `httpx.AsyncClient` to POST task features to the forgetting-ml prediction endpoint, then writes the result to the `predictions` table via a new Prediction model write path.
- **FR-1.3**: `task_service.create_task()` and `task_event_service.create_task_event()` and `task_service.update_task()` trigger orchestrator calls (background tasks so HTTP responses aren't blocked).
- **FR-1.4**: `tasks.py` router `POST /tasks` accepts FastAPI `BackgroundTasks` and schedules the forget-risk computation immediately after task creation.
- **FR-1.5**: `GET /predictions/{task_id}` endpoint returns the latest prediction row for a task if one exists.

### FR-2: Missing Dashboard Visualizations
- **FR-2.1**: New analytics endpoint in data-engine or proxied through backend: returns a context-switch time series with `[{timestamp, task_id, location, is_interruption}]` timeline entries.
- **FR-2.2**: New analytics endpoint returning heatmap cells: rows = task categories (context_tag or category), columns = hour-of-day buckets, value = completion_rate or forget_rate.
- **FR-2.3**: enhanced-dashboard.tsx replaces the two `UnavailableVisual` components with real Recharts charts. Context-switch timeline uses AreaChart with interruption markers. Task/Context heatmap uses a colored grid.
- **FR-2.4**: Frontend analytics service (`analytics.ts`) adds typed methods to fetch the new series and heatmap data.

### FR-3: Recommendation Feedback Loop
- **FR-3.1**: New `recommendation_feedback` ORM model with columns: `id`, `recommendation_id` (FK), `user_id` (FK), `action` (ACCEPTED|DISMISSED|DEFERRED enum), `created_at`, and a `suggested_task_id` nullable FK to the auto-created task when applicable.
- **FR-3.2**: Alembic migration adding the `recommendation_feedback` table and `recommendation_feedback_action` enum.
- **FR-3.3**: Backend endpoint `POST /api/v1/recommendations/{id}/feedback` accepting `{action, prefill_context?}`. On ACCEPTED: auto-create a Task using the recommendation's title/message/context and link it via `suggested_task_id`. Update the parent `recommendations.status` column.
- **FR-3.4**: context-engine `ml/associations/mining.py` exposes a way to boost rule confidence by acceptance rate (e.g., a `rule_weights` dict passed into mining that multiplies the confidence score by `weight` for rules matching accepted antecedent/consequent patterns).
- **FR-3.5**: Recommendation card UI shows an acceptance-count hint string (e.g., "Accepted 3/3 times" from feedback counts) when available.

## Non-Functional Requirements
- **NFR-1**: Orchestrator calls use the existing `ORCHESTRATOR_TIMEOUT_SECONDS` config value and catch HTTP errors; a failed downstream service call logs a warning but never breaks the user-facing task creation API call.
- **NFR-2**: Dashboard chart components handle empty/missing data gracefully with an inline "Insufficient data" message rather than throwing errors.
- **NFR-3**: All new backend endpoints are gated behind the existing `get_current_user_id` dependency to preserve user-level row isolation.
- **NFR-4**: Predictions are append-only (no UPDATE on existing Prediction rows per the model docstring). A new prediction invalidates the previous one via `valid_until` set on the prior row.
- **NFR-5**: Frontend TypeScript code compiles without new `tsc` errors. Python code passes import/syntax checks.

## Constraints
- **Technical**: Must use the existing FastAPI + SQLAlchemy backend stack. New async HTTP calls must use `httpx` (already available or add to requirements.txt if missing). Frontend charts must use `recharts` (already used in other charts).
- **Technical**: Orchestrator calls happen as `BackgroundTasks`, never blocking the HTTP response path.
- **Business**: The existing dev-mode `X-User-Id` header auth flow remains the default; JWT is explicitly out of scope for this phase.
- **Dependencies**: Depends on forgetting-ml service exposing the single-task prediction endpoint (already present at `/api/v1/predictions/forgetting`). Depends on the backend's existing `Prediction` model being writeable.

## Assumptions
- The user will run the backend with all 4 downstream services reachable at the URLs specified in `.env` (the default docker-compose.yml configuration).
- Recharts is already installed in the frontend project (confirmed via import of `AreaChart` in existing chart components like focus-interruption-chart.tsx).
- httpx is already installed or can be added to backend/requirements.txt without conflict.
- `tenacity` is not required for Phase 1; simple try/except logging is sufficient per NFR-1. Full retry/circuit-breaking is deferred to the architectural improvements phase.

## Acceptance Criteria

### AC-1: Task creation triggers forget-risk prediction
- **Type**: `rule`
- **Given**: A user creates a task via `POST /api/v1/tasks` with all downstream services running.
- **When**: Within 10 seconds the user calls `GET /api/v1/predictions/forgetting/task/{task_id}` (or the existing predictions endpoint by task).
- **Then**: The endpoint returns a non-empty Prediction record with `prediction_type=FORGET_RISK`, a numeric `confidence`, and a populated `predicted_value` dict including a forget risk probability.
- **Pass Condition**: Creating a task and polling predictions for it returns data within 15 seconds (accommodating background scheduling). Backend logs include an "orchestrator: forget-risk prediction stored" entry or equivalent on success, and a warning log (not exception) if the ML service is down.
- **Evidence**: `curl` /docs UI test: create task → read its prediction; OR a pytest integration test covering the path.

### AC-2: Dashboard has Context-switch timeline chart
- **Type**: `rule`
- **Given**: A user with ≥ 3 task events (containing location/context changes) in the analytics window.
- **When**: The dashboard loads and `loadAnalytics()` resolves.
- **Then**: The "Context-switch timeline" card renders a Recharts AreaChart (or equivalent) with a non-empty x-axis of timestamps, y-axis/task-location color encoding, and visual vertical markers at interruption events.
- **Pass Condition**: No `UnavailableVisual` component is rendered for this card; DOM contains a `<svg>` child of the card with ≥ 2 plotted data points and ≥ 1 interruption annotation.
- **Evidence**: Screenshot or React testing-library query for the chart SVG within the card, plus absence of "Not available yet" text.

### AC-3: Dashboard has Task/Context heatmap
- **Type**: `rule`
- **Given**: A user with ≥ 3 distinct task categories/context_tags and ≥ 2 different completion outcomes in the data window.
- **When**: The dashboard loads.
- **Then**: The "Task / context heatmap" card renders a grid of ≥ 3 rows × ≥ 3 columns with cell colors varying by the completion/forget rate value. Row and column labels are visible.
- **Pass Condition**: No `UnavailableVisual` for this card; grid cells are present with computed background colors.
- **Evidence**: Same as AC-2 — screenshot or DOM query.

### AC-4: Accepting a recommendation creates a task and stores feedback
- **Type**: `rule`
- **Given**: A pending recommendation exists via `GET /recommendations` with a suggested task title.
- **When**: The frontend calls `POST /api/v1/recommendations/{id}/feedback` with `action=ACCEPTED`.
- **Then**: (a) A new Task row exists with title matching the suggested task, context_tag prefilled from the recommendation. (b) A `recommendation_feedback` row exists with action=ACCEPTED and `suggested_task_id` pointing at the new task. (c) The parent recommendation row has `status=ACCEPTED` and `responded_at` set.
- **Pass Condition**: All three DB conditions are verifiable via SELECT or by calling the respective GET endpoints.
- **Evidence**: Test script or curl sequence: list rec → accept → list tasks → GET feedback.

### AC-5: Association mining uses acceptance-rate weights
- **Type**: `rule`
- **Given**: An association rule `{antecedent=home_morning, consequent=take_trash_out}` has been accepted 3/3 times in feedback.
- **When**: `mine_associations()` (or equivalent miner entry point) runs with the accumulated feedback counts.
- **Then**: The rule's output confidence (or priority score) is strictly higher than the same rule would have had with zero acceptance feedback for identical raw support counts.
- **Pass Condition**: Unit test in context-engine/tests comparing weighted vs unweighted confidence for a fixed synthetic transaction set with injected acceptance feedback.
- **Evidence**: pytest output of the comparison test with the assertion `weighted_conf > unweighted_conf`.

### AC-6: Dashboard data quality (rubric)
- **Type**: `rubric`
- **Dimension**: Visual completeness and information clarity of the two new charts
- **Scale**: 1–5
- **Anchors**: 1 = blank/unavailable cards still shown; 3 = charts render with data but missing labels/legends/axis titles and no empty-state handling; 5 = both charts have clear axis labels, value tooltips on hover, sensible color coding, a friendly "Insufficient data for this view" empty state when the dataset is too small, and interruption markers on the timeline chart have a tooltip explaining what the marker means.
- **Pass Threshold**: >= 4
- **Evidence**: Screenshot of both rendered charts with tooltip hover; code review of the React components showing label/tooltip/empty-state props.

## Open Questions
- [ ] Which exact predictions endpoint path should be used for "by task_id" lookup? The current router has `predictions.py`; confirm whether `GET /predictions/forgetting/task/{task_id}` already exists or needs to be added. (Will verify during Plan by reading predictions.py.)
- [ ] For the Task/Context heatmap, should rows be `context_tag` (present on Task model) or a separate `category` field? The current data-engine analytics endpoints include `context_consistency.category_scores`; we'll inspect its schema and use the closest available, defaulting to `context_tag` if category is absent.
- [ ] For recommendation feedback, should DEFERRED be a separate action or mapped to DISMISSED? The roadmap specifies ACCEPTED|DISMISSED|DEFERRED schema, so we will implement all three.
