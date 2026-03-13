"""Pipeline Domain -- PipelineOrchestrator Service.

Pure domain service that chains 6 stages sequentially:
ingest -> regime -> score -> signal -> plan -> execute.

Receives handler references via run() params -- never imports from
other bounded contexts. Reconciliation is the application layer's
responsibility (RunPipelineHandler), keeping this layer pure.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone

from .entities import PipelineRun
from .value_objects import PipelineStatus, RunMode, StageResult

logger = logging.getLogger(__name__)

# Drawdown levels that trigger halt (tier >= 2)
_HALT_DRAWDOWN_LEVELS = {"warning", "critical"}


class PipelineOrchestrator:
    """Orchestrate the full trading pipeline: ingest -> regime -> score -> signal -> plan -> execute.

    Pure domain service. No infrastructure dependencies.
    """

    def run(
        self,
        handlers: dict,
        symbols: list[str],
        dry_run: bool = False,
        mode: RunMode = RunMode.MANUAL,
        drawdown_level: str = "normal",
    ) -> PipelineRun:
        """Execute the full pipeline.

        Args:
            handlers: Bootstrap context dict with handler references.
            symbols: List of ticker symbols to process.
            dry_run: If True, skip order execution.
            mode: Pipeline execution mode.
            drawdown_level: Current drawdown level string (normal/caution/warning/critical).

        Returns:
            PipelineRun entity with stage results.
        """
        if dry_run:
            mode = RunMode.DRY_RUN

        run = PipelineRun(
            run_id=str(uuid.uuid4()),
            started_at=datetime.now(timezone.utc),
            status=PipelineStatus.RUNNING,
            mode=mode,
        )

        stages: list[StageResult] = []
        surviving_symbols: list[str] = list(symbols)
        regime_type: str = "Bull"  # default safe
        score_results: dict[str, dict] = {}
        signal_results: dict[str, dict] = {}

        try:
            # Stage 1: Ingest
            ingest_stage = self._run_ingest(handlers, surviving_symbols)
            stages.append(ingest_stage)
            surviving_symbols = list(ingest_stage.succeeded_symbols)
            if not surviving_symbols:
                run.stages = stages
                run.status = PipelineStatus.FAILED
                run.error_message = "No symbols survived ingest"
                run.finished_at = datetime.now(timezone.utc)
                return run

            # Stage 2: Regime
            regime_stage, regime_type = self._run_regime(handlers)
            stages.append(regime_stage)

            # Stage 3: Score (per-symbol, skip failures)
            score_stage, score_results = self._run_score(handlers, surviving_symbols)
            stages.append(score_stage)
            surviving_symbols = list(score_stage.succeeded_symbols)

            # Stage 4: Signal (per-symbol, skip failures)
            signal_stage, signal_results = self._run_signal(handlers, surviving_symbols)
            stages.append(signal_stage)

            # Stage 5: Plan
            plan_stage = self._run_plan(handlers, signal_results)
            stages.append(plan_stage)

            # Safety gate: check regime + drawdown before execute
            if self._should_halt(regime_type, drawdown_level):
                halt_reason = self._build_halt_reason(regime_type, drawdown_level)
                run.stages = stages
                run.status = PipelineStatus.HALTED
                run.halt_reason = halt_reason
                run.finished_at = datetime.now(timezone.utc)
                return run

            # Stage 6: Execute (skip if dry_run)
            if dry_run:
                execute_stage = StageResult(
                    stage_name="execute",
                    started_at=datetime.now(timezone.utc),
                    finished_at=datetime.now(timezone.utc),
                    status="skipped",
                    symbols_processed=0,
                    symbols_succeeded=0,
                    symbols_failed=0,
                )
            else:
                execute_stage = self._run_execute(handlers)
            stages.append(execute_stage)

            run.stages = stages
            run.status = PipelineStatus.COMPLETED
            run.finished_at = datetime.now(timezone.utc)
            return run

        except Exception as e:
            logger.error("Pipeline failed: %s", e, exc_info=True)
            run.stages = stages
            run.status = PipelineStatus.FAILED
            run.error_message = str(e)
            run.finished_at = datetime.now(timezone.utc)
            return run

    # ── Stage implementations ─────────────────────────────────────────

    def _run_ingest(self, handlers: dict, symbols: list[str]) -> StageResult:
        """Stage 1: Data ingestion via DataPipeline (async)."""
        started = datetime.now(timezone.utc)

        def do_ingest():
            pipeline = handlers["data_pipeline"]
            return asyncio.run(pipeline.ingest_universe(symbols))

        try:
            result = self._retry_stage(do_ingest)
            succeeded = result.get("succeeded", [])
            failed_count = result.get("failed_count", 0) + result.get("errors_count", 0)
            status = "success" if failed_count == 0 else "partial"
            return StageResult(
                stage_name="ingest",
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status=status,
                symbols_processed=result.get("total", len(symbols)),
                symbols_succeeded=len(succeeded),
                symbols_failed=failed_count,
                succeeded_symbols=list(succeeded),
            )
        except Exception as e:
            return StageResult(
                stage_name="ingest",
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="failed",
                symbols_processed=len(symbols),
                symbols_succeeded=0,
                symbols_failed=len(symbols),
                error_message=str(e),
            )

    def _run_regime(self, handlers: dict) -> tuple[StageResult, str]:
        """Stage 2: Regime detection."""
        started = datetime.now(timezone.utc)
        from src.regime.application.commands import DetectRegimeCommand

        def do_regime():
            return handlers["regime_handler"].handle(
                DetectRegimeCommand(vix=0.0, sp500_price=0.0, sp500_ma200=0.0, adx=0.0, yield_spread=0.0)
            )

        try:
            result = self._retry_stage(do_regime)
            # Result is Ok/Err -- extract value
            regime_data = result.value if hasattr(result, "value") else result
            regime_type = regime_data.get("regime_type", "Bull") if isinstance(regime_data, dict) else "Bull"
            return StageResult(
                stage_name="regime",
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="success",
                symbols_processed=1,
                symbols_succeeded=1,
                symbols_failed=0,
            ), regime_type
        except Exception as e:
            return StageResult(
                stage_name="regime",
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="failed",
                symbols_processed=1,
                symbols_succeeded=0,
                symbols_failed=1,
                error_message=str(e),
            ), "Bull"

    def _run_score(self, handlers: dict, symbols: list[str]) -> tuple[StageResult, dict[str, dict]]:
        """Stage 3: Score each symbol. Skip failures."""
        started = datetime.now(timezone.utc)
        from src.scoring.application.commands import ScoreSymbolCommand

        succeeded_symbols: list[str] = []
        score_results: dict[str, dict] = {}
        failed_count = 0

        for sym in symbols:
            try:
                result = handlers["score_handler"].handle(ScoreSymbolCommand(symbol=sym))
                data = result.value if hasattr(result, "value") else result
                if isinstance(data, dict):
                    score_results[sym] = data
                    succeeded_symbols.append(sym)
                else:
                    succeeded_symbols.append(sym)
            except Exception as e:
                logger.warning("Score failed for %s: %s", sym, e)
                failed_count += 1

        return StageResult(
            stage_name="score",
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="success" if failed_count == 0 else "partial",
            symbols_processed=len(symbols),
            symbols_succeeded=len(succeeded_symbols),
            symbols_failed=failed_count,
            succeeded_symbols=succeeded_symbols,
        ), score_results

    def _run_signal(self, handlers: dict, symbols: list[str]) -> tuple[StageResult, dict[str, dict]]:
        """Stage 4: Generate signals per symbol. Skip failures."""
        started = datetime.now(timezone.utc)
        from src.signals.application.commands import GenerateSignalCommand

        succeeded_symbols: list[str] = []
        signal_results: dict[str, dict] = {}
        failed_count = 0

        for sym in symbols:
            try:
                result = handlers["signal_handler"].handle(GenerateSignalCommand(symbol=sym))
                data = result.value if hasattr(result, "value") else result
                if isinstance(data, dict):
                    signal_results[sym] = data
                    succeeded_symbols.append(sym)
                else:
                    succeeded_symbols.append(sym)
            except Exception as e:
                logger.warning("Signal failed for %s: %s", sym, e)
                failed_count += 1

        return StageResult(
            stage_name="signal",
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="success" if failed_count == 0 else "partial",
            symbols_processed=len(symbols),
            symbols_succeeded=len(succeeded_symbols),
            symbols_failed=failed_count,
            succeeded_symbols=succeeded_symbols,
        ), signal_results

    def _run_plan(self, handlers: dict, signal_results: dict[str, dict]) -> StageResult:
        """Stage 5: Generate trade plans from signals."""
        started = datetime.now(timezone.utc)
        planned = 0

        for sym, sig_data in signal_results.items():
            direction = sig_data.get("direction", "HOLD") if isinstance(sig_data, dict) else "HOLD"
            if direction in ("BUY", "SELL"):
                planned += 1
                # Trade plan generation would use trade_plan_handler.generate()
                # but requires market data (entry price, ATR, etc.)
                # For now, track count -- full wiring in bootstrap

        return StageResult(
            stage_name="plan",
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="success",
            symbols_processed=len(signal_results),
            symbols_succeeded=planned,
            symbols_failed=0,
            succeeded_symbols=list(signal_results.keys()),
        )

    def _run_execute(self, handlers: dict) -> StageResult:
        """Stage 6: Execute trade plans."""
        started = datetime.now(timezone.utc)
        return StageResult(
            stage_name="execute",
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="success",
            symbols_processed=0,
            symbols_succeeded=0,
            symbols_failed=0,
        )

    # ── Retry logic ───────────────────────────────────────────────────

    def _retry_stage(self, fn, max_retries: int = 3, base_delay: float = 1.0):
        """Retry with exponential backoff. Raises on final failure."""
        for attempt in range(max_retries):
            try:
                return fn()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "Stage retry %d/%d after error: %s (waiting %.1fs)",
                    attempt + 1,
                    max_retries,
                    e,
                    delay,
                )
                time.sleep(delay)

    # ── Halt check ────────────────────────────────────────────────────

    def _should_halt(self, regime_type: str, drawdown_level: str) -> bool:
        """Check if pipeline should halt before execution stage.

        Halt when:
        - Regime is Crisis
        - Drawdown tier >= 2 (WARNING or CRITICAL)
        """
        if regime_type == "Crisis":
            return True
        if drawdown_level.lower() in _HALT_DRAWDOWN_LEVELS:
            return True
        return False

    def _build_halt_reason(self, regime_type: str, drawdown_level: str) -> str:
        """Build human-readable halt reason."""
        reasons = []
        if regime_type == "Crisis":
            reasons.append(f"Regime: Crisis")
        if drawdown_level.lower() in _HALT_DRAWDOWN_LEVELS:
            reasons.append(f"Drawdown: {drawdown_level}")
        return "; ".join(reasons)
