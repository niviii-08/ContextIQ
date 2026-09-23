# API Contract

Base path: `/api/v1`. All request/response bodies are JSON, validated by
the Pydantic models in `app/schemas/`. Interactive docs are available at
`/docs` (Swagger) and `/redoc` when the app is running.

## POST /api/v1/context/analyze

Runs the full System A pipeline (session reconstruction → metrics →
pattern discovery → recovery cost) over a batch of raw events, and
opportunistically mines & caches association rules per context found in
the batch (so subsequent `GET /context/{context_id}/associations` and
`POST /recommendations/context` calls have data to serve).

**Request body** (`EventBatch`):

```json
{
  "events": [
    {
      "user_id": "user_001",
      "timestamp": "2026-01-01T09:00:00",
      "task_id": "collect_form",
      "task_category": "admin",
      "context": "department",
      "event_type": "START",
      "interruption_source": null
    }
  ]
}
```

**Response** (`ContextAnalysisResult`): `sessions`, `metrics`, `patterns`,
`recovery_estimates` — see schemas below.

**Errors**: `400` if `events` is empty.

## GET /api/v1/context/{context_id}/associations

**Query params**: `algorithm` (`apriori` | `fpgrowth`, default `apriori`),
`min_support` (default 0.1), `min_confidence` (default 0.3), `min_lift`
(default 1.0).

**Response** (`ContextAssociationResult`): `context`, `num_transactions`
(`-1` when serving cached rules where the original transaction count
wasn't tracked post-hoc — mine fresh via `/context/analyze` if you need
this figure), `frequent_itemsets_count`, `rules`, `algorithm`,
`thresholds`.

**Errors**: `404` if no rules have been mined yet for that context (call
`POST /context/analyze` first).

## POST /api/v1/recommendations/context

**Request body** (`RecommendationRequest`):

```json
{
  "user_id": "user_001",
  "context": "department",
  "completed_tasks": ["collect_form"]
}
```

**Response** (`RecommendationResponse`):

```json
{
  "user_id": "user_001",
  "context": "department",
  "recommendations": [
    {
      "task": "submit_record",
      "confidence": 0.78,
      "support": 0.42,
      "lift": 1.8,
      "reason": "Frequently completed together with collect_form during department visits."
    }
  ]
}
```

**Errors**: `404` if no rules exist yet for that context.

## GET /api/v1/recommendations/context/{context_id}

**Query params**: `user_id` (required).

Same as the POST variant with `completed_tasks=[]` — a convenience GET
for clients that just want to poll/refresh the current suggestion for a
context. **Errors**: `404` if no rules exist yet for that context.

---

# Integration Contract

This section is the authoritative contract for integrating this module
into ContextIQ.

## Input event schema

```python
class RawEvent(BaseModel):
    user_id: str
    timestamp: datetime            # UTC
    task_id: str                   # STABLE task type identifier — see note below
    task_category: str             # e.g. "programming", "admin", "study"
    context: str                   # e.g. "department", "library"
    event_type: Literal["START", "PAUSE", "RESUME", "INTERRUPTION", "COMPLETE", "TASK_SWITCH"]
    interruption_source: str | None = None
```

> **Integration note**: `task_id` must be stable across occurrences of
> the same task type (e.g. always `"collect_form"`), not a freshly
> generated unique ID per instance. System A's session reconstruction
> groups by `(user_id, task_id)` and relies on `START`/`COMPLETE` pairs
> to delimit individual sessions even when `task_id` repeats across
> visits; System B's association mining requires `task_id` to repeat
> across transactions to compute meaningful support/confidence/lift.

## Context schema

A context is just a `str` (e.g. `"department"`, `"library"`,
`"home_office"`, `"gym"`). There is no separate context registration
endpoint — contexts are implicitly defined by their appearance in event
data.

## Association schema

```python
class AssociationRule(BaseModel):
    context: str
    antecedents: list[str]     # [] means "unconditional / popularity rule"
    consequents: list[str]
    support: float              # [0, 1]
    confidence: float            # [0, 1]
    lift: float                  # >= 0
    leverage: float | None = None
    conviction: float | None = None
```

## Recommendation schema

```python
class TaskRecommendation(BaseModel):
    task: str
    confidence: float
    support: float
    lift: float
    reason: str

class PrioritizedRecommendation(BaseModel):   # combined-intelligence output
    task: str
    association_confidence: float
    forgetting_probability: float | None
    priority_score: float
    reason: str
```

## API endpoints

| method | path | purpose |
|---|---|---|
| POST | `/api/v1/context/analyze` | run System A + mine associations |
| GET  | `/api/v1/context/{context_id}/associations` | fetch mined rules for a context |
| POST | `/api/v1/recommendations/context` | get ranked recommendations for a visit |
| GET  | `/api/v1/recommendations/context/{context_id}` | poll current recommendations |
| GET  | `/health` | liveness check |

## Python interfaces

For in-process integration (no HTTP hop), import directly:

```python
from ml.context.session_reconstruction import reconstruct_sessions
from ml.context.metrics import compute_session_metrics
from ml.context.pattern_discovery import discover_all_patterns
from ml.context.recovery_cost import estimate_recovery_costs

from ml.associations.transactions import generate_transactions, transactions_to_basket_list
from ml.associations.mining import mine_association_rules
from ml.associations.recommender import (
    recommend_for_context,
    prioritize_recommendations,
    RecommendationQualityConfig,
    DismissalStore,
    ForgettingRiskProvider,      # implement this with the real forgetting model
    MockForgettingRiskProvider,  # for testing only
)
```

To plug in the real forgetting model once it exists, implement:

```python
class RealForgettingRiskProvider(ForgettingRiskProvider):
    def get_forgetting_probability(self, user_id: str, task: str) -> float | None:
        ...  # call the real model here

prioritized = prioritize_recommendations(
    user_id, recommendations, forgetting_provider=RealForgettingRiskProvider()
)
```

No other code in this module needs to change for that integration.

## Explicitly out of scope

- Frontend / UI.
- Any LLM component.
- The forgetting-risk model itself (only the `ForgettingRiskProvider`
  interface and a deterministic mock are provided).
