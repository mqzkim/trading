"""Position sizing: Fractional Kelly (1/4) + ATR-based stop."""
import math


KELLY_FRACTION = 0.25          # Fractional Kelly — never use full Kelly
MAX_POSITION_PCT = 0.08        # Max 8% per position
MAX_SECTOR_PCT = 0.25          # Max 25% per sector
RISK_PER_TRADE_PCT = 0.01      # Max 1% capital at risk per trade


def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Kelly criterion: f* = (p*b - q) / b
    where p=win_rate, q=1-p, b=avg_win/avg_loss
    Returns Fractional Kelly (f* / 4), clamped to [0, 0.25].
    """
    if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0
    b = avg_win / avg_loss
    q = 1 - win_rate
    full_kelly = (win_rate * b - q) / b
    fractional = full_kelly * KELLY_FRACTION
    return max(0.0, min(fractional, MAX_POSITION_PCT))


def atr_position_size(
    capital: float,
    entry_price: float,
    atr: float,
    atr_multiplier: float = 3.0,    # 2.5~3.5
) -> dict:
    """
    ATR-based position sizing.
    Stop distance = atr_multiplier * ATR
    Shares = (capital * RISK_PER_TRADE_PCT) / stop_distance
    """
    if atr <= 0 or entry_price <= 0 or capital <= 0:
        return {"shares": 0, "stop_price": entry_price, "risk_amount": 0, "position_value": 0}

    atr_multiplier = max(2.5, min(3.5, atr_multiplier))  # clamp to allowed range
    stop_distance = atr_multiplier * atr
    stop_price = entry_price - stop_distance
    risk_amount = capital * RISK_PER_TRADE_PCT
    shares = math.floor(risk_amount / stop_distance)

    # Cap at MAX_POSITION_PCT of capital
    max_shares = math.floor((capital * MAX_POSITION_PCT) / entry_price)
    shares = min(shares, max_shares)

    position_value = shares * entry_price
    actual_risk_pct = (shares * stop_distance) / capital if capital > 0 else 0

    return {
        "shares": shares,
        "stop_price": round(stop_price, 2),
        "stop_distance": round(stop_distance, 2),
        "risk_amount": round(shares * stop_distance, 2),
        "risk_pct": round(actual_risk_pct * 100, 3),
        "position_value": round(position_value, 2),
        "position_pct": round(position_value / capital * 100, 2) if capital > 0 else 0,
        "atr_multiplier": atr_multiplier,
    }


def validate_position(
    position_value: float,
    capital: float,
    sector_exposure: float = 0.0,
) -> dict:
    """
    Validate position against hard limits.
    Returns dict with passed=True/False and violations list.
    """
    violations = []
    position_pct = position_value / capital if capital > 0 else 1.0

    if position_pct > MAX_POSITION_PCT:
        violations.append(f"Position {position_pct:.1%} exceeds max {MAX_POSITION_PCT:.0%}")

    new_sector_pct = sector_exposure + position_pct
    if new_sector_pct > MAX_SECTOR_PCT:
        violations.append(f"Sector exposure {new_sector_pct:.1%} exceeds max {MAX_SECTOR_PCT:.0%}")

    return {"passed": len(violations) == 0, "violations": violations}
