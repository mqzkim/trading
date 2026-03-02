"""Backtest performance metrics."""
import math
import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    cagr: float  # Compound Annual Growth Rate
    sharpe_ratio: float  # Annualized Sharpe Ratio (risk-free=0)
    max_drawdown: float  # Maximum drawdown (negative, e.g., -0.25)
    win_rate: float  # Fraction of winning trades (0-1)
    total_return: float  # Total return over period (e.g., 0.35 = 35%)
    num_trades: int  # Number of trades executed
    avg_return_per_trade: float  # Average return per trade


def compute_cagr(equity_curve: pd.Series, days: int) -> float:
    """Compute Compound Annual Growth Rate.

    Args:
        equity_curve: Daily portfolio values.
        days: Number of trading days in the period.

    Returns:
        CAGR as a decimal (e.g. 0.414 for 41.4%).
    """
    if days <= 0 or len(equity_curve) < 2:
        return 0.0
    start_val = equity_curve.iloc[0]
    end_val = equity_curve.iloc[-1]
    if start_val <= 0:
        return 0.0
    return (end_val / start_val) ** (252 / days) - 1


def compute_sharpe(returns: pd.Series) -> float:
    """Compute annualized Sharpe Ratio (risk-free rate = 0).

    Args:
        returns: Daily return series.

    Returns:
        Annualized Sharpe Ratio.
    """
    if len(returns) < 2:
        return 0.0
    std = returns.std()
    if std == 0 or math.isnan(std):
        return 0.0
    return float(returns.mean() / std * np.sqrt(252))


def compute_max_drawdown(equity_curve: pd.Series) -> float:
    """Compute maximum drawdown from equity curve.

    Args:
        equity_curve: Daily portfolio values.

    Returns:
        Maximum drawdown as a negative decimal (e.g. -0.25 for 25% drawdown).
    """
    if len(equity_curve) < 2:
        return 0.0
    rolling_peak = equity_curve.cummax()
    drawdown = (equity_curve - rolling_peak) / rolling_peak
    return float(drawdown.min())


def compute_win_rate(trade_returns: list[float]) -> float:
    """Compute fraction of winning trades.

    Args:
        trade_returns: List of per-trade returns.

    Returns:
        Win rate as a decimal (0-1).
    """
    if not trade_returns:
        return 0.0
    winners = sum(1 for r in trade_returns if r > 0)
    return winners / len(trade_returns)


def compute_metrics(
    equity_curve: pd.Series, trade_returns: list[float]
) -> PerformanceMetrics:
    """Compute all performance metrics from equity curve and trade returns.

    Args:
        equity_curve: Daily portfolio value Series (index=dates).
        trade_returns: List of per-trade returns (e.g. [0.05, -0.02, 0.08]).

    Returns:
        PerformanceMetrics dataclass with all computed metrics.
    """
    days = len(equity_curve)

    if days < 2:
        return PerformanceMetrics(
            cagr=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            total_return=0.0,
            num_trades=len(trade_returns),
            avg_return_per_trade=0.0,
        )

    # Daily returns from equity curve
    daily_returns = equity_curve.pct_change().dropna()

    start_val = equity_curve.iloc[0]
    end_val = equity_curve.iloc[-1]
    total_return = (end_val / start_val - 1) if start_val > 0 else 0.0

    avg_return_per_trade = (
        sum(trade_returns) / len(trade_returns) if trade_returns else 0.0
    )

    return PerformanceMetrics(
        cagr=compute_cagr(equity_curve, days),
        sharpe_ratio=compute_sharpe(daily_returns),
        max_drawdown=compute_max_drawdown(equity_curve),
        win_rate=compute_win_rate(trade_returns),
        total_return=total_return,
        num_trades=len(trade_returns),
        avg_return_per_trade=avg_return_per_trade,
    )
