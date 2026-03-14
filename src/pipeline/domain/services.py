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
            plan_stage, trade_plans = self._run_plan(handlers, signal_results, score_results)
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
                execute_stage = self._run_execute(handlers, trade_plans)
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

    def _run_plan(
        self,
        handlers: dict,
        signal_results: dict[str, dict],
        score_results: dict[str, dict],
    ) -> tuple[StageResult, list]:
        """Stage 5: Generate trade plans from actionable signals.

        For each BUY/SELL signal, fetches market data via injected data_client
        and calls trade_plan_handler.generate(). Uses valuation_reader callable
        (injected from infrastructure layer) for intrinsic_value lookup.
        """
        from src.execution.application.commands import GenerateTradePlanCommand

        started = datetime.now(timezone.utc)
        trade_plan_handler = handlers["trade_plan_handler"]
        capital = handlers.get("capital", 100_000.0)
        data_client = handlers.get("data_client")

        plans: list = []
        succeeded = 0
        failed = 0

        for sym, sig_data in signal_results.items():
            direction = sig_data.get("direction", "HOLD") if isinstance(sig_data, dict) else "HOLD"
            if direction not in ("BUY", "SELL"):
                continue

            try:
                entry_price = 0.0
                atr = 3.0

                if data_client is not None:
                    full_data = data_client.get_full(sym)
                    entry_price = full_data.get("price", {}).get("close", 0.0)
                    atr = full_data.get("indicators", {}).get("atr21", 0.0) or 3.0

                score_data = score_results.get(sym, {})
                composite_score = score_data.get("composite_score", 50.0)
                margin_of_safety = score_data.get("margin_of_safety", 0.0)
                reasoning = sig_data.get("reasoning", sig_data.get("reasoning_trace", ""))

                # Query intrinsic_value via injected valuation_reader (DDD-compliant)
                intrinsic_value = self._get_intrinsic_value(
                    handlers, sym, entry_price, margin_of_safety,
                )

                cmd = GenerateTradePlanCommand(
                    symbol=sym,
                    entry_price=entry_price,
                    atr=atr,
                    capital=capital,
                    peak_value=capital,
                    current_value=capital,
                    intrinsic_value=intrinsic_value,
                    composite_score=composite_score,
                    margin_of_safety=margin_of_safety,
                    signal_direction=direction,
                    reasoning_trace=reasoning,
                )
                plan = trade_plan_handler.generate(cmd)
                if plan is not None:
                    plans.append(plan)
                    succeeded += 1
                else:
                    logger.info("Plan rejected by risk gates for %s", sym)
            except Exception as e:
                logger.warning("Plan generation failed for %s: %s", sym, e)
                failed += 1

        return StageResult(
            stage_name="plan",
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status="success" if failed == 0 else "partial",
            symbols_processed=len(signal_results),
            symbols_succeeded=succeeded,
            symbols_failed=failed,
            succeeded_symbols=[p.symbol for p in plans] if plans else [],
        ), plans

    def _get_intrinsic_value(
        self,
        handlers: dict,
        symbol: str,
        entry_price: float,
        margin_of_safety: float,
    ) -> float:
        """Get intrinsic value via injected reader, fallback to heuristic.

        Priority:
        1. valuation_reader callable (injected from infrastructure layer)
        2. Heuristic: entry_price * (1 + margin_of_safety) if margin_of_safety > 0
        3. Fallback: entry_price * 1.2
        """
        valuation_reader = handlers.get("valuation_reader")
        if valuation_reader is not None:
            try:
                value = valuation_reader(symbol)
                if value is not None and value > 0:
                    return value
            except Exception:
                pass  # Fall through to heuristic

        # Heuristic fallback
        if margin_of_safety > 0:
            return entry_price * (1 + margin_of_safety)
        return entry_price * 1.2

    def _run_execute(self, handlers: dict, trade_plans: list) -> StageResult:
        """Stage 6: Submit generated trade plans via approval gate + execute.

        For each TradePlan: check approval gate, then approve+execute if passed.
        Rejected trades are queued for manual review.
        If no approval gate configured, skip execution (backward compatible).
        """
        from src.execution.application.commands import ApproveTradePlanCommand, ExecuteOrderCommand

        started = datetime.now(timezone.utc)

        # Check for approval gate (backward compatible)
        approval_gate = handlers.get("approval_gate")
        approval_handler = handlers.get("approval_handler")

        if approval_gate is None or approval_handler is None:
            logger.info("No approval gate configured -- skipping execution")
            return StageResult(
                stage_name="execute",
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="skipped",
                symbols_processed=0,
                symbols_succeeded=0,
                symbols_failed=0,
            )

        # Get active approval
        status = approval_handler.get_status()
        approval = status.get("approval")

        if approval is None:
            logger.info("No active approval -- skipping execution")
            return StageResult(
                stage_name="execute",
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                status="skipped",
                symbols_processed=0,
                symbols_succeeded=0,
                symbols_failed=0,
            )

        # Check expiration warning (24h)
        notifier = handlers.get("notifier")
        hours_remaining = (approval.expires_at - datetime.now(timezone.utc)).total_seconds() / 3600
        if 0 < hours_remaining <= 24 and notifier:
            notifier.notify(f"Approval expires in {hours_remaining:.0f}h")

        # Get today's budget tracker
        budget_repo = handlers.get("budget_repo")
        if budget_repo is None:
            raise RuntimeError("budget_repo not configured")
        budget = budget_repo.get_or_create_today(approval.daily_budget_cap)

        # Get current regime for gate check
        regime_handler = handlers.get("regime_handler")
        current_regime = "Bull"  # safe default
        if regime_handler:
            try:
                from src.regime.application.commands import DetectRegimeCommand
                regime_result = regime_handler.handle(
                    DetectRegimeCommand(vix=0.0, sp500_price=0.0, sp500_ma200=0.0, adx=0.0, yield_spread=0.0)
                )
                regime_data = regime_result.value if hasattr(regime_result, "value") else regime_result
                if isinstance(regime_data, dict):
                    current_regime = regime_data.get("regime_type", "Bull")
            except Exception:
                pass  # Use default regime

        trade_plan_handler = handlers["trade_plan_handler"]
        review_queue_repo = handlers.get("review_queue_repo")
        succeeded = 0
        failed = 0
        queued = 0

        # Order monitor and trading stream managed by dashboard app lifecycle
        order_monitor = handlers.get("order_monitor")
        halted = False

        try:
            for plan in trade_plans:
                try:
                    plan_score = getattr(plan, "composite_score", 50.0)
                    plan_position_pct = getattr(plan, "position_pct", 5.0)
                    plan_position_value = getattr(plan, "position_value", 0.0)

                    gate_result = approval_gate.check(
                        plan_symbol=plan.symbol,
                        plan_score=plan_score,
                        plan_position_pct=plan_position_pct,
                        current_regime=current_regime,
                        daily_remaining=budget.remaining,
                        plan_position_value=plan_position_value,
                        approval=approval,
                    )

                    if gate_result.approved:
                        trade_plan_handler.approve(
                            ApproveTradePlanCommand(symbol=plan.symbol, approved=True)
                        )
                        result = trade_plan_handler.execute(ExecuteOrderCommand(symbol=plan.symbol))
                        succeeded += 1

                        # Track order in monitor if available
                        if order_monitor is not None:
                            order_id = getattr(result, "order_id", None)
                            if order_id:
                                order_monitor.track(order_id)

                        # Record spend in budget tracker
                        budget.record_spend(plan_position_value)
                        budget_repo.save(budget)

                        # Budget 80% warning
                        if budget.spent >= budget.budget_cap * 0.8 and notifier:
                            pct = (budget.spent / budget.budget_cap) * 100
                            notifier.notify(
                                f"Budget {pct:.0f}% used (${budget.spent:.0f}/${budget.budget_cap:.0f})"
                            )
                    else:
                        # Rejected -- queue for manual review
                        import json as _json
                        from src.approval.domain.value_objects import TradeReviewItem

                        review_item = TradeReviewItem(
                            symbol=plan.symbol,
                            plan_json=_json.dumps({"symbol": plan.symbol, "score": plan_score}),
                            rejection_reason=gate_result.reason,
                        )
                        if review_queue_repo:
                            review_queue_repo.add(review_item)
                        queued += 1
                        logger.info("Trade %s queued for review: %s", plan.symbol, gate_result.reason)

                except Exception as e:
                    # Check if circuit breaker tripped
                    from src.execution.infrastructure.safe_adapter import CircuitBreakerTrippedError
                    if isinstance(e, CircuitBreakerTrippedError):
                        logger.error("Circuit breaker tripped: %s -- halting execution", e)
                        halted = True
                        break
                    logger.error("Execution failed for %s: %s", plan.symbol, e)
                    failed += 1

        finally:
            pass  # Monitor/stream lifecycle managed by dashboard app

        total = succeeded + queued + failed
        status = "halted" if halted else ("success" if failed == 0 and queued == 0 else "partial")
        return StageResult(
            stage_name="execute",
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            status=status,
            symbols_processed=total,
            symbols_succeeded=succeeded,
            symbols_failed=failed,
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
            reasons.append("Regime: Crisis")
        if drawdown_level.lower() in _HALT_DRAWDOWN_LEVELS:
            reasons.append(f"Drawdown: {drawdown_level}")
        return "; ".join(reasons)
