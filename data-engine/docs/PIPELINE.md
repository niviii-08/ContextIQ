# ContextIQ Data Engineering Pipeline

## Overview

ContextIQ's behavioural data pipeline is a 10-stage, deterministic, end-to-end pipeline that transforms raw append-only event streams into ML-ready datasets, trained prediction models, populated analytics tables, and auditable data-quality reports.

```
Raw Events (CSV/Synthetic)
  │
  ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 1  VALIDATION     (pipeline/validate.py)               │
│  ─ timestamp sanity  ─  required fields  ─  enum validity    │
│  ─ duplicate fingerprinting  ─  sequence ordering            │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 2  CLEANING       (pipeline/clean.py)                  │
│  ─ tz → UTC  ─  dedup on natural keys  ─  category alias map │
│  ─ duration/end_time imputation  ─  outlier (is_anomaly) flag│
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 3  TRANSFORMATION  (pipeline/transform.py)             │
│  ─ hour/weekday/late-night buckets   ─  inter-event gaps     │
│  ─ task_age_at_start  ─  session_index  ─  task_location_pair│
│  ─ is_repeated_context  ─  interruption_density              │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 4  SESSION RECON  (pipeline/reconstruct.py)            │
│  ─ wraps app/services/session_engine.py (pure functions)     │
│  ─ open/close event walk  ─  overlap-based interruption attach│
│  ─ focused_time, context_switches, resume_delay per session  │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 5  FEATURE ENG    (pipeline/features.py)               │
│  ─ extends app/utils/features.py (leakage-free, as_of-based) │
│  ─ recovery_time  ─  daily_friction  ─  forgetting_streak    │
│  ─ rolling 7d session/switch rates  ─  repeated_context_count│
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 6  ML EXPORT      (pipeline/ml_export.py)              │
│  ─ TEMPORAL train/test split (NOT random — no future leak)   │
│  ─ Parquet: train.parquet, test.parquet, labels, schema.json │
│  ─ logs class balance, completeness, missing-value rates     │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 7  MODEL TRAIN    (pipeline/model.py)                  │
│  ─ LogisticRegression + RandomForest (impute→scale→model)    │
│  ─ metrics: prec/recall/F1/ROC-AUC/confusion matrix          │
│  ─ SHAP mean|abs| feature importance (RF)                    │
│  ─ saved: data/ml/models/*.joblib + evaluation_report.json   │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 8  ANALYTICS POP  (pipeline/populate_analytics.py)     │
│  ─ daily_completion_rate / daily_forgetting_rate (per user)  │
│  ─ daily_friction_score (composite 4-component 0-100)        │
│  ─ per-category and per-location rollups                     │
│  ─ upsert into behaviour_metrics via UNIQUE constraint       │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 9  ORCHESTRATOR   (pipeline/run_pipeline.py)           │
│  ─ single entry:  python pipeline/run_pipeline.py --seed 42  │
│  ─ CLI: --users N --days N --skip-training --csv-only        │
│  ─ per-stage timing + logger-based progress + final summary  │
└──────────────────────┬───────────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 10 QUALITY REPORT (pipeline/quality_report.py)         │
│  ─ record counts, null rates, duplicate rates, time ranges   │
│  ─ sequence validity, ML class balance, feature completeness │
│  ─ output: data/quality_report.md  +  quality_report.html    │
└──────────────────────────────────────────────────────────────┘
```

---

## Running the Pipeline

```bash
cd data-engine

# End-to-end with default synthetic dataset params
python pipeline/run_pipeline.py --seed 42

# Custom dataset size, skip training for quick iteration
python pipeline/run_pipeline.py --users 20 --days 30 --seed 42 --skip-training

# Orchestrator flags:
#   --users N        Number of synthetic user personas to simulate
#   --days N         Days of behavioural history per user
#   --seed N         Fixed RNG seed for reproducibility
#   --skip-training  Skip Stage 7 (model training / SHAP)
#   --csv-only       Only write CSVs; don't load to DB
#   --report-dir D   Output directory for quality reports
```

---

## Stage 1 — Validation (`pipeline/validate.py`)

### Purpose
Catch data-quality issues **before** they reach cleaning, the DB, or analytics. Returns a structured `ValidationReport` dataclass; never modifies input DataFrames.

### Rules

