import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.ingestion import router as ingestion_router
from app.api.sessions import router as sessions_router
from app.config import get_settings
from app.database.base import Base
from app.database.session import engine
import app.models  # noqa: F401  (ensure all models are registered on Base)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(o) for o in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]


cors_origins = _parse_cors_origins()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up ContextIQ Data Engine...")
    Base.metadata.create_all(bind=engine)
    logger.info("ContextIQ Data Engine started successfully.")
    yield
    logger.info("Shutting down ContextIQ Data Engine...")
    logger.info("ContextIQ Data Engine shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    description=(
        "ContextIQ Data + Behaviour Analytics Module — a standalone service "
        "for behavioural event ingestion, context-session reconstruction, "
        "friction scoring, and ML-ready feature generation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-User-Id"],
)


@app.get("/", tags=["health"])
def root():
    return {
        "service": settings.app_name,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.get(f"{settings.api_v1_prefix}/health", tags=["health"])
def api_v1_health():
    return {"status": "ok"}


app.include_router(ingestion_router, prefix=settings.api_v1_prefix)
app.include_router(sessions_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
