"""CoreScoringAdapter -- DDD infrastructure adapter wrapping core scoring functions.

Bridges the DDD scoring bounded context with existing proven scoring logic
in core/scoring/. Does NOT rewrite scoring math -- only adapts interfaces.

Wrapped functions:
  core.scoring.safety: altman_z_score, beneish_m_score
  core.scoring.fundamental: piotroski_f_score, compute_fundamental_score
"""
from __future__ import annotations

from typing import Any

from core.scoring.safety import altman_z_score, beneish_m_score
from core.scoring.fundamental import piotroski_f_score, compute_fundamental_score, mohanram_g_score

from src.scoring.domain.value_objects import SafetyGate


class CoreScoringAdapter:
    """Infrastructure adapter wrapping core/scoring/ functions for DDD compliance.

    This adapter translates between DDD-style dict inputs and the positional
    arguments expected by core scoring functions. It also maps results to
    domain Value Objects (SafetyGate).
    """

    def compute_altman_z(self, financial_data: dict[str, Any]) -> float:
        """Compute Altman Z-Score from financial data dict.

        Args:
            financial_data: Dict with keys: working_capital, total_assets,
                retained_earnings, ebit, market_cap, total_liabilities, revenue.

        Returns:
            Float Z-Score. > 1.81 = safe zone, < 1.81 = distress zone.
        """
        return altman_z_score(
            working_capital=financial_data.get("working_capital", 0.0),
            total_assets=financial_data.get("total_assets", 0.0),
            retained_earnings=financial_data.get("retained_earnings", 0.0),
            ebit=financial_data.get("ebit", 0.0),
            market_cap=financial_data.get("market_cap", 0.0),
            total_liabilities=financial_data.get("total_liabilities", 0.0),
            revenue=financial_data.get("revenue", 0.0),
        )

    def compute_beneish_m(
        self, current: dict[str, Any], previous: dict[str, Any]
    ) -> float:
        """Compute Beneish M-Score from current and previous period data.

        Calculates the 8 M-Score input ratios from two periods,
        then delegates to core.scoring.safety.beneish_m_score().

        Args:
            current: Current period financials (receivables, revenue, etc.)
            previous: Previous period financials.

        Returns:
            Float M-Score. < -1.78 = clean, > -1.78 = possible manipulation.
        """

        def _safe_div(numerator: float, denominator: float, default: float = 1.0) -> float:
            if denominator == 0:
                return default
            return numerator / denominator

        # Extract current period
        recv_c = float(current.get("receivables", 0))
        rev_c = float(current.get("revenue", 1))
        gp_c = float(current.get("gross_profit", rev_c * 0.4))
        ta_c = float(current.get("total_assets", 1))
        ppe_c = float(current.get("ppe", ta_c * 0.3))
        depr_c = float(current.get("depreciation", ppe_c * 0.1))
        sga_c = float(current.get("sga", rev_c * 0.2))
        tl_c = float(current.get("total_liabilities", ta_c * 0.5))
        ni_c = float(current.get("net_income", 0))
        ocf_c = float(current.get("operating_cashflow", ni_c))

        # Extract previous period
        recv_p = float(previous.get("receivables", recv_c))
        rev_p = float(previous.get("revenue", rev_c))
        gp_p = float(previous.get("gross_profit", rev_p * 0.4))
        ta_p = float(previous.get("total_assets", ta_c))
        ppe_p = float(previous.get("ppe", ta_p * 0.3))
        depr_p = float(previous.get("depreciation", ppe_p * 0.1))
        sga_p = float(previous.get("sga", rev_p * 0.2))
        tl_p = float(previous.get("total_liabilities", ta_p * 0.5))

        # Calculate 8 M-Score input ratios
        # DSRI: Days Sales Receivable Index
        dsri = _safe_div(recv_c / max(rev_c, 1), recv_p / max(rev_p, 1))

        # GMI: Gross Margin Index
        gm_c = _safe_div(gp_c, rev_c, 0.4)
        gm_p = _safe_div(gp_p, rev_p, 0.4)
        gmi = _safe_div(gm_p, gm_c)

        # AQI: Asset Quality Index
        aq_c = 1.0 - _safe_div(ppe_c + ta_c * 0.1, ta_c, 0.5)
        aq_p = 1.0 - _safe_div(ppe_p + ta_p * 0.1, ta_p, 0.5)
        aqi = _safe_div(aq_c, aq_p)

        # SGI: Sales Growth Index
        sgi = _safe_div(rev_c, rev_p)

        # DEPI: Depreciation Index
        depr_rate_c = _safe_div(depr_c, depr_c + ppe_c, 0.1)
        depr_rate_p = _safe_div(depr_p, depr_p + ppe_p, 0.1)
        depi = _safe_div(depr_rate_p, depr_rate_c)

        # SGAI: SGA Expense Index
        sga_ratio_c = _safe_div(sga_c, rev_c, 0.2)
        sga_ratio_p = _safe_div(sga_p, rev_p, 0.2)
        sgai = _safe_div(sga_ratio_c, sga_ratio_p)

        # LVGI: Leverage Index
        lev_c = _safe_div(tl_c, ta_c, 0.5)
        lev_p = _safe_div(tl_p, ta_p, 0.5)
        lvgi = _safe_div(lev_c, lev_p)

        # TATA: Total Accruals to Total Assets
        tata = _safe_div(ni_c - ocf_c, ta_c, 0.0)

        return beneish_m_score(dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata)

    def compute_piotroski_f(self, highlights: dict[str, Any]) -> int:
        """Compute Piotroski F-Score (0-9) from highlights dict.

        Args:
            highlights: Dict with keys: roa, fcf, debt_to_equity,
                current_ratio, roe, revenue, market_cap.

        Returns:
            Integer 0-9. Higher = stronger fundamentals.
        """
        return piotroski_f_score(highlights)

    def check_safety_gate(self, z_score: float, m_score: float) -> SafetyGate:
        """Create SafetyGate VO from Z-Score and M-Score.

        Args:
            z_score: Altman Z-Score value.
            m_score: Beneish M-Score value.

        Returns:
            SafetyGate VO with .passed property checking:
            Z > 1.81 AND M < -1.78
        """
        return SafetyGate(z_score=z_score, m_score=m_score)

    def compute_mohanram_g(self, data: dict[str, Any]) -> int:
        """Compute Mohanram G-Score (0-8) from financial data dict.

        Args:
            data: Dict with keys: roa, cfo_to_assets, cfo, net_income,
                roa_variance, sales_growth_variance, rd_to_assets,
                capex_to_assets, ad_to_assets, and sector_median_* versions.
                Missing R&D/advertising/capex default to 0.0 (conservative).

        Returns:
            Integer 0-8. Higher = better growth quality.
        """
        return mohanram_g_score(
            roa=data.get("roa", 0.0),
            cfo_to_assets=data.get("cfo_to_assets", 0.0),
            cfo=data.get("cfo", 0.0),
            net_income=data.get("net_income", 0.0),
            roa_variance=data.get("roa_variance", 0.0),
            sales_growth_variance=data.get("sales_growth_variance", 0.0),
            rd_to_assets=data.get("rd_to_assets", 0.0),
            capex_to_assets=data.get("capex_to_assets", 0.0),
            ad_to_assets=data.get("ad_to_assets", 0.0),
            sector_median_roa=data.get("sector_median_roa", 0.0),
            sector_median_cfo_to_assets=data.get("sector_median_cfo_to_assets", 0.0),
            sector_median_roa_variance=data.get("sector_median_roa_variance", 0.0),
            sector_median_sales_growth_variance=data.get("sector_median_sales_growth_variance", 0.0),
            sector_median_rd_to_assets=data.get("sector_median_rd_to_assets", 0.0),
            sector_median_capex_to_assets=data.get("sector_median_capex_to_assets", 0.0),
            sector_median_ad_to_assets=data.get("sector_median_ad_to_assets", 0.0),
        )

    def compute_full_fundamental(
        self, highlights: dict[str, Any], valuation: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute full fundamental score including safety + sub-scores.

        Delegates to core.scoring.fundamental.compute_fundamental_score().

        Args:
            highlights: Company financial highlights.
            valuation: Valuation metrics (pb, ev_ebitda, etc.)

        Returns:
            Dict with safety_passed, f_score, value_score, quality_score,
            fundamental_score (composite 0-100).
        """
        return compute_fundamental_score(highlights, valuation)
