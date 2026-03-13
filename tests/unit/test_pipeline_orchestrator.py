"""Tests for PipelineOrchestrator domain service and application handlers.

Covers: full pipeline run, dry-run skip, halt on crisis, halt on drawdown,
retry on transient failure, partial symbol failure, reconciliation gate.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.domain.entities import PipelineRun
from src.pipeline.domain.value_objects import PipelineStatus, RunMode, StageResult
from src.pipeline.domain.services import PipelineOrchestrator
from src.pipeline.application.commands import RunPipelineCommand, GetPipelineStatusQuery
from src.pipeline.application.handlers import RunPipelineHandler, PipelineStatusHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_handlers(
    ingest_result: dict | None = None,
    regime_result: dict | None = None,
    score_results: dict[str, dict] | None = None,
    signal_results: dict[str, dict] | None = None,
    score_error_symbols: set[str] | None = None,
    signal_error_symbols: set[str] | None = None,
) -> dict:
    """Build a mock handlers dict that mimics bootstrap context."""

    # Default successful results
    if ingest_result is None:
        ingest_result = {
            "total": 3,
            "succeeded": ["AAPL", "MSFT", "GOOGL"],
            "succeeded_count": 3,
            "failed": [],
            "failed_count": 0,
            "errors": [],
            "errors_count": 0,
        }

    if regime_result is None:
        from src.shared.domain import Ok
        regime_result = Ok({
            "regime_type": "Bull",
            "confidence": 0.85,
            "confirmed_days": 5,
            "is_confirmed": True,
        })

    if score_results is None:
        score_results = {
            "AAPL": {"symbol": "AAPL", "composite_score": 75.0, "safety_passed": True},
            "MSFT": {"symbol": "MSFT", "composite_score": 68.0, "safety_passed": True},
            "GOOGL": {"symbol": "GOOGL", "composite_score": 72.0, "safety_passed": True},
        }

    if signal_results is None:
        signal_results = {
            "AAPL": {"symbol": "AAPL", "direction": "BUY", "strength": "STRONG"},
            "MSFT": {"symbol": "MSFT", "direction": "BUY", "strength": "MODERATE"},
            "GOOGL": {"symbol": "GOOGL", "direction": "HOLD", "strength": "WEAK"},
        }

    score_error_symbols = score_error_symbols or set()
    signal_error_symbols = signal_error_symbols or set()

    # Data pipeline (async)
    data_pipeline = MagicMock()

    async def mock_ingest(*args, **kwargs):
        return ingest_result

    data_pipeline.ingest_universe = mock_ingest

    # Regime handler
    regime_handler = MagicMock()
    regime_handler.handle.return_value = regime_result

    # Score handler (per symbol)
    score_handler = MagicMock()

    def mock_score(cmd):
        from src.shared.domain import Ok
        sym = cmd.symbol.upper()
        if sym in score_error_symbols:
            raise RuntimeError(f"Score failed for {sym}")
        return Ok(score_results.get(sym, {"symbol": sym, "composite_score": 50.0, "safety_passed": True}))

    score_handler.handle.side_effect = mock_score

    # Signal handler (per symbol)
    signal_handler = MagicMock()

    def mock_signal(cmd):
        from src.shared.domain import Ok
        sym = cmd.symbol.upper()
        if sym in signal_error_symbols:
            raise RuntimeError(f"Signal failed for {sym}")
        return Ok(signal_results.get(sym, {"symbol": sym, "direction": "HOLD", "strength": "WEAK"}))

    signal_handler.handle.side_effect = mock_signal

    # Trade plan handler
    trade_plan_handler = MagicMock()
    trade_plan_handler.generate.return_value = MagicMock()  # returns a plan
    trade_plan_handler.execute.return_value = MagicMock(status="filled")

    return {
        "data_pipeline": data_pipeline,
        "regime_handler": regime_handler,
        "score_handler": score_handler,
        "signal_handler": signal_handler,
        "trade_plan_handler": trade_plan_handler,
        "capital": 100_000.0,
        "portfolio_handler": MagicMock(),
    }


# ---------------------------------------------------------------------------
# PipelineOrchestrator Tests
# ---------------------------------------------------------------------------

class TestPipelineOrchestrator:
    """Test PipelineOrchestrator domain service."""

    def test_full_pipeline_run_completes(self):
        """Full pipeline run: 6 stages complete successfully."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()
        symbols = ["AAPL", "MSFT", "GOOGL"]

        run = orchestrator.run(handlers=handlers, symbols=symbols)

        assert run.status == PipelineStatus.COMPLETED
        assert len(run.stages) >= 5  # at least ingest through plan
        assert run.finished_at is not None

    def test_dry_run_skips_execution(self):
        """Dry-run mode: everything runs except execute stage."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()
        symbols = ["AAPL", "MSFT"]

        run = orchestrator.run(handlers=handlers, symbols=symbols, dry_run=True)

        assert run.status == PipelineStatus.COMPLETED
        assert run.mode == RunMode.DRY_RUN
        # Execute stage should be skipped
        stage_names = [s.stage_name for s in run.stages]
        execute_stages = [s for s in run.stages if s.stage_name == "execute"]
        if execute_stages:
            assert execute_stages[0].status == "skipped"

    def test_halt_on_crisis_regime(self):
        """Pipeline halts before execution when regime is Crisis."""
        from src.shared.domain import Ok
        crisis_result = Ok({
            "regime_type": "Crisis",
            "confidence": 0.95,
            "confirmed_days": 3,
            "is_confirmed": True,
        })
        handlers = _make_handlers(regime_result=crisis_result)
        orchestrator = PipelineOrchestrator()

        run = orchestrator.run(handlers=handlers, symbols=["AAPL"])

        assert run.status == PipelineStatus.HALTED
        assert run.halt_reason is not None
        assert "crisis" in run.halt_reason.lower() or "Crisis" in run.halt_reason

    def test_halt_on_warning_drawdown(self):
        """Pipeline halts when drawdown level is WARNING."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()
        # Mock portfolio_handler to return WARNING drawdown
        handlers["portfolio_handler"].get_drawdown_level.return_value = "warning"

        run = orchestrator.run(
            handlers=handlers,
            symbols=["AAPL"],
            drawdown_level="warning",
        )

        assert run.status == PipelineStatus.HALTED
        assert run.halt_reason is not None

    def test_halt_on_critical_drawdown(self):
        """Pipeline halts when drawdown level is CRITICAL."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()

        run = orchestrator.run(
            handlers=handlers,
            symbols=["AAPL"],
            drawdown_level="critical",
        )

        assert run.status == PipelineStatus.HALTED

    def test_retry_on_transient_failure(self):
        """Stage retries 3 times with exponential backoff on transient failure."""
        orchestrator = PipelineOrchestrator()

        call_count = 0

        def failing_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Transient error")
            return "success"

        with patch("time.sleep"):  # Skip actual delays in test
            result = orchestrator._retry_stage(failing_fn, max_retries=3, base_delay=0.01)

        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted_raises(self):
        """After 3 failed retries, exception is raised."""
        orchestrator = PipelineOrchestrator()

        def always_fails():
            raise RuntimeError("Persistent error")

        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="Persistent error"):
                orchestrator._retry_stage(always_fails, max_retries=3, base_delay=0.01)

    def test_partial_ingest_continues_with_survivors(self):
        """Partial ingest failure: continue with succeeded symbols only."""
        partial_ingest = {
            "total": 3,
            "succeeded": ["AAPL", "MSFT"],
            "succeeded_count": 2,
            "failed": ["GOOGL"],
            "failed_count": 1,
            "errors": [],
            "errors_count": 0,
        }
        handlers = _make_handlers(ingest_result=partial_ingest)
        orchestrator = PipelineOrchestrator()

        run = orchestrator.run(handlers=handlers, symbols=["AAPL", "MSFT", "GOOGL"])

        # Pipeline should complete, not fail
        assert run.status in (PipelineStatus.COMPLETED, PipelineStatus.HALTED)
        # Ingest stage should report partial success
        ingest_stage = next(s for s in run.stages if s.stage_name == "ingest")
        assert ingest_stage.symbols_succeeded == 2

    def test_per_symbol_score_failure_skips_symbol(self):
        """Score failure for one symbol: skip that symbol, continue rest."""
        handlers = _make_handlers(score_error_symbols={"MSFT"})
        orchestrator = PipelineOrchestrator()

        run = orchestrator.run(handlers=handlers, symbols=["AAPL", "MSFT", "GOOGL"])

        assert run.status in (PipelineStatus.COMPLETED, PipelineStatus.HALTED)
        score_stage = next(s for s in run.stages if s.stage_name == "score")
        assert score_stage.symbols_failed >= 1

    def test_per_symbol_signal_failure_skips_symbol(self):
        """Signal failure for one symbol: skip that symbol, continue rest."""
        handlers = _make_handlers(signal_error_symbols={"GOOGL"})
        orchestrator = PipelineOrchestrator()

        run = orchestrator.run(handlers=handlers, symbols=["AAPL", "MSFT", "GOOGL"])

        assert run.status in (PipelineStatus.COMPLETED, PipelineStatus.HALTED)
        signal_stage = next(s for s in run.stages if s.stage_name == "signal")
        assert signal_stage.symbols_failed >= 1

    def test_run_mode_set_correctly(self):
        """RunMode is set correctly based on input."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()

        run = orchestrator.run(handlers=handlers, symbols=["AAPL"], mode=RunMode.AUTO)
        assert run.mode == RunMode.AUTO

        run2 = orchestrator.run(handlers=handlers, symbols=["AAPL"], dry_run=True)
        assert run2.mode == RunMode.DRY_RUN


