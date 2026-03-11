"""Async in-process event bus for bounded context communication.

Supports both sync and async handlers. Uses event class name
as the routing key for handler lookup.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Callable

from src.shared.domain import DomainEvent


class AsyncEventBus:
    """Simple async in-process event bus.

    Usage:
        bus = AsyncEventBus()
        bus.subscribe(DataIngestedEvent, my_handler)
        await bus.publish(DataIngestedEvent(ticker="AAPL", ...))
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable
    ) -> None:
        """Register a handler for a specific event type."""
        self._handlers[event_type.__name__].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers.

        Handles both sync and async handlers. Does not raise
        if there are no subscribers for the event type.
        """
        event_name = event.__class__.__name__
        for handler in self._handlers.get(event_name, []):
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
