"""Tests for MarketCalendarService -- NYSE trading day checks."""
from __future__ import annotations

from datetime import date

import pytest

from src.pipeline.infrastructure.market_calendar import MarketCalendarService


@pytest.fixture(scope="module")
def calendar() -> MarketCalendarService:
    """Shared calendar instance -- expensive to create."""
    return MarketCalendarService()


class TestMarketCalendarService:
    def test_weekday_is_trading_day(self, calendar: MarketCalendarService) -> None:
        # 2026-01-02 is a Friday (first trading day of 2026)
        assert calendar.is_trading_day(date(2026, 1, 2)) is True

    def test_weekend_is_not_trading_day(self, calendar: MarketCalendarService) -> None:
        # 2026-01-03 is Saturday
        assert calendar.is_trading_day(date(2026, 1, 3)) is False
        # 2026-01-04 is Sunday
        assert calendar.is_trading_day(date(2026, 1, 4)) is False

    def test_new_years_day_is_holiday(self, calendar: MarketCalendarService) -> None:
        # 2026-01-01 is Thursday (New Year's Day)
        assert calendar.is_trading_day(date(2026, 1, 1)) is False

    def test_christmas_is_holiday(self, calendar: MarketCalendarService) -> None:
        # 2025-12-25 is Thursday (Christmas)
        assert calendar.is_trading_day(date(2025, 12, 25)) is False

    def test_next_trading_day_from_friday(
        self, calendar: MarketCalendarService
    ) -> None:
        # 2026-01-02 is Friday -> next trading day is Monday 2026-01-05
        nxt = calendar.next_trading_day(date(2026, 1, 2))
        assert nxt == date(2026, 1, 5)

    def test_next_trading_day_from_saturday(
        self, calendar: MarketCalendarService
    ) -> None:
        # 2026-01-03 is Saturday -> next trading day is Monday 2026-01-05
        nxt = calendar.next_trading_day(date(2026, 1, 3))
        assert nxt == date(2026, 1, 5)

    def test_next_trading_day_from_holiday(
        self, calendar: MarketCalendarService
    ) -> None:
        # 2026-01-01 is New Year's Day -> next is 2026-01-02
        nxt = calendar.next_trading_day(date(2026, 1, 1))
        assert nxt == date(2026, 1, 2)

    def test_next_trading_day_from_wednesday(
        self, calendar: MarketCalendarService
    ) -> None:
        # 2026-01-07 is Wednesday -> next is Thursday 2026-01-08
        nxt = calendar.next_trading_day(date(2026, 1, 7))
        assert nxt == date(2026, 1, 8)

    def test_is_early_close_returns_bool(
        self, calendar: MarketCalendarService
    ) -> None:
        # Just verify it returns a bool for a known date
        result = calendar.is_early_close(date(2026, 1, 5))
        assert isinstance(result, bool)

    def test_early_close_day_before_christmas(
        self, calendar: MarketCalendarService
    ) -> None:
        # 2025-12-24 is typically an early close (Christmas Eve, Wednesday)
        result = calendar.is_early_close(date(2025, 12, 24))
        assert result is True

    def test_regular_day_not_early_close(
        self, calendar: MarketCalendarService
    ) -> None:
        # A regular Monday is not early close
        result = calendar.is_early_close(date(2026, 1, 5))
        assert result is False
