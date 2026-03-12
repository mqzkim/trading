"""Unit tests for CLI ingest command."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()


class TestIngestCommand:
    """Tests for the 'trading ingest' CLI command."""

    @patch("cli.main.asyncio")
    @patch("cli.main.DataPipeline")
    def test_ingest_with_tickers(self, mock_pipeline_cls, mock_asyncio):
        """'trading ingest AAPL MSFT' calls pipeline with those tickers."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_asyncio.run.return_value = {
            "total": 2,
            "succeeded": ["AAPL", "MSFT"],
            "succeeded_count": 2,
            "failed": [],
            "failed_count": 0,
            "errors": [],
            "errors_count": 0,
        }

        result = runner.invoke(app, ["ingest", "AAPL", "MSFT"])
        assert result.exit_code == 0
        assert "2" in result.output  # succeeded count
        mock_asyncio.run.assert_called_once()

    @patch("cli.main.asyncio")
    @patch("cli.main.DataPipeline")
    def test_ingest_with_universe(self, mock_pipeline_cls, mock_asyncio):
        """'trading ingest --universe sp500' calls pipeline with universe name."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_asyncio.run.return_value = {
            "total": 400,
            "succeeded": ["AAPL"],
            "succeeded_count": 400,
            "failed": [],
            "failed_count": 0,
            "errors": [],
            "errors_count": 0,
        }

        result = runner.invoke(app, ["ingest", "--universe", "sp500"])
        assert result.exit_code == 0
        assert "400" in result.output

    def test_ingest_no_args_exits_with_error(self):
        """'trading ingest' with no tickers and no --universe exits with code 1."""
        result = runner.invoke(app, ["ingest"])
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "provide" in result.output.lower()

    @patch("cli.main.asyncio")
    @patch("cli.main.DataPipeline")
    def test_ingest_shows_failure_count(self, mock_pipeline_cls, mock_asyncio):
        """Ingest shows failed ticker count when some fail."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_asyncio.run.return_value = {
            "total": 3,
            "succeeded": ["AAPL"],
            "succeeded_count": 1,
            "failed": ["INVALID"],
            "failed_count": 1,
            "errors": ["BROKEN"],
            "errors_count": 1,
        }

        result = runner.invoke(app, ["ingest", "AAPL", "INVALID", "BROKEN"])
        assert result.exit_code == 0
        # Should show some indication of failures
        assert "1" in result.output
