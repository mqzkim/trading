# Phase 11: Commercial FastAPI REST API - Research

**Researched:** 2026-03-13
**Domain:** FastAPI REST API with JWT auth, tiered rate limiting, API key management
**Confidence:** HIGH

## Summary

Phase 11 builds the commercial REST API that exposes QuantScore, RegimeRadar, and SignalFusion to external users. The project already has a partially-implemented `commercial/api/` directory with legacy routes (importing from `core/`) and two DDD-based v1 routers (scoring, regime). The existing code uses a simple `x-api-key` header check against a single env variable -- this must be replaced with proper JWT authentication with tiered user management.

The existing DDD handlers in `src/scoring/`, `src/regime/`, and `src/signals/` already return structured result dicts via `Ok(result)` / `Err(error)` patterns. The API layer's job is to wrap these handlers with proper HTTP concerns: authentication, rate limiting, response schemas with disclaimers, and legal boundary enforcement (information only -- never position sizing or buy/sell recommendations).

**Primary recommendation:** Restructure `commercial/api/` to use a clean `/api/v1/` prefix, replace the legacy `core/` imports with DDD handler calls via `bootstrap()`, implement JWT auth with PyJWT, add tiered rate limiting with slowapi, and build API key CRUD endpoints backed by SQLite.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | QuantScore API endpoint (composite score query) | Existing `ScoreSymbolHandler.handle()` returns full score breakdown. Wrap with v1 endpoint schema including sub-scores and disclaimer. |
| API-02 | RegimeRadar API endpoint (current regime + history) | Existing `DetectRegimeHandler` + `SqliteRegimeRepository.find_latest()` / `find_by_date_range()`. Two endpoints: `/regime/current` and `/regime/history`. |
| API-03 | SignalFusion API endpoint (consensus signal query) | Existing `GenerateSignalHandler.handle()` returns direction, strength, methodology votes. Filter out position sizing fields, add disclaimer. |
| API-04 | JWT-based tier authentication (free/basic/pro) | PyJWT 2.11.0 for token creation/verification. Store user tier in JWT claims. FastAPI dependency injection for auth. |
| API-05 | Tiered rate limiting (slowapi) | slowapi 0.1.9 with custom key function. Dynamic limits: free=10/min, basic=30/min, pro=100/min. |
| API-06 | API key management and disclaimer inclusion | SQLite-backed API key store. CRUD endpoints: create, list, revoke. All responses include legal disclaimer field. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.104 (already in pyproject.toml) | REST framework | Already a project dependency. Async, OpenAPI auto-docs, dependency injection. |
| Uvicorn | >=0.24 (already in pyproject.toml) | ASGI server | Already a project dependency. Standard FastAPI server. |
| PyJWT | 2.11.0 | JWT token creation/verification | Official FastAPI docs recommend PyJWT over python-jose. Lightweight, actively maintained. |
| slowapi | 0.1.9 | Rate limiting | Standard FastAPI rate limiter. Decorator-based, supports custom key functions for tiered limits. |
| Pydantic | >=2.0 (already in pyproject.toml) | Request/response schemas | Already a project dependency. FastAPI's native validation layer. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| passlib[bcrypt] | >=1.7 | Password hashing for API key secrets | Hashing API key secrets before storage |
| python-multipart | >=0.0.9 | Form data parsing | Required by FastAPI for OAuth2PasswordRequestForm |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyJWT | python-jose | python-jose is heavier, less maintained; PyJWT is FastAPI's official recommendation |
| slowapi | fastapi-limiter | fastapi-limiter requires Redis; slowapi works with in-memory (sufficient for single-instance) |
| SQLite API key store | Redis | Redis adds infra dependency; SQLite is already used throughout the project |

**Installation:**
```bash
pip install PyJWT slowapi "passlib[bcrypt]"
```

## Architecture Patterns

