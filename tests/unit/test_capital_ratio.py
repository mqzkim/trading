"""Capital ratio and OrderFilledEvent tests.

Tests that LIVE_CAPITAL_RATIO reduces effective capital in live mode,
and OrderFilledEvent has the correct schema.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest


class TestCapitalRatioDefault:
    def test_default_is_025(self):
        from src.settings import Settings

        s = Settings(
            _env_file=None,
            EXECUTION_MODE="paper",
        )
        assert s.LIVE_CAPITAL_RATIO == 0.25


class TestCapitalRatioAppliedInLiveMode:
    def test_live_mode_applies_ratio(self):
        """Bootstrap with EXECUTION_MODE=live applies LIVE_CAPITAL_RATIO to capital."""
        from src.shared.infrastructure.db_factory import DBFactory

        db_factory = DBFactory(data_dir=":memory:")

        mock_settings = MagicMock()
        mock_settings.EXECUTION_MODE = "live"
        mock_settings.US_CAPITAL = 100_000.0
        mock_settings.LIVE_CAPITAL_RATIO = 0.25
        mock_settings.ALPACA_LIVE_KEY = "fake-key"
        mock_settings.ALPACA_LIVE_SECRET = "fake-secret"
        mock_settings.ALPACA_PAPER_KEY = None
        mock_settings.ALPACA_PAPER_SECRET = None
        mock_settings.ALPACA_API_KEY = None
        mock_settings.ALPACA_SECRET_KEY = None
        mock_settings.KIS_APP_KEY = None
        mock_settings.KIS_APP_SECRET = None
        mock_settings.KIS_ACCOUNT_NO = None
        mock_settings.KR_CAPITAL = 10_000_000.0
        mock_settings.SLACK_WEBHOOK_URL = None
        mock_settings.PIPELINE_SCHEDULE_HOUR = 16
        mock_settings.PIPELINE_SCHEDULE_MINUTE = 30

        with (
            patch("src.settings.settings", mock_settings),
            patch("src.execution.infrastructure.AlpacaExecutionAdapter"),
        ):
            from src.bootstrap import bootstrap

            ctx = bootstrap(db_factory=db_factory, market="us")

        assert ctx["capital"] == 25_000.0


class TestCapitalRatioNotAppliedInPaper:
    def test_paper_mode_uses_full_capital(self):
        """Bootstrap with paper mode uses full US_CAPITAL."""
        from src.shared.infrastructure.db_factory import DBFactory

        db_factory = DBFactory(data_dir=":memory:")

        mock_settings = MagicMock()
        mock_settings.EXECUTION_MODE = "paper"
        mock_settings.US_CAPITAL = 100_000.0
        mock_settings.LIVE_CAPITAL_RATIO = 0.25
        mock_settings.ALPACA_PAPER_KEY = "fake-key"
        mock_settings.ALPACA_PAPER_SECRET = "fake-secret"
        mock_settings.ALPACA_LIVE_KEY = None
        mock_settings.ALPACA_LIVE_SECRET = None
        mock_settings.ALPACA_API_KEY = None
        mock_settings.ALPACA_SECRET_KEY = None
        mock_settings.KIS_APP_KEY = None
        mock_settings.KIS_APP_SECRET = None
        mock_settings.KIS_ACCOUNT_NO = None
        mock_settings.KR_CAPITAL = 10_000_000.0
        mock_settings.SLACK_WEBHOOK_URL = None
        mock_settings.PIPELINE_SCHEDULE_HOUR = 16
        mock_settings.PIPELINE_SCHEDULE_MINUTE = 30

        with (
            patch("src.settings.settings", mock_settings),
            patch("src.execution.infrastructure.AlpacaExecutionAdapter"),
        ):
            from src.bootstrap import bootstrap

            ctx = bootstrap(db_factory=db_factory, market="us")

        assert ctx["capital"] == 100_000.0


class TestOrderFilledEventSchema:
    def test_has_required_fields(self):
        from src.execution.domain.events import OrderFilledEvent

        event = OrderFilledEvent(
            order_id="ord-1",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
            position_qty=20.0,
        )
        assert event.order_id == "ord-1"
        assert event.symbol == "AAPL"
        assert event.quantity == 10
        assert event.filled_price == 150.0
        assert event.position_qty == 20.0
        assert "OrderFilledEvent" in event.event_type
