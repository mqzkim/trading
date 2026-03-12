"""Tests for JWT auth flow -- token exchange and protected endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest_api import (
    make_jwt_token,
    make_expired_jwt_token,
    TEST_JWT_SECRET,
    TEST_JWT_ALGORITHM,
)


@pytest.fixture
def api_client():
    """Create TestClient with patched settings."""
    import commercial.api.config as config_mod

    config_mod.api_settings.JWT_SECRET_KEY = TEST_JWT_SECRET
    config_mod.api_settings.JWT_ALGORITHM = TEST_JWT_ALGORITHM

    from commercial.api.main import app

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def user_and_key(tmp_path):
    """Create a test user and API key, wire dependency override."""
    from commercial.api.infrastructure.user_repo import UserRepository
    from commercial.api.infrastructure.api_key_repo import ApiKeyRepository
    from commercial.api.routers.auth import _get_api_key_repo
    from commercial.api.main import app

    db_path = str(tmp_path / "test_auth.db")
    user_repo = UserRepository(db_path=db_path)
    api_key_repo = ApiKeyRepository(db_path=db_path, user_repo=user_repo)
    user_repo.create_user("test-user-1", tier="free")
    key_id, raw_key = api_key_repo.create_key("test-user-1", "test-key")

    app.dependency_overrides[_get_api_key_repo] = lambda: api_key_repo

    return {
        "user_id": "test-user-1",
        "key_id": key_id,
        "raw_key": raw_key,
        "user_repo": user_repo,
        "api_key_repo": api_key_repo,
    }


class TestTokenExchange:
    """POST /api/v1/auth/token with API key."""

    def test_valid_api_key_returns_jwt(self, api_client, user_and_key):
        """Valid API key in x-api-key header returns 200 + JWT."""
        resp = api_client.post(
            "/api/v1/auth/token",
            headers={"x-api-key": user_and_key["raw_key"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400

    def test_invalid_api_key_returns_401(self, api_client, user_and_key):
        """Invalid API key returns 401."""
        resp = api_client.post(
            "/api/v1/auth/token",
            headers={"x-api-key": "invalid-key-abc"},
        )
        assert resp.status_code == 401


class TestProtectedEndpoints:
    """Auth enforcement on protected endpoints."""

    def test_no_auth_header_returns_401_or_403(self, api_client):
        """Request without Authorization header is rejected."""
        resp = api_client.get("/api/v1/auth/keys")
        # HTTPBearer returns 401 (unauthenticated) or 403 (forbidden) depending on version
        assert resp.status_code in (401, 403)

    def test_expired_token_returns_401(self, api_client):
        """Expired JWT returns 401."""
        token = make_expired_jwt_token()
        resp = api_client.get(
            "/api/v1/auth/keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_valid_token_allows_access(self, api_client, user_and_key):
        """Valid JWT allows access to protected endpoints."""
        token = make_jwt_token(user_id="test-user-1", tier="free")
        resp = api_client.get(
            "/api/v1/auth/keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