# ---------------------------------------------------------------------------
# Application Handler Tests
# ---------------------------------------------------------------------------

class TestRunPipelineHandler:
    """Test RunPipelineHandler application handler."""

    def test_handler_calls_reconciliation_first(self):
        """RunPipelineHandler calls reconciliation check before orchestrator."""
        orchestrator = MagicMock()
        orchestrator.run.return_value = PipelineRun(
            run_id="test-1",
            started_at=datetime.now(timezone.utc),
            status=PipelineStatus.COMPLETED,
            mode=RunMode.MANUAL,
            finished_at=datetime.now(timezone.utc),
        )

        repo = MagicMock()
        notifier = MagicMock()
        reconciliation = MagicMock()
        handlers = _make_handlers()

        handler = RunPipelineHandler(
            orchestrator=orchestrator,
            pipeline_run_repo=repo,
            notifier=notifier,
            reconciliation_service=reconciliation,
            handlers=handlers,
        )

        result = handler.handle(RunPipelineCommand())
        reconciliation.check_and_halt.assert_called_once()
        assert result.status == PipelineStatus.COMPLETED

    def test_handler_aborts_on_reconciliation_error(self):
        """ReconciliationError causes FAILED pipeline run."""
        from src.execution.infrastructure.reconciliation import ReconciliationError, Discrepancy

        orchestrator = MagicMock()
        repo = MagicMock()
        notifier = MagicMock()
        reconciliation = MagicMock()
        reconciliation.check_and_halt.side_effect = ReconciliationError(
            [Discrepancy(symbol="AAPL", discrepancy_type="qty_mismatch", local_qty=10, broker_qty=5)]
        )
        handlers = _make_handlers()

        handler = RunPipelineHandler(
            orchestrator=orchestrator,
            pipeline_run_repo=repo,
            notifier=notifier,
            reconciliation_service=reconciliation,
            handlers=handlers,
        )

        result = handler.handle(RunPipelineCommand())
        assert result.status == PipelineStatus.FAILED
        assert "reconciliation" in (result.error_message or "").lower() or "mismatch" in (result.error_message or "").lower()
        # Orchestrator should NOT have been called
        orchestrator.run.assert_not_called()

    def test_handler_saves_run_and_notifies(self):
        """Handler saves PipelineRun to repo and sends notification."""
        orchestrator = MagicMock()
        orchestrator.run.return_value = PipelineRun(
            run_id="test-2",
            started_at=datetime.now(timezone.utc),
            status=PipelineStatus.COMPLETED,
            mode=RunMode.MANUAL,
            finished_at=datetime.now(timezone.utc),
        )

        repo = MagicMock()
        notifier = MagicMock()
        reconciliation = MagicMock()
        handlers = _make_handlers()

        handler = RunPipelineHandler(
            orchestrator=orchestrator,
            pipeline_run_repo=repo,
            notifier=notifier,
            reconciliation_service=reconciliation,
            handlers=handlers,
        )

        result = handler.handle(RunPipelineCommand())
        repo.save.assert_called_once()
        notifier.notify.assert_called_once()


