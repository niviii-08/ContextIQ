# ContextIQ Recruiter Demo

## Goal

Show the complete path from behavioural events to analytics, explainable risk, context recommendations, and evidence-backed intelligence in about 10 minutes.

## Sequence

1. Start the stack with [docs/SETUP.md](SETUP.md).
2. Open the frontend at `http://localhost:3000` and show the dashboard's friction, forgetting-risk, interruption, and recovery views.
3. Open `/tasks`, create or inspect a task, and show lifecycle events and context metadata.
4. Open `/predictions` and explain that the probability is produced by a versioned model artifact, not a hardcoded UI score.
5. Open `/context` and show reconstructed sessions, context switches, interruptions, and recovery cost.
6. Open `/recommendations` and explain that suggestions come from context transactions and association confidence, with cooldown/de-duplication rules.
7. Open `/insights` and show how structured evidence is turned into a human-readable insight.
8. Open FastAPI `/docs` for one API and demonstrate a validation error or health response.
9. Show [docs/ARCHITECTURE.md](ARCHITECTURE.md), [docs/DATA_PIPELINE.md](DATA_PIPELINE.md), and the ML methodology to connect the UI to engineering decisions.

## Strong Talking Points

- This is not a todo list: the system studies repeated behaviour over time.
- Features are computed as-of the task timestamp, preventing future leakage.
- PR-AUC, calibration, and chronological evaluation matter more than a flattering accuracy number.
- Recommendations are grounded in mined associations and structured evidence.
- Synthetic data makes the demo reproducible but does not prove real-world validity.

## Resetting the Demo

```bash
docker compose down -v
docker compose up --build
```

Use this only for a local demo because it removes the local database volume.
