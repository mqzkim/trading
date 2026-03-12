"""Infrastructure adapter wrapping core/signals/ evaluators for DDD signals context.

Thin wrapper -- no math rewriting. Delegates to core/signals/*.evaluate() functions.
"""
from __future__ import annotations

from core.signals.canslim import evaluate as canslim_evaluate
from core.signals.magic_formula import evaluate as magic_evaluate
from core.signals.dual_momentum import evaluate as dual_evaluate
from core.signals.trend_following import evaluate as trend_evaluate


class CoreSignalAdapter:
    """Wraps core/signals/ evaluators for DDD signals context.

    Each method delegates directly to the corresponding core/signals/*.evaluate()
    function. No math is rewritten -- adapter pattern only.
    """

    def evaluate_canslim(self, **kwargs) -> dict:
        """Evaluate CAN SLIM 7-criteria."""
        return canslim_evaluate(**kwargs)

    def evaluate_magic_formula(self, **kwargs) -> dict:
        """Evaluate Magic Formula (Earnings Yield + ROC)."""
        return magic_evaluate(**kwargs)

    def evaluate_dual_momentum(self, **kwargs) -> dict:
        """Evaluate Dual Momentum (absolute + relative)."""
        return dual_evaluate(**kwargs)

    def evaluate_trend_following(self, **kwargs) -> dict:
        """Evaluate Trend Following (MA cross, ADX, breakout)."""
        return trend_evaluate(**kwargs)

    def evaluate_all(self, symbol_data: dict) -> list[dict]:
        """Run all 4 evaluators with appropriate kwargs extracted from symbol_data.

        Args:
            symbol_data: dict containing all input fields for the 4 evaluators.

        Returns:
            List of 4 result dicts, one per methodology.
        """
        canslim = self.evaluate_canslim(
            eps_growth_qoq=symbol_data.get("eps_growth_qoq"),
            eps_cagr_3y=symbol_data.get("eps_cagr_3y"),
            near_52w_high=symbol_data.get("near_52w_high", False),
            volume_ratio=symbol_data.get("volume_ratio", 1.0),
            relative_strength=symbol_data.get("relative_strength", 50),
            institutional_increase=symbol_data.get("institutional_increase", False),
            market_uptrend=symbol_data.get("market_uptrend", True),
        )

        magic = self.evaluate_magic_formula(
            earnings_yield=symbol_data.get("earnings_yield"),
            return_on_capital=symbol_data.get("return_on_capital"),
            ey_percentile=symbol_data.get("ey_percentile", 50.0),
            roc_percentile=symbol_data.get("roc_percentile", 50.0),
        )

        dual = self.evaluate_dual_momentum(
            return_12m=symbol_data.get("return_12m"),
            return_12m_benchmark=symbol_data.get("return_12m_benchmark"),
            tbill_rate=symbol_data.get("tbill_rate", 0.04),
        )

        trend = self.evaluate_trend_following(
            above_ma50=symbol_data.get("above_ma50", False),
            above_ma200=symbol_data.get("above_ma200", False),
            adx=symbol_data.get("adx", 15.0),
            at_20d_high=symbol_data.get("at_20d_high", False),
        )

        return [canslim, magic, dual, trend]
