"""Backtest domain -- Domain Services.

BacktestValidationService computes profit factor (new domain logic)
and enriches core PerformanceMetrics with it to produce PerformanceReport VO.
"""
from __future__ import annotations

from .value_objects import PerformanceReport


class BacktestValidationService:
    """Computes profit factor and enriches core metrics into PerformanceReport."""

    def compute_profit_factor(self, trade_returns: list[float]) -> float:
        """Compute profit factor = gross_profit / abs(gross_loss).

        Edge cases:
        - No trades or all-zero returns: 0.0
        - No losses but has profit: inf
        - No profits: 0.0
        """
        if not trade_returns:
            return 0.0

        gross_profit = sum(r for r in trade_returns if r > 0)
        gross_loss = sum(r for r in trade_returns if r < 0)

        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        if gross_profit == 0:
            return 0.0

        return gross_profit / abs(gross_loss)

    def enrich_metrics(
        self, core_metrics: dict, trade_returns: list[float]
    ) -> PerformanceReport:
        """Add profit_factor to core 7-field metrics dict, return PerformanceReport VO."""
        profit_factor = self.compute_profit_factor(trade_returns)
        return PerformanceReport(
            cagr=core_metrics["cagr"],
            sharpe_ratio=core_metrics["sharpe_ratio"],
            max_drawdown=core_metrics["max_drawdown"],
            win_rate=core_metrics["win_rate"],
            total_return=core_metrics["total_return"],
            num_trades=core_metrics["num_trades"],
            avg_return_per_trade=core_metrics["avg_return_per_trade"],
            profit_factor=profit_factor,
        )
