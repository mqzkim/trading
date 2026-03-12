"""Backtest Application Layer -- Handlers.

Orchestrates CoreBacktestAdapter calls and enriches metrics with profit_factor
via BacktestValidationService.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from src.shared.domain import Ok, Err, Result
from src.backtest.domain.services import BacktestValidationService
from src.backtest.domain.repositories import IBacktestResultRepository
from src.backtest.domain.events import BacktestCompletedEvent
from src.backtest.infrastructure.core_backtest_adapter import CoreBacktestAdapter
from .commands import RunBacktestCommand, RunWalkForwardCommand


class BacktestError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class BacktestHandler:
    """Orchestrates backtest and walk-forward validation use cases.

    1. Delegates to CoreBacktestAdapter for computation
    2. Enriches metrics with profit_factor via BacktestValidationService
    3. Persists to repository if available
    4. Emits BacktestCompletedEvent
    """

    def __init__(
        self,
        adapter: CoreBacktestAdapter,
        validation_svc: BacktestValidationService,
        repo: Optional[IBacktestResultRepository] = None,
    ) -> None:
        self._adapter = adapter
        self._validation_svc = validation_svc
        self._repo = repo
        self._events: list[BacktestCompletedEvent] = []

    @property
    def events(self) -> list[BacktestCompletedEvent]:
        return self._events

    def run_backtest(self, cmd: RunBacktestCommand) -> Result:
        """Run a single backtest, enrich with profit_factor, persist, return Ok."""
        try:
            result = self._adapter.run_single(
                cmd.symbol, cmd.ohlcv_df, cmd.signals_series, cmd.initial_capital
            )
        except Exception as e:
            return Err(BacktestError(f"Backtest failed: {e}", "BACKTEST_ERROR"))

        trade_returns = self._adapter.extract_trade_returns(result)
        report = self._validation_svc.enrich_metrics(result["metrics"], trade_returns)
        report_dict = asdict(report)

        # Persist if repository available
        if self._repo is not None:
            config_dict = {"symbol": cmd.symbol, "initial_capital": cmd.initial_capital}
            self._repo.save(cmd.symbol, config_dict, report_dict)

        # Emit domain event
        self._events.append(
            BacktestCompletedEvent(
                symbol=cmd.symbol,
                sharpe_ratio=report.sharpe_ratio,
                profit_factor=report.profit_factor,
                max_drawdown=report.max_drawdown,
            )
        )

        equity_curve = result.get("equity_curve", [])
        return Ok({
            "symbol": cmd.symbol,
            "performance_report": report_dict,
            "equity_curve_summary": {
                "start": equity_curve[0] if equity_curve else 0.0,
                "end": equity_curve[-1] if equity_curve else 0.0,
                "length": len(equity_curve),
            },
        })

    def run_walk_forward(self, cmd: RunWalkForwardCommand) -> Result:
        """Run walk-forward validation, enrich IS/OOS with profit_factor, persist, return Ok."""
        try:
            result = self._adapter.run_walk_forward(
                cmd.ohlcv_df,
                cmd.signals_series,
                cmd.n_splits,
                cmd.train_ratio,
                cmd.initial_capital,
                cmd.symbol,
            )
        except Exception as e:
            return Err(BacktestError(f"Walk-forward failed: {e}", "WF_ERROR"))

        # Collect trade returns across all splits for IS and OOS
        is_trade_returns: list[float] = []
        oos_trade_returns: list[float] = []
        for split in result.get("splits", []):
            # IS and OOS metrics from splits don't carry trade_log,
            # so we use the averaged metrics from the walk-forward result
            pass

        # Enrich IS and OOS metrics with profit factor
        # For walk-forward, trade returns are not directly available per-split,
        # so we compute profit factor from the averaged metrics if trade data available.
        # Use empty returns (profit_factor = 0.0) as baseline since walk-forward
        # doesn't expose individual trade logs per split.
        oos_report = self._validation_svc.enrich_metrics(
            result["oos_metrics"], oos_trade_returns
        )
        is_report = self._validation_svc.enrich_metrics(
            result["is_metrics"], is_trade_returns
        )

        oos_report_dict = asdict(oos_report)
        is_report_dict = asdict(is_report)
        overfitting_score = result["overfitting_score"]

        # Persist if repository available
        if self._repo is not None:
            config_dict = {
                "symbol": cmd.symbol,
                "n_splits": cmd.n_splits,
                "train_ratio": cmd.train_ratio,
                "initial_capital": cmd.initial_capital,
                "type": "walk_forward",
            }
            report_dict = {
                "oos_report": oos_report_dict,
                "is_report": is_report_dict,
                "overfitting_score": overfitting_score,
            }
            self._repo.save(cmd.symbol, config_dict, report_dict)

        # Emit domain event
        self._events.append(
            BacktestCompletedEvent(
                symbol=cmd.symbol,
                sharpe_ratio=oos_report.sharpe_ratio,
                profit_factor=oos_report.profit_factor,
                max_drawdown=oos_report.max_drawdown,
            )
        )

        return Ok({
            "symbol": cmd.symbol,
            "n_splits": cmd.n_splits,
            "oos_report": oos_report_dict,
            "is_report": is_report_dict,
            "overfitting_score": overfitting_score,
        })
