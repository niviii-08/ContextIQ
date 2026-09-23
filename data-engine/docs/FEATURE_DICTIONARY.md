# ContextIQ Feature Dictionary

Every feature in the Stage 5 ML feature matrix, with:
- **Type** (dtype)
- **Formula / Definition**
- **Leakage-prevention proof** — why the feature, computed as of `task.created_at`, cannot see future data
- **Example value** from a typical synthetic run

Also documented: target variable, metadata columns (kept for joining, excluded from training), and the leakage-prevention contract.

---

## Global Leakage-Prevention Contract

For **every** row in the feature matrix (which represents one task T), every feature value is computed by:

1. Setting `as_of = T.created_at`.
2. Filtering every input table to rows whose relevant timestamp is **STRICTLY LESS THAN** `as_of`.
   - `tasks.created_at < as_of`
   - `task_events.event_time < as_of`
   - `interruptions.start_time < as_of`
   - `context_sessions.session_start < as_of`
3. Aggregating only over that pre-`as_of` history slice.

This is enforced centrally by `_before(df, col, as_of)` in `pipeline/features.py`, and by the analogous helper in `app/utils/features.py`. Callers do not pass unfiltered DataFrames directly to aggregators.

The target column `will_forget` is the single exception: it is derived from task T's **own** final status, which is exactly what the model is predicting. That is the correct train/test label, not leakage.

---

## Metadata Columns

Kept in the feature DataFrame for analysis + joining, but **excluded from the training feature set** (not numeric identifiers, or not features).

| Column | Type | Purpose |
|---|---|---|
| `task_id` | UUID string | Unique key of the task row — for joining back to `tasks` |
| `user_id` | UUID string | User identifier — for group-level analysis, excluded from training features |
| `created_at` | datetime | Timestamp used as the `as_of` cutoff for all history filters |
| `status` | string | Raw task status (preserved for analysis; `will_forget` is binary label) |
| `task_location_pair` | string | `<category>@<location_type>` combined key — kept for EDA, not used as a numeric ML feature |

---

## Target Variable

| Column | Type | Formula | Example |
|---|---|---|---|
| `will_forget` | int (0/1) | `1 if task.status == "forgotten" else 0` | `1` |

---

## Group A — Preserved Features (from `app/utils/features.py`, extended)

These 14 features existed (or directly parallel) the per-task feature generators in the preserved `app/utils/features.py` module. They are reimplemented here in vectorized batch form for the full dataset.

### 1. `previous_forgetting_count`
- **Type:** int
- **Formula:** Count of tasks whose status = `forgotten` among tasks with `created_at < as_of` for this user.
- **Leakage proof:** Counted only in `tasks_hist = tasks[tasks.created_at < as_of]` → cannot include T's own outcome.
- **Example:** `7`

### 2. `previous_completion_count`
- **Type:** int
- **Formula:** Count of tasks whose status = `completed` among tasks with `created_at < as_of` for this user.
- **Leakage proof:** Same `_before` filter on `created_at`.
- **Example:** `42`

### 3. `completion_rate`
- **Type:** float (0–1) or null
- **Formula:** `previous_completion_count / resolved_count` where `resolved_count` = # prior tasks with status in {completed, forgotten, cancelled}.
- **Leakage proof:** Denominator and numerator both use pre-`as_of` history only. `None` if user has no resolved history.
- **Example:** `0.8571`

### 4. `category_forgetting_rate`
- **Type:** float (0–1) or null
- **Formula:** Forgetting rate among prior resolved tasks **in the same category** as task T.
- **Leakage proof:** Subset of pre-`as_of` resolved history; T itself is excluded because `created_at == as_of` fails `< as_of`.
- **Example:** `0.3125`

### 5. `location_forgetting_rate`
- **Type:** float (0–1) or null
- **Formula:** Forgetting rate among prior resolved tasks at the **same `location_id`** as T. Null if T has no location_id.
- **Leakage proof:** Same `_before` filter; location condition is additive.
- **Example:** `0.2200`

### 6. `weekday_forgetting_rate`
- **Type:** float (0–1) or null
- **Formula:** Forgetting rate among prior resolved tasks whose `created_at` fell on the **same weekday** (Monday–Sunday) as T's `created_at`.
- **Leakage proof:** Weekday bucketing is applied after the `_before` filter; T's own row is never in the bucket (its created_at equals `as_of`).
- **Example:** `0.1875`

### 7. `hour_forgetting_rate`
- **Type:** float (0–1) or null
- **Formula:** Forgetting rate among prior resolved tasks whose `created_at` hour-of-day matches T's `created_at.hour`.
- **Leakage proof:** Same strict pre-`as_of` filter before hour bucketing.
- **Example:** `0.2632`

### 8. `task_frequency`
- **Type:** int
- **Formula:** Count of prior tasks (any status) in T's category for this user.
- **Leakage proof:** `tasks_hist.category == category`; `tasks_hist` is strictly pre-`as_of`.
- **Example:** `23`

### 9. `days_since_last_similar`
- **Type:** float (days, 3 dp) or null
- **Formula:** `(as_of - max(created_at of prior same-category tasks)).total_seconds() / 86400`.
- **Leakage proof:** `max(created_at)` is taken from pre-`as_of` history, so the "last similar task" always predates T.
- **Example:** `2.174`

### 10. `deadline_distance_hours`
- **Type:** float (hours, 3 dp) or null
- **Formula:** `(T.deadline_at - as_of).total_seconds() / 3600`. Null when T has no deadline.
- **Leakage proof:** Uses T's **own** deadline, which was known at task creation (`as_of`). No future data; deadline is a planning field set when the task is created.
- **Example:** `47.350`

