"""API dependencies -- auth, bootstrap context, handler injection.

Uses sync `def` endpoints (not async) since all DDD handlers are synchronous.
FastAPI runs sync dependencies in a threadpool automatically.
"""
from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import api_settings

security = HTTPBearer()


@lru_cache(maxsize=1)
def get_context() -> dict:
    """Singleton bootstrap context for the API server.

    Uses lru_cache to ensure bootstrap() is called exactly once.
    """
    from src.bootstrap import bootstrap

    return bootstrap()


def get_score_handler():
    """Extract score handler from bootstrap context."""
    return get_context()["score_handler"]


def get_regime_handler():
    """Extract regime handler from bootstrap context."""
    return get_context()["regime_handler"]


def get_signal_handler():
    """Extract signal handler from bootstrap context."""
    return get_context()["signal_handler"]


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Decode JWT and return user info dict.

    Returns: {"user_id": str, "tier": str}
    Raises: HTTPException 401 on missing/expired/invalid token.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            api_settings.JWT_SECRET_KEY,
            algorithms=[api_settings.JWT_ALGORITHM],
        )
        return {
            "user_id": payload["sub"],
            "tier": payload.get("tier", "free"),
        }
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
