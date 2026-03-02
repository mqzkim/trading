"""Self-improvement advisor: analyzes walk-forward results and suggests parameter adjustments."""
from dataclasses import dataclass, field
from typing import Optional
from core.backtest.walk_forward import WalkForwardResult
from core.backtest.metrics import PerformanceMetrics


@dataclass
class ImprovementAdvice:
    current_sharpe: float
    suggested_regime_weights: Optional[dict] = None
    suggested_risk_adjustment: Optional[float] = None
    recommendations: list[str] = field(default_factory=list)
    priority: str = "low"  # "low" | "medium" | "high"


def suggest_improvements(
    wf_result: WalkForwardResult,
    current_regime: str = "Transition",
) -> ImprovementAdvice:
    """Analyze walk-forward results and produce improvement advice.

    Rules:
        - Sharpe >= 1.5: high priority (good -- maintain params)
        - 1.0 <= Sharpe < 1.5: medium priority, minor adjustments
        - Sharpe < 1.0: high priority, aggressive adjustments needed
        - Overfitting score > 1.0: overfitting warning
        - Max drawdown < -0.25: reduce risk adjustment factor

    Args:
        wf_result: Walk-forward backtest result.
        current_regime: Current market regime label.

    Returns:
        ImprovementAdvice with suggestions.
    """
    oos_sharpe = wf_result.oos_metrics.sharpe_ratio
    oos_max_dd = wf_result.oos_metrics.max_drawdown
    overfitting = wf_result.overfitting_score

    recommendations: list[str] = []
    suggested_regime_weights: Optional[dict] = None
    suggested_risk_adjustment: Optional[float] = None
    priority = "low"

    # 1. OOS Sharpe analysis
    if oos_sharpe >= 1.5:
        priority = "high"
        recommendations.append(
            f"OOS Sharpe {oos_sharpe:.2f} is excellent. Maintain current parameters."
        )
    elif 1.0 <= oos_sharpe < 1.5:
        priority = "medium"
        suggested_risk_adjustment = 0.7
        recommendations.append(
            f"OOS Sharpe {oos_sharpe:.2f} is adequate. Consider minor parameter tuning."
        )
    elif 0.5 <= oos_sharpe < 1.0:
        priority = "high"
        suggested_risk_adjustment = 0.7
        recommendations.append(
            f"OOS Sharpe {oos_sharpe:.2f} is below target. "
            f"Retain current regime weights for '{current_regime}' but tighten risk."
        )
    else:
        # Sharpe < 0.5
        priority = "high"
        suggested_risk_adjustment = 0.5
        suggested_regime_weights = {
            "Bull": 0.25,
            "Bear": 0.25,
            "Sideways": 0.25,
            "Transition": 0.25,
        }
        recommendations.append(
            f"OOS Sharpe {oos_sharpe:.2f} is critically low. "
            "Reset regime weights to equal (0.25) and reduce risk exposure."
        )

    # 2. Overfitting check
    if overfitting > 1.0:
        recommendations.append(
            f"Overfitting score {overfitting:.2f} exceeds 1.0. "
            "IS performance significantly exceeds OOS -- reduce model complexity."
        )

    # 3. Max drawdown check
    if oos_max_dd < -0.25:
        dd_risk = (suggested_risk_adjustment or 1.0) * 0.8
        suggested_risk_adjustment = round(dd_risk, 2)
        recommendations.append(
            f"Max drawdown {oos_max_dd:.2%} exceeds -25% threshold. "
            f"Risk adjustment factor reduced to {suggested_risk_adjustment}."
        )

    return ImprovementAdvice(
        current_sharpe=oos_sharpe,
        suggested_regime_weights=suggested_regime_weights,
        suggested_risk_adjustment=suggested_risk_adjustment,
        recommendations=recommendations,
        priority=priority,
    )


def analyze_strategy_performance(trade_returns: list[float]) -> dict:
    """Summarize per-strategy performance from trade returns.

    Args:
        trade_returns: List of per-trade return values.

    Returns:
        Dict with win_rate, avg_return, and consistency (1 - normalized std).
    """
    if not trade_returns:
        return {"win_rate": 0.0, "avg_return": 0.0, "consistency": 0.0}

    winners = sum(1 for r in trade_returns if r > 0)
    win_rate = winners / len(trade_returns)
    avg_return = sum(trade_returns) / len(trade_returns)

    if len(trade_returns) < 2:
        consistency = 1.0
    else:
        std = (
            sum((r - avg_return) ** 2 for r in trade_returns)
            / (len(trade_returns) - 1)
        ) ** 0.5
        # Consistency: 1.0 means perfectly consistent, approaches 0 as std grows
        # Normalize by abs(avg_return) to make it scale-invariant
        if abs(avg_return) > 0:
            consistency = max(0.0, 1.0 - std / abs(avg_return))
        else:
            consistency = max(0.0, 1.0 - std)

    return {
        "win_rate": round(win_rate, 4),
        "avg_return": round(avg_return, 6),
        "consistency": round(consistency, 4),
    }
