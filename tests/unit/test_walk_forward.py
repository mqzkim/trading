"""Tests for walk-forward backtesting."""
import pytest
import pandas as pd
import numpy as np

from core.backtest.walk_forward import WalkForwardResult, run_walk_forward
from core.backtest.metrics import PerformanceMetrics


def _make_ohlcv(prices: list[float], start_date: str = "2020-01-01") -> pd.DataFrame:
    """Helper: build an OHLCV DataFrame from a list of close prices."""
    dates = pd.bdate_range(start=start_date, periods=len(prices))
    df = pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1_000_000] * len(prices),
        },
        index=dates,
    )
    return df


def _make_signals(index: pd.DatetimeIndex, pattern: str = "BUY") -> pd.Series:
    """Helper: build a signals Series. pattern='BUY' means all BUY signals."""
    return pd.Series([pattern] * len(index), index=index)


# --- Tests ---


def test_walk_forward_result_structure():
    """WalkForwardResult has all expected fields."""
    prices = list(range(100, 200))
    df = _make_ohlcv(prices)
    signals = _make_signals(df.index, "BUY")
    result = run_walk_forward(df, signals, n_splits=3)

    assert hasattr(result, "n_splits")
    assert hasattr(result, "splits")
    assert hasattr(result, "oos_metrics")
    assert hasattr(result, "is_metrics")
    assert hasattr(result, "overfitting_score")


def test_walk_forward_splits_count():
    """n_splits=3 produces exactly 3 splits."""
    prices = list(range(100, 200))
    df = _make_ohlcv(prices)
    signals = _make_signals(df.index, "HOLD")
    result = run_walk_forward(df, signals, n_splits=3)

    assert result.n_splits == 3
    assert len(result.splits) == 3


def test_walk_forward_oos_metrics_type():
    """oos_metrics is a PerformanceMetrics instance."""
    prices = list(range(100, 200))
    df = _make_ohlcv(prices)
    signals = _make_signals(df.index, "HOLD")
    result = run_walk_forward(df, signals, n_splits=2)

    assert isinstance(result.oos_metrics, PerformanceMetrics)
    assert isinstance(result.is_metrics, PerformanceMetrics)


def test_walk_forward_no_data_loss():
    """All dates appear in either IS or OOS across all splits."""
    prices = list(range(100, 200))
    df = _make_ohlcv(prices)
    signals = _make_signals(df.index, "HOLD")
    result = run_walk_forward(df, signals, n_splits=5)

    # Gather all train/test ranges from splits -- each split covers a fold,
    # and together the folds cover the entire dataset.
    covered_dates = set()
    for split in result.splits:
        train_start = split["train_start"]
        train_end = split["train_end"]
        test_start = split["test_start"]
        test_end = split["test_end"]
        # Each split has IS data from train_start..train_end
        if train_start and train_end:
            mask = (df.index >= pd.Timestamp(train_start)) & (
                df.index <= pd.Timestamp(train_end)
            )
            covered_dates.update(df.index[mask])
        # And OOS data from test_start..test_end
        if test_start and test_end:
            mask = (df.index >= pd.Timestamp(test_start)) & (
                df.index <= pd.Timestamp(test_end)
            )
            covered_dates.update(df.index[mask])

    assert len(covered_dates) == len(df)


def test_walk_forward_overfitting_score_defined():
    """overfitting_score is a float."""
    prices = list(range(100, 200))
    df = _make_ohlcv(prices)
    signals = _make_signals(df.index, "HOLD")
    result = run_walk_forward(df, signals, n_splits=3)

    assert isinstance(result.overfitting_score, float)


def test_walk_forward_ascending_prices():
    """Ascending prices with BUY signals should yield positive OOS total return."""
    # Steadily rising prices: 100, 101, 102, ...
    prices = [100.0 + i * 0.5 for i in range(200)]
    df = _make_ohlcv(prices)
    # Alternate BUY/SELL to ensure trades complete in each fold
    signal_list = []
    for i in range(len(prices)):
        if i % 20 == 0:
            signal_list.append("BUY")
        elif i % 20 == 10:
            signal_list.append("SELL")
        else:
            signal_list.append("HOLD")
    signals = pd.Series(signal_list, index=df.index)

    result = run_walk_forward(df, signals, n_splits=3, train_ratio=0.7)

    # With ascending prices and BUY-then-SELL, OOS should show positive return
    assert result.oos_metrics.total_return >= 0.0


def test_walk_forward_single_split():
    """n_splits=1 produces exactly 1 split."""
    prices = list(range(100, 200))
    df = _make_ohlcv(prices)
    signals = _make_signals(df.index, "HOLD")
    result = run_walk_forward(df, signals, n_splits=1)

    assert result.n_splits == 1
    assert len(result.splits) == 1


def test_walk_forward_returns_result_type():
    """run_walk_forward returns a WalkForwardResult."""
    prices = list(range(100, 200))
    df = _make_ohlcv(prices)
    signals = _make_signals(df.index, "HOLD")
    result = run_walk_forward(df, signals, n_splits=2)

    assert isinstance(result, WalkForwardResult)
