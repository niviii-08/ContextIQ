# Feature Engineering

This document describes every feature used by the Forgetting Prediction
Engine, how it is constructed, and why it is safe from data leakage.

## Prediction point definition

Each row in the dataset represents a **prediction point**: the moment a
task is logged/created, before its outcome (completed or forgotten) is
known. All features attached to a row must be computable using only
information available strictly **before** that moment. The label
(`forgotten`) is the outcome of that specific task instance, observed
only after the fact.

## Feature list

### Categorical features

| Feature | Description | Domain |
|---|---|---|
| `task_category` | Type of task | Academic, Work, Personal, Health, Household, Social, Finance |
| `priority` | User- or system-assigned priority | LOW, MEDIUM, HIGH |
| `location` | Context/location associated with the task | Home, Campus, Office, Commute, Gym, Other |

### Numeric features

| Feature | Description | Leakage-safety notes |
|---|---|---|
| `weekday` | Day of week (0=Monday) the task was created | Known at creation time |
| `hour` | Hour of day the task was logged | Known at creation time |
| `deadline_distance_hours` | Hours between task creation and its deadline | Deadline is set at creation time; safe |
| `previous_completion_count` | Running count of this user's completed tasks **before** this one | Computed from a rolling counter updated only *after* each prior task's outcome was recorded |
| `previous_forgetting_count` | Running count of this user's forgotten tasks **before** this one | Same rolling-counter construction |
| `historical_completion_rate` | `previous_completion_count / total_tasks_seen_so_far` | Derived purely from prior rows |
| `historical_forgetting_rate` | `previous_forgetting_count / total_tasks_seen_so_far` | Derived purely from prior rows |
| `task_frequency` | How often this task's category has recurred for this user, relative to all tasks seen so far | Rolling per-category counter, prior-only |
| `tasks_today` | Number of tasks logged by the user on this calendar day | Known once the day's task list is being generated; does not depend on any task's outcome |
| `interruptions_today` | Interruptions experienced by the user up to this point in the day | Environmental signal, independent of any task outcome |
| `recent_context_switches` | Context switches in the recent window (last ~24h) | Environmental signal, independent of any task outcome |
| `avg_interruption_duration` | Average duration of interruptions that day (minutes) | Environmental signal |
| `avg_session_duration` | Average focused work-session duration that day (minutes) | Environmental signal |

## Explicitly excluded (leakage) features

The following are **never** used as model inputs, because they are only
knowable after the outcome:

- Final task status / completion timestamp
- Time actually spent on the task
- Interruptions that occurred *after* the task's deadline window
- Any aggregate statistic that includes the current row's own outcome
  (all rolling counters are updated strictly *after* a row is generated —
  see `ml/data/generate_dataset.py`, which increments counters only after
  each row is appended)

## Rolling counter construction (temporal safety)

For every synthetic user, counters (`completions`, `forgettings`,
`total_tasks_seen`, and per-category equivalents) are initialized to zero
and processed **chronologically**, one task at a time:

1. Compute this row's features from the *current* counter state.
2. Generate this row's label (`forgotten`).
3. **Only after** the row is finalized, update the counters using this
   row's own outcome.

This guarantees that no row's features are influenced by its own label,
and that later rows correctly reflect everything that happened earlier —
mirroring how a real production system would compute these features from
an event log at serving time.

## Encoding at inference time

- Categorical features are one-hot encoded (`OneHotEncoder(handle_unknown="ignore")`)
  so previously unseen category values at inference time do not crash the
  pipeline; they are encoded as all-zero rather than raising an error.
- Numeric features are median-imputed (missing-value robustness) and,
  for the Logistic Regression model specifically, standard-scaled.
- The exact same fitted `ColumnTransformer` used during training is
  serialized and reused at inference — there is no re-fitting or
  separate inference-time feature logic, eliminating train/serve skew.
