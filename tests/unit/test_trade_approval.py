"""Tests for TradePlanHandler — generate, approve, execute flow."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.execution.domain.value_objects import (
    OrderResult,
    TradePlan,
    TradePlanStatus,
)


def _make_plan(**overrides) -> TradePlan:
    defaults = dict(
        symbol="AAPL",
        direction="BUY",
        entry_price=150.0,
        stop_loss_price=140.0,
        take_profit_price=170.0,
        quantity=10,
        position_value=1500.0,
        reasoning_trace="test reasoning",
        composite_score=75.0,
        margin_of_safety=0.15,
        signal_direction="BUY",
    )
    defaults.update(overrides)
    return TradePlan(**defaults)


def _plan_dict(**overrides) -> dict:
    """Return a plan dict as returned by the repository."""
    defaults = dict(
        symbol="AAPL",
        direction="BUY",
        entry_price=150.0,
        stop_loss_price=140.0,
        take_profit_price=170.0,
        quantity=10,
        position_value=1500.0,
        reasoning_trace="test reasoning",
        composite_score=75.0,
        margin_of_safety=0.15,
        signal_direction="BUY",
        status="PENDING",
    )
    defaults.update(overrides)
    return defaults


class TestTradePlanHandlerGenerate:
    """Test TradePlanHandler.generate() method."""

    def test_generate_calls_service_and_saves_pending(self):
        from src.execution.application.commands import GenerateTradePlanCommand
        from src.execution.application.handlers import TradePlanHandler

        plan = _make_plan()
        service = MagicMock()
        service.generate_plan.return_value = plan
        repo = MagicMock()
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = GenerateTradePlanCommand(
            symbol="AAPL",
            entry_price=150.0,
            atr=5.0,
            capital=100000.0,
            peak_value=100000.0,
            current_value=100000.0,
            intrinsic_value=180.0,
            composite_score=75.0,
            margin_of_safety=0.15,
            signal_direction="BUY",
            reasoning_trace="test reasoning",
        )
        result = handler.generate(cmd)

        assert result is not None
        assert result.symbol == "AAPL"
        service.generate_plan.assert_called_once()
        repo.save.assert_called_once_with(plan, TradePlanStatus.PENDING)

    def test_generate_returns_none_when_service_rejects(self):
        from src.execution.application.commands import GenerateTradePlanCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        service.generate_plan.return_value = None
        repo = MagicMock()
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = GenerateTradePlanCommand(
            symbol="AAPL",
            entry_price=150.0,
            atr=5.0,
            capital=100000.0,
            peak_value=100000.0,
            current_value=100000.0,
            intrinsic_value=180.0,
            composite_score=75.0,
            margin_of_safety=0.15,
            signal_direction="BUY",
            reasoning_trace="test reasoning",
        )
        result = handler.generate(cmd)

        assert result is None
        repo.save.assert_not_called()


class TestTradePlanHandlerApprove:
    """Test TradePlanHandler.approve() method."""

    def test_approve_true_updates_to_approved(self):
        from src.execution.application.commands import ApproveTradePlanCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = _plan_dict()
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ApproveTradePlanCommand(symbol="AAPL", approved=True)
        result = handler.approve(cmd)

        assert result["status"] == "APPROVED"
        assert result["symbol"] == "AAPL"
        repo.update_status.assert_called_once_with("AAPL", TradePlanStatus.APPROVED)

    def test_approve_false_updates_to_rejected(self):
        from src.execution.application.commands import ApproveTradePlanCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = _plan_dict()
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ApproveTradePlanCommand(symbol="AAPL", approved=False)
        result = handler.approve(cmd)

        assert result["status"] == "REJECTED"
        assert result["symbol"] == "AAPL"
        repo.update_status.assert_called_once_with("AAPL", TradePlanStatus.REJECTED)

    def test_approve_not_found_returns_error(self):
        from src.execution.application.commands import ApproveTradePlanCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = None
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ApproveTradePlanCommand(symbol="AAPL", approved=True)
        result = handler.approve(cmd)

        assert "error" in result
        repo.update_status.assert_not_called()

    def test_approve_with_modified_quantity_creates_modified(self):
        from src.execution.application.commands import ApproveTradePlanCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = _plan_dict()
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ApproveTradePlanCommand(
            symbol="AAPL", approved=True, modified_quantity=5
        )
        result = handler.approve(cmd)

        assert result["status"] == "MODIFIED"
        assert result["symbol"] == "AAPL"
        # Should save modified plan and update status
        repo.save.assert_called_once()
        saved_plan = repo.save.call_args[0][0]
        assert saved_plan.quantity == 5
        assert repo.save.call_args[0][1] == TradePlanStatus.MODIFIED

    def test_approve_with_modified_stop_loss_creates_modified(self):
        from src.execution.application.commands import ApproveTradePlanCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = _plan_dict()
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ApproveTradePlanCommand(
            symbol="AAPL", approved=True, modified_stop_loss=135.0
        )
        result = handler.approve(cmd)

        assert result["status"] == "MODIFIED"
        repo.save.assert_called_once()
        saved_plan = repo.save.call_args[0][0]
        assert saved_plan.stop_loss_price == 135.0


class TestTradePlanHandlerExecute:
    """Test TradePlanHandler.execute() method."""

    def test_execute_approved_plan_calls_adapter(self):
        from src.execution.application.commands import ExecuteOrderCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = _plan_dict(status="APPROVED")
        adapter = MagicMock()
        adapter.submit_bracket_order.return_value = OrderResult(
            order_id="ORD-123",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
        )

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ExecuteOrderCommand(symbol="AAPL")
        result = handler.execute(cmd)

        assert result.order_id == "ORD-123"
        assert result.status == "filled"
        adapter.submit_bracket_order.assert_called_once()
        repo.update_status.assert_called_once_with("AAPL", TradePlanStatus.EXECUTED)

    def test_execute_failed_order_updates_to_failed(self):
        from src.execution.application.commands import ExecuteOrderCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = _plan_dict(status="APPROVED")
        adapter = MagicMock()
        adapter.submit_bracket_order.return_value = OrderResult(
            order_id="ORD-456",
            status="rejected",
            symbol="AAPL",
            quantity=10,
            error_message="Insufficient buying power",
        )

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ExecuteOrderCommand(symbol="AAPL")
        result = handler.execute(cmd)

        assert result.status == "rejected"
        repo.update_status.assert_called_once_with("AAPL", TradePlanStatus.FAILED)

    def test_execute_not_approved_raises_error(self):
        from src.execution.application.commands import ExecuteOrderCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = _plan_dict(status="PENDING")
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ExecuteOrderCommand(symbol="AAPL")

        with pytest.raises(ValueError):
            handler.execute(cmd)

    def test_execute_not_found_raises_error(self):
        from src.execution.application.commands import ExecuteOrderCommand
        from src.execution.application.handlers import TradePlanHandler

        service = MagicMock()
        repo = MagicMock()
        repo.find_by_symbol.return_value = None
        adapter = MagicMock()

        handler = TradePlanHandler(service, repo, adapter)
        cmd = ExecuteOrderCommand(symbol="AAPL")

        with pytest.raises(ValueError):
            handler.execute(cmd)
