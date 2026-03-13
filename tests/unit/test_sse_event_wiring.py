"""Tests for SSE event wiring -- verifies templates, handlers, and monitor lifecycle."""
from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.pipeline.application.commands import RunPipelineCommand
from src.pipeline.application.handlers import RunPipelineHandler
from src.pipeline.domain.entities import PipelineRun
from src.pipeline.domain.events import PipelineCompletedEvent, PipelineHaltedEvent
from src.pipeline.domain.value_objects import PipelineStatus, RunMode
from src.portfolio.application.handlers import PortfolioManagerHandler
from src.execution.infrastructure.order_monitor import AlpacaOrderMonitor


# Known event class names that SSEBridge subscribes to
SUBSCRIBED_EVENTS = {
    "OrderFilledEvent",
    "RegimeChangedEvent",
    "DrawdownAlertEvent",
    "PipelineCompletedEvent",
    "PipelineHaltedEvent",
}

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "src" / "dashboard" / "presentation" / "templates"


def test_event_names_match():
    """All sse-swap attributes in templates must match subscribed event class names."""
    sse_swap_pattern = re.compile(r'sse-swap="([^"]+)"')
    mismatches: list[str] = []

    for html_file in TEMPLATES_DIR.rglob("*.html"):
        content = html_file.read_text()
        for match in sse_swap_pattern.finditer(content):
            event_name = match.group(1)
            if event_name not in SUBSCRIBED_EVENTS:
                rel = html_file.relative_to(TEMPLATES_DIR)
                mismatches.append(f"{rel}: sse-swap=\"{event_name}\"")

    assert not mismatches, (
        f"SSE event name mismatches found:\n" + "\n".join(f"  - {m}" for m in mismatches)
    )


def test_pipeline_completed_event_published():
    """RunPipelineHandler publishes PipelineCompletedEvent after successful run."""
    bus = MagicMock()
    now = datetime.now(timezone.utc)
    completed_run = PipelineRun(
        run_id="test-run-1",
        started_at=now - timedelta(seconds=30),
        finished_at=now,
        status=PipelineStatus.COMPLETED,
        mode=RunMode.MANUAL,
    )
    orchestrator = MagicMock()
    orchestrator.run.return_value = completed_run

    handlers_ctx = {"bus": bus}
    handler = RunPipelineHandler(
        orchestrator=orchestrator,
        pipeline_run_repo=MagicMock(),
        notifier=MagicMock(),
        reconciliation_service=MagicMock(),
        handlers=handlers_ctx,
    )

    handler.handle(RunPipelineCommand(dry_run=False, mode=RunMode.MANUAL))

    # Verify bus.publish was called with PipelineCompletedEvent
    assert bus.publish.called
    published_event = bus.publish.call_args[0][0]
    assert isinstance(published_event, PipelineCompletedEvent)
    assert published_event.run_id == "test-run-1"


def test_pipeline_halted_event_published():
    """RunPipelineHandler publishes PipelineHaltedEvent when pipeline halts."""
    bus = MagicMock()
    now = datetime.now(timezone.utc)
    halted_run = PipelineRun(
        run_id="test-run-2",
        started_at=now - timedelta(seconds=10),
        finished_at=now,
        status=PipelineStatus.HALTED,
        mode=RunMode.MANUAL,
        halt_reason="Regime: Crisis",
    )
    orchestrator = MagicMock()
    orchestrator.run.return_value = halted_run

    handlers_ctx = {"bus": bus}
    handler = RunPipelineHandler(
        orchestrator=orchestrator,
        pipeline_run_repo=MagicMock(),
        notifier=MagicMock(),
        reconciliation_service=MagicMock(),
        handlers=handlers_ctx,
    )

    handler.handle(RunPipelineCommand(dry_run=False, mode=RunMode.MANUAL))

    assert bus.publish.called
    published_event = bus.publish.call_args[0][0]
    assert isinstance(published_event, PipelineHaltedEvent)
    assert published_event.run_id == "test-run-2"
    assert published_event.halt_reason == "Regime: Crisis"


def test_drawdown_event_published():
    """PortfolioManagerHandler publishes DrawdownAlertEvent via bus after save."""
    from src.portfolio.domain.events import DrawdownAlertEvent

    bus = MagicMock()
    portfolio_repo = MagicMock()
    position_repo = MagicMock()

    # Create a mock portfolio that returns domain events when pull_domain_events is called
    mock_portfolio = MagicMock()
    alert_event = DrawdownAlertEvent(
        portfolio_id="test-portfolio",
        drawdown=0.12,
        level="caution",
    )
    mock_portfolio.pull_domain_events.return_value = [alert_event]
    mock_portfolio.drawdown_level.value = "normal"
    mock_portfolio.total_value = 100_000.0
    mock_portfolio.can_open_position.return_value = True
    mock_portfolio.positions = {}

    portfolio_repo.find_by_id.return_value = mock_portfolio

    handler = PortfolioManagerHandler(
        portfolio_repo=portfolio_repo,
        position_repo=position_repo,
        bus=bus,
    )

    from src.portfolio.application.commands import OpenPositionCommand

    cmd = OpenPositionCommand(
        portfolio_id="test-portfolio",
        symbol="AAPL",
        entry_price=150.0,
        win_rate=0.55,
        win_loss_ratio=2.0,
    )

    # Mock the risk service to return valid sizing
    handler._risk_svc = MagicMock()
    handler._risk_svc.compute_kelly_size.return_value = {
        "shares": 10,
        "weight": 0.05,
        "kelly": 0.1,
    }

    handler.open_position(cmd)

    # Verify bus.publish was called with the DrawdownAlertEvent
    assert bus.publish.called
    published_event = bus.publish.call_args[0][0]
    assert isinstance(published_event, DrawdownAlertEvent)
    assert published_event.level == "caution"


def test_monitor_persistent_loop():
    """AlpacaOrderMonitor does not exit when tracked orders is empty."""
    monitor = AlpacaOrderMonitor(
        client=MagicMock(),
        poll_interval=0.1,
    )

    monitor.start()
    # Give loop time to run with empty tracked_orders
    time.sleep(0.3)

    # Monitor should still be alive (not exited)
    assert monitor._thread is not None
    assert monitor._thread.is_alive(), "Monitor should stay alive with empty tracked_orders"

    # Clean shutdown
    monitor.stop(timeout=2.0)
    assert not monitor._thread.is_alive(), "Monitor should stop cleanly after stop()"
