"""Tests for Task 1: Config, schemas, and auth infrastructure.

RED phase: These tests verify the core behaviors of ApiSettings,
ApiKeyRepository, UserRepository, schemas, dependencies, and rate limiter.
"""
from __future__ import annotations

import os
import tempfile
import datetime

import pytest


class TestApiSettings:
    """Test ApiSettings loads from env with safe defaults."""

    def test_default_jwt_algorithm(self):
        from commercial.api.config import api_settings

        assert api_settings.JWT_ALGORITHM == "HS256"

    def test_default_token_expire_hours(self):
        from commercial.api.config import api_settings

        assert api_settings.TOKEN_EXPIRE_HOURS == 24

    def test_jwt_secret_key_has_default_for_dev(self):
        from commercial.api.config import api_settings

        assert api_settings.JWT_SECRET_KEY is not None
        assert len(api_settings.JWT_SECRET_KEY) >= 32


class TestSchemas:
    """Test Pydantic schemas are defined with proper fields and DISCLAIMER."""

    def test_disclaimer_constant_exists(self):
        from commercial.api.schemas.common import DISCLAIMER

        assert DISCLAIMER is not None
        assert len(DISCLAIMER) > 0

    def test_error_response_model(self):
        from commercial.api.schemas.common import ErrorResponse

        resp = ErrorResponse(error="test error")
        assert resp.error == "test error"

    def test_quantscore_response_has_disclaimer(self):
        from commercial.api.schemas.score import QuantScoreResponse

        resp = QuantScoreResponse(
            symbol="AAPL",
            composite_score=75.0,
            risk_adjusted_score=70.0,
            safety_passed=True,
        )
        assert resp.disclaimer is not None
        assert len(resp.disclaimer) > 0

    def test_signal_response_has_no_position_sizing(self):
        """SignalResponse must NOT have position sizing fields (legal boundary)."""
        from commercial.api.schemas.signal import SignalResponse

        fields = set(SignalResponse.model_fields.keys())
        forbidden = {"position_size", "margin_of_safety", "stop_loss", "take_profit", "recommendation"}
        assert fields.isdisjoint(forbidden), f"Found forbidden fields: {fields & forbidden}"

    def test_signal_response_has_disclaimer(self):
        from commercial.api.schemas.signal import SignalResponse

        resp = SignalResponse(
            symbol="AAPL",
            direction="BULLISH",
            strength=0.8,
            consensus_count=3,
            methodology_count=4,
        )
        assert resp.disclaimer is not None

    def test_token_response(self):
        from commercial.api.schemas.auth import TokenResponse

        resp = TokenResponse(
            access_token="abc",
            token_type="bearer",
            expires_in=86400,
        )
        assert resp.access_token == "abc"

    def test_schemas_init_reexports_all(self):
        from commercial.api.schemas import (
            QuantScoreResponse,
            TokenResponse,
            ErrorResponse,
            DISCLAIMER,
        )

        assert QuantScoreResponse is not None
        assert TokenResponse is not None


