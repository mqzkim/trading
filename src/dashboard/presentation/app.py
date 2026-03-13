"""Dashboard FastAPI app factory.

Creates a FastAPI application with bootstrap context, SSE bridge,
and dashboard routes mounted at /dashboard/.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.dashboard.infrastructure.sse_bridge import SSEBridge
from src.dashboard.presentation.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage order monitor and trading stream lifecycle."""
    ctx = app.state.ctx
    monitor = ctx.get("order_monitor")
    stream = ctx.get("trading_stream")

    if monitor is not None:
        monitor.start()
        logger.info("Order monitor started")
    if stream is not None:
        stream.start()
        logger.info("Trading stream started")

    yield

    if monitor is not None:
        try:
            monitor.stop(timeout=10.0)
            logger.info("Order monitor stopped")
        except Exception:
            logger.exception("Error stopping order monitor")
    if stream is not None:
        try:
            stream.stop()
            logger.info("Trading stream stopped")
        except Exception:
            logger.exception("Error stopping trading stream")


def create_dashboard_app(ctx: dict | None = None) -> FastAPI:
    """Create the dashboard FastAPI application.

    Args:
        ctx: Bootstrap context dict. If None, calls bootstrap() to create one.

    Returns:
        Configured FastAPI app with dashboard routes.
    """
    if ctx is None:
        from src.bootstrap import bootstrap

        ctx = bootstrap()

    app = FastAPI(title="Trading Dashboard", lifespan=lifespan)
    app.state.ctx = ctx

    # SSE bridge: subscribe to domain events
    from src.execution.domain.events import OrderFilledEvent
    from src.pipeline.domain.events import PipelineCompletedEvent, PipelineHaltedEvent
    from src.portfolio.domain.events import DrawdownAlertEvent
    from src.regime.domain.events import RegimeChangedEvent

    bridge = SSEBridge(ctx["bus"])
    bridge.subscribe_events(
        OrderFilledEvent,
        PipelineCompletedEvent,
        PipelineHaltedEvent,
        DrawdownAlertEvent,
        RegimeChangedEvent,
    )
    app.state.sse_bridge = bridge

    app.include_router(router)

    return app
