"""Tests for dashboard JSON REST API endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.dashboard.presentation.app import create_dashboard_app
from src.execution.domain.value_objects import ExecutionMode
from src.shared.infrastructure.sync_event_bus import SyncEventBus


def _make_ctx(execution_mode: ExecutionMode = ExecutionMode.PAPER) -> dict:
    """Create a minimal mock bootstrap context for tests."""
    position_repo = MagicMock()
    position_repo.find_all_open.return_value = []

    score_repo = MagicMock()
    score_repo.find_all_latest.return_value = {}
    score_repo.find_all_latest_with_details.return_value = []

    trade_plan_repo = MagicMock()
    trade_plan_repo._db_path = ":memory:"

    pipeline_run_repo = MagicMock()
    pipeline_run_repo.get_recent.return_value = []

    regime_repo = MagicMock()
    regime_repo.find_latest.return_value = None

    portfolio_handler = MagicMock()
    portfolio_handler._portfolio_repo.find_by_id.return_value = None

    signal_repo = MagicMock()
    signal_repo.find_all_active.return_value = []

    approval_handler = MagicMock()
    approval_handler.get_status.return_value = {
        "approval": None,
        "budget": None,
        "pending_review_count": 0,
    }

    review_queue_repo = MagicMock()
    review_queue_repo.list_pending.return_value = []

    run_pipeline_handler = MagicMock()

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
        "approval_handler": approval_handler,
        "review_queue_repo": review_queue_repo,
        "run_pipeline_handler": run_pipeline_handler,
    }


@pytest.fixture
def client():
    """Test client with paper mode context."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    return TestClient(app)


# -- GET /api/v1/dashboard/overview --


