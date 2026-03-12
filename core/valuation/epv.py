"""EPV valuation model -- pure math, no external dependencies.

Earnings Power Value (Greenwald method):
  EPV = Adjusted Earnings / WACC
  Adjusted Earnings = NOPAT + Depreciation - Maintenance CapEx
  Maintenance CapEx = Depreciation * 1.1 (standard proxy)
  Normalized margin = 5-year average operating margin

References:
- Bruce Greenwald, "Value Investing: From Graham to Buffett and Beyond"
- https://www.wallstreetprep.com/knowledge/earnings-power-value-epv/
- https://stablebread.com/earnings-power-value/
"""
from __future__ import annotations

import math


def compute_epv(
    revenues: list[float],
    operating_margins: list[float],
    tax_rate: float,
    depreciation: float,
    wacc: float,
    shares_outstanding: float,
) -> dict:
    """Earnings Power Value (Greenwald method).

    Uses 5-year averaged operating margin applied to most recent revenue.
    Calculates coefficient of variation of annual earnings for cyclical detection.
    """
    # Guard: zero or negative WACC
    if wacc <= 0:
        return {
            "epv_total": 0.0,
            "epv_per_share": 0.0,
            "normalized_margin": 0.0,
            "adjusted_earnings": 0.0,
            "earnings_cv": None,
            "confidence": 0,
        }

    # Step 1: Normalize operating margin (5-year average)
    if operating_margins:
        normalized_margin = sum(operating_margins) / len(operating_margins)
    else:
        normalized_margin = 0.10  # conservative default

    # Step 2: Apply to most recent revenue
    if revenues:
        normalized_ebit = revenues[-1] * normalized_margin
    else:
        normalized_ebit = 0.0

    # Step 3: After-tax earnings (NOPAT)
    nopat = normalized_ebit * (1.0 - tax_rate)

    # Step 4: Maintenance CapEx proxy
    maintenance_capex = depreciation * 1.1

    # Step 5: Adjusted earnings
    adjusted_earnings = nopat + depreciation - maintenance_capex

    # Step 6: EPV
    epv_total = adjusted_earnings / wacc

    # Step 7: Per-share
    if shares_outstanding > 0:
        epv_per_share = epv_total / shares_outstanding
    else:
        epv_per_share = 0.0

    # Step 8: Coefficient of variation of annual earnings (cyclical detection)
    earnings_cv = None
    if revenues and operating_margins and len(revenues) == len(operating_margins):
        annual_earnings = [
            rev * margin * (1.0 - tax_rate)
            for rev, margin in zip(revenues, operating_margins)
        ]
        if len(annual_earnings) >= 2:
            mean_e = sum(annual_earnings) / len(annual_earnings)
            if mean_e != 0:
                variance = sum((e - mean_e) ** 2 for e in annual_earnings) / len(annual_earnings)
                std_e = math.sqrt(variance)
                earnings_cv = std_e / abs(mean_e)

    return {
        "epv_total": epv_total,
        "epv_per_share": epv_per_share,
        "normalized_margin": normalized_margin,
        "adjusted_earnings": adjusted_earnings,
        "earnings_cv": earnings_cv,
    }
