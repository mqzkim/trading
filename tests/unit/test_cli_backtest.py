"""Unit tests for CLI backtest command."""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

# Patch at source modules since cli/main.py uses lazy import inside function body
_BACKTEST_HANDLER = "src.backtest.application.handlers.BacktestHandler"
_ADAPTER = "src.backtest.infrastructure.core_backtest_adapter.CoreBacktestAdapter"
_VALIDATION = "src.backtest.domain.services.BacktestValidationService"
_FETCH = "cli.main._fetch_ohlcv_for_backtest"


class TestBacktestCommand:
    """Tests for the 'trading backtest' CLI command."""

    @patch(_FETCH)
    @patch(_BACKTEST_HANDLER)
    @patch(_VALIDATION)
    @patch(_ADAPTER)
    def test_backtest_with_dates(
        self, mock_adapter_cls, mock_validation_cls, mock_handler_cls, mock_fetch
    ):
        """'trading backtest AAPL --start 2020-01-01 --end 2024-01-01' runs backtest."""
        import pandas as pd

        mock_fetch.return_value = (
            pd.DataFrame({"close": [100, 101, 102]}),
            pd.Series([1, 0, 1]),
        )

        mock_handler = MagicMock()
        mock_result = MagicMock()
        mock_result.is_ok = True
        mock_result.value = {
            "symbol": "AAPL",
            "performance_report": {
                "total_return": 0.45,
                "sharpe_ratio": 1.2,
                "max_drawdown": -0.15,
                "win_rate": 0.55,
                "profit_factor": 1.8,
            },
        }
        mock_handler.run_backtest.return_value = mock_result
        mock_handler_cls.return_value = mock_handler

        result = runner.invoke(
            app, ["backtest", "AAPL", "--start", "2020-01-01", "--end", "2024-01-01"]
        )

        assert result.exit_code == 0
        assert "AAPL" in result.output

    @patch(_FETCH)
    @patch(_BACKTEST_HANDLER)
    @patch(_VALIDATION)
    @patch(_ADAPTER)
    def test_backtest_default_dates(
        self, mock_adapter_cls, mock_validation_cls, mock_handler_cls, mock_fetch
    ):
        """'trading backtest AAPL' uses default dates."""
        import pandas as pd

        mock_fetch.return_value = (
            pd.DataFrame({"close": [100, 101, 102]}),
            pd.Series([1, 0, 1]),
        )

        mock_handler = MagicMock()
        mock_result = MagicMock()
        mock_result.is_ok = True
        mock_result.value = {
            "symbol": "AAPL",
            "performance_report": {
                "total_return": 0.30,
                "sharpe_ratio": 1.0,
                "max_drawdown": -0.20,
                "win_rate": 0.50,
                "profit_factor": 1.5,
            },
        }
        mock_handler.run_backtest.return_value = mock_result
        mock_handler_cls.return_value = mock_handler

        result = runner.invoke(app, ["backtest", "AAPL"])

        assert result.exit_code == 0
        assert "AAPL" in result.output