def test_overview_returns_json_with_expected_keys(client):
    """GET /overview returns 200 with JSON containing total_value, positions keys."""
    resp = client.get("/api/v1/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value" in data
    assert "positions" in data
    assert "equity_curve" in data
    assert "regime_periods" in data


def test_overview_does_not_contain_plotly_keys(client):
    """GET /overview does NOT contain equity_curve_chart_json key."""
    resp = client.get("/api/v1/dashboard/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "equity_curve_chart_json" not in data


# -- GET /api/v1/dashboard/signals --


def test_signals_returns_json_with_expected_keys(client):
    """GET /signals returns 200 with JSON containing scores, signals keys."""
    resp = client.get("/api/v1/dashboard/signals")
    assert resp.status_code == 200
    data = resp.json()
    assert "scores" in data
    assert "signals" in data


def test_signals_accepts_sort_params(client):
    """GET /signals accepts sort and desc query params."""
    resp = client.get("/api/v1/dashboard/signals?sort=risk_adjusted&desc=false")
    assert resp.status_code == 200
    data = resp.json()
    assert "scores" in data


def test_signals_returns_sub_score_fields():
    """GET /signals returns scores with fundamental_score, technical_score, sentiment_score."""
    ctx = _make_ctx()
    ctx["score_repo"].find_all_latest_with_details.return_value = [
        {
            "symbol": "AAPL",
            "composite_score": 72.5,
            "risk_adjusted": 68.3,
            "strategy": "swing",
            "fundamental_score": 65.0,
            "technical_score": 78.0,
            "sentiment_score": 55.0,
        }
    ]
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/api/v1/dashboard/signals")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["scores"]) == 1
    score = data["scores"][0]
    assert score["fundamental_score"] == 65.0
    assert score["technical_score"] == 78.0
    assert score["sentiment_score"] == 55.0
    assert score["sentiment_confidence"] == "NONE"


# -- GET /api/v1/dashboard/risk --


def test_risk_returns_json_with_expected_keys(client):
    """GET /risk returns 200 with JSON containing drawdown_pct, regime keys."""
    resp = client.get("/api/v1/dashboard/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert "drawdown_pct" in data
    assert "regime" in data
    assert "sector_weights" in data
    assert "position_count" in data


def test_risk_does_not_contain_plotly_keys(client):
    """GET /risk does NOT contain gauge_json or donut_json keys (Plotly stripped)."""
    resp = client.get("/api/v1/dashboard/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert "gauge_json" not in data
    assert "donut_json" not in data


def test_risk_returns_regime_probabilities_when_regime_exists():
    """GET /risk returns regime_probabilities dict with 4 regimes summing to ~1.0."""
    ctx = _make_ctx()
    mock_regime = MagicMock()
    mock_regime.regime_type.value = "Bull"
    mock_regime.confidence = 0.82
    ctx["regime_repo"].find_latest.return_value = mock_regime
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/api/v1/dashboard/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert "regime_probabilities" in data
    probs = data["regime_probabilities"]
    assert len(probs) == 4
    assert probs["Bull"] == 0.82
    assert abs(sum(probs.values()) - 1.0) < 0.01
    assert data["regime_confidence"] == 0.82


def test_risk_returns_empty_regime_probabilities_when_no_regime():
    """GET /risk returns empty regime_probabilities when no regime data."""
    ctx = _make_ctx()
    ctx["regime_repo"].find_latest.return_value = None
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/api/v1/dashboard/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["regime_probabilities"] == {}
    assert data["regime_confidence"] == 0.0


# -- GET /api/v1/dashboard/pipeline --


def test_pipeline_returns_json_with_expected_keys(client):
    """GET /pipeline returns 200 with JSON containing pipeline_runs, approval_status keys."""
    resp = client.get("/api/v1/dashboard/pipeline")
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline_runs" in data
    assert "approval_status" in data
    assert "daily_budget" in data
    assert "review_queue" in data


# -- POST /api/v1/dashboard/pipeline/run --


def test_pipeline_run_accepts_json_and_returns_status():
    """POST /pipeline/run accepts JSON body and returns status=running."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/dashboard/pipeline/run",
        json={"symbols": ["AAPL", "MSFT"], "dry_run": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["dry_run"] is True
    assert "AAPL" in data["symbols"]
    assert "MSFT" in data["symbols"]


# -- POST /api/v1/dashboard/approval/create --


def test_approval_create_accepts_json_and_calls_handler():
    """POST /approval/create accepts JSON body and calls approval_handler.create."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/dashboard/approval/create",
        json={
            "score_threshold": 75.0,
            "allowed_regimes": ["Bull"],
            "max_per_trade_pct": 5.0,
            "daily_budget_cap": 8000.0,
            "expires_in_days": 14,
        },
    )
    assert resp.status_code == 200
    assert ctx["approval_handler"].create.called


# -- POST /api/v1/dashboard/approval/suspend --


def test_approval_suspend_accepts_json_and_calls_handler():
    """POST /approval/suspend accepts JSON body and calls approval_handler.revoke."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/dashboard/approval/suspend",
        json={"approval_id": "appr-001"},
    )
    assert resp.status_code == 200
    assert ctx["approval_handler"].revoke.called


# -- POST /api/v1/dashboard/approval/resume --


def test_approval_resume_accepts_json_and_calls_handler():
    """POST /approval/resume accepts JSON body and calls approval_handler.resume."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/dashboard/approval/resume",
        json={"approval_id": "appr-001"},
    )
    assert resp.status_code == 200
    assert ctx["approval_handler"].resume.called


# -- POST /api/v1/dashboard/review/approve --


def test_review_approve_accepts_json_and_calls_mark_reviewed():
    """POST /review/approve accepts JSON body and calls mark_reviewed(id, approved=True)."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/dashboard/review/approve",
        json={"review_id": 42},
    )
    assert resp.status_code == 200
    ctx["review_queue_repo"].mark_reviewed.assert_called_once_with(42, approved=True)


# -- POST /api/v1/dashboard/review/reject --


def test_review_reject_accepts_json_and_calls_mark_reviewed():
    """POST /review/reject accepts JSON body and calls mark_reviewed(id, approved=False)."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/dashboard/review/reject",
        json={"review_id": 99},
    )
    assert resp.status_code == 200
    ctx["review_queue_repo"].mark_reviewed.assert_called_once_with(99, approved=False)


# -- GET /api/v1/dashboard/events (SSE) --


def test_sse_endpoint_registered():
    """GET /api/v1/dashboard/events route is registered on the app."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    route_paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/api/v1/dashboard/events" in route_paths
