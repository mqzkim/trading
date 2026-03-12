"""Fundamental scoring: F-Score, Z-Score, M-Score, G-Score, composite."""
import math
from typing import Any
from .safety import altman_z_score, beneish_m_score, check_safety


def piotroski_f_score(h: dict[str, Any]) -> int:
    """
    Piotroski F-Score (0-9).
    Uses 'highlights' dict from DataClient.get_fundamentals().
    Proxies where direct data unavailable via yfinance.
    """
    score = 0

    # Profitability (4 points)
    roa = h.get("roa") or 0.0
    if roa > 0:
        score += 1  # F1: ROA > 0
    fcf = h.get("fcf") or 0.0
    if fcf > 0:
        score += 1  # F3: CFO > 0
    if roa > 0:
        score += 1  # F4: delta ROA > 0 (proxy: positive ROA)
    if fcf > 0 and roa > 0 and (fcf / max(abs(roa), 1e-9)) > 0:
        score += 1  # F5: accrual (CFO > ROA proxy)

    # Leverage / Liquidity (3 points)
    debt_to_equity = h.get("debt_to_equity") or 0.0
    current_ratio = h.get("current_ratio") or 0.0
    if debt_to_equity < 1.0:
        score += 1  # F6: lower leverage
    if current_ratio > 1.0:
        score += 1  # F7: higher liquidity
    # F8: no dilution (proxy: skip, assume no new shares)
    score += 1  # F8 proxy: give benefit of doubt

    # Operating Efficiency (2 points)
    roe = h.get("roe") or 0.0
    if roe > 0:
        score += 1  # F9: higher gross margin proxy
    revenue = h.get("revenue") or 0
    market_cap = h.get("market_cap") or 1
    if revenue > 0 and market_cap > 0:
        score += 1  # F10: higher asset turnover proxy

    return min(score, 9)


def mohanram_g_score(
    roa: float,
    cfo_to_assets: float,
    cfo: float,
    net_income: float,
    roa_variance: float,
    sales_growth_variance: float,
    rd_to_assets: float,
    capex_to_assets: float,
    ad_to_assets: float,
    sector_median_roa: float,
    sector_median_cfo_to_assets: float,
    sector_median_roa_variance: float,
    sector_median_sales_growth_variance: float,
    sector_median_rd_to_assets: float,
    sector_median_capex_to_assets: float,
    sector_median_ad_to_assets: float,
) -> int:
    """Mohanram G-Score (0-8) for growth stock quality.

    Returns integer score 0-8. Higher = better growth quality.
    Only meaningful for growth stocks (PBR > 3).

    Criteria:
      G1: ROA > sector median
      G2: CFO/Assets > sector median
      G3: CFO > net income (earnings quality)
      G4: ROA variance < sector median (stability)
      G5: Sales growth variance < sector median (stability)
      G6: R&D/Assets > sector median (growth investment)
      G7: CapEx/Assets > sector median (growth investment)
      G8: Advertising/Assets > sector median (growth investment)

    Reference: Mohanram (2004)
    """
    score = 0

    # Profitability (3 points)
    if roa > sector_median_roa:
        score += 1  # G1
    if cfo_to_assets > sector_median_cfo_to_assets:
        score += 1  # G2
    if cfo > net_income:
        score += 1  # G3

    # Earnings stability (2 points) -- LOWER variance is better
    if roa_variance < sector_median_roa_variance:
        score += 1  # G4
    if sales_growth_variance < sector_median_sales_growth_variance:
        score += 1  # G5

    # Growth investment / accounting conservatism (3 points)
    if rd_to_assets > sector_median_rd_to_assets:
        score += 1  # G6
    if capex_to_assets > sector_median_capex_to_assets:
        score += 1  # G7
    if ad_to_assets > sector_median_ad_to_assets:
        score += 1  # G8

    return score


def _safe(v: Any, default: float = 0.0) -> float:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def compute_fundamental_score(highlights: dict, valuation: dict) -> dict:
    """
    Compute fundamental sub-scores and composite (0-100).
    Returns dict with all component scores.
    """
    h = highlights or {}
    v = valuation or {}

    # --- Safety Filters ---
    market_cap = _safe(h.get("market_cap"), 1e9)
    revenue = _safe(h.get("revenue"), 1)
    net_income = _safe(h.get("net_income"), 0)
    debt_to_equity = _safe(h.get("debt_to_equity"), 1)
    current_ratio = _safe(h.get("current_ratio"), 1)
    roa = _safe(h.get("roa"), 0)
    roe = _safe(h.get("roe"), 0)
    fcf = _safe(h.get("fcf"), 0)
    pe = _safe(h.get("pe_ratio"), 20)
    pb = _safe(v.get("pb"), 3)

    # Altman Z-Score proxies
    working_capital = (current_ratio - 1) * (market_cap * 0.1)  # rough proxy
    total_assets = market_cap * 0.8  # rough proxy
    retained_earnings = net_income * 3  # rough proxy (3 years)
    ebit = net_income * 1.3  # rough proxy (add back taxes)
    total_liabilities = debt_to_equity * market_cap * 0.5

    z = altman_z_score(working_capital, total_assets, retained_earnings,
                       ebit, market_cap, total_liabilities, revenue)

    # Beneish M-Score (use neutral values as proxy when quarterly data unavailable)
    m = beneish_m_score(1.0, 1.0, 1.0, max(1.0, revenue / max(revenue * 0.9, 1)),
                        1.0, 1.0, 1.0, max(-0.1, min(0.1, net_income / max(total_assets, 1))))

    safety = check_safety(z, m)

    if not safety["safety_passed"]:
        return {
            **safety,
            "f_score": 0,
            "value_score": 0,
            "quality_score": 0,
            "fundamental_score": 0,
        }

    # --- Sub-scores (0-100) ---
    # F-Score (Piotroski)
    f_raw = piotroski_f_score(h)
    f_score_normalized = (f_raw / 9) * 100

    # Value score: lower PE/PB is better. Cap PE at 50, PB at 10.
    pe_clamped = max(1, min(pe, 50))
    pb_clamped = max(0.1, min(pb, 10))
    value_score = (1 - (pe_clamped - 1) / 49) * 50 + (1 - (pb_clamped - 0.1) / 9.9) * 50

    # Quality score: ROE + ROA
    roe_score = min(100, max(0, roe * 200))   # 50% ROE -> 100
    roa_score = min(100, max(0, roa * 500))   # 20% ROA -> 100
    quality_score = (roe_score + roa_score) / 2

    # Composite: 40% F-score + 30% value + 30% quality
    composite = 0.4 * f_score_normalized + 0.3 * value_score + 0.3 * quality_score
    composite = max(0, min(100, composite))

    return {
        **safety,
        "f_score": f_raw,
        "f_score_normalized": round(f_score_normalized, 1),
        "value_score": round(value_score, 1),
        "quality_score": round(quality_score, 1),
        "fundamental_score": round(composite, 1),
    }
