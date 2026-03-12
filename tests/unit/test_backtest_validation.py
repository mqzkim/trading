"""Tests for backtest bounded context -- walk-forward validation and performance reporting.

Covers:
- BacktestConfig VO validation (BACK-01)
- WalkForwardConfig VO validation (BACK-01)
- PerformanceReport VO fields (BACK-02)
- BacktestValidationService.compute_profit_factor (BACK-02)
- BacktestValidationService.enrich_metrics (BACK-02)
- CoreBacktestAdapter.run_single delegation (BACK-01)
- CoreBacktestAdapter.run_walk_forward delegation (BACK-01)
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers: synthetic OHLCV + signals
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 50) -> pd.DataFrame:
    """Create synthetic OHLCV DataFrame with DatetimeIndex."""
    dates = pd.bdate_range("2024-01-02", periods=n, freq="B")
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.normal(0.1, 1.0, n))
    close = np.maximum(close, 10.0)  # prevent negative prices
    return pd.DataFrame(
        {
            "open": close * 0.99,
            "high": close * 1.01,
            "low": close * 0.98,
            "close": close,
            "volume": rng.integers(1_000_000, 5_000_000, n),
        },
        index=dates,
    )


def _make_signals(n: int = 50) -> pd.Series:
    """Create signal series: BUY at day 5, SELL at day 20, BUY at day 30, SELL at day 45."""
    dates = pd.bdate_range("2024-01-02", periods=n, freq="B")
    signals = pd.Series(["HOLD"] * n, index=dates)
    if n > 5:
        signals.iloc[5] = "BUY"
    if n > 20:
        signals.iloc[20] = "SELL"
    if n > 30:
        signals.iloc[30] = "BUY"
    if n > 45:
        signals.iloc[45] = "SELL"
    return signals


# ===========================================================================
# Task 1: Domain VOs
# ===========================================================================

class TestBacktestConfigVO:
    """BacktestConfig validates symbol non-empty, initial_capital > 0."""

    def test_valid_config(self):
        from src.backtest.domain.value_objects import BacktestConfig
        cfg = BacktestConfig(symbol="AAPL", initial_capital=100_000.0)
        assert cfg.symbol == "AAPL"
        assert cfg.initial_capital == 100_000.0

    def test_empty_symbol_raises(self):
        from src.backtest.domain.value_objects import BacktestConfig
        with pytest.raises(ValueError):
            BacktestConfig(symbol="", initial_capital=100_000.0)

    def test_negative_capital_raises(self):
        from src.backtest.domain.value_objects import BacktestConfig
        with pytest.raises(ValueError):
            BacktestConfig(symbol="AAPL", initial_capital=-1.0)

    def test_zero_capital_raises(self):
        from src.backtest.domain.value_objects import BacktestConfig
        with pytest.raises(ValueError):
            BacktestConfig(symbol="AAPL", initial_capital=0.0)


class TestWalkForwardConfigVO:
    """WalkForwardConfig validates n_splits >= 2, 0 < train_ratio < 1, capital > 0, symbol."""

    def test_valid_config(self):
        from src.backtest.domain.value_objects import WalkForwardConfig
        cfg = WalkForwardConfig(symbol="MSFT", n_splits=5, train_ratio=0.7, initial_capital=50_000.0)
        assert cfg.n_splits == 5
        assert cfg.train_ratio == 0.7

    def test_n_splits_below_2_raises(self):
        from src.backtest.domain.value_objects import WalkForwardConfig
        with pytest.raises(ValueError):
            WalkForwardConfig(symbol="MSFT", n_splits=1)

    def test_train_ratio_0_raises(self):
        from src.backtest.domain.value_objects import WalkForwardConfig
        with pytest.raises(ValueError):
            WalkForwardConfig(symbol="MSFT", train_ratio=0.0)

    def test_train_ratio_1_raises(self):
        from src.backtest.domain.value_objects import WalkForwardConfig
        with pytest.raises(ValueError):
            WalkForwardConfig(symbol="MSFT", train_ratio=1.0)

    def test_empty_symbol_raises(self):
        from src.backtest.domain.value_objects import WalkForwardConfig
        with pytest.raises(ValueError):
            WalkForwardConfig(symbol="")


class TestPerformanceReportVO:
    """PerformanceReport includes all 8 fields."""

    def test_all_8_fields(self):
        from src.backtest.domain.value_objects import PerformanceReport
        report = PerformanceReport(
            cagr=0.15,
            sharpe_ratio=1.2,
            max_drawdown=-0.10,
            win_rate=0.6,
            total_return=0.35,
            num_trades=10,
            avg_return_per_trade=0.035,
            profit_factor=2.0,
        )
        assert report.cagr == 0.15
        assert report.sharpe_ratio == 1.2
        assert report.max_drawdown == -0.10
        assert report.win_rate == 0.6
        assert report.total_return == 0.35
        assert report.num_trades == 10
        assert report.avg_return_per_trade == 0.035
        assert report.profit_factor == 2.0


# ===========================================================================
# Task 1: BacktestValidationService
# ===========================================================================

class TestComputeProfitFactor:
    """Profit factor = gross_profit / abs(gross_loss)."""

    def test_mixed_returns(self):
        from src.backtest.domain.services import BacktestValidationService
        svc = BacktestValidationService()
        pf = svc.compute_profit_factor([0.10, -0.05, 0.08, -0.03])
        assert math.isclose(pf, 2.25, rel_tol=1e-9)

    def test_no_losses_with_profit(self):
        from src.backtest.domain.services import BacktestValidationService
        svc = BacktestValidationService()
        pf = svc.compute_profit_factor([0.10, 0.05])
        assert pf == float("inf")

    def test_no_losses_no_profit(self):
        from src.backtest.domain.services import BacktestValidationService
        svc = BacktestValidationService()
        pf = svc.compute_profit_factor([0.0, 0.0])
        assert pf == 0.0

    def test_no_profits(self):
        from src.backtest.domain.services import BacktestValidationService
        svc = BacktestValidationService()
        pf = svc.compute_profit_factor([-0.05, -0.10])
        assert pf == 0.0

    def test_empty_returns(self):
        from src.backtest.domain.services import BacktestValidationService
        svc = BacktestValidationService()
        pf = svc.compute_profit_factor([])
        assert pf == 0.0


class TestEnrichMetrics:
    """enrich_metrics adds profit_factor to core metrics dict."""

    def test_enriches_with_profit_factor(self):
        from src.backtest.domain.services import BacktestValidationService
        from src.backtest.domain.value_objects import PerformanceReport
        svc = BacktestValidationService()
        core_metrics = {
            "cagr": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.10,
            "win_rate": 0.6,
            "total_return": 0.35,
            "num_trades": 4,
            "avg_return_per_trade": 0.025,
        }
        trade_returns = [0.10, -0.05, 0.08, -0.03]
        report = svc.enrich_metrics(core_metrics, trade_returns)
        assert isinstance(report, PerformanceReport)
        assert math.isclose(report.profit_factor, 2.25, rel_tol=1e-9)
        assert report.sharpe_ratio == 1.2
        assert report.num_trades == 4


# ===========================================================================
# Task 1: CoreBacktestAdapter
# ===========================================================================

class TestCoreBacktestAdapterRunSingle:
    """run_single delegates to core/backtest/engine.run_backtest()."""

    def test_run_single_returns_expected_keys(self):
        from src.backtest.infrastructure.core_backtest_adapter import CoreBacktestAdapter
        adapter = CoreBacktestAdapter()
        ohlcv = _make_ohlcv(50)
        signals = _make_signals(50)
        result = adapter.run_single("TEST", ohlcv, signals, 100_000.0)
        assert result["symbol"] == "TEST"
        assert "metrics" in result
        assert "equity_curve" in result
        assert "trade_log" in result

    def test_run_single_metrics_has_7_fields(self):
        from src.backtest.infrastructure.core_backtest_adapter import CoreBacktestAdapter
        adapter = CoreBacktestAdapter()
        ohlcv = _make_ohlcv(50)
        signals = _make_signals(50)
        result = adapter.run_single("TEST", ohlcv, signals, 100_000.0)
        metrics = result["metrics"]
        expected_keys = {"cagr", "sharpe_ratio", "max_drawdown", "win_rate",
                         "total_return", "num_trades", "avg_return_per_trade"}
        assert expected_keys.issubset(set(metrics.keys()))


class TestCoreBacktestAdapterWalkForward:
    """run_walk_forward delegates to core/backtest/walk_forward.run_walk_forward()."""

    def test_run_walk_forward_returns_expected_keys(self):
        from src.backtest.infrastructure.core_backtest_adapter import CoreBacktestAdapter
        adapter = CoreBacktestAdapter()
        ohlcv = _make_ohlcv(100)
        signals = _make_signals(100)
        result = adapter.run_walk_forward(ohlcv, signals, n_splits=3, train_ratio=0.7,
                                          initial_capital=100_000.0, symbol="WF")
        assert result["n_splits"] == 3
        assert "oos_metrics" in result
        assert "is_metrics" in result
        assert "overfitting_score" in result

    def test_run_walk_forward_metrics_are_dicts(self):
        from src.backtest.infrastructure.core_backtest_adapter import CoreBacktestAdapter
        adapter = CoreBacktestAdapter()
        ohlcv = _make_ohlcv(100)
        signals = _make_signals(100)
        result = adapter.run_walk_forward(ohlcv, signals, n_splits=2, train_ratio=0.6,
                                          initial_capital=100_000.0, symbol="WF")
        assert isinstance(result["oos_metrics"], dict)
        assert isinstance(result["is_metrics"], dict)


class TestExtractTradeReturns:
    """extract_trade_returns gets returns from trade_log."""

    def test_extracts_returns(self):
        from src.backtest.infrastructure.core_backtest_adapter import CoreBacktestAdapter
        adapter = CoreBacktestAdapter()
        ohlcv = _make_ohlcv(50)
        signals = _make_signals(50)
        result = adapter.run_single("TEST", ohlcv, signals, 100_000.0)
        returns = adapter.extract_trade_returns(result)
        assert isinstance(returns, list)
        # Should have returns for completed trades (SELL entries have 'return' field)
        sell_count = sum(1 for t in result["trade_log"] if t["action"] == "SELL")
        assert len(returns) == sell_count
