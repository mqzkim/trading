"""Backtest domain -- Value Objects.

Invariants:
  BacktestConfig: symbol non-empty, initial_capital > 0
  WalkForwardConfig: n_splits >= 2, 0 < train_ratio < 1, capital > 0, symbol non-empty
  PerformanceReport: all 8 metrics (no validation -- computed values)
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import ValueObject


@dataclass(frozen=True)
class BacktestConfig(ValueObject):
    """Configuration for a single backtest run."""

    symbol: str
    initial_capital: float = 100_000.0

    def _validate(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol must be non-empty")
        if self.initial_capital <= 0:
            raise ValueError(f"initial_capital must be > 0, got {self.initial_capital}")


@dataclass(frozen=True)
class WalkForwardConfig(ValueObject):
    """Configuration for walk-forward validation."""

    symbol: str
    n_splits: int = 5
    train_ratio: float = 0.7
    initial_capital: float = 100_000.0

    def _validate(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol must be non-empty")
        if self.n_splits < 2:
            raise ValueError(f"n_splits must be >= 2, got {self.n_splits}")
        if not (0 < self.train_ratio < 1):
            raise ValueError(f"train_ratio must be in (0, 1), got {self.train_ratio}")
        if self.initial_capital <= 0:
            raise ValueError(f"initial_capital must be > 0, got {self.initial_capital}")


@dataclass(frozen=True)
class PerformanceReport(ValueObject):
    """Performance metrics including profit factor (8 fields total).

    No validation needed -- all values are computed by domain services.
    """

    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_return: float
    num_trades: int
    avg_return_per_trade: float
    profit_factor: float

    def _validate(self) -> None:
        pass  # computed values -- no invariants to enforce
