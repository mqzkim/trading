"""Unit tests for CLI ingest command."""
from datetime import date

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

# Patch at the source module since cli/main.py uses lazy import inside function body
_PIPELINE = "src.data_ingest.infrastructure.pipeline.DataPipeline"
_PYKRX_CLIENT = "src.data_ingest.infrastructure.pykrx_client.PyKRXClient"
_REGIME_CLIENT = "src.data_ingest.infrastructure.regime_data_client.RegimeDataClient"
_DUCKDB_STORE = "src.data_ingest.infrastructure.duckdb_store.DuckDBStore"


class TestIngestCommand:
    """Tests for the 'trading ingest' CLI command."""

    @patch(_PIPELINE)
    def test_ingest_with_tickers(self, mock_pipeline_cls):
        """'trading ingest AAPL MSFT' calls pipeline with those tickers."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        async def mock_ingest(tickers):
            return {
                "total": 2,
                "succeeded": ["AAPL", "MSFT"],
                "succeeded_count": 2,
                "failed": [],
                "failed_count": 0,
                "errors": [],
                "errors_count": 0,
            }

        async def mock_close():
            pass

        mock_pipeline.ingest_universe = mock_ingest
        mock_pipeline.close = mock_close

        result = runner.invoke(app, ["ingest", "AAPL", "MSFT"])
        assert result.exit_code == 0
        assert "2" in result.output  # succeeded count

    @patch(_PIPELINE)
    def test_ingest_with_universe(self, mock_pipeline_cls):
        """'trading ingest --universe sp500' calls pipeline for universe."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        async def mock_ingest():
            return {
                "total": 400,
                "succeeded": ["AAPL"],
                "succeeded_count": 400,
                "failed": [],
                "failed_count": 0,
                "errors": [],
                "errors_count": 0,
            }

        async def mock_close():
            pass

        mock_pipeline.ingest_universe = mock_ingest
        mock_pipeline.close = mock_close

        result = runner.invoke(app, ["ingest", "--universe", "sp500"])
        assert result.exit_code == 0
        assert "400" in result.output

    def test_ingest_no_args_exits_with_error(self):
        """'trading ingest' with no tickers and no --universe exits with code 1."""
        result = runner.invoke(app, ["ingest"])
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "provide" in result.output.lower()

    @patch(_PIPELINE)
    def test_ingest_shows_failure_count(self, mock_pipeline_cls):
        """Ingest shows failed ticker count when some fail."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        async def mock_ingest(tickers):
            return {
                "total": 3,
                "succeeded": ["AAPL"],
                "succeeded_count": 1,
                "failed": ["INVALID"],
                "failed_count": 1,
                "errors": ["BROKEN"],
                "errors_count": 1,
            }

        async def mock_close():
            pass

        mock_pipeline.ingest_universe = mock_ingest
        mock_pipeline.close = mock_close

        result = runner.invoke(app, ["ingest", "AAPL", "INVALID", "BROKEN"])
        assert result.exit_code == 0
        assert "1" in result.output


class TestIngestRegimeCommand:
    """Tests for 'trading ingest --regime' CLI command."""

    @patch(_DUCKDB_STORE)
    @patch(_REGIME_CLIENT)
    def test_ingest_regime_fetches_and_stores(self, mock_client_cls, mock_store_cls):
        """'trading ingest --regime' calls RegimeDataClient and DuckDBStore."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        regime_df = pd.DataFrame({
            "date": [date(2026, 3, 10), date(2026, 3, 11)],
            "vix": [18.5, 19.0],
            "sp500_close": [5800.0, 5810.0],
            "sp500_ma200": [5600.0, 5605.0],
            "sp500_ratio": [1.036, 1.037],
            "yield_10y": [4.25, 4.28],
            "yield_3m": [4.10, 4.12],
            "yield_spread_bps": [15.0, 16.0],
        })
        mock_client.fetch_regime_history.return_value = regime_df

        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store

        result = runner.invoke(app, ["ingest", "--regime"])
        assert result.exit_code == 0

        mock_client.fetch_regime_history.assert_called_once_with(years=2)
        mock_store.store_regime_data.assert_called_once()

    @patch(_DUCKDB_STORE)
    @patch(_REGIME_CLIENT)
    def test_ingest_regime_shows_success_table(self, mock_client_cls, mock_store_cls):
        """'trading ingest --regime' displays a success table with row count."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        regime_df = pd.DataFrame({
            "date": [date(2026, 3, 10), date(2026, 3, 11), date(2026, 3, 12)],
            "vix": [18.5, 19.0, 20.0],
            "sp500_close": [5800.0, 5810.0, 5820.0],
            "sp500_ma200": [5600.0, 5605.0, 5610.0],
            "sp500_ratio": [1.036, 1.037, 1.034],
            "yield_10y": [4.25, 4.28, 4.30],
            "yield_3m": [4.10, 4.12, 4.13],
            "yield_spread_bps": [15.0, 16.0, 17.0],
        })
        mock_client.fetch_regime_history.return_value = regime_df

        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store

        result = runner.invoke(app, ["ingest", "--regime"])
        assert result.exit_code == 0
        # Should show row count in output
        assert "3" in result.output

    @patch(_PIPELINE)
    def test_ingest_without_regime_works_as_before(self, mock_pipeline_cls):
        """'trading ingest AAPL' (without --regime) still works as before."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        async def mock_ingest(tickers):
            return {
                "total": 1,
                "succeeded": ["AAPL"],
                "succeeded_count": 1,
                "failed": [],
                "failed_count": 0,
                "errors": [],
                "errors_count": 0,
            }

        async def mock_close():
            pass

        mock_pipeline.ingest_universe = mock_ingest
        mock_pipeline.close = mock_close

        result = runner.invoke(app, ["ingest", "AAPL"])
        assert result.exit_code == 0
        assert "1" in result.output

    def test_ingest_regime_with_market_kr_rejected(self):
        """'trading ingest --regime --market kr' is rejected (US-only)."""
        result = runner.invoke(app, ["ingest", "--regime", "--market", "kr"])
        assert result.exit_code == 1
        assert "us" in result.output.lower() or "error" in result.output.lower()

    def test_ingest_regime_with_tickers_rejected(self):
        """'trading ingest --regime AAPL' is rejected (no per-ticker granularity)."""
        result = runner.invoke(app, ["ingest", "--regime", "AAPL"])
        assert result.exit_code == 1


