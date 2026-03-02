"""Execution planner: generate order plan after risk checks pass."""
import math
from personal.sizer.kelly import atr_position_size
from personal.risk.manager import full_risk_check


ORDER_TYPES = ("LIMIT", "MARKET", "STOP_LIMIT")


def plan_entry(
    symbol: str,
    entry_price: float,
    atr: float,
    capital: float,
    peak_value: float,
    current_value: float,
    sector_exposure: float = 0.0,
    cooldown_days: int = 0,
    order_type: str = "LIMIT",
    atr_multiplier: float = 3.0,
) -> dict:
    """
    Generate an entry order plan.
    1. Check risk gate
    2. Calculate position size
    3. Return order plan dict
    """
    # Step 1: Risk gate
    sizing = atr_position_size(capital, entry_price, atr, atr_multiplier)
    risk_check = full_risk_check(
        peak_value, current_value,
        sizing["position_value"], sector_exposure, cooldown_days
    )

    if not risk_check["passed"]:
        return {
            "symbol": symbol,
            "status": "REJECTED",
            "violations": risk_check["violations"],
            "drawdown_level": risk_check["drawdown_level"],
        }

    # Step 2: Order plan
    limit_offset = 0.005  # 0.5% below current for LIMIT orders
    limit_price = round(entry_price * (1 - limit_offset), 2) if order_type == "LIMIT" else entry_price

    return {
        "symbol": symbol,
        "status": "APPROVED",
        "order_type": order_type,
        "entry_price": entry_price,
        "limit_price": limit_price,
        "shares": sizing["shares"],
        "stop_price": sizing["stop_price"],
        "stop_distance": sizing["stop_distance"],
        "position_value": sizing["position_value"],
        "position_pct": sizing["position_pct"],
        "risk_pct": sizing["risk_pct"],
        "atr_multiplier": atr_multiplier,
        "drawdown_level": risk_check["drawdown_level"],
    }


def plan_exit(
    symbol: str,
    current_price: float,
    stop_price: float,
    shares: int,
    reason: str = "stop_hit",
) -> dict:
    """Generate an exit order plan."""
    return {
        "symbol": symbol,
        "action": "SELL",
        "order_type": "MARKET" if reason == "stop_hit" else "LIMIT",
        "shares": shares,
        "price": current_price,
        "stop_price": stop_price,
        "reason": reason,
        "triggered": current_price <= stop_price if reason == "stop_hit" else True,
    }
