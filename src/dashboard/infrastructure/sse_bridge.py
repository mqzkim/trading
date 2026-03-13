"""SSE bridge -- bridges SyncEventBus (sync) to async SSE consumers.

Subscribes to domain events on the synchronous bus, serializes them,
and fans out to all connected SSE consumer queues.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator

from src.shared.infrastructure.sync_event_bus import SyncEventBus

logger = logging.getLogger(__name__)


class SSEBridge:
    """Bridge between SyncEventBus and async SSE streams.

    Usage:
        bridge = SSEBridge(bus)
        bridge.subscribe_events(OrderFilledEvent, RegimeChangedEvent)

        # In SSE endpoint:
        async for data in bridge.stream():
            yield ServerSentEvent(data=json.dumps(data))
    """

    def __init__(self, bus: SyncEventBus) -> None:
        self._bus = bus
        self._queues: list[asyncio.Queue[dict]] = []

    def subscribe_events(self, *event_types: type) -> None:
        """Subscribe to domain event types on the bus."""
        for et in event_types:
            self._bus.subscribe(et, self._on_event)

    def _on_event(self, event: Any) -> None:
        """Sync handler called by SyncEventBus -- serialize and fan out."""
        data = {
            "type": event.__class__.__name__,
            "payload": {
                k: str(v) for k, v in vars(event).items() if not k.startswith("_")
            },
        }
        for q in list(self._queues):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                logger.warning("SSE queue full, dropping event for consumer")

    async def stream(self) -> AsyncIterator[dict]:
        """Async generator yielding events for a single SSE consumer."""
        q: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        self._queues.append(q)
        try:
            while True:
                data = await q.get()
                yield data
        finally:
            self._queues.remove(q)
