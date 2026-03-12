"""Execution Domain — Domain Services.

TradePlanService: personal/execution/planner.plan_entry()에 위임하여 TradePlan VO 생성.
수학 로직 재작성 금지 -- adapter pattern only.
"""
from __future__ import annotations

from typing import Optional

from personal.execution.planner import plan_entry
from src.portfolio.domain.value_objects import TakeProfitLevels

from .value_objects import TradePlan


class TradePlanService:
    """Trade plan 생성 서비스.

    personal/execution/planner.plan_entry()에 위임하여
    리스크 체크 + 포지션 사이징 후 TradePlan VO로 변환.
    """

    def generate_plan(
        self,
        symbol: str,
        entry_price: float,
        atr: float,
        capital: float,
        peak_value: float,
        current_value: float,
        intrinsic_value: float,
        composite_score: float,
        margin_of_safety: float,
        signal_direction: str,
        reasoning_trace: str,
        sector_exposure: float = 0.0,
        atr_multiplier: float = 3.0,
    ) -> Optional[TradePlan]:
        """Generate a trade plan via planner delegation.

        Returns None if planner rejects the plan (risk gate failure).
        """
        result = plan_entry(
            symbol=symbol,
            entry_price=entry_price,
            atr=atr,
            capital=capital,
            peak_value=peak_value,
            current_value=current_value,
            sector_exposure=sector_exposure,
            atr_multiplier=atr_multiplier,
        )

        if result["status"] == "REJECTED":
            return None

        # Compute take-profit price from TakeProfitLevels VO
        tp_levels = TakeProfitLevels(
            entry_price=entry_price,
            intrinsic_value=intrinsic_value,
        )
        if tp_levels.has_upside and tp_levels.levels:
            take_profit_price = tp_levels.levels[0]["price"]
        else:
            take_profit_price = round(entry_price * 1.1, 2)

        return TradePlan(
            symbol=symbol,
            direction="BUY",
            entry_price=result["entry_price"],
            stop_loss_price=result["stop_price"],
            take_profit_price=take_profit_price,
            quantity=result["shares"],
            position_value=result["position_value"],
            reasoning_trace=reasoning_trace,
            composite_score=composite_score,
            margin_of_safety=margin_of_safety,
            signal_direction=signal_direction,
        )
