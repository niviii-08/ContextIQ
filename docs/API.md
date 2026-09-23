# ContextIQ API Map

All services expose FastAPI OpenAPI documentation when running. The detailed request and response contracts remain beside each service; this page maps the system for a recruiter or demo operator.

## Core API :8000

Base path: `/api/v1`

- `GET /health`: database-aware health status.
- Users: registration and current-user access.
- Tasks: create, list, retrieve, update, delete.
- Task events: append and list lifecycle events.
- Locations: create, list, update, delete.
- Interruptions: create, list, retrieve, delete.
- Analytics and stored prediction reads.

Detailed implementation: `backend/app/api/v1/`.

## Data Engine :8001

- `GET /health` and `/api/v1/health`.
- Ingestion endpoints for users, locations, tasks, task events, and interruptions.
- Session rebuild and analytics endpoints.

Contract: [data-engine/docs/API.md](../data-engine/docs/API.md).

## Forgetting ML :8002

- `GET /health`: model availability and version.
- `POST /api/v1/predictions/forgetting`: one validated task feature payload.
- `POST /api/v1/predictions/forgetting/batch`: validated batch prediction.

Contract: [forgetting-ml/docs/API_CONTRACT.md](../forgetting-ml/docs/API_CONTRACT.md).

## Context Engine :8003

- `POST /api/v1/context/analyze`: reconstruct sessions, compute metrics, discover patterns, and cache associations.
- `GET /api/v1/context/{context_id}/associations`: retrieve mined rules.
- `POST /api/v1/recommendations/context`: generate context recommendations.

Contract: [context-engine/docs/API_CONTRACT.md](../context-engine/docs/API_CONTRACT.md).

## Intelligence :8004

The intelligence API accepts structured behavioural metrics, prediction evidence, associations, and context outputs. It returns typed insights, recommendations, explanations, or daily summaries. The mock provider is the default demonstration mode; external provider keys remain server-side.

Contracts: [intelligence/docs/INTEGRATION_CONTRACT.md](../intelligence/docs/INTEGRATION_CONTRACT.md) and [intelligence/docs/LLM_ARCHITECTURE.md](../intelligence/docs/LLM_ARCHITECTURE.md).

## Error and Security Conventions

- Invalid UUIDs and malformed bodies are rejected by FastAPI/Pydantic validation.
- Database and integrity failures use safe structured error responses.
- Core queries are user-scoped and expressed through SQLAlchemy.
- Bearer tokens are validated when supplied; development `X-User-Id` identity is not a production authentication mechanism.
- CORS origins are explicitly configured through environment variables.
- Secrets never belong in client-side `NEXT_PUBLIC_*` variables.
