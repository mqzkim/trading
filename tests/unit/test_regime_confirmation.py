"""Tests for 3-day confirmation state machine (REGIME-02).

Covers:
  4. First detection (no previous) sets confirmed_days=1
  5. Second consecutive same-regime detection increments to 2
  6. Third consecutive same-regime detection increments to 3 (is_confirmed=True)
  7. Detection of different regime resets confirmed_days to 1
  8. confirmed_days persists across separate handle() calls via find_latest
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from src.regime.application.commands import DetectRegimeCommand
from src.regime.application.handlers import DetectRegimeHandler
from src.regime.domain import (
    IRegimeRepository,
    MarketRegime,
    RegimeType,
)
from src.shared.domain import Ok


class InMemoryRegimeRepo(IRegimeRepository):
    """Dict-backed in-memory repo for testing."""

    def __init__(self) -> None:
        self._store: list[MarketRegime] = []

    def save(self, regime: MarketRegime) -> None:
        self._store.append(regime)

    def find_latest(self) -> Optional[MarketRegime]:
        return self._store[-1] if self._store else None

    def find_by_date_range(
        self, start: datetime, end: datetime
    ) -> list[MarketRegime]:
        return [
            r
            for r in self._store
            if start <= r.detected_at <= end
        ]


def _bull_cmd() -> DetectRegimeCommand:
    """Command that produces Bull regime."""
    return DetectRegimeCommand(
        vix=15.0,
        sp500_price=5000.0,
        sp500_ma200=4800.0,
        adx=30.0,
        yield_spread=0.5,
    )


def _bear_cmd() -> DetectRegimeCommand:
    """Command that produces Bear regime."""
    return DetectRegimeCommand(
        vix=35.0,
        sp500_price=4200.0,
        sp500_ma200=4500.0,
        adx=28.0,
        yield_spread=-0.3,
    )


class TestConfirmationStateMachine:
    def test_first_detection_sets_confirmed_days_1(self) -> None:
        """Test 4: First detection with no previous regime -> confirmed_days=1."""
        repo = InMemoryRegimeRepo()
        handler = DetectRegimeHandler(regime_repo=repo)

        result = handler.handle(_bull_cmd())

        assert isinstance(result, Ok)
        assert result.value["confirmed_days"] == 1
        assert result.value["is_confirmed"] is False

    def test_second_same_regime_increments_to_2(self) -> None:
        """Test 5: Second consecutive same-regime -> confirmed_days=2."""
        repo = InMemoryRegimeRepo()
        handler = DetectRegimeHandler(regime_repo=repo)

        handler.handle(_bull_cmd())
        result = handler.handle(_bull_cmd())

        assert isinstance(result, Ok)
        assert result.value["confirmed_days"] == 2
        assert result.value["is_confirmed"] is False

    def test_third_same_regime_confirms(self) -> None:
        """Test 6: Third consecutive same-regime -> confirmed_days=3, is_confirmed=True."""
        repo = InMemoryRegimeRepo()
        handler = DetectRegimeHandler(regime_repo=repo)

        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())
        result = handler.handle(_bull_cmd())

        assert isinstance(result, Ok)
        assert result.value["confirmed_days"] == 3
        assert result.value["is_confirmed"] is True

    def test_different_regime_resets_to_1(self) -> None:
        """Test 7: Detecting a different regime resets confirmed_days to 1."""
        repo = InMemoryRegimeRepo()
        handler = DetectRegimeHandler(regime_repo=repo)

        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())
        # Now switch to Bear
        result = handler.handle(_bear_cmd())

        assert isinstance(result, Ok)
        assert result.value["confirmed_days"] == 1
        assert result.value["is_confirmed"] is False
        assert result.value["regime_type"] == "Bear"

    def test_confirmed_days_persists_via_find_latest(self) -> None:
        """Test 8: confirmed_days increments across calls loaded from repo."""
        repo = InMemoryRegimeRepo()
        handler = DetectRegimeHandler(regime_repo=repo)

        # Three calls should show incrementing confirmed_days
        handler.handle(_bull_cmd())
        assert repo.find_latest() is not None
        assert repo.find_latest().confirmed_days == 1

        handler.handle(_bull_cmd())
        assert repo.find_latest().confirmed_days == 2

        handler.handle(_bull_cmd())
        assert repo.find_latest().confirmed_days == 3
        assert repo.find_latest().is_confirmed is True
