"""
config.py
=========
Centralized configuration, sourced from environment variables. See
.env.example for the full list.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")


settings = Settings()
