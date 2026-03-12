"""Tests for tiered rate limiting configuration and wiring."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from tests.unit.conftest_api import (
    make_jwt_token,
    TEST_JWT_SECRET,
    TEST_JWT_ALGORITHM,
)


class TestTierLimitsConfig:
    """Test TIER_LIMITS dict has correct values."""

    def test_free_tier_limit(self):
        from commercial.api.middleware.rate_limit import TIER_LIMITS

        assert TIER_LIMITS["free"] == "10/minute"

    def test_basic_tier_limit(self):
        from commercial.api.middleware.rate_limit import TIER_LIMITS

        assert TIER_LIMITS["basic"] == "30/minute"

    def test_pro_tier_limit(self):
        from commercial.api.middleware.rate_limit import TIER_LIMITS

        assert TIER_LIMITS["pro"] == "100/minute"

    def test_all_tiers_present(self):
        from commercial.api.middleware.rate_limit import TIER_LIMITS

        assert set(TIER_LIMITS.keys()) == {"free", "basic", "pro"}


class TestTierKeyFunc:
    """Test _tier_key_func extracts user identity from JWT."""

    def test_extracts_user_id_from_valid_jwt(self):
        """Key function returns user_id from valid JWT."""
        import commercial.api.config as config_mod

        config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
        config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

        from commercial.api.middleware.rate_limit import _tier_key_func

        token = make_jwt_token(user_id="user-123", tier="pro")
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}
        request.client.host = "127.0.0.1"

        result = _tier_key_func(request)
        assert result == "user-123"

    def test_falls_back_to_remote_address_without_jwt(self):
        """Key function falls back to IP when no JWT present."""
        from commercial.api.middleware.rate_limit import _tier_key_func

        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.1"

        result = _tier_key_func(request)
        # Falls back to remote address
        assert result == "192.168.1.1"


class TestGetTierLimit:
    """Test get_tier_limit reads tier from JWT."""

    def test_returns_pro_limit_for_pro_user(self):
        import commercial.api.config as config_mod

        config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
        config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

        from commercial.api.middleware.rate_limit import get_tier_limit

        token = make_jwt_token(user_id="user-pro", tier="pro")
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}

        result = get_tier_limit(request)
        assert result == "100/minute"

    def test_returns_free_limit_for_free_user(self):
        import commercial.api.config as config_mod

        config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
        config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

        from commercial.api.middleware.rate_limit import get_tier_limit

        token = make_jwt_token(user_id="user-free", tier="free")
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}

        result = get_tier_limit(request)
        assert result == "10/minute"

    def test_returns_free_limit_without_auth(self):
        from commercial.api.middleware.rate_limit import get_tier_limit

        request = MagicMock()
        request.headers = {}

        result = get_tier_limit(request)
        assert result == "10/minute"


class TestRateLimiterWiring:
    """Test rate limiter is wired to FastAPI app."""

    def test_app_has_limiter_state(self):
        from commercial.api.main import app

        assert hasattr(app.state, "limiter")
        assert app.state.limiter is not None

    def test_health_endpoint_not_rate_limited(self):
        """Health endpoint works without auth (sanity check)."""
        import commercial.api.config as config_mod

        config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET

        from commercial.api.main import app

        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