| Rule | Stage | Severity | Description |
|---|---|---|---|
| `missing_required_field` | events, interruptions, tasks | error | user_id/task_id/event_type/event_time (events); user_id/type/start (interruptions) |
| `invalid_event_type` | events | error | `event_type ∉ {created,started,paused,resumed,completed,forgotten,cancelled}` |
| `invalid_interruption_type` | interruptions | error | `interruption_type ∉ {phone,social_media,message,call,search,person,food,other}` |
| `invalid_status` | tasks | error | `status ∉ valid task set` |
| `invalid_timestamp` | events, interruptions | error | Cannot be parsed as datetime |
| `future_timestamp` | events, interruptions | warning | event_time > now |
| `prehistoric_timestamp` | events | error | event_time < 2000-01-01 |
| `duplicate_event` | events | warning | Same (user_id, task_id, event_type, event_time) fingerprint |
| `impossible_sequence` | events | error | completed/forgotten/cancelled precedes any created/started on same task |
| `end_before_start` | interruptions | error | end_time < start_time |
| `negative_duration` | interruptions | error | duration_seconds < 0 |
| `invalid_priority` | tasks | error | priority ∉ [1,5] |
| `started_before_created` | tasks | error | started_at < created_at |
| `completed_before_started` | tasks | error | completed_at < started_at |

### Key Types
```python
@dataclass
class ValidationReport:
    issues: list[ValidationIssue]
    @property errors   # severity=="error"
    @property warnings # severity=="warning"
    @property is_clean # no errors
```

---

## Stage 2 — Cleaning (`pipeline/clean.py`)

### Purpose
Deterministically correct / flag data issues. Every operation is counted in a `CleaningReport` for auditability.

### Operations (applied in order)

1. **Timezone normalization** — every datetime column coerced to UTC-aware via `pd.to_datetime(..., utc=True)`
2. **Duplicate removal** — drop duplicates on natural keys, keeping first occurrence:
   - events: `(user_id, task_id, event_type, event_time)`
   - interruptions: `(user_id, task_id, interruption_type, start_time)`
   - tasks: `(id)`
3. **Duration imputation** — `interruption.duration_seconds = end_time - start_time` where duration is null but both timestamps exist
4. **End-time imputation** — `interruption.end_time = start_time + duration_seconds` where end_time is null but duration is known
5. **Category normalization** — lowercase + strip + alias map. E.g. `"Deep Work"` → `"deep_work"`, `"e-mail"` → `"email"`, `"housework"` → `"chores"`
6. **Priority clamping** — any priority outside [1,5] clamped defensively
7. **Outlier flagging** — sessions/tasks > 12 hours get `is_anomaly=True` (kept, not removed)

---

## Stage 3 — Transformation (`pipeline/transform.py`)

### Purpose
Enrich cleaned DataFrames with derived columns needed by Stage 5 (features) and analytics. Non-destructive: original columns preserved.

### Derived Columns

**`task_events` DataFrame:**

| Column | Type | Formula / Description |
|---|---|---|
| `event_hour` | int | `event_time.dt.hour` |
| `event_weekday` | str | `event_time.dt.day_name()` ("Monday", ...) |
| `event_weekday_num` | int | 0=Monday … 6=Sunday |
| `is_late_night` | bool | `event_hour >= 21` |
| `inter_event_gap_s` | float | Seconds between this event and the previous event on the **same task** (NaN for first event) |
| `session_index` | int | 0-based session counter within task; increments on every `started`/`resumed` event |

**`tasks` DataFrame:**

| Column | Type | Formula / Description |
|---|---|---|
| `task_age_at_start_h` | float | `(started_at - created_at).total_seconds() / 3600` |
| `task_duration_h` | float | `(completed_at - started_at).total_seconds() / 3600` |
| `deadline_distance_h` | float | `(deadline_at - created_at).total_seconds() / 3600` |
| `is_late_night_start` | bool | `started_at.hour >= 21` |
| `location_type` | str | Lookup from `locations_df.location_type` keyed by `tasks.location_id` |
| `task_location_pair` | str | `<category>@<location_type>` combined context key |
| `is_repeated_context` | bool | `True` if user already had ≥1 prior task with the same `(category, location_id)` |

**`interruptions` DataFrame:**

| Column | Type | Formula / Description |
|---|---|---|
| `interruption_hour` | int | `start_time.dt.hour` |
| `interruption_weekday` | str | `start_time.dt.day_name()` |
| `interruption_density` | float | `1 / (duration_seconds / 60)` → higher = shorter, "denser" bursts of disruption |

---

## Stage 4 — Session Reconstruction (`pipeline/reconstruct.py`)

