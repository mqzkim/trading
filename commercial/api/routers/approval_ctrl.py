"""Approval control router -- create, status, revoke, resume.

POST /api/v1/approval/create -- create strategy approval.
GET /api/v1/approval/status -- current approval status + budget.
POST /api/v1/approval/revoke -- revoke active approval.
POST /api/v1/approval/resume -- resume suspended approval.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from commercial.api.dependencies import get_approval_handler, verify_dashboard_secret

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approval", tags=["Approval"])


class CreateApprovalRequest(BaseModel):
    """Request body for creating a strategy approval."""

    score_threshold: float = 70.0
    allowed_regimes: list[str] = ["Bull", "Sideways"]
    max_per_trade_pct: float = 8.0
    daily_budget_cap: float = 10000.0
    expires_in_days: int = 7


@router.post("/create")
def create_approval(
    body: CreateApprovalRequest,
    handler=Depends(get_approval_handler),
    _: None = Depends(verify_dashboard_secret),
):
    """Create a new strategy approval."""
    from src.approval.application.commands import CreateApprovalCommand

    cmd = CreateApprovalCommand(
        score_threshold=body.score_threshold,
        allowed_regimes=body.allowed_regimes,
        max_per_trade_pct=body.max_per_trade_pct,
        daily_budget_cap=body.daily_budget_cap,
        expires_in_days=body.expires_in_days,
    )
    approval = handler.create(cmd)
    return {
        "status": "created",
        "approval_id": approval.id,
        "expires_at": approval.expires_at.isoformat(),
    }


@router.get("/status")
def get_approval_status(
    handler=Depends(get_approval_handler),
    _: None = Depends(verify_dashboard_secret),
):
    """Return current approval status, budget, and pending review count."""
    result = handler.get_status()
    approval = result.get("approval")
    budget = result.get("budget")

    approval_data: Optional[dict] = None
    if approval is not None:
        approval_data = {
            "id": approval.id,
            "score_threshold": approval.score_threshold,
            "allowed_regimes": approval.allowed_regimes,
            "max_per_trade_pct": approval.max_per_trade_pct,
            "daily_budget_cap": approval.daily_budget_cap,
            "expires_at": approval.expires_at.isoformat(),
            "is_active": approval.is_active,
            "is_expired": approval.is_expired,
            "is_suspended": approval.is_suspended,
            "is_effective": approval.is_effective,
            "suspended_reasons": list(approval.suspended_reasons),
        }

    budget_data: Optional[dict] = None
    if budget is not None:
        budget_data = {
            "date": budget.date,
            "spent": budget.spent,
            "limit": budget.budget_cap,
            "remaining": budget.remaining,
            "trade_count": budget.trade_count,
        }

    return {
        "approval": approval_data,
        "budget": budget_data,
        "pending_review_count": result.get("pending_review_count", 0),
    }


@router.post("/revoke")
def revoke_approval(
    handler=Depends(get_approval_handler),
    _: None = Depends(verify_dashboard_secret),
):
    """Revoke the currently active approval."""
    from src.approval.application.commands import RevokeApprovalCommand

    handler.revoke(RevokeApprovalCommand())
    return {"status": "revoked"}


@router.post("/resume")
def resume_approval(
    handler=Depends(get_approval_handler),
    _: None = Depends(verify_dashboard_secret),
):
    """Resume a suspended approval (removes drawdown_tier2 suspension)."""
    from src.approval.application.commands import ResumeApprovalCommand

    handler.resume(ResumeApprovalCommand())
    return {"status": "resumed"}
