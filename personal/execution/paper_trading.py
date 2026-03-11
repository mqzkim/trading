"""Paper trading interface -- Alpaca with mock fallback."""
import os
import logging
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class Order:
    order_id: str
    symbol: str
    qty: int
    side: str  # "buy" | "sell"
    order_type: str  # "market" | "limit"
    limit_price: Optional[float]
    status: str  # "submitted" | "filled" | "cancelled"
    filled_price: Optional[float] = None


@dataclass
class Position:
    symbol: str
    qty: int
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PaperTradingClient:
    """Alpaca paper trading client with mock fallback."""

    def __init__(self):
        self._api_key = os.getenv("ALPACA_API_KEY")
        self._secret = os.getenv("ALPACA_SECRET_KEY")
        self._base_url = os.getenv(
            "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
        )
        self._use_mock = not (self._api_key and self._secret)
        self._mock_orders: dict[str, Order] = {}
        self._mock_positions: dict[str, Position] = {}
        self._mock_cash: float = 100_000.0

        if self._use_mock:
            logger.warning(
                "ALPACA credentials not set -- using mock paper trading"
            )

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str = "market",
        limit_price: Optional[float] = None,
    ) -> Order:
        """Submit a buy or sell order.

        In mock mode the order is filled immediately at a synthetic price.
        When real Alpaca credentials are available, delegates to the SDK.
        """
        if self._use_mock:
            return self._mock_submit(symbol, qty, side, order_type, limit_price)

        # Real Alpaca path
        try:
            import alpaca_trade_api as tradeapi

            api = tradeapi.REST(
                self._api_key, self._secret, self._base_url, api_version="v2"
            )
            alpaca_order = api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force="gtc",
                limit_price=limit_price if order_type == "limit" else None,
            )
            return Order(
                order_id=alpaca_order.id,
                symbol=symbol,
                qty=qty,
                side=side,
                order_type=order_type,
                limit_price=limit_price,
                status=alpaca_order.status,
                filled_price=float(alpaca_order.filled_avg_price)
                if alpaca_order.filled_avg_price
                else None,
            )
        except Exception as exc:
            logger.error("Alpaca submit_order failed: %s -- falling back to mock", exc)
            return self._mock_submit(symbol, qty, side, order_type, limit_price)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order. Returns True on success."""
        if self._use_mock:
            if order_id in self._mock_orders:
                self._mock_orders[order_id].status = "cancelled"
                return True
            return False

        try:
            import alpaca_trade_api as tradeapi

            api = tradeapi.REST(
                self._api_key, self._secret, self._base_url, api_version="v2"
            )
            api.cancel_order(order_id)
            return True
        except Exception as exc:
            logger.error("Alpaca cancel_order failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------------

    def get_positions(self) -> list[Position]:
        """Return all open positions."""
        if self._use_mock:
            return list(self._mock_positions.values())

        try:
            import alpaca_trade_api as tradeapi

            api = tradeapi.REST(
                self._api_key, self._secret, self._base_url, api_version="v2"
            )
            raw = api.list_positions()
            return [
                Position(
                    symbol=p.symbol,
                    qty=int(p.qty),
                    avg_entry_price=float(p.avg_entry_price),
                    current_price=float(p.current_price),
                    unrealized_pnl=float(p.unrealized_pl),
                    unrealized_pnl_pct=float(p.unrealized_plpc),
                )
                for p in raw
            ]
        except Exception as exc:
            logger.error("Alpaca get_positions failed: %s", exc)
            return list(self._mock_positions.values())

    # ------------------------------------------------------------------
    # Portfolio / Account
    # ------------------------------------------------------------------

    def get_portfolio_value(self) -> float:
        """Return total portfolio value (cash + position market values)."""
        if self._use_mock:
            positions_value = sum(
                pos.qty * pos.current_price
                for pos in self._mock_positions.values()
            )
            return self._mock_cash + positions_value

        try:
            import alpaca_trade_api as tradeapi

            api = tradeapi.REST(
                self._api_key, self._secret, self._base_url, api_version="v2"
            )
            account = api.get_account()
            return float(account.portfolio_value)
        except Exception as exc:
            logger.error("Alpaca get_portfolio_value failed: %s", exc)
            positions_value = sum(
                pos.qty * pos.current_price
                for pos in self._mock_positions.values()
            )
            return self._mock_cash + positions_value

    def get_account(self) -> dict:
        """Return account summary dict."""
        if self._use_mock:
            return {
                "cash": self._mock_cash,
                "portfolio_value": self.get_portfolio_value(),
                "status": "ACTIVE",
            }

        try:
            import alpaca_trade_api as tradeapi

            api = tradeapi.REST(
                self._api_key, self._secret, self._base_url, api_version="v2"
            )
            account = api.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "status": account.status,
            }
        except Exception as exc:
            logger.error("Alpaca get_account failed: %s", exc)
            return {
                "cash": self._mock_cash,
                "portfolio_value": self.get_portfolio_value(),
                "status": "ACTIVE",
            }

    # ------------------------------------------------------------------
    # Mock internals
    # ------------------------------------------------------------------

    def _mock_submit(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str,
        limit_price: Optional[float],
    ) -> Order:
        """Create a mock order and update mock positions."""
        order_id = f"MOCK-{symbol}-{side}-{len(self._mock_orders) + 1}"
        # Synthetic fill price
        filled_price = limit_price if limit_price else 150.0

        order = Order(
            order_id=order_id,
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            limit_price=limit_price,
            status="filled",
            filled_price=filled_price,
        )
        self._mock_orders[order_id] = order

        # Update mock positions
        self._update_mock_position(symbol, qty, side, filled_price)
        return order

    def _update_mock_position(
        self, symbol: str, qty: int, side: str, price: float
    ) -> None:
        """Adjust mock positions and cash after a fill."""
        if side == "buy":
            self._mock_cash -= qty * price
            if symbol in self._mock_positions:
                pos = self._mock_positions[symbol]
                total_cost = pos.avg_entry_price * pos.qty + price * qty
                new_qty = pos.qty + qty
                pos.avg_entry_price = total_cost / new_qty
                pos.qty = new_qty
                # Approximate current_price with a small gain for mock
                pos.current_price = pos.avg_entry_price * 1.01
                pos.unrealized_pnl = (pos.current_price - pos.avg_entry_price) * pos.qty
                pos.unrealized_pnl_pct = (
                    (pos.current_price / pos.avg_entry_price - 1) * 100
                    if pos.avg_entry_price > 0
                    else 0.0
                )
            else:
                current = price * 1.01
                self._mock_positions[symbol] = Position(
                    symbol=symbol,
                    qty=qty,
                    avg_entry_price=price,
                    current_price=current,
                    unrealized_pnl=(current - price) * qty,
                    unrealized_pnl_pct=(current / price - 1) * 100,
                )
        elif side == "sell":
            self._mock_cash += qty * price
            if symbol in self._mock_positions:
                pos = self._mock_positions[symbol]
                pos.qty -= qty
                if pos.qty <= 0:
                    del self._mock_positions[symbol]
