"""Application settings -- reads from environment variables / .env file.

Uses pydantic-settings for typed, validated configuration.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Trading system configuration. All values have safe defaults."""

    # Execution mode (paper default, explicit setting required for live)
    EXECUTION_MODE: Literal["paper", "live"] = "paper"

    # Alpaca paper trading
    ALPACA_PAPER_KEY: Optional[str] = None
    ALPACA_PAPER_SECRET: Optional[str] = None

    # Alpaca live trading
    ALPACA_LIVE_KEY: Optional[str] = None
    ALPACA_LIVE_SECRET: Optional[str] = None

    # Legacy (backward compat, mapped to paper)
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

    # Pipeline scheduler
    SLACK_WEBHOOK_URL: Optional[str] = None
    PIPELINE_SCHEDULE_HOUR: int = 16
    PIPELINE_SCHEDULE_MINUTE: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton instance -- import this
settings = Settings()
