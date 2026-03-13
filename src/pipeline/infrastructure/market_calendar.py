"""Pipeline Infrastructure -- NYSE Market Calendar Service.

Wraps exchange_calendars for NYSE (XNYS) trading day checks.
Calendar object is cached -- expensive to create (~100ms).
"""
from __future__ import annotations

from datetime import date

import exchange_calendars as xcals
import pandas as pd


class MarketCalendarService:
    """NYSE market calendar wrapper.

    Provides trading day, early close, and next trading day queries.
    """

    def __init__(self) -> None:
        self._cal = xcals.get_calendar("XNYS")

    def is_trading_day(self, d: date) -> bool:
        """Return True if the given date is an NYSE trading session."""
        ts = pd.Timestamp(d)
        return bool(self._cal.is_session(ts))

    def is_early_close(self, d: date) -> bool:
        """Return True if the given date is an NYSE early close session."""
        ts = pd.Timestamp(d)
        if not self._cal.is_session(ts):
            return False
        return ts in self._cal.early_closes

    def next_trading_day(self, d: date) -> date:
        """Return the next NYSE trading session after the given date.

        Always returns a date strictly after d.
        """
        # Add 1 day to ensure we get a date after d, not d itself
        next_day = pd.Timestamp(d) + pd.Timedelta(days=1)
        session = self._cal.date_to_session(next_day, direction="next")
        return session.date()
