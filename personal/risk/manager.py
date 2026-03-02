"""Risk manager: integrate drawdown defense + position validation."""
from .drawdown import assess_drawdown, LEVEL_1_PCT, LEVEL_2_PCT, LEVEL_3_PCT
from personal.sizer.kelly import validate_position


def check_entry_allowed(
    peak_value: float,
    current_value: float,
    cooldown_days: int = 0,
) -> dict:
    """Check if new entries are allowed given current drawdown state."""
    dd = assess_drawdown(peak_value, current_value, cooldown_days)
    return {
        "allowed": dd["allow_new_entries"],
        "drawdown_level": dd["level"],
        "drawdown_pct": dd["drawdown_pct"],
        "reason": dd["action"],
    }


def full_risk_check(
    peak_value: float,
    current_value: float,
    proposed_position_value: float,
    sector_exposure: float = 0.0,
    cooldown_days: int = 0,
) -> dict:
    """
    Full risk gate: drawdown check + position limit check.
    Returns passed=True only if ALL checks pass.
    """
    entry_check = check_entry_allowed(peak_value, current_value, cooldown_days)
    position_check = validate_position(proposed_position_value, current_value, sector_exposure)

    all_passed = entry_check["allowed"] and position_check["passed"]
    violations = position_check["violations"].copy()
    if not entry_check["allowed"]:
        violations.append(entry_check["reason"])

    return {
        "passed": all_passed,
        "violations": violations,
        "drawdown_level": entry_check["drawdown_level"],
        "drawdown_pct": entry_check["drawdown_pct"],
    }