### Purpose
DataFrame-in / DataFrame-out wrapper around the **existing pure functions** in `app/services/session_engine.py` so they can be used **without a database connection** (fully testable offline).

### Reuse (no duplication)
- `build_raw_sessions_for_task()` → walks events, produces `_RawSession` windows
- `compute_session_metrics()` → focused_time, interruption_time, resume_delay, context_switches, interruption_count

### Algorithm Summary (per task)
1. Sort events by `event_time`.
2. Walk events pairwise. Open session on `created / started / resumed`; close on `paused / completed / forgotten / cancelled`.
3. Dangling open session → close at `last_event + idle_timeout_minutes` (default 30 min).
4. Attach every interruption whose `[start, end]` overlaps the session window.
5. Compute:
   - `focused_time_seconds = max(0, session_seconds − overlapping_interruption_seconds)`
   - `interruption_time_seconds = Σ overlap_seconds`
   - `context_switch_count = # interruptions with duration ≥ context_switch_gap_minutes`
   - `resume_delay_seconds` (only for resumed-opened sessions): gap between prior pause and this resume

### Output Schema (`sessions_df`)
```
task_id, user_id, location_id,
session_start, session_end,
focused_time_seconds, interruption_time_seconds,
resume_delay_seconds, context_switch_count, interruption_count
```

---

## Stage 5 — Feature Engineering (`pipeline/features.py`)

### Purpose
Build the ML-ready feature matrix. **One row per task.** Every feature computed strictly BEFORE that task's `created_at`.

### Leakage Prevention (critical)
All history slices use `_before(df, col, as_of)` → `df[df[col] < as_of]`, where `as_of = task.created_at`. This means the model, at prediction time, only sees the exact information that would have been available at the moment the task was created. No future data ever leaks.

### Feature Groups
- **Group A — preserved & extended from `app/utils/features.py`:** previous forgetting/completion counts, completion rate, category/location/weekday/hour forgetting rates, task_frequency, days_since_last_similar, deadline_distance, priority, tasks_today, interruptions_today, recent_context_switches, avg_interruption_duration.
- **Group B — new in this module:** recovery_time_s, daily_friction_score, repeated_context_count, forgetting_streak, avg_session_duration_7d_s, context_switch_rate_7d, is_late_night, is_repeated_context.
- **Target:** `will_forget = 1 if task.status == "forgotten" else 0`

Full catalog: see [`FEATURE_DICTIONARY.md`](./FEATURE_DICTIONARY.md).

---

## Stage 6 — ML Dataset Export (`pipeline/ml_export.py`)

### Split Strategy: TEMPORAL (not random)
Tasks are sorted by `created_at`. First `(1 - test_fraction)` chronologically → training set; remaining → test set.

**Why temporal?** A random split would leak future information: a training row's features could be computed using events that only exist after the test row's `created_at`. Temporal split guarantees `max(train.created_at) < min(test.created_at)`, exactly matching a live production deployment where models are trained on historical data and evaluated on the future.

### Outputs (`data/ml/`)
| File | Contents |
|---|---|
| `train.parquet` | Training feature matrix (numeric features only) |
| `train_labels.parquet` | Single column `will_forget` for training set |
| `test.parquet` | Test feature matrix |
| `test_labels.parquet` | Single column `will_forget` for test set |
| `feature_schema.json` | Per-column: dtype, null_rate, min, max, mean |
| `split_summary.json` | n_train, n_test, split_date, class balance, feature names |

---

## Stage 7 — Model Training / Inference (`pipeline/model.py`)

### Models Trained
Both models are wrapped in an identical `Impute(median) → StandardScaler → Estimator` sklearn Pipeline so production inference code can call `.predict_proba()` with identical preprocessing.

| Model | Rationale | Hyperparams |
|---|---|---|
| **Logistic Regression** | Baseline: fast, interpretable, linear signal | `max_iter=1000, class_weight="balanced"` |
| **Random Forest** | Non-linear + interactions, feature importance | `n_estimators=200, max_depth=8, class_weight="balanced"` |

### Evaluation Metrics
- Accuracy, Precision (macro), Recall (macro), F1 (macro + weighted), ROC-AUC, Confusion Matrix
- SHAP mean|SHAP| per feature (Random Forest only, subsample of 500 rows)

### Artifacts (`data/ml/models/`)
- `logistic_regression.joblib`
- `random_forest.joblib`
- `evaluation_report.json`
- `shap_importance.csv`

