"""Backtest Application Layer -- Commands."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class RunBacktestCommand:
    """Run a single backtest for a symbol."""

    symbol: str
    ohlcv_df: pd.DataFrame = field(repr=False)
    signals_series: pd.Series = field(repr=False)
    initial_capital: float = 100_000.0


@dataclass(frozen=True)
class RunWalkForwardCommand:
    """Run walk-forward validation for a symbol."""

    symbol: str
    ohlcv_df: pd.DataFrame = field(repr=False)
    signals_series: pd.Series = field(repr=False)
    n_splits: int = 5
    train_ratio: float = 0.7
    initial_capital: float = 100_000.0
