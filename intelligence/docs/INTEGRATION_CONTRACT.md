# Integration Contract

This is the contract the rest of ContextIQ needs to integrate this module.
Everything below is stable, versioned by this document, and independent of
this module's internal implementation.

## 1. Input schemas (what you send in)

Defined in `app/schemas.py`. Top-level input object: `IntelligenceBundle`.

```python
class ForgettingPrediction(BaseModel):
    task: str
    probability: float            # 0..1
    risk_level: Literal["low","medium","high"]
    model_version: str
    contributing_features: list[str] = []
    previous_forgetting_count: int | None = None
    weekday_pattern: str | None = None
    timestamp: datetime | None = None

class ContextInsight(BaseModel):
    switch_count: int
    interruption_time_minutes: float
    recovery_cost_minutes: float
    top_interruption: str | None = None
    affected_category: str | None = None
    period: str | None = None

class Association(BaseModel):
    context: str
    task: str
    support: float                # 0..1
    confidence: float              # 0..1
    lift: float                    # >=0

class BehaviourMetric(BaseModel):
    metric_name: str
    value: float
    period: str

class IntelligenceBundle(BaseModel):
    user_id: str
    forgetting_predictions: list[ForgettingPrediction] = []
    context_insights: list[ContextInsight] = []
    associations: list[Association] = []
    metrics: list[BehaviourMetric] = []
    generated_at: datetime | None = None
```

The upstream forgetting model, context-switch analyzer, and association
miner are each responsible for producing lists of these objects. This module
does not validate cross-system consistency beyond field-level types/ranges.

## 2. Output schemas (what you get back)

- `Insight` / `RankedInsight` — see `app/schemas.py`. Always includes
  traceable `evidence`.
- `DailySummary`
- `Recommendation`
- `FeedbackAck`

All are Pydantic models with `.model_dump()` / `.model_dump_json()`
available for serialization.

## 3. API routes

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/insights/generate` | Generate ranked insights (optionally LLM-explained) |
| POST | `/api/v1/insights/daily` | Generate the daily summary |
| POST | `/api/v1/recommendations/generate` | Generate ranked "One More Thing?" recommendations |
| POST | `/api/v1/feedback` | Store user feedback on an insight/recommendation |
| GET | `/api/v1/health` | Health/status check |

Full request/response bodies: `docs/API_CONTRACT.md`.

## 4. Python interfaces (for in-process integration, no HTTP)

If ContextIQ wants to call this module in-process rather than over HTTP:

```python
from app.schemas import IntelligenceBundle
from app.insight_engine import generate_insights
from app.ranking import rank_insights
from app.daily_summary import generate_daily_summary
from app.recommendations import generate_recommendations
from app.llm.provider import get_provider
from app.llm.explanation_service import generate_explanation
from app.feedback_store import FeedbackStore, InMemoryFeedbackStore

bundle = IntelligenceBundle(**upstream_data)

insights = rank_insights(generate_insights(bundle))
summary = generate_daily_summary(bundle)
recommendations = generate_recommendations(bundle, max_recommendations=5)
```

## 5. LLM abstraction

```python
from app.llm.provider import LLMProvider, get_provider

provider: LLMProvider = get_provider("mock")        # or "anthropic" / "openai"
# implement LLMProvider.complete(system_prompt, user_prompt, max_tokens) for a new vendor
```

`get_provider(name, api_key)` is the only factory ContextIQ needs to call.
No other integration code should import a specific vendor SDK directly.

## 6. Error handling

- All inputs are validated via Pydantic at the API boundary; malformed input
  produces `422` with a structured FastAPI validation error body.
- LLM provider failures (network errors, missing API key, vendor exceptions)
  never propagate as explanation failures — they trigger the deterministic
  fallback path (`LLMExplanationResult.used_fallback = True`) rather than
  raising, so `/insights/generate` never fails due to LLM issues alone.
- A genuinely misconfigured provider (unknown `LLM_PROVIDER` value, or a
  cloud provider selected with no API key) raises at request time as `500`,
  which should be treated as a deployment/config issue, not a runtime data
  issue.

## 7. Feedback structure

```python
class FeedbackEntry(BaseModel):
    user_id: str
    target_type: str   # "insight" | "recommendation" | "summary"
    target_id: str
    feedback: Literal["useful","not_useful","incorrect","dismissed"]
    comment: str | None = None
    created_at: datetime
```

Persisted via the `FeedbackStore` interface (`app/feedback_store.py`).
`InMemoryFeedbackStore` is the default; swap in a database-backed
implementation of the same interface for production without touching
callers.

## 8. What this module explicitly does NOT do

Per the original scope, this module does not implement, and should never be
asked to implement:
- The forgetting prediction model itself
- Association mining itself
- Any frontend/UI
- Message reading, screen monitoring, keylogging, or other surveillance

These remain the responsibility of separate ContextIQ modules, which should
produce data conforming to the input schemas in Section 1.
