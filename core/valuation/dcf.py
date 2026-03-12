"""DCF valuation model -- pure math, no external dependencies.

2-stage DCF with CAPM-derived WACC (clipped to 6-14%) and terminal value
averaging Gordon Growth Model and Exit Multiple method. Terminal value
capped at 40% of total.

References:
- CONTEXT.md locked decisions: WACC clip 6-14%, TV cap 40%
- https://www.tidy-finance.org/python/discounted-cash-flow-analysis.html
"""
from __future__ import annotations

WACC_FLOOR = 0.06
WACC_CEILING = 0.14


def compute_wacc(
    beta: float,
    risk_free_rate: float,
    equity_risk_premium: float,
    debt_to_equity: float,
    cost_of_debt: float,
    tax_rate: float,
) -> dict:
    """Compute WACC via CAPM. Clip to [6%, 14%] range.

    WACC = We * Ke + Wd * Kd * (1 - T)
    Ke = Rf + Beta * ERP  (CAPM)
    """
    cost_of_equity = risk_free_rate + beta * equity_risk_premium

    weight_equity = 1.0 / (1.0 + debt_to_equity) if (1.0 + debt_to_equity) != 0 else 1.0
    weight_debt = debt_to_equity / (1.0 + debt_to_equity) if (1.0 + debt_to_equity) != 0 else 0.0

    raw_wacc = (
        weight_equity * cost_of_equity
        + weight_debt * cost_of_debt * (1.0 - tax_rate)
    )

    clipped = raw_wacc < WACC_FLOOR or raw_wacc > WACC_CEILING
    wacc = max(WACC_FLOOR, min(WACC_CEILING, raw_wacc))

    return {
        "wacc": wacc,
        "cost_of_equity": cost_of_equity,
        "weight_equity": weight_equity,
        "weight_debt": weight_debt,
        "clipped": clipped,
    }


def compute_dcf(
    base_fcf: float,
    stage1_growth: float,
    stage2_growth: float,
    wacc: float,
    exit_multiple: float,
    projection_years: int = 5,
    terminal_value_cap: float = 0.40,
) -> dict:
    """2-stage DCF with Gordon Growth + Exit Multiple terminal value.

    Terminal Value = average of Gordon Growth and Exit Multiple methods.
    Cap TV at terminal_value_cap (default 40%) of total.
    If cap triggers, confidence_penalty = 0.2.
    If base_fcf <= 0, return dcf_value = 0.
    """
    if base_fcf <= 0:
        return {
            "dcf_value": 0.0,
            "projected_fcfs": (),
            "tv_gordon": 0.0,
            "tv_exit": 0.0,
            "tv_average": 0.0,
            "tv_pct": 0.0,
            "tv_capped": False,
            "confidence_penalty": 0.0,
        }

    # Stage 1: Project FCF for projection_years and discount to PV
    projected_fcfs = []
    pv_fcfs = []
    for year in range(1, projection_years + 1):
        fcf = base_fcf * (1.0 + stage1_growth) ** year
        pv = fcf / (1.0 + wacc) ** year
        projected_fcfs.append(fcf)
        pv_fcfs.append(pv)

    pv_stage1 = sum(pv_fcfs)

    # Terminal FCF (year after projection period)
    terminal_fcf = base_fcf * (1.0 + stage1_growth) ** projection_years * (1.0 + stage2_growth)

    # Gordon Growth Model terminal value
    if wacc > stage2_growth:
        tv_gordon = terminal_fcf / (wacc - stage2_growth)
    else:
        tv_gordon = terminal_fcf * 50.0  # fallback cap for edge case

    # Exit Multiple terminal value (using last projected FCF * exit_multiple)
    last_fcf = projected_fcfs[-1]
    tv_exit = last_fcf * exit_multiple

    # Average of both methods (per locked decision)
    tv_average = (tv_gordon + tv_exit) / 2.0

    # Discount TV to present value
    pv_tv = tv_average / (1.0 + wacc) ** projection_years

    # Total before cap
    total_before_cap = pv_stage1 + pv_tv

    # Apply TV cap
    if total_before_cap > 0 and pv_tv / total_before_cap > terminal_value_cap:
        capped_tv = (pv_stage1 * terminal_value_cap) / (1.0 - terminal_value_cap)
        dcf_value = pv_stage1 + capped_tv
        return {
            "dcf_value": dcf_value,
            "projected_fcfs": tuple(projected_fcfs),
            "tv_gordon": tv_gordon,
            "tv_exit": tv_exit,
            "tv_average": tv_average,
            "tv_pct": terminal_value_cap,
            "tv_capped": True,
            "confidence_penalty": 0.2,
        }

    tv_pct = pv_tv / total_before_cap if total_before_cap > 0 else 0.0

    return {
        "dcf_value": total_before_cap,
        "projected_fcfs": tuple(projected_fcfs),
        "tv_gordon": tv_gordon,
        "tv_exit": tv_exit,
        "tv_average": tv_average,
        "tv_pct": tv_pct,
        "tv_capped": False,
        "confidence_penalty": 0.0,
    }
