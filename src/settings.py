"""Application settings -- reads from environment variables / .env file.

Uses pydantic-settings for typed, validated configuration.
"""
from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Trading system configuration. All values have safe defaults."""

    # Alpaca broker
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None

    # US capital
    US_CAPITAL: float = 100_000.0  # USD default

    # KIS broker (한국투자증권)
    KIS_APP_KEY: Optional[str] = None
    KIS_APP_SECRET: Optional[str] = None
    KIS_ACCOUNT_NO: Optional[str] = None

    # KR capital
    KR_CAPITAL: float = 10_000_000.0  # KRW default

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton instance -- import this
settings = Settings()
