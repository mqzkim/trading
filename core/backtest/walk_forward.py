"""Walk-forward backtesting for out-of-sample validation."""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from .engine import run_backtest, BacktestResult
from .metrics import PerformanceMetrics, compute_metrics


@dataclass
class WalkForwardResult:
    n_splits: int
    splits: list[dict]  # Each split: {train_start, train_end, test_start, test_end, metrics}
    oos_metrics: PerformanceMetrics  # Out-of-Sample average performance
    is_metrics: PerformanceMetrics  # In-Sample average performance
    overfitting_score: float  # IS Sharpe - OOS Sharpe (lower is better)


def run_walk_forward(
    ohlcv_df: pd.DataFrame,
    signals_series: pd.Series,
    n_splits: int = 5,
    train_ratio: float = 0.7,
    initial_capital: float = 100_000.0,
    symbol: str = "WF",
) -> WalkForwardResult:
    """Run walk-forward backtesting with rolling IS/OOS splits.

    Divides the full period into n_splits equal folds. Within each fold,
    the first train_ratio fraction is in-sample (IS) and the remainder
    is out-of-sample (OOS). Runs backtest on each segment independently.

    Args:
        ohlcv_df: OHLCV DataFrame with DatetimeIndex.
        signals_series: Series of signals ('BUY', 'SELL', 'HOLD')
                        aligned with ohlcv_df index.
        n_splits: Number of walk-forward folds.
        train_ratio: Fraction of each fold used for training (IS).
        initial_capital: Starting capital for each fold backtest.
        symbol: Ticker symbol passed to backtest engine.

    Returns:
        WalkForwardResult with IS/OOS metrics and overfitting score.
    """
    total_len = len(ohlcv_df)
    fold_size = total_len // n_splits

    splits: list[dict] = []
    is_sharpes: list[float] = []
    oos_sharpes: list[float] = []

    # Accumulators for averaging IS and OOS metrics
    is_cagrs: list[float] = []
    is_max_dds: list[float] = []
    is_win_rates: list[float] = []
    is_total_returns: list[float] = []
    is_num_trades: list[int] = []
    is_avg_returns: list[float] = []

    oos_cagrs: list[float] = []
    oos_max_dds: list[float] = []
    oos_win_rates: list[float] = []
    oos_total_returns: list[float] = []
    oos_num_trades: list[int] = []
    oos_avg_returns: list[float] = []

    for i in range(n_splits):
        fold_start = i * fold_size
        # Last fold takes remaining data
        fold_end = total_len if i == n_splits - 1 else (i + 1) * fold_size

        fold_data = ohlcv_df.iloc[fold_start:fold_end]
        fold_signals = signals_series.iloc[fold_start:fold_end]

        train_size = max(1, int(len(fold_data) * train_ratio))

        train_data = fold_data.iloc[:train_size]
        train_signals = fold_signals.iloc[:train_size]
        test_data = fold_data.iloc[train_size:]
        test_signals = fold_signals.iloc[train_size:]

        # Run IS backtest
        is_result = run_backtest(
            symbol=symbol,
            ohlcv_df=train_data,
            signals_series=train_signals,
            initial_capital=initial_capital,
        )

        # Run OOS backtest (only if test data exists)
        if len(test_data) > 0:
            oos_result = run_backtest(
                symbol=symbol,
                ohlcv_df=test_data,
                signals_series=test_signals,
                initial_capital=initial_capital,
            )
        else:
            oos_result = is_result

        split_info = {
            "train_start": str(train_data.index[0]) if len(train_data) > 0 else "",
            "train_end": str(train_data.index[-1]) if len(train_data) > 0 else "",
            "test_start": str(test_data.index[0]) if len(test_data) > 0 else "",
            "test_end": str(test_data.index[-1]) if len(test_data) > 0 else "",
            "is_metrics": is_result.metrics,
            "oos_metrics": oos_result.metrics,
        }
        splits.append(split_info)

        # Collect metrics
        is_sharpes.append(is_result.metrics.sharpe_ratio)
        oos_sharpes.append(oos_result.metrics.sharpe_ratio)

        is_cagrs.append(is_result.metrics.cagr)
        is_max_dds.append(is_result.metrics.max_drawdown)
        is_win_rates.append(is_result.metrics.win_rate)
        is_total_returns.append(is_result.metrics.total_return)
        is_num_trades.append(is_result.metrics.num_trades)
        is_avg_returns.append(is_result.metrics.avg_return_per_trade)

        oos_cagrs.append(oos_result.metrics.cagr)
        oos_max_dds.append(oos_result.metrics.max_drawdown)
        oos_win_rates.append(oos_result.metrics.win_rate)
        oos_total_returns.append(oos_result.metrics.total_return)
        oos_num_trades.append(oos_result.metrics.num_trades)
        oos_avg_returns.append(oos_result.metrics.avg_return_per_trade)

    def _mean(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    is_metrics_avg = PerformanceMetrics(
        cagr=_mean(is_cagrs),
        sharpe_ratio=_mean(is_sharpes),
        max_drawdown=_mean(is_max_dds),
        win_rate=_mean(is_win_rates),
        total_return=_mean(is_total_returns),
        num_trades=sum(is_num_trades),
        avg_return_per_trade=_mean(is_avg_returns),
    )

    oos_metrics_avg = PerformanceMetrics(
        cagr=_mean(oos_cagrs),
        sharpe_ratio=_mean(oos_sharpes),
        max_drawdown=_mean(oos_max_dds),
        win_rate=_mean(oos_win_rates),
        total_return=_mean(oos_total_returns),
        num_trades=sum(oos_num_trades),
        avg_return_per_trade=_mean(oos_avg_returns),
    )

    overfitting_score = _mean(is_sharpes) - _mean(oos_sharpes)

    return WalkForwardResult(
        n_splits=n_splits,
        splits=splits,
        oos_metrics=oos_metrics_avg,
        is_metrics=is_metrics_avg,
        overfitting_score=overfitting_score,
    )
