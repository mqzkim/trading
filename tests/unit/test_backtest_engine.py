"""Unit tests for backtest engine."""
import pytest
import pandas as pd
import numpy as np
from core.backtest.engine import run_backtest, BacktestResult
from core.backtest.metrics import (
    compute_cagr,
    compute_sharpe,
    compute_max_drawdown,
    compute_win_rate,
    compute_metrics,
    PerformanceMetrics,
)


# --- Helpers ---


def _make_ohlcv(prices: list[float], start_date: str = "2024-01-01") -> pd.DataFrame:
    """Create a minimal OHLCV DataFrame from a list of close prices."""
    dates = pd.bdate_range(start=start_date, periods=len(prices))
    df = pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1_000_000] * len(prices),
        },
        index=dates,
    )
    return df


def _make_signals(ohlcv_df: pd.DataFrame, signal_map: dict[int, str]) -> pd.Series:
    """Create a signals Series. signal_map maps positional index -> signal.
    Defaults to 'HOLD' for unlisted positions.
    """
    signals = ["HOLD"] * len(ohlcv_df)
    for idx, sig in signal_map.items():
        signals[idx] = sig
    return pd.Series(signals, index=ohlcv_df.index)


# --- Test 1: BacktestResult structure ---


def test_backtest_result_structure():
    prices = [100.0, 101.0, 102.0, 103.0, 104.0]
    ohlcv = _make_ohlcv(prices)
    signals = _make_signals(ohlcv, {0: "BUY", 4: "SELL"})

    result = run_backtest("TEST", ohlcv, signals)

    assert isinstance(result, BacktestResult)
    assert hasattr(result, "symbol")
    assert hasattr(result, "start_date")
    assert hasattr(result, "end_date")
    assert hasattr(result, "initial_capital")
    assert hasattr(result, "final_capital")
    assert hasattr(result, "metrics")
    assert hasattr(result, "equity_curve")
    assert hasattr(result, "trade_log")
    assert hasattr(result, "signals")
    assert isinstance(result.metrics, PerformanceMetrics)


# --- Test 2: BUY and HOLD with increasing price ---


def test_buy_and_hold_increasing_price():
    prices = [100.0, 105.0, 110.0, 115.0, 120.0]
    ohlcv = _make_ohlcv(prices)
    signals = _make_signals(ohlcv, {0: "BUY", 4: "SELL"})

    result = run_backtest("UPTREND", ohlcv, signals, initial_capital=100_000.0)

    assert result.final_capital > result.initial_capital
    assert len(result.trade_log) == 2  # BUY + SELL
    assert result.trade_log[0]["action"] == "BUY"
    assert result.trade_log[1]["action"] == "SELL"
    assert result.trade_log[1]["return"] > 0


# --- Test 3: No trades with HOLD only ---


def test_no_trades_hold_only():
    prices = [100.0, 101.0, 102.0]
    ohlcv = _make_ohlcv(prices)
    signals = _make_signals(ohlcv, {})  # all HOLD

    result = run_backtest("HOLDONLY", ohlcv, signals)

    assert len(result.trade_log) == 0
    assert result.metrics.num_trades == 0
    assert result.final_capital == result.initial_capital


# --- Test 4: SELL without position is no-op ---


def test_sell_without_position_noop():
    prices = [100.0, 101.0, 102.0]
    ohlcv = _make_ohlcv(prices)
    signals = _make_signals(ohlcv, {1: "SELL"})  # SELL on day 1 with no position

    result = run_backtest("NOSELL", ohlcv, signals)

    assert len(result.trade_log) == 0
    assert result.final_capital == result.initial_capital


# --- Test 5: Equity curve length matches OHLCV rows ---


def test_equity_curve_length_matches_days():
    prices = [100.0 + i for i in range(20)]
    ohlcv = _make_ohlcv(prices)
    signals = _make_signals(ohlcv, {0: "BUY", 10: "SELL"})

    result = run_backtest("LEN", ohlcv, signals)

    assert len(result.equity_curve) == len(ohlcv)
    assert len(result.signals) == len(ohlcv)


# --- Test 6: CAGR calculation ---


def test_cagr_calculation():
    """2 years (504 trading days), 2x return -> CAGR ~ 41.4%."""
    days = 504
    values = np.linspace(100, 200, days)
    equity = pd.Series(values)

    cagr = compute_cagr(equity, days)

    assert pytest.approx(cagr, rel=0.01) == 0.414


# --- Test 7: Sharpe positive returns ---


def test_sharpe_positive_returns():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.01, 252))  # positive mean

    sharpe = compute_sharpe(returns)

    assert sharpe > 0


# --- Test 8: Max drawdown is negative ---


def test_max_drawdown_negative():
    equity = pd.Series([100.0, 110.0, 90.0, 95.0, 80.0, 100.0])

    mdd = compute_max_drawdown(equity)

    assert mdd < 0
    # Peak was 110, trough was 80 -> drawdown = (80-110)/110 ~ -0.2727
    assert pytest.approx(mdd, abs=0.01) == -0.2727


# --- Test 9: Win rate calculation ---


def test_win_rate_calculation():
    trade_returns = [0.05, -0.02, 0.03]

    wr = compute_win_rate(trade_returns)

    assert pytest.approx(wr, abs=0.001) == 2 / 3


# --- Test 10: Metrics all zero if no trades ---


def test_metrics_all_zero_if_no_trades():
    equity = pd.Series([100_000.0] * 10)
    trade_returns: list[float] = []

    metrics = compute_metrics(equity, trade_returns)

    assert metrics.num_trades == 0
    assert metrics.win_rate == 0.0
    assert metrics.avg_return_per_trade == 0.0
    assert metrics.total_return == 0.0
