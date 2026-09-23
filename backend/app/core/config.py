"""
Application configuration.

Loads settings from environment variables / .env file using pydantic-settings.
All configuration for ContextIQ backend should flow through this module —
never read os.environ directly elsewhere in the codebase.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _parse_cors_origins(v: Any) -> list[str]:
    """Parse CORS origins robustly: JSON array, comma-separated string, or Python list."""
    if v is None:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
                logger.warning("CORS_ORIGINS parsed as JSON but was not a list; falling back to comma-split")
            except json.JSONDecodeError:
                logger.warning("CORS_ORIGINS looked like JSON but failed to parse; falling back to comma-split")
        return [origin.strip() for origin in s.split(",") if origin.strip()]
    return [str(x).strip() for x in list(v) if str(x).strip()]


class Settings(BaseSettings):
    """Central application settings, sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata ---
    APP_NAME: str = "ContextIQ API"
    APP_ENV: str = Field(default="development")  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Database (Supabase Postgres) ---
    # Standard Postgres connection string, e.g.
    # postgresql+psycopg://postgres:password@db.xxxx.supabase.co:5432/postgres
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres@localhost:5432/contextiq"
    )
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_CONNECT_TIMEOUT_SECONDS: int = 10

    # --- Supabase specific (used by frontend / future auth integration) ---
    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")

    # --- Auth / security ---
    SECRET_KEY: str = Field(default="dev-secret-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # --- CORS ---
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, v):
        return _parse_cors_origins(v)

    # --- ML ---
    ML_MODEL_DIR: str = Field(default="ml/models/artifacts")
    ML_MIN_EVENTS_FOR_TRAINING: int = 50

    # --- Downstream service URLs (internal orchestration, NOT exposed to browsers) ---
    # Inside docker-compose these resolve via service DNS names. Outside compose
    # (e.g. running backend bare-metal) override to localhost:<host_port>.
    FORGETTING_ML_URL: str = Field(default="http://forgetting-ml:8000")
    DATA_ENGINE_URL: str = Field(default="http://data-engine:8000")
    CONTEXT_ENGINE_URL: str = Field(default="http://context-engine:8000")
    INTELLIGENCE_URL: str = Field(default="http://intelligence:8000")

    # --- Downstream service tuning ---
    ORCHESTRATOR_TIMEOUT_SECONDS: int = 8
    ORCHESTRATOR_RETRY_ATTEMPTS: int = 2

    def validate_runtime(self) -> list[str]:
        """Return a list of human-readable configuration warnings (never raises)."""
        warnings: list[str] = []
        if "localhost" in self.DATABASE_URL and self.APP_ENV == "production":
            warnings.append("DATABASE_URL points at localhost in APP_ENV=production")
        if self.SECRET_KEY == "dev-secret-change-me" and self.APP_ENV == "production":
            warnings.append("SECRET_KEY is still the development default in production")
        if self.APP_ENV == "production" and not self.CORS_ORIGINS:
            warnings.append("CORS_ORIGINS is empty in production")
        return warnings


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — import and call this, don't instantiate Settings() directly."""
    s = Settings()
    for w in s.validate_runtime():
        logger.warning("config: %s", w)
    return s