class TestPlanStage:
    """Test _run_plan generates TradePlan objects from signal results."""

    def test_plan_stage_generates_trade_plans(self):
        """_run_plan calls trade_plan_handler.generate for BUY signals."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()
        signal_results = {
            "AAPL": {"symbol": "AAPL", "direction": "BUY", "strength": "STRONG", "reasoning": "Strong momentum"},
            "MSFT": {"symbol": "MSFT", "direction": "BUY", "strength": "MODERATE", "reasoning": "Value play"},
        }
        score_results = {
            "AAPL": {"composite_score": 75.0, "margin_of_safety": 0.15},
            "MSFT": {"composite_score": 68.0, "margin_of_safety": 0.10},
        }

        with patch("core.data.client.DataClient") as mock_dc_cls:
            mock_client = MagicMock()
            mock_client.get_full.return_value = {
                "price": {"close": 150.0},
                "indicators": {"atr21": 5.0},
            }
            mock_dc_cls.return_value = mock_client

            stage, plans = orchestrator._run_plan(handlers, signal_results, score_results)

        assert stage.stage_name == "plan"
        assert stage.symbols_succeeded == 2
        assert len(plans) == 2
        assert handlers["trade_plan_handler"].generate.call_count == 2

    def test_plan_stage_skips_hold_signals(self):
        """HOLD signals are not sent to trade_plan_handler."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()
        signal_results = {
            "AAPL": {"symbol": "AAPL", "direction": "HOLD", "strength": "WEAK"},
            "GOOGL": {"symbol": "GOOGL", "direction": "HOLD", "strength": "WEAK"},
        }
        score_results = {}

        with patch("core.data.client.DataClient") as mock_dc_cls:
            stage, plans = orchestrator._run_plan(handlers, signal_results, score_results)

        assert stage.symbols_succeeded == 0
        assert len(plans) == 0
        handlers["trade_plan_handler"].generate.assert_not_called()

    def test_plan_stage_handles_data_fetch_failure(self):
        """DataClient failure for a symbol: skip that symbol, continue rest."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()
        signal_results = {
            "AAPL": {"symbol": "AAPL", "direction": "BUY", "strength": "STRONG", "reasoning": "Good"},
            "MSFT": {"symbol": "MSFT", "direction": "BUY", "strength": "MODERATE", "reasoning": "Ok"},
        }
        score_results = {
            "AAPL": {"composite_score": 75.0, "margin_of_safety": 0.15},
            "MSFT": {"composite_score": 68.0, "margin_of_safety": 0.10},
        }

        with patch("core.data.client.DataClient") as mock_dc_cls:
            mock_client = MagicMock()
            call_count = {"n": 0}

            def side_effect(sym):
                call_count["n"] += 1
                if sym == "AAPL":
                    raise RuntimeError("Network timeout")
                return {"price": {"close": 200.0}, "indicators": {"atr21": 4.0}}

            mock_client.get_full.side_effect = side_effect
            mock_dc_cls.return_value = mock_client

            stage, plans = orchestrator._run_plan(handlers, signal_results, score_results)

        # AAPL failed, MSFT succeeded
        assert stage.symbols_succeeded == 1
        assert stage.symbols_failed == 1
        assert len(plans) == 1

    def test_plan_stage_handles_rejected_plan(self):
        """generate() returns None (rejected by risk gates) -> not counted as succeeded."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()
        handlers["trade_plan_handler"].generate.return_value = None  # rejected
        signal_results = {
            "AAPL": {"symbol": "AAPL", "direction": "BUY", "strength": "STRONG", "reasoning": "Test"},
        }
        score_results = {
            "AAPL": {"composite_score": 75.0, "margin_of_safety": 0.15},
        }

        with patch("core.data.client.DataClient") as mock_dc_cls:
            mock_client = MagicMock()
            mock_client.get_full.return_value = {
                "price": {"close": 150.0},
                "indicators": {"atr21": 5.0},
            }
            mock_dc_cls.return_value = mock_client

            stage, plans = orchestrator._run_plan(handlers, signal_results, score_results)

        assert stage.symbols_succeeded == 0
        assert len(plans) == 0
        handlers["trade_plan_handler"].generate.assert_called_once()


