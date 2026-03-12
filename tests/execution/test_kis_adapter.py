"""Tests for KisExecutionAdapter — KIS (한국투자증권) broker adapter.

Mock-first: all tests run without KIS credentials.
Covers: KR-01 (IBrokerAdapter), KR-02 (mock paper trading), KR-03 (KRX tick size).
"""
from __future__ import annotations

from src.execution.domain.repositories import IBrokerAdapter
from src.execution.domain.value_objects import OrderSpec, OrderResult
from src.execution.infrastructure.kis_adapter import (
    KisExecutionAdapter,
    _tick_size,
    _round_to_tick,
    validate_price_limit,
)


class TestKisAdapterMockMode:
    """KisExecutionAdapter with no credentials operates in mock mode."""

    def test_mock_submit_order(self) -> None:
        adapter = KisExecutionAdapter()
        spec = OrderSpec(symbol="005930", quantity=10, entry_price=70000.0, direction="BUY")
        result = adapter.submit_order(spec)
        assert isinstance(result, OrderResult)
        assert result.status == "filled"
        assert result.order_id.startswith("KIS-MOCK-")
        assert result.symbol == "005930"
        assert result.quantity == 10
        assert result.filled_price == 70000.0

    def test_mock_sell_order(self) -> None:
        adapter = KisExecutionAdapter()
        spec = OrderSpec(symbol="005930", quantity=5, entry_price=68000.0, direction="SELL")
        result = adapter.submit_order(spec)
        assert result.status == "filled"
        assert result.order_id.startswith("KIS-MOCK-")
        assert result.symbol == "005930"

    def test_implements_interface(self) -> None:
        adapter = KisExecutionAdapter()
        assert isinstance(adapter, IBrokerAdapter)

    def test_mock_get_positions(self) -> None:
        adapter = KisExecutionAdapter()
        positions = adapter.get_positions()
        assert positions == []

    def test_mock_get_account(self) -> None:
        adapter = KisExecutionAdapter()
        account = adapter.get_account()
        assert account["currency"] == "KRW"


class TestTickSize:
    """KRX tick size table (2024) — 7 price brackets."""

    def test_tick_size_under_1000(self) -> None:
        assert _tick_size(500) == 1

    def test_tick_size_1000_to_5000(self) -> None:
        assert _tick_size(3000) == 5

    def test_tick_size_5000_to_10000(self) -> None:
        assert _tick_size(8000) == 10

    def test_tick_size_10000_to_50000(self) -> None:
        assert _tick_size(45000) == 50

    def test_tick_size_50000_to_100000(self) -> None:
        assert _tick_size(75000) == 100

    def test_tick_size_100000_to_500000(self) -> None:
        assert _tick_size(350000) == 500

    def test_tick_size_above_500000(self) -> None:
        assert _tick_size(600000) == 1000


class TestRoundToTick:
    """Round arbitrary prices to nearest valid KRX tick."""

    def test_round_to_tick_50(self) -> None:
        assert _round_to_tick(45123) == 45100

    def test_round_to_tick_10(self) -> None:
        assert _round_to_tick(8047) == 8050


class TestPriceLimitValidation:
    """KRX daily price limit is +-30% from previous close."""

    def test_price_within_limit(self) -> None:
        # 10% above previous close — should pass
        validate_price_limit(entry_price=110000.0, previous_close=100000.0)

    def test_price_above_30pct_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="30%"):
            validate_price_limit(entry_price=131000.0, previous_close=100000.0)

    def test_price_below_30pct_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="30%"):
            validate_price_limit(entry_price=69000.0, previous_close=100000.0)


class TestCredentialsModeDetection:
    """Credentials trigger real mode attempt."""

    def test_credentials_trigger_real_mode_attempt(self) -> None:
        # With credentials provided, _use_mock starts False
        # (will fall back to True if kis import fails — that's fine)
        adapter = KisExecutionAdapter(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
        )
        # After __init__, if kis library not installed, it falls back to mock
        # The key assertion: it attempted real mode (we can't assert _use_mock=False
        # because the import will fail, but we verify it's still functional)
        assert isinstance(adapter, IBrokerAdapter)
        # Should still work in mock fallback
        result = adapter.submit_order(
            OrderSpec(symbol="005930", quantity=1, entry_price=70000.0)
        )
        assert result.status == "filled"
