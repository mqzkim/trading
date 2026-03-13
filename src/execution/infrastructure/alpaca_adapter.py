"""Execution Infrastructure — Alpaca Execution Adapter.

Mock fallback: credentials 없으면 mock 모드로 작동 (paper mode only).
Live mode: order failures return error OrderResult, never phantom fills.
alpaca-py imports는 메서드 내부에서만 (module-level import 금지).
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import uuid4

from src.execution.domain.repositories import IBrokerAdapter
from src.execution.domain.value_objects import BracketSpec, OrderResult, OrderSpec

logger = logging.getLogger(__name__)


class AlpacaExecutionAdapter(IBrokerAdapter):
    """Alpaca bracket order adapter with mock fallback.

    Credentials 없으면 mock 모드로 동작 (unit test 및 개발 환경).
    Real 모드에서는 alpaca-py SDK를 사용하여 주문 제출.
    paper=True (default) for paper trading, paper=False for live trading.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: bool = True,
    ) -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._use_mock = not (api_key and secret_key)
        self._client: Any = None

        if not self._use_mock:
            self._init_client()

    def _init_client(self) -> None:
        """Lazily initialize Alpaca TradingClient."""
        from alpaca.trading.client import TradingClient

        self._client = TradingClient(
            self._api_key, self._secret_key, paper=self._paper
        )

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        """IBrokerAdapter interface — delegates to submit_bracket_order."""
        return self.submit_bracket_order(spec)

    def submit_bracket_order(self, spec: BracketSpec) -> OrderResult:
        """Submit a bracket order (entry + stop-loss + take-profit).

        Mock mode: returns simulated filled result.
        Real mode: submits via alpaca-py MarketOrderRequest with OrderClass.BRACKET.
        """
        if self._use_mock:
            return self._mock_bracket_order(spec)
        return self._real_bracket_order(spec)

    def get_positions(self) -> list[dict]:
        """Get current open positions."""
        if self._use_mock:
            return []
        return self._real_get_positions()

    def get_account(self) -> dict:
        """Get account summary."""
        if self._use_mock:
            return {
                "cash": 100000.0,
                "portfolio_value": 100000.0,
                "status": "ACTIVE",
            }
        return self._real_get_account()

    # ── Mock implementations ──────────────────────────────────────────

    def _mock_bracket_order(self, spec: BracketSpec) -> OrderResult:
        order_id = f"MOCK-{spec.symbol}-{uuid4().hex[:8]}"
        return OrderResult(
            order_id=order_id,
            status="filled",
            symbol=spec.symbol,
            quantity=spec.quantity,
            filled_price=spec.entry_price,
        )

    # ── Real Alpaca implementations ───────────────────────────────────

    def _real_bracket_order(self, spec: BracketSpec) -> OrderResult:
        try:
            from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
            from alpaca.trading.requests import (
                MarketOrderRequest,
                StopLossRequest,
                TakeProfitRequest,
            )

            if spec.stop_loss_price is None or spec.take_profit_price is None:
                raise ValueError(
                    "Alpaca bracket orders require stop_loss_price and take_profit_price"
                )

            request = MarketOrderRequest(
                symbol=spec.symbol,
                qty=spec.quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=spec.take_profit_price),
                stop_loss=StopLossRequest(stop_price=spec.stop_loss_price),
            )
            order = self._client.submit_order(request)
            return OrderResult(
                order_id=str(order.id),
                status=str(order.status),
                symbol=spec.symbol,
                quantity=spec.quantity,
                filled_price=float(order.filled_avg_price) if order.filled_avg_price else None,
            )
        except Exception as e:
            logger.error("Alpaca bracket order failed for %s: %s", spec.symbol, e)
            return OrderResult(
                order_id="",
                status="error",
                symbol=spec.symbol,
                quantity=spec.quantity,
                filled_price=None,
                error_message=str(e),
            )

    def _real_get_positions(self) -> list[dict]:
        try:
            positions = self._client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": int(p.qty),
                    "market_value": float(p.market_value),
                    "unrealized_pl": float(p.unrealized_pl),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error("Alpaca get_positions failed: %s", e)
            return []

    def _real_get_account(self) -> dict:
        try:
            account = self._client.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "status": str(account.status),
            }
        except Exception as e:
            logger.error("Alpaca get_account failed: %s", e)
            return {
                "cash": 0.0,
                "portfolio_value": 0.0,
                "status": "ERROR",
            }
