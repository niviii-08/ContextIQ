"""
FastAPI application entrypoint for the Context Intelligence Module.

Run locally with:
    uvicorn app.main:app --reload

See docs/API_CONTRACT.md for the full endpoint contract.
"""

from __future__ import annotations

import json
import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.context import router as context_router
from app.api.recommendations import router as recommendations_router


def _parse_cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    if not raw:
        return ["http://localhost:3000"]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="ContextIQ - Context Intelligence Module",
    description=(
        "Standalone context-switching intelligence (System A) and "
        "'One More Thing' contextual task discovery (System B) engine, "
        "for later integration into ContextIQ."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-User-Id"],
)

app.include_router(context_router, prefix="/api/v1/context", tags=["context"])
app.include_router(recommendations_router, prefix="/api/v1/recommendations", tags=["recommendations"])


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "context-engine",
        "status": "running",
        "docs": "/docs",
        "health_url": "/health",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
