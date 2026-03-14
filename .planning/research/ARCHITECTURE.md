# Architecture Research

**Domain:** Integration of Technical Scoring, Sentiment Scoring, Commercial API, and Performance Attribution into existing DDD trading system
**Researched:** 2026-03-14
**Confidence:** HIGH

## System Overview (Current + New Features)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │ CLI (Typer)   │  │ Dashboard    │  │ Commercial API (FastAPI)     │  │
│  │ (existing)    │  │ (existing)   │  │ [NEW: auth/billing/rate-limit]│  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┬───────────────┘  │
│         │                 │                          │                   │
│  Next.js 16 BFF ──────────┘                          │                   │
├─────────┴────────────────────────────────────────────┴───────────────────┤
│                        APPLICATION LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Bootstrap (Composition Root)                    │   │
│  │                    SyncEventBus cross-context wiring               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                       BOUNDED CONTEXTS (DOMAIN)                         │
│                                                                          │
│  EXISTING:                                                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │scoring  │ │signals  │ │regime   │ │portfolio│ │execution│          │
│  │         │ │         │ │         │ │         │ │         │          │
│  │[MODIFY] │ │         │ │[MODIFY] │ │[MODIFY] │ │         │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
│       │           │           │           │           │                │
│  ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐          │
│  │approval │ │pipeline │ │dashboard│ │data_    │ │backtest │          │
│  │         │ │         │ │         │ │ingest   │ │         │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                                          │
│  NEW BOUNDED CONTEXTS:                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ sentiment    │  │ performance  │  │ commercial   │                   │
│  │ [NEW]        │  │ [NEW]        │  │ [NEW]        │                   │
│  │ news/insider │  │ attribution  │  │ auth/billing │                   │
│  │ /instit/anlst│  │ /pnl decomp  │  │ /rate-limit  │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                      INFRASTRUCTURE LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ SQLite (ops) │  │ DuckDB       │  │ External APIs│                   │
│  │              │  │ (analytics)  │  │ (yfinance,   │                   │
│  │              │  │              │  │  EDGAR, etc) │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Integration Decision: New vs Modified Contexts

### Decision Matrix

| Feature Area | New Context? | Rationale |
|---|---|---|
| Technical Scoring | **NO** -- Modify `scoring` | Already lives there. `TechnicalScoringService` + `TechnicalScore` VO exist in `scoring/domain/`. Technical scoring is a scoring axis, not an independent domain. |
| Sentiment Scoring | **YES** -- New `sentiment` context | Current `SentimentScore` VO is a placeholder (value=50). Real sentiment requires external data sources (news APIs, SEC filings, institutional holdings) and its own ingestion pipeline. Separate bounded context because it has distinct data sources, update cadence, and failure modes. Publishes `SentimentScoreUpdatedEvent` consumed by `scoring`. |
| Commercial API | **YES** -- New `commercial` context | Auth, billing, rate-limiting, and API key management are an entirely separate business domain. Must not pollute the dashboard or personal use paths. Wraps scoring/regime/signals handlers behind auth + rate-limit middleware. |
| Performance Attribution | **YES** -- New `performance` context | 4-level P&L decomposition (market/sector/stock/timing) is a read-heavy analytics domain. Consumes `PositionClosedEvent` and trade history. Produces attribution reports. Does not affect trading decisions (read-only analysis). |
| Regime Enhancement | **NO** -- Modify `regime` | VIX/yield curve/HMM additions extend existing `RegimeDetectionService`. Same domain, same responsibilities, richer inputs. |

### Summary: 3 New Contexts + 3 Modified Contexts

**New:** `sentiment`, `performance`, `commercial`
**Modified:** `scoring` (technical axis integration), `regime` (HMM enhancement), `portfolio` (attribution data export)

## New Bounded Context Designs

### 1. Sentiment Context (`src/sentiment/`)

