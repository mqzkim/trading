"""Approval Application -- Handlers.

ApprovalHandler: CRUD, regime/drawdown suspension.
No direct infrastructure imports -- depends on repository interfaces.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from src.approval.domain.entities import StrategyApproval
from src.approval.domain.repositories import (
    IApprovalRepository,
    IBudgetRepository,
    IReviewQueueRepository,
)
from .commands import (
    CreateApprovalCommand,
    RevokeApprovalCommand,
    ResumeApprovalCommand,
)

logger = logging.getLogger(__name__)


class ApprovalHandler:
    """Application handler for approval lifecycle management.

    Manages: create, get_status, revoke, resume, regime/drawdown suspension.
    """

    def __init__(
        self,
        approval_repo: IApprovalRepository,
        budget_repo: IBudgetRepository,
        review_queue_repo: IReviewQueueRepository,
    ) -> None:
        self._approval_repo = approval_repo
        self._budget_repo = budget_repo
        self._review_queue_repo = review_queue_repo

    def create(self, cmd: CreateApprovalCommand) -> StrategyApproval:
        """Create a new strategy approval, deactivating any previous one."""
        approval = StrategyApproval(
            _id=str(uuid.uuid4()),
            score_threshold=cmd.score_threshold,
            allowed_regimes=list(cmd.allowed_regimes),
            max_per_trade_pct=cmd.max_per_trade_pct,
            daily_budget_cap=cmd.daily_budget_cap,
            expires_at=datetime.now(timezone.utc) + timedelta(days=cmd.expires_in_days),
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )
        self._approval_repo.save(approval)
        logger.info("Created approval %s (expires %s)", approval.id, approval.expires_at)
        return approval

    def get_status(self) -> dict[str, Any]:
        """Return current approval status, budget, and pending review count."""
        approval = self._approval_repo.get_active()
        budget = None
        if approval is not None:
            budget = self._budget_repo.get_or_create_today(approval.daily_budget_cap)
        pending_count = len(self._review_queue_repo.list_pending())
        return {
            "approval": approval,
            "budget": budget,
            "pending_review_count": pending_count,
        }

    def revoke(self, cmd: RevokeApprovalCommand) -> None:
        """Revoke an approval by ID, or the currently active one."""
        if cmd.approval_id:
            approval = self._approval_repo.find_by_id(cmd.approval_id)
        else:
            approval = self._approval_repo.get_active()

        if approval is None:
            logger.warning("No approval found to revoke")
            return

        approval.revoke()
        self._approval_repo.save(approval)
        logger.info("Revoked approval %s", approval.id)

    def resume(self, cmd: ResumeApprovalCommand) -> None:
        """Remove drawdown_tier2 suspension from active approval."""
        if cmd.approval_id:
            approval = self._approval_repo.find_by_id(cmd.approval_id)
        else:
            approval = self._approval_repo.get_active()

        if approval is None:
            logger.warning("No approval found to resume")
            return

        approval.unsuspend("drawdown_tier2")
        self._approval_repo.save(approval)
        logger.info("Resumed approval %s (remaining reasons: %s)", approval.id, approval.suspended_reasons)

    def suspend_if_regime_invalid(self, new_regime: str) -> None:
        """Check if new regime is in allowed_regimes; suspend/unsuspend accordingly.

        Called by RegimeChangedEvent subscription. Accepts regime as string
        (RegimeType.value or raw string).
        """
        approval = self._approval_repo.get_active()
        if approval is None:
            return

        # Normalize: RegimeType enum has .value like "Bull", but event may pass enum
        regime_str = new_regime.value if hasattr(new_regime, "value") else str(new_regime)

        if regime_str not in approval.allowed_regimes:
            approval.suspend("regime_change")
            self._approval_repo.save(approval)
            logger.info("Suspended approval %s: regime %s not allowed", approval.id, regime_str)
        elif "regime_change" in approval.suspended_reasons:
            approval.unsuspend("regime_change")
            self._approval_repo.save(approval)
            logger.info("Unsuspended approval %s: regime %s returned to allowed list", approval.id, regime_str)

    def suspend_for_drawdown(self) -> None:
        """Suspend active approval due to drawdown tier 2+."""
        approval = self._approval_repo.get_active()
        if approval is None:
            logger.warning("No active approval to suspend for drawdown")
            return

        approval.suspend("drawdown_tier2")
        self._approval_repo.save(approval)
        logger.info("Suspended approval %s for drawdown_tier2", approval.id)