### Recommended Project Structure
```
commercial/
  api/
    __init__.py
    main.py                  # FastAPI app, middleware, exception handlers
    config.py                # API-specific settings (JWT secret, rate limits)
    dependencies.py          # DI: auth, rate limiter, bootstrap context
    schemas/
      __init__.py
      common.py              # DISCLAIMER, ErrorResponse, PaginatedResponse
      score.py               # QuantScoreResponse, ScoreBreakdown
      regime.py              # RegimeResponse, RegimeHistoryResponse
      signal.py              # SignalResponse, MethodologyVote
      auth.py                # TokenResponse, APIKeyResponse, APIKeyCreate
    routers/
      __init__.py
      v1_router.py           # Aggregated /api/v1 router
      quantscore.py          # GET /api/v1/quantscore/{ticker}
      regime.py              # GET /api/v1/regime/current, /regime/history
      signals.py             # GET /api/v1/signals/{ticker}
      auth.py                # POST /api/v1/auth/token, API key CRUD
    middleware/
      __init__.py
      rate_limit.py          # slowapi setup + tiered key function
      disclaimer.py          # Response middleware adding disclaimer
    infrastructure/
      __init__.py
      api_key_repo.py        # SQLite API key CRUD
      user_repo.py           # SQLite user/tier store (minimal)
```

### Pattern 1: DDD Handler Consumption via Bootstrap
**What:** API endpoints call DDD handlers through the bootstrap context, never importing from `core/` directly.
**When to use:** Every data endpoint (score, regime, signal).
**Example:**
```python
# commercial/api/dependencies.py
from functools import lru_cache
from src.bootstrap import bootstrap

@lru_cache(maxsize=1)
def get_context() -> dict:
    """Singleton bootstrap context for the API server."""
    return bootstrap()

def get_score_handler():
    return get_context()["score_handler"]

def get_regime_handler():
    return get_context()["regime_handler"]

def get_signal_handler():
    return get_context()["signal_handler"]
```

### Pattern 2: JWT Auth Dependency
**What:** FastAPI dependency that extracts and validates JWT, returns user info with tier.
**When to use:** All protected endpoints.
**Example:**
```python
# commercial/api/dependencies.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
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
```

### Pattern 3: Tiered Rate Limiting
**What:** slowapi with custom key function that reads user tier from JWT and applies different limits.
**When to use:** All data endpoints.
**Example:**
```python
# commercial/api/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

TIER_LIMITS = {
    "free": "10/minute",
    "basic": "30/minute",
    "pro": "100/minute",
}

def _tier_key_func(request):
    """Extract user ID from JWT for rate limiting key."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(
                auth[7:], settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload.get("sub", get_remote_address(request))
        except jwt.InvalidTokenError:
            pass
    return get_remote_address(request)

limiter = Limiter(key_func=_tier_key_func)

# In endpoint:
@router.get("/quantscore/{ticker}")
@limiter.limit(lambda: "100/minute")  # default; overridden dynamically
async def get_quantscore(request: Request, ticker: str, ...):
    ...
```

### Pattern 4: Legal Boundary Enforcement
**What:** Signal responses NEVER include position sizing, buy/sell recommendations, or stop-loss prices.
**When to use:** SignalFusion endpoint specifically.
**Example:**
```python
# The handler returns methodology_directions, reasoning_trace, etc.
# API schema intentionally EXCLUDES:
#   - Any "recommendation" or "action" field
#   - Position size or capital allocation
#   - Stop-loss or take-profit prices
# Only exposes: direction (informational), strength, consensus_count, methodology_scores
```

### Anti-Patterns to Avoid
- **Importing from core/ in API endpoints:** All legacy routes currently do this. Must migrate to DDD handler calls.
- **Single hardcoded API key:** Current `verify_api_key` uses `os.getenv("COMMERCIAL_API_KEY")`. Replace with JWT + API key CRUD.
- **Duplicate Pydantic models:** Current code has both `models.py` and `schemas.py` with overlapping definitions. Consolidate into `schemas/` directory.
- **Exposing personal-use fields:** Signal response must not leak position sizing or explicit buy/sell recommendations (legal boundary per CLAUDE.md strategy doc).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT token creation/verification | Custom token encoding | PyJWT `jwt.encode()` / `jwt.decode()` | Edge cases: timing attacks, algorithm confusion, expiry validation |
| Rate limiting | Custom counter middleware | slowapi `@limiter.limit()` | Sliding windows, distributed backends, proper 429 headers |
| Password/key hashing | Raw hashlib | passlib `CryptContext` | Salt management, algorithm upgrades, timing-safe comparison |
| OpenAPI documentation | Manual swagger | FastAPI auto-docs (built-in) | Automatic from Pydantic models and type hints |
| CORS handling | Custom headers | `CORSMiddleware` (already present) | Preflight handling, credential support |