class TestApiKeyRepository:
    """Test SQLite-backed API key CRUD."""

    @pytest.fixture
    def repo_and_user_repo(self, tmp_path):
        from commercial.api.infrastructure.api_key_repo import ApiKeyRepository
        from commercial.api.infrastructure.user_repo import UserRepository

        db_path = str(tmp_path / "test_api_keys.db")
        user_repo = UserRepository(db_path=db_path)
        repo = ApiKeyRepository(db_path=db_path, user_repo=user_repo)
        user_repo.create_user("user-1", tier="free")
        return repo, user_repo

    def test_create_key_returns_id_and_raw_key(self, repo_and_user_repo):
        repo, _ = repo_and_user_repo
        key_id, raw_key = repo.create_key("user-1", "test-key")
        assert key_id is not None
        assert raw_key.startswith("iat_")

    def test_verify_key_returns_user_info(self, repo_and_user_repo):
        repo, _ = repo_and_user_repo
        key_id, raw_key = repo.create_key("user-1", "test-key")
        info = repo.verify_key(raw_key)
        assert info is not None
        assert info["user_id"] == "user-1"
        assert info["tier"] == "free"

    def test_verify_key_returns_none_for_invalid(self, repo_and_user_repo):
        repo, _ = repo_and_user_repo
        assert repo.verify_key("invalid-key-123") is None

    def test_revoke_key_makes_verify_fail(self, repo_and_user_repo):
        repo, _ = repo_and_user_repo
        key_id, raw_key = repo.create_key("user-1", "test-key")
        repo.revoke_key(key_id, "user-1")
        assert repo.verify_key(raw_key) is None

    def test_list_keys_without_raw_material(self, repo_and_user_repo):
        repo, _ = repo_and_user_repo
        repo.create_key("user-1", "key-a")
        repo.create_key("user-1", "key-b")
        keys = repo.list_keys("user-1")
        assert len(keys) == 2
        for k in keys:
            assert "key_hash" not in k
            assert "name" in k


class TestUserRepository:
    """Test SQLite-backed user/tier store."""

    @pytest.fixture
    def user_repo(self, tmp_path):
        from commercial.api.infrastructure.user_repo import UserRepository

        db_path = str(tmp_path / "test_users.db")
        return UserRepository(db_path=db_path)

    def test_create_user_default_tier(self, user_repo):
        user_repo.create_user("user-1")
        user = user_repo.get_by_id("user-1")
        assert user is not None
        assert user["tier"] == "free"

    def test_create_user_custom_tier(self, user_repo):
        user_repo.create_user("user-pro", tier="pro")
        user = user_repo.get_by_id("user-pro")
        assert user["tier"] == "pro"

    def test_get_nonexistent_user(self, user_repo):
        assert user_repo.get_by_id("no-such-user") is None

    def test_update_tier(self, user_repo):
        user_repo.create_user("user-1", tier="free")
        user_repo.update_tier("user-1", "basic")
        user = user_repo.get_by_id("user-1")
        assert user["tier"] == "basic"


class TestGetCurrentUser:
    """Test JWT dependency decodes token and returns user dict."""

    def test_valid_token_returns_user_dict(self):
        import jwt as pyjwt
        from commercial.api.config import api_settings
        from commercial.api.dependencies import get_current_user

        # Set test secret
        api_settings.JWT_SECRET_KEY = "test-secret-key-for-unit-tests-only-32chars!"

        token = pyjwt.encode(
            {
                "sub": "user-1",
                "tier": "pro",
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=1),
            },
            api_settings.JWT_SECRET_KEY,
            algorithm=api_settings.JWT_ALGORITHM,
        )

        # Simulate FastAPI dependency call
        from fastapi.security import HTTPAuthorizationCredentials

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # get_current_user is sync (per RESEARCH pitfall 2)
        result = get_current_user(credentials=creds)
        assert result["user_id"] == "user-1"
        assert result["tier"] == "pro"

    def test_expired_token_raises_401(self):
        import jwt as pyjwt
        from fastapi import HTTPException
        from commercial.api.config import api_settings
        from commercial.api.dependencies import get_current_user

        api_settings.JWT_SECRET_KEY = "test-secret-key-for-unit-tests-only-32chars!"

        token = pyjwt.encode(
            {
                "sub": "user-1",
                "tier": "free",
                "exp": datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(hours=1),
            },
            api_settings.JWT_SECRET_KEY,
            algorithm=api_settings.JWT_ALGORITHM,
        )

        from fastapi.security import HTTPAuthorizationCredentials

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=creds)
        assert exc_info.value.status_code == 401


class TestTierLimits:
    """Test rate limiter tier configuration."""

    def test_tier_limits_mapping(self):
        from commercial.api.middleware.rate_limit import TIER_LIMITS

        assert TIER_LIMITS["free"] == "10/minute"
        assert TIER_LIMITS["basic"] == "30/minute"
        assert TIER_LIMITS["pro"] == "100/minute"
