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

    # Mock approval_handler (returns no active approval by default)
    approval_handler = MagicMock()
    approval_handler.get_status.return_value = {
        "approval": None,
        "budget": None,
        "pending_review_count": 0,
    }

    # Mock review_queue_repo
    review_queue_repo = MagicMock()
    review_queue_repo.list_pending.return_value = []

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


# -- Signals page tests (16-03) --


def test_signals_page_renders_table():
    """GET /dashboard/signals with score data contains table headers."""
    from src.scoring.domain.value_objects import CompositeScore

    ctx = _make_ctx(ExecutionMode.PAPER)
    mock_score = CompositeScore(value=75.0, risk_adjusted=70.0, strategy="swing")
    ctx["score_repo"].find_all_latest.return_value = {"AAPL": mock_score}
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/dashboard/signals")
    assert resp.status_code == 200
    assert "Scoring Results" in resp.text
    assert "AAPL" in resp.text
    assert "Composite" in resp.text


def test_signals_empty_state(paper_client):
    """With empty scores, contains 'No scoring data' message."""
    resp = paper_client.get("/dashboard/signals")
    assert resp.status_code == 200
    assert "No scoring data" in resp.text


def test_signals_page_shows_recommendations_section(paper_client):
    """Signals page shows 'Signal Recommendations' section."""
    resp = paper_client.get("/dashboard/signals")
    assert resp.status_code == 200
    assert "Signal Recommendations" in resp.text
    assert "No signals generated" in resp.text


# -- Risk page tests (16-03) --


def test_risk_page_renders_gauge(paper_client):
    """GET /dashboard/risk contains drawdown-chart-container div."""
    resp = paper_client.get("/dashboard/risk")
    assert resp.status_code == 200
    assert "drawdown-chart-container" in resp.text


def test_risk_page_shows_regime(paper_client):
    """GET /dashboard/risk contains regime badge text."""
    resp = paper_client.get("/dashboard/risk")
    assert resp.status_code == 200
    assert "Market Regime" in resp.text
    assert "Unknown" in resp.text


def test_risk_page_sector_chart(paper_client):
    """GET /dashboard/risk contains sector-donut div."""
    resp = paper_client.get("/dashboard/risk")
    assert resp.status_code == 200
    assert "sector-donut" in resp.text


def test_risk_page_position_limits(paper_client):
    """GET /dashboard/risk shows position limits bar."""
    resp = paper_client.get("/dashboard/risk")
    assert resp.status_code == 200
    assert "Position Limits" in resp.text
    assert "0 / 20" in resp.text


# -- Pipeline page tests (16-04) --


def test_pipeline_page_renders_runs():
    """GET /dashboard/pipeline with pipeline run data contains Run History."""
    from datetime import datetime, timezone

    from src.pipeline.domain.entities import PipelineRun
    from src.pipeline.domain.value_objects import PipelineStatus, RunMode

    ctx = _make_ctx(ExecutionMode.PAPER)
    mock_run = PipelineRun(
        run_id="abc-123-def",
        started_at=datetime(2026, 3, 13, 16, 30, tzinfo=timezone.utc),
        finished_at=datetime(2026, 3, 13, 16, 35, tzinfo=timezone.utc),
        status=PipelineStatus.COMPLETED,
        mode=RunMode.AUTO,
        stages=[],
    )
    ctx["pipeline_run_repo"].get_recent.return_value = [mock_run]
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/dashboard/pipeline")
    assert resp.status_code == 200
    assert "Run History" in resp.text
    assert "abc-123-" in resp.text


