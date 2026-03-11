"""Data Ingest domain events.

Events published when data ingestion succeeds or quality checks fail.
Used for cross-context communication via async event bus.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import DomainEvent


@dataclass(frozen=True, kw_only=True)
class DataIngestedEvent(DomainEvent):
    """Raised when data for a ticker has been successfully ingested and stored."""

    ticker: str
    ohlcv_rows: int
    financial_quarters: int


@dataclass(frozen=True, kw_only=True)
class QualityCheckFailedEvent(DomainEvent):
    """Raised when data quality validation fails for a ticker."""

    ticker: str
    failures: tuple[str, ...]
