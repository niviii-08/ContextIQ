# ContextIQ — Forgetting Prediction Engine

A standalone machine learning module that estimates:

> **P(task will be forgotten | information available before prediction time)**

This is a **behavioural prediction system**, built from historical
task-completion patterns. It is explicitly **not** a psychological or
medical diagnostic system, and its outputs must never be represented as
a clinical assessment.

This module is fully self-contained — it does not depend on any other
ContextIQ repository or service, and can be trained, tested, and served
independently of everything else.

---

## What's in this repo

```
contextiq-forgetting-ml/
├── app/                    # FastAPI inference service
│   ├── main.py              # app entrypoint
│   ├── api.py                # routes
│   ├── schemas.py            # Pydantic request/response contracts
│   └── inference.py          # loads model bundle, runs predictions
├── ml/
│   ├── data/                 # synthetic dataset generator
│   ├── features/              # shared feature spec (single source of truth)
│   ├── preprocessing/         # sklearn ColumnTransformer pipeline
│   ├── training/               # train.py, chronological split logic
│   ├── evaluation/             # plot/report generation
│   └── explainability/         # SHAP-based reason generation
├── datasets/                 # generated CSVs (tasks_raw.csv, users.csv)
├── artifacts/                 # trained model bundle, metrics.json, plots
├── scripts/                    # CLI batch-scoring utility
├── tests/                       # pytest suite
├── docs/                         # methodology, features, evaluation, API docs
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate the synthetic dataset

```bash
python -m ml.data.generate_dataset
```

Produces `datasets/tasks_raw.csv` (~49.8K rows across 100 simulated users
over 95 days) and `datasets/users.csv` (reference/debug table of latent
user archetypes — not used directly as a model feature).

### 3. Train all models and generate the evaluation report

```bash
python -m ml.training.train
```

This trains Logistic Regression, Random Forest, and XGBoost, evaluates
all three on a chronological (time-aware) held-out test set, selects a
winner using a documented multi-metric strategy, calibrates its
probabilities, and writes everything to `artifacts/`:

- `model_bundle.joblib` — the model, preprocessor, feature list, version, threshold
- `metrics.json` — full metrics for every candidate model + the final selected model
- `confusion_matrix.png`, `roc_curve.png`, `precision_recall_curve.png`,
  `feature_importance.png`, `calibration_plot.png`

### 4. Run the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000/docs` for interactive Swagger docs.

### 5. Run the tests

```bash
pytest tests/ -v
```

### 6. Batch-score a CSV offline (no server required)

```bash
python scripts/run_batch_prediction.py --input my_tasks.csv --output predictions.csv
```

---

## Docker

```bash
docker build -t contextiq-forgetting-ml .

# Train first (writes into a mounted artifacts/ volume)
docker run --rm -v $(pwd)/datasets:/app/datasets -v $(pwd)/artifacts:/app/artifacts \
  contextiq-forgetting-ml \
  sh -c "python -m ml.data.generate_dataset && python -m ml.training.train"

# Then serve
docker run --rm -p 8000:8000 -v $(pwd)/artifacts:/app/artifacts \
  contextiq-forgetting-ml
```

---

## Documentation

| Doc | Covers |
|---|---|
| [`docs/FEATURE_ENGINEERING.md`](docs/FEATURE_ENGINEERING.md) | Every feature, how it's constructed, and why it's leakage-safe |
| [`docs/MODEL_METHODOLOGY.md`](docs/MODEL_METHODOLOGY.md) | Dataset, models, validation strategy, actual trained results, trade-offs, limitations |
| [`docs/EVALUATION.md`](docs/EVALUATION.md) | Metric definitions, imbalance handling, calibration analysis, known limitations |
| [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) | Full request/response schemas for every endpoint |

---

## Integration Contract

This section specifies exactly how another application integrates with
this module. Two integration paths are supported: **HTTP API** (for
services in any language) and **direct Python import** (for services
that can run in the same Python environment/process).

### Option A — HTTP API integration

**Endpoint:** `POST /api/v1/predictions/forgetting`

**Input JSON schema:**

```json
{
  "task_id": "string | null (optional)",
  "task_category": "Academic | Work | Personal | Health | Household | Social | Finance",
  "priority": "LOW | MEDIUM | HIGH",
  "location": "Home | Campus | Office | Commute | Gym | Other",
  "weekday": "int, 0-6",
  "hour": "int, 0-23",
  "deadline_distance_hours": "float, >= 0",
  "previous_completion_count": "int, >= 0",
  "previous_forgetting_count": "int, >= 0",
  "historical_completion_rate": "float, 0-1",
  "historical_forgetting_rate": "float, 0-1",
  "task_frequency": "float, 0-1",
  "tasks_today": "int, >= 0",
  "interruptions_today": "int, >= 0",
  "recent_context_switches": "int, >= 0",
  "avg_interruption_duration": "float, >= 0",
  "avg_session_duration": "float, >= 0"
}
```