### ⚠ Synthetic Data Notice
All models are explicitly trained on **synthetic, persona-driven behavioural data**. They demonstrate pipeline architecture and feature quality — they are not production-ready predictors. The evaluation JSON and the training log both carry this notice.

---

## Stage 8 — Analytics Table Population (`pipeline/populate_analytics.py`)

### Purpose
Pre-compute expensive aggregates into the existing `behaviour_metrics` table so dashboard endpoints (FastAPI routes in `app/api/analytics.py`) return instantly rather than scanning raw tables.

### Writes (all idempotent via `UNIQUE(user_id, metric_name, dimension, period_start)` + upsert)

**Per-user per-day (dimension="overall"):**
- `daily_task_count` — tasks created
- `daily_completion_rate` — % of resolved tasks completed (×100)
- `daily_forgetting_rate` — % of resolved tasks forgotten (×100)
- `daily_interruption_count` — interruptions started
- `daily_friction_score` — composite 4-component score 0–100 (see `app/analytics/friction.py`), persisted with all 4 sub-scores in `extra: JSON`

**Per-user per-category (dimension=`"category:<cat>"`):**
- `category_completion_rate`, `category_forgetting_rate`, `category_task_count`

**Per-user per-location (dimension=`"location:<uuid>"`):**
- `location_completion_rate`, `location_forgetting_rate`, `location_task_count` (with `extra.location_name` human label)

---

## Stage 9 — Orchestration (`pipeline/run_pipeline.py`)

Single entrypoint. Runs stages 0→1→2→3→4→5→6→(7 unless `--skip-training`)→8→10 with stage headers, timing, and a final summary block listing every output artifact.

---

## Stage 10 — Data Quality Report (`pipeline/quality_report.py`)

Both Markdown (`data/quality_report.md`) and styled HTML (`data/quality_report.html`) versions are generated. Sections:

1. **Record counts per table** — rows × cols
2. **Null rates per column** — with 🔴 (>20%) / 🟡 (5–20%) badges
3. **Event sequence validity** — impossible sequences, dangling open sessions
4. **Duplicate rates** — per-table counts removed at Stage 2
5. **Timestamp range sanity** — earliest, latest, range in days
6. **ML target class balance** — `will_forget` distribution
7. **Feature completeness** — features <90% populated called out
8. **Validation & cleaning summary** — all issue counts + operation counts

---

## Folder Layout

```
data-engine/
├─ app/                          ← UNCHANGED preserved ORM + services + utils
│   ├─ models/                        Task, TaskEvent, Interruption, Location
│   ├─ services/session_engine.py     Pure session reconstruction algos
│   ├─ utils/features.py              Per-task / user / context features
│   └─ analytics/                     friction.py + metrics.py
├─ pipeline/                      ← all 10 pipeline stages (new files)
│   ├─ validate.py                     Stage 1
│   ├─ clean.py                        Stage 2
│   ├─ transform.py                    Stage 3
│   ├─ reconstruct.py                  Stage 4  (wraps session_engine.py)
│   ├─ features.py                     Stage 5  (extends utils/features.py)
│   ├─ ml_export.py                    Stage 6
│   ├─ model.py                        Stage 7
│   ├─ populate_analytics.py           Stage 8
│   ├─ run_pipeline.py                 Stage 9 — orchestrator
│   └─ quality_report.py               Stage 10
├─ docs/
│   ├─ PIPELINE.md                     ← this file
│   └─ FEATURE_DICTIONARY.md           ← every feature documented
├─ data/
│   ├─ synthetic/                  Raw CSVs from Stage 0
│   ├─ ml/                         Stage 6 + Stage 7 outputs
│   │   ├─ train.parquet
│   │   ├─ test.parquet
│   │   ├─ feature_schema.json
│   │   └─ models/                 *.joblib, evaluation_report.json, shap_importance.csv
│   ├─ quality_report.md           Stage 10 output
│   └─ quality_report.html
└─ requirements.txt                Already updated: sklearn, shap, pyarrow, tabulate
```

---

## Preservation Guarantee

- Every file under `app/models/`, `app/services/session_engine.py`, `app/utils/features.py`, `app/analytics/metrics.py`, `app/analytics/friction.py`, `scripts/generate_synthetic_data.py` is **preserved and reused** — never replaced or duplicated.
- Pipeline stages either call the existing pure functions directly (Stage 4 → `session_engine.py`, Stage 5 extends `features.py` patterns) or consume their outputs as DataFrames.
