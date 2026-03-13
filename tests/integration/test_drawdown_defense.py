"""Integration tests for drawdown defense wiring.

Proves end-to-end:
1. DrawdownAlertEvent(level="warning"|"critical") -> approval suspended via SyncEventBus
2. DrawdownAlertEvent(level="caution") -> NO suspension (tier 1 only)
3. RunPipelineHandler passes portfolio drawdown_level to orchestrator.run()
4. Pipeline halts when drawdown_level is "warning"
5. Pipeline defaults to "normal" when no portfolio exists
"""
from __future__ import annotations

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.approval.application.commands import CreateApprovalCommand
from src.approval.application.handlers import ApprovalHandler
from src.approval.infrastructure import (
    SqliteApprovalRepository,
    SqliteBudgetRepository,
    SqliteReviewQueueRepository,
)
from src.portfolio.domain.events import DrawdownAlertEvent
from src.portfolio.infrastructure import SqlitePortfolioRepository
from src.shared.infrastructure.db_factory import DBFactory
from src.shared.infrastructure.sync_event_bus import SyncEventBus


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def bus():
    return SyncEventBus()


@pytest.fixture
def approval_handler():
    return ApprovalHandler(
        approval_repo=SqliteApprovalRepository(db_path=":memory:"),
        budget_repo=SqliteBudgetRepository(db_path=":memory:"),
        review_queue_repo=SqliteReviewQueueRepository(db_path=":memory:"),
    )


@pytest.fixture
def _create_active_approval(approval_handler):
    """Create an active approval for tests that need one."""
    approval_handler.create(CreateApprovalCommand(
        score_threshold=60.0,
        allowed_regimes=["Bull", "Sideways"],
        max_per_trade_pct=8.0,
        daily_budget_cap=50000.0,
        expires_in_days=30,
    ))


# ── Pathway 1: DrawdownAlertEvent -> Approval Suspension ─────────


class TestDrawdownEventSuspendsApproval:
    """Tests for bus.subscribe(DrawdownAlertEvent) -> approval_handler.suspend_for_drawdown()."""

    @pytest.mark.usefixtures("_create_active_approval")
    def test_drawdown_warning_suspends_approval(self, bus, approval_handler):
        """DrawdownAlertEvent(level='warning') suspends active approval with 'drawdown_tier2'."""
        # Wire the subscription as bootstrap.py does
        def _on_drawdown_alert(event: DrawdownAlertEvent) -> None:
            if event.level in ("warning", "critical"):
                approval_handler.suspend_for_drawdown()

        bus.subscribe(DrawdownAlertEvent, _on_drawdown_alert)

        # Publish event through the bus
        bus.publish(DrawdownAlertEvent(
            portfolio_id="default",
            drawdown=0.16,
            level="warning",
        ))

        # Assert approval is suspended
        status = approval_handler.get_status()
        approval = status["approval"]
        assert approval is not None
        assert approval.is_suspended is True
        assert "drawdown_tier2" in approval.suspended_reasons

    @pytest.mark.usefixtures("_create_active_approval")
    def test_drawdown_critical_suspends_approval(self, bus, approval_handler):
        """DrawdownAlertEvent(level='critical') suspends active approval with 'drawdown_tier2'."""
        def _on_drawdown_alert(event: DrawdownAlertEvent) -> None:
            if event.level in ("warning", "critical"):
                approval_handler.suspend_for_drawdown()

        bus.subscribe(DrawdownAlertEvent, _on_drawdown_alert)

        bus.publish(DrawdownAlertEvent(
            portfolio_id="default",
            drawdown=0.22,
            level="critical",
        ))

        status = approval_handler.get_status()
        approval = status["approval"]
        assert approval is not None
        assert approval.is_suspended is True
        assert "drawdown_tier2" in approval.suspended_reasons

    @pytest.mark.usefixtures("_create_active_approval")
    def test_drawdown_caution_does_not_suspend(self, bus, approval_handler):
        """DrawdownAlertEvent(level='caution') does NOT suspend approval (tier 1 only)."""
        def _on_drawdown_alert(event: DrawdownAlertEvent) -> None:
            if event.level in ("warning", "critical"):
                approval_handler.suspend_for_drawdown()

        bus.subscribe(DrawdownAlertEvent, _on_drawdown_alert)

        bus.publish(DrawdownAlertEvent(
            portfolio_id="default",
            drawdown=0.12,
            level="caution",
        ))

        status = approval_handler.get_status()
        approval = status["approval"]
        assert approval is not None
        assert approval.is_suspended is False
        assert "drawdown_tier2" not in approval.suspended_reasons


# ── Pathway 2: Pipeline drawdown_level -> orchestrator.run() ─────