**Output JSON schema:**

```json
{
  "task": "string | null",
  "prediction_probability": "float, 0-1",
  "risk_level": "LOW | MEDIUM | HIGH",
  "model_version": "string (semver)",
  "top_features": ["string", "..."]
}
```

**Batch variant:** `POST /api/v1/predictions/forgetting/batch` accepts
`{"tasks": [ ...same shape as above... ]}` and returns
`{"predictions": [ ...same response shape... ]}` in the same order.

Full field-level constraints, examples, and error codes:
[`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).

### Option B — Direct Python integration

If the integrating application runs in the same Python environment, it
can import the inference layer directly without going through HTTP:

```python
from app.inference import ForgettingPredictor

predictor = ForgettingPredictor.instance()  # loads artifacts/model_bundle.joblib once

result = predictor.predict_single({
    "task_id": "Lab Record",
    "task_category": "Academic",
    "priority": "HIGH",
    "location": "Campus",
    "weekday": 2,
    "hour": 14,
    "deadline_distance_hours": 18.0,
    "previous_completion_count": 12,
    "previous_forgetting_count": 8,
    "historical_completion_rate": 0.4,
    "historical_forgetting_rate": 0.55,
    "task_frequency": 0.3,
    "tasks_today": 5,
    "interruptions_today": 4,
    "recent_context_switches": 6,
    "avg_interruption_duration": 8.5,
    "avg_session_duration": 22.0,
})
# result == {"task": ..., "prediction_probability": ..., "risk_level": ...,
#            "model_version": ..., "top_features": [...]}

# Batch:
results = predictor.predict_batch([task_dict_1, task_dict_2, ...])
```

### Required feature names (exact strings, order-independent)

Categorical: `task_category`, `priority`, `location`

Numeric: `weekday`, `hour`, `deadline_distance_hours`,
`previous_completion_count`, `previous_forgetting_count`,
`historical_completion_rate`, `historical_forgetting_rate`,
`task_frequency`, `tasks_today`, `interruptions_today`,
`recent_context_switches`, `avg_interruption_duration`,
`avg_session_duration`

This list is defined once in `ml/features/feature_spec.py` and imported
by both the API schema (`app/schemas.py`) and the training pipeline —
there is a single source of truth, so integrators can rely on it not
drifting between training and serving.

### Model artifact structure

`artifacts/model_bundle.joblib` is a single joblib-serialized dict:

```python
{
    "model": ...,                       # final (possibly calibrated) sklearn-compatible classifier
    "raw_model": ...,                    # uncalibrated model, used internally for SHAP
    "preprocessor": ...,                  # fitted sklearn ColumnTransformer
    "model_name": "logistic_regression",   # which of the 3 candidate model types was selected
    "model_version": "1.0.0",
    "threshold": 0.215,                     # F1-tuned decision threshold for this model version
    "calibrated": True,
    "feature_names_raw": [...],              # input column names, in required order
    "feature_names_transformed": [...],       # post-preprocessing column names (for explainability)
    "categorical_features": [...],
    "numeric_features": [...],
    "background_sample": ...,                 # SHAP background set (logistic regression only)
}
```

Integrating applications should treat this file as an opaque artifact
and always go through `app/inference.py`'s `ForgettingPredictor` class
(HTTP or direct import) rather than unpickling and using its internals
directly, so that preprocessing and explainability stay correctly
paired with the model.

### What this module does NOT do

Per scope, the following are explicitly out of scope for this module and
are left to separate ContextIQ modules:

- Recommendation engine
- Association mining
- LLM-based features
- Frontend / UI

---

## Ethical & responsible-use notes

- Outputs are **probabilistic behavioural estimates**, not facts about a
  specific future event and not a diagnosis of any condition.
- `top_features` explanations describe **statistical association**
  learned from (synthetic) historical data — never causation.
- All reported evaluation metrics are measured on a **synthetic**
  dataset (see `docs/MODEL_METHODOLOGY.md`). They demonstrate that the
  pipeline works end-to-end and recovers a known synthetic signal; they
  are **not** a claim about real-world accuracy. Retraining and
  revalidation on real data is required before using this in any
  decision that materially affects a user.
