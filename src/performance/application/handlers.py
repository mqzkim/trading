"""Performance application -- handlers."""
from __future__ import annotations

from typing import Optional

from src.performance.domain.repositories import IProposalRepository, ITradeHistoryRepository
from src.performance.domain.services import (
    BrinsonFachlerService,
    ICCalculationService,
    KellyEfficiencyService,
    compute_sortino,
)
from src.performance.domain.value_objects import PerformanceReport

from .commands import ApproveProposalCommand, RejectProposalCommand
from .queries import ComputeAttributionQuery

# Reuse existing metrics from core
from core.backtest.metrics import compute_sharpe, compute_max_drawdown, compute_win_rate


class AttributionHandler:
    """Computes full performance attribution report."""

    def __init__(
        self,
        trade_repo: ITradeHistoryRepository,
        proposal_repo: Optional[IProposalRepository] = None,
    ) -> None:
        self._trade_repo = trade_repo
        self._proposal_repo = proposal_repo
        self._bf = BrinsonFachlerService()
        self._ic = ICCalculationService()
        self._kelly = KellyEfficiencyService()

    def handle(self, query: ComputeAttributionQuery) -> PerformanceReport:
        trades = self._trade_repo.find_all()
        count = len(trades)

        if count < 50:
            return PerformanceReport(
                sharpe=None,
                sortino=None,
                win_rate=None,
                max_drawdown=None,
                trade_count=count,
                attribution=[],
                signal_ic_fundamental=None,
                signal_ic_technical=None,
                signal_ic_sentiment=None,
                kelly_efficiency=None,
            )

        returns = [t.pnl_pct for t in trades]

        import pandas as pd

        returns_series = pd.Series(returns)
        sharpe = compute_sharpe(returns_series)
        # compute_max_drawdown expects equity curve, build from returns
        equity = (1 + returns_series).cumprod()
        max_dd = compute_max_drawdown(equity)
        win_r = compute_win_rate(returns)
        sortino = compute_sortino(returns)

        attribution = self._bf.compute(trades)
        ic_fund = self._ic.compute_axis_ic(trades, "fundamental")
        ic_tech = self._ic.compute_axis_ic(trades, "technical")
        ic_sent = self._ic.compute_axis_ic(trades, "sentiment")
        kelly = self._kelly.compute(trades)

        return PerformanceReport(
            sharpe=round(sharpe, 4) if sharpe else None,
            sortino=sortino,
            win_rate=round(win_r, 4) if win_r is not None else None,
            max_drawdown=round(max_dd, 4) if max_dd else None,
            trade_count=count,
            attribution=attribution,
            signal_ic_fundamental=ic_fund,
            signal_ic_technical=ic_tech,
            signal_ic_sentiment=ic_sent,
            kelly_efficiency=kelly,
        )

    def handle_approve(self, cmd: ApproveProposalCommand) -> dict:
        if self._proposal_repo is None:
            return {"error": "proposal repository not configured"}
        self._proposal_repo.approve(cmd.proposal_id)
        return {"status": "approved", "proposal_id": cmd.proposal_id}

    def handle_reject(self, cmd: RejectProposalCommand) -> dict:
        if self._proposal_repo is None:
            return {"error": "proposal repository not configured"}
        self._proposal_repo.reject(cmd.proposal_id)
        return {"status": "rejected", "proposal_id": cmd.proposal_id}
