"""Dashboard routes -- page routes and SSE endpoint."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from src.dashboard.application.queries import (
    OverviewQueryHandler,
    PipelineQueryHandler,
    RiskQueryHandler,
    SignalsQueryHandler,
)
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
def signals_page(request: Request, sort: str = "composite", desc: str = "1"):
    """Signals page with scoring heatmap and recommendations."""
    ctx = request.app.state.ctx
    handler = SignalsQueryHandler(ctx)
    data = handler.handle(sort_by=sort, sort_desc=(desc == "1"))

    return templates.TemplateResponse(
        request,
        "signals.html",
        {
            "execution_mode": _get_mode(request),
            "active_page": "signals",
            "scores": data["scores"],
            "signals": data["signals"],
            "sort_by": sort,
            "sort_desc": desc == "1",
        },
    )


@router.get("/risk")
def risk_page(request: Request):
    """Risk page with drawdown gauge, sector exposure, position limits."""
    ctx = request.app.state.ctx
    handler = RiskQueryHandler(ctx)
    data = handler.handle()

    return templates.TemplateResponse(
        request,
        "risk.html",
        {
            "execution_mode": _get_mode(request),
            "active_page": "risk",
            **data,
        },
    )


@router.get("/pipeline")
def pipeline_page(request: Request):
    """Pipeline & Approval page with run history, approval CRUD, budget."""
    ctx = request.app.state.ctx
    handler = PipelineQueryHandler(ctx)
    data = handler.handle()

    return templates.TemplateResponse(
        request,
        "pipeline.html",
        {
            "execution_mode": _get_mode(request),
            "active_page": "pipeline",
            # Run Pipeline section initial state
            "run_status": None,
            "symbols": "",
            "dry_run": False,
            **data,
        },
    )


@router.post("/pipeline/run", response_class=HTMLResponse)
def pipeline_run(
    request: Request,
    symbols: str = Form(""),
    dry_run: str = Form(""),
):
    """Trigger a pipeline run via HTMX POST.

    Runs the pipeline in a background thread so the web server stays responsive.
    Returns an immediate "running" state; the SSE bridge will push the final result
    when PipelineCompletedEvent/PipelineHaltedEvent fires.
    """
    import threading

    from src.pipeline.application.commands import RunPipelineCommand
    from src.pipeline.domain.value_objects import RunMode

    ctx = request.app.state.ctx
    handler = ctx["run_pipeline_handler"]

    # Parse symbols
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    is_dry_run = dry_run == "1"
    symbols_display = ", ".join(symbol_list) if symbol_list else "default universe"
    mode_display = "dry_run" if is_dry_run else "manual"

    def _run_pipeline() -> None:
        """Execute the pipeline in a background thread."""
        if symbol_list:
            handler._symbols = symbol_list
        else:
            handler._symbols = None
        cmd = RunPipelineCommand(dry_run=is_dry_run, mode=RunMode.MANUAL)
        handler.handle(cmd)

    thread = threading.Thread(target=_run_pipeline, daemon=True)
    thread.start()

    return templates.TemplateResponse(
        request,
        "partials/pipeline_run_result.html",
        {
            "run_status": "running",
            "symbols": symbols_display,
            "mode": mode_display,
            "dry_run": is_dry_run,
        },
    )


@router.post("/approval/create", response_class=HTMLResponse)
def approval_create(
    request: Request,
    score_threshold: float = Form(70.0),
    allowed_regimes: str = Form("Bull,Accumulation"),
    max_per_trade_pct: float = Form(8.0),
    daily_budget_cap: float = Form(10000.0),
    expires_in_days: int = Form(30),
):
    """Create a new strategy approval via HTMX POST."""
    from src.approval.application.commands import CreateApprovalCommand

    ctx = request.app.state.ctx
    handler = ctx["approval_handler"]
    regimes_list = [r.strip() for r in allowed_regimes.split(",") if r.strip()]
    cmd = CreateApprovalCommand(
        score_threshold=score_threshold,
        allowed_regimes=regimes_list,
        max_per_trade_pct=max_per_trade_pct,
        daily_budget_cap=daily_budget_cap,
        expires_in_days=expires_in_days,
    )
    handler.create(cmd)

    # Re-render approval section
    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return templates.TemplateResponse(
        request,
        "partials/approval_section.html",
        {"approval_status": data["approval_status"], "daily_budget": data["daily_budget"]},
    )


@router.post("/approval/suspend", response_class=HTMLResponse)
def approval_suspend(
    request: Request,
    approval_id: str = Form(""),
):
    """Suspend (revoke) the active approval via HTMX POST."""
    from src.approval.application.commands import RevokeApprovalCommand

    ctx = request.app.state.ctx
    handler = ctx["approval_handler"]
    handler.revoke(RevokeApprovalCommand(approval_id=approval_id or None))

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return templates.TemplateResponse(
        request,
        "partials/approval_section.html",
        {"approval_status": data["approval_status"], "daily_budget": data["daily_budget"]},
    )


@router.post("/approval/resume", response_class=HTMLResponse)
def approval_resume(
    request: Request,
    approval_id: str = Form(""),
):
    """Resume a suspended approval via HTMX POST."""
    from src.approval.application.commands import ResumeApprovalCommand

    ctx = request.app.state.ctx
    handler = ctx["approval_handler"]
    handler.resume(ResumeApprovalCommand(approval_id=approval_id or None))

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return templates.TemplateResponse(
        request,
        "partials/approval_section.html",
        {"approval_status": data["approval_status"], "daily_budget": data["daily_budget"]},
    )


@router.post("/review/approve", response_class=HTMLResponse)
def review_approve(
    request: Request,
    review_id: int = Form(...),
):
    """Approve a queued trade via HTMX POST."""
    ctx = request.app.state.ctx
    repo = ctx["review_queue_repo"]
    repo.mark_reviewed(review_id, approved=True)

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return templates.TemplateResponse(
        request,
        "partials/review_queue_section.html",
        {"review_queue": data["review_queue"]},
    )


@router.post("/review/reject", response_class=HTMLResponse)
def review_reject(
    request: Request,
    review_id: int = Form(...),
):
    """Reject a queued trade via HTMX POST."""
    ctx = request.app.state.ctx
    repo = ctx["review_queue_repo"]
    repo.mark_reviewed(review_id, approved=False)

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return templates.TemplateResponse(
        request,
        "partials/review_queue_section.html",
        {"review_queue": data["review_queue"]},
    )


def _render_partial(event_type: str, payload: dict, request: Request) -> str:
    """Render an HTML partial for an SSE event type."""
    ctx = request.app.state.ctx
    if event_type in ("PipelineCompletedEvent", "PipelineHaltedEvent"):
        pq = PipelineQueryHandler(ctx)
        data = pq.handle()
        return templates.get_template("partials/pipeline_status.html").render(
            pipeline_runs=data["pipeline_runs"],
            next_scheduled=data["next_scheduled"],
        )
    if event_type == "OrderFilledEvent":
        handler = OverviewQueryHandler(ctx)
        data = handler.handle()
        return templates.get_template("partials/holdings_table.html").render(
            positions=data["positions"],
        )
    if event_type == "DrawdownAlertEvent":
        from src.dashboard.presentation.charts import build_drawdown_gauge

        pct = float(payload.get("drawdown_pct", "0"))
        gauge_json = build_drawdown_gauge(pct)
        return templates.get_template("partials/drawdown_gauge.html").render(
            drawdown_pct=pct,
            gauge_json=gauge_json,
        )
    if event_type == "RegimeChangedEvent":
        regime = payload.get("new_regime", "Unknown")
        return templates.get_template("partials/regime_badge.html").render(
            regime=regime,
        )
    return ""


@router.get("/events")
async def sse_events(request: Request):
    """SSE endpoint streaming domain events to dashboard."""
    bridge = request.app.state.sse_bridge

    async def event_generator():
        async for data in bridge.stream():
            if await request.is_disconnected():
                break
            event_type = data.get("type", "message")
            payload = data.get("payload", {})
            html = _render_partial(event_type, payload, request)
            yield ServerSentEvent(
                data=html if html else json.dumps(data),
                event=event_type,
            )

    return EventSourceResponse(event_generator())