**Key insight:** The auth + rate limiting combination is deceptively complex. JWT verification must be timing-safe, rate limiting must handle concurrent requests atomically, and API key hashing must use proper bcrypt -- all solved by the standard libraries.

## Common Pitfalls

### Pitfall 1: Duplicate Bootstrap Initialization
**What goes wrong:** Each request creates a new `bootstrap()` context, opening new DB connections and re-wiring handlers.
**Why it happens:** Calling `bootstrap()` inside each dependency function.
**How to avoid:** Use `@lru_cache(maxsize=1)` or module-level singleton for the context dict. Bootstrap once at app startup.
**Warning signs:** Slow response times, "too many open files" errors, SQLite locking issues.

### Pitfall 2: Blocking I/O in Async Endpoints
**What goes wrong:** DDD handlers use synchronous SQLite calls. Calling them directly in `async def` endpoints blocks the event loop.
**Why it happens:** Mixing sync handlers with async FastAPI endpoints.
**How to avoid:** Either use `def` (sync) endpoints (FastAPI runs them in threadpool automatically) or wrap handler calls in `asyncio.to_thread()`. For this project, sync `def` endpoints are simpler and correct since all handlers are synchronous.
**Warning signs:** High latency under concurrent requests, event loop warnings.

### Pitfall 3: Leaking Personal-Use Fields in Commercial API
**What goes wrong:** Signal handler returns `margin_of_safety`, `reasoning_trace` with "BUY" language, strategy weights -- these constitute investment advice.
**Why it happens:** Directly serializing handler result dicts to response.
**How to avoid:** Define explicit Pydantic response schemas that whitelist only information-safe fields. Never pass raw handler dicts to response.
**Warning signs:** Legal liability, "this looks like investment advice" in responses.

### Pitfall 4: JWT Secret Key Management
**What goes wrong:** Hardcoded or weak JWT secret allows token forgery.
**Why it happens:** Using example keys from tutorials.
**How to avoid:** Generate with `openssl rand -hex 32`, store in `.env`, load via pydantic-settings. Never commit to git.
**Warning signs:** `JWT_SECRET_KEY` contains "secret" or "example" or is shorter than 32 chars.

### Pitfall 5: Rate Limiter State Loss on Restart
**What goes wrong:** In-memory rate limiter resets all counters when server restarts.
**Why it happens:** Default slowapi uses in-memory storage.
**How to avoid:** For Phase 11 (single instance), in-memory is acceptable. Document that Redis backend (SCALE-01) is deferred to v1.2. Add a comment noting the limitation.
**Warning signs:** Users bypass rate limits by waiting for server restart.

### Pitfall 6: Legacy Route Conflicts
**What goes wrong:** Existing legacy routes (`/score/{symbol}`, `/regime`, `/signal/{symbol}`) conflict with new v1 routes.
**Why it happens:** Both sets of routes mounted on the same app.
**How to avoid:** Remove legacy routes entirely or prefix them with `/legacy/`. New routes use `/api/v1/` prefix exclusively.
**Warning signs:** 405 Method Not Allowed, wrong handler being called.

## Code Examples

