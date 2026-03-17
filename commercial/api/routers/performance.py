"""Performance router -- attribution, proposals.

GET /api/v1/performance/attribution -- Brinson-Fachler 4-level attribution + KPIs.
PUT /api/v1/performance/proposals/{id}/approve -- Approve a parameter proposal.
PUT /api/v1/performance/proposals/{id}/reject -- Reject a parameter proposal.
GET /api/v1/performance/proposals/pending -- List pending proposals.
GET /api/v1/performance/proposals/history -- List decided proposals.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from commercial.api.dependencies import get_attribution_handler, get_current_user
from commercial.api.middleware.rate_limit import get_tier_limit, limiter
from commercial.api.schemas.common import DISCLAIMER
from commercial.api.schemas.performance import (
    AttributionResponse,
    BrinsonRow,
    KPIs,
    ProposalActionResponse,
    ProposalResponse,
    SignalICPerAxis,
)
from src.performance.application.commands import ApproveProposalCommand, RejectProposalCommand
from src.performance.application.queries import ComputeAttributionQuery

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("/attribution", response_model=AttributionResponse)
@limiter.limit(get_tier_limit)
def get_attribution(
    request: Request,
    user: dict = Depends(get_current_user),
    handler=Depends(get_attribution_handler),
):
    """Brinson-Fachler 4-level attribution with KPIs."""
    report = handler.handle(ComputeAttributionQuery())

    brinson_table = [
        BrinsonRow(
            name=level.name,
            allocation_effect=level.allocation_effect,
            selection_effect=level.selection_effect,
            interaction_effect=level.interaction_effect,
            total_effect=level.total_effect,
        )
        for level in report.attribution
    ]

    # Average non-null axis ICs for composite signal_ic
    ic_values = [
        v
        for v in [
            report.signal_ic_fundamental,
            report.signal_ic_technical,
            report.signal_ic_sentiment,
        ]
        if v is not None
    ]
    signal_ic = round(sum(ic_values) / len(ic_values), 4) if ic_values else None

    return AttributionResponse(
        kpis=KPIs(
            sharpe=report.sharpe,
            sortino=report.sortino,
            win_rate=report.win_rate,
            max_drawdown=report.max_drawdown,
        ),
        brinson_table=brinson_table,
        equity_curve=None,
        signal_ic=signal_ic,
        signal_ic_per_axis=SignalICPerAxis(
            fundamental=report.signal_ic_fundamental,
            technical=report.signal_ic_technical,
            sentiment=report.signal_ic_sentiment,
        ),
        kelly_efficiency=report.kelly_efficiency,
        trade_count=report.trade_count,
        disclaimer=DISCLAIMER,
    )


@router.put(
    "/proposals/{proposal_id}/approve",
    response_model=ProposalActionResponse,
)
@limiter.limit(get_tier_limit)
def approve_proposal(
    request: Request,
    proposal_id: str,
    user: dict = Depends(get_current_user),
    handler=Depends(get_attribution_handler),
):
    """Approve a parameter adjustment proposal."""
    result = handler.handle_approve(ApproveProposalCommand(proposal_id=proposal_id))
    return ProposalActionResponse(**result)


@router.put(
    "/proposals/{proposal_id}/reject",
    response_model=ProposalActionResponse,
)
@limiter.limit(get_tier_limit)
def reject_proposal(
    request: Request,
    proposal_id: str,
    user: dict = Depends(get_current_user),
    handler=Depends(get_attribution_handler),
):
    """Reject a parameter adjustment proposal."""
    result = handler.handle_reject(RejectProposalCommand(proposal_id=proposal_id))
    return ProposalActionResponse(**result)


@router.get("/proposals/pending", response_model=list[ProposalResponse])
@limiter.limit(get_tier_limit)
def get_pending_proposals(
    request: Request,
    user: dict = Depends(get_current_user),
    handler=Depends(get_attribution_handler),
):
    """List pending parameter proposals."""
    if handler._proposal_repo is None:
        return []
    return handler._proposal_repo.find_pending()


@router.get("/proposals/history", response_model=list[ProposalResponse])
@limiter.limit(get_tier_limit)
def get_proposal_history(
    request: Request,
    user: dict = Depends(get_current_user),
    handler=Depends(get_attribution_handler),
):
    """List last 5 decided proposals."""
    if handler._proposal_repo is None:
        return []
    return handler._proposal_repo.list_history(limit=5)