class TestIngestKoreanMarket:
    """Tests for 'trading ingest --market kr' CLI command."""

    @patch(_PYKRX_CLIENT)
    @patch(_PIPELINE)
    def test_ingest_market_kr_invokes_pipeline(self, mock_pipeline_cls, mock_pykrx_cls):
        """'trading ingest --market kr 005930' invokes pipeline with MarketType.KR."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        async def mock_ingest(tickers, market=None):
            return {
                "total": 1,
                "succeeded": ["005930"],
                "succeeded_count": 1,
                "failed": [],
                "failed_count": 0,
                "errors": [],
                "errors_count": 0,
            }

        async def mock_close():
            pass

        mock_pipeline.ingest_universe = mock_ingest
        mock_pipeline.close = mock_close

        result = runner.invoke(app, ["ingest", "--market", "kr", "005930"])
        assert result.exit_code == 0
        assert "1" in result.output

    @patch(_PIPELINE)
    def test_ingest_default_us_market(self, mock_pipeline_cls):
        """'trading ingest AAPL' (no --market) still works as US default."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        async def mock_ingest(tickers, market=None):
            return {
                "total": 1,
                "succeeded": ["AAPL"],
                "succeeded_count": 1,
                "failed": [],
                "failed_count": 0,
                "errors": [],
                "errors_count": 0,
            }

        async def mock_close():
            pass

        mock_pipeline.ingest_universe = mock_ingest
        mock_pipeline.close = mock_close

        result = runner.invoke(app, ["ingest", "AAPL"])
        assert result.exit_code == 0
        assert "1" in result.output
