"""Dashboard routes -- page routes and SSE endpoint."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from src.dashboard.application.queries import OverviewQueryHandler
from src.dashboard.presentation.charts import build_equity_curve

router = APIRouter(prefix="/dashboard")

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def _get_mode(request: Request) -> str:
    """Get execution_mode string from app context."""
    ctx = request.app.state.ctx
    mode = ctx.get("execution_mode")
    if mode is None:
        return "paper"
    return mode.value if hasattr(mode, "value") else str(mode)


@router.get("/")
def overview_page(request: Request):
    """Overview page with KPI cards, holdings, equity curve."""
    ctx = request.app.state.ctx
    handler = OverviewQueryHandler(ctx)
    data = handler.handle()

    # Build equity curve chart JSON
    equity = data["equity_curve"]
    chart_json = build_equity_curve(
        values=equity["values"],
        dates=equity["dates"],
        regime_periods=data["regime_periods"],
    )

    return templates.TemplateResponse(
        request,
        "overview.html",
        {
            "execution_mode": _get_mode(request),
            "active_page": "overview",
            "total_value": data["total_value"],
            "today_pnl": data["today_pnl"],
            "drawdown_pct": data["drawdown_pct"],
            "last_pipeline": data["last_pipeline"],
            "positions": data["positions"],
            "trade_history": data["trade_history"],
            "chart_json": chart_json,
        },
    )


@router.get("/signals")
def signals_page(request: Request):
    """Signals page with scoring heatmap and recommendations."""
    return templates.TemplateResponse(
        request,
        "signals.html",
        {"execution_mode": _get_mode(request), "active_page": "signals"},
    )


@router.get("/risk")
def risk_page(request: Request):
    """Risk page with drawdown gauge, sector exposure, position limits."""
    return templates.TemplateResponse(
        request,
        "risk.html",
        {"execution_mode": _get_mode(request), "active_page": "risk"},
    )


@router.get("/pipeline")
def pipeline_page(request: Request):
    """Pipeline & Approval page with run history, approval CRUD, budget."""
    return templates.TemplateResponse(
        request,
        "pipeline.html",
        {"execution_mode": _get_mode(request), "active_page": "pipeline"},
    )


@router.get("/events")
async def sse_events(request: Request):
    """SSE endpoint streaming domain events to dashboard."""
    bridge = request.app.state.sse_bridge

    async def event_generator():
        async for data in bridge.stream():
            if await request.is_disconnected():
                break
            yield ServerSentEvent(
                data=json.dumps(data),
                event=data.get("type", "message"),
            )

    return EventSourceResponse(event_generator())
