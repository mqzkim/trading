"""Unit tests for RegimeDataClient -- regime indicator fetching."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.data_ingest.infrastructure.regime_data_client import RegimeDataClient


def _make_history(n_days: int, start_date: date, close_vals: list[float] | None = None) -> pd.DataFrame:
    """Create a realistic yfinance-style DataFrame for mocking."""
    dates = pd.bdate_range(start=start_date, periods=n_days)
    if close_vals is None:
        close_vals = [100.0 + i * 0.1 for i in range(n_days)]
    return pd.DataFrame(
        {
            "Open": close_vals,
            "High": [v + 1.0 for v in close_vals],
            "Low": [v - 1.0 for v in close_vals],
            "Close": close_vals,
            "Volume": [1_000_000] * n_days,
        },
        index=dates,
    )


class TestRegimeDataClientSnapshot:
    """Tests for fetch_regime_snapshot."""

    @patch("src.data_ingest.infrastructure.regime_data_client.yf")
    def test_snapshot_returns_all_keys(self, mock_yf: MagicMock) -> None:
        """Snapshot must contain all 10 regime data keys (including adx and yield_spread)."""
        sp500_hist = _make_history(250, date(2024, 1, 2))
        vix_hist = _make_history(5, date(2026, 3, 7), [18.5] * 5)
        tnx_hist = _make_history(5, date(2026, 3, 7), [4.25] * 5)
        irx_hist = _make_history(5, date(2026, 3, 7), [4.10] * 5)

        def make_ticker(symbol: str) -> MagicMock:
            t = MagicMock()
            histories = {
                "^GSPC": sp500_hist,
                "^VIX": vix_hist,
                "^TNX": tnx_hist,
                "^IRX": irx_hist,
            }
            t.history.return_value = histories[symbol]
            return t

        mock_yf.Ticker.side_effect = make_ticker

        client = RegimeDataClient()
        result = client.fetch_regime_snapshot()

        expected_keys = {
            "date", "vix", "sp500_close", "sp500_ma200",
            "sp500_ratio", "yield_10y", "yield_3m", "yield_spread_bps",
            "adx", "yield_spread",
        }
        assert set(result.keys()) == expected_keys

    @patch("src.data_ingest.infrastructure.regime_data_client.yf")
    def test_snapshot_computes_yield_spread(self, mock_yf: MagicMock) -> None:
        """yield_spread_bps = (yield_10y - yield_3m) * 100."""
        sp500_hist = _make_history(250, date(2024, 1, 2))
        vix_hist = _make_history(5, date(2026, 3, 7), [20.0] * 5)
        tnx_hist = _make_history(5, date(2026, 3, 7), [4.50] * 5)
        irx_hist = _make_history(5, date(2026, 3, 7), [4.00] * 5)

        def make_ticker(symbol: str) -> MagicMock:
            t = MagicMock()
            histories = {
                "^GSPC": sp500_hist,
                "^VIX": vix_hist,
                "^TNX": tnx_hist,
                "^IRX": irx_hist,
            }
            t.history.return_value = histories[symbol]
            return t

        mock_yf.Ticker.side_effect = make_ticker

        client = RegimeDataClient()
        result = client.fetch_regime_snapshot()

        assert result["yield_10y"] == pytest.approx(4.50)
        assert result["yield_3m"] == pytest.approx(4.00)
        assert result["yield_spread_bps"] == pytest.approx(50.0)


class TestRegimeDataClientHistory:
    """Tests for fetch_regime_history."""

    @patch("src.data_ingest.infrastructure.regime_data_client.yf")
    def test_history_returns_dataframe_with_all_columns(self, mock_yf: MagicMock) -> None:
        """History DataFrame must have all regime columns plus date."""
        n_days = 504  # ~2 years of trading days
        sp500_hist = _make_history(n_days, date(2024, 1, 2))
        vix_hist = _make_history(n_days, date(2024, 1, 2), [18.0 + i * 0.01 for i in range(n_days)])
        tnx_hist = _make_history(n_days, date(2024, 1, 2), [4.25 + i * 0.001 for i in range(n_days)])
        irx_hist = _make_history(n_days, date(2024, 1, 2), [4.10 + i * 0.001 for i in range(n_days)])

        def make_ticker(symbol: str) -> MagicMock:
            t = MagicMock()
            histories = {
                "^GSPC": sp500_hist,
                "^VIX": vix_hist,
                "^TNX": tnx_hist,
                "^IRX": irx_hist,
            }
            t.history.return_value = histories[symbol]
            return t

        mock_yf.Ticker.side_effect = make_ticker

        client = RegimeDataClient()
        df = client.fetch_regime_history(years=2)

        expected_cols = {
            "date", "vix", "sp500_close", "sp500_ma200",
            "sp500_ratio", "yield_10y", "yield_3m", "yield_spread_bps",
        }
        assert expected_cols == set(df.columns)
        assert len(df) > 0

    @patch("src.data_ingest.infrastructure.regime_data_client.yf")
    def test_history_fetches_sufficient_data_for_200ma(self, mock_yf: MagicMock) -> None:
        """2y of history provides enough data for 200-day MA calculation."""
        n_days = 504
        sp500_hist = _make_history(n_days, date(2024, 1, 2))
        vix_hist = _make_history(n_days, date(2024, 1, 2))
        tnx_hist = _make_history(n_days, date(2024, 1, 2))
        irx_hist = _make_history(n_days, date(2024, 1, 2))

        def make_ticker(symbol: str) -> MagicMock:
            t = MagicMock()
            histories = {
                "^GSPC": sp500_hist,
                "^VIX": vix_hist,
                "^TNX": tnx_hist,
                "^IRX": irx_hist,
            }
            t.history.return_value = histories[symbol]
            return t

        mock_yf.Ticker.side_effect = make_ticker

        client = RegimeDataClient()
        df = client.fetch_regime_history(years=2)

        # After dropping NaN rows from 200MA, should still have many rows
        valid_rows = df.dropna(subset=["sp500_ma200"])
        assert len(valid_rows) > 200  # 504 - 199 NaN rows = 305+

    @patch("src.data_ingest.infrastructure.regime_data_client.yf")
    def test_history_forward_fills_nan(self, mock_yf: MagicMock) -> None:
        """NaN from date misalignment should be forward-filled."""
        n_days = 504
        sp500_hist = _make_history(n_days, date(2024, 1, 2))
        # VIX has fewer days (simulating different trading calendar)
        vix_hist = _make_history(n_days - 10, date(2024, 1, 15))
        tnx_hist = _make_history(n_days, date(2024, 1, 2))
        irx_hist = _make_history(n_days, date(2024, 1, 2))

        def make_ticker(symbol: str) -> MagicMock:
            t = MagicMock()
            histories = {
                "^GSPC": sp500_hist,
                "^VIX": vix_hist,
                "^TNX": tnx_hist,
                "^IRX": irx_hist,
            }
            t.history.return_value = histories[symbol]
            return t

        mock_yf.Ticker.side_effect = make_ticker

        client = RegimeDataClient()
        df = client.fetch_regime_history(years=2)

        # After forward-fill, no NaN in rows that have sp500_ma200
        valid = df.dropna(subset=["sp500_ma200"])
        assert valid["vix"].isna().sum() == 0
