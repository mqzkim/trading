"""Execution Infrastructure -- Kill Switch Service.

Provides emergency stop capability: cancel all orders, optionally liquidate
all positions, and trigger cooldown to prevent emotional re-entry.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from src.execution.domain.repositories import ICooldownRepository
from src.execution.domain.value_objects import CooldownState

logger = logging.getLogger(__name__)

COOLDOWN_DAYS = 30
KILL_SWITCH_TIER = 20


class KillSwitchService:
    """Kill switch service -- cancels orders and triggers cooldown.

    Works with any broker adapter. If the adapter has a _client attribute
    (real broker), uses it for cancel/liquidate. Otherwise (mock mode),
    logs warnings and still creates cooldown.
    """

    def __init__(
        self,
        broker_adapter: object,
        cooldown_repo: ICooldownRepository,
    ) -> None:
        self._adapter = broker_adapter
        self._cooldown_repo = cooldown_repo

    def execute(self, liquidate: bool = False) -> dict:
        """Execute kill switch.

        Args:
            liquidate: If True, also close all positions after canceling orders.

        Returns:
            Dict with orders_canceled and positions_closed counts.
        """
        orders_canceled = 0
        positions_closed = 0

        client = getattr(self._adapter, "_client", None)

        if client is not None:
            # Cancel all open orders
            try:
                canceled = client.cancel_orders()
                orders_canceled = len(canceled) if canceled else 0
                logger.info("Kill switch: canceled %d orders", orders_canceled)
            except Exception:
                logger.exception("Kill switch: failed to cancel orders")

            # Liquidate all positions if requested
            if liquidate:
                try:
                    closed = client.close_all_positions(cancel_orders=True)
                    positions_closed = len(closed) if closed else 0
                    logger.info("Kill switch: closed %d positions", positions_closed)
                except Exception:
                    logger.exception("Kill switch: failed to close positions")
        else:
            logger.warning(
                "Kill switch: no broker client available (mock mode) "
                "-- no orders to cancel, no positions to close"
            )

        # Always trigger cooldown -- even in mock mode
        now = datetime.now(timezone.utc)
        cooldown = CooldownState(
            triggered_at=now,
            expires_at=now + timedelta(days=COOLDOWN_DAYS),
            current_tier=KILL_SWITCH_TIER,
            re_entry_pct=0,
            reason="kill_switch",
        )
        self._cooldown_repo.save(cooldown)
        logger.info(
            "Kill switch: cooldown activated until %s",
            cooldown.expires_at.isoformat(),
        )

        return {
            "orders_canceled": orders_canceled,
            "positions_closed": positions_closed,
            "cooldown_until": cooldown.expires_at.isoformat(),
        }
