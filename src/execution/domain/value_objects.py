"""Execution Domain — Value Objects.

TradePlan, OrderSpec (formerly BracketSpec), OrderResult: 불변 VO.
TradePlanStatus: 상태 열거형.
BracketSpec is a backward-compatible alias for OrderSpec.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.shared.domain import ValueObject


class TradePlanStatus(Enum):
    """Trade plan lifecycle status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class TradePlan(ValueObject):
    """Trade plan VO — holds entry/stop/target/size/reasoning.

    BUY direction: stop_loss_price < entry_price < take_profit_price
    """

    symbol: str = ""
    direction: str = "BUY"
    entry_price: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    quantity: int = 0
    position_value: float = 0.0
    reasoning_trace: str = ""
    composite_score: float = 0.0
    margin_of_safety: float = 0.0
    signal_direction: str = ""

    def _validate(self) -> None:
        if self.entry_price <= 0:
            raise ValueError(f"entry_price must be positive: {self.entry_price}")
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive: {self.quantity}")
        if self.direction == "BUY":
            if self.stop_loss_price >= self.entry_price:
                raise ValueError(
                    f"stop_loss_price must be below entry_price for BUY: "
                    f"{self.stop_loss_price} >= {self.entry_price}"
                )
            if self.take_profit_price <= self.entry_price:
                raise ValueError(
                    f"take_profit_price must be above entry_price for BUY: "
                    f"{self.take_profit_price} <= {self.entry_price}"
                )


@dataclass(frozen=True)
class OrderSpec(ValueObject):
    """Market-agnostic order specification.

    Generalizes the former BracketSpec. stop_loss_price and take_profit_price
    are Optional — Korean market orders may omit bracket legs.
    """

    symbol: str = ""
    quantity: int = 0
    entry_price: float = 0.0
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    direction: str = "BUY"

    def _validate(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive: {self.quantity}")
        if self.entry_price <= 0:
            raise ValueError(f"entry_price must be positive: {self.entry_price}")
        if self.direction == "BUY" and self.stop_loss_price is not None:
            if self.stop_loss_price >= self.entry_price:
                raise ValueError(
                    f"stop_loss_price must be below entry_price for BUY: "
                    f"{self.stop_loss_price} >= {self.entry_price}"
                )
        if self.direction == "BUY" and self.take_profit_price is not None:
            if self.take_profit_price <= self.entry_price:
                raise ValueError(
                    f"take_profit_price must be above entry_price for BUY: "
                    f"{self.take_profit_price} <= {self.entry_price}"
                )


# Backward-compatible alias
BracketSpec = OrderSpec


@dataclass(frozen=True)
class OrderResult(ValueObject):
    """Order execution result."""

    order_id: str = ""
    status: str = ""
    symbol: str = ""
    quantity: int = 0
    filled_price: Optional[float] = None
    error_message: Optional[str] = None

    def _validate(self) -> None:
        pass  # No special validation needed
