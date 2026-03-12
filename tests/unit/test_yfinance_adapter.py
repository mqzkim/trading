"""Tests for YFinanceClient — wraps core DataClient via async executor."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Sample OHLCV DataFrame matching core DataClient output."""
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [99.0, 100.0, 101.0],
            "close": [104.0, 105.0, 106.0],
            "volume": [1000000, 1100000, 1200000],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="B"),
    )


@pytest.fixture
def sample_fundamentals() -> dict:
    """Sample fundamentals dict matching core DataClient output."""
    return {
        "income": {},
        "balance": {},
        "cashflow": {},
        "highlights": {"market_cap": 3_000_000_000_000, "pe_ratio": 30.5},
        "valuation": {"pb": 45.2},
    }


class TestYFinanceClientInit:
    """Test YFinanceClient initialization."""

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    def test_creates_core_client_on_init(self, mock_core_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        client = YFinanceClient()
        mock_core_cls.assert_called_once()

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    def test_accepts_optional_semaphore(self, mock_core_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        sem = asyncio.Semaphore(3)
        client = YFinanceClient(semaphore=sem)
        assert client._semaphore is sem

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    def test_no_semaphore_by_default(self, mock_core_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        client = YFinanceClient()
        assert client._semaphore is None


class TestYFinanceClientFetchOHLCV:
    """Test async OHLCV fetching."""

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_ohlcv_returns_dataframe(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        client = YFinanceClient()
        result = await client.fetch_ohlcv("AAPL", days=756)

        pd.testing.assert_frame_equal(result, sample_ohlcv_df)
        mock_instance.get_price_history.assert_called_once_with("AAPL", 756)

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_ohlcv_default_days(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        client = YFinanceClient()
        await client.fetch_ohlcv("AAPL")

        mock_instance.get_price_history.assert_called_once_with("AAPL", 756)

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_ohlcv_with_semaphore(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        sem = asyncio.Semaphore(1)
        client = YFinanceClient(semaphore=sem)
        result = await client.fetch_ohlcv("AAPL")

        pd.testing.assert_frame_equal(result, sample_ohlcv_df)

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_ohlcv_has_expected_columns(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        client = YFinanceClient()
        result = await client.fetch_ohlcv("AAPL")

        assert set(result.columns) == {"open", "high", "low", "close", "volume"}


class TestYFinanceClientFetchFundamentals:
    """Test async fundamentals fetching."""

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_fundamentals_returns_dict(
        self, mock_core_cls: MagicMock, sample_fundamentals: dict
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_fundamentals.return_value = sample_fundamentals

        client = YFinanceClient()
        result = await client.fetch_fundamentals("AAPL")

        assert result == sample_fundamentals
        mock_instance.get_fundamentals.assert_called_once_with("AAPL")

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_fundamentals_with_semaphore(
        self, mock_core_cls: MagicMock, sample_fundamentals: dict
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_fundamentals.return_value = sample_fundamentals

        sem = asyncio.Semaphore(2)
        client = YFinanceClient(semaphore=sem)
        result = await client.fetch_fundamentals("AAPL")

        assert result == sample_fundamentals


class TestYFinanceAdjustedCloseValidation:
    """Validate that auto_adjust=True returns adjusted OHLCV without Adj Close column.

    DATA-01 validation: yfinance 0.2.28+ with auto_adjust=True means the
    Close column IS the adjusted close. No separate "Adj Close" column exists.
    """

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_ohlcv_has_no_adj_close_column(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        client = YFinanceClient()
        result = await client.fetch_ohlcv("AAPL")

        assert "Adj Close" not in result.columns
        assert "adj_close" not in result.columns

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_ohlcv_columns_are_adjusted_lowercase(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        client = YFinanceClient()
        result = await client.fetch_ohlcv("AAPL")

        assert set(result.columns) == {"open", "high", "low", "close", "volume"}

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_ohlcv_close_has_no_nans(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        client = YFinanceClient()
        result = await client.fetch_ohlcv("AAPL")

        assert result["close"].isna().sum() == 0

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_core_client_receives_ticker_and_days(
        self, mock_core_cls: MagicMock, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.return_value = sample_ohlcv_df

        client = YFinanceClient()
        await client.fetch_ohlcv("MSFT", days=500)

        mock_instance.get_price_history.assert_called_once_with("MSFT", 500)


class TestYFinanceClientErrorHandling:
    """Test error propagation from core DataClient."""

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_ohlcv_propagates_error(self, mock_core_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_price_history.side_effect = Exception("API error")

        client = YFinanceClient()
        with pytest.raises(Exception, match="API error"):
            await client.fetch_ohlcv("INVALID")

    @patch("src.data_ingest.infrastructure.yfinance_client.CoreDataClient")
    async def test_fetch_fundamentals_propagates_error(self, mock_core_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.yfinance_client import YFinanceClient

        mock_instance = mock_core_cls.return_value
        mock_instance.get_fundamentals.side_effect = ValueError("Not found")

        client = YFinanceClient()
        with pytest.raises(ValueError, match="Not found"):
            await client.fetch_fundamentals("INVALID")
