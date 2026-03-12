# Technology Stack -- v1.1 Additions

**Project:** Intrinsic Alpha Trader
**Researched:** 2026-03-12
**Scope:** NEW dependencies only for v1.1 capabilities
**Overall confidence:** HIGH

## Existing Stack (DO NOT re-add)

These are already installed and working. Listed for reference -- skip when reading dependency recommendations below.

| Already Have | Version Installed | Used By |
|-------------|-------------------|---------|
| pandas | 3.0.1 | All data processing |
| numpy | 2.4.3 | Numerical computation |
| yfinance | 1.2.0 | US market OHLCV + fundamentals |
| duckdb | 1.5.0 | Analytical database |
| SQLite | stdlib | Operational database |
| alpaca-py | 0.43.2 | US broker + market data |
| FastAPI | 0.135.1 | Commercial API (already in deps) |
| uvicorn | 0.41.0 | ASGI server (already in deps) |
| httpx | 0.28.1 | HTTP client (already in deps) |
| pydantic | 2.12.5 | Data models |
| pydantic-settings | 2.13.1 | Configuration |
| typer | 0.24.1 | CLI |
| rich | 14.3.3 | Terminal formatting |
| edgartools | 5.23.0 | SEC EDGAR |
| aiohttp | 3.13.3 | Async HTTP |
| pytest | 9.0.2 | Testing |
| mypy | 1.19.1 | Type checking |
| ruff | 0.15.5 | Linting + formatting |

