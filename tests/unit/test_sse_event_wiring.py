"""Tests for SSE event wiring -- verifies templates, handlers, and monitor lifecycle."""
from __future__ import annotations

import re
from pathlib import Path


# Known event class names that SSEBridge subscribes to
SUBSCRIBED_EVENTS = {
    "OrderFilledEvent",
    "RegimeChangedEvent",
    "DrawdownAlertEvent",
    "PipelineCompletedEvent",
    "PipelineHaltedEvent",
}

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "src" / "dashboard" / "presentation" / "templates"


def test_event_names_match():
    """All sse-swap attributes in templates must match subscribed event class names."""
    sse_swap_pattern = re.compile(r'sse-swap="([^"]+)"')
    mismatches: list[str] = []

    for html_file in TEMPLATES_DIR.rglob("*.html"):
        content = html_file.read_text()
        for match in sse_swap_pattern.finditer(content):
            event_name = match.group(1)
            if event_name not in SUBSCRIBED_EVENTS:
                rel = html_file.relative_to(TEMPLATES_DIR)
                mismatches.append(f"{rel}: sse-swap=\"{event_name}\"")

    assert not mismatches, (
        f"SSE event name mismatches found:\n" + "\n".join(f"  - {m}" for m in mismatches)
    )


def test_pipeline_completed_event_published():
    """RunPipelineHandler publishes PipelineCompletedEvent after successful run."""
    # Stub -- will be completed in Task 2
    pass


def test_drawdown_event_published():
    """PortfolioManagerHandler publishes DrawdownAlertEvent via bus after save."""
    # Stub -- will be completed in Task 2
    pass


def test_monitor_persistent_loop():
    """AlpacaOrderMonitor does not exit when tracked orders is empty."""
    # Stub -- will be completed in Task 2
    pass
