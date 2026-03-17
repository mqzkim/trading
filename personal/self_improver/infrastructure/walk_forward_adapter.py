"""Self-improver infrastructure -- walk-forward adapter.

Wraps core/backtest/walk_forward.py for use by the self-improver application layer.
"""
from __future__ import annotations

import pandas as pd

from core.backtest.walk_forward import WalkForwardResult, run_walk_forward


class WalkForwardAdapter:
    """Adapter that runs walk-forward validation on trade return series.

    Converts a flat list of trade returns into the OHLCV + signals format
    expected by run_walk_forward, using a synthetic price series.
    """

    def run(self, trade_returns: list[float]) -> WalkForwardResult:
        """Run walk-forward validation on trade returns.

        Args:
            trade_returns: List of per-trade PnL percentages.

        Returns:
            WalkForwardResult with OOS/IS metrics and overfitting score.
        """
        # Build synthetic OHLCV from cumulative returns
        equity = [1.0]
        for r in trade_returns:
            equity.append(equity[-1] * (1 + r))

        dates = pd.date_range("2020-01-01", periods=len(equity), freq="B")
        prices = pd.Series(equity, index=dates)

        ohlcv_df = pd.DataFrame(
            {
                "Open": prices,
                "High": prices * 1.01,
                "Low": prices * 0.99,
                "Close": prices,
                "Volume": 1000,
            },
            index=dates,
        )

        # Generate synthetic signals: BUY when return > 0, SELL when < 0
        signals = []
        signals.append("HOLD")  # First entry
        for r in trade_returns:
            signals.append("BUY" if r > 0 else "SELL")
        signals_series = pd.Series(signals, index=dates)

        return run_walk_forward(ohlcv_df, signals_series)
