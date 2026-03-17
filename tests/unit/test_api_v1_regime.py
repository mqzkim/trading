"""Tests for GET /api/v1/regime/current and /regime/history endpoints."""
from __future__ import annotations

import datetime
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


MOCK_REGIME_RESULT = {
    "regime_type": "Bull",
    "confidence": 0.85,
    "vix": 15.2,
    "adx": 28.5,
    "yield_spread": 1.2,
    "sp500_above_ma200": True,
    "sp500_deviation_pct": 5.3,
    "detected_at": "2026-03-12T10:00:00+00:00",
    "confirmed_days": 5,
    "is_confirmed": True,
}


def _make_mock_regime_entity(
    regime_type: str = "Bull",
    confidence: float = 0.85,
    detected_at: str = "2026-03-10T10:00:00+00:00",
    is_confirmed: bool = True,
    confirmed_days: int = 5,
):
    """Build a mock MarketRegime entity for history tests."""
    entity = MagicMock()
    entity.regime_type.value = regime_type
    entity.confidence = confidence
    entity.detected_at.isoformat.return_value = detected_at
    entity.is_confirmed = is_confirmed
    entity.confirmed_days = confirmed_days
    return entity


@pytest.fixture
def client_and_mocks():
    """Set up TestClient with mocked dependencies."""
    import commercial.api.config as config_mod

    config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
    config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

    from commercial.api.main import app
    from commercial.api.dependencies import (
        get_current_user,
        get_regime_handler,
        get_context,
    )
    from commercial.api.middleware.rate_limit import limiter

    limiter.reset()

    ctx = mock_bootstrap_context()
    mock_handler = ctx["regime_handler"]

    # Mock regime repo for history endpoint
    mock_regime_repo = MagicMock()
    mock_handler._regime_repo = mock_regime_repo

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": "test-user-1",
        "tier": "free",
    }
    app.dependency_overrides[get_regime_handler] = lambda: mock_handler
    # Provide context with regime_handler for history endpoint
    app.dependency_overrides[get_context] = lambda: {
        "regime_handler": mock_handler,
    }

    client = TestClient(app)
    yield client, mock_handler, mock_regime_repo

    app.dependency_overrides.clear()


class TestRegimeCurrentEndpoint:
    """GET /api/v1/regime/current tests."""

    def test_returns_200_with_regime_data(self, client_and_mocks):
        client, handler, _ = client_and_mocks
        handler.handle.return_value = Ok(MOCK_REGIME_RESULT)

        resp = client.get(
            "/api/v1/regime/current",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["regime_type"] == "Bull"
        assert data["confidence"] == 0.85
        assert data["is_confirmed"] is True
        assert data["vix"] == 15.2
        assert data["adx"] == 28.5
        assert data["yield_spread"] == 1.2
        assert "detected_at" in data
        assert "disclaimer" in data

    def test_returns_404_when_no_data(self, client_and_mocks):
        client, handler, repo = client_and_mocks
        handler.handle.return_value = Err(Exception("No data"))
        repo.find_latest.return_value = None

        resp = client.get(
            "/api/v1/regime/current",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 404

    def test_no_jwt_returns_401_or_403(self, client_and_mocks):
        client, _, _ = client_and_mocks

        from commercial.api.dependencies import get_current_user
        from commercial.api.main import app

        app.dependency_overrides.pop(get_current_user, None)

        resp = client.get("/api/v1/regime/current")

        assert resp.status_code in (401, 403)


class TestRegimeProbabilities:
    """Test regime_probabilities dict in /current response."""

    def test_regime_probabilities_present_with_4_keys(self, client_and_mocks):
        """regime_probabilities has Bull/Bear/Sideways/Crisis keys."""
        client, handler, _ = client_and_mocks
        handler.handle.return_value = Ok(MOCK_REGIME_RESULT)

        resp = client.get(
            "/api/v1/regime/current",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        assert "regime_probabilities" in data
        probs = data["regime_probabilities"]
        assert set(probs.keys()) == {"Bull", "Bear", "Sideways", "Crisis"}

    def test_regime_probabilities_sum_to_one(self, client_and_mocks):
        """Probability values sum to approximately 1.0."""
        client, handler, _ = client_and_mocks
        handler.handle.return_value = Ok(MOCK_REGIME_RESULT)

        resp = client.get(
            "/api/v1/regime/current",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        probs = data["regime_probabilities"]
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01, f"Probabilities sum to {total}, expected ~1.0"

    def test_dominant_regime_has_highest_probability(self, client_and_mocks):
        """The dominant regime type should have the highest probability."""
        client, handler, _ = client_and_mocks
        handler.handle.return_value = Ok(MOCK_REGIME_RESULT)

        resp = client.get(
            "/api/v1/regime/current",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        data = resp.json()
        probs = data["regime_probabilities"]
        dominant = data["regime_type"]
        assert probs[dominant] == max(probs.values())


class TestRegimeHistoryEndpoint:
    """GET /api/v1/regime/history tests."""

    def test_returns_history_with_entries(self, client_and_mocks):
        client, _, repo = client_and_mocks
        repo.find_by_date_range.return_value = [
            _make_mock_regime_entity("Bull", 0.85, "2026-03-10T10:00:00+00:00"),
            _make_mock_regime_entity("Sideways", 0.65, "2026-03-05T10:00:00+00:00"),
        ]

        resp = client.get(
            "/api/v1/regime/history?days=90",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["period_days"] == 90
        assert len(data["entries"]) == 2
        assert data["entries"][0]["regime_type"] == "Bull"
        assert "disclaimer" in data

    def test_history_days_over_365_returns_422(self, client_and_mocks):
        client, _, _ = client_and_mocks

        resp = client.get(
            "/api/v1/regime/history?days=400",
            headers={"Authorization": f"Bearer {make_jwt_token()}"},
        )

        assert resp.status_code == 422

    def test_history_no_jwt_returns_401_or_403(self, client_and_mocks):
        client, _, _ = client_and_mocks

        from commercial.api.dependencies import get_current_user
        from commercial.api.main import app

        app.dependency_overrides.pop(get_current_user, None)

        resp = client.get("/api/v1/regime/history?days=30")

        assert resp.status_code in (401, 403)
