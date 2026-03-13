"""Tests for dashboard web routes and app factory."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.dashboard.presentation.app import create_dashboard_app
from src.execution.domain.value_objects import ExecutionMode
from src.shared.infrastructure.sync_event_bus import SyncEventBus


def _make_ctx(execution_mode: ExecutionMode = ExecutionMode.PAPER) -> dict:
    """Create a minimal mock bootstrap context for tests."""
    # Mock position_repo returning empty list
    position_repo = MagicMock()
    position_repo.find_all_open.return_value = []

    # Mock score_repo
    score_repo = MagicMock()
    score_repo.find_all_latest.return_value = {}

    # Mock trade_plan_repo with _db_path that won't exist (graceful handling)
    trade_plan_repo = MagicMock()
    trade_plan_repo._db_path = ":memory:"

    # Mock pipeline_run_repo
    pipeline_run_repo = MagicMock()
    pipeline_run_repo.get_recent.return_value = []

    # Mock regime_repo
    regime_repo = MagicMock()
    regime_repo.find_latest.return_value = None

    # Mock portfolio_handler
    portfolio_handler = MagicMock()
    portfolio_handler._portfolio_repo.find_by_id.return_value = None

    # Mock signal_repo
    signal_repo = MagicMock()
    signal_repo.find_all_active.return_value = []

    return {
        "bus": SyncEventBus(),
        "execution_mode": execution_mode,
        "position_repo": position_repo,
        "score_repo": score_repo,
        "trade_plan_repo": trade_plan_repo,
        "pipeline_run_repo": pipeline_run_repo,
        "regime_repo": regime_repo,
        "portfolio_handler": portfolio_handler,
        "signal_repo": signal_repo,
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


def test_overview_shows_kpi_cards(paper_client):
    resp = paper_client.get("/dashboard/")
    assert resp.status_code == 200
    assert "Total Assets" in resp.text


def test_overview_shows_holdings(paper_client):
    resp = paper_client.get("/dashboard/")
    assert resp.status_code == 200
    assert "Ticker" in resp.text
    assert "Score" in resp.text


def test_overview_empty_state(paper_client):
    resp = paper_client.get("/dashboard/")
    assert resp.status_code == 200
    assert "No open positions" in resp.text


def test_trade_history_renders(paper_client):
    resp = paper_client.get("/dashboard/")
    assert resp.status_code == 200
    assert "Trade History" in resp.text
    assert "No trades yet" in resp.text
