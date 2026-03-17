"""Performance domain -- pure domain services.

BrinsonFachlerService: 4-level attribution decomposition.
ICCalculationService: Spearman IC per scoring axis.
KellyEfficiencyService: Kelly efficiency ratio.
compute_sortino: Sortino ratio (not in core/backtest/metrics.py).
"""
from __future__ import annotations

import math
from typing import Optional

from .entities import ClosedTrade
from .value_objects import AttributionLevel


class BrinsonFachlerService:
    """4-level Brinson-Fachler attribution.

    Levels:
      1. portfolio: total portfolio return vs benchmark (0 placeholder)
      2. strategy: swing vs position strategy contribution
      3. trade: individual trade quality vs strategy avg
      4. skill: IC-based signal quality per scoring axis
    """

    def compute(self, trades: list[ClosedTrade]) -> list[AttributionLevel]:
        zero = AttributionLevel
        if not trades:
            return [
                zero(name="portfolio", allocation_effect=0.0, selection_effect=0.0, interaction_effect=0.0, total_effect=0.0),
                zero(name="strategy", allocation_effect=0.0, selection_effect=0.0, interaction_effect=0.0, total_effect=0.0),
                zero(name="trade", allocation_effect=0.0, selection_effect=0.0, interaction_effect=0.0, total_effect=0.0),
                zero(name="skill", allocation_effect=0.0, selection_effect=0.0, interaction_effect=0.0, total_effect=0.0),
            ]

        # Level 1: Portfolio -- total return vs benchmark (0)
        avg_return = sum(t.pnl_pct for t in trades) / len(trades)
        portfolio_total = avg_return
        portfolio_level = zero(
            name="portfolio",
            allocation_effect=0.0,
            selection_effect=portfolio_total,
            interaction_effect=0.0,
            total_effect=portfolio_total,
        )

        # Level 2: Strategy -- group by strategy
        strategy_groups: dict[str, list[ClosedTrade]] = {}
        for t in trades:
            strategy_groups.setdefault(t.strategy, []).append(t)

        alloc_effect = 0.0
        select_effect = 0.0
        interact_effect = 0.0
        for strat, strat_trades in strategy_groups.items():
            w_p = len(strat_trades) / len(trades)
            w_b = 1.0 / max(len(strategy_groups), 1)
            r_p = sum(t.pnl_pct for t in strat_trades) / len(strat_trades)
            r_b = avg_return

            alloc_effect += (w_p - w_b) * r_b
            select_effect += w_b * (r_p - r_b)
            interact_effect += (w_p - w_b) * (r_p - r_b)

        strategy_total = alloc_effect + select_effect + interact_effect
        strategy_level = zero(
            name="strategy",
            allocation_effect=round(alloc_effect, 6),
            selection_effect=round(select_effect, 6),
            interaction_effect=round(interact_effect, 6),
            total_effect=round(strategy_total, 6),
        )

        # Level 3: Trade -- per-trade excess return vs strategy avg
        trade_select = 0.0
        for t in trades:
            strat_trades = strategy_groups.get(t.strategy, [t])
            strat_avg = sum(st.pnl_pct for st in strat_trades) / len(strat_trades)
            trade_select += (t.pnl_pct - strat_avg) / len(trades)

        trade_level = zero(
            name="trade",
            allocation_effect=0.0,
            selection_effect=round(trade_select, 6),
            interaction_effect=0.0,
            total_effect=round(trade_select, 6),
        )

        # Level 4: Skill -- IC-based signal quality
        scores = [t.composite_score for t in trades if t.composite_score is not None]
        if scores:
            avg_score = sum(scores) / len(scores)
            skill_alloc = (avg_score / 100.0) * avg_return if avg_score else 0.0
        else:
            skill_alloc = 0.0

        skill_level = zero(
            name="skill",
            allocation_effect=round(skill_alloc, 6),
            selection_effect=0.0,
            interaction_effect=0.0,
            total_effect=round(skill_alloc, 6),
        )

        return [portfolio_level, strategy_level, trade_level, skill_level]


class ICCalculationService:
    """Compute Information Coefficient per scoring axis."""

    MIN_TRADES_FOR_IC = 20

    def compute_axis_ic(
        self, trades: list[ClosedTrade], axis: str
    ) -> Optional[float]:
        """Spearman rank correlation between axis score and realized return.

        Args:
            trades: Closed trades with score snapshots.
            axis: "fundamental", "technical", or "sentiment".

        Returns:
            IC value or None if insufficient data / no variance.
        """
        if len(trades) < self.MIN_TRADES_FOR_IC:
            return None

        pairs = [
            (getattr(t, f"{axis}_score"), t.pnl_pct)
            for t in trades
            if getattr(t, f"{axis}_score", None) is not None
        ]
        if len(pairs) < self.MIN_TRADES_FOR_IC:
            return None

        scores_list = [p[0] for p in pairs]
        returns_list = [p[1] for p in pairs]

        if all(s == scores_list[0] for s in scores_list):
            return None

        from scipy.stats import spearmanr

        ic, _ = spearmanr(scores_list, returns_list)
        if math.isnan(ic):
            return None
        return round(float(ic), 4)


class KellyEfficiencyService:
    """Compute Kelly efficiency = actual geometric return / Kelly-optimal return."""

    def compute(self, trades: list[ClosedTrade]) -> Optional[float]:
        if len(trades) < 20:
            return None

        returns = [t.pnl_pct for t in trades]
        winners = [r for r in returns if r > 0]
        losers = [r for r in returns if r <= 0]

        if not winners or not losers:
            return None

        win_rate = len(winners) / len(returns)
        avg_win = sum(winners) / len(winners)
        avg_loss = abs(sum(losers) / len(losers))

        if avg_loss == 0:
            return None

        kelly_f = win_rate - (1 - win_rate) / (avg_win / avg_loss)
        if kelly_f <= 0:
            return 0.0

        kelly_growth = win_rate * math.log(1 + kelly_f * avg_win) + (
            1 - win_rate
        ) * math.log(1 - kelly_f * avg_loss)

        actual_f = kelly_f * 0.25
        actual_growth = win_rate * math.log(1 + actual_f * avg_win) + (
            1 - win_rate
        ) * math.log(1 - actual_f * avg_loss)

        if kelly_growth <= 0:
            return None

        efficiency = (actual_growth / kelly_growth) * 100
        return round(efficiency, 1)


def compute_sortino(returns: list[float]) -> Optional[float]:
    """Compute annualized Sortino ratio.

    Uses only downside returns for denominator.
    Returns None if insufficient data.
    """
    if len(returns) < 2:
        return None

    downside = [r for r in returns if r < 0]
    if not downside:
        return None

    import numpy as np

    mean_r = float(np.mean(returns))
    downside_dev = float(np.std(downside))
    if downside_dev == 0:
        return None

    return round(mean_r / downside_dev * (252**0.5), 4)
