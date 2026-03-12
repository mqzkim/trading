"""Shared fixtures for commercial API tests."""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi.testclient import TestClient


# JWT test configuration
TEST_JWT_SECRET = "test-secret-key-for-unit-tests-only-32chars!"
TEST_JWT_ALGORITHM = "HS256"


def make_jwt_token(
    user_id: str = "test-user-1",
    tier: str = "free",
    expires_delta_hours: int = 24,
    secret: str = TEST_JWT_SECRET,
) -> str:
    """Generate a valid JWT for tests."""
    payload = {
        "sub": user_id,
        "tier": tier,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=expires_delta_hours),
    }
    return jwt.encode(payload, secret, algorithm=TEST_JWT_ALGORITHM)


def make_expired_jwt_token(
    user_id: str = "test-user-1",
    tier: str = "free",
    secret: str = TEST_JWT_SECRET,
) -> str:
    """Generate an expired JWT for tests."""
    payload = {
        "sub": user_id,
        "tier": tier,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm=TEST_JWT_ALGORITHM)


def mock_bootstrap_context() -> dict:
    """Return dict with mock handlers mimicking bootstrap() output."""
    mock_score_handler = MagicMock()
    mock_regime_handler = MagicMock()
    mock_signal_handler = MagicMock()
    return {
        "score_handler": mock_score_handler,
        "regime_handler": mock_regime_handler,
        "signal_handler": mock_signal_handler,
    }


@pytest.fixture
def api_client():
    """Create TestClient with mocked bootstrap and test JWT settings."""
    # Patch settings before importing app
    import commercial.api.config as config_mod

    config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
    config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

    from commercial.api.main import app

    return TestClient(app)