class TestExecuteStage:
    """Test _run_execute submits orders via trade_plan_handler."""

    def test_execute_stage_submits_orders(self):
        """_run_execute calls approve + execute for each plan."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()

        plan1 = MagicMock()
        plan1.symbol = "AAPL"
        plan2 = MagicMock()
        plan2.symbol = "MSFT"

        stage = orchestrator._run_execute(handlers, [plan1, plan2])

        assert stage.stage_name == "execute"
        assert stage.symbols_processed == 2
        assert stage.symbols_succeeded == 2
        assert handlers["trade_plan_handler"].approve.call_count == 2
        assert handlers["trade_plan_handler"].execute.call_count == 2

    def test_execute_stage_handles_execution_failure(self):
        """Execute failure for one symbol: skip and continue."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()

        call_count = {"n": 0}

        def mock_execute(cmd):
            call_count["n"] += 1
            if cmd.symbol == "AAPL":
                raise RuntimeError("Broker timeout")
            return MagicMock(status="filled")

        handlers["trade_plan_handler"].execute.side_effect = mock_execute

        plan1 = MagicMock()
        plan1.symbol = "AAPL"
        plan2 = MagicMock()
        plan2.symbol = "MSFT"

        stage = orchestrator._run_execute(handlers, [plan1, plan2])

        assert stage.symbols_processed == 2
        assert stage.symbols_succeeded == 1
        assert stage.symbols_failed == 1

    def test_execute_stage_empty_plans(self):
        """Empty plan list returns success with 0 counts."""
        orchestrator = PipelineOrchestrator()
        handlers = _make_handlers()

        stage = orchestrator._run_execute(handlers, [])

        assert stage.symbols_processed == 0
        assert stage.symbols_succeeded == 0
        assert stage.status == "success"


class TestPipelineStatusHandler:
    """Test PipelineStatusHandler application handler."""

    def test_status_returns_recent_runs(self):
        """PipelineStatusHandler returns recent runs from repo."""
        repo = MagicMock()
        repo.get_recent.return_value = [
            PipelineRun(
                run_id="run-1",
                started_at=datetime.now(timezone.utc),
                status=PipelineStatus.COMPLETED,
                mode=RunMode.MANUAL,
            ),
        ]

        handler = PipelineStatusHandler(pipeline_run_repo=repo)
        result = handler.handle(GetPipelineStatusQuery(limit=5))
        repo.get_recent.assert_called_once_with(5)
        assert len(result) == 1
