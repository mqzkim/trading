"""Safety filters: Altman Z-Score and Beneish M-Score hard gates."""
import math


def altman_z_score(
    working_capital: float,
    total_assets: float,
    retained_earnings: float,
    ebit: float,
    market_cap: float,
    total_liabilities: float,
    revenue: float,
) -> float:
    """
    Altman Z-Score (public company version).
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    where:
      X1 = Working Capital / Total Assets
      X2 = Retained Earnings / Total Assets
      X3 = EBIT / Total Assets
      X4 = Market Cap / Total Liabilities
      X5 = Revenue / Total Assets
    """
    if total_assets == 0:
        return float("nan")
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / max(total_liabilities, 1)
    x5 = revenue / total_assets
    return 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5


def beneish_m_score(
    dsri: float,   # Days Sales Receivable Index
    gmi: float,    # Gross Margin Index
    aqi: float,    # Asset Quality Index
    sgi: float,    # Sales Growth Index
    depi: float,   # Depreciation Index
    sgai: float,   # SGA Expense Index
    lvgi: float,   # Leverage Index
    tata: float,   # Total Accruals to Total Assets
) -> float:
    """
    Beneish M-Score (8-variable model).
    M = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
        + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    M > -1.78 -> possible manipulation
    """
    return (
        -4.84
        + 0.920 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.679 * tata
        - 0.327 * lvgi
    )


ALTMAN_THRESHOLD = 1.81   # below = distress zone
BENEISH_THRESHOLD = -1.78  # above = possible manipulation


def check_safety(z_score: float, m_score: float) -> dict:
    """
    Returns safety gate result.
    Both conditions must pass for safety_passed=True.
    """
    z_pass = (not math.isnan(z_score)) and z_score > ALTMAN_THRESHOLD
    m_pass = (not math.isnan(m_score)) and m_score < BENEISH_THRESHOLD
    return {
        "safety_passed": z_pass and m_pass,
        "z_score": z_score,
        "z_pass": z_pass,
        "m_score": m_score,
        "m_pass": m_pass,
    }
