"""Tiered rate limiting with slowapi.

Uses JWT claims to determine per-user rate limit tier.
In-memory storage is acceptable for single-instance deployment.
TODO: Switch to Redis backend for multi-instance (SCALE-01, deferred to v1.2).
"""
from __future__ import annotations

import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from commercial.api.config import api_settings

TIER_LIMITS: dict[str, str] = {
    "free": "10/minute",
    "basic": "30/minute",
    "pro": "100/minute",
}


def _tier_key_func(request: Request) -> str:
    """Extract user ID from JWT for per-user rate tracking.

    Also populates _user_tier_cache so get_tier_limit() can look up the tier.
    Falls back to remote address for unauthenticated requests.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(
                auth[7:],
                api_settings.JWT_SECRET_KEY,
                algorithms=[api_settings.JWT_ALGORITHM],
            )
            user_id = payload.get("sub", get_remote_address(request))
            tier = payload.get("tier", "free")
            _user_tier_cache[user_id] = tier
            return user_id
        except jwt.InvalidTokenError:
            pass
    return get_remote_address(request)


def get_tier_limit(key: str) -> str:
    """Dynamic limit function for slowapi @limiter.limit() decorator.

    Receives the rate-limit key (user_id) from _tier_key_func.
    Looks up the user's tier from the stored mapping.
    """
    tier = _user_tier_cache.get(key, "free")
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


# Lightweight cache: maps user_id -> tier string (populated by _tier_key_func)
_user_tier_cache: dict[str, str] = {}


limiter = Limiter(key_func=_tier_key_func)
