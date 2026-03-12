"""Execution Infrastructure -- KIS (한국투자증권) Execution Adapter.

Mock fallback: credentials 없으면 mock 모드로 작동.
python-kis imports는 _init_client() 내부에서만 (module-level import 금지).
CRITICAL: virtual=True 고정 -- Phase 10은 paper trading만.
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import uuid4

from src.execution.domain.repositories import IBrokerAdapter
from src.execution.domain.value_objects import OrderResult, OrderSpec

logger = logging.getLogger(__name__)

# KRX tick size table (2024)
_TICK_TABLE = [
    (1_000, 1),
    (5_000, 5),
    (10_000, 10),
    (50_000, 50),
    (100_000, 100),
    (500_000, 500),
]


def _tick_size(price: float) -> int:
    """Return the KRX tick size for a given price level."""
    for threshold, tick in _TICK_TABLE:
        if price < threshold:
            return tick
    return 1_000


def _round_to_tick(price: float) -> int:
    """Round a price to the nearest valid KRX tick."""
    tick = _tick_size(price)
    return int(round(price / tick) * tick)


def validate_price_limit(
    entry_price: float,
    previous_close: float,
    limit_pct: float = 0.30,
) -> None:
    """Validate KRX daily price limit (+-30% from previous close).

    Raises ValueError if entry_price is outside the allowed range.
    """
    upper = previous_close * (1 + limit_pct)
    lower = previous_close * (1 - limit_pct)
    if entry_price > upper or entry_price < lower:
        raise ValueError(
            f"Entry price {entry_price:,.0f} is outside the 30% daily limit "
            f"[{lower:,.0f} ~ {upper:,.0f}] from previous close {previous_close:,.0f}"
        )


class KisExecutionAdapter(IBrokerAdapter):
    """KIS broker adapter. Always paper trading (virtual=True).

    Operates in mock mode when credentials are absent.
    """

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        account_no: Optional[str] = None,
    ) -> None:
        self._app_key = app_key
        self._app_secret = app_secret
        self._account_no = account_no
        self._use_mock = not (app_key and app_secret and account_no)
        self._client: Any = None
        if not self._use_mock:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize KIS client. Falls back to mock on failure."""
        try:
            import mojito  # noqa: F401 -- lazy import, never at module level

            self._client = mojito.KoreaInvestment(
                api_key=self._app_key,
                api_secret=self._app_secret,
                acc_no=self._account_no,
                mock=True,  # ALWAYS paper trading
            )
        except Exception as e:
            logger.warning("KIS client init failed, falling back to mock: %s", e)
            self._use_mock = True

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        """Submit an order. Mock mode returns filled result."""
        if self._use_mock:
            return self._mock_order(spec)
        return self._real_order(spec)

    def _mock_order(self, spec: OrderSpec) -> OrderResult:
        """Mock order -- returns simulated filled result."""
        order_id = f"KIS-MOCK-{spec.symbol}-{uuid4().hex[:8]}"
        return OrderResult(
            order_id=order_id,
            status="filled",
            symbol=spec.symbol,
            quantity=spec.quantity,
            filled_price=spec.entry_price,
        )

    def _real_order(self, spec: OrderSpec) -> OrderResult:
        """Real KIS order. Only called when credentials present."""
        rounded_price = _round_to_tick(spec.entry_price)
        # python-kis/mojito exact API TBD -- KIS developer registration pending
        raise NotImplementedError(
            f"Real KIS order submission (price={rounded_price}) requires "
            "KIS developer setup. Register at https://apiportal.koreainvestment.com"
        )

    def get_positions(self) -> list[dict]:
        """Get current open positions."""
        if self._use_mock:
            return []
        raise NotImplementedError("KIS get_positions: requires KIS developer setup")

    def get_account(self) -> dict:
        """Get account summary."""
        if self._use_mock:
            return {"currency": "KRW", "cash": 0.0, "portfolio_value": 0.0}
        raise NotImplementedError("KIS get_account: requires KIS developer setup")
