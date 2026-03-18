"""SSE events router -- real-time event streaming.

GET /api/v1/events -- Server-Sent Events stream.
Subscribes to the event bus and emits domain events as SSE messages.
"""
from __future__ import annotations

import asyncio
import json
import logging
import queue
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from commercial.api.dependencies import get_event_bus, verify_dashboard_secret

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events"])

# Event types to bridge from domain bus to SSE
_SSE_EVENT_TYPES: list[str] = [
    "OrderFilledEvent",
    "DrawdownAlertEvent",
    "RegimeChangedEvent",
    "PipelineCompletedEvent",
    "PipelineHaltedEvent",
]


def _event_to_dict(event: Any) -> dict:
    """Convert a domain event to a JSON-serializable dict."""
    if hasattr(event, "__dataclass_fields__"):
        result: dict[str, Any] = {}
        for field_name in event.__dataclass_fields__:
            val = getattr(event, field_name)
            if isinstance(val, datetime):
                result[field_name] = val.isoformat()
            elif hasattr(val, "value"):
                result[field_name] = val.value
            else:
                result[field_name] = val
        return result
    return {"data": str(event)}


@router.get("/events")
async def sse_stream(
    bus=Depends(get_event_bus),
    _: None = Depends(verify_dashboard_secret),
):
    """SSE stream of domain events."""
    event_queue: queue.Queue[tuple[str, dict]] = queue.Queue(maxsize=100)

    # Subscribe to all SSE event types
    def _make_handler(event_type_name: str):
        def _handler(event: Any) -> None:
            try:
                event_queue.put_nowait((event_type_name, _event_to_dict(event)))
            except queue.Full:
                pass  # Drop if consumer is too slow

        return _handler

    # Register handlers (they persist for this request's lifetime)
    handlers = []
    for event_type_name in _SSE_EVENT_TYPES:
        handler = _make_handler(event_type_name)
        handlers.append(handler)
        # Subscribe by importing the event class dynamically
        _subscribe_if_exists(bus, event_type_name, handler)

    async def _generate():
        """Async generator yielding SSE events."""
        try:
            while True:
                # Check for events from the domain bus
                try:
                    event_type, data = event_queue.get_nowait()
                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                except queue.Empty:
                    pass

                # Send keep-alive ping every iteration (15s sleep)
                yield ": ping\n\n"
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _subscribe_if_exists(bus: Any, event_type_name: str, handler: Any) -> None:
    """Subscribe handler to an event type by name, importing the class if found."""
    event_class = _resolve_event_class(event_type_name)
    if event_class is not None:
        bus.subscribe(event_class, handler)


def _resolve_event_class(name: str) -> type | None:
    """Resolve event class by name from known modules."""
    _event_modules = [
        "src.pipeline.domain.events",
        "src.regime.domain.events",
        "src.portfolio.domain.events",
        "src.execution.domain.events",
    ]
    for module_path in _event_modules:
        try:
            import importlib

            mod = importlib.import_module(module_path)
            cls = getattr(mod, name, None)
            if cls is not None:
                return cls
        except ImportError:
            continue
    return None