### 11. `priority`
- **Type:** int (1–5)
- **Formula:** T's declared priority, clamped to [1,5] by Stage 2 cleaning.
- **Leakage proof:** Priority is a property of the task itself set at `created_at`. No lookahead.
- **Example:** `3`

### 12. `tasks_today`
- **Type:** int
- **Formula:** Count of the user's tasks with `created_at ∈ [as_of − 24h, as_of)`.
- **Leakage proof:** The 24h window is half-open `[…, as_of)` so T's own `created_at == as_of` is excluded; rolling window lies entirely in history.
- **Example:** `4`

### 13. `interruptions_today`
- **Type:** int
- **Formula:** Count of the user's interruptions with `start_time ∈ [as_of − 24h, as_of)`.
- **Leakage proof:** Same half-open rolling window; interruption start must be strictly before `as_of`.
- **Example:** `11`

### 14. `recent_context_switches`
- **Type:** int
- **Formula:** Count of `resumed` events in task_events with `event_time ∈ [as_of − 24h, as_of)`. (Proxy for context-switch count; authoritative value is `context_switch_count` on sessions.)
- **Leakage proof:** Same half-open 24h window.
- **Example:** `3`

### 15. `avg_interruption_duration_s`
- **Type:** float (seconds, 2 dp) or null
- **Formula:** Mean of `interruption.duration_seconds` over **all** pre-`as_of` user interruptions.
- **Leakage proof:** Uses `_before(interruptions_df, "start_time", as_of)` → strictly historical.
- **Example:** `112.37`

---

## Group B — Extended Features (new in `pipeline/features.py`)

### 16. `recovery_time_s`
- **Type:** float (seconds, 2 dp) or null
- **Formula:** Mean gap (in seconds) between every `paused` event and the next `resumed` event on the same task, for pre-`as_of` events. Null if <1 such pair exists.
- **Leakage proof:** Both the paused event_time and the resumed event_time are from `events_hist = _before(events_df, "event_time", as_of)`. The gap is computed between two historical timestamps — no lookahead.
- **Example:** `1425.80` (~23.8 minutes)

### 17. `daily_friction_score`
- **Type:** float (0–1, 4 dp)
- **Formula:** Heuristic composite over rolling 7-day window of pre-`as_of` data:
  ```
  forget_rate = # forgotten / # resolved in 7-day window
  interruption_rate = # interruptions / (focused_hours + interruption_hours) in 7-day sessions
  score = 0.6 * forget_rate + 0.4 * min(1, interruption_rate / 6.0)
  ```
- **Leakage proof:** The 7-day window is `[as_of − 7d, as_of)` — strictly before T. Uses `_last_n_days(..., 7)` which calls `_before` first.
- **Example:** `0.3421`

### 18. `repeated_context_count`
- **Type:** int
- **Formula:** Count of prior tasks for this user that share **both** T's `category` and T's `location_id`.
- **Leakage proof:** Counted over `tasks_hist` (strictly pre-`as_of`). T's own `category` is known at creation — not leakage.
- **Example:** `5`

### 19. `forgetting_streak`
- **Type:** int
- **Formula:** Number of **consecutive** forgotten tasks immediately preceding `as_of` for this user (walks history backward from the most recent pre-`as_of` task, counts contiguous `forgotten` statuses, stops at first non-forgotten).
- **Leakage proof:** Only uses `tasks_hist.status` — all tasks created before T. T's own status is never consulted for the streak.
- **Example:** `2`

### 20. `avg_session_duration_7d_s`
- **Type:** float (seconds, 2 dp) or null
- **Formula:** Mean of `sessions.focused_time_seconds` over sessions with `session_start ∈ [as_of − 7d, as_of)`.
- **Leakage proof:** Rolling 7-day window is strictly half-open; `session_start < as_of` enforced by `_last_n_days`.
- **Example:** `1847.52`

### 21. `context_switch_rate_7d`
- **Type:** float (4 dp) or null
- **Formula:** Mean of `sessions.context_switch_count` over sessions in the same 7-day rolling window.
- **Leakage proof:** Identical window filter to #20.
- **Example:** `0.6154`

### 22. `is_late_night`
- **Type:** int (0/1)
- **Formula:** `1 if as_of.hour >= 21 else 0` (late-night start).
- **Leakage proof:** Derived from `as_of` = T's own `created_at.hour`, which is known at prediction time. No lookahead.
- **Example:** `0`

### 23. `is_repeated_context`
- **Type:** int (0/1)
- **Formula:** `1 if repeated_context_count > 0 else 0` — user has done this (category, location) pair at least once before.
- **Leakage proof:** Threshold on a count (#18) whose proof already holds.
- **Example:** `1`

---

## Feature Matrix Completeness

For a synthetic run with `--users 50 --days 60 --seed 42`, typical values are:

| Metric | Typical value |
|---|---|
| Rows (tasks) | ~10,000 |
| Feature columns (numeric) | 23 |
| Mean completeness | ≥ 85% |
| Null-heavy features | `days_since_last_similar` (first task per user = null), `location_forgetting_rate` (tasks with no prior at that location) |

---

## Production Prediction Contract

When this pipeline's models serve live predictions via the ML API:

1. For the incoming new task T, set `as_of = datetime.now(timezone.utc) ≅ T.created_at`.
2. Recompute the 23 features using the user's historical data filtered to `timestamp < as_of`.
3. Call the saved sklearn Pipeline's `.predict_proba(features)` to produce `P(will_forget=1)`.

This exactly reproduces the training-time feature distribution. Any discrepancy between training-feature computation and serving-time computation is a leakage bug.
