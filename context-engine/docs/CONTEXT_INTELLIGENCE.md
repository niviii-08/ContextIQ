# Context Intelligence (System A)

Covers session reconstruction, aggregate metrics, behavioural pattern
discovery, and recovery cost estimation.

## 1. Event model

Raw events (`app/schemas/events.py::RawEvent`) share this shape:

| field                 | type      | notes                                             |
|-----------------------|-----------|----------------------------------------------------|
| `user_id`              | string    | stable user identifier                            |
| `timestamp`             | datetime  | UTC                                                |
| `task_id`               | string    | stable per task instance (see note below)         |
| `task_category`          | string    | e.g. `programming`, `admin`, `study`, `fitness`   |
| `context`                | string    | e.g. `department`, `library`, `home_office`       |
| `event_type`             | enum      | `START, PAUSE, RESUME, INTERRUPTION, COMPLETE, TASK_SWITCH` |
| `interruption_source`     | string?   | optional, only meaningful on `INTERRUPTION`       |

**Note on `task_id` stability**: for session reconstruction, a `task_id`
identifies one task instance across its lifecycle events (its `START`
through its `COMPLETE`). For association mining (System B), the same
`task_id` value recurring across many separate visits is what allows
support/confidence/lift to be computed meaningfully — i.e. `task_id`
should be the stable *type* of task (e.g. `"collect_form"`), not a
freshly-generated unique ID per occurrence.

## 2. Session reconstruction

`ml/context/session_reconstruction.py::reconstruct_sessions(events)`

Events are grouped by `(user_id, task_id)` and processed in timestamp
order. A session begins at `START` (or defensively at the first event
seen if no `START` was recorded) and ends at `COMPLETE`. Within a
session:

- `INTERRUPTION` closes out the current focused-time span and opens an
  "interruption window".
- The next `RESUME` (or `COMPLETE`) closes that window; its duration is
  added to `interruption_time_seconds` and recorded in both
  `interruption_durations_seconds` and `resume_delays_seconds` (in this
  model, the delay between an interruption starting and the user
  resuming *is* the interruption's duration).
- `PAUSE` without a preceding `INTERRUPTION` is treated as a voluntary
  break: it closes the current focused-time span but is **not** counted
  as interruption time.
- `TASK_SWITCH` increments `num_context_switches` and closes the current
  focused-time span, without ending the session.
- `COMPLETE` ends the session and finalizes all metrics.

Output: one `ReconstructedSession` per detected session (a single
user/task pair can yield multiple sessions if started/completed more
than once).

## 3. Aggregate metrics

`ml/context/metrics.py::compute_session_metrics(sessions, scope)`

| metric | formula |
|---|---|
| `average_interruption_duration_seconds` | mean of all `interruption_durations_seconds` across sessions |
| `average_resume_delay_seconds` | mean of all `resume_delays_seconds` across sessions |
| `switches_per_hour` | `total_context_switches / (total_focused_time_seconds / 3600)` |
| `interruptions_per_session` | `total_interruptions / num_sessions` |
| `average_session_duration_seconds` | `sum(session_duration_seconds) / num_sessions` |

All are plain descriptive statistics; none claim psychological validity.

## 4. Pattern discovery

`ml/context/pattern_discovery.py`

Three classical, non-deep-learning techniques, all operating on the same
hand-engineered feature space (`ml/features/feature_engineering.py`):

1. **Frequency analysis** (`discover_frequency_patterns`) — z-scores of
   each `(task_category, context)` group's interruption/switch rate
   against the population mean; groups scoring above `z_threshold` (default
   1.0 std dev) become patterns like *"User frequently switches tasks
   during programming"*. Groups with fewer than `min_sessions` (default 5)
   observations are skipped to avoid noisy single-sample conclusions.

2. **Resume-delay pattern** (`discover_resume_delay_pattern`) — flags
   sessions where interruptions classified as "short" (≤ `short_threshold_seconds`,
   default 30s) are nonetheless associated with a disproportionately long
   average resume delay for that session (≥ 2×), surfacing the
   *"short interruptions are followed by long resume delays"* pattern.

3. **Clustering** (`discover_clusters`) — KMeans (default `k=3`) over
   standardized session features (duration, focused time, interruption
   time, interruption count, switch count, avg resume delay). Each
   cluster is described by its centroid and given a heuristic label such
   as *"high-switch / low-focus sessions"*.

4. **Anomaly detection** (`discover_anomalies`) — IsolationForest (default
   `contamination=0.05`) over the same feature space flags individual
   sessions with unusual timing profiles.

`discover_all_patterns(sessions)` runs all four and returns a combined,
unranked list of `BehaviouralPattern` objects, each carrying its own
`confidence` (∈ [0, 1]) and a machine-readable `evidence` dict.

## 5. Recovery cost estimation

`ml/context/recovery_cost.py::estimate_recovery_costs(sessions)`

**This is a transparent, feature-based score — not a validated
psychological measurement of actual cognitive recovery cost.** It exists
so that downstream consumers (e.g. a prioritization model) have a single,
documented, recomputable number to work with.

Formula: for each session, five raw features are extracted:

- `num_interruptions`
- `avg_interruption_duration` (mean of `interruption_durations_seconds`)
- `avg_resume_delay` (mean of `resume_delays_seconds`)
- `num_context_switches`
- `interruption_time_ratio` (`interruption_time_seconds / session_duration_seconds`)

Each is min-max normalized against the population of sessions passed
into the same call (so `estimate_recovery_costs` should generally be
called with a representative population, not one session at a time — a
population of 1 collapses every feature to 0 by construction). Normalized
features are combined with default weights (`DEFAULT_WEIGHTS` in the
module, summing to 1.0) and clipped to `[0, 1]`:

```
recovery_cost_score = Σ weight_i * normalized_feature_i
```

`contributing_features` in the returned `RecoveryCostEstimate` includes
the raw values, normalized values, and weights used, so the score is
always auditable. Weights are configurable via the `weights` parameter
for downstream recalibration.
