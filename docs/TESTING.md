# ContextIQ Testing Guide

## Frontend

Run from `frontend/`:

```bash
npm ci
npm test
npx tsc --noEmit
npm run lint
npm run build
```

The tests cover loading, empty, error, malformed-response, timeout, form validation, and API-client behaviour. `frontend/docs/QA_CHECKLIST.md` contains the manual responsive and accessibility checklist.

## Python Services

Run each service independently so local `app` and `tests` packages do not collide:

```bash
cd backend && pytest -q
cd data-engine && pytest -q
cd forgetting-ml && pytest -q
cd context-engine && pytest -q
cd intelligence && pytest -q
```

The repository root also contains a pytest configuration, but separate service runs are the reliable diagnostic command because the services have independent dependencies and test fixtures.

## Pipeline and ML Checks

The ML suite includes feature schema validation, unexpected category handling, missing features, probability range checks, model artifact loading, leakage assertions, chronological splits, and integration training. Full end-to-end training is intentionally more expensive than unit tests because it trains multiple candidate models.

Data-engine tests cover malformed records, session reconstruction, timestamp handling, analytics, and ingestion/API flows. Context-engine tests cover event ordering, empty input, transactions, association rules, recommendation quality, and recovery costs.

## Production Gate

A green frontend build or service unit suite is not sufficient to claim production readiness. Before deployment, also require:

- all service dependencies installed from their lock/requirements files;
- backend tests against a configured PostgreSQL test database;
- complete ML integration training and artifact validation;
- container startup and health checks in a clean environment;
- authenticated end-to-end tests with production identity configuration;
- browser checks at desktop and 375px mobile widths;
- no secrets in source, build output, logs, or client bundles.
