# ContextIQ — Integration Blueprint

This document explains exactly how `contextiq-frontend` should connect to the
independently developed ContextIQ backend and ML services once they exist.
The frontend currently runs entirely on mock data (`NEXT_PUBLIC_USE_MOCK=true`)
and requires **zero code changes in components** to switch to a live
backend — only the service implementations in `lib/api/services/*.ts` need a
`false` mock flag and a reachable `NEXT_PUBLIC_API_BASE_URL`.

## 1. Architecture overview

```
components/*  →  lib/api/services/*Api  →  lib/api/client.ts (fetch wrapper)  →  Backend
                          ↑
                 mock/*.mock.ts (dev/demo only)
```

Every component talks only to a typed `*Api` object (`tasksApi`,
`analyticsApi`, `predictionApi`, `contextApi`, `recommendationApi`,
`insightsApi`, `feedbackApi`). Each service module exports **one interface**
and **two implementations** (mock + live), selected at module-load time by
`apiClient.USE_MOCK`. This is the seam the real backend plugs into.

The conceptual backend is expected to be composed of four logical services,
which MAY be deployed as a single gateway or as separate microservices:

| Logical service | Frontend service module | Responsibility |
|---|---|---|
| Data Analytics API | `analyticsApi` | Daily summaries, friction score |
| Forgetting ML API | `predictionApi` | Per-task forgetting risk + reasons |
| Context Intelligence API | `contextApi` | Focus/interruption metrics, associations |
| Behaviour Intelligence API | `insightsApi`, `recommendationApi` | Insights, "one more thing" suggestions |
| Core task service | `tasksApi`, `feedbackApi` | Task CRUD, task events, feedback |

All requests are made through `lib/api/client.ts`, which:
- Prefixes every path with `NEXT_PUBLIC_API_BASE_URL`
- Attaches `Authorization: Bearer <token>` from `localStorage` (`contextiq_token`) if present
- Normalizes every non-2xx response into the shared `ApiError` shape
- Applies a 10s timeout via `AbortController`

## 2. Standard response envelope

The frontend does **not** expect a `{ data, error }` envelope from the wire —
`ApiResult<T>` is a frontend-side type. On the wire:

- **Success**: HTTP 200/201 with the resource as the JSON body (matching the
  relevant TypeScript interface in `types/index.ts` exactly).
- **Error**: any non-2xx status with this JSON body:

```json
{
  "code": "TASK_NOT_FOUND",
  "message": "Task with id 'task-123' was not found.",
  "status": 404,
  "details": { "taskId": "task-123" }
}
```

`code` is a stable machine-readable string (SCREAMING_SNAKE_CASE), `message`
is safe to render directly to the user, `status` mirrors the HTTP status
code, and `details` is optional structured context.

## 3. Auth

Not yet implemented in the UI. The client already forwards a bearer token
from `localStorage.getItem("contextiq_token")` if present, so the minimal
integration path is: after login, `localStorage.setItem("contextiq_token", jwt)`.
A dedicated `authApi` module and login UI are out of scope for this
deliverable and should be added following the same service-interface pattern.

## 4. Endpoint contracts

Base path: `{NEXT_PUBLIC_API_BASE_URL}` (default `http://localhost:8000/api/v1`).

### 4.1 Core Task Service

#### `GET /tasks`
List tasks, optionally filtered.

- Query params: `status?: TaskStatus`, `context?: string`
- Response: `200 Task[]`
- Errors: `500 INTERNAL_ERROR`

#### `GET /tasks/{id}`
- Response: `200 Task`
- Errors: `404 TASK_NOT_FOUND`

#### `POST /tasks`
- Request body (`CreateTaskInput`):
```json
{
  "title": "Lab Record",
  "description": "Complete and submit the weekly physics lab record.",
  "category": "Academic",
  "context": "Department",
  "priority": "HIGH",
  "dueAt": "2026-08-19T15:00:00Z",
  "estimatedMinutes": 45,
  "tags": ["lab", "physics"]
}
```
- Response: `201 Task`
- Errors: `400 VALIDATION_ERROR`

#### `PATCH /tasks/{id}/status`
- Request body: `{ "status": "COMPLETED" }` (`TaskStatus`)
- Response: `200 Task`
- Errors: `404 TASK_NOT_FOUND`, `400 INVALID_STATUS_TRANSITION`

#### `POST /tasks/{id}/events`
Records a discrete task event (start/pause/resume/complete/forgotten/etc).
This is the primary signal stream consumed by the ML/analytics services.
- Request body: `{ "type": "STARTED" }` (`TaskEventType`)
- Response: `201 TaskEvent`
- Errors: `404 TASK_NOT_FOUND`

#### `GET /tasks/{id}/events`
- Response: `200 TaskEvent[]`

### 4.2 Data Analytics API

#### `GET /analytics/daily-summary`
Powers the "Today's Behaviour Overview" dashboard section.
- Query params: `date?: string` (ISO date, defaults to today, server timezone
  should be documented and ideally configurable per-user)
