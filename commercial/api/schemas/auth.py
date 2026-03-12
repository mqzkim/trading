"""Authentication schemas."""
from __future__ import annotations

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response for POST /api/v1/auth/token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class APIKeyCreate(BaseModel):
    """Request body for POST /api/v1/auth/keys."""

    name: str


class APIKeyResponse(BaseModel):
    """Response for API key creation (raw key shown once)."""

    key_id: str
    raw_key: str
    name: str


class APIKeyListItem(BaseModel):
    """Single API key in list response (no raw key material)."""

    key_id: str
    name: str
    created_at: str
    is_active: bool


class APIKeyListResponse(BaseModel):
    """Response for GET /api/v1/auth/keys."""

    keys: list[APIKeyListItem]
    total: int
