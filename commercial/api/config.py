"""API-specific settings -- JWT, rate limiting, and related configuration.

Loads from environment variables / .env file via pydantic-settings.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    """Commercial API configuration. All values have safe defaults for dev."""

    # JWT
    JWT_SECRET_KEY: str = "dev-only-change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_HOURS: int = 24

    # Rate limits per tier
    RATE_LIMIT_FREE: str = "10/minute"
    RATE_LIMIT_BASIC: str = "30/minute"
    RATE_LIMIT_PRO: str = "100/minute"

    # Dashboard internal secret (BFF -> FastAPI)
    DASHBOARD_SECRET: str = "dashboard-internal"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton instance
api_settings = ApiSettings()