```
src/sentiment/
    domain/
        entities.py         # SentimentAnalysis (per-symbol aggregate)
        value_objects.py     # NewsSentiment, InsiderActivity, InstitutionalHoldings, AnalystRevisions
        events.py           # SentimentUpdatedEvent
        services.py         # SentimentScoringDomainService
        repositories.py     # ISentimentRepository (ABC)
        __init__.py
    application/
        commands.py          # ComputeSentimentCommand
        queries.py           # GetSentimentQuery
        handlers.py          # SentimentHandler
        __init__.py
    infrastructure/
        news_adapter.py      # External news API adapter
        edgar_insider_adapter.py  # SEC EDGAR insider transactions
        institutional_adapter.py  # 13F filings adapter
        sqlite_repo.py       # Persistence
        __init__.py
    DOMAIN.md
```

**Domain events emitted:** `SentimentUpdatedEvent(symbol, sentiment_score, sub_scores, timestamp)`
**Domain events consumed:** None (independent data source)
**Integration point:** `scoring` context subscribes to `SentimentUpdatedEvent` to replace the hardcoded `SentimentScore(value=50)` default.

**Key design decision:** The `SentimentScore` VO stays in `scoring/domain/value_objects.py` (it is a scoring axis). The `sentiment` context produces the _data_ that populates it. This follows the existing pattern where `core/scoring/sentiment.py` computes the score and `ScoreSymbolHandler._get_sentiment()` calls it.

### 2. Performance Context (`src/performance/`)

```
src/performance/
    domain/
        entities.py          # AttributionReport, TradePerformance
        value_objects.py     # MarketReturn, SectorReturn, StockAlpha, TimingEffect
        events.py            # AttributionComputedEvent
        services.py          # AttributionDomainService (Brinson-Fachler model)
        repositories.py      # IPerformanceRepository (ABC)
        __init__.py
    application/
        commands.py          # ComputeAttributionCommand
        queries.py           # GetAttributionQuery, GetPerformanceSummaryQuery
        handlers.py          # PerformanceHandler
        __init__.py
    infrastructure/
        benchmark_adapter.py  # S&P 500, sector ETF returns
        sqlite_repo.py
        __init__.py
    DOMAIN.md
```

**Domain events emitted:** `AttributionComputedEvent(portfolio_id, period, total_return, attribution_breakdown)`
**Domain events consumed:** `PositionClosedEvent` (from portfolio), `OrderFilledEvent` (from execution)
**Integration point:** Read-only analytics. Queries portfolio/position repos for trade history. Does not affect trading logic.

**Key design decision:** Performance attribution is a _consumer_ of trading data, not a producer of trading decisions. It never writes to scoring, signals, or execution. This keeps it safely decoupled and allows it to be built and tested independently.

### 3. Commercial Context (`src/commercial/`)

```
src/commercial/
    domain/
        entities.py          # ApiKey, Subscription, UsageRecord
        value_objects.py     # ApiTier, RateLimit, BillingPeriod
        events.py            # SubscriptionCreatedEvent, RateLimitExceededEvent
        services.py          # AuthDomainService, RateLimitDomainService
        repositories.py      # IApiKeyRepository, ISubscriptionRepository, IUsageRepository
        __init__.py
    application/
        commands.py          # CreateApiKeyCommand, RecordUsageCommand
        queries.py           # ValidateApiKeyQuery, GetUsageQuery
        handlers.py          # AuthHandler, BillingHandler, RateLimitHandler
        __init__.py
    infrastructure/
        sqlite_repo.py       # API keys, subscriptions, usage tracking
        rate_limiter.py      # Token bucket / sliding window implementation
        __init__.py
    presentation/
        api/
            router.py        # FastAPI router for /api/v1/{quantscore,regimeradar,signalfusion}
            middleware.py     # Auth middleware, rate-limit middleware
            __init__.py
        __init__.py
    DOMAIN.md
```

**Domain events emitted:** `RateLimitExceededEvent`, `SubscriptionCreatedEvent`
**Domain events consumed:** None (independent)
**Integration point:** The commercial API's presentation layer _calls_ existing application handlers (`ScoreSymbolHandler`, `DetectRegimeHandler`, `GenerateSignalHandler`) through the composition root. It does NOT import domain objects directly from other contexts.

**Key design decision:** The commercial context has its own `presentation/api/` because it serves a different audience (external API consumers) with different concerns (auth, billing, rate limits, disclaimers). The personal dashboard and commercial API are separate FastAPI apps mounted on the same process or separate deployments.

## Modifications to Existing Contexts

### Scoring Context (Modified)

**What changes:**
1. `ScoreSymbolHandler._get_sentiment()` currently falls back to `core/scoring/sentiment.py`. Replace with: query `sentiment` context's handler (or subscribe to `SentimentUpdatedEvent` and cache latest value).
2. `ScoreSymbolHandler._get_technical()` already works with raw indicator values and `TechnicalScoringService`. No domain changes needed -- only infrastructure wiring to ensure indicators are always computed (not just when `core/` fallback runs).
3. Add `sentiment_client` injection in bootstrap to wire the sentiment context adapter.

**Files affected:**
- `src/scoring/application/handlers.py` -- wire sentiment client
- `src/bootstrap.py` -- add sentiment context wiring

### Regime Context (Modified)

**What changes:**
1. Add HMM-based regime detection as alternative/ensemble method alongside rule-based.
2. New infrastructure adapter for HMM model (hmmlearn dependency).
3. Domain service remains pure -- HMM outputs `RegimeType` + `confidence` same as current.
4. `RegimeDetectionService.detect()` gains an optional `method` parameter ("rule_based" | "hmm" | "ensemble").

**Files affected:**
- `src/regime/domain/services.py` -- add ensemble method
- `src/regime/infrastructure/` -- add `hmm_adapter.py`
- `src/regime/domain/value_objects.py` -- possibly add `DetectionMethod` enum

### Portfolio Context (Modified)

**What changes:**
1. Add query methods to expose trade history for performance attribution.
2. No new domain logic -- just ensure `IPositionRepository` has methods to query closed positions with entry/exit details.

**Files affected:**
- `src/portfolio/domain/repositories.py` -- add `find_closed_positions(start, end)` if missing
- `src/portfolio/infrastructure/sqlite_position_repo.py` -- implement query

## Data Flow

### Current Pipeline Flow (Unchanged)

```
DataIngest --> Scoring --> Signals --> Risk/Position --> Execution --> Monitoring
     |           |          |          |              |
     v           v          v          v              v
  DuckDB     SQLite     SQLite     SQLite         Alpaca
```

### New Data Flows

```
1. SENTIMENT FLOW (new):
   External APIs (news, EDGAR, 13F)
       |
   sentiment/infrastructure/adapters
       |
   SentimentScoringDomainService --> SentimentUpdatedEvent
       |                              |
   sentiment/sqlite_repo          EventBus
                                      |
                                  scoring/ScoreSymbolHandler (replaces hardcoded 50)

2. PERFORMANCE ATTRIBUTION FLOW (new):
   PositionClosedEvent (from portfolio)
       |
   performance/PerformanceHandler
       |
   AttributionDomainService (Brinson-Fachler)
       |
   performance/sqlite_repo --> Dashboard queries

3. COMMERCIAL API FLOW (new):
   External HTTP Request
       |
   commercial/middleware (auth --> rate-limit --> usage-tracking)
       |
   Existing handlers (score_handler, regime_handler, signal_handler)
       |
   JSON response + disclaimer

4. REGIME ENHANCEMENT FLOW (modified):
   DataIngest (VIX, S&P, yield curve, historical returns)
       |
   regime/hmm_adapter (fit HMM on returns)
       |
   RegimeDetectionService.detect(method="ensemble")
       |
   RegimeChangedEvent --> scoring weight adjustment (existing wiring)
```

### Event Bus Subscriptions (Updated Bootstrap)

```python
# EXISTING subscriptions:
bus.subscribe(RegimeChangedEvent, regime_adjuster.on_regime_changed)
bus.subscribe(RegimeChangedEvent, approval_handler.suspend_if_regime_invalid)
bus.subscribe(DrawdownAlertEvent, approval_handler.suspend_for_drawdown)

# NEW subscriptions:
bus.subscribe(SentimentUpdatedEvent, score_handler.on_sentiment_updated)   # sentiment -> scoring
bus.subscribe(PositionClosedEvent, performance_handler.on_position_closed) # portfolio -> performance
bus.subscribe(OrderFilledEvent, performance_handler.on_order_filled)       # execution -> performance
```

## Architectural Patterns

### Pattern 1: Cross-Context Query via Composition Root

**What:** When `performance` context needs trade history from `portfolio`, it does NOT import `portfolio` repositories directly. Instead, `bootstrap.py` injects the portfolio repo _reference_ into `PerformanceHandler` at construction time.

**When to use:** Any time a context needs to read data owned by another context.

**Trade-offs:** Slightly more wiring in bootstrap, but maintains strict DDD boundary rules. The alternative (shared DB queries) violates context boundaries.

**Example:**
```python
# In bootstrap.py
performance_handler = PerformanceHandler(
    performance_repo=performance_repo,
    position_reader=position_repo,  # injected from portfolio context
    benchmark_adapter=benchmark_adapter,
)
```

### Pattern 2: Commercial API as Facade over Existing Handlers

**What:** The commercial API does not duplicate scoring/signal logic. It calls the same `ScoreSymbolHandler`, `DetectRegimeHandler`, `GenerateSignalHandler` that the personal dashboard uses, but wraps them with auth + rate-limiting + disclaimer middleware.

**When to use:** Building a public-facing API over internal domain logic.

**Trade-offs:** Tight coupling to handler signatures -- if handlers change, commercial API needs updating. Mitigated by the fact that handlers return `Result` objects with stable schemas.

**Example:**
```python
# commercial/presentation/api/router.py
@router.get("/v1/quantscore/{symbol}")
async def get_quantscore(symbol: str, request: Request):
    # Auth + rate-limit already handled by middleware
    ctx = request.app.state.ctx
    handler = ctx["score_handler"]
    result = handler.handle(ScoreSymbolCommand(symbol=symbol))
    if isinstance(result, Ok):
        return {**result.value, "disclaimer": DISCLAIMER_TEXT}
    raise HTTPException(400, detail=str(result.error))
```

### Pattern 3: Sentiment as Event-Driven Data Supplier

**What:** The `sentiment` context runs on its own schedule (e.g., hourly or daily) and publishes `SentimentUpdatedEvent`. The `scoring` context listens and caches the latest sentiment score per symbol. When `ScoreSymbolHandler` runs, it uses cached sentiment instead of the hardcoded default.

**When to use:** When two contexts have different update cadences (sentiment: hourly, scoring: on-demand).

**Trade-offs:** Eventual consistency -- sentiment data may be stale by minutes/hours. Acceptable for mid-term trading (holding period: weeks to months).

**Example:**
```python
# scoring/application/handlers.py
class ScoreSymbolHandler:
    def __init__(self, ..., sentiment_cache: dict[str, float] | None = None):
        self._sentiment_cache = sentiment_cache or {}

    def on_sentiment_updated(self, event: SentimentUpdatedEvent) -> None:
        self._sentiment_cache[event.symbol] = event.sentiment_score

    def _get_sentiment(self, symbol: str) -> dict:
        cached = self._sentiment_cache.get(symbol)
        if cached is not None:
            return {"sentiment_score": cached}
        # Fallback to existing core/scoring/sentiment.py
        ...
```

## Recommended Project Structure (After Integration)

```
src/
├── scoring/            # [MODIFIED] Wire real sentiment + technical indicators
│   ├── domain/
│   │   ├── services.py         # CompositeScoringService, TechnicalScoringService (unchanged)
│   │   ├── value_objects.py    # FundamentalScore, TechnicalScore, SentimentScore (unchanged)
│   │   └── events.py           # ScoreUpdatedEvent (unchanged)
│   ├── application/
│   │   └── handlers.py         # Wire sentiment_cache, sentiment_client
│   └── infrastructure/
├── sentiment/          # [NEW] News, insider, institutional, analyst data
│   ├── domain/
│   │   ├── value_objects.py    # NewsSentiment, InsiderActivity, etc.
│   │   ├── services.py         # SentimentScoringDomainService
│   │   ├── events.py           # SentimentUpdatedEvent
│   │   └── repositories.py     # ISentimentRepository
│   ├── application/
│   │   └── handlers.py         # SentimentHandler
│   ├── infrastructure/
│   │   ├── news_adapter.py     # News API integration
│   │   ├── edgar_insider_adapter.py
│   │   └── sqlite_repo.py
│   └── DOMAIN.md
├── performance/        # [NEW] P&L attribution (read-only analytics)
│   ├── domain/
│   │   ├── value_objects.py    # MarketReturn, SectorReturn, StockAlpha, TimingEffect
│   │   ├── services.py         # AttributionDomainService (Brinson-Fachler)
│   │   ├── events.py           # AttributionComputedEvent
│   │   └── repositories.py     # IPerformanceRepository
│   ├── application/
│   │   └── handlers.py         # PerformanceHandler
│   ├── infrastructure/
│   │   ├── benchmark_adapter.py
│   │   └── sqlite_repo.py
│   └── DOMAIN.md
├── commercial/         # [NEW] Auth, billing, rate-limiting for public API
│   ├── domain/
│   │   ├── entities.py         # ApiKey, Subscription, UsageRecord
│   │   ├── value_objects.py    # ApiTier, RateLimit, BillingPeriod
│   │   ├── services.py         # AuthDomainService, RateLimitDomainService
│   │   └── repositories.py
│   ├── application/
│   │   └── handlers.py         # AuthHandler, BillingHandler
│   ├── infrastructure/
│   │   ├── sqlite_repo.py
│   │   └── rate_limiter.py     # Token bucket implementation
│   ├── presentation/
│   │   └── api/
│   │       ├── router.py       # /api/v1/quantscore, /api/v1/regimeradar, /api/v1/signalfusion
│   │       └── middleware.py   # Auth + rate-limit middleware
│   └── DOMAIN.md
├── regime/             # [MODIFIED] Add HMM-based detection
│   ├── domain/
│   │   └── services.py         # Add ensemble method
│   └── infrastructure/
│       └── hmm_adapter.py      # [NEW] hmmlearn integration
├── portfolio/          # [MODIFIED] Expose closed position queries
│   └── domain/
│       └── repositories.py     # Add find_closed_positions()
├── signals/            # (unchanged)
├── execution/          # (unchanged)
├── pipeline/           # (unchanged)
├── approval/           # (unchanged)
├── dashboard/          # (unchanged -- queries new contexts via bootstrap)
├── data_ingest/        # (unchanged)
├── backtest/           # (unchanged)
├── shared/             # (unchanged)
└── bootstrap.py        # [MODIFIED] Wire 3 new contexts + event subscriptions
```

## Bootstrap Wiring (Key Changes)

```python
# bootstrap.py additions (pseudocode)

# -- Sentiment context --
from src.sentiment.infrastructure import SqliteSentimentRepository, NewsAdapter, EdgarInsiderAdapter
from src.sentiment.application.handlers import SentimentHandler

sentiment_repo = SqliteSentimentRepository(db_path=db_factory.sqlite_path("sentiment"))
news_adapter = NewsAdapter()
sentiment_handler = SentimentHandler(
    sentiment_repo=sentiment_repo,
    news_adapter=news_adapter,
)

# -- Performance context --
from src.performance.infrastructure import SqlitePerformanceRepository, BenchmarkAdapter
from src.performance.application.handlers import PerformanceHandler

performance_repo = SqlitePerformanceRepository(db_path=db_factory.sqlite_path("performance"))
performance_handler = PerformanceHandler(
    performance_repo=performance_repo,
    position_reader=position_repo,   # cross-context injection
    benchmark_adapter=BenchmarkAdapter(),
)

# -- Commercial context --
from src.commercial.infrastructure import SqliteApiKeyRepository, RateLimiter
from src.commercial.application.handlers import AuthHandler

api_key_repo = SqliteApiKeyRepository(db_path=db_factory.sqlite_path("commercial"))
auth_handler = AuthHandler(api_key_repo=api_key_repo)

# -- Event subscriptions --
from src.sentiment.domain.events import SentimentUpdatedEvent
bus.subscribe(SentimentUpdatedEvent, score_handler.on_sentiment_updated)
bus.subscribe(PositionClosedEvent, performance_handler.on_position_closed)
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Personal use (1 user) | Current monolith is perfect. SQLite + SyncEventBus. All contexts in single process. |
| Commercial API (10-100 users) | Add Redis for rate-limiting (replace in-memory token bucket). Keep SQLite for API keys. Consider async event bus for commercial endpoints only. |
| Commercial API (1K+ users) | Move commercial context to separate process. Add PostgreSQL for commercial data (API keys, usage, billing). Keep personal trading in original monolith. |

### Scaling Priorities

1. **First bottleneck:** Rate-limiting state. In-memory token bucket does not survive restarts. Move to Redis when commercial API launches. LOW urgency for initial release.
2. **Second bottleneck:** Concurrent scoring requests from commercial API. Each `ScoreSymbolHandler.handle()` calls yfinance/EDGAR synchronously. Add caching layer (score results valid for 1 hour) to avoid redundant data fetches.

## Anti-Patterns

### Anti-Pattern 1: Sentiment Logic in Scoring Context

**What people do:** Add news fetching, insider trade parsing, and institutional holdings queries directly into `scoring/infrastructure/`.
**Why it is wrong:** Scoring becomes a monolith. Sentiment has different failure modes (news API down != scoring broken), different update cadence, and different data sources. Mixing them makes testing and maintenance harder.
**Do this instead:** Separate `sentiment` context with its own adapters. Publish events. Scoring consumes events.

### Anti-Pattern 2: Commercial API Duplicating Domain Logic

**What people do:** Copy-paste scoring/signal logic into commercial API routes to "keep them independent."
**Why it is wrong:** Two codepaths to maintain. Bugs fixed in one are missed in the other. Commercial and personal scores diverge.
**Do this instead:** Commercial API is a thin facade over the same handlers. Auth/billing/rate-limiting wraps calls to existing handlers.

### Anti-Pattern 3: Performance Attribution Writing Back to Trading Contexts

**What people do:** Have the performance context modify scoring weights or signal thresholds based on attribution results.
**Why it is wrong:** Creates circular dependency (scoring -> performance -> scoring). Makes the system unpredictable.
**Do this instead:** Performance context is strictly read-only. If attribution results should inform parameter tuning, that is the `self-improver` context's job (future phase), which reads attribution reports and produces config changes through a separate, auditable process.

### Anti-Pattern 4: Sharing SQLite DB Files Across Contexts

**What people do:** Put sentiment, performance, and commercial tables in the same SQLite file as scoring.
**Why it is wrong:** SQLite write locks cause contention. One context's migration breaks another.
**Do this instead:** Each context gets its own SQLite file via `db_factory.sqlite_path("context_name")`. This follows the existing pattern (scoring.db, signals.db, regime.db, etc.).

## Integration Points

### External Services

| Service | Context | Integration Pattern | Notes |
|---------|---------|---------------------|-------|
| News API (e.g., Finnhub, Alpha Vantage) | sentiment | Infrastructure adapter, daily batch | Free tiers may suffice for daily sentiment |
| SEC EDGAR (insider trades, 13F) | sentiment | Infrastructure adapter, edgartools library | Already used in data_ingest |
| S&P 500 / sector ETF data | performance | Infrastructure adapter, benchmark returns | yfinance or existing data pipeline |
| Stripe/Lemon Squeezy | commercial | Infrastructure adapter, webhook handler | Phase 2 of commercial -- start with manual billing |

### Internal Boundaries (Event-Based Communication)

| Boundary | Communication | Direction |
|----------|---------------|-----------|
| sentiment -> scoring | `SentimentUpdatedEvent` via EventBus | sentiment publishes, scoring subscribes |
| portfolio -> performance | `PositionClosedEvent` via EventBus | portfolio publishes, performance subscribes |
| execution -> performance | `OrderFilledEvent` via EventBus | execution publishes, performance subscribes |
| scoring -> signals | `ScoreUpdatedEvent` via EventBus | existing (currently logging-only) |
| regime -> scoring | `RegimeChangedEvent` via EventBus | existing (weight adjustment) |
| commercial -> scoring/regime/signals | Direct handler call via bootstrap ctx | commercial calls handlers, no events needed |

### Cross-Context Query Injection (via Bootstrap)

| Consumer | Provider | What Is Injected |
|----------|----------|------------------|
| performance | portfolio | `position_repo` (read-only) |
| commercial | scoring/regime/signals | handler references via ctx dict |
| dashboard | all contexts | repo + handler references via ctx dict |

## Build Order (Dependency-Aware)

**Phase ordering rationale based on dependencies:**

1. **Technical Scoring Integration** (no new context, modifies `scoring`)
   - Zero external dependencies. Already has `TechnicalScoringService` in domain.
   - Just needs infrastructure wiring to ensure indicators always flow through DDD path.
   - Prerequisite for: commercial API (needs complete scoring)

2. **Regime Enhancement** (modifies `regime`)
   - Adds HMM adapter. Isolated change to regime context.
   - No downstream dependencies blocked by this.
   - Prerequisite for: commercial RegimeRadar product

3. **Sentiment Context** (new context)
   - Independent data sources. Can be built in parallel with #1 and #2.
   - Only dependency: event bus subscription to scoring (simple wiring).
   - Prerequisite for: commercial QuantScore product (needs all 3 scoring axes real)

4. **Performance Attribution** (new context)
   - Depends on: portfolio context having closed position query (minor addition).
   - Read-only consumer. Does not block anything else.
   - Can be built in parallel with #3.

5. **Commercial API** (new context)
   - Depends on: scoring, regime, signals all working correctly.
   - Should be last because it is a facade over the other features.
   - Auth/billing/rate-limiting are independent of trading logic.

**Parallel opportunities:**
- Technical Scoring (#1) + Regime Enhancement (#2) can be parallel
- Sentiment (#3) + Performance (#4) can be parallel
- Commercial (#5) last, after #1-#3 complete

## Sources

- Existing codebase analysis (HIGH confidence): `src/scoring/`, `src/regime/`, `src/bootstrap.py`, `src/dashboard/`
- DDD architecture rules: `.claude/rules/ddd.md`
- API feasibility study: `docs/api-technical-feasibility.md`
- Strategy documentation: `docs/strategy-recommendation.md` (via CLAUDE.md summary)
- Brinson-Fachler performance attribution model: standard financial literature (HIGH confidence)

---
*Architecture research for: v1.4 Full Stack Trading Platform integration*
*Researched: 2026-03-14*
