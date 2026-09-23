# ContextIQ Data Engine

The **Data + Behaviour Analytics Module** for ContextIQ — a privacy-conscious
Personal Behaviour Intelligence System.

This module is a **complete, standalone** service. It has no dependency on
any other ContextIQ codebase and can be run, tested, and integrated on its
own. It is responsible for:

- Ingesting behavioural events (tasks, task lifecycle events, interruptions, locations)
- Reconstructing behavioural sessions from raw events (the **Context Session Engine**)
- Computing behavioural analytics (completion/forgetting rates, interruption
  patterns, context-switching patterns, and more)
- Computing an experimental, transparent **Behavioural Friction Score**
- Generating **ML-ready features** for a downstream, independently-built
  forgetting-prediction / recommendation model
- Generating a realistic **synthetic dataset** for development and testing

It deliberately does **not** implement: a forgetting-prediction ML model,
association-rule mining, an LLM explanation layer, or a recommendation
engine. Those are separate modules — see [INTEGRATION CONTRACT](#integration-contract)
below for exactly how they should consume this module's output.

---

## Quickstart

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

By default `DATABASE_URL` in `.env` points at a local SQLite file
(`sqlite:///./contextiq.db`) — **no database server required** to get
started. To use Supabase/PostgreSQL instead, edit `.env`:

```
DATABASE_URL=postgresql+psycopg2://postgres:<password>@db.<project>.supabase.co:5432/postgres
```

### 2. Initialize the database

```bash
python scripts/init_db.py
```

(Tables are also auto-created on API startup for convenience, but running
this explicitly is recommended for scripted/CI setups.)

### 3. Generate synthetic data (optional but recommended)

```bash
python scripts/generate_synthetic_data.py --users 50 --days 60 --seed 42 --db
```

This writes CSVs to `data/synthetic/` **and** loads the same dataset into
your configured database. Drop `--db` to only write CSVs (e.g. for
inspection or use in a separate ML pipeline without touching the DB).

### 4. Start the API server

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`, with interactive docs
at `http://localhost:8000/docs`.

### 5. Run tests

```bash
pytest tests/ -v
```

All 60+ tests use an isolated, file-backed SQLite database per test — no
shared state, no need for a running Postgres instance to run the suite.

### Docker (with bundled Postgres)

```bash
docker compose up --build
```

This starts the API on `:8000` and a local Postgres 16 instance on `:5432`.
Swap `DATABASE_URL` in `docker-compose.yml` for a Supabase connection
string to skip the bundled `db` service entirely.

---

## Project Structure

```
contextiq-data-engine/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── config.py            # Settings (env-var driven)
│   ├── database/            # Engine/session + cross-DB UUID type
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── api/                  # FastAPI routers (ingestion, sessions, analytics)
│   ├── services/              # Context Session Engine
│   ├── analytics/            # Behavioural metrics + friction score
│   └── utils/                 # ML feature engine
├── data/
│   ├── synthetic/            # Generated synthetic CSVs
│   └── generated/            # Scratch space for other generated artifacts
├── scripts/                   # init_db.py, generate_synthetic_data.py
├── tests/                     # pytest suite
├── docs/                      # Architecture / analytics / feature / API docs
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Documentation

- [`docs/DATA_ARCHITECTURE.md`](docs/DATA_ARCHITECTURE.md) — schema design, ERD description, indexing strategy
- [`docs/BEHAVIOUR_ANALYTICS.md`](docs/BEHAVIOUR_ANALYTICS.md) — every metric formula, the session-reconstruction algorithm, and the friction score
- [`docs/FEATURE_ENGINE.md`](docs/FEATURE_ENGINE.md) — ML feature interfaces and the temporal-leakage-prevention design
- [`docs/API.md`](docs/API.md) — every endpoint with example requests/responses

---

## INTEGRATION CONTRACT

This is the contract another developer (or another Claude session) needs to
build ContextIQ's ML / recommendation / LLM layers on top of this module.

### Database tables (read access assumed for downstream modules)

| Table               | Purpose                                                             |
|---------------------|----------------------------------------------------------------------|
| `users`              | One row per person using the system                                  |
| `locations`          | Named contexts/locations a user works from                           |
| `tasks`               | Denormalized current state of every task                             |
| `task_events`         | **Authoritative**, append-only log of every task lifecycle event      |
| `interruptions`       | Logged interruptions, optionally tied to a task and/or location       |
| `context_sessions`    | Derived/reconstructed behavioural sessions (see Context Session Engine) |
| `behaviour_metrics`   | Optional materialized/cached analytics rollups                        |

Full column-level schema: see `docs/DATA_ARCHITECTURE.md`.

**Important:** `tasks.status` is denormalized for fast reads. Any module
doing historical/causal analysis (e.g. a forgetting-prediction model)
should prefer `task_events` as the source of truth for *when* something
happened.

### API endpoints (base path `/api/v1`)

**Ingestion:**
- `POST /users`, `GET /users/{id}`
- `POST /locations`
- `POST /tasks`, `GET /tasks/{id}`
- `POST /task-events`
- `POST /interruptions`

**Session engine:**
- `POST /context-sessions/rebuild?user_id={id}` — recompute all
  `context_sessions` for a user from raw events. **Call this after
  ingesting new events, before reading `/analytics/context` or
  `/analytics/friction`,** so those reflect the latest activity.

**Analytics (all take `user_id` + optional `period_days`, default 30):**
- `GET /analytics/overview`
- `GET /analytics/tasks`
- `GET /analytics/interruptions`
- `GET /analytics/context`
- `GET /analytics/friction`

Full request/response JSON examples: see `docs/API.md`.

### Feature-engine interfaces (Python, `app/utils/features.py`)

These are the functions a downstream ML module should import and call
directly (this module is a Python package, so `from app.utils.features
import generate_task_features` works if this repo is installed/vendored
alongside the ML module — or the same logic can be re-implemented from
this documented contract if the ML module lives in a fully separate
deployment):

```python
generate_task_features(
    *, task_row: dict, tasks_df: pd.DataFrame, events_df: pd.DataFrame,
    interruptions_df: pd.DataFrame, as_of: datetime,
) -> dict
# Returns: previous_forgetting_count, previous_completion_count,
# completion_rate, category_forgetting_rate, location_forgetting_rate,
# weekday_forgetting_rate, hour_forgetting_rate, task_frequency,
# days_since_last_similar_task, deadline_distance_hours, priority,
# tasks_today, interruptions_today, recent_context_switches,
# average_interruption_duration_seconds

generate_user_features(
    *, tasks_df, interruptions_df, sessions_df, as_of: datetime,
) -> dict
# Returns: completion_rate, forgetting_rate, total_tasks,
# total_interruptions, average_session_duration_seconds,
# average_interruption_duration_seconds, total_context_switches

generate_context_features(
    *, location_id, tasks_df, interruptions_df, as_of: datetime,
) -> dict
# Returns: location_task_count, location_forgetting_rate,
# location_interruption_count, location_average_interruption_duration_seconds
```

**Critical contract guarantee:** every feature is computed using only data
with a timestamp strictly before `as_of`. A training pipeline should call
`generate_task_features(..., as_of=task.created_at)` for each historical
task to reproduce exactly the information horizon a live prediction would
have. See `docs/FEATURE_ENGINE.md` for the full leakage-prevention design.

### Event formats

**TaskEvent** (`task_events` table / `POST /task-events` body):
```json
{
  "user_id": "uuid",
  "task_id": "uuid",
  "event_type": "created | started | paused | resumed | completed | forgotten | cancelled",
  "event_time": "ISO-8601 datetime",
  "location_id": "uuid | null",
  "event_metadata": { "any": "free-form JSON" }
}
```

**Interruption** (`interruptions` table / `POST /interruptions` body):
```json
{
  "user_id": "uuid",
  "task_id": "uuid | null",
  "location_id": "uuid | null",
  "interruption_type": "phone | social_media | message | call | search | person | food | other",
  "start_time": "ISO-8601 datetime",
  "end_time": "ISO-8601 datetime | null",
  "duration_seconds": "int | null (derived from start/end if omitted)"
}
```

---

## Notes for integrators

- All timestamps are treated as UTC throughout the module. Note that
  **SQLite does not round-trip timezone-aware datetimes** (a well-known
  SQLAlchemy/SQLite limitation) — values written as tz-aware come back
  naive when read. The module handles this transparently internally, but
  if you query the SQLite database directly, treat every timestamp as
  UTC regardless of whether it carries a `+00:00` suffix.
- `context_sessions` are a **derived/cache table** — they are fully
  rebuilt (not incrementally patched) by `rebuild_sessions_for_user`, so
  it's always safe to re-run after new events arrive.
- The Friction Score is explicitly experimental. Do not present
  `overall_score` to end users without the accompanying disclaimer
  returned in the API response's `label` field.