**NOTE:** The existing `core/data/indicators.py` already implements RSI, MACD, MA(50/200), ADX, OBV, and ATR using pure pandas/numpy. No technical analysis library is needed. The existing implementations are correct (Wilder's smoothing for RSI, proper DM+/DM- for ADX, EMA-based MACD) and are already consumed by `core/scoring/technical.py` and `core/data/client.py`. Do not add pandas-ta or TA-Lib.

---

## New Dependencies for v1.1

### 1. Market Regime Detection (HMM)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| hmmlearn | >=0.3.3 | Hidden Markov Model for regime detection | GaussianHMM fits 2-4 hidden states on daily returns + volatility features. The existing rule-based classifier in `core/regime/classifier.py` uses hard-coded thresholds (VIX > 20, ADX > 25, etc.) -- HMM adds probabilistic regime transitions with proper state duration modeling. hmmlearn 0.3.3 (Oct 2024) provides cp312 wheels and numpy 2.x compatibility. scikit-learn API (fit/predict). Already in `pyproject.toml` ml optional deps but not installed. | HIGH |
| scikit-learn | >=1.5.0 | Feature preprocessing for HMM | StandardScaler for normalizing returns/volatility features before HMM input. Also provides GaussianMixture as a non-temporal baseline for regime clustering. Required by hmmlearn as dependency anyway. Already in `pyproject.toml` ml optional deps but not installed. | HIGH |

**Architecture integration:** HMM supplements (not replaces) the rule-based classifier. The combined approach: rule-based classifier provides deterministic labels for clear-cut regimes; HMM provides transition probabilities and handles ambiguous states. The `core/regime/classifier.py` output structure (`regime`, `confidence`, `probabilities`) already supports this dual approach -- HMM results feed into the `probabilities` dict.

**What NOT to add:** Do not add `pomegranate` (heavier, less maintained for HMM), `statsmodels.tsa` MarkovSwitching (regime-switching regression is a different model -- it switches regression coefficients, not hidden states), or `tensorflow-probability` (massive dependency for simple 3-4 state HMM).

### 2. Korean Market Data

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pykrx | >=1.2.4 | KOSPI/KOSDAQ historical OHLCV + fundamentals | Scrapes directly from Korea Exchange (KRX). Returns pandas DataFrames matching existing data pipeline. Supports KOSPI, KOSDAQ, KONEX. Provides OHLCV, market cap, PER/PBR/DIV fundamentals. No API key required (public KRX data). Latest v1.2.4 (Feb 2026), requires Python >=3.10. Fills same role as yfinance for Korean market. | HIGH |
| python-kis | >=2.1.6 | KIS broker API (trading + real-time) | Korea Investment & Securities REST-based trading API wrapper. Covers order execution (buy/sell), account balance, real-time price streaming. Same role as alpaca-py for Korean market. v2.1.6 (Oct 2025), requires Python >=3.10. Official KIS API requires developer registration at apiportal.koreainvestment.com. Supports paper trading mode. | MEDIUM |

**Architecture integration:**

- **pykrx** integrates into `src/data_ingest/infrastructure/` as a new adapter implementing the existing `IMarketDataRepository` interface. It returns pandas DataFrames with the same column schema (open/high/low/close/volume) as yfinance. The `core/data/indicators.py` functions work unchanged on Korean stock data.
- **python-kis** integrates into `src/execution/infrastructure/` as a new broker adapter alongside `AlpacaBrokerAdapter`. The existing `IBrokerRepository` interface in `src/execution/domain/repositories.py` defines the contract.

**pykrx vs FinanceDataReader for data:**

| Criterion | pykrx | FinanceDataReader |
|-----------|-------|-------------------|
| KRX OHLCV | Direct KRX scraping | Multiple sources (KRX, Yahoo, Naver) |
| Fundamentals | PER/PBR/DIV from KRX | No KRX fundamentals |
| Maintenance | Active (Feb 2026) | Active (v0.9.102) |
| Dependencies | requests, pandas | requests, pandas, tqdm |
| API surface | Focused on KRX | Broader (US, crypto, etc.) |

Use **pykrx** because it provides KRX fundamentals (PER/PBR/DIV) that are needed for scoring, while FinanceDataReader focuses on price data only. pykrx's API is simpler and purpose-built for the Korean market -- no ambiguity about data source.

**python-kis vs pykis (by pjueon):**

| Criterion | python-kis (Soju06) | pykis (pjueon) |
|-----------|---------------------|----------------|
| PyPI version | 2.1.6 (Oct 2025) | Not on PyPI |
| Maintenance | Active, regular releases | Sporadic |
| Real-time | WebSocket streaming | WebSocket streaming |
| Documentation | Korean, decent coverage | Sparse |

Use **python-kis** (Soju06) because it is on PyPI with versioned releases and has more recent maintenance activity. The pjueon/pykis alternative is GitHub-only with no PyPI packaging.

**MEDIUM confidence on python-kis** because: (1) KIS API developer registration requires a Korean brokerage account, which may block international users; (2) API documentation is Korean-only; (3) the library is community-maintained, not official KIS SDK. The official `koreainvestment/open-trading-api` repo provides sample code but not a packaged library.

### 3. Commercial API -- Production Hardening

FastAPI (0.135.1) and uvicorn (0.41.0) are already installed. The following additions are needed for production-grade API serving.

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| slowapi | >=0.1.9 | Rate limiting | Adapted from flask-limiter for Starlette/FastAPI. Production-proven (millions of requests/month). In-memory storage for single-instance deployment, Redis backend available when scaling. Token bucket and fixed/sliding window algorithms. <1ms latency overhead. | HIGH |
| PyJWT | >=2.9.0 | JWT token handling | For API key management and tier-based access control. FastAPI official docs now recommend PyJWT over python-jose (python-jose last released 2021, has security issues). Minimal dependencies. Supports HS256/RS256. | HIGH |
| passlib[bcrypt] | >=1.7.4 | Password/key hashing | Secure hashing for API key storage. bcrypt backend is the standard choice. Needed if implementing user registration for commercial API tiers ($29/$49/$199). | HIGH |

**What NOT to add:**

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| python-jose | Last release 2021, known security issues. FastAPI team has moved to PyJWT. | PyJWT >=2.9.0 |
| fastapi-limiter | Less mature than slowapi, fewer production deployments documented. | slowapi >=0.1.9 |
| Redis (for v1.1) | Overkill for single-instance deployment. slowapi's in-memory backend is sufficient until scaling to multiple instances. Existing SQLite + DuckDB caching handles data caching. | slowapi in-memory storage |
| Stripe | Premature. Build the API first, validate demand, then add billing. Stripe integration is a separate milestone. | Defer to v1.2+ |

**Architecture integration:**

- `slowapi` wraps the existing FastAPI `app` in `commercial/api/main.py`. Rate limits defined as decorators on existing route handlers.
- The existing `dependencies.py` already has `verify_api_key` using header-based API key. Upgrade path: add JWT for tier-based access (free/basic/pro), keep API key as fallback for simple integrations.
- Rate limit tiers map to commercial product pricing: free (10 req/min), basic $29 (60 req/min), pro $99 (300 req/min).

### 4. ML Dependencies (Optional, Install on Demand)

These are already declared in `pyproject.toml` under `[project.optional-dependencies] ml` but NOT currently installed in the venv.

| Technology | Version | Purpose | Status | Confidence |
|------------|---------|---------|--------|------------|
| scikit-learn | >=1.5.0 | Feature scaling, GMM baseline | Declared, not installed | HIGH |
| hmmlearn | >=0.3.3 | HMM regime detection | Declared, needs version bump (currently >=0.3) | HIGH |
| xgboost | >=2.0.0 | Future: ML-based scoring enhancement | Declared, not needed for v1.1 | N/A |
| optuna | >=3.3.0 | Future: hyperparameter optimization | Declared, not needed for v1.1 | N/A |

**Action needed:** Install ml extras (`pip install -e ".[ml]"`) and update hmmlearn version pin from `>=0.3` to `>=0.3.3` to ensure numpy 2.x wheel availability.

---

## Updated pyproject.toml Changes

Only changes needed (diff from current):

```toml
# ADD to [project] dependencies
dependencies = [
    # ... existing deps unchanged ...

    # NEW: Korean market data
    "pykrx>=1.2.4",

    # NEW: Korean broker
    "python-kis>=2.1.6",

    # NEW: Commercial API hardening
    "slowapi>=0.1.9",
    "PyJWT>=2.9.0",
    "passlib[bcrypt]>=1.7.4",
]

# UPDATE [project.optional-dependencies] ml
[project.optional-dependencies]
ml = [
    "scikit-learn>=1.5.0",     # was >=1.3
    "hmmlearn>=0.3.3",         # was >=0.3 -- need numpy 2.x wheels
    "xgboost>=2.0",            # unchanged
    "optuna>=3.3",             # unchanged
]
```

## Installation Commands

```bash
# Install new v1.1 core dependencies
pip install pykrx>=1.2.4 python-kis>=2.1.6 slowapi>=0.1.9 PyJWT>=2.9.0 "passlib[bcrypt]>=1.7.4"

# Install ML dependencies (for HMM regime detection)
pip install -e ".[ml]"

# Or all at once
pip install pykrx python-kis slowapi PyJWT "passlib[bcrypt]" scikit-learn hmmlearn
```

---

## Integration Points with Existing Stack

### Technical Scoring: NO new dependencies

The existing `core/data/indicators.py` already computes all required technical indicators:

| Indicator | Function | Status |
|-----------|----------|--------|
| RSI(14) | `indicators.rsi(close, 14)` | Implemented (Wilder's smoothing) |
| MACD(12,26,9) | `indicators.macd(close)` | Implemented (returns line/signal/histogram) |
| MA(50), MA(200) | `indicators.ma(close, N)` | Implemented (SMA) |
| ADX(14) | `indicators.adx(df, 14)` | Implemented (DM+/DM-, smoothed) |
| OBV | `indicators.obv(df)` | Implemented (cumulative signed volume) |
| ATR(21) | `indicators.atr(df, 21)` | Implemented (Wilder's smoothing) |

The `core/scoring/technical.py` already uses these to produce `trend_score`, `momentum_score`, `volume_score`, and composite `technical_score` (0-100). The v1.1 work is to integrate this into the DDD path (`src/scoring/`) and add it to the composite scoring alongside fundamental scores -- this is architecture work, not a dependency issue.

### HMM Regime Detection: hmmlearn + scikit-learn

Integration flow:
1. `core/data/market.py` provides VIX, S&P 500 vs 200MA, yield curve (already implemented)
2. NEW: Feed daily log returns + range + VIX to `GaussianHMM(n_components=3)` (Bull/Bear/Transition)
3. HMM output feeds into existing `core/regime/weights.py` regime-weight mapping
4. Rule-based classifier (`core/regime/classifier.py`) serves as fallback when HMM confidence < threshold

### Korean Market: pykrx + python-kis

Integration flow:
1. pykrx returns pandas DataFrames with same schema as yfinance (date-indexed OHLCV)
2. Existing `core/data/indicators.compute_all(df)` works unchanged on Korean stock data
3. Existing `core/scoring/technical.compute_technical_score(df, indicators)` works unchanged
4. Fundamental scoring needs adaptation: Korean companies use IFRS (same as SEC EDGAR) but data fields may differ (PER vs P/E naming, etc.)
5. python-kis broker adapter maps to same `IBrokerRepository` interface as Alpaca

### Commercial API: slowapi + PyJWT + passlib

Integration flow:
1. `commercial/api/main.py` already has FastAPI app with CORS, health check, and 3 product routers
2. `commercial/api/dependencies.py` already has `verify_api_key` -- extend with JWT-based tier verification
3. Add slowapi limiter as middleware wrapping existing app
4. Existing Pydantic schemas in `commercial/api/schemas.py` and `commercial/api/models.py` need no changes

---

## Alternatives Considered (v1.1 specific)

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Korean data | pykrx | FinanceDataReader | FDR has no KRX fundamentals (PER/PBR/DIV). pykrx provides both price + fundamentals from KRX directly. |
| Korean data | pykrx | yfinance (KRX) | yfinance has limited KRX coverage, unreliable for KOSDAQ small-caps, no KRX-specific fundamentals. |
| Korean broker | python-kis | pykis (pjueon) | pykis not on PyPI, sporadic maintenance. python-kis has versioned releases. |
| Korean broker | python-kis | Official KIS samples | Official repo provides sample code, not a packaged library. python-kis wraps the API properly. |
| Regime detection | hmmlearn | pomegranate | Heavier dependency, less focused on financial HMM patterns. hmmlearn has scikit-learn-compatible API. |
| Regime detection | hmmlearn | statsmodels MarkovSwitching | Different model (regime-switching regression, not hidden state). MarkovSwitching switches regression coefficients; HMM detects hidden states from observed features. |
| Rate limiting | slowapi | Custom middleware | slowapi is battle-tested (millions req/month). No reason to write custom token-bucket code. |
| Rate limiting | slowapi | fastapi-limiter | Less community adoption, fewer production references. slowapi is the de facto choice. |
| JWT | PyJWT | python-jose | python-jose abandoned since 2021, known CVEs. FastAPI team recommends PyJWT. |
| JWT | PyJWT | joserfc (authlib) | joserfc is newer with JWE support, but overkill for API key tier management. PyJWT is simpler and sufficient. |
| Tech indicators | Existing code | pandas-ta | Already implemented all needed indicators in `core/data/indicators.py`. Adding pandas-ta would duplicate existing code. |
| Tech indicators | Existing code | TA-Lib | Requires C compilation. Already have pure-Python implementations. No benefit for 6 indicators. |

---

## Version Verification Sources

| Package | Version | Source | Verified Date | Confidence |
|---------|---------|--------|---------------|------------|
| hmmlearn | 0.3.3 | [PyPI](https://pypi.org/project/hmmlearn/) | 2026-03-12 | HIGH |
| scikit-learn | 1.5.x | [PyPI](https://pypi.org/project/scikit-learn/) | 2026-03-12 | HIGH |
| pykrx | 1.2.4 | [PyPI](https://pypi.org/project/pykrx/) | 2026-03-12 | HIGH |
| python-kis | 2.1.6 | [PyPI](https://pypi.org/project/python-kis/) | 2026-03-12 | HIGH |
| slowapi | 0.1.9 | [PyPI](https://pypi.org/project/slowapi/), [GitHub](https://github.com/laurentS/slowapi) | 2026-03-12 | HIGH |
| PyJWT | 2.9.x | [PyPI](https://pypi.org/project/PyJWT/) | 2026-03-12 | HIGH |
| passlib | 1.7.4 | [PyPI](https://pypi.org/project/passlib/) | 2026-03-12 | HIGH |
| FastAPI | 0.135.1 | Already installed | 2026-03-12 | HIGH |
| uvicorn | 0.41.0 | Already installed | 2026-03-12 | HIGH |

---

## Dependency Summary

### Must Add (5 packages)

| Package | Purpose | Risk |
|---------|---------|------|
| pykrx | Korean market OHLCV + fundamentals | Low -- pure Python, KRX public data |
| python-kis | Korean broker integration | Medium -- requires KIS account, Korean docs |
| slowapi | API rate limiting | Low -- battle-tested, simple integration |
| PyJWT | JWT authentication for API tiers | Low -- industry standard |
| passlib[bcrypt] | API key hashing | Low -- industry standard |

### Must Install (2 packages, already declared)

| Package | Purpose | Action |
|---------|---------|--------|
| hmmlearn | HMM regime detection | `pip install -e ".[ml]"` |
| scikit-learn | Feature preprocessing | `pip install -e ".[ml]"` |

### Do NOT Add

| Package | Reason |
|---------|--------|
| pandas-ta / TA-Lib | Indicators already implemented in core/data/indicators.py |
| Redis | Overkill for single-instance API. Use slowapi in-memory. |
| python-jose | Abandoned, CVEs. Use PyJWT. |
| FinanceDataReader | pykrx provides both price + fundamentals |
| Stripe | Premature. Build API first, validate demand. |
| pomegranate | hmmlearn is simpler and sufficient |
| Celery | No background task queue needed for v1.1 |

---

## Key Stack Decisions for v1.1

1. **No new technical analysis library needed** -- All RSI/MACD/MA/ADX/OBV indicators are already implemented with pure pandas/numpy in `core/data/indicators.py`. The v1.1 work is DDD integration and composite scoring, not computation.

2. **HMM supplements rule-based regime detection** -- hmmlearn's GaussianHMM adds probabilistic transitions. The existing rule-based classifier remains as the deterministic fallback. Both feed into the same regime output structure.

3. **pykrx for Korean data, python-kis for Korean trading** -- Clean separation matching the existing yfinance (data) / alpaca-py (trading) pattern. Same adapter interfaces, same data schemas.

4. **In-memory rate limiting first** -- slowapi with in-memory storage handles single-instance deployment. Redis backend is a configuration switch when scaling to multi-instance. No new infrastructure.

5. **PyJWT over python-jose** -- python-jose is abandoned (2021). FastAPI team officially recommends PyJWT now. Simpler, actively maintained.

6. **Defer Redis, Stripe, Celery** -- Single-instance deployment does not need distributed caching, payment processing, or background task queues. Add when scaling demands it (v1.2+).

---
*Stack research for: v1.1 Stabilization & Expansion (technical scoring, regime detection, Korean market, commercial API)*
*Researched: 2026-03-12*
*All versions verified against PyPI on 2026-03-12*
