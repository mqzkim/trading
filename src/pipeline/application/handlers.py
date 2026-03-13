"""Pipeline Application -- Handlers.

RunPipelineHandler: orchestrates reconciliation check, pipeline execution,
    persistence, and notification.
PipelineStatusHandler: queries recent pipeline runs.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from src.pipeline.domain.entities import PipelineRun
from src.pipeline.domain.repositories import IPipelineRunRepository
from src.pipeline.domain.services import PipelineOrchestrator
from src.pipeline.domain.value_objects import PipelineStatus, RunMode

from .commands import GetPipelineStatusQuery, RunPipelineCommand

logger = logging.getLogger(__name__)


class RunPipelineHandler:
    """Application handler for running the full trading pipeline.

    Responsibilities (in order):
    1. Call reconciliation_service.check_and_halt() -- abort if positions diverge
    2. Create PipelineRun entity
    3. Invoke PipelineOrchestrator.run()
    4. Save run to repository
    5. Send notification (complete/halt/error)
    6. Return PipelineRun result
    """

    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        pipeline_run_repo: IPipelineRunRepository,
        notifier,
        reconciliation_service,
        handlers: dict,
        symbols: list[str] | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._repo = pipeline_run_repo
        self._notifier = notifier
        self._reconciliation = reconciliation_service
        self._handlers = handlers
        self._symbols = symbols

    def handle(self, cmd: RunPipelineCommand) -> PipelineRun:
        """Execute the pipeline with reconciliation pre-check.

        Returns PipelineRun with final status.
        """
        # 1. Reconciliation check (application layer responsibility)
        try:
            self._reconciliation.check_and_halt()
        except Exception as e:
            logger.error("Reconciliation failed: %s", e)
            failed_run = PipelineRun(
                run_id=str(uuid.uuid4()),
                started_at=datetime.now(timezone.utc),
                status=PipelineStatus.FAILED,
                mode=cmd.mode if not cmd.dry_run else RunMode.DRY_RUN,
                finished_at=datetime.now(timezone.utc),
                error_message=f"Position reconciliation failed: {e}",
            )
            self._repo.save(failed_run)
            self._notifier.notify(
                title="Pipeline Failed: Reconciliation Error",
                message=str(e),
                level="error",
            )
            return failed_run

        # 2. Get symbols from handlers context or provided list
        symbols = self._symbols or self._get_default_symbols()

        # 3. Query portfolio drawdown level for safety gate
        drawdown_level = "normal"
        portfolio_repo = self._handlers.get("portfolio_repo")
        if portfolio_repo is not None:
            portfolio = portfolio_repo.find_by_id("default")
            if portfolio is not None:
                drawdown_level = portfolio.drawdown_level.value

        # 4. Run pipeline with drawdown state
        mode = RunMode.DRY_RUN if cmd.dry_run else cmd.mode
        run = self._orchestrator.run(
            handlers=self._handlers,
            symbols=symbols,
            dry_run=cmd.dry_run,
            mode=mode,
            drawdown_level=drawdown_level,
        )

        # 5. Save to repo
        self._repo.save(run)

        # 6. Notify based on result
        self._send_notification(run)

        # 7. Publish domain event to bus for SSE bridge
        self._publish_pipeline_event(run)

        return run

    def _get_default_symbols(self) -> list[str]:
        """Get default symbol universe from data pipeline."""
        try:
            from src.data_ingest.infrastructure.universe_provider import UniverseProvider
            provider = UniverseProvider()
            df = provider.get_universe()
            return df["ticker"].tolist()
        except Exception:
            logger.warning("Failed to get default universe, using empty list")
            return []

    def _publish_pipeline_event(self, run: PipelineRun) -> None:
        """Publish pipeline completion/halt event to bus for SSE updates."""
        bus = self._handlers.get("bus")
        if bus is None:
            return

        from src.pipeline.domain.events import PipelineCompletedEvent, PipelineHaltedEvent

        if run.status == PipelineStatus.COMPLETED:
            bus.publish(PipelineCompletedEvent(
                run_id=run.run_id,
                duration_seconds=run.duration.total_seconds() if run.duration else 0.0,
                symbols_succeeded=run.symbols_succeeded,
                mode=run.mode.value,
            ))
        elif run.status == PipelineStatus.HALTED:
            bus.publish(PipelineHaltedEvent(
                run_id=run.run_id,
                halt_reason=run.halt_reason or "",
                regime_type="",
                drawdown_level="",
            ))

    def _send_notification(self, run: PipelineRun) -> None:
        """Send notification based on pipeline result."""
        duration = run.duration
        duration_str = f"{duration.total_seconds():.0f}s" if duration else "N/A"

        if run.status == PipelineStatus.COMPLETED:
            self._notifier.notify(
                title="Pipeline Completed",
                message=(
                    f"Mode: {run.mode.value} | Duration: {duration_str} | "
                    f"Symbols: {run.symbols_succeeded}/{run.symbols_total}"
                ),
                level="success",
            )
        elif run.status == PipelineStatus.HALTED:
            self._notifier.notify(
                title="Pipeline Halted",
                message=f"Reason: {run.halt_reason} | Duration: {duration_str}",
                level="warning",
            )
        elif run.status == PipelineStatus.FAILED:
            self._notifier.notify(
                title="Pipeline Failed",
                message=f"Error: {run.error_message} | Duration: {duration_str}",
                level="error",
            )


class PipelineStatusHandler:
    """Application handler for querying pipeline run history."""

    def __init__(self, pipeline_run_repo: IPipelineRunRepository) -> None:
        self._repo = pipeline_run_repo

    def handle(self, query: GetPipelineStatusQuery) -> list[PipelineRun]:
        """Return recent pipeline runs."""
        return self._repo.get_recent(query.limit)
