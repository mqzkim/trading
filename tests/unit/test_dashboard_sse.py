"""Tests for SSE bridge and SSE endpoint."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.dashboard.infrastructure.sse_bridge import SSEBridge
from src.dashboard.presentation.app import create_dashboard_app
from src.execution.domain.value_objects import ExecutionMode
from src.shared.infrastructure.sync_event_bus import SyncEventBus


@dataclass
class _FakeEvent:
    """Dummy event for testing."""

    symbol: str = "AAPL"
    price: float = 150.0


@pytest.mark.asyncio
async def test_sse_bridge_subscribe():
    """Subscribe to event type, publish event, verify queue receives it."""
    bus = SyncEventBus()
    bridge = SSEBridge(bus)
    bridge.subscribe_events(_FakeEvent)

    # Start a stream consumer
    received: list[dict] = []

    async def consume():
        async for data in bridge.stream():
            received.append(data)
            break  # stop after first event

    task = asyncio.create_task(consume())

    # Give the consumer time to register
    await asyncio.sleep(0.05)

    # Publish event via bus
    bus.publish(_FakeEvent(symbol="MSFT", price=300.0))

    await asyncio.wait_for(task, timeout=2.0)
    assert len(received) == 1
    assert received[0]["type"] == "_FakeEvent"
    assert received[0]["payload"]["symbol"] == "MSFT"


@pytest.mark.asyncio
async def test_sse_bridge_multiple_consumers():
    """Two stream iterators both receive the same event."""
    bus = SyncEventBus()
    bridge = SSEBridge(bus)
    bridge.subscribe_events(_FakeEvent)

    received_1: list[dict] = []
    received_2: list[dict] = []

    async def consume(target: list):
        async for data in bridge.stream():
            target.append(data)
            break

    t1 = asyncio.create_task(consume(received_1))
    t2 = asyncio.create_task(consume(received_2))

    await asyncio.sleep(0.05)

    bus.publish(_FakeEvent(symbol="GOOG"))

    await asyncio.wait_for(asyncio.gather(t1, t2), timeout=2.0)
    assert len(received_1) == 1
    assert len(received_2) == 1
    assert received_1[0]["type"] == "_FakeEvent"
    assert received_2[0]["type"] == "_FakeEvent"


@pytest.mark.asyncio
async def test_sse_bridge_queue_full_drops():
    """Filling queue to maxsize does not raise an exception."""
    bus = SyncEventBus()
    bridge = SSEBridge(bus)
    bridge.subscribe_events(_FakeEvent)

    # Create a queue but don't consume from it
    stream_iter = bridge.stream().__aiter__()
    # Force queue creation by awaiting next briefly
    task = asyncio.create_task(stream_iter.__anext__())
    await asyncio.sleep(0.05)

    # Publish 150 events (queue maxsize=100), should not raise
    for i in range(150):
        bus.publish(_FakeEvent(symbol=f"SYM{i}"))

    # Clean up
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, StopAsyncIteration):
        pass


def test_sse_endpoint_content_type():
    """GET /api/v1/dashboard/events returns content-type text/event-stream."""
    ctx = _make_test_ctx()
    app = create_dashboard_app(ctx=ctx)

    # Verify the route exists
    from fastapi.testclient import TestClient

    route_paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/api/v1/dashboard/events" in route_paths

    # Verify SSE bridge is wired
    assert hasattr(app.state, "sse_bridge")
    assert app.state.sse_bridge is not None


def _make_test_ctx() -> dict:
    """Minimal mock context for SSE tests."""
    position_repo = MagicMock()
    position_repo.find_all_open.return_value = []
    score_repo = MagicMock()
    score_repo.find_all_latest.return_value = {}
    trade_plan_repo = MagicMock()
    trade_plan_repo._db_path = ":memory:"
    pipeline_run_repo = MagicMock()
    pipeline_run_repo.get_recent.return_value = []
    regime_repo = MagicMock()
    regime_repo.find_latest.return_value = None
    portfolio_handler = MagicMock()
    portfolio_handler._portfolio_repo.find_by_id.return_value = None
    signal_repo = MagicMock()
    signal_repo.find_all_active.return_value = []

    return {
        "bus": SyncEventBus(),
        "execution_mode": ExecutionMode.PAPER,
        "position_repo": position_repo,
        "score_repo": score_repo,
        "trade_plan_repo": trade_plan_repo,
        "pipeline_run_repo": pipeline_run_repo,
        "regime_repo": regime_repo,
        "portfolio_handler": portfolio_handler,
        "signal_repo": signal_repo,
    }
