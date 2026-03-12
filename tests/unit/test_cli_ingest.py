"""Unit tests for CLI ingest command."""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

# Patch at the source module since cli/main.py uses lazy import inside function body
_PIPELINE = "src.data_ingest.infrastructure.pipeline.DataPipeline"


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
