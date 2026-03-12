"""Tests for GET /api/v1/signals/{ticker} endpoint.

Includes LEGAL BOUNDARY tests -- signal responses must not contain
investment advice fields (margin_of_safety, reasoning_trace, position
sizing, stop-loss, take-profit, or recommendation language).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.shared.domain import Ok, Err

from tests.unit.conftest_api import (
    TEST_JWT_SECRET,
    TEST_JWT_ALGORITHM,
    make_jwt_token,
    mock_bootstrap_context,
)


# Full handler result including fields that MUST NOT appear in API response
MOCK_SIGNAL_RESULT = {
    "symbol": "AAPL",
    "direction": "BUY",
    "strength": "STRONG",
    "consensus_count": 3,
    "methodology_count": 4,
    "composite_score": 72.5,
    "margin_of_safety": 0.15,  # MUST NOT appear in response
    "methodology_scores": {
        "CAN_SLIM": 80.0,
        "MAGIC_FORMULA": 70.0,
        "DUAL_MOMENTUM": 65.0,
        "TREND_FOLLOWING": 75.0,
    },
    "reasoning_trace": "AAPL: BUY\n  Composite Score: 72.5\n  Margin of Safety: 15.0%",  # MUST NOT appear
    "regime_type": "Bull",
    "strategy_weights": {
        "CAN_SLIM": 0.30,
        "MAGIC_FORMULA": 0.25,
        "DUAL_MOMENTUM": 0.20,
        "TREND_FOLLOWING": 0.25,
    },
    "methodology_directions": {
        "CAN_SLIM": "BUY",
        "MAGIC_FORMULA": "BUY",
        "DUAL_MOMENTUM": "HOLD",
        "TREND_FOLLOWING": "BUY",
    },
}


@pytest.fixture
def client_and_mocks():
    """Set up TestClient with mocked dependencies."""
    import commercial.api.config as config_mod

    config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
    config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

    from commercial.api.main import app
    from commercial.api.dependencies import get_current_user, get_signal_handler
    from commercial.api.middleware.rate_limit import limiter

    # Reset rate limiter storage to avoid cross-test accumulation
    limiter.reset()

    ctx = mock_bootstrap_context()
    mock_handler = ctx["signal_handler"]

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user-1",
        "tier": "free",
    }
    app.dependency_overrides[get_signal_handler] = lambda: mock_handler

    client = TestClient(app)
    yield client, mock_handler

    app.dependency_overrides.clear()


class TestSignalFusionEndpoint:
    """GET /api/v1/signals/{ticker} tests."""

    def test_valid_request_returns_200(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert data["consensus_count"] == 3
        assert data["methodology_count"] == 4

    def test_direction_uses_informational_language(self, client_and_mocks):
        """Direction should be Bullish/Bearish/Neutral, NOT BUY/SELL/HOLD."""
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert data["direction"] in ("Bullish", "Bearish", "Neutral")
        assert data["direction"] == "Bullish"  # BUY -> Bullish

    def test_handler_err_returns_422(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Err(Exception("Scoring failed"))

        resp = client.get(
            "/api/v1/signals/FAIL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 422

    def test_no_jwt_returns_401_or_403(self, client_and_mocks):
        client, handler = client_and_mocks

        from commercial.api.dependencies import get_current_user
        from commercial.api.main import app

        app.dependency_overrides.pop(get_current_user, None)

        resp = client.get("/api/v1/signals/AAPL")

        assert resp.status_code in (401, 403)

    def test_disclaimer_present(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert "disclaimer" in data
        assert len(data["disclaimer"]) > 10


class TestSignalLegalBoundary:
    """CRITICAL: Legal boundary enforcement tests.

    Signal responses must NEVER contain investment advice fields.
    Violation = potential regulatory issue.
    """

    def test_no_margin_of_safety_in_response(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert "margin_of_safety" not in data

    def test_no_reasoning_trace_in_response(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert "reasoning_trace" not in data

    def test_no_position_fields_in_response(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        for key in data:
            assert "position" not in key.lower(), f"Legal violation: '{key}' field found"

    def test_no_recommendation_fields_in_response(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        for key in data:
            assert "recommendation" not in key.lower(), f"Legal violation: '{key}' field found"

    def test_no_stop_loss_or_take_profit_in_response(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        for key in data:
            assert "stop_loss" not in key.lower(), f"Legal violation: '{key}' field found"
            assert "take_profit" not in key.lower(), f"Legal violation: '{key}' field found"


class TestSignalMethodologyVotes:
    """Test methodology_votes list structure."""

    def test_methodology_votes_has_4_entries(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert data["methodology_votes"] is not None
        assert len(data["methodology_votes"]) == 4

    def test_each_vote_has_name_direction_score(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        for vote in data["methodology_votes"]:
            assert "name" in vote
            assert "direction" in vote
            assert "score" in vote

    def test_vote_directions_use_informational_language(self, client_and_mocks):
        """Per-vote directions also use Bullish/Bearish/Neutral."""
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SIGNAL_RESULT)

        resp = client.get(
            "/api/v1/signals/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        allowed = {"Bullish", "Bearish", "Neutral"}
        for vote in data["methodology_votes"]:
            assert vote["direction"] in allowed, f"Vote direction '{vote['direction']}' not informational"
