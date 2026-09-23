# Feature Engine

**Source:** `app/utils/features.py`

This module generates ML-ready features for consumption by an
independently-built downstream module (a forgetting-prediction model,
association-rule mining, recommendation engine, etc.). It performs no I/O
itself — callers load DataFrames via `app/analytics/metrics.py`'s
`load_*_df` helpers and pass them in.

## Why this exists as a separate layer

Analytics endpoints answer "what happened, in aggregate, over the last N
days" — good for dashboards, bad for training data, because dashboard
aggregates don't carry the **per-row, point-in-time** structure a
supervised model needs. The feature engine instead answers, for a single
task/user/context **as of a specific moment**, "what was knowable at that
moment" — which is exactly what a training example or a live prediction
request needs.

## CRITICAL: temporal leakage prevention

Every function takes an explicit `as_of` timestamp (the "prediction
time") and **only uses rows whose relevant timestamp is strictly before
`as_of`**:

- Task rows are filtered on `created_at < as_of`
- Event rows are filtered on `event_time < as_of`
- Interruption rows are filtered on `start_time < as_of`

This is enforced by the internal `_before()` / `_align_tz()` helpers,
used consistently across every public function. The strict `<` (not
`<=`) means a task's own `created_at` is excluded from its own feature
computation — **a task can never see its own outcome.**

### Practical guarantee for training pipelines

To build a training dataset without leakage, call:

```python
generate_task_features(task_row=row, ..., as_of=row["created_at"])
```

for every historical task. Because `as_of` equals the task's own creation
time, the function naturally reproduces exactly the information horizon a
live, production prediction request would have at that same moment — no
special-casing needed.

### Cross-database timestamp handling

SQLite (used for local development) does not round-trip
timezone-aware datetimes — SQLAlchemy reads them back as naive, even if
they were written as aware. PostgreSQL preserves tz-awareness correctly.
Rather than assuming one behavior, every comparison in this module
dynamically aligns `as_of`'s tz-awareness to match whatever the loaded
DataFrame column actually has, so the same code is correct on both
backends without special configuration.

## Interfaces

### `generate_task_features(*, task_row, tasks_df, events_df, interruptions_df, as_of) -> dict`

Per-task features, typically computed with `as_of = task.created_at`.

| Feature | Meaning |
|---|---|
| `previous_forgetting_count` | # of this user's prior resolved tasks that were forgotten |
| `previous_completion_count` | # of this user's prior resolved tasks that were completed |
| `completion_rate` | prior completion rate across all categories |
| `category_forgetting_rate` | prior forgetting rate within this task's category |
| `location_forgetting_rate` | prior forgetting rate at this task's location (null if no location) |
| `weekday_forgetting_rate` | prior forgetting rate on this weekday |
| `hour_forgetting_rate` | prior forgetting rate at this hour-of-day |
| `task_frequency` | # of prior tasks in this category |
| `days_since_last_similar_task` | days since the last task in this category (null if none) |
| `deadline_distance_hours` | hours between `as_of` and the task's deadline (null if no deadline) |
| `priority` | the task's own priority (1–5), passed through |
| `tasks_today` | # of tasks created by this user in the preceding 24h |
| `interruptions_today` | # of interruptions in the preceding 24h |
| `recent_context_switches` | # of `resumed` events in the preceding 24h (event-log proxy) |
| `average_interruption_duration_seconds` | mean interruption duration prior to `as_of` |

### `generate_user_features(*, tasks_df, interruptions_df, sessions_df, as_of) -> dict`

Aggregate, user-level features as of a point in time.

| Feature | Meaning |
|---|---|
| `completion_rate` / `forgetting_rate` | across all resolved tasks prior to `as_of` |
| `total_tasks` / `total_interruptions` | counts prior to `as_of` |
| `average_session_duration_seconds` | mean `focused_time_seconds` across sessions prior to `as_of` |
| `average_interruption_duration_seconds` | mean interruption duration prior to `as_of` |
| `total_context_switches` | sum of `context_switch_count` across sessions prior to `as_of` |

### `generate_context_features(*, location_id, tasks_df, interruptions_df, as_of) -> dict`

Features scoped to one location/context.

| Feature | Meaning |
|---|---|
| `location_task_count` | # of tasks at this location prior to `as_of` |
| `location_forgetting_rate` | forgetting rate among resolved tasks at this location |
| `location_interruption_count` | # of interruptions at this location prior to `as_of` |
| `location_average_interruption_duration_seconds` | mean interruption duration at this location |

## Testing

`tests/test_features.py` includes explicit leakage-regression tests:
verifying a task created after `as_of` is excluded from history, and that
a task can never see its own outcome (`as_of == task.created_at` case).
