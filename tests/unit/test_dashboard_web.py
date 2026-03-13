"""Tests for dashboard web routes and app factory."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.dashboard.presentation.app import create_dashboard_app
from src.execution.domain.value_objects import ExecutionMode
from src.shared.infrastructure.sync_event_bus import SyncEventBus


def _make_ctx(execution_mode: ExecutionMode = ExecutionMode.PAPER) -> dict:
    """Create a minimal mock bootstrap context for tests."""
    return {
        "bus": SyncEventBus(),
        "execution_mode": execution_mode,
    }


@pytest.fixture
def paper_client():
    """Test client with paper mode context."""
    app = create_dashboard_app(ctx=_make_ctx(ExecutionMode.PAPER))
    return TestClient(app)


@pytest.fixture
def live_client():
    """Test client with live mode context."""
    app = create_dashboard_app(ctx=_make_ctx(ExecutionMode.LIVE))
    return TestClient(app)


def test_overview_page(paper_client):
    resp = paper_client.get("/dashboard/")
    assert resp.status_code == 200
    assert "PAPER TRADING" in resp.text
    assert "Overview" in resp.text


def test_signals_page(paper_client):
    resp = paper_client.get("/dashboard/signals")
    assert resp.status_code == 200
    assert "Signals" in resp.text


def test_risk_page(paper_client):
    resp = paper_client.get("/dashboard/risk")
    assert resp.status_code == 200
    assert "Risk" in resp.text


def test_pipeline_page(paper_client):
    resp = paper_client.get("/dashboard/pipeline")
    assert resp.status_code == 200
    assert "Pipeline" in resp.text


def test_mode_banner_live(live_client):
    resp = live_client.get("/dashboard/")
    assert resp.status_code == 200
    assert "LIVE TRADING" in resp.text


def test_mode_banner_paper(paper_client):
    resp = paper_client.get("/dashboard/")
    assert resp.status_code == 200
    assert "PAPER TRADING" in resp.text


def test_sse_endpoint_registered():
    """Verify SSE endpoint is registered on the app router."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)

    # Check that the /dashboard/events route exists in the app
    route_paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/dashboard/events" in route_paths

    # Verify SSE bridge is wired
    assert hasattr(app.state, "sse_bridge")
    assert app.state.sse_bridge is not None
