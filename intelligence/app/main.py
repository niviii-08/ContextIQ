"""
main.py
=======
FastAPI application entrypoint for the ContextIQ Behaviour Intelligence +
LLM Explanation module.

Run locally:
    uvicorn app.main:app --reload

This module is fully standalone: it does not import anything from the rest
of the ContextIQ codebase and only depends on the structured input schemas
defined in app/schemas.py.
"""

from __future__ import annotations

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.llm.provider import get_provider


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if not raw:
        return ["http://localhost:3000"]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _check_llm_available() -> tuple[bool, str]:
    try:
        get_provider(settings.llm_provider, settings.llm_api_key or None)
        return True, settings.llm_provider
    except ValueError:
        return False, settings.llm_provider


cors_origins = _parse_cors_origins()
llm_available, llm_provider = _check_llm_available()

app = FastAPI(
    title="ContextIQ Behaviour Intelligence + LLM Explanation Module",
    description=(
        "Transforms structured ML outputs (forgetting prediction, context-switch "
        "analysis, association mining, behavioural metrics) into insights, "
        "prioritized recommendations, daily summaries, and human-readable "
        "explanations. Performs no ML prediction itself."
    ),
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/")
def root():
    return {
        "service": "ContextIQ Intelligence Service",
        "status": "ok",
        "version": settings.app_version,
        "docs": "/docs",
        "llm_provider": llm_provider,
        "llm_available": llm_available,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": llm_provider,
        "llm_available": llm_available,
        "version": settings.app_version,
    }


app.include_router(router)