- Response: `200 DailySummary`
```json
{
  "date": "2026-08-18",
  "frictionScore": 64,
  "tasksCompleted": 5,
  "tasksForgotten": 2,
  "contextSwitches": 14,
  "interruptionMinutes": 87,
  "recoveryCostMinutes": 39,
  "comparedToYesterday": { "frictionScoreDelta": 6, "tasksCompletedDelta": -1 }
}
```
- Errors: `500 INTERNAL_ERROR`

### 4.3 Forgetting ML API

#### `GET /predictions/forgetting`
Powers the Forget Risk panel.
- Query params: `riskLevel?: "LOW" | "MEDIUM" | "HIGH"`
- Response: `200 ForgettingPrediction[]`
```json
{
  "id": "pred-001",
  "taskId": "task-001",
  "taskTitle": "Lab Record",
  "riskScore": 82,
  "riskLevel": "HIGH",
  "reasons": [
    {
      "label": "Previous forgetting frequency",
      "detail": "Forgotten 6 out of the last 10 weeks.",
      "weight": 0.45
    }
  ],
  "generatedAt": "2026-08-18T06:00:00Z",
  "modelVersion": "forgetting-model-v1.3.0"
}
```
- Errors: `503 MODEL_UNAVAILABLE` (model service temporarily down — frontend
  should render the standard error state with retry)

#### `GET /predictions/forgetting/task/{taskId}`
- Response: `200 ForgettingPrediction | null`

### 4.4 Context Intelligence API

#### `GET /context/metrics`
Powers the Context Intelligence page (charts + summary metrics).
- Query params: `date?: string`
- Response: `200 ContextMetrics`
```json
{
  "date": "2026-08-18",
  "focusMinutes": 214,
  "interruptionMinutes": 87,
  "contextSwitches": 14,
  "recoveryCostMinutes": 39,
  "topInterruptionCategory": "Notifications",
  "mostAffectedTaskCategory": "Academic",
  "byHour": [{ "hour": 9, "focusMinutes": 35, "interruptionMinutes": 10 }],
  "byCategory": [{ "category": "Notifications", "minutes": 34, "count": 21 }]
}
```

#### `GET /context/associations`
Powers the reliable/at-risk task groupings surfaced in Recommendations and
Behaviour Insights.
- Response: `200 Association[]`

### 4.5 Behaviour Intelligence API

#### `GET /insights`
- Response: `200 BehaviourInsight[]`
```json
{
  "id": "insight-001",
  "type": "FRICTION_SOURCE",
  "title": "Your biggest friction source",
  "description": "Notification interruptions between 12–1 PM cost you the most recovery time this week.",
  "priority": "HIGH",
  "metricLabel": "Avg. recovery cost",
  "metricValue": "6.2 min/interruption",
  "generatedAt": "2026-08-18T06:00:00Z"
}
```

#### `GET /recommendations`
Powers "One More Thing". Only `PENDING` recommendations should be returned.
- Response: `200 Recommendation[]`

#### `POST /recommendations/{id}/accept`
Called when the user clicks **Add**. The backend is responsible for creating
the corresponding task (or linking to an existing one) and should return the
updated recommendation with `status: "ADDED"`.
- Response: `200 Recommendation`

#### `POST /recommendations/{id}/dismiss`
- Response: `200 Recommendation` with `status: "DISMISSED"`

### 4.6 Feedback

#### `POST /feedback`
Generic feedback endpoint for predictions/recommendations/insights — used to
close the loop back into the ML/behaviour models.
- Request body (`SubmitFeedbackInput`):
```json
{
  "targetType": "PREDICTION",
  "targetId": "pred-001",
  "helpful": true,
  "comment": "Accurate — I did forget this."
}
```
- Response: `201 Feedback`

## 5. Error format (all endpoints)

```ts
interface ApiError {
  code: string;       // e.g. "TASK_NOT_FOUND", "VALIDATION_ERROR"
  message: string;     // human-readable, safe to render
  status: number;      // mirrors HTTP status
  details?: Record<string, unknown>;
}
```

Recommended standard codes: `VALIDATION_ERROR` (400), `UNAUTHORIZED` (401),
`FORBIDDEN` (403), `*_NOT_FOUND` (404), `MODEL_UNAVAILABLE` (503),
`INTERNAL_ERROR` (500).

## 6. Steps to switch from mock to live

1. Stand up the backend implementing the endpoints in section 4.
2. Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` to the backend's base URL.
3. Set `NEXT_PUBLIC_USE_MOCK=false`.
4. Optionally delete or ignore `/mock` (kept for local dev/demo/tests).
5. Run `npm run build` and `npm run test` — no component changes required
   because every component is already written against the `*Api` interfaces,
   not against `fetch` directly.
6. If the real backend is split across multiple base URLs instead of one
   gateway, extend `lib/api/client.ts` to route per-service (the
   `.env.example` file has commented-out per-service URL variables ready for
   this).

## 7. Non-functional expectations for the backend

- All list endpoints should be reasonably fast (<300ms p50) since they back
  synchronous dashboard loads with no client-side caching layer yet.
- ML endpoints (`/predictions/forgetting`) may be slower; the frontend
  already renders a loading skeleton and has a 10s client timeout — align
  backend SLAs with (or below) that timeout, or the frontend will surface a
  "Request timed out" error.
- CORS must allow the frontend's origin(s) for browser-based requests.
