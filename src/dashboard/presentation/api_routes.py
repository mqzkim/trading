"""Dashboard JSON REST API routes.

Provides JSON API endpoints for the React dashboard frontend via the BFF proxy.

All GET endpoints call QueryHandlers and return dicts directly.
All POST endpoints accept JSON bodies (Pydantic BaseModel).
The SSE endpoint sends raw JSON payloads for real-time updates.
"""
from __future__ import annotations

import json
import threading
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from src.dashboard.application.queries import (
    OverviewQueryHandler,
    PipelineQueryHandler,
    RiskQueryHandler,
    SignalsQueryHandler,
)

api_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard-json"])


# -- Pydantic request models --


class PipelineRunRequest(BaseModel):
    symbols: list[str] = []
    dry_run: bool = False


class ApprovalCreateRequest(BaseModel):
    score_threshold: float = 70.0
    allowed_regimes: list[str] = ["Bull", "Accumulation"]
    max_per_trade_pct: float = 8.0
    daily_budget_cap: float = 10000.0
    expires_in_days: int = 30


class ApprovalActionRequest(BaseModel):
    approval_id: str | None = None


class ReviewActionRequest(BaseModel):
    review_id: int


# -- GET endpoints --


@api_router.get("/overview")
def api_overview(request: Request) -> dict[str, Any]:
    """Return overview data as JSON (KPIs, positions, equity curve, regime periods)."""
    ctx = request.app.state.ctx
    handler = OverviewQueryHandler(ctx)
    return handler.handle()


@api_router.get("/signals")
def api_signals(
    request: Request, sort: str = "composite", desc: bool = True
) -> dict[str, Any]:
    """Return signals and scores as JSON."""
    ctx = request.app.state.ctx
    handler = SignalsQueryHandler(ctx)
    return handler.handle(sort_by=sort, sort_desc=desc)


@api_router.get("/risk")
def api_risk(request: Request) -> dict[str, Any]:
    """Return risk metrics as JSON."""
    ctx = request.app.state.ctx
    handler = RiskQueryHandler(ctx)
    return handler.handle()


@api_router.get("/pipeline")
def api_pipeline(request: Request) -> dict[str, Any]:
    """Return pipeline runs, approval status, budget, and review queue as JSON."""
    ctx = request.app.state.ctx
    handler = PipelineQueryHandler(ctx)
    return handler.handle()


# -- POST endpoints --


@api_router.post("/pipeline/run")
def api_pipeline_run(request: Request, body: PipelineRunRequest) -> dict[str, Any]:
    """Trigger a pipeline run. Runs in a background thread."""
    from src.pipeline.application.commands import RunPipelineCommand
    from src.pipeline.domain.value_objects import RunMode

    ctx = request.app.state.ctx
    handler = ctx["run_pipeline_handler"]

    symbol_list = [s.strip().upper() for s in body.symbols if s.strip()]
    is_dry_run = body.dry_run

    def _run_pipeline() -> None:
        if symbol_list:
            handler._symbols = symbol_list
        else:
            handler._symbols = None
        cmd = RunPipelineCommand(dry_run=is_dry_run, mode=RunMode.MANUAL)
        handler.handle(cmd)

    thread = threading.Thread(target=_run_pipeline, daemon=True)
    thread.start()

    return {
        "status": "running",
        "symbols": symbol_list if symbol_list else [],
        "dry_run": is_dry_run,
    }


@api_router.post("/approval/create")
def api_approval_create(
    request: Request, body: ApprovalCreateRequest
) -> dict[str, Any]:
    """Create a new strategy approval."""
    from src.approval.application.commands import CreateApprovalCommand

    ctx = request.app.state.ctx
    handler = ctx["approval_handler"]
    cmd = CreateApprovalCommand(
        score_threshold=body.score_threshold,
        allowed_regimes=body.allowed_regimes,
        max_per_trade_pct=body.max_per_trade_pct,
        daily_budget_cap=body.daily_budget_cap,
        expires_in_days=body.expires_in_days,
    )
    handler.create(cmd)

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return {"approval_status": data["approval_status"], "daily_budget": data["daily_budget"]}


@api_router.post("/approval/suspend")
def api_approval_suspend(
    request: Request, body: ApprovalActionRequest
) -> dict[str, Any]:
    """Suspend (revoke) the active approval."""
    from src.approval.application.commands import RevokeApprovalCommand

    ctx = request.app.state.ctx
    handler = ctx["approval_handler"]
    handler.revoke(RevokeApprovalCommand(approval_id=body.approval_id))

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return {"approval_status": data["approval_status"], "daily_budget": data["daily_budget"]}


@api_router.post("/approval/resume")
def api_approval_resume(
    request: Request, body: ApprovalActionRequest
) -> dict[str, Any]:
    """Resume a suspended approval."""
    from src.approval.application.commands import ResumeApprovalCommand

    ctx = request.app.state.ctx
    handler = ctx["approval_handler"]
    handler.resume(ResumeApprovalCommand(approval_id=body.approval_id))

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return {"approval_status": data["approval_status"], "daily_budget": data["daily_budget"]}


@api_router.post("/review/approve")
def api_review_approve(request: Request, body: ReviewActionRequest) -> dict[str, Any]:
    """Approve a queued trade."""
    ctx = request.app.state.ctx
    repo = ctx["review_queue_repo"]
    repo.mark_reviewed(body.review_id, approved=True)

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return {"review_queue": data["review_queue"]}


@api_router.post("/review/reject")
def api_review_reject(request: Request, body: ReviewActionRequest) -> dict[str, Any]:
    """Reject a queued trade."""
    ctx = request.app.state.ctx
    repo = ctx["review_queue_repo"]
    repo.mark_reviewed(body.review_id, approved=False)

    pq = PipelineQueryHandler(ctx)
    data = pq.handle()
    return {"review_queue": data["review_queue"]}


# -- SSE endpoint --


@api_router.get("/events")
async def api_sse_events(request: Request):
    """SSE endpoint streaming domain events as raw JSON payloads."""
    bridge = request.app.state.sse_bridge

    async def event_generator():
        async for data in bridge.stream():
            if await request.is_disconnected():
                break
            event_type = data.get("type", "message")
            payload = data.get("payload", {})
            yield ServerSentEvent(
                data=json.dumps(payload),
                event=event_type,
            )

    return EventSourceResponse(event_generator())