### QuantScore Endpoint (API-01)
```python
# commercial/api/routers/quantscore.py
from fastapi import APIRouter, Depends, HTTPException, Request
from src.scoring.application.commands import ScoreSymbolCommand
from src.shared.domain import Err
from ..dependencies import get_current_user, get_score_handler
from ..schemas.score import QuantScoreResponse
from ..middleware.rate_limit import limiter

router = APIRouter(prefix="/quantscore", tags=["QuantScore"])

@router.get("/{ticker}", response_model=QuantScoreResponse)
@limiter.limit("10/minute")  # dynamic override via tier
def get_quantscore(
    request: Request,
    ticker: str,
    strategy: str = "swing",
    user: dict = Depends(get_current_user),
    handler=Depends(get_score_handler),
):
    result = handler.handle(ScoreSymbolCommand(symbol=ticker, strategy=strategy))
    if isinstance(result, Err):
        raise HTTPException(status_code=422, detail=str(result.error))
    data = result.value
    return QuantScoreResponse(
        symbol=data["symbol"],
        composite_score=data["composite_score"],
        risk_adjusted_score=data["risk_adjusted_score"],
        safety_passed=data["safety_passed"],
        fundamental_score=data.get("fundamental_score"),
        technical_score=data.get("technical_score"),
        sentiment_score=data.get("sentiment_score"),
        sub_scores=data.get("technical_sub_scores"),
    )
```

### Regime History Endpoint (API-02)
```python
# commercial/api/routers/regime.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from ..dependencies import get_current_user
from ..schemas.regime import RegimeCurrentResponse, RegimeHistoryResponse

router = APIRouter(prefix="/regime", tags=["RegimeRadar"])

@router.get("/current", response_model=RegimeCurrentResponse)
def get_current_regime(
    request: Request,
    user: dict = Depends(get_current_user),
):
    from src.regime.infrastructure import SqliteRegimeRepository
    repo = SqliteRegimeRepository()
    latest = repo.find_latest()
    if latest is None:
        raise HTTPException(status_code=404, detail="No regime data available")
    return RegimeCurrentResponse(
        regime_type=latest.regime_type.value,
        confidence=latest.confidence,
        is_confirmed=latest.is_confirmed,
        confirmed_days=latest.confirmed_days,
        vix=latest.vix.value,
        adx=latest.trend.adx,
        yield_spread=latest.yield_curve.spread,
        detected_at=latest.detected_at.isoformat(),
    )

@router.get("/history", response_model=RegimeHistoryResponse)
def get_regime_history(
    request: Request,
    days: int = Query(default=90, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    from src.regime.infrastructure import SqliteRegimeRepository
    repo = SqliteRegimeRepository()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    regimes = repo.find_by_date_range(start, end)
    return RegimeHistoryResponse(
        entries=[...],  # Map each MarketRegime to response schema
        total=len(regimes),
        period_days=days,
    )
```

