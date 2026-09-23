"""
main.py

FastAPI application entrypoint for the ContextIQ Forgetting Prediction Engine.

Run locally:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Docs available at /docs (Swagger) and /redoc.
"""

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router


def _parse_cors_origins():
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(o) for o in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="ContextIQ Forgetting Prediction Engine",
    description=(
        "Behavioural prediction API estimating P(task will be forgotten | "
        "information available before prediction time). This is a "
        "behavioural prediction system, NOT a psychological or medical "
        "diagnostic system."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router)


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "contextiq-forgetting-ml",
        "status": "running",
        "docs": "/docs",
        "health_url": "/health",
        "predict_endpoint": "/api/v1/predictions/forgetting",
    }


@app.get("/health", tags=["meta"])
def health():
    model_loaded = False
    status = "running"
    reason = None
    try:
        from app.inference import ForgettingPredictor
        ForgettingPredictor.instance()
        model_loaded = True
    except Exception:
        status = "degraded"
        reason = "model unavailable"
    payload = {
        "status": status,
        "service": "contextiq-forgetting-ml",
        "model_loaded": model_loaded,
    }
    if reason is not None:
        payload["reason"] = reason
    return payload