def test_pipeline_shows_approval_form():
    """With no active approval, page shows Create Approval form."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/dashboard/pipeline")
    assert resp.status_code == 200
    assert "Create Approval" in resp.text


def test_pipeline_shows_active_approval():
    """With active approval mock, page contains Suspend button."""
    from datetime import datetime, timezone

    from src.approval.domain.entities import StrategyApproval

    ctx = _make_ctx(ExecutionMode.PAPER)
    mock_approval = StrategyApproval(
        _id="appr-001",
        score_threshold=75.0,
        allowed_regimes=["Bull", "Accumulation"],
        max_per_trade_pct=8.0,
        daily_budget_cap=10000.0,
        expires_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
        created_at=datetime(2026, 3, 13, tzinfo=timezone.utc),
        is_active=True,
    )
    ctx["approval_handler"].get_status.return_value = {
        "approval": mock_approval,
        "budget": None,
        "pending_review_count": 0,
    }
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/dashboard/pipeline")
    assert resp.status_code == 200
    assert "Suspend" in resp.text
    assert "75.0" in resp.text


def test_pipeline_shows_budget_bar():
    """Page contains budget progress section."""
    from src.approval.domain.entities import StrategyApproval
    from src.approval.domain.value_objects import DailyBudgetTracker
    from datetime import datetime, timezone

    ctx = _make_ctx(ExecutionMode.PAPER)
    mock_approval = StrategyApproval(
        _id="appr-002",
        score_threshold=70.0,
        allowed_regimes=["Bull"],
        max_per_trade_pct=8.0,
        daily_budget_cap=5000.0,
        expires_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
        created_at=datetime(2026, 3, 13, tzinfo=timezone.utc),
        is_active=True,
    )
    mock_budget = DailyBudgetTracker(
        budget_cap=5000.0,
        date="2026-03-13",
        spent=1500.0,
        trade_count=3,
    )
    ctx["approval_handler"].get_status.return_value = {
        "approval": mock_approval,
        "budget": mock_budget,
        "pending_review_count": 0,
    }
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/dashboard/pipeline")
    assert resp.status_code == 200
    assert "Daily Budget" in resp.text
    assert "1,500" in resp.text
    assert "5,000" in resp.text


def test_pipeline_shows_review_queue():
    """With pending reviews, page contains Approve button."""
    from datetime import datetime, timezone

    from src.approval.domain.value_objects import TradeReviewItem

    ctx = _make_ctx(ExecutionMode.PAPER)
    mock_item = TradeReviewItem(
        symbol="AAPL",
        plan_json='{"strategy": "swing", "composite_score": 68.5}',
        rejection_reason="score_below_threshold",
        pipeline_run_id="run-001",
        created_at=datetime(2026, 3, 13, tzinfo=timezone.utc),
        id=42,
    )
    ctx["review_queue_repo"].list_pending.return_value = [mock_item]
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.get("/dashboard/pipeline")
    assert resp.status_code == 200
    assert "Approve" in resp.text
    assert "AAPL" in resp.text


def test_approval_create_post():
    """POST /dashboard/approval/create with form data returns 200."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    # After create, get_status returns the new approval
    from datetime import datetime, timezone

    from src.approval.domain.entities import StrategyApproval

    new_approval = StrategyApproval(
        _id="appr-new",
        score_threshold=70.0,
        allowed_regimes=["Bull"],
        max_per_trade_pct=8.0,
        daily_budget_cap=10000.0,
        expires_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
        created_at=datetime(2026, 3, 13, tzinfo=timezone.utc),
        is_active=True,
    )
    ctx["approval_handler"].get_status.return_value = {
        "approval": new_approval,
        "budget": None,
        "pending_review_count": 0,
    }
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/dashboard/approval/create",
        data={
            "score_threshold": "70.0",
            "allowed_regimes": "Bull,Accumulation",
            "max_per_trade_pct": "8.0",
            "daily_budget_cap": "10000",
            "expires_in_days": "30",
        },
    )
    assert resp.status_code == 200
    assert ctx["approval_handler"].create.called


def test_review_approve_post():
    """POST /dashboard/review/approve returns 200."""
    ctx = _make_ctx(ExecutionMode.PAPER)
    app = create_dashboard_app(ctx=ctx)
    client = TestClient(app)
    resp = client.post(
        "/dashboard/review/approve",
        data={"review_id": "42"},
    )
    assert resp.status_code == 200
    ctx["review_queue_repo"].mark_reviewed.assert_called_once_with(42, approved=True)