### API Key Management (API-06)
```python
# commercial/api/infrastructure/api_key_repo.py
import secrets
import sqlite3
from datetime import datetime, timezone
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ApiKeyRepository:
    """SQLite-backed API key store."""

    def create_key(self, user_id: str, name: str) -> tuple[str, str]:
        """Create a new API key. Returns (key_id, raw_key).
        raw_key is shown once, then only the hash is stored."""
        key_id = secrets.token_urlsafe(8)
        raw_key = f"iat_{secrets.token_urlsafe(32)}"
        hashed = pwd_context.hash(raw_key)
        # Store key_id, hashed key, user_id, name, created_at, is_active
        ...
        return key_id, raw_key

    def verify_key(self, raw_key: str) -> dict | None:
        """Verify API key, return user info if valid."""
        # Look up by prefix, verify hash
        ...

    def revoke_key(self, key_id: str, user_id: str) -> bool:
        """Revoke (soft-delete) an API key."""
        ...

    def list_keys(self, user_id: str) -> list[dict]:
        """List all API keys for a user (without raw keys)."""
        ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT (official FastAPI recommendation) | FastAPI docs updated 2024+ | Simpler API, lighter dependency |
| Single API key env var | JWT + API key CRUD | Industry standard | Proper multi-user, tiered access |
| Legacy core/ imports in routes | DDD handler calls via bootstrap() | This project v1.1 Phase 5+ | Clean architecture, testability |
| Duplicate models.py/schemas.py | Consolidated schemas/ directory | This phase | Single source of truth |

**Deprecated/outdated:**
- `python-jose`: FastAPI official docs no longer recommend it. Use PyJWT instead.
- `commercial/api/routes/` (legacy): These import from `core/` directly. Must be replaced with DDD handler-based routes.
- `commercial/api/models.py` + `commercial/api/schemas.py`: Overlapping response models. Consolidate.

## Open Questions

1. **User registration flow**
   - What we know: JWT requires user records with tier info. API keys need user_id foreign key.
   - What's unclear: How do users register? Self-service signup? Manual onboarding?
   - Recommendation: Implement minimal SQLite user store with manual creation (admin endpoint). Self-service signup deferred to v1.2.

2. **Token refresh mechanism**
   - What we know: JWTs expire. Users need a way to get new tokens.
   - What's unclear: Refresh token rotation? Token lifetime?
   - Recommendation: 24-hour access tokens. Token obtained via API key exchange (POST /api/v1/auth/token with API key). No refresh tokens needed -- re-exchange API key.

3. **Rate limit response headers**
   - What we know: Standard headers are X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset.
   - What's unclear: slowapi may or may not add these automatically.
   - Recommendation: Verify slowapi header behavior in testing. Add custom middleware if needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ (already configured) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_api_v1.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | GET /api/v1/quantscore/{ticker} returns score + disclaimer | unit | `pytest tests/unit/test_api_v1_quantscore.py -x` | No -- Wave 0 |
| API-02 | GET /api/v1/regime/current and /history return regime data | unit | `pytest tests/unit/test_api_v1_regime.py -x` | No -- Wave 0 |
| API-03 | GET /api/v1/signals/{ticker} returns consensus (no position sizing) | unit | `pytest tests/unit/test_api_v1_signals.py -x` | No -- Wave 0 |
| API-04 | Requests without valid JWT rejected with 401 | unit | `pytest tests/unit/test_api_v1_auth.py -x` | No -- Wave 0 |
| API-05 | Free-tier rate limited more aggressively than pro-tier | unit | `pytest tests/unit/test_api_v1_rate_limit.py -x` | No -- Wave 0 |
| API-06 | API key create/list/revoke endpoints work | unit | `pytest tests/unit/test_api_v1_apikeys.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_api_v1*.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_api_v1_quantscore.py` -- covers API-01
- [ ] `tests/unit/test_api_v1_regime.py` -- covers API-02
- [ ] `tests/unit/test_api_v1_signals.py` -- covers API-03
- [ ] `tests/unit/test_api_v1_auth.py` -- covers API-04
- [ ] `tests/unit/test_api_v1_rate_limit.py` -- covers API-05
- [ ] `tests/unit/test_api_v1_apikeys.py` -- covers API-06
- [ ] `tests/unit/conftest_api.py` -- shared fixtures (TestClient, mock bootstrap, mock JWT)
- [ ] Install: `pip install PyJWT slowapi "passlib[bcrypt]"` -- new dependencies

## Sources

### Primary (HIGH confidence)
- [FastAPI Official Docs - OAuth2 JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) - JWT implementation pattern, PyJWT recommendation
- [FastAPI Official Docs - Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) - Router structure, prefix pattern
- [PyJWT 2.11.0 Documentation](https://pyjwt.readthedocs.io/en/stable/) - Current version, API reference
- Project source code: `src/bootstrap.py`, `src/scoring/application/handlers.py`, `src/regime/application/handlers.py`, `src/signals/application/handlers.py` - Handler interfaces and return types
- Project source code: `commercial/api/` - Existing API structure, legacy routes, current schemas

### Secondary (MEDIUM confidence)
- [slowapi GitHub](https://github.com/laurentS/slowapi) - Rate limiting library, version 0.1.9
- [slowapi Documentation](https://slowapi.readthedocs.io/) - Custom key functions, storage backends
- [API Key Management Best Practices](https://oneuptime.com/blog/post/2026-02-20-api-key-management-best-practices/view) - Key rotation, hashing patterns

### Tertiary (LOW confidence)
- slowapi dynamic tiered rate limiting -- documented in issues/examples but not extensively tested at scale. May need custom middleware if slowapi's dynamic limit support is insufficient.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - FastAPI/PyJWT/slowapi are well-established, versions verified
- Architecture: HIGH - DDD handler pattern already proven in 10 phases, bootstrap() singleton is standard
- Pitfalls: HIGH - Based on direct code review of existing codebase and known FastAPI patterns
- Auth/rate limiting: MEDIUM - slowapi tiered dynamic limits have limited documentation, may need custom implementation

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable ecosystem, 30 days)