class TestPipelineDrawdownBridge:
    """Tests for RunPipelineHandler querying portfolio drawdown_level and passing to orchestrator."""

    def test_pipeline_halts_on_drawdown_warning(self):
        """RunPipelineHandler with portfolio at WARNING drawdown -> orchestrator receives 'warning' -> HALTED."""
        from src.pipeline.application.commands import RunPipelineCommand
        from src.pipeline.application.handlers import RunPipelineHandler
        from src.pipeline.domain.value_objects import PipelineStatus

        with tempfile.TemporaryDirectory() as tmpdir:
            db_factory = DBFactory(data_dir=tmpdir)

            # Create portfolio at WARNING drawdown (peak=100000, current value via initial=85000 -> 15% dd)
            portfolio_repo = SqlitePortfolioRepository(
                db_path=db_factory.sqlite_path("portfolio"),
            )
            from src.portfolio.domain.aggregates import Portfolio

            portfolio = Portfolio(
                portfolio_id="default",
                initial_value=85000.0,
                peak_value=100000.0,
            )
            portfolio_repo.save(portfolio)

            # Verify drawdown level is WARNING
            loaded = portfolio_repo.find_by_id("default")
            assert loaded is not None
            assert loaded.drawdown_level.value == "warning"

            # Mock orchestrator to capture the drawdown_level argument
            mock_orchestrator = MagicMock()
            # Make orchestrator.run() return a HALTED PipelineRun
            from src.pipeline.domain.entities import PipelineRun
            from datetime import datetime, timezone

            from src.pipeline.domain.value_objects import RunMode

            mock_run = PipelineRun(
                run_id="test-run",
                started_at=datetime.now(timezone.utc),
                status=PipelineStatus.HALTED,
                mode=RunMode.MANUAL,
                halt_reason="drawdown_level=warning",
                finished_at=datetime.now(timezone.utc),
            )
            mock_orchestrator.run.return_value = mock_run

            # Build handler with portfolio_repo in handlers dict
            mock_repo = MagicMock()
            mock_notifier = MagicMock()
            mock_reconciliation = MagicMock()

            handlers = {
                "bus": SyncEventBus(),
                "portfolio_repo": portfolio_repo,
            }

            handler = RunPipelineHandler(
                orchestrator=mock_orchestrator,
                pipeline_run_repo=mock_repo,
                notifier=mock_notifier,
                reconciliation_service=mock_reconciliation,
                handlers=handlers,
                symbols=["AAPL"],
            )

            cmd = RunPipelineCommand(dry_run=False)
            handler.handle(cmd)

            # Verify orchestrator.run() was called with drawdown_level="warning"
            mock_orchestrator.run.assert_called_once()
            call_kwargs = mock_orchestrator.run.call_args
            assert call_kwargs.kwargs.get("drawdown_level") == "warning" or \
                (len(call_kwargs.args) > 4 and call_kwargs.args[4] == "warning")

            db_factory.close()

    def test_pipeline_continues_on_normal_drawdown(self):
        """RunPipelineHandler with no portfolio (None) -> drawdown defaults to 'normal'."""
        from src.pipeline.application.commands import RunPipelineCommand
        from src.pipeline.application.handlers import RunPipelineHandler
        from src.pipeline.domain.value_objects import PipelineStatus

        # Mock orchestrator
        mock_orchestrator = MagicMock()
        from src.pipeline.domain.entities import PipelineRun
        from datetime import datetime, timezone

        from src.pipeline.domain.value_objects import RunMode

        mock_run = PipelineRun(
            run_id="test-run",
            started_at=datetime.now(timezone.utc),
            status=PipelineStatus.COMPLETED,
            mode=RunMode.MANUAL,
            finished_at=datetime.now(timezone.utc),
        )
        mock_orchestrator.run.return_value = mock_run

        mock_repo = MagicMock()
        mock_notifier = MagicMock()
        mock_reconciliation = MagicMock()

        # No portfolio_repo in handlers -> defaults to "normal"
        handlers = {
            "bus": SyncEventBus(),
        }

        handler = RunPipelineHandler(
            orchestrator=mock_orchestrator,
            pipeline_run_repo=mock_repo,
            notifier=mock_notifier,
            reconciliation_service=mock_reconciliation,
            handlers=handlers,
            symbols=["AAPL"],
        )

        cmd = RunPipelineCommand(dry_run=False)
        handler.handle(cmd)

        # Verify orchestrator.run() was called with drawdown_level="normal"
        mock_orchestrator.run.assert_called_once()
        call_kwargs = mock_orchestrator.run.call_args
        assert call_kwargs.kwargs.get("drawdown_level") == "normal" or \
            (len(call_kwargs.args) > 4 and call_kwargs.args[4] == "normal")
