"""Data Ingest domain Value Objects.

Immutable VOs for market data: Ticker, OHLCV, FinancialStatement, FilingDate,
DataQualityReport. Each validates invariants on construction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from src.shared.domain import ValueObject

_TICKER_RE = re.compile(r"^[A-Z0-9]{1,10}$")


class MarketType(Enum):
    """Market type for multi-market support."""

    US = "us"
    KR = "kr"


@dataclass(frozen=True)
class Ticker(ValueObject):
    """Stock ticker symbol -- uppercase letters or digits, 1-10 characters."""

    ticker: str

    def _validate(self) -> None:
        if not _TICKER_RE.match(self.ticker):
            raise ValueError(
                f"Ticker must be 1-10 uppercase letters or digits, got '{self.ticker}'"
            )


@dataclass(frozen=True)
class OHLCV(ValueObject):
    """Single OHLCV price bar."""

    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int

    def _validate(self) -> None:
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) must be >= low ({self.low})")
        if self.close <= 0:
            raise ValueError(f"close must be > 0, got {self.close}")
        if self.volume < 0:
            raise ValueError(f"volume must be >= 0, got {self.volume}")


@dataclass(frozen=True)
class FinancialStatement(ValueObject):
    """Financial statement with point-in-time awareness.

    filing_date is the SEC submission date (when data became public).
    period_end is the fiscal quarter/year end date.
    """

    ticker: str
    period_end: date
    filing_date: date
    form_type: str
    revenue: float
    net_income: float
    total_assets: float
    total_liabilities: float
    working_capital: float
    retained_earnings: float
    ebit: float
    operating_cashflow: float
    free_cashflow: float
    current_ratio: float
    debt_to_equity: float
    roa: float
    roe: float

    def _validate(self) -> None:
        if self.filing_date < self.period_end:
            raise ValueError(
                f"filing_date ({self.filing_date}) cannot precede "
                f"period_end ({self.period_end})"
            )
        if self.form_type not in ("10-Q", "10-K"):
            raise ValueError(
                f"form_type must be '10-Q' or '10-K', got '{self.form_type}'"
            )


@dataclass(frozen=True)
class FilingDate(ValueObject):
    """SEC filing date -- must not be in the future (1 day timezone tolerance)."""

    value: date

    def _validate(self) -> None:
        max_allowed = date.today() + timedelta(days=1)
        if self.value > max_allowed:
            raise ValueError(
                f"FilingDate cannot be in the future: {self.value} > {max_allowed}"
            )


@dataclass(frozen=True)
class DataQualityReport(ValueObject):
    """Result of data quality validation for a ticker."""

    ticker: str
    passed: bool
    missing_pct: float
    stale_days: int
    outlier_count: int
    failures: tuple[str, ...]

    def _validate(self) -> None:
        if not 0 <= self.missing_pct <= 100:
            raise ValueError(
                f"missing_pct must be 0-100, got {self.missing_pct}"
            )
