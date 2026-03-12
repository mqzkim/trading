"""Infrastructure adapter wrapping core/backtest/ engine and walk-forward.

Thin wrapper -- no math rewriting. Delegates to core/backtest/*.
Converts core dataclass results to plain dicts for domain layer consumption.
"""
from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from core.backtest.engine import run_backtest
from core.backtest.walk_forward import run_walk_forward


class CoreBacktestAdapter:
    """Wraps core/backtest/ engine and walk-forward for DDD backtest context.

    Each method delegates directly to the corresponding core function.
    Results are converted from dataclasses to dicts.
    """

    def run_single(
        self,
        symbol: str,
        ohlcv_df: pd.DataFrame,
        signals_series: pd.Series,
        initial_capital: float = 100_000.0,
    ) -> dict:
        """Run a single backtest via core/backtest/engine.run_backtest().

        Returns:
            Dict with keys: symbol, start_date, end_date, initial_capital,
            final_capital, metrics (dict), equity_curve (list), trade_log (list),
            signals (list).
        """
        result = run_backtest(symbol, ohlcv_df, signals_series, initial_capital)
        return {
            "symbol": result.symbol,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "initial_capital": result.initial_capital,
            "final_capital": result.final_capital,
            "metrics": asdict(result.metrics),
            "equity_curve": result.equity_curve,
            "trade_log": result.trade_log,
            "signals": result.signals,
        }

    def run_walk_forward(
        self,
        ohlcv_df: pd.DataFrame,
        signals_series: pd.Series,
        n_splits: int = 5,
        train_ratio: float = 0.7,
        initial_capital: float = 100_000.0,
        symbol: str = "WF",
    ) -> dict:
        """Run walk-forward validation via core/backtest/walk_forward.run_walk_forward().

        Returns:
            Dict with keys: n_splits, splits (list[dict]), oos_metrics (dict),
            is_metrics (dict), overfitting_score (float).
        """
        result = run_walk_forward(
            ohlcv_df, signals_series, n_splits, train_ratio, initial_capital, symbol
        )
        splits = []
        for s in result.splits:
            split_dict = {
                "train_start": s["train_start"],
                "train_end": s["train_end"],
                "test_start": s["test_start"],
                "test_end": s["test_end"],
                "is_metrics": asdict(s["is_metrics"]),
                "oos_metrics": asdict(s["oos_metrics"]),
            }
            splits.append(split_dict)

        return {
            "n_splits": result.n_splits,
            "splits": splits,
            "oos_metrics": asdict(result.oos_metrics),
            "is_metrics": asdict(result.is_metrics),
            "overfitting_score": result.overfitting_score,
        }

    def extract_trade_returns(self, backtest_result_dict: dict) -> list[float]:
        """Extract trade returns from trade_log entries.

        Only SELL entries have a 'return' field in the trade log.
        """
        return [
            t["return"]
            for t in backtest_result_dict.get("trade_log", [])
            if "return" in t
        ]
