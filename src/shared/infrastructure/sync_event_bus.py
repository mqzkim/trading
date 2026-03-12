"""Synchronous in-process event bus for CLI context.

Same API as AsyncEventBus but all calls are synchronous.
Uses event class name as the routing key for handler lookup.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

from src.shared.domain import DomainEvent


class SyncEventBus:
    """Synchronous in-process event bus.

    Usage:
        bus = SyncEventBus()
        bus.subscribe(ScoreUpdatedEvent, my_handler)
        bus.publish(ScoreUpdatedEvent(symbol="AAPL", ...))
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable
    ) -> None:
        """Register a handler for a specific event type."""
        self._handlers[event_type.__name__].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers synchronously.

        Does not raise if there are no subscribers for the event type.
        """
        event_name = event.__class__.__name__
        for handler in self._handlers.get(event_name, []):
            handler(event)
