"""Simple rule-based backtest engine."""
import math
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from .metrics import compute_metrics, PerformanceMetrics


@dataclass
class BacktestResult:
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    metrics: PerformanceMetrics
    equity_curve: list[float]  # Daily portfolio values
    trade_log: list[dict]  # Trade records
    signals: list[str]  # Per-day signals (BUY/SELL/HOLD)


def run_backtest(
    symbol: str,
    ohlcv_df: pd.DataFrame,
    signals_series: pd.Series,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Run a simple long-only, fully-invested backtest.

    Args:
        symbol: Ticker symbol.
        ohlcv_df: OHLCV DataFrame with DatetimeIndex and columns
                  ['open', 'high', 'low', 'close', 'volume'].
        signals_series: Series of signals ('BUY', 'SELL', 'HOLD') aligned
                        with ohlcv_df index.
        initial_capital: Starting capital.

    Returns:
        BacktestResult with equity curve, trade log, and performance metrics.
    """
    cash = initial_capital
    shares = 0
    entry_price = 0.0

    equity_curve_values: list[float] = []
    trade_log: list[dict] = []
    trade_returns: list[float] = []
    signals_list: list[str] = []

    for date, row in ohlcv_df.iterrows():
        price = row["close"]
        signal = signals_series.get(date, "HOLD")
        signals_list.append(str(signal))

        if signal == "BUY" and shares == 0:
            # Buy: fully invest
            shares = math.floor(cash / price)
            if shares > 0:
                cost = shares * price
                cash -= cost
                entry_price = price
                trade_log.append(
                    {
                        "date": str(date),
                        "action": "BUY",
                        "price": price,
                        "shares": shares,
                        "value": cost,
                    }
                )

        elif signal == "SELL" and shares > 0:
            # Sell: liquidate entire position
            proceeds = shares * price
            trade_return = price / entry_price - 1 if entry_price > 0 else 0.0
            trade_returns.append(trade_return)
            trade_log.append(
                {
                    "date": str(date),
                    "action": "SELL",
                    "price": price,
                    "shares": shares,
                    "value": proceeds,
                    "return": trade_return,
                }
            )
            cash += proceeds
            shares = 0
            entry_price = 0.0

        portfolio_value = cash + shares * price
        equity_curve_values.append(portfolio_value)

    # Build equity curve as a pandas Series for metrics computation
    equity_series = pd.Series(equity_curve_values, index=ohlcv_df.index)

    metrics = compute_metrics(equity_series, trade_returns)

    dates = ohlcv_df.index
    start_date = str(dates[0]) if len(dates) > 0 else ""
    end_date = str(dates[-1]) if len(dates) > 0 else ""
    final_capital = equity_curve_values[-1] if equity_curve_values else initial_capital

    return BacktestResult(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        final_capital=final_capital,
        metrics=metrics,
        equity_curve=equity_curve_values,
        trade_log=trade_log,
        signals=signals_list,
    )
