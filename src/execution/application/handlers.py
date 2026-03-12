"""Execution Application — TradePlanHandler.

Orchestrates the trade plan lifecycle: generate -> approve -> execute.
All dependencies injected via constructor (TradePlanService, ITradePlanRepository, AlpacaExecutionAdapter).
"""
from __future__ import annotations

from typing import Optional

from src.execution.domain.repositories import ITradePlanRepository
from src.execution.domain.services import TradePlanService
from src.execution.domain.value_objects import (
    BracketSpec,
    OrderResult,
    TradePlan,
    TradePlanStatus,
)
from src.execution.infrastructure.alpaca_adapter import AlpacaExecutionAdapter

from .commands import ApproveTradePlanCommand, ExecuteOrderCommand, GenerateTradePlanCommand

_SUCCESS_STATUSES = {"filled", "accepted", "partially_filled", "new"}


class TradePlanHandler:
    """Application handler for trade plan lifecycle.

    generate(cmd) -> approve(cmd) -> execute(cmd) flow.
    """

    def __init__(
        self,
        trade_plan_service: TradePlanService,
        trade_plan_repo: ITradePlanRepository,
        execution_adapter: AlpacaExecutionAdapter,
    ) -> None:
        self._service = trade_plan_service
        self._repo = trade_plan_repo
        self._adapter = execution_adapter

    def generate(self, cmd: GenerateTradePlanCommand) -> Optional[TradePlan]:
        """Generate a trade plan via TradePlanService.

        Returns None if the plan is rejected by risk gates.
        Saves accepted plans to repo with PENDING status.
        """
        plan = self._service.generate_plan(
            symbol=cmd.symbol,
            entry_price=cmd.entry_price,
            atr=cmd.atr,
            capital=cmd.capital,
            peak_value=cmd.peak_value,
            current_value=cmd.current_value,
            intrinsic_value=cmd.intrinsic_value,
            composite_score=cmd.composite_score,
            margin_of_safety=cmd.margin_of_safety,
            signal_direction=cmd.signal_direction,
            reasoning_trace=cmd.reasoning_trace,
            sector_exposure=cmd.sector_exposure,
            atr_multiplier=cmd.atr_multiplier,
        )

        if plan is None:
            return None

        self._repo.save(plan, TradePlanStatus.PENDING)
        return plan

    def approve(self, cmd: ApproveTradePlanCommand) -> dict:
        """Approve or reject a pending trade plan.

        If approved with modifications, saves a new plan with MODIFIED status.
        Returns dict with status and symbol (or error).
        """
        plan_dict = self._repo.find_by_symbol(cmd.symbol)
        if plan_dict is None:
            return {"error": f"No pending plan for {cmd.symbol}"}

        if not cmd.approved:
            self._repo.update_status(cmd.symbol, TradePlanStatus.REJECTED)
            return {"status": "REJECTED", "symbol": cmd.symbol}

        # Check for modifications
        has_modifications = (
            cmd.modified_quantity is not None or cmd.modified_stop_loss is not None
        )

        if has_modifications:
            modified_plan = TradePlan(
                symbol=plan_dict["symbol"],
                direction=plan_dict["direction"],
                entry_price=plan_dict["entry_price"],
                stop_loss_price=(
                    cmd.modified_stop_loss
                    if cmd.modified_stop_loss is not None
                    else plan_dict["stop_loss_price"]
                ),
                take_profit_price=plan_dict["take_profit_price"],
                quantity=(
                    cmd.modified_quantity
                    if cmd.modified_quantity is not None
                    else plan_dict["quantity"]
                ),
                position_value=plan_dict["position_value"],
                reasoning_trace=plan_dict.get("reasoning_trace", ""),
                composite_score=plan_dict.get("composite_score", 0.0),
                margin_of_safety=plan_dict.get("margin_of_safety", 0.0),
                signal_direction=plan_dict.get("signal_direction", ""),
            )
            self._repo.save(modified_plan, TradePlanStatus.MODIFIED)
            return {"status": "MODIFIED", "symbol": cmd.symbol}

        self._repo.update_status(cmd.symbol, TradePlanStatus.APPROVED)
        return {"status": "APPROVED", "symbol": cmd.symbol}

    def execute(self, cmd: ExecuteOrderCommand) -> OrderResult:
        """Execute an approved trade plan as a bracket order.

        Raises ValueError if plan not found or not in APPROVED/MODIFIED status.
        """
        plan_dict = self._repo.find_by_symbol(cmd.symbol)
        if plan_dict is None:
            raise ValueError(f"No trade plan found for {cmd.symbol}")

        status = plan_dict.get("status", "")
        if status not in ("APPROVED", "MODIFIED"):
            raise ValueError(
                f"Trade plan for {cmd.symbol} is not approved (status={status})"
            )

        spec = BracketSpec(
            symbol=plan_dict["symbol"],
            quantity=plan_dict["quantity"],
            entry_price=plan_dict["entry_price"],
            stop_loss_price=plan_dict["stop_loss_price"],
            take_profit_price=plan_dict["take_profit_price"],
        )

        result = self._adapter.submit_bracket_order(spec)

        if result.status in _SUCCESS_STATUSES:
            self._repo.update_status(cmd.symbol, TradePlanStatus.EXECUTED)
        else:
            self._repo.update_status(cmd.symbol, TradePlanStatus.FAILED)

        return result
