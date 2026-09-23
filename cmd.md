# ContextIQ — Command Reference (cmd.md)

This file contains every command needed to set up, run, develop, test, and
maintain the full ContextIQ stack.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start — Docker (All Services)](#2-quick-start--docker-all-services)
3. [Manual Setup — No Docker](#3-manual-setup--no-docker)
   - 3.1 [Database Setup](#31-database-setup)
   - 3.2 [Backend (Core API)](#32-backend-core-api--port-8000)
   - 3.3 [Data Engine](#33-data-engine--port-8001)
   - 3.4 [Forgetting ML](#34-forgetting-ml-service--port-8002)
   - 3.5 [Context Engine](#35-context-engine--port-8003)
   - 3.6 [Intelligence Service](#36-intelligence-service--port-8004)
   - 3.7 [Frontend](#37-frontend--port-3000)
4. [Seed & Synthetic Data](#4-seed--synthetic-data)
5. [ML Pipeline](#5-ml-pipeline)
6. [Testing](#6-testing)
7. [Database Migrations](#7-database-migrations)
8. [Docker — Individual Services](#8-docker--individual-services)
9. [Useful API calls](#9-useful-api-calls)
10. [Environment Variables](#10-environment-variables)

---

## 1. Prerequisites

| Tool | Minimum version | Install |
|---|---|---|
| Python | 3.11+ | https://python.org |
| Node.js | 20+ | https://nodejs.org |
| npm | 10+ | Bundled with Node.js |
| Docker Desktop | latest | https://docs.docker.com/get-docker/ |
| PostgreSQL | 15+ | https://www.postgresql.org/download/ (only for manual setup) |
| Git | any | https://git-scm.com |

Verify your setup:
```bash
python --version
node --version
npm --version
docker --version
docker compose version
psql --version
```

---

## 2. Quick Start — Docker (All Services)

**The simplest way to run the entire stack with one command.**

```bash
# Step 1 — Enter the project root
cd contextiq-complete

# Step 2 — Copy environment variables (edit if needed)
cp .env.example .env
# On Windows:
copy .env.example .env

# Step 3 — Build all Docker images and start all services
docker compose up --build

# Step 4 — (New terminal) Apply database migrations
docker compose exec backend alembic upgrade head

# Step 5 — Seed the database with 2 synthetic users (90 days of data)
docker compose exec backend python ../scripts/generate_synthetic_data.py --mode db --users 2

# Step 6 — (Optional) Seed small hand-written demo data instead
docker compose exec db psql -U postgres -d contextiq -f /dev/stdin < database/seeds/seed_demo.sql
```

### Service URLs after startup

| Service | URL | Notes |
|---|---|---|
| Frontend | http://localhost:3000 | Main UI |
| Core API | http://localhost:8000/docs | FastAPI Swagger UI |
| Data Engine | http://localhost:8001/docs | Analytics API |
| Forgetting ML | http://localhost:8002/docs | Prediction API |
| Context Engine | http://localhost:8003/docs | Association mining API |
| Intelligence | http://localhost:8004/docs | LLM insight API |

### Useful Docker commands

```bash
# Start all services (without rebuilding)
docker compose up

# Start in background (detached)
docker compose up -d

# View logs for all services
docker compose logs -f

# View logs for a specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f forgetting-ml

# Stop all services
docker compose down

# Stop and remove volumes (reset database)
docker compose down -v

# Rebuild a single service after code changes
docker compose up --build backend
docker compose up --build frontend

# Open a shell in a running container
docker compose exec backend bash
docker compose exec frontend sh
docker compose exec db psql -U postgres -d contextiq

# Check container status
docker compose ps
```

---

## 3. Manual Setup — No Docker

Run each service in its own terminal window.

### 3.1 Database Setup

```bash
# Create the contextiq database
createdb contextiq
psql -d contextiq -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

# Create a separate test database (for running tests)
createdb contextiq_test
psql -d contextiq_test -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

### 3.2 Backend (Core API) — port 8000

```bash
cd contextiq-complete/backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp ../.env.example .env
# Edit .env: set DATABASE_URL to your local Postgres connection string

# Apply database migrations
alembic upgrade head

# Start the backend API (with hot reload)
uvicorn app.main:app --reload --port 8000

# Verify it is running:
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok", "database":{"connected":true}, ...}
```

### 3.3 Data Engine — port 8001

```bash
cd contextiq-complete/data-engine

# Create virtual environment
python -m venv .venv

# Activate
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Default DATABASE_URL uses SQLite (no server needed)

# Initialize the database
python scripts/init_db.py

# Start the data engine API
uvicorn app.main:app --reload --port 8001

# Verify:
curl http://localhost:8001/docs
```

### 3.4 Forgetting ML Service — port 8002

```bash
cd contextiq-complete/forgetting-ml

# Create virtual environment
python -m venv .venv

# Activate
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate the training dataset first (creates datasets/tasks_raw.csv)
python -m ml.data.generate_dataset

# Train all models and generate evaluation report
# (creates artifacts/model_bundle.joblib, metrics.json, plots)
python -m ml.training.train

# Start the prediction API
uvicorn app.main:app --reload --port 8002

# Verify:
curl http://localhost:8002/docs
```

### 3.5 Context Engine — port 8003

```bash
cd contextiq-complete/context-engine

# Create virtual environment
python -m venv .venv

# Activate
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate synthetic data for the context engine
python scripts/generate_synthetic_data.py

# Run the full demo pipeline (writes results to artifacts/)
python scripts/run_pipeline.py

# Start the context engine API
uvicorn app.main:app --reload --port 8003

# Verify:
curl http://localhost:8003/docs
```

### 3.6 Intelligence Service — port 8004

```bash
cd contextiq-complete/intelligence

# Create virtual environment
python -m venv .venv

# Activate
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Default LLM_PROVIDER=mock (no API key needed)
# Set LLM_PROVIDER=anthropic or openai and add LLM_API_KEY if you have one

# Run the standalone example (no API key, no server needed)
python examples/run_example.py

# Start the intelligence API
uvicorn app.main:app --reload --port 8004

# Verify:
curl http://localhost:8004/docs
```

### 3.7 Frontend — port 3000

```bash
cd contextiq-complete/frontend

# Install Node.js dependencies
npm install

# Copy and configure environment variables
cp .env.example .env.local
# Edit .env.local:
#   NEXT_PUBLIC_USE_MOCK=false  (to use live backends)
#   NEXT_PUBLIC_USE_MOCK=true   (to use mock data, no backends needed)

# Start the development server (hot reload)
npm run dev

# Open: http://localhost:3000
```

---

## 4. Seed & Synthetic Data

```bash
# Option A — Realistic synthetic data (recommended, 90 days x N users)
# Write into Postgres database:
python scripts/generate_synthetic_data.py --mode db --users 2

# Write as CSVs into data/ (no DB needed, for ML pipeline):
python scripts/generate_synthetic_data.py --mode csv --users 2

# Write both:
python scripts/generate_synthetic_data.py --mode both --users 2

# Option B — Small hand-written demo seed (fast, good for API exploration)
psql "$DATABASE_URL" -f database/seeds/seed_demo.sql
# Demo user ID: 11111111-1111-1111-1111-111111111111

# Generate synthetic data for the data-engine (standalone SQLite)
cd data-engine
python scripts/generate_synthetic_data.py --users 50 --days 60 --seed 42 --db

# Generate dataset for the forgetting-ml service
cd forgetting-ml
python -m ml.data.generate_dataset

# Generate dataset for the context engine
cd context-engine
python scripts/generate_synthetic_data.py
```

---

## 5. ML Pipeline

### Forgetting Prediction Model

```bash
cd contextiq-complete/forgetting-ml

# 1. Generate synthetic training dataset
python -m ml.data.generate_dataset
# Output: datasets/tasks_raw.csv (~49,800 rows), datasets/users.csv

# 2. Train all candidate models + select the best
python -m ml.training.train
# Output: artifacts/model_bundle.joblib, metrics.json, evaluation plots

# 3. Batch-score tasks from a CSV file
python scripts/batch_score.py --input datasets/tasks_raw.csv --output artifacts/scores.csv
```

### Context Engine Pipeline

```bash
cd contextiq-complete/context-engine

# Generate synthetic events
python scripts/generate_synthetic_data.py

# Run the full end-to-end pipeline (context switching + association mining)
python scripts/run_pipeline.py
# Writes results to artifacts/
```

### Core ML Pipeline (from prompt1)

```bash
cd contextiq-complete

# Activate the scripts venv (or reuse backend venv)
python -m venv .venv-scripts
# Linux/Mac:
source .venv-scripts/bin/activate
# Windows:
.venv-scripts\Scripts\activate

pip install -r backend/requirements.txt

# Build feature file for forgetting risk
python -m ml.features.build_features --data-dir data --out data/features_forget_risk.csv

# Train XGBoost forget-risk classifier
python -m ml.models.train_forget_risk

# Run FP-Growth association rule mining
python -m ml.features.association_mining --data-dir data
```

---

## 6. Testing

### Run all tests

```bash
cd contextiq-complete

# Backend + ML tests (requires PostgreSQL contextiq_test database)
pytest tests/backend tests/ml -v

# Or just:
pytest
```

### Per-service tests

```bash
# Backend only
pytest tests/backend -v

# ML pipeline only (no DB required)
pytest tests/ml -v

# Data engine (uses SQLite, no server needed)
cd data-engine && pytest tests/ -v

# Forgetting ML
cd forgetting-ml && pytest tests/ -v

# Context engine (46 tests)
cd context-engine && pytest -q

# Intelligence service (no API key required -- uses mock LLM)
cd intelligence && pytest -v

# Frontend (Vitest)
cd frontend && npm run test

# Frontend in watch mode
cd frontend && npm run test:watch
```

### Code quality

```bash
# Frontend linting
cd frontend && npm run lint

# Frontend TypeScript check (standalone, no build)
cd frontend && npx tsc --noEmit
```

---

## 7. Database Migrations

Migrations are managed with Alembic from the `backend/` directory.

```bash
cd contextiq-complete/backend
# (with venv activated)

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back all migrations
alembic downgrade base

# Generate a new migration after changing SQLAlchemy models
alembic revision --autogenerate -m "describe your change here"

# View migration history
alembic history --verbose

# View current revision
alembic current
```

---

## 8. Docker — Individual Services

Build and run each service as an independent Docker container.

### Core Backend

```bash
cd contextiq-complete/backend
docker build -t contextiq-backend .
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg://postgres:<password>@host.docker.internal:5432/contextiq" \
  -e SECRET_KEY="dev-secret" \
  contextiq-backend
```

### Data Engine

```bash
cd contextiq-complete/data-engine
docker build -t contextiq-data-engine .
docker run -p 8001:8000 contextiq-data-engine
```

### Forgetting ML

```bash
cd contextiq-complete/forgetting-ml

# Build (train inside the image at build time)
docker build -t contextiq-forgetting-ml .

# Train model, then run API (volume mounts artifacts so they persist)
docker run --rm -v $(pwd)/artifacts:/app/artifacts contextiq-forgetting-ml \
  sh -c "python -m ml.data.generate_dataset && python -m ml.training.train"

# Serve the trained model
docker run -p 8002:8000 -v $(pwd)/artifacts:/app/artifacts contextiq-forgetting-ml
```

### Context Engine

```bash
cd contextiq-complete/context-engine
docker build -t contextiq-context-engine .
docker run -p 8003:8000 contextiq-context-engine
```

### Intelligence Service

```bash
cd contextiq-complete/intelligence
docker build -t contextiq-intelligence .

# With mock LLM (no API key needed):
docker run -p 8004:8000 --env-file .env contextiq-intelligence

# With a real LLM provider:
docker run -p 8004:8000 \
  -e LLM_PROVIDER=anthropic \
  -e LLM_API_KEY="<provider-api-key>" \
  contextiq-intelligence
```

### Frontend

```bash
cd contextiq-complete/frontend
docker build -t contextiq-frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL="http://localhost:8000/api/v1" \
  -e NEXT_PUBLIC_USE_MOCK="false" \
  contextiq-frontend
```

---

## 9. Useful API calls

Test the services are alive with these quick curl commands.

```bash
# Core backend health check
curl http://localhost:8000/api/v1/health

# Core backend — list users
curl http://localhost:8000/api/v1/users

# Core backend — list tasks for demo user
curl -H "X-User-Id: 11111111-1111-1111-1111-111111111111" \
     http://localhost:8000/api/v1/tasks

# Data engine — get analytics for a user
curl http://localhost:8001/api/v1/analytics/user/11111111-1111-1111-1111-111111111111

# Data engine — compute friction score
curl http://localhost:8001/api/v1/analytics/friction-score/11111111-1111-1111-1111-111111111111

# Forgetting ML — predict forget risk for a task
curl -X POST http://localhost:8002/api/v1/predict \
  -H "Content-Type: application/json" \
  -d "{\"task_id\": \"abc123\", \"user_id\": \"11111111-1111-1111-1111-111111111111\"}"

# Context engine — get recommendations
curl http://localhost:8003/api/v1/recommendations?location=department

# Intelligence — generate insights (POST with a bundle payload)
curl -X POST http://localhost:8004/api/v1/insights \
  -H "Content-Type: application/json" \
  -d @intelligence/examples/sample_bundle.json

# Frontend — open in browser
start http://localhost:3000
```

---

## 10. Environment Variables

Copy `.env.example` to `.env` and configure the variables below.

```bash
cp .env.example .env
# Windows:
copy .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:<password>@localhost:5432/contextiq` | Postgres connection for core backend |
| `SECRET_KEY` | `dev-secret-change-me` | JWT / session secret (change in production) |
| `APP_ENV` | `development` | `development` or `production` |
| `DEBUG` | `true` | Enable debug logging |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins |
| `DATA_ENGINE_DATABASE_URL` | `sqlite:///./contextiq.db` | Data engine DB (SQLite ok for dev) |
| `LLM_PROVIDER` | `mock` | `mock`, `anthropic`, or `openai` |
| `LLM_API_KEY` | (empty) | API key for non-mock LLM providers |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model name for the LLM provider |
| `NEXT_PUBLIC_USE_MOCK` | `false` | `true` = frontend uses mock data only |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | Core backend URL for frontend |
| `NEXT_PUBLIC_DEV_USER_ID` | `11111111-1111-1111-1111-111111111111` | Dev user ID for auth-less mode |
| `SUPABASE_URL` | (empty) | Optional: Supabase project URL |
| `SUPABASE_ANON_KEY` | (empty) | Optional: Supabase anon key |
| `ML_MODEL_DIR` | `ml/models/artifacts` | Directory where trained ML models are saved |
