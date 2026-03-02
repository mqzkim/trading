"""Unit tests for core/data/preprocessor.py"""
import pandas as pd
import numpy as np
import pytest
from core.data import preprocessor


@pytest.fixture
def raw_ohlcv():
    n = 100
    np.random.seed(0)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    data = {
        "Open": close,
        "High": close + 0.5,
        "Low": close - 0.5,
        "Close": close,
        "Volume": np.ones(n) * 1_000_000,
    }
    # Insert some NaN
    data["Close"][10] = np.nan
    return pd.DataFrame(data)


def test_columns_lowercased(raw_ohlcv):
    result = preprocessor.preprocess_ohlcv(raw_ohlcv)
    assert all(c.islower() for c in result.columns)


def test_no_nan_after_preprocess(raw_ohlcv):
    result = preprocessor.preprocess_ohlcv(raw_ohlcv)
    assert not result.isnull().any().any()


def test_adj_close_replaces_close():
    df = pd.DataFrame({
        "Open": [100.0], "High": [101.0], "Low": [99.0],
        "Close": [100.0], "Adj_Close": [95.0], "Volume": [1e6],
    })
    result = preprocessor.preprocess_ohlcv(df)
    assert float(result["close"].iloc[0]) == pytest.approx(95.0)
    assert "adj_close" not in result.columns


def test_winsorize_clips_extremes():
    s = pd.Series(list(range(100)) + [10000, -10000])
    result = preprocessor.winsorize(s)
    assert result.max() < 10000
    assert result.min() > -10000


def test_normalize_fundamentals_none_to_nan():
    data = {"pe": None, "eps": "3.5", "nested": {"revenue": None}}
    result = preprocessor.normalize_fundamentals(data)
    assert np.isnan(result["pe"])
    assert result["eps"] == pytest.approx(3.5)
    assert np.isnan(result["nested"]["revenue"])
