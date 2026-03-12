"""Auth router -- JWT token exchange and API key management.

POST /api/v1/auth/token  -- exchange API key for JWT
POST /api/v1/auth/keys   -- create new API key (JWT required)
GET  /api/v1/auth/keys   -- list user's API keys (JWT required)
DELETE /api/v1/auth/keys/{key_id} -- revoke API key (JWT required)
"""
from __future__ import annotations

import datetime

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from commercial.api.config import api_settings
from commercial.api.dependencies import get_current_user
from commercial.api.infrastructure.api_key_repo import ApiKeyRepository
from commercial.api.infrastructure.user_repo import UserRepository
from commercial.api.schemas.auth import (
    APIKeyCreate,
    APIKeyListItem,
    APIKeyListResponse,
    APIKeyResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_api_key_repo() -> ApiKeyRepository:
    """Default API key repo factory. Patched in tests."""
    return ApiKeyRepository()


@router.post("/token", response_model=TokenResponse)
def exchange_token(
    x_api_key: str = Header(..., alias="x-api-key"),
    repo: ApiKeyRepository = Depends(_get_api_key_repo),
):
    """Exchange API key for JWT access token."""
    user_info = repo.verify_key(x_api_key)
    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        hours=api_settings.TOKEN_EXPIRE_HOURS
    )
    payload = {
        "sub": user_info["user_id"],
        "tier": user_info["tier"],
        "exp": expire,
    }
    access_token = jwt.encode(
        payload, api_settings.JWT_SECRET_KEY, algorithm=api_settings.JWT_ALGORITHM
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=api_settings.TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post("/keys", response_model=APIKeyResponse)
def create_api_key(
    body: APIKeyCreate,
    user: dict = Depends(get_current_user),
    repo: ApiKeyRepository = Depends(_get_api_key_repo),
):
    """Create a new API key. Raw key is shown once."""
    key_id, raw_key = repo.create_key(user["user_id"], body.name)
    return APIKeyResponse(key_id=key_id, raw_key=raw_key, name=body.name)


@router.get("/keys", response_model=APIKeyListResponse)
def list_api_keys(
    user: dict = Depends(get_current_user),
    repo: ApiKeyRepository = Depends(_get_api_key_repo),
):
    """List user's API keys (without raw key material)."""
    keys = repo.list_keys(user["user_id"])
    return APIKeyListResponse(
        keys=[APIKeyListItem(**k) for k in keys],
        total=len(keys),
    )


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: str,
    user: dict = Depends(get_current_user),
    repo: ApiKeyRepository = Depends(_get_api_key_repo),
):
    """Revoke an API key. Returns 204 on success, 404 if not found/owned."""
    revoked = repo.revoke_key(key_id, user["user_id"])
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found or not owned by user",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
