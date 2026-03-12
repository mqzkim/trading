"""Tests for IBrokerAdapter ABC — market-agnostic broker interface."""
from __future__ import annotations

import pytest

from src.execution.domain.repositories import IBrokerAdapter
from src.execution.domain.value_objects import OrderResult, OrderSpec


class TestIBrokerAdapterABC:
    """IBrokerAdapter cannot be instantiated directly; concrete subclass works."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            IBrokerAdapter()  # type: ignore[abstract]

    def test_concrete_implementation_can_be_instantiated(self):
        class StubBroker(IBrokerAdapter):
            def submit_order(self, spec: OrderSpec) -> OrderResult:
                return OrderResult(
                    order_id="STUB-1",
                    status="filled",
                    symbol=spec.symbol,
                    quantity=spec.quantity,
                    filled_price=spec.entry_price,
                )

            def get_positions(self) -> list[dict]:
                return []

            def get_account(self) -> dict:
                return {"cash": 0.0}

        broker = StubBroker()
        assert broker is not None

    def test_concrete_must_implement_all_methods(self):
        """Partial implementation still raises TypeError."""

        class PartialBroker(IBrokerAdapter):
            def submit_order(self, spec: OrderSpec) -> OrderResult:
                return OrderResult()  # type: ignore[call-arg]

        with pytest.raises(TypeError):
            PartialBroker()  # type: ignore[abstract]
