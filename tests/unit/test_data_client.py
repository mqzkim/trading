"""Unit tests for DataClient using yfinance fallback (no API key required)."""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from core.data.client import DataClient


@pytest.fixture
def mock_yf_ticker():
    """Mock yfinance Ticker to avoid real network calls."""
    n = 300
    np.random.seed(1)
    close = pd.Series(150 + np.cumsum(np.random.randn(n) * 0.5))
    df = pd.DataFrame({
        "Open": close,
        "High": close + 0.5,
        "Low": close - 0.5,
        "Close": close,
        "Volume": pd.Series(np.ones(n) * 1e6),
    })
    df.columns = [c.lower() for c in df.columns]

    ticker_mock = MagicMock()
    ticker_mock.history.return_value = df
    ticker_mock.info = {
        "marketCap": 2_500_000_000_000,
        "trailingPE": 28.5,
        "trailingEps": 6.11,
    }
    return ticker_mock


def test_client_uses_yfinance_when_no_api_key(mock_yf_ticker):
    with patch("core.data.client.yf.Ticker", return_value=mock_yf_ticker):
        client = DataClient(api_key=None)
        df = client.get_price_history("AAPL", days=100)
    assert len(df) == 100
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_get_full_returns_all_keys(mock_yf_ticker):
    with patch("core.data.client.yf.Ticker", return_value=mock_yf_ticker):
        client = DataClient(api_key=None)
        result = client.get_full("AAPL", days=300)
    assert "symbol" in result
    assert "price" in result
    assert "indicators" in result
    assert "fundamentals" in result
    assert result["symbol"] == "AAPL"


def test_indicators_all_present(mock_yf_ticker):
    with patch("core.data.client.yf.Ticker", return_value=mock_yf_ticker):
        client = DataClient(api_key=None)
        result = client.get_full("AAPL", days=300)
    ind = result["indicators"]
    for key in ["ma50", "ma200", "rsi14", "atr21", "adx14", "obv", "macd"]:
        assert key in ind, f"Missing indicator: {key}"


def test_cache_hit_on_second_call(mock_yf_ticker):
    """Second call must use cache and not call yfinance again."""
    with patch("core.data.client.yf.Ticker", return_value=mock_yf_ticker) as mock_cls:
        client = DataClient(api_key=None)
        client.get_price_history("MSFT", days=100)
        client.get_price_history("MSFT", days=100)
    # yf.Ticker should be called only once (cache hit on second)
    assert mock_cls.call_count == 1
