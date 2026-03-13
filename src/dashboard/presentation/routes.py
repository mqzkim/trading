"""Dashboard routes -- page routes and SSE endpoint."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

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
    return templates.TemplateResponse(
        request,
        "overview.html",
        {"execution_mode": _get_mode(request), "active_page": "overview"},
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
