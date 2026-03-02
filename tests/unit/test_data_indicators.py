"""Unit tests for core/data/indicators.py"""
import pandas as pd
import numpy as np
import pytest
from core.data import indicators


@pytest.fixture
def ohlcv():
    """Generate synthetic OHLCV data with 300 rows."""
    np.random.seed(42)
    n = 300
    close = pd.Series(100 + np.cumsum(np.random.randn(n) * 0.5))
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    volume = pd.Series(np.random.randint(1_000_000, 5_000_000, n), dtype=float)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume})


def test_ma_length(ohlcv):
    result = indicators.ma(ohlcv["close"], 50)
    assert len(result) == len(ohlcv)
    assert result.iloc[:49].isna().all()
    assert not pd.isna(result.iloc[-1])


def test_rsi_range(ohlcv):
    result = indicators.rsi(ohlcv["close"], 14)
    valid = result.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_atr_positive(ohlcv):
    result = indicators.atr(ohlcv, 21)
    valid = result.dropna()
    assert (valid > 0).all()


def test_obv_cumulative(ohlcv):
    result = indicators.obv(ohlcv)
    assert len(result) == len(ohlcv)


def test_macd_columns(ohlcv):
    result = indicators.macd(ohlcv["close"])
    assert set(result.columns) == {"macd", "signal", "histogram"}


def test_compute_all_keys(ohlcv):
    result = indicators.compute_all(ohlcv)
    expected = {"ma50", "ma200", "rsi14", "atr21", "adx14", "obv", "macd", "macd_signal", "macd_histogram"}
    assert set(result.keys()) == expected


def test_indicator_reproducibility(ohlcv):
    """Same input must produce identical output (deterministic)."""
    r1 = indicators.compute_all(ohlcv)
    r2 = indicators.compute_all(ohlcv)
    for key in r1:
        pd.testing.assert_series_equal(r1[key], r2[key])
