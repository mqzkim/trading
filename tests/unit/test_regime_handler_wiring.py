"""Tests for DetectRegimeHandler data fetching and regime detection (REGIME-01).

Covers:
  1. Handler with explicit command values creates MarketRegime with correct regime_type
  2. Handler with no data_client falls back to importing RegimeDataClient
  3. Handler with injected data_client uses client.fetch_regime_snapshot()
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from src.regime.application.commands import DetectRegimeCommand
from src.regime.application.handlers import DetectRegimeHandler
from src.regime.domain import (
    IRegimeRepository,
    MarketRegime,
    RegimeType,
    VIXLevel,
    TrendStrength,
    YieldCurve,
    SP500Position,
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


class TestHandlerWithExplicitValues:
    """Test 1: handler.handle() with explicit command values creates correct regime."""

    def test_creates_regime_with_correct_type_and_saves(self) -> None:
        repo = InMemoryRegimeRepo()
        handler = DetectRegimeHandler(regime_repo=repo)

        # Bull conditions: VIX < 20, S&P above MA200, ADX > 25, positive yield
        cmd = DetectRegimeCommand(
            vix=15.0,
            sp500_price=5000.0,
            sp500_ma200=4800.0,
            adx=30.0,
            yield_spread=0.5,
        )
        result = handler.handle(cmd)

        assert isinstance(result, Ok)
        assert result.value["regime_type"] == "Bull"
        assert result.value["confidence"] > 0
        assert len(repo._store) == 1
        assert repo._store[0].regime_type == RegimeType.BULL


class TestHandlerFallbackDataClient:
    """Test 2: handler with no data_client falls back to importing RegimeDataClient."""

    def test_fallback_import_uses_snapshot_values(self) -> None:
        repo = InMemoryRegimeRepo()
        handler = DetectRegimeHandler(regime_repo=repo)

        mock_snapshot = {
            "vix": 15.0,
            "sp500_close": 5000.0,
            "sp500_ma200": 4800.0,
            "adx": 30.0,
            "yield_spread": 0.5,
        }

        # Patch the RegimeDataClient at module-level import location
        with patch(
            "src.data_ingest.infrastructure.regime_data_client.RegimeDataClient"
        ) as MockClientClass:
            mock_instance = MagicMock()
            mock_instance.fetch_regime_snapshot.return_value = mock_snapshot
            MockClientClass.return_value = mock_instance

            # Sentinel zeros trigger data fetch fallback
            cmd = DetectRegimeCommand(
                vix=0.0,
                sp500_price=0.0,
                sp500_ma200=0.0,
                adx=0.0,
                yield_spread=0.0,
            )
            result = handler.handle(cmd)

        assert isinstance(result, Ok)
        assert result.value["regime_type"] == "Bull"
        mock_instance.fetch_regime_snapshot.assert_called_once()


class TestHandlerInjectedDataClient:
    """Test 3: handler with injected data_client uses client.fetch_regime_snapshot()."""

    def test_injected_client_used_for_data_fetch(self) -> None:
        repo = InMemoryRegimeRepo()
        mock_client = MagicMock()
        mock_client.fetch_regime_snapshot.return_value = {
            "vix": 35.0,
            "sp500_close": 4200.0,
            "sp500_ma200": 4500.0,
            "adx": 28.0,
            "yield_spread": -0.3,
        }

        handler = DetectRegimeHandler(
            regime_repo=repo, data_client=mock_client
        )

        # Sentinel zeros trigger data fetch
        cmd = DetectRegimeCommand(
            vix=0.0,
            sp500_price=0.0,
            sp500_ma200=0.0,
            adx=0.0,
            yield_spread=0.0,
        )
        result = handler.handle(cmd)

        assert isinstance(result, Ok)
        mock_client.fetch_regime_snapshot.assert_called_once()
        # Bear conditions: VIX > 30, S&P below MA200
        assert result.value["regime_type"] == "Bear"
