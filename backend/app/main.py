"""
ContextIQ API — application entry point.

Run locally with:
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers

settings = get_settings()

if settings.APP_ENV == "production" and settings.SECRET_KEY == "dev-secret-change-me":
    raise RuntimeError("SECRET_KEY must be explicitly configured in production.")

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "ContextIQ — a privacy-conscious Personal Behaviour Intelligence System. "
        "Learns behavioural patterns around forgetting, context switching, and "
        "recurring 'one more thing' tasks from explicitly-logged user events."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-User-Id"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }
