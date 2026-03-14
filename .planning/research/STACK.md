# Technology Stack -- v1.4 Full Stack Trading Platform

**Project:** Intrinsic Alpha Trader v1.4
**Researched:** 2026-03-14
**Confidence:** HIGH
**Scope:** Stack additions for technical scoring, sentiment data, commercial API infrastructure, and performance attribution. Python backend only -- Next.js dashboard (v1.3) is unchanged.

## Existing Stack (DO NOT CHANGE)

Already validated and deployed. Listed here for integration context only.

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Runtime |
| pandas | >=2.0 | Data manipulation |
| numpy | >=1.26 | Numerical computation |
| DuckDB | 1.5.0 | Analytics store |
| SQLite | (stdlib) | Operational store |
| yfinance | >=0.2 | Market data (OHLCV, fundamentals) |
| edgartools | 5.23.0 | SEC EDGAR filings |
| alpaca-py | 0.43.2 | Broker + market data + news |
| FastAPI | >=0.104 | Dashboard + commercial API |
| uvicorn | >=0.24 | ASGI server |
| Typer + Rich | >=0.9 / >=13.0 | CLI |
| pydantic / pydantic-settings | >=2.0 | Data validation + config |
| sse-starlette | >=2.0 | Server-sent events |
| Next.js 16 + React 19 | v1.3 stack | Bloomberg dashboard |

---

## New Stack Additions by Feature

### 1. Technical Scoring -- NO NEW DEPENDENCIES

**Recommendation: Keep using pure pandas/numpy. Do NOT add TA-Lib or pandas-ta.**

| Decision | Rationale |
|----------|-----------|
| No TA-Lib | System already has RSI, MACD, MA, ADX, OBV implemented in `core/data/indicators.py` (92 lines of pure pandas/numpy). TA-Lib requires C library compilation (`ta-lib` system package + `TA-Lib` Python wrapper), adding build complexity for zero functional gain. |
| No pandas-ta | Would add 30+ transitive dependencies for indicators already implemented. The existing implementations use Wilder's smoothing correctly. |

**What exists:** `core/data/indicators.py` computes all required indicators via `compute_all()`:
- `ma(close, period)` -- Simple moving average (MA-50, MA-200)
- `rsi(close, 14)` -- RSI with Wilder's smoothing
- `macd(close, 12, 26, 9)` -- MACD line + signal + histogram
- `adx(df, 14)` -- Average Directional Index
- `obv(df)` -- On-Balance Volume
- `atr(df, 21)` -- Average True Range (for risk management)

**What exists:** `core/scoring/technical.py` already scores these into:
- `trend_score` (MA position + ADX strength + MACD direction)
- `momentum_score` (RSI + 12-1 month price momentum)
- `volume_score` (OBV trend)
- `technical_score` (40% trend + 40% momentum + 20% volume)

**v1.4 work is DDD integration, not library replacement.** The scoring logic needs to be wired into the DDD bounded context (`src/scoring/domain/`) and integrated with the composite score pipeline. If supplementary indicators are needed later (Bollinger Bands, Stochastic RSI), they are 5-10 line functions using `pandas.rolling()`.

**Confidence:** HIGH -- verified by reading `core/data/indicators.py` and `core/scoring/technical.py`.

---

### 2. Sentiment Data Sources

#### 2a. News Sentiment

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| alpaca-py (existing) | 0.43.2 | News headlines (Benzinga) | Already installed. Includes `alpaca.data.historical.news` and `alpaca.data.live.news` modules (verified in installed package). Free tier: 200 calls/min. 6+ years of historical data. Covers all US equities. Zero new dependencies. |
| vaderSentiment | 3.3.2 | Headline sentiment scoring | Lexicon-based, no GPU needed, ~339x faster than FinBERT, zero transitive dependencies. Adequate for headline-level sentiment on a daily scoring pipeline. |

**Why vaderSentiment and NOT FinBERT/transformers:**
- FinBERT requires `torch` (~2GB) + `transformers` (~500MB). Massive dependency footprint.
- VADER accuracy on financial headlines: ~56%. FinBERT: ~91%. BUT sentiment is ONE of THREE scoring axes at 20% composite weight. A 35% accuracy gap on sentiment reduces overall composite accuracy by ~7%.
- The system already handles sentiment uncertainty -- `core/scoring/sentiment.py` defaults to neutral (50) when data is insufficient.
- **Upgrade path:** If accuracy becomes critical, FinBERT can be added to `requirements-ml.txt` as optional without architectural changes.

**Why NOT a paid news API (FMP, Finnhub, Marketaux):**
- Alpaca already provides Benzinga news with existing API keys.
- Project constraint: "Free data sources preferred; paid APIs only if free sources insufficient."

**Confidence:** HIGH -- verified `alpaca/data/historical/news.py` and `alpaca/data/models/news.py` exist in installed alpaca-py 0.43.2.

#### 2b. Insider Trades (Form 4)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| edgartools (existing) | 5.23.0 | SEC Form 3/4/5 insider transactions | Already installed. Parses insider name, relationship, transaction type, shares, price, date. Free, no API key. |

**No new dependency needed.** edgartools parses structured Form 4 data directly from SEC EDGAR.

**Confidence:** HIGH -- edgartools docs confirm Form 3/4/5 support.

#### 2c. Institutional Holdings (13F)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| edgartools (existing) | 5.23.0 | SEC 13F institutional holdings | Already installed. Parses portfolio holdings with position sizes, values, and quarter-over-quarter changes from 13F filings. |

**No new dependency needed** for raw 13F data.

#### 2d. Ownership Enrichment (Supplementary)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| finvizfinance | 1.3.0 | Aggregated ownership %, analyst ratings | `ticker_fundament()` returns insider/institutional ownership percentages. `ticker_inside_trader()` returns recent insider trades (backup to SEC). `ticker_outer_ratings()` returns analyst consensus. Fills aggregation gaps that raw SEC filings don't provide. |

**Risk:** finvizfinance is a web scraper -- fragile to FinViz site changes. Use edgartools as primary data source, finvizfinance as supplementary enrichment only. Fail gracefully if scraping fails.

**Confidence:** MEDIUM -- finvizfinance 1.3.0 confirmed on PyPI (Jan 2026 release). Web scraping reliability is inherently uncertain.

---

### 3. Commercial API Infrastructure

#### 3a. Authentication (JWT)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PyJWT | >=2.12 | JWT token encode/decode | Already used in `commercial/api/dependencies.py` (imported as `jwt`). Industry standard, lightweight, zero transitive dependencies. Latest: 2.12.0 (released 2026-03-12). |

**Note:** CVE-2026-32597 exists (unknown `crit` header extensions) -- low severity for our use case since we control token issuance and don't use critical headers.

**Status:** Code written but not declared in `pyproject.toml`. Must be added.

**Confidence:** HIGH -- already in codebase, just missing dependency declaration.

#### 3b. Rate Limiting

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| slowapi | >=0.1.9 | Per-user tiered rate limiting | Already used in `commercial/api/middleware/rate_limit.py`. Wraps `limits` library. In-memory storage for single-instance deployment. |

**Maintenance concern:** slowapi 0.1.9 is the latest version and hasn't had updates in 12+ months. However, the library is stable and feature-complete for our use case. If it becomes unmaintained, replacing with direct `limits` library usage is straightforward (slowapi is a thin wrapper).

**Status:** Code written but not declared in `pyproject.toml`. Must be added.

**Confidence:** HIGH -- already in codebase.

#### 3c. Billing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| stripe | >=14.4 | Subscription billing (Checkout + Webhooks) | De facto standard for SaaS billing. Latest: 14.4.1 (released 2026-03-06). Handles subscription lifecycle, invoicing, payment methods. Stripe Checkout = hosted payment page (no PCI scope). |

**Integration pattern:**
1. **Stripe Checkout** -- redirect users to Stripe-hosted payment page for subscription creation
2. **Stripe Webhooks** -- receive subscription status changes via `POST /api/v1/webhooks/stripe`
3. **JWT tier claim** -- update user's JWT `tier` field on subscription change
4. **Rate limit sync** -- `_user_tier_cache` in `rate_limit.py` already maps tier to limit

**Why NOT `fastapi-payments`:** Direct Stripe SDK is simpler and better documented than the wrapper. `fastapi-payments` abstracts multiple providers -- unnecessary complexity when we only need Stripe.

**Why NOT Paddle/LemonSqueezy:** Stripe has the largest ecosystem, best Python SDK, most documentation. No reason to use alternatives for a new API product.

**Confidence:** HIGH -- Stripe is the industry standard for SaaS billing. Well-documented FastAPI integration patterns.

---

### 4. Performance Attribution -- NO NEW DEPENDENCIES

**Recommendation: Implement Brinson-Fachler model using pure pandas/numpy.**

| Decision | Rationale |
|----------|-----------|
| No QuantFAA library | Thin wrapper (~200 LOC) around basic pandas operations. Adding a dependency for straightforward math adds maintenance burden without value. |
| No brinson_attribution library | Same issue -- thin wrapper, not actively maintained. |
| No pyfolio | Part of the Zipline ecosystem (quantopian), heavy dependencies (matplotlib, seaborn). We need attribution math, not charting. |

**What to implement (pure pandas):**
- **4-level P&L decomposition:** Market return, sector allocation, stock selection, timing effect
- **Brinson-Fachler attribution:** Allocation effect + selection effect + interaction effect vs. benchmark (SPY)
- **Per-trade attribution:** Entry quality, exit quality, holding period return vs. benchmark
- **Factor exposure:** Market beta, size, value, momentum via pandas rolling regression

The math is well-established (50+ years of academic literature). Implementation is ~150-200 lines of pandas code with no external library needed.

**Confidence:** HIGH -- Brinson attribution is textbook finance math, easily implemented in pandas.

---

## Dependencies to Add to pyproject.toml

### Core dependencies (add to `[project.dependencies]`)

```toml
"PyJWT>=2.12",
"slowapi>=0.1.9",
"vaderSentiment>=3.3.2",
"finvizfinance>=1.3",
```

### Optional commercial dependencies (add to `[project.optional-dependencies]`)

```toml
commercial = [
    "stripe>=14.4",
]
```

### Full new dependencies summary

| Package | Version | Category | Required By | Transitive Deps |
|---------|---------|----------|-------------|-----------------|
| PyJWT | >=2.12 | Core | Commercial API (auth) | 0 |
| slowapi | >=0.1.9 | Core | Commercial API (rate limit) | limits |
| vaderSentiment | >=3.3.2 | Core | Sentiment scoring | 0 |
| finvizfinance | >=1.3 | Core | Ownership data enrichment | requests, lxml, beautifulsoup4 (already installed) |
| stripe | >=14.4 | Optional | Subscription billing | httplib2, typing-extensions (already installed) |

**Total new packages: 4 core + 1 optional.** Minimal footprint. No C extensions. No GPU requirements. No large ML frameworks.

---

## Installation

```bash
# Activate existing venv
cd /home/mqz/workspace/trading
source .venv/bin/activate

# New core dependencies
pip install "PyJWT>=2.12" "slowapi>=0.1.9" "vaderSentiment>=3.3.2" "finvizfinance>=1.3"

# Commercial-only (optional -- only needed for billing)
pip install "stripe>=14.4"

# Already installed, no action needed:
# alpaca-py 0.43.2 (news data), edgartools 5.23.0 (SEC filings)
# pandas, numpy, fastapi, pydantic (core stack)
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Technical indicators | Pure pandas/numpy (existing) | TA-Lib | C library build dependency; all 5 indicators already implemented |
| Technical indicators | Pure pandas/numpy (existing) | pandas-ta | 30+ transitive deps for 5 functions that already exist |
| News data source | Alpaca News API (existing) | Finnhub, FMP, Marketaux | Paid APIs; Alpaca already provides Benzinga news free |
| News sentiment | vaderSentiment (lexicon) | FinBERT (transformer) | 2.5GB deps (torch+transformers) for 20%-weight scoring axis |
| News sentiment | vaderSentiment | TextBlob | Not designed for financial text; VADER has better financial coverage |
| Insider data | edgartools (existing) | sec-api (paid) | edgartools is free, already installed |
| Institutional data | edgartools (existing) | sec-api (paid) | Free and already installed |
| Ownership enrichment | finvizfinance | OpenBB | OpenBB is a full platform (~100+ deps); overkill for ownership % |
| JWT auth | PyJWT | python-jose | PyJWT already in codebase; python-jose adds cryptography dep |
| JWT auth | PyJWT | authlib | Heavier; designed for OAuth providers, not simple JWT encode/decode |
| Rate limiting | slowapi | Custom middleware | slowapi already in codebase; works correctly |
| Rate limiting | slowapi | fastapi-limiter | Less mature than slowapi; different API surface |
| Billing | Stripe | Paddle | Stripe has better Python SDK, larger ecosystem |
| Billing | Stripe | LemonSqueezy | Newer, smaller ecosystem, less documentation |
| Billing | Stripe | fastapi-payments | Unnecessary abstraction; direct Stripe SDK is simpler |
| Attribution | Pure pandas | QuantFAA | Thin wrapper (~200 LOC); DDD requires custom entities |
| Attribution | Pure pandas | pyfolio | Heavy deps (matplotlib, seaborn); we need math, not charts |

---

## What NOT to Add

| Package | Why Not | Use Instead |
|---------|---------|-------------|
| TA-Lib | C library dependency; all indicators already implemented in 92 LOC | `core/data/indicators.py` (existing) |
| pandas-ta | 30+ transitive deps for existing functionality | `core/data/indicators.py` (existing) |
| torch + transformers | 2.5GB for one scoring axis at 20% composite weight | vaderSentiment (339x faster, 0 deps) |
| OpenBB | Full quant platform; massive dependency tree | finvizfinance (focused, lightweight) |
| sec-api | Paid service; edgartools covers the same need for free | edgartools (existing) |
| Redis | Premature for single-instance; in-memory rate limiting is fine | slowapi in-memory (current) |
| Celery | No async job queue needed; APScheduler already handles scheduling | APScheduler (existing) |
| SQLAlchemy | DuckDB + SQLite direct access is simpler; no ORM needed | Direct DuckDB/SQLite |
| pyfolio | Part of Zipline ecosystem; heavy deps for simple attribution math | Pure pandas implementation |
| Finnhub / FMP (paid) | Violates "free data first" constraint | Alpaca News + edgartools |

---

## Version Compatibility Matrix

| Package | Version | Requires | Compatible With |
|---------|---------|----------|-----------------|
| PyJWT | 2.12.0 | Python >=3.9 | Python 3.12 |
| slowapi | 0.1.9 | Python >=3.7 | FastAPI >=0.104 |
| vaderSentiment | 3.3.2 | Python >=3.x | No conflicts |
| finvizfinance | 1.3.0 | requests, lxml, bs4 | All already installed |
| stripe | 14.4.1 | Python >=3.7 | No conflicts |

**No version conflicts identified.** All packages are compatible with Python 3.12 and existing dependencies.

---

## Integration Points with Existing Architecture

### Sentiment Scoring Integration

```
Data Flow:
alpaca-py News API → news headlines (JSON)
  → vaderSentiment → sentiment score per headline (-1 to +1)
  → aggregate by symbol (mean/median of recent N headlines)
  → normalized to 0-100 scale
  → feeds into core/scoring/sentiment.py (replace current proxy-based scoring)

edgartools Form 4 → insider transactions
  → net insider buying ratio (shares bought - sold / total)
  → normalized to 0-100 scale (net buying = bullish)

edgartools 13F → institutional holdings changes
  → quarter-over-quarter change in institutional ownership
  → normalized to 0-100 scale (increasing = bullish)

finvizfinance → insider/institutional ownership %
  → enrichment data for sentiment score
```

### Commercial API Integration

```
Data Flow:
Client → FastAPI (commercial/api/main.py)
  → JWT auth (PyJWT) via dependencies.py
  → Rate limiting (slowapi) via middleware/rate_limit.py
  → DDD handlers (existing) → scoring/regime/signal results

Billing:
Stripe Checkout → subscription created
  → Stripe webhook → POST /api/v1/webhooks/stripe
  → Update user tier in DB
  → JWT tier claim updated on next token refresh
  → Rate limit tier applied via _user_tier_cache
```

---

## Sources

- [EdgarTools documentation - 13F filings](https://edgartools.readthedocs.io/en/latest/13f-filings/) -- Institutional holdings parsing (HIGH confidence)
- [EdgarTools complete guide (2026)](https://edgartools.readthedocs.io/en/stable/complete-guide/) -- Form 4 insider trades (HIGH confidence)
- [Alpaca News API documentation](https://docs.alpaca.markets/docs/historical-news-data) -- Historical news data access (HIGH confidence)
- [Alpaca real-time news streaming](https://docs.alpaca.markets/docs/streaming-real-time-news) -- Live news WebSocket (HIGH confidence)
- [Alpaca + Benzinga partnership](https://alpaca.markets/blog/alpaca-partners-with-benzinga-to-deliver-real-time-embedded-financial-news/) -- News source confirmation (HIGH confidence)
- [VADER vs FinBERT accuracy comparison](https://dzone.com/articles/improving-sentiment-score-accuracy-with-finbert-an) -- VADER 56% vs FinBERT 91% (MEDIUM confidence)
- [FinBERT GitHub](https://github.com/ProsusAI/finBERT) -- FinBERT capabilities reference (HIGH confidence)
- [vaderSentiment PyPI](https://pypi.org/project/vaderSentiment/) -- Version 3.3.2 (HIGH confidence)
- [finvizfinance PyPI](https://pypi.org/project/finvizfinance/) -- Version 1.3.0, Jan 2026 (HIGH confidence)
- [finvizfinance insider documentation](https://finvizfinance.readthedocs.io/en/latest/insider.html) -- Insider data API (HIGH confidence)
- [PyJWT PyPI](https://pypi.org/project/PyJWT/) -- Version 2.12.0 (HIGH confidence)
- [PyJWT CVE-2026-32597](https://advisories.gitlab.com/pkg/pypi/pyjwt/CVE-2026-32597/) -- Security advisory (MEDIUM confidence)
- [slowapi PyPI](https://pypi.org/project/slowapi/) -- Version 0.1.9 (HIGH confidence)
- [Stripe Python SDK PyPI](https://pypi.org/project/stripe/) -- Version 14.4.1 (HIGH confidence)
- [FastAPI + Stripe integration guide](https://dev.to/fastapier/building-a-stripe-subscription-backend-with-fastapi-3n3) -- Integration patterns (MEDIUM confidence)
- [Brinson attribution in Python](https://dataninjago.com/2025/01/19/coding-towards-cfa-36-performance-attribution-with-brinson-model-in-dolphindb-and-python/) -- Implementation reference (MEDIUM confidence)
- Direct codebase verification: `core/data/indicators.py` -- all 5 indicators implemented (HIGH confidence)
- Direct codebase verification: `core/scoring/technical.py` -- technical scoring already functional (HIGH confidence)
- Direct codebase verification: `core/scoring/sentiment.py` -- sentiment scoring stub exists (HIGH confidence)
- Direct codebase verification: `commercial/api/` -- JWT auth + rate limiting already coded (HIGH confidence)
- Direct codebase verification: `alpaca/data/historical/news.py` exists in installed package (HIGH confidence)

---
*Stack research for: v1.4 Full Stack Trading Platform*
*Researched: 2026-03-14*
*All versions verified against PyPI and installed packages on 2026-03-14*
