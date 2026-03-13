"""Dashboard FastAPI app factory.

Creates a FastAPI application with bootstrap context, SSE bridge,
and dashboard routes mounted at /dashboard/.
"""
from __future__ import annotations

from fastapi import FastAPI

from src.dashboard.infrastructure.sse_bridge import SSEBridge
from src.dashboard.presentation.routes import router


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

    app = FastAPI(title="Trading Dashboard")
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
