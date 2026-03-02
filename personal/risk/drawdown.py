"""Drawdown defense — 3-level protection policy."""

# Drawdown thresholds
LEVEL_1_PCT = 0.10   # 10%: halt new entries
LEVEL_2_PCT = 0.15   # 15%: reduce 50%
LEVEL_3_PCT = 0.20   # 20%: full liquidation + 1-month cooldown

COOLDOWN_DAYS = 30


def assess_drawdown(
    peak_value: float,
    current_value: float,
    cooldown_days_remaining: int = 0,
) -> dict:
    """
    Assess current drawdown level and return action.

    Returns:
        level: 0-3 (0=normal, 1=caution, 2=reduce, 3=liquidate)
        action: string description
        allow_new_entries: bool
        reduce_pct: float (0.0-1.0, how much to reduce)
        in_cooldown: bool
    """
    if peak_value <= 0:
        return {"level": 0, "action": "normal", "allow_new_entries": True,
                "reduce_pct": 0.0, "in_cooldown": False, "drawdown_pct": 0.0}

    if cooldown_days_remaining > 0:
        return {
            "level": 3,
            "action": f"cooldown: {cooldown_days_remaining} days remaining",
            "allow_new_entries": False,
            "reduce_pct": 1.0,
            "in_cooldown": True,
            "drawdown_pct": (peak_value - current_value) / peak_value,
        }

    drawdown = (peak_value - current_value) / peak_value

    if drawdown >= LEVEL_3_PCT:
        return {
            "level": 3,
            "action": "FULL LIQUIDATION — 20% drawdown exceeded. 30-day cooldown required.",
            "allow_new_entries": False,
            "reduce_pct": 1.0,
            "in_cooldown": False,
            "drawdown_pct": round(drawdown, 4),
            "requires_cooldown": True,
        }
    elif drawdown >= LEVEL_2_PCT:
        return {
            "level": 2,
            "action": "REDUCE 50% — 15% drawdown. Switch to defensive posture.",
            "allow_new_entries": False,
            "reduce_pct": 0.5,
            "in_cooldown": False,
            "drawdown_pct": round(drawdown, 4),
        }
    elif drawdown >= LEVEL_1_PCT:
        return {
            "level": 1,
            "action": "HALT NEW ENTRIES — 10% drawdown. Monitor closely.",
            "allow_new_entries": False,
            "reduce_pct": 0.0,
            "in_cooldown": False,
            "drawdown_pct": round(drawdown, 4),
        }
    else:
        return {
            "level": 0,
            "action": "normal",
            "allow_new_entries": True,
            "reduce_pct": 0.0,
            "in_cooldown": False,
            "drawdown_pct": round(drawdown, 4),
        }
