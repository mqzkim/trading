"""Tests for GET /api/v1/quantscore/{ticker} endpoint."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.shared.domain import Ok, Err

# Reuse shared fixtures
from tests.unit.conftest_api import (
    TEST_JWT_SECRET,
    TEST_JWT_ALGORITHM,
    make_jwt_token,
    mock_bootstrap_context,
)


MOCK_SCORE_RESULT = {
    "symbol": "AAPL",
    "safety_passed": True,
    "composite_score": 72.5,
    "risk_adjusted_score": 68.3,
    "strategy": "swing",
    "fundamental_score": 65.0,
    "technical_score": 78.0,
    "sentiment_score": 55.0,
    "f_score": 7,
    "z_score": 2.1,
    "m_score": -1.8,
    "event": MagicMock(),  # Internal -- should NOT appear in response
    "technical_sub_scores": [
        {"name": "RSI", "value": 62.0, "explanation": "Neutral", "raw_value": 45.0},
        {"name": "MACD", "value": 70.0, "explanation": "Bullish", "raw_value": 1.2},
    ],
    "sentiment_sub_scores": [
        {"name": "News", "value": 60.0, "raw_value": 60.0},
        {"name": "Insider", "value": 45.0, "raw_value": 45.0},
        {"name": "Institutional", "value": 70.0, "raw_value": 70.0},
        {"name": "Analyst", "value": 55.0, "raw_value": 55.0},
    ],
    "sentiment_confidence": "MEDIUM",
}

MOCK_SCORE_RESULT_NO_SENTIMENT = {
    "symbol": "AAPL",
    "safety_passed": True,
    "composite_score": 72.5,
    "risk_adjusted_score": 68.3,
    "strategy": "swing",
    "fundamental_score": 65.0,
    "technical_score": 78.0,
    "sentiment_score": None,
    "f_score": 7,
    "z_score": 2.1,
    "m_score": -1.8,
    "event": MagicMock(),
    "technical_sub_scores": [
        {"name": "RSI", "value": 62.0, "explanation": "Neutral", "raw_value": 45.0},
    ],
    "sentiment_confidence": "NONE",
}


@pytest.fixture
def client_and_mocks():
    """Set up TestClient with mocked dependencies."""
    import commercial.api.config as config_mod

    config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
    config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

    from commercial.api.main import app
    from commercial.api.dependencies import get_current_user, get_score_handler
    from commercial.api.middleware.rate_limit import limiter

    limiter.reset()

    ctx = mock_bootstrap_context()
    mock_handler = ctx["score_handler"]

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user-1",
        "tier": "free",
    }
    app.dependency_overrides[get_score_handler] = lambda: mock_handler

    client = TestClient(app)
    yield client, mock_handler

    app.dependency_overrides.clear()


class TestQuantScoreEndpoint:
    """GET /api/v1/quantscore/{ticker} tests."""

    def test_valid_request_returns_200_with_score_breakdown(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT)

        resp = client.get(
            "/api/v1/quantscore/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert data["composite_score"] == 72.5
        assert data["risk_adjusted_score"] == 68.3
        assert data["safety_passed"] is True
        assert data["fundamental_score"] == 65.0
        assert data["technical_score"] == 78.0
        assert data["sentiment_score"] == 55.0
        assert "disclaimer" in data
        assert len(data["disclaimer"]) > 10

    def test_sub_scores_included_when_present(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT)

        resp = client.get(
            "/api/v1/quantscore/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert data["sub_scores"] is not None
        assert len(data["sub_scores"]) == 2
        assert "RSI" in data["sub_scores"]
        assert data["sub_scores"]["RSI"]["value"] == 62.0

    def test_strategy_query_param_passed_to_handler(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT)

        resp = client.get(
            "/api/v1/quantscore/AAPL?strategy=position",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 200
        call_args = handler.handle.call_args[0][0]
        assert call_args.symbol == "AAPL"
        assert call_args.strategy == "position"

    def test_handler_err_returns_422(self, client_and_mocks):
        client, handler = client_and_mocks
        handler.handle.return_value = Err(Exception("Data fetch failed"))

        resp = client.get(
            "/api/v1/quantscore/FAIL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 422

    def test_no_jwt_returns_401_or_403(self, client_and_mocks):
        client, handler = client_and_mocks

        # Remove the auth override so real auth kicks in
        from commercial.api.dependencies import get_current_user
        from commercial.api.main import app

        app.dependency_overrides.pop(get_current_user, None)

        resp = client.get("/api/v1/quantscore/AAPL")

        assert resp.status_code in (401, 403)

    def test_response_has_no_event_field(self, client_and_mocks):
        """Internal 'event' field from handler must be stripped."""
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT)

        resp = client.get(
            "/api/v1/quantscore/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert "event" not in data


class TestQuantScoreSubScores:
    """Test typed sub-score lists and sentiment confidence."""

    def test_technical_sub_scores_list_structure(self, client_and_mocks):
        """technical_sub_scores is a list of {name, value, raw_value}."""
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT)

        resp = client.get(
            "/api/v1/quantscore/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert data["technical_sub_scores"] is not None
        assert len(data["technical_sub_scores"]) == 2
        entry = data["technical_sub_scores"][0]
        assert "name" in entry
        assert "value" in entry
        assert "raw_value" in entry
        assert entry["name"] == "RSI"
        assert entry["value"] == 62.0

    def test_sentiment_sub_scores_list_structure(self, client_and_mocks):
        """sentiment_sub_scores is a list of {name, value, raw_value}."""
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT)

        resp = client.get(
            "/api/v1/quantscore/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert data["sentiment_sub_scores"] is not None
        assert len(data["sentiment_sub_scores"]) == 4
        names = [s["name"] for s in data["sentiment_sub_scores"]]
        assert "News" in names
        assert "Insider" in names
        assert "Institutional" in names
        assert "Analyst" in names

    def test_sentiment_confidence_present(self, client_and_mocks):
        """sentiment_confidence is always present as string."""
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT)

        resp = client.get(
            "/api/v1/quantscore/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert "sentiment_confidence" in data
        assert data["sentiment_confidence"] == "MEDIUM"

    def test_no_sentiment_data_returns_none_and_confidence_none(self, client_and_mocks):
        """When no sentiment, score is null and confidence is NONE."""
        client, handler = client_and_mocks
        handler.handle.return_value = Ok(MOCK_SCORE_RESULT_NO_SENTIMENT)

        resp = client.get(
            "/api/v1/quantscore/AAPL",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert data["sentiment_score"] is None
        assert data["sentiment_confidence"] == "NONE"
