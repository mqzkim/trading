"""Self-improver domain -- ImprovementAdvisorService.

Migrated from personal/self_improver/advisor.py into DDD domain service.
Generates weight adjustment proposals based on walk-forward results.
Only proposes scoring axis weight changes (fundamental/technical/sentiment).
"""
from __future__ import annotations

from uuid import uuid4

from core.backtest.walk_forward import WalkForwardResult
from personal.self_improver.domain.value_objects import WeightProposal


# Default weights when no regime-specific weights are available
_DEFAULT_WEIGHTS: dict[str, float] = {
    "fundamental": 0.40,
    "technical": 0.35,
    "sentiment": 0.25,
}

_ALLOWED_AXES = ("fundamental", "technical", "sentiment")


class ImprovementAdvisorService:
    """Analyzes walk-forward results and generates scoring weight proposals.

    Rules:
    - Sharpe >= 1.0 AND overfitting <= 1.0: no proposals (system performing well)
    - Sharpe < 0.5: propose equalizing weights to 1/3 per axis
    - 0.5 <= Sharpe < 1.0: shift 5% from weakest to strongest axis
    - Overfitting > 1.0: propose reducing fundamental weight by 5%
    """

    def suggest(
        self,
        wf_result: WalkForwardResult,
        current_weights: dict[str, dict[str, float]] | None = None,
        current_regime: str = "Transition",
    ) -> list[WeightProposal]:
        """Generate weight proposals from walk-forward validation results.

        Args:
            wf_result: Walk-forward backtest result with OOS metrics.
            current_weights: Per-regime weight dict, e.g.
                {"Bull": {"fundamental": 0.35, ...}, ...}
            current_regime: Current market regime label.

        Returns:
            List of WeightProposal (may be empty if system is performing well).
        """
        oos_sharpe = wf_result.oos_metrics.sharpe_ratio
        overfitting = wf_result.overfitting_score

        # No proposals if performing well
        if oos_sharpe >= 1.0 and overfitting <= 1.0:
            return []

        # Get current weights for the regime
        weights = _DEFAULT_WEIGHTS.copy()
        if current_weights and current_regime in current_weights:
            regime_w = current_weights[current_regime]
            # Only use scoring axis weights
            for axis in _ALLOWED_AXES:
                if axis in regime_w:
                    weights[axis] = regime_w[axis]

        proposals: list[WeightProposal] = []

        if oos_sharpe < 0.5:
            # Equalize weights to 1/3 each
            equal_w = round(1.0 / 3, 4)
            for axis in _ALLOWED_AXES:
                if abs(weights[axis] - equal_w) > 0.001:
                    proposals.append(
                        WeightProposal(
                            id=str(uuid4()),
                            regime=current_regime,
                            axis=axis,
                            current_weight=weights[axis],
                            proposed_weight=equal_w,
                            walk_forward_sharpe=round(oos_sharpe, 4),
                        )
                    )
        elif oos_sharpe < 1.0:
            # Shift 5% from weakest to strongest axis
            sorted_axes = sorted(_ALLOWED_AXES, key=lambda a: weights[a])
            weakest = sorted_axes[0]
            strongest = sorted_axes[-1]

            if weights[weakest] >= 0.05:
                proposals.append(
                    WeightProposal(
                        id=str(uuid4()),
                        regime=current_regime,
                        axis=weakest,
                        current_weight=weights[weakest],
                        proposed_weight=round(weights[weakest] - 0.05, 4),
                        walk_forward_sharpe=round(oos_sharpe, 4),
                    )
                )
                proposals.append(
                    WeightProposal(
                        id=str(uuid4()),
                        regime=current_regime,
                        axis=strongest,
                        current_weight=weights[strongest],
                        proposed_weight=round(weights[strongest] + 0.05, 4),
                        walk_forward_sharpe=round(oos_sharpe, 4),
                    )
                )

        # Overfitting check: reduce fundamental weight by 5%
        if overfitting > 1.0 and weights["fundamental"] >= 0.05:
            # Avoid duplicate if fundamental already proposed
            already_proposed = {p.axis for p in proposals}
            if "fundamental" not in already_proposed:
                proposals.append(
                    WeightProposal(
                        id=str(uuid4()),
                        regime=current_regime,
                        axis="fundamental",
                        current_weight=weights["fundamental"],
                        proposed_weight=round(weights["fundamental"] - 0.05, 4),
                        walk_forward_sharpe=round(oos_sharpe, 4),
                    )
                )

        return proposals
