"""
Application configuration.

All settings are loaded from environment variables (or a local .env file).
The module is designed so the service runs out-of-the-box against a local
SQLite database with zero configuration, while remaining fully compatible
with a Supabase-hosted PostgreSQL database when DATABASE_URL is provided.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Application ---
    app_name: str = "ContextIQ Data Engine"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    # Defaults to a local SQLite file so the module runs with no external
    # dependencies. Point this at a Supabase Postgres URL in production:
    #   postgresql+psycopg2://postgres:<password>@<host>:5432/postgres
    database_url: str = "sqlite:///./contextiq.db"

    # --- Context Session Engine tuning ---
    # Gap (minutes) between two events on the SAME task, beyond which we
    # consider the person to have actually left and returned (a genuine
    # context switch) rather than a brief pause.
    context_switch_gap_minutes: int = 5

    # Idle time (minutes) after which an open context session is
    # automatically closed even if no explicit "completed" event arrives.
    session_idle_timeout_minutes: int = 30

    # --- Synthetic data ---
    synthetic_random_seed: int = 42

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
