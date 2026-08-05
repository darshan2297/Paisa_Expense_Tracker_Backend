"""Application settings loaded from environment variables / .env file.

Uses pydantic-settings so configuration is validated at startup rather than
failing lazily deep in application code. `get_settings()` is cached with
`lru_cache` so the environment is parsed exactly once per process and the
same `Settings` instance is reused (and easy to override in tests via
`app.dependency_overrides` or by clearing the cache).
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["dev", "test", "prod"]


class Settings(BaseSettings):
    """Strongly typed application configuration.

    All values may be overridden via environment variables or a `.env` file
    in the working directory. See `.env.example` for the full list with
    sample (non-secret) values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App metadata ---
    APP_NAME: str = "Paisa API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = "dev"

    # --- Database ---
    # Async SQLAlchemy engine URL, must use the asyncpg driver, e.g.
    # postgresql+asyncpg://user:password@host:5432/dbname
    DATABASE_URL: str = "postgresql+asyncpg://paisa:paisa@localhost:5432/paisa"

    # asyncpg does not understand a `sslmode=` query parameter the way psycopg2
    # does, so SSL is enabled via connect_args instead (see core/database.py).
    # Local docker-compose Postgres doesn't need it; hosted Postgres (e.g. Neon)
    # requires it - set true via the environment in production. See
    # docs/DEPLOYMENT_GUIDE.md.
    DATABASE_SSL_REQUIRED: bool = False

    # --- JWT ---
    JWT_SECRET_KEY: str = "change-me-in-prod"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    # --- CORS ---
    # `NoDecode` tells pydantic-settings not to attempt its default JSON
    # decoding of this env var before our validator runs (env vars are
    # plain strings like "http://a,http://b", not JSON arrays) - without it,
    # pydantic-settings raises a SettingsError trying to json.loads() the
    # raw comma-separated string.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # --- Redis / cache ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_DEFAULT_TTL_SECONDS: int = 300

    # --- Celery ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- Rate limiting ---
    # slowapi limit-string syntax, e.g. "100/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # --- Local file storage (receipt slips, backups later) ---
    # Relative to the backend working directory, or an absolute path.
    STORAGE_DIR: str = "storage"

    # --- Email (Resend — F17 reminders) ---
    # Option B (no domain): EMAIL_FROM=Paisa <onboarding@resend.dev>
    # (delivers only to the email on your Resend account).
    # With a verified domain: EMAIL_FROM=Paisa <reminders@yourdomain.com>
    RESEND_API_KEY: str | None = None
    EMAIL_FROM: str | None = None

    # Shared secret for POST /api/v1/internal/reminders/run (GitHub Actions cron).
    CRON_SECRET: str | None = None

    # --- Seed (scripts/seed.py only - there is no public registration
    # endpoint; the single user is created by this script) ---
    SEED_USER_EMAIL: str | None = None
    SEED_USER_PASSWORD: str | None = None
    SEED_USER_NAME: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_csv_origins(cls, value: object) -> object:
        """Allow CORS_ORIGINS to be supplied as a comma-separated string in
        the environment (the common case for .env files / Docker env vars)
        while still accepting a native list when constructed in Python.
        """
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_prod(self) -> bool:
        return self.ENVIRONMENT == "prod"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached Settings instance."""
    return Settings()
