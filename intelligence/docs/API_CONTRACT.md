# API Contract

Base path: none (routes are absolute, e.g. `/api/v1/...`).
Content type: `application/json` throughout.

## POST /api/v1/insights/generate

**Request** (`GenerateInsightsRequest`):
```json
{
  "bundle": { "...": "IntelligenceBundle, see schemas.py" },
  "use_llm_explanations": true
}
```

**Response** (`GenerateInsightsResponse`):
```json
{
  "insights": [
    {
      "type": "frequent_forgetting",
      "title": "Frequent forgetting: Lab Record",
      "description": "...",
      "evidence": [{"field": "...", "value": "...", "source": "..."}],
      "priority": "HIGH",
      "confidence": 0.82,
      "source": "forgetting_prediction",
      "rank_score": 0.71,
      "rank_position": 1
    }
  ]
}
```

## POST /api/v1/insights/daily

**Request** (`DailySummaryRequest`): same shape as above.

**Response** (`DailySummary`):
```json
{
  "biggest_friction": "Repeated context switching",
  "highest_risk_task": "Lab Record",
  "highest_risk_probability": 0.82,
  "context_reminder": "Department tasks are frequently forgotten",
  "estimated_avoidable_friction_minutes": 18.0,
  "top_insights": ["..."],
  "generated_at": "2026-08-18T09:00:00Z"
}
```

## POST /api/v1/recommendations/generate

**Request** (`RecommendationsRequest`):
```json
{
  "bundle": { "...": "IntelligenceBundle" },
  "max_recommendations": 5
}
```

**Response** (`RecommendationsResponse`):
```json
{
  "recommendations": [
    {
      "context": "Department",
      "associated_task": "Collect Form",
      "association_confidence": 0.78,
      "forgetting_probability": 0.81,
      "headline": "One More Thing?",
      "explanation": "You're often in the context 'Department'. ...",
      "priority": "HIGH",
      "rank_score": 0.79
    }
  ]
}
```

## POST /api/v1/feedback

**Request** (`FeedbackRequest`):
```json
{
  "entry": {
    "user_id": "user_123",
    "target_type": "insight",
    "target_id": "insight_1",
    "feedback": "useful",
    "comment": "optional"
  }
}
```

**Response** (`FeedbackAck`):
```json
{ "status": "stored", "stored_id": "..." }
```

Valid `feedback` values: `useful`, `not_useful`, `incorrect`, `dismissed`.

## GET /api/v1/health

**Response** (`HealthResponse`):
```json
{ "status": "ok", "llm_provider": "mock", "version": "0.1.0" }
```

## Errors

- `422 Unprocessable Entity` — request body fails Pydantic validation
  (e.g. `probability` outside `[0, 1]`). FastAPI's default validation error
  body is returned.
- `500 Internal Server Error` — misconfigured LLM provider (e.g.
  `LLM_PROVIDER=anthropic` with no `LLM_API_KEY` set).

Full interactive schema is also available at `/docs` (Swagger UI) and
`/openapi.json` when the server is running.
