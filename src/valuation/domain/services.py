"""Valuation domain services.

EnsembleValuationService orchestrates DCF + EPV + Relative models
into a confidence-weighted intrinsic value estimate with margin of safety.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.valuation.infrastructure.core_valuation_adapter import CoreValuationAdapter


class EnsembleValuationService:
    """Orchestrates the full valuation pipeline: DCF + EPV + Relative -> Ensemble -> MoS.

    Accepts CoreValuationAdapter via dependency injection.
    Extracts per-share values, computes model-specific confidence,
    then delegates ensemble and MoS computation to the adapter.
    """

    def __init__(self, adapter: CoreValuationAdapter) -> None:
        self._adapter = adapter

    def valuate(
        self,
        dcf_result: dict,
        epv_result: dict,
        relative_result: dict,
        market_price: float,
        shares_outstanding: float,
        sector: str,
    ) -> dict:
        """Run full valuation pipeline: extract values, compute ensemble, compute MoS.

        Args:
            dcf_result: Output from adapter.compute_dcf().
            epv_result: Output from adapter.compute_epv().
            relative_result: Output from adapter.compute_relative().
            market_price: Current market price per share.
            shares_outstanding: Total shares outstanding.
            sector: GICS sector name.

        Returns:
            Dict with ensemble results, margin of safety, and all intermediate values.
        """
        # Step 1: Extract per-share values
        dcf_total = dcf_result.get("dcf_value", 0.0)
        dcf_per_share = dcf_total / shares_outstanding if shares_outstanding > 0 else 0.0

        epv_per_share = epv_result.get("epv_per_share", 0.0)

        # Step 2: Convert relative percentile to estimated value
        # Stocks below median (percentile < 50) are undervalued relative to peers
        composite_percentile = relative_result.get("composite_percentile")
        if composite_percentile is not None:
            relative_value = market_price * (1.0 + (50.0 - composite_percentile) / 100.0)
        else:
            relative_value = 0.0

        # Step 3: Compute per-model confidence
        # DCF: 1.0 - confidence_penalty, further reduced if dcf_value <= 0
        dcf_confidence_penalty = dcf_result.get("confidence_penalty", 0.0)
        dcf_confidence = 1.0 - dcf_confidence_penalty
        if dcf_total <= 0:
            dcf_confidence = 0.0

        # EPV: 1.0 if earnings_cv < 0.5, else 0.5 (cyclical stock penalty)
        earnings_cv = epv_result.get("earnings_cv")
        if earnings_cv is not None and earnings_cv >= 0.5:
            epv_confidence = 0.5
        else:
            epv_confidence = 1.0
        # Zero EPV means no confidence
        if epv_per_share <= 0:
            epv_confidence = 0.0

        # Relative: 1.0 if composite_percentile available and peer_count >= 5, else 0.3
        peer_count = relative_result.get("peer_count", 0)
        if composite_percentile is not None and peer_count >= 5:
            relative_confidence = 1.0
        else:
            relative_confidence = 0.3
        # Zero relative value means no confidence
        if relative_value <= 0:
            relative_confidence = 0.0

        # Step 4: Compute ensemble
        ensemble = self._adapter.compute_ensemble(
            dcf_value=dcf_per_share,
            dcf_confidence=dcf_confidence,
            epv_value=epv_per_share,
            epv_confidence=epv_confidence,
            relative_value=relative_value,
            relative_confidence=relative_confidence,
        )

        # Step 5: Compute margin of safety
        intrinsic_value = ensemble["intrinsic_value"]
        mos = self._adapter.compute_margin_of_safety(
            intrinsic_mid=intrinsic_value,
            market_price=market_price,
            sector=sector,
        )

        return {
            "dcf_per_share": dcf_per_share,
            "epv_per_share": epv_per_share,
            "relative_value": relative_value,
            "dcf_confidence": dcf_confidence,
            "epv_confidence": epv_confidence,
            "relative_confidence": relative_confidence,
            "intrinsic_value": ensemble["intrinsic_value"],
            "confidence": ensemble["confidence"],
            "effective_weights": ensemble["effective_weights"],
            "model_agreement": ensemble["model_agreement"],
            "data_completeness": ensemble["data_completeness"],
            "margin_of_safety": mos["margin_of_safety"],
            "sector_threshold": mos["sector_threshold"],
            "has_margin": mos["has_margin"],
            "sector": sector,
        }
