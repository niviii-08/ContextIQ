# ContextIQ — Behaviour Intelligence + LLM Explanation Module

A standalone Python/FastAPI module that turns structured outputs from
independent ML systems — forgetting prediction, context-switch analysis,
association mining, behavioural metrics — into human-readable insights,
prioritized recommendations, and daily summaries.

**This module performs no ML prediction.** All probabilities, associations,
and metrics come from upstream systems as structured input. The LLM here is
used only as an explanation/communication layer, with hallucination
validation and a deterministic fallback so no invented fact ever reaches the
user.

It runs completely independently of the rest of ContextIQ, using its own
Pydantic input contract and example JSON fixtures.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the standalone example (no API key, no server needed)
python examples/run_example.py

# Run the test suite (no API key required — uses a mock LLM provider)
pytest

# Start the API
cp .env.example .env
uvicorn app.main:app --reload
```

Then visit `http://127.0.0.1:8000/docs` for interactive API docs.

## Project layout

```
contextiq-intelligence/
├── app/
│   ├── main.py              FastAPI app entrypoint
│   ├── config.py            Environment-driven settings
│   ├── schemas.py           Pydantic input/output contracts
│   ├── insight_engine.py    Deterministic pattern detection
│   ├── ranking.py           Priority/ranking engine
│   ├── recommendations.py   "One More Thing?" recommendation engine
│   ├── daily_summary.py     Daily summary builder
│   ├── feedback_store.py    Feedback persistence interface + in-memory impl
│   ├── llm/
│   │   ├── provider.py            LLM provider abstraction (mock/Anthropic/OpenAI)
│   │   └── explanation_service.py LLM explanation generation + hallucination guard
│   └── api/
│       └── routes.py         FastAPI routes
├── examples/
│   ├── sample_bundle.json    Example structured input fixture
│   └── run_example.py        End-to-end run without the API server
├── tests/                    pytest suite (runs without any API key)
├── docs/                     Architecture and contract documentation
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

## LLM provider configuration

Set `LLM_PROVIDER` in `.env`:

| Value       | Requires API key | Notes                                   |
|-------------|-------------------|------------------------------------------|
| `mock`      | No                | Default. Deterministic, offline, used by tests. |
| `anthropic` | Yes (`LLM_API_KEY`) | Requires `pip install anthropic`.      |
| `openai`    | Yes (`LLM_API_KEY`) | Requires `pip install openai`.         |

Adding a new provider means implementing `LLMProvider.complete()` in
`app/llm/provider.py` — nothing else in the module needs to change.

## Safety model for LLM explanations

1. The LLM receives **only** the already-validated structured JSON for a
   single insight/recommendation, with an explicit instruction not to invent
   facts.
2. Every generated explanation is checked against the source payload: any
   number in the output that doesn't trace back to the payload causes the
   output to be **rejected**.
3. On rejection (or provider failure), the module **falls back** to a fully
   deterministic, template-based explanation that interpolates only payload
   values — it cannot hallucinate by construction.

See `docs/LLM_ARCHITECTURE.md` for details.

## Docker

```bash
docker build -t contextiq-intelligence .
docker run -p 8000:8000 --env-file .env contextiq-intelligence
```

## Documentation

- `docs/INTELLIGENCE_ENGINE.md` — insight detection + ranking logic
- `docs/LLM_ARCHITECTURE.md` — LLM abstraction, prompts, validation, fallback
- `docs/API_CONTRACT.md` — full API request/response reference
- `docs/PRIVACY.md` — data-handling boundaries
- `docs/INTEGRATION_CONTRACT.md` — the contract for integrating this module
  into the rest of ContextIQ
