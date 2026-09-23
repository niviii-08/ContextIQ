# ContextIQ Project Overview

## Project Objective

ContextIQ uses behavioural event data to identify recurring patterns of forgetting, context switching, and daily friction. It predicts potential forgetting risk with explainable machine learning and converts those patterns into evidence-based proactive recommendations.

This is a portfolio-scale system demonstrating data ingestion, temporal feature engineering, leakage-safe model evaluation, API design, analytics, explainability, and a frontend workflow.

## Key Features

- Core task, event, location, interruption, and user APIs.
- Session reconstruction from timestamped behavioural events.
- Context-switch, interruption, recovery-cost, and friction analytics.
- Association mining for context-dependent "one more thing" recommendations.
- Forgetting-risk prediction with Logistic Regression, Random Forest, and XGBoost candidates.
- Probability calibration, threshold tuning, chronological validation, and SHAP explanations.
- Intelligence layer that ranks evidence-backed recommendations and supports mock or external LLM providers.
- Next.js frontend with loading, empty, error, timeout, and mock-data states.

## Architecture

The frontend calls service APIs. The backend owns core user-scoped data and PostgreSQL persistence. The data engine transforms events into sessions and analytical features. The forgetting ML service trains and serves risk predictions. The context engine reconstructs sessions and mines associations. The intelligence service turns structured outputs into constrained explanations and recommendations.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Technology Stack

| Area | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, Vitest |
| APIs | FastAPI, Pydantic, Uvicorn |
| Persistence | PostgreSQL, SQLAlchemy, Alembic; SQLite for the standalone data engine |
| Data and ML | pandas, NumPy, scikit-learn, XGBoost, SHAP, joblib |
| Analytics | pandas-based metrics, session reconstruction, FP-Growth/Apriori association mining |
| Deployment | Docker Compose, health checks, environment-based configuration |

## Data Pipeline

1. Validate raw events and schemas.
2. Clean malformed, duplicate, missing, and out-of-order records.
3. Normalize timestamps and event fields.
4. Reconstruct task sessions.
5. Compute behavioural metrics and historical features.
6. Export a temporal ML dataset.
7. Train, evaluate, calibrate, and persist the selected model.
8. Populate analytics outputs and quality reports.

Every task feature is computed from information strictly before that task's creation timestamp. See [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) and [docs/FEATURE_DICTIONARY.md](docs/FEATURE_DICTIONARY.md).

## ML Pipeline

The target is `will_forget`: whether a task eventually reaches the forgotten state. Logistic Regression, Random Forest, and XGBoost are compared. Selection prioritizes PR-AUC, then ROC-AUC and F1, because accuracy is misleading for an imbalanced target. Chronological train/validation/test splits, walk-forward validation, leakage assertions, validation threshold tuning, and probability calibration are used.

SHAP or model-native explanations provide ranked contributing features. They describe model associations, not causes or diagnoses.

See [docs/ML_METHODOLOGY.md](docs/ML_METHODOLOGY.md) and the detailed [forgetting-ml methodology](forgetting-ml/docs/MODEL_METHODOLOGY.md).

## Major Engineering Decisions

- Temporal splits instead of random splits for behavioural data.
- `as_of` feature construction to prevent target and future-history leakage.
- User-scoped queries and UUID validation at the core API boundary.
- Centralized API error normalization and environment-only secrets.
- A mock LLM provider so the system is demonstrable without an API key.
- Structured outputs passed to the intelligence layer instead of unrestricted raw user data.
- Health-gated Docker startup and fail-fast database migrations.

## Challenges Solved

- Converting irregular event streams into meaningful sessions.
- Keeping historical features faithful to prediction-time information.
- Handling class imbalance without relying on accuracy.
- Making probability outputs useful through calibration and threshold tuning.
- Combining deterministic analytics, association mining, ML, and optional language generation without presenting generated text as ground truth.

## Limitations

- The current dataset is synthetic and does not establish real-world predictive validity.
- Authentication is still a documented integration boundary in the core backend; development header identity must not be used as production authentication.
- The service suite is independently deployable rather than a single transactionally coordinated application.
- The LLM layer can explain supplied structured evidence, but it cannot make unsupported behavioural claims safe by itself.
- Model performance and fairness on real users are unknown until consented, representative data is collected and evaluated.

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Future Roadmap

- Replace development identity resolution with verified production JWT/OIDC integration.
- Add service-level observability, metrics, tracing, and rate limiting at the deployment edge.
- Validate models on consented longitudinal data with subgroup and calibration monitoring.
- Add model/data contract versioning and automated artifact promotion.
- Improve event deduplication with durable idempotency keys.
- Add a privacy-preserving retention and deletion workflow.

## Responsible Use

ContextIQ is a behavioural productivity research/demo system. It is not a medical, psychological, employment, academic, or credit decision system. Users should be able to understand, correct, delete, and opt out of their data. See [docs/PRIVACY.md](docs/PRIVACY.md).
