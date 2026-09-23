# Data Architecture

## Design principles

1. **Event-sourced at the core.** `task_events` is an append-only,
   immutable log — the single source of truth for "what happened, when."
   Everything else (task status, sessions, metrics) is derived from it.
2. **Denormalize for read speed, not as a source of truth.** `tasks.status`
   and the lifecycle timestamp columns on `tasks` exist purely so simple
   reads don't need to replay the event log. They are kept in sync by the
   ingestion API (`POST /task-events`), but if they ever drift, `task_events`
   wins.
3. **Cross-database by construction.** Every model works unmodified against
   SQLite (local dev, zero config) and PostgreSQL/Supabase (production). This
   is achieved via a custom `GUID` type (`app/database/base.py`) that stores
   native `UUID` on Postgres and `CHAR(36)` on SQLite.
4. **ML-ready from day one.** Every event carries `user_id`, a timestamp,
   and enough foreign keys (task, location) that a downstream feature/ML
   pipeline never needs a second ingestion path.

## Entity-relationship overview

```
users 1───* locations
users 1───* tasks
users 1───* task_events
users 1───* interruptions
users 1───* context_sessions
users 1───* behaviour_metrics

locations 1───* tasks           (a task's "home" context, optional)
locations 1───* task_events      (context at time of event, optional)
locations 1───* interruptions    (context at time of interruption, optional)
locations 1───* context_sessions (context of a reconstructed session, optional)

tasks 1───* task_events
tasks 1───* interruptions        (an interruption can be tied to a task, optional)
tasks 1───* context_sessions
```

## Table reference

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| email | varchar(255) | unique, indexed |
| display_name | varchar(255) | nullable |
| timezone | varchar(64) | default `UTC` |
| created_at / updated_at | timestamptz | |

### `locations`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → users, cascade delete) | |
| label | varchar(120) | e.g. "Home Office"; doubles as a generic "context" label, doesn't require real GPS |
| latitude / longitude | float | nullable |
| created_at | timestamptz | |

Indexed on `(user_id, label)`.

### `tasks`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → users, cascade delete) | |
| location_id | UUID (FK → locations, set null on delete) | nullable |
| title | varchar(255) | |
| category | varchar(80) | free-form, indexed; default `general` |
| priority | int | 1–5, **CHECK constraint enforced** |
| status | enum (string-backed) | created / started / paused / resumed / completed / forgotten / cancelled |
| deadline_at | timestamptz | nullable |
| created_at, started_at, completed_at, forgotten_at, cancelled_at | timestamptz | denormalized lifecycle markers |
| updated_at | timestamptz | auto-updated |

Indexed on `(user_id, status)`, `(user_id, category)`, `(user_id, created_at)`.

### `task_events`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → users, cascade delete) | |
| task_id | UUID (FK → tasks, cascade delete) | |
| location_id | UUID (FK → locations, set null on delete) | nullable |
| event_type | enum | created / started / paused / resumed / completed / forgotten / cancelled |
| event_time | timestamptz | **not** `created_at` — this is when the behaviour happened, which may be backfilled |
| event_metadata | JSON | free-form, e.g. `{"source": "mobile_widget"}` |
| created_at | timestamptz | row insertion time (audit only) |

Indexed on `(user_id, event_time)` and `(task_id, event_time)` — the two
access patterns the Context Session Engine and analytics queries need.

### `interruptions`
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → users, cascade delete) | |
| task_id | UUID (FK → tasks, set null on delete) | **nullable** — an interruption can happen with no active task |
| location_id | UUID (FK → locations, set null on delete) | nullable |
| interruption_type | enum | phone / social_media / message / call / search / person / food / other |
| source_label | varchar(120) | nullable, free-form (e.g. app name) |
| start_time | timestamptz | |
| end_time | timestamptz | nullable |
| duration_seconds | int | nullable; derived from start/end at ingestion time if omitted |
| created_at | timestamptz | |

Indexed on `(user_id, start_time)` and `(task_id)`.

### `context_sessions` (derived table)
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → users, cascade delete) | |
| task_id | UUID (FK → tasks, set null on delete) | nullable |
| location_id | UUID (FK → locations, set null on delete) | nullable |
| session_start / session_end | timestamptz | |
| focused_time_seconds | int | |
| interruption_time_seconds | int | |
| resume_delay_seconds | float | nullable — only set for sessions opened by a `resumed` event |
| context_switch_count | int | |
| interruption_count | int | |
| created_at | timestamptz | |

Indexed on `(user_id, session_start)` and `(task_id)`. See
`docs/BEHAVIOUR_ANALYTICS.md` for the full reconstruction algorithm.

### `behaviour_metrics` (optional materialized rollups)
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → users, cascade delete) | |
| metric_name | varchar(80) | e.g. `"forgetting_rate"` |
| dimension | varchar(120) | e.g. `"weekday:Monday"`, `"category:deep_work"`, `"overall"` |
| period_start / period_end | timestamptz | |
| value | float | |
| extra | JSON | nullable, additional structured detail |
| computed_at | timestamptz | |

Unique constraint on `(user_id, metric_name, dimension, period_start)`.
This table exists so expensive rollups can be pre-computed once and
reused by downstream modules instead of recomputing from raw tables on
every request — the analytics API currently computes on the fly and does
not yet write to this table, but the schema is ready for that
optimization.

## Indexing strategy

Every table is indexed on `user_id` in combination with the columns most
commonly filtered/sorted on (status, category, timestamp), because nearly
every query in this system is scoped to a single user. No cross-user
aggregate queries are part of the current API surface, so no global
secondary indexes beyond `users.email` (unique) were added.

## Why UUIDs

UUIDs (rather than auto-increment integers) were chosen so that:
- IDs can be generated client-side or by any future distributed ingestion
  path without a round-trip to the database.
- Downstream ML/analytics modules never need to worry about ID collisions
  when combining data from synthetic + real sources.
