"""Unit tests for PositionReconciliationService.

Tests reconciliation between local SQLite positions and broker positions.
Covers SAFE-04: position divergence detection and pipeline halt.
"""
from __future__ import annotations

import pytest

from src.execution.infrastructure.reconciliation import (
    Discrepancy,
    PositionReconciliationService,
    ReconciliationError,
)


class MockBrokerAdapter:
    """Mock broker adapter that returns preset positions."""

    def __init__(self, positions: list[dict] | None = None) -> None:
        self._positions = positions or []

    def get_positions(self) -> list[dict]:
        return self._positions

    def submit_order(self, spec):  # noqa: ARG002
        return None

    def get_account(self) -> dict:
        return {}


class MockPositionRepo:
    """Mock position repo that returns preset position dicts."""

    def __init__(self, positions: list[dict] | None = None) -> None:
        self._positions = positions or []

    def find_all_open(self) -> list[dict]:
        return self._positions


class TestReconcileDetection:
    """Tests for reconcile() discrepancy detection."""

    def test_no_discrepancies(self) -> None:
        """Both local and broker have same symbols and quantities."""
        repo = MockPositionRepo([
            {"symbol": "AAPL", "qty": 10},
            {"symbol": "MSFT", "qty": 5},
        ])
        broker = MockBrokerAdapter([
            {"symbol": "AAPL", "qty": 10},
            {"symbol": "MSFT", "qty": 5},
        ])
        service = PositionReconciliationService(repo, broker)

        result = service.reconcile()

        assert result == []

    def test_local_only(self) -> None:
        """Symbol in local but not in broker -> local_only discrepancy."""
        repo = MockPositionRepo([
            {"symbol": "AAPL", "qty": 10},
            {"symbol": "TSLA", "qty": 3},
        ])
        broker = MockBrokerAdapter([
            {"symbol": "AAPL", "qty": 10},
        ])
        service = PositionReconciliationService(repo, broker)

        result = service.reconcile()

        assert len(result) == 1
        assert result[0].symbol == "TSLA"
        assert result[0].discrepancy_type == "local_only"
        assert result[0].local_qty == 3
        assert result[0].broker_qty is None

    def test_broker_only(self) -> None:
        """Symbol in broker but not in local -> broker_only discrepancy."""
        repo = MockPositionRepo([
            {"symbol": "AAPL", "qty": 10},
        ])
        broker = MockBrokerAdapter([
            {"symbol": "AAPL", "qty": 10},
            {"symbol": "GOOGL", "qty": 7},
        ])
        service = PositionReconciliationService(repo, broker)

        result = service.reconcile()

        assert len(result) == 1
        assert result[0].symbol == "GOOGL"
        assert result[0].discrepancy_type == "broker_only"
        assert result[0].local_qty is None
        assert result[0].broker_qty == 7

    def test_qty_mismatch(self) -> None:
        """Same symbol, different qty -> qty_mismatch discrepancy."""
        repo = MockPositionRepo([
            {"symbol": "AAPL", "qty": 10},
        ])
        broker = MockBrokerAdapter([
            {"symbol": "AAPL", "qty": 15},
        ])
        service = PositionReconciliationService(repo, broker)

        result = service.reconcile()

        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].discrepancy_type == "qty_mismatch"
        assert result[0].local_qty == 10
        assert result[0].broker_qty == 15

    def test_multiple_discrepancies(self) -> None:
        """Mix of all three discrepancy types."""
        repo = MockPositionRepo([
            {"symbol": "AAPL", "qty": 10},
            {"symbol": "TSLA", "qty": 3},
        ])
        broker = MockBrokerAdapter([
            {"symbol": "AAPL", "qty": 15},
            {"symbol": "GOOGL", "qty": 7},
        ])
        service = PositionReconciliationService(repo, broker)

        result = service.reconcile()

        assert len(result) == 3
        types = {d.discrepancy_type for d in result}
        assert types == {"local_only", "broker_only", "qty_mismatch"}

    def test_empty_both_sides(self) -> None:
        """Both local and broker empty -> no discrepancies."""
        repo = MockPositionRepo([])
        broker = MockBrokerAdapter([])
        service = PositionReconciliationService(repo, broker)

        result = service.reconcile()

        assert result == []


class TestCheckAndHalt:
    """Tests for check_and_halt() pipeline blocking."""

    def test_halt_on_mismatch(self) -> None:
        """check_and_halt raises ReconciliationError when discrepancies exist."""
        repo = MockPositionRepo([{"symbol": "AAPL", "qty": 10}])
        broker = MockBrokerAdapter([{"symbol": "AAPL", "qty": 15}])
        service = PositionReconciliationService(repo, broker)

        with pytest.raises(ReconciliationError) as exc_info:
            service.check_and_halt()

        assert len(exc_info.value.discrepancies) == 1
        assert exc_info.value.discrepancies[0].symbol == "AAPL"

    def test_halt_passes_when_synced(self) -> None:
        """check_and_halt returns None when positions are in sync."""
        repo = MockPositionRepo([{"symbol": "AAPL", "qty": 10}])
        broker = MockBrokerAdapter([{"symbol": "AAPL", "qty": 10}])
        service = PositionReconciliationService(repo, broker)

        result = service.check_and_halt()

        assert result is None
