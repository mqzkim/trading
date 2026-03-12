"""Tests for API key management endpoints (CRUD)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest_api import (
    make_jwt_token,
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
def repos(tmp_path):
    """Create fresh repos and wire dependency override."""
    from commercial.api.infrastructure.user_repo import UserRepository
    from commercial.api.infrastructure.api_key_repo import ApiKeyRepository
    from commercial.api.routers.auth import _get_api_key_repo
    from commercial.api.main import app

    db_path = str(tmp_path / "test_apikeys.db")
    user_repo = UserRepository(db_path=db_path)
    api_key_repo = ApiKeyRepository(db_path=db_path, user_repo=user_repo)
    user_repo.create_user("test-user-1", tier="free")
    user_repo.create_user("test-user-2", tier="pro")

    app.dependency_overrides[_get_api_key_repo] = lambda: api_key_repo

    return {"api_key_repo": api_key_repo, "user_repo": user_repo}


class TestCreateApiKey:
    """POST /api/v1/auth/keys -- create API key."""

    def test_create_key_returns_id_and_raw_key(self, api_client, repos):
        """Create key returns key_id and raw_key."""
        token = make_jwt_token(user_id="test-user-1", tier="free")
        resp = api_client.post(
            "/api/v1/auth/keys",
            json={"name": "my-test-key"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "key_id" in data
        assert "raw_key" in data
        assert data["raw_key"].startswith("iat_")


class TestListApiKeys:
    """GET /api/v1/auth/keys -- list keys."""

    def test_list_keys_without_raw_material(self, api_client, repos):
        """List keys returns key info without raw key material."""
        repos["api_key_repo"].create_key("test-user-1", "key-a")
        repos["api_key_repo"].create_key("test-user-1", "key-b")

        token = make_jwt_token(user_id="test-user-1", tier="free")
        resp = api_client.get(
            "/api/v1/auth/keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for key in data["keys"]:
            assert "raw_key" not in key
            assert "key_hash" not in key
            assert "name" in key


class TestRevokeApiKey:
    """DELETE /api/v1/auth/keys/{key_id} -- revoke key."""

    def test_revoke_own_key(self, api_client, repos):
        """Revoke own key returns 204."""
        key_id, _ = repos["api_key_repo"].create_key("test-user-1", "to-revoke")
        token = make_jwt_token(user_id="test-user-1", tier="free")
        resp = api_client.delete(
            f"/api/v1/auth/keys/{key_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    def test_revoke_other_user_key_returns_404(self, api_client, repos):
        """Revoke key owned by another user returns 404."""
        key_id, _ = repos["api_key_repo"].create_key("test-user-2", "other-key")
        token = make_jwt_token(user_id="test-user-1", tier="free")
        resp = api_client.delete(
            f"/api/v1/auth/keys/{key_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_revoked_key_fails_token_exchange(self, api_client, repos):
        """Revoked key no longer works for token exchange."""
        key_id, raw_key = repos["api_key_repo"].create_key("test-user-1", "temp-key")
        repos["api_key_repo"].revoke_key(key_id, "test-user-1")

        resp = api_client.post(
            "/api/v1/auth/token",
            headers={"x-api-key": raw_key},
        )
        assert resp.status_code == 401
