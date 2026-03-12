"""Unit tests for PyKRX Korean market data adapter."""
from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import patch

import pandas as pd

from src.data_ingest.infrastructure.pykrx_client import PyKRXClient


class TestPyKRXClientFetchOHLCV:
    """Tests for PyKRXClient.fetch_ohlcv."""

    @patch("src.data_ingest.infrastructure.pykrx_client.stock")
    def test_returns_english_column_names(self, mock_stock) -> None:
        """fetch_ohlcv returns DataFrame with English column names, not Korean."""
        korean_df = pd.DataFrame(
            {
                "\uc2dc\uac00": [70000.0],
                "\uace0\uac00": [71000.0],
                "\uc800\uac00": [69000.0],
                "\uc885\uac00": [70500.0],
                "\uac70\ub798\ub7c9": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2024, 3, 1)]),
        )
        mock_stock.get_market_ohlcv.return_value = korean_df

        client = PyKRXClient()
        result = asyncio.run(client.fetch_ohlcv("005930", days=30))

        assert list(result.columns) == ["open", "high", "low", "close", "volume"]

    @patch("src.data_ingest.infrastructure.pykrx_client.stock")
    def test_formats_dates_as_yyyymmdd(self, mock_stock) -> None:
        """fetch_ohlcv passes dates as YYYYMMDD strings (no dashes) to pykrx."""
        mock_stock.get_market_ohlcv.return_value = pd.DataFrame(
            columns=["\uc2dc\uac00", "\uace0\uac00", "\uc800\uac00", "\uc885\uac00", "\uac70\ub798\ub7c9"]
        )

        client = PyKRXClient()
        asyncio.run(client.fetch_ohlcv("005930", days=30))

        call_args = mock_stock.get_market_ohlcv.call_args
        start_date = call_args[0][0]
        end_date = call_args[0][1]

        # Dates must be YYYYMMDD format (no dashes)
        assert len(start_date) == 8
        assert "-" not in start_date
        assert len(end_date) == 8
        assert "-" not in end_date

    @patch("src.data_ingest.infrastructure.pykrx_client.stock")
    def test_handles_empty_dataframe(self, mock_stock) -> None:
        """fetch_ohlcv returns empty DataFrame gracefully when pykrx returns no data."""
        mock_stock.get_market_ohlcv.return_value = pd.DataFrame()

        client = PyKRXClient()
        result = asyncio.run(client.fetch_ohlcv("999999", days=30))

        assert result.empty

    @patch("src.data_ingest.infrastructure.pykrx_client.stock")
    @patch("src.data_ingest.infrastructure.pykrx_client.time")
    def test_enforces_rate_limit(self, mock_time, mock_stock) -> None:
        """fetch_ohlcv enforces 1-second delay between pykrx calls."""
        korean_df = pd.DataFrame(
            {
                "\uc2dc\uac00": [70000.0],
                "\uace0\uac00": [71000.0],
                "\uc800\uac00": [69000.0],
                "\uc885\uac00": [70500.0],
                "\uac70\ub798\ub7c9": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2024, 3, 1)]),
        )
        mock_stock.get_market_ohlcv.return_value = korean_df

        client = PyKRXClient()
        asyncio.run(client.fetch_ohlcv("005930", days=30))

        mock_time.sleep.assert_called_once_with(1.0)


class TestPyKRXClientFetchFundamentals:
    """Tests for PyKRXClient.fetch_fundamentals."""

    @patch("src.data_ingest.infrastructure.pykrx_client.stock")
    def test_returns_lowercase_columns(self, mock_stock) -> None:
        """fetch_fundamentals returns DataFrame with lowercase English column names."""
        fund_df = pd.DataFrame(
            {
                "BPS": [50000.0],
                "PER": [12.5],
                "PBR": [1.2],
                "EPS": [5000.0],
                "DIV": [1.8],
                "DPS": [1000.0],
            },
            index=pd.DatetimeIndex([datetime(2024, 3, 1)]),
        )
        mock_stock.get_market_fundamental.return_value = fund_df

        client = PyKRXClient()
        result = asyncio.run(client.fetch_fundamentals("005930", days=30))

        expected_cols = ["bps", "per", "pbr", "eps", "div_yield", "dps"]
        assert list(result.columns) == expected_cols

    @patch("src.data_ingest.infrastructure.pykrx_client.stock")
    def test_handles_empty_fundamentals(self, mock_stock) -> None:
        """fetch_fundamentals returns empty DataFrame when no data available."""
        mock_stock.get_market_fundamental.return_value = pd.DataFrame()

        client = PyKRXClient()
        result = asyncio.run(client.fetch_fundamentals("999999", days=30))

        assert result.empty

    @patch("src.data_ingest.infrastructure.pykrx_client.stock")
    @patch("src.data_ingest.infrastructure.pykrx_client.time")
    def test_enforces_rate_limit(self, mock_time, mock_stock) -> None:
        """fetch_fundamentals enforces 1-second delay."""
        fund_df = pd.DataFrame(
            {
                "BPS": [50000.0],
                "PER": [12.5],
                "PBR": [1.2],
                "EPS": [5000.0],
                "DIV": [1.8],
                "DPS": [1000.0],
            },
            index=pd.DatetimeIndex([datetime(2024, 3, 1)]),
        )
        mock_stock.get_market_fundamental.return_value = fund_df

        client = PyKRXClient()
        asyncio.run(client.fetch_fundamentals("005930", days=30))

        mock_time.sleep.assert_called_once_with(1.0)
