"""CoreValuationAdapter -- DDD infrastructure adapter wrapping core valuation functions.

Bridges the DDD valuation bounded context with existing proven valuation logic
in core/valuation/. Does NOT rewrite valuation math -- only adapts interfaces.

Wrapped functions:
  core.valuation.dcf: compute_wacc, compute_dcf
  core.valuation.epv: compute_epv
  core.valuation.relative: compute_relative
  core.valuation.ensemble: compute_ensemble, compute_margin_of_safety
"""
from __future__ import annotations

from core.valuation.dcf import compute_wacc, compute_dcf
from core.valuation.epv import compute_epv
from core.valuation.relative import compute_relative
from core.valuation.ensemble import compute_ensemble, compute_margin_of_safety


class CoreValuationAdapter:
    """Infrastructure adapter wrapping core/valuation/ functions for DDD compliance.

    Each method delegates directly to the corresponding core function.
    No math rewriting -- adapter pattern only.
    """

    def compute_wacc(
        self,
        beta: float,
        risk_free_rate: float,
        equity_risk_premium: float,
        debt_to_equity: float,
        cost_of_debt: float,
        tax_rate: float,
    ) -> dict:
        """Compute WACC via CAPM. Delegates to core.valuation.dcf.compute_wacc."""
        return compute_wacc(
            beta=beta,
            risk_free_rate=risk_free_rate,
            equity_risk_premium=equity_risk_premium,
            debt_to_equity=debt_to_equity,
            cost_of_debt=cost_of_debt,
            tax_rate=tax_rate,
        )

    def compute_dcf(
        self,
        base_fcf: float,
        stage1_growth: float,
        stage2_growth: float,
        wacc: float,
        exit_multiple: float,
        projection_years: int = 5,
        terminal_value_cap: float = 0.40,
    ) -> dict:
        """2-stage DCF. Delegates to core.valuation.dcf.compute_dcf."""
        return compute_dcf(
            base_fcf=base_fcf,
            stage1_growth=stage1_growth,
            stage2_growth=stage2_growth,
            wacc=wacc,
            exit_multiple=exit_multiple,
            projection_years=projection_years,
            terminal_value_cap=terminal_value_cap,
        )

    def compute_epv(
        self,
        revenues: list[float],
        operating_margins: list[float],
        tax_rate: float,
        depreciation: float,
        wacc: float,
        shares_outstanding: float,
    ) -> dict:
        """Earnings Power Value. Delegates to core.valuation.epv.compute_epv."""
        return compute_epv(
            revenues=revenues,
            operating_margins=operating_margins,
            tax_rate=tax_rate,
            depreciation=depreciation,
            wacc=wacc,
            shares_outstanding=shares_outstanding,
        )

    def compute_relative(
        self,
        per: float,
        pbr: float,
        ev_ebitda: float,
        sector_pers: list[float],
        sector_pbrs: list[float],
        sector_ev_ebitdas: list[float],
    ) -> dict:
        """Relative multiples percentile. Delegates to core.valuation.relative.compute_relative."""
        return compute_relative(
            per=per,
            pbr=pbr,
            ev_ebitda=ev_ebitda,
            sector_pers=sector_pers,
            sector_pbrs=sector_pbrs,
            sector_ev_ebitdas=sector_ev_ebitdas,
        )

    def compute_ensemble(
        self,
        dcf_value: float,
        dcf_confidence: float,
        epv_value: float,
        epv_confidence: float,
        relative_value: float,
        relative_confidence: float,
    ) -> dict:
        """Confidence-weighted ensemble. Delegates to core.valuation.ensemble.compute_ensemble."""
        return compute_ensemble(
            dcf_value=dcf_value,
            dcf_confidence=dcf_confidence,
            epv_value=epv_value,
            epv_confidence=epv_confidence,
            relative_value=relative_value,
            relative_confidence=relative_confidence,
        )

    def compute_margin_of_safety(
        self,
        intrinsic_mid: float,
        market_price: float,
        sector: str,
    ) -> dict:
        """Sector-adjusted MoS. Delegates to core.valuation.ensemble.compute_margin_of_safety."""
        return compute_margin_of_safety(
            intrinsic_mid=intrinsic_mid,
            market_price=market_price,
            sector=sector,
        )
