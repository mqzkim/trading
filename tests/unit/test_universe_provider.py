"""Tests for UniverseProvider — S&P 500+400 ticker universe management."""
from __future__ import annotations

import time
from unittest.mock import patch

import pandas as pd
import pytest


@pytest.fixture
def sp500_html_df() -> pd.DataFrame:
    """Sample S&P 500 Wikipedia table."""
    return pd.DataFrame(
        {
            "Symbol": ["AAPL", "MSFT", "JPM", "NEE", "GOOGL"],
            "Security": [
                "Apple Inc.",
                "Microsoft Corp.",
                "JPMorgan Chase",
                "NextEra Energy",
                "Alphabet Inc.",
            ],
            "GICS Sector": [
                "Information Technology",
                "Information Technology",
                "Financials",
                "Utilities",
                "Communication Services",
            ],
            "GICS Sub-Industry": [
                "Technology Hardware",
                "Systems Software",
                "Diversified Banks",
                "Electric Utilities",
                "Interactive Media",
            ],
        }
    )


@pytest.fixture
def sp400_html_df() -> pd.DataFrame:
    """Sample S&P 400 Wikipedia table."""
    return pd.DataFrame(
        {
            "Symbol": ["DECK", "WSM", "WBS"],
            "Company": ["Deckers Outdoor", "Williams-Sonoma", "Webster Financial"],
            "GICS Sector": [
                "Consumer Discretionary",
                "Consumer Discretionary",
                "Financials",
            ],
            "GICS Sub-Industry": [
                "Footwear",
                "Home Furnishings",
                "Regional Banks",
            ],
        }
    )


class TestUniverseProviderSP500:
    """Test S&P 500 ticker fetching."""

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_get_sp500_returns_dataframe(
        self, mock_read_html: object, sp500_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.return_value = [sp500_html_df]

        provider = UniverseProvider()
        result = provider.get_sp500_tickers()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_sp500_normalizes_column_names(
        self, mock_read_html: object, sp500_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.return_value = [sp500_html_df]

        provider = UniverseProvider()
        result = provider.get_sp500_tickers()

        expected_cols = {"ticker", "name", "sector", "sub_industry"}
        assert set(result.columns) == expected_cols


class TestUniverseProviderSP400:
    """Test S&P 400 ticker fetching."""

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_get_sp400_returns_dataframe(
        self, mock_read_html: object, sp400_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.return_value = [sp400_html_df]

        provider = UniverseProvider()
        result = provider.get_sp400_tickers()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_sp400_normalizes_column_names(
        self, mock_read_html: object, sp400_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.return_value = [sp400_html_df]

        provider = UniverseProvider()
        result = provider.get_sp400_tickers()

        expected_cols = {"ticker", "name", "sector", "sub_industry"}
        assert set(result.columns) == expected_cols

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_sp400_fallback_on_error(self, mock_read_html: object) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.side_effect = Exception("Network error")

        provider = UniverseProvider()
        result = provider.get_sp400_tickers()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestUniverseProviderGetUniverse:
    """Test combined universe with sector filtering."""

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_get_universe_excludes_financials_and_utilities(
        self, mock_read_html: object, sp500_html_df: pd.DataFrame, sp400_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.side_effect = [[sp500_html_df], [sp400_html_df]]

        provider = UniverseProvider()
        result = provider.get_universe()

        sectors = result["sector"].unique().tolist()
        assert "Financials" not in sectors
        assert "Utilities" not in sectors

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_get_universe_combines_sp500_and_sp400(
        self, mock_read_html: object, sp500_html_df: pd.DataFrame, sp400_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.side_effect = [[sp500_html_df], [sp400_html_df]]

        provider = UniverseProvider()
        result = provider.get_universe()

        # sp500: AAPL, MSFT, GOOGL pass (JPM=Financials, NEE=Utilities excluded)
        # sp400: DECK, WSM pass (WBS=Financials excluded)
        assert len(result) == 5  # AAPL + MSFT + GOOGL + DECK + WSM

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_get_universe_deduplicates(
        self, mock_read_html: object
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        # Same ticker in both indices
        df_500 = pd.DataFrame(
            {
                "Symbol": ["AAPL"],
                "Security": ["Apple Inc."],
                "GICS Sector": ["Information Technology"],
                "GICS Sub-Industry": ["Technology Hardware"],
            }
        )
        df_400 = pd.DataFrame(
            {
                "Symbol": ["AAPL"],
                "Company": ["Apple Inc."],
                "GICS Sector": ["Information Technology"],
                "GICS Sub-Industry": ["Technology Hardware"],
            }
        )
        mock_read_html.side_effect = [[df_500], [df_400]]

        provider = UniverseProvider()
        result = provider.get_universe()

        assert len(result) == 1  # No duplicates

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_get_universe_caches_result(
        self, mock_read_html: object, sp500_html_df: pd.DataFrame, sp400_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.side_effect = [[sp500_html_df], [sp400_html_df]]

        provider = UniverseProvider()
        result1 = provider.get_universe()
        result2 = provider.get_universe()

        # read_html should only be called once (cached)
        assert mock_read_html.call_count == 2  # once for sp500, once for sp400

        pd.testing.assert_frame_equal(result1, result2)


class TestUniverseProviderGetSectors:
    """Test sector listing."""

    @patch("src.data_ingest.infrastructure.universe_provider.pd.read_html")
    def test_get_sectors_returns_unique_sectors(
        self, mock_read_html: object, sp500_html_df: pd.DataFrame, sp400_html_df: pd.DataFrame
    ) -> None:
        from src.data_ingest.infrastructure.universe_provider import UniverseProvider

        mock_read_html.side_effect = [[sp500_html_df], [sp400_html_df]]

        provider = UniverseProvider()
        sectors = provider.get_sectors()

        assert isinstance(sectors, list)
        assert "Financials" not in sectors
        assert "Utilities" not in sectors
        assert "Information Technology" in sectors
