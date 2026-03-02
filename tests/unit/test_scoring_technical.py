"""Unit tests for core/scoring/technical.py"""
import pandas as pd
import numpy as np
import pytest
from core.scoring.technical import compute_technical_score
from core.data.indicators import compute_all


@pytest.fixture
def bullish_df():
    """Trending up OHLCV with 300 days."""
    np.random.seed(10)
    n = 300
    close = pd.Series(100 + np.cumsum(np.random.randn(n) * 0.3 + 0.2))
    high = close + 0.5
    low = close - 0.5
    volume = pd.Series(np.random.randint(1_000_000, 5_000_000, n), dtype=float)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume})


@pytest.fixture
def bearish_df():
    """Trending down OHLCV."""
    np.random.seed(11)
    n = 300
    close = pd.Series(200 - np.cumsum(np.random.randn(n) * 0.3 + 0.2))
    close = close.clip(lower=10)
    high = close + 0.5
    low = close - 0.5
    volume = pd.Series(np.random.randint(1_000_000, 5_000_000, n), dtype=float)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume})


def test_bullish_score_higher(bullish_df, bearish_df):
    ind_bull = compute_all(bullish_df)
    ind_bear = compute_all(bearish_df)
    bull_result = compute_technical_score(bullish_df, ind_bull)
    bear_result = compute_technical_score(bearish_df, ind_bear)
    assert bull_result["technical_score"] > bear_result["technical_score"]


def test_score_range(bullish_df):
    ind = compute_all(bullish_df)
    result = compute_technical_score(bullish_df, ind)
    assert 0 <= result["technical_score"] <= 100
    assert 0 <= result["trend_score"] <= 100
    assert 0 <= result["momentum_score"] <= 100
    assert 0 <= result["volume_score"] <= 100


def test_required_keys(bullish_df):
    ind = compute_all(bullish_df)
    result = compute_technical_score(bullish_df, ind)
    for key in ["trend_score", "momentum_score", "volume_score", "technical_score", "above_ma200"]:
        assert key in result


def test_reproducibility(bullish_df):
    ind = compute_all(bullish_df)
    r1 = compute_technical_score(bullish_df, ind)
    r2 = compute_technical_score(bullish_df, ind)
    assert r1["technical_score"] == r2["technical_score"]
