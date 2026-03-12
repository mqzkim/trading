"""Unit tests for CLI backtest command."""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()


class TestBacktestCommand:
    """Tests for the 'trading backtest' CLI command."""

    @patch("cli.main.CoreBacktestAdapter")
    @patch("cli.main.BacktestValidationService")
    def test_backtest_with_dates(self, mock_validation_cls, mock_adapter_cls):
        """'trading backtest AAPL --start 2020-01-01 --end 2024-01-01' runs backtest."""
        mock_handler = MagicMock()
        mock_ok = MagicMock()
        mock_ok.value = {
            "symbol": "AAPL",
            "performance_report": {
                "total_return": 0.45,
                "sharpe_ratio": 1.2,
                "max_drawdown": -0.15,
                "win_rate": 0.55,
                "profit_factor": 1.8,
            },
        }
        mock_ok.is_ok = True
        mock_handler.run_backtest.return_value = mock_ok

        with patch("cli.main.BacktestHandler", return_value=mock_handler):
            with patch("cli.main._fetch_ohlcv_for_backtest") as mock_fetch:
                import pandas as pd
                mock_fetch.return_value = (
                    pd.DataFrame({"close": [100, 101, 102]}),
                    pd.Series([1, 0, 1]),
                )
                result = runner.invoke(
                    app, ["backtest", "AAPL", "--start", "2020-01-01", "--end", "2024-01-01"]
                )

        assert result.exit_code == 0
        assert "AAPL" in result.output

    @patch("cli.main.CoreBacktestAdapter")
    @patch("cli.main.BacktestValidationService")
    def test_backtest_default_dates(self, mock_validation_cls, mock_adapter_cls):
        """'trading backtest AAPL' uses default dates."""
        mock_handler = MagicMock()
        mock_ok = MagicMock()
        mock_ok.value = {
            "symbol": "AAPL",
            "performance_report": {
                "total_return": 0.30,
                "sharpe_ratio": 1.0,
                "max_drawdown": -0.20,
                "win_rate": 0.50,
                "profit_factor": 1.5,
            },
        }
        mock_ok.is_ok = True
        mock_handler.run_backtest.return_value = mock_ok

        with patch("cli.main.BacktestHandler", return_value=mock_handler):
            with patch("cli.main._fetch_ohlcv_for_backtest") as mock_fetch:
                import pandas as pd
                mock_fetch.return_value = (
                    pd.DataFrame({"close": [100, 101, 102]}),
                    pd.Series([1, 0, 1]),
                )
                result = runner.invoke(app, ["backtest", "AAPL"])

        assert result.exit_code == 0
        assert "AAPL" in result.output
