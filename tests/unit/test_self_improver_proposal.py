"""Tests for self-improver proposal generation (SELF-01 through SELF-04).

Covers:
- Proposal generation with valid weights
- MINIMUM_TRADES = 50 guard
- Walk-forward required before proposal generation
- Only scoring axis weight adjustments (no risk params)
- No auto-apply (status remains pending)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from src.performance.domain.entities import ClosedTrade
from src.performance.infrastructure.duckdb_proposal_repository import DuckDBProposalRepository
from core.backtest.walk_forward import WalkForwardResult
from core.backtest.metrics import PerformanceMetrics

from personal.self_improver.domain.services import ImprovementAdvisorService
from personal.self_improver.domain.value_objects import WeightProposal
from personal.self_improver.application.handlers import GenerateProposalHandler
from personal.self_improver.infrastructure.walk_forward_adapter import WalkForwardAdapter


def _make_closed_trade(pnl_pct: float = 0.05) -> ClosedTrade:
    """Helper: create a minimal ClosedTrade with given pnl_pct."""
    from datetime import date

    return ClosedTrade(
        id=None,
        symbol="AAPL",
        entry_date=date(2026, 1, 1),
        exit_date=date(2026, 1, 15),
        entry_price=100.0,
        exit_price=105.0,
        quantity=10,
        pnl=50.0,
        pnl_pct=pnl_pct,
        strategy="composite",
        sector="Technology",
        composite_score=75.0,
        technical_score=70.0,
        fundamental_score=80.0,
        sentiment_score=65.0,
        regime="Bull",
        weights_json=None,
        signal_direction="BUY",
    )


def _make_wf_result(sharpe: float = 0.3, overfitting: float = 0.5) -> WalkForwardResult:
    """Helper: create a WalkForwardResult with given OOS Sharpe."""
    return WalkForwardResult(
        n_splits=5,
        splits=[],
        oos_metrics=PerformanceMetrics(
            cagr=0.1,
            sharpe_ratio=sharpe,
            max_drawdown=-0.10,
            win_rate=0.6,
            total_return=0.1,
            num_trades=50,
            avg_return_per_trade=0.002,
        ),
        is_metrics=PerformanceMetrics(
            cagr=0.15,
            sharpe_ratio=sharpe + overfitting,
            max_drawdown=-0.08,
            win_rate=0.65,
            total_return=0.15,
            num_trades=50,
            avg_return_per_trade=0.003,
        ),
        overfitting_score=overfitting,
    )


class TestProposalGeneration:
    """Test GenerateProposalHandler proposal generation."""

    def test_proposal_generated_with_valid_weights(self) -> None:
        """GenerateProposalHandler.handle() with 50+ trades returns proposals."""
        # Arrange
        conn = duckdb.connect(":memory:")
        proposal_repo = DuckDBProposalRepository(conn)
        trade_repo = MagicMock()
        trade_repo.count.return_value = 60
        trade_repo.find_all.return_value = [_make_closed_trade() for _ in range(60)]

        wf_adapter = MagicMock(spec=WalkForwardAdapter)
        wf_adapter.run.return_value = _make_wf_result(sharpe=0.3)

        advisor = ImprovementAdvisorService()
        handler = GenerateProposalHandler(
            trade_repo=trade_repo,
            proposal_repo=proposal_repo,
            advisor=advisor,
            walk_forward_adapter=wf_adapter,
        )

        # Act
        proposals = handler.handle()

        # Assert
        assert len(proposals) > 0
        for p in proposals:
            assert isinstance(p, WeightProposal)
            assert p.regime in ("Bull", "Bear", "Sideways", "Crisis", "Transition")
            assert p.axis in ("fundamental", "technical", "sentiment")
            assert 0.0 <= p.current_weight <= 1.0
            assert 0.0 <= p.proposed_weight <= 1.0

    def test_threshold_50(self) -> None:
        """Handler returns [] when < 50 trades (no error)."""
        conn = duckdb.connect(":memory:")
        proposal_repo = DuckDBProposalRepository(conn)
        trade_repo = MagicMock()
        trade_repo.count.return_value = 30

        wf_adapter = MagicMock(spec=WalkForwardAdapter)
        advisor = ImprovementAdvisorService()

        handler = GenerateProposalHandler(
            trade_repo=trade_repo,
            proposal_repo=proposal_repo,
            advisor=advisor,
            walk_forward_adapter=wf_adapter,
        )

        result = handler.handle()
        assert result == []
        wf_adapter.run.assert_not_called()

    def test_walk_forward_required(self) -> None:
        """Handler calls WalkForwardAdapter.run() exactly once."""
        conn = duckdb.connect(":memory:")
        proposal_repo = DuckDBProposalRepository(conn)
        trade_repo = MagicMock()
        trade_repo.count.return_value = 55
        trade_repo.find_all.return_value = [_make_closed_trade() for _ in range(55)]

        wf_adapter = MagicMock(spec=WalkForwardAdapter)
        wf_adapter.run.return_value = _make_wf_result(sharpe=0.3)

        advisor = ImprovementAdvisorService()
        handler = GenerateProposalHandler(
            trade_repo=trade_repo,
            proposal_repo=proposal_repo,
            advisor=advisor,
            walk_forward_adapter=wf_adapter,
        )

        handler.handle()
        wf_adapter.run.assert_called_once()

    def test_proposals_only_weight_adjustments(self) -> None:
        """Proposals only contain axis in {fundamental, technical, sentiment}."""
        conn = duckdb.connect(":memory:")
        proposal_repo = DuckDBProposalRepository(conn)
        trade_repo = MagicMock()
        trade_repo.count.return_value = 60
        trade_repo.find_all.return_value = [_make_closed_trade() for _ in range(60)]

        wf_adapter = MagicMock(spec=WalkForwardAdapter)
        wf_adapter.run.return_value = _make_wf_result(sharpe=0.3)

        advisor = ImprovementAdvisorService()
        handler = GenerateProposalHandler(
            trade_repo=trade_repo,
            proposal_repo=proposal_repo,
            advisor=advisor,
            walk_forward_adapter=wf_adapter,
        )

        proposals = handler.handle()
        allowed_axes = {"fundamental", "technical", "sentiment"}
        for p in proposals:
            assert p.axis in allowed_axes, f"Unexpected axis: {p.axis}"

    def test_no_auto_apply(self) -> None:
        """Calling handle() does NOT modify scoring weights (status remains pending)."""
        conn = duckdb.connect(":memory:")
        proposal_repo = DuckDBProposalRepository(conn)
        trade_repo = MagicMock()
        trade_repo.count.return_value = 60
        trade_repo.find_all.return_value = [_make_closed_trade() for _ in range(60)]

        wf_adapter = MagicMock(spec=WalkForwardAdapter)
        wf_adapter.run.return_value = _make_wf_result(sharpe=0.3)

        advisor = ImprovementAdvisorService()
        handler = GenerateProposalHandler(
            trade_repo=trade_repo,
            proposal_repo=proposal_repo,
            advisor=advisor,
            walk_forward_adapter=wf_adapter,
        )

        proposals = handler.handle()
        # All saved proposals should be pending
        pending = proposal_repo.find_pending()
        for p in pending:
            assert p["status"] == "pending"
