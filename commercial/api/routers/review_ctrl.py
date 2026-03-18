"""Trade review queue router -- list pending, approve, reject.

GET /api/v1/review/queue -- pending review items.
POST /api/v1/review/{review_id}/approve -- approve a queued trade.
POST /api/v1/review/{review_id}/reject -- reject a queued trade.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from commercial.api.dependencies import get_review_queue_repo, verify_dashboard_secret

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("/queue")
def get_review_queue(
    repo=Depends(get_review_queue_repo),
    _: None = Depends(verify_dashboard_secret),
):
    """Return pending trade review items."""
    items = repo.list_pending()
    return {
        "items": [
            {
                "id": item.id,
                "symbol": item.symbol,
                "plan_json": item.plan_json,
                "rejection_reason": item.rejection_reason,
                "pipeline_run_id": item.pipeline_run_id,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ],
    }


@router.post("/{review_id}/approve")
def approve_review(
    review_id: int,
    repo=Depends(get_review_queue_repo),
    _: None = Depends(verify_dashboard_secret),
):
    """Approve a queued trade review item."""
    try:
        repo.mark_reviewed(review_id, approved=True)
        return {"status": "approved", "review_id": review_id}
    except Exception as e:
        logger.error("Failed to approve review %d: %s", review_id, e)
        raise HTTPException(status_code=404, detail=f"Review item {review_id} not found")


@router.post("/{review_id}/reject")
def reject_review(
    review_id: int,
    repo=Depends(get_review_queue_repo),
    _: None = Depends(verify_dashboard_secret),
):
    """Reject a queued trade review item."""
    try:
        repo.mark_reviewed(review_id, approved=False)
        return {"status": "rejected", "review_id": review_id}
    except Exception as e:
        logger.error("Failed to reject review %d: %s", review_id, e)
        raise HTTPException(status_code=404, detail=f"Review item {review_id} not found")
