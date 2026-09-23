# API Reference

Base URL: `http://localhost:8000`
Base path for all routes below: `/api/v1`
Interactive docs (auto-generated from the same schemas): `/docs`

All request/response bodies are JSON. All timestamps are ISO-8601; treat
them as UTC (see the note on SQLite tz-handling in the main README).

---

## Health

### `GET /health`
```json
{ "status": "ok" }
```

---

## Ingestion

### `POST /api/v1/users`
Create a user.

Request:
```json
{ "email": "alice@example.com", "display_name": "Alice", "timezone": "UTC" }
```
Response `201`:
```json
{
  "id": "5c9c...uuid",
  "email": "alice@example.com",
  "display_name": "Alice",
  "timezone": "UTC",
  "created_at": "2026-08-19T10:00:00Z"
}
```
`409` if the email already exists.

### `GET /api/v1/users/{user_id}`
Returns the same shape as above, or `404`.

### `POST /api/v1/locations`
```json
{ "user_id": "uuid", "label": "Home Office", "latitude": null, "longitude": null }
```
`201` → the created location. `404` if `user_id` doesn't exist.

### `POST /api/v1/tasks`
```json
{
  "user_id": "uuid",
  "title": "Write Q3 report",
  "category": "deep_work",
  "priority": 4,
  "location_id": "uuid",
  "deadline_at": "2026-08-25T17:00:00Z"
}
```
Response `201` — creates the task **and** an implicit `created` task_event
at the same timestamp:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "location_id": "uuid",
  "title": "Write Q3 report",
  "category": "deep_work",
  "priority": 4,
  "status": "created",
  "deadline_at": "2026-08-25T17:00:00Z",
  "created_at": "2026-08-19T10:00:00Z",
  "started_at": null,
  "completed_at": null,
  "forgotten_at": null,
  "cancelled_at": null,
  "updated_at": "2026-08-19T10:00:00Z"
}
```

### `GET /api/v1/tasks/{task_id}`
Same shape as above, or `404`.

### `POST /api/v1/task-events`
Record a lifecycle event. This also updates the denormalized fields on
the parent `tasks` row.
```json
{
  "user_id": "uuid",
  "task_id": "uuid",
  "event_type": "started",
  "event_time": "2026-08-19T10:05:00Z",
  "location_id": "uuid",
  "event_metadata": { "source": "mobile_widget" }
}
```
`event_type` ∈ `created | started | paused | resumed | completed | forgotten | cancelled`.
`201` → the created event. `404` if task not found. `400` if `task_id`
doesn't belong to `user_id`.

### `POST /api/v1/interruptions`
```json
{
  "user_id": "uuid",
  "task_id": "uuid",
  "location_id": "uuid",
  "interruption_type": "phone",
  "start_time": "2026-08-19T10:10:00Z",
  "end_time": "2026-08-19T10:11:30Z"
}
```
`duration_seconds` is derived automatically from `start_time`/`end_time`
if omitted. `interruption_type` ∈ `phone | social_media | message | call
| search | person | food | other`. `201` → the created interruption.

---

## Context Session Engine

### `POST /api/v1/context-sessions/rebuild?user_id={uuid}`
Recomputes all `context_sessions` rows for a user from raw
`task_events` + `interruptions`. Idempotent — safe to call repeatedly.
Call this after ingesting a batch of events, before reading
`/analytics/context` or `/analytics/friction`.

Response:
```json
{ "user_id": "uuid", "sessions_created": 42 }
```

---

## Analytics

All analytics endpoints take `user_id` (required) and `period_days`
(optional, default 30, max 3650) as query parameters, and return `404` if
`user_id` doesn't exist. Every endpoint gracefully returns zeros/empty
objects (not an error) for a user with no data in the period.

### `GET /analytics/overview`
```
GET /api/v1/analytics/overview?user_id=uuid&period_days=30
```
```json
{
  "user_id": "uuid",
  "period_days": 30,
  "task_completion_rate": 0.82,
  "task_forgetting_rate": 0.11,
  "average_task_duration_minutes": 34.2,
  "average_task_delay_minutes": -12.5,
  "tasks_per_day": 4.3,
  "tasks_per_category": { "deep_work": 40, "email": 25 },
  "tasks_per_location": { "Home Office": 50, "Cafe": 15 },
  "total_tasks": 130,
  "total_interruptions": 210,
  "total_context_switches": 34
}
```

### `GET /analytics/tasks`
```json
{
  "user_id": "uuid",
  "period_days": 30,
  "total_tasks": 130,
  "completion_rate": 0.82,
  "forgetting_rate": 0.11,
  "average_duration_minutes": 34.2,
  "average_delay_minutes": -12.5,
  "tasks_per_day": 4.3,
  "tasks_per_category": { "deep_work": 40 },
  "tasks_per_location": { "Home Office": 50 },
  "forgetting_by_weekday": { "Monday": 0.15, "Friday": 0.22 },
  "forgetting_by_hour": { "9": 0.05, "17": 0.3 },
  "forgetting_by_category": { "email": 0.4, "deep_work": 0.05 },
  "forgetting_by_location": { "Commute": 0.5 }
}
```

### `GET /analytics/interruptions`
```json
{
  "user_id": "uuid",
  "period_days": 30,
  "interruption_count": 210,
  "interruption_duration_minutes_total": 350.5,
  "interruption_duration_minutes_avg": 1.67,
  "interruption_by_weekday": { "Monday": 40 },
  "interruption_by_hour": { "14": 25 },
  "interruption_by_category": { "phone": 80, "message": 60 }
}
```

### `GET /analytics/context`
```json
{
  "user_id": "uuid",
  "period_days": 30,
  "total_sessions": 145,
  "average_focus_session_minutes": 22.4,
  "total_context_switches": 34,
  "resume_count": 28,
  "pause_count": 60,
  "average_resume_delay_seconds": 5400.0,
  "context_switching_by_task_category": { "deep_work": 20 },
  "context_switching_by_location": { "Cafe": 15 }
}
```

### `GET /analytics/friction`
```json
{
  "user_id": "uuid",
  "period_days": 30,
  "label": "Experimental behavioural metric — not scientifically validated.",
  "overall_score": 41.25,
  "forgetting_score": 38.5,
  "interruption_score": 55.0,
  "context_switch_score": 33.0,
  "recovery_score": 40.0,
  "formula_version": "1.0"
}
```

---

## Error format

All errors follow FastAPI's default shape:
```json
{ "detail": "User not found" }
```
with the appropriate HTTP status code (`404`, `409`, `400`, or `422` for
request-validation failures).
