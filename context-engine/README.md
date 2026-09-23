# ContextIQ — Context Intelligence Module

A standalone, independently-runnable module implementing two intelligence
systems for later integration into **ContextIQ**:

- **System A — Context Switching Intelligence**: reconstructs work
  sessions from raw behavioural events, computes interruption/switching
  metrics, discovers recurring behavioural patterns, and estimates a
  transparent "recovery cost" score.
- **System B — "One More Thing" Contextual Task Discovery**: mines
  association rules (Apriori / FP-Growth) over tasks completed within a
  context, and generates ranked, quality-filtered task recommendations,
  optionally combined with an external forgetting-risk signal.

This module does **not** implement a frontend, an LLM, or the forgetting
model itself — those are separate modules. A mock forgetting-risk
provider is included purely so the combined-intelligence interface can
be exercised end-to-end in tests and demos.

## Project layout

```
contextiq-context-engine/
├── app/                      FastAPI application
│   ├── main.py                app entrypoint
│   ├── state.py                in-memory store (swap for real DB in production)
│   ├── api/
│   │   ├── context.py          /api/v1/context/* routes
│   │   └── recommendations.py  /api/v1/recommendations/* routes
│   └── schemas/                 Pydantic request/response models
├── ml/
│   ├── context/                 System A: session reconstruction, metrics,
│   │                             pattern discovery, recovery cost
│   ├── associations/             System B: transactions, mining, recommender
│   ├── features/                 shared feature engineering
│   └── evaluation/               offline evaluation helpers
├── datasets/
│   └── synthetic_data_generator.py   realistic synthetic event generator
├── scripts/
│   ├── generate_synthetic_data.py
│   └── run_pipeline.py           end-to-end demo, writes to artifacts/
├── artifacts/                    generated CSVs / plots (gitignored contents)
├── tests/                        pytest suite (46 tests)
├── docs/
│   ├── CONTEXT_INTELLIGENCE.md   System A design + formulas
│   ├── ASSOCIATION_MINING.md     System B design + metric definitions
│   ├── API_CONTRACT.md           full API + Python integration contract
│   └── EVALUATION.md             how to evaluate quality offline
├── requirements.txt
└── Dockerfile
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate synthetic data and run the full demo pipeline
python scripts/generate_synthetic_data.py
python scripts/run_pipeline.py

# Run the test suite
pytest -q

# Run the API locally
uvicorn app.main:app --reload
# then open http://127.0.0.1:8000/docs
```

Or with Docker:

```bash
docker build -t contextiq-context-engine .
docker run -p 8000:8000 contextiq-context-engine
```

## The two systems, briefly

### System A — Context Switching Intelligence

1. `ml/context/session_reconstruction.py` turns a flat stream of
   `START / PAUSE / RESUME / INTERRUPTION / TASK_SWITCH / COMPLETE`
   events into structured sessions with derived timing fields.
2. `ml/context/metrics.py` aggregates those sessions into rates such as
   `switches_per_hour` and `interruptions_per_session`.
3. `ml/context/pattern_discovery.py` finds recurring behaviour using
   frequency analysis (z-scores over group rates), KMeans clustering,
   and IsolationForest anomaly detection — no deep learning.
4. `ml/context/recovery_cost.py` estimates a transparent, documented
   "recovery cost" score from measurable timing features. It is
   explicitly **not** a validated psychological measurement.

### System B — "One More Thing"

1. `ml/associations/transactions.py` groups `COMPLETE` events into
   per-visit "baskets" of tasks per (user, context).
2. `ml/associations/mining.py` mines frequent itemsets (Apriori or
   FP-Growth via mlxtend) and derives support/confidence/lift rules,
   filtered by configurable thresholds.
3. `ml/associations/recommender.py`'s `recommend_for_context(...)` turns
   rules into ranked, de-duplicated recommendations, applying
   confidence/support/lift thresholds, cooldown, and dismissal support.
   `prioritize_recommendations(...)` optionally blends in an external
   forgetting-risk signal via a pluggable `ForgettingRiskProvider`.

See `docs/CONTEXT_INTELLIGENCE.md`, `docs/ASSOCIATION_MINING.md`, and
`docs/API_CONTRACT.md` for full details and the integration contract.

## Design constraints honoured

- No deep learning used anywhere (KMeans, IsolationForest, Apriori/FP-Growth,
  and transparent hand-engineered formulas only).
- Recovery cost formula is documented and explicitly disclaimed as not
  psychologically validated.
- No recommendation is hardcoded — everything is derived from mined
  association rules over (synthetic or real) transaction data.
- The forgetting model is not implemented here; only a mock/pluggable
  interface is provided (`ForgettingRiskProvider`).
- No frontend or LLM code is included.
