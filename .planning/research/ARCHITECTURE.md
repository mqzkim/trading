# Architecture Patterns: v1.1 Integration

**Domain:** Quantitative trading system -- expanding from fundamental-only to multi-factor scoring, regime-aware signals, Korean market, and commercial API
**Researched:** 2026-03-12
**Overall Confidence:** HIGH (based on direct codebase analysis of 20K LOC across 8 bounded contexts)

---

## Executive Summary

The v1.0 system already has a well-structured DDD architecture with 8 bounded contexts (`data_ingest`, `scoring`, `signals`, `regime`, `portfolio`, `execution`, `valuation`, `backtest`), an `AsyncEventBus` (defined but not yet wired for cross-context communication), and a dual-database strategy (DuckDB for analytics, SQLite for operational data). The `core/` wrapper layer provides proven mathematical logic that DDD adapters delegate to.

The v1.1 features integrate as follows:

1. **Technical Scoring Engine** -- NOT a new bounded context. It extends the existing `scoring` context. The `TechnicalScore` VO already exists. The `core/scoring/technical.py` already computes RSI, MACD, MA, ADX, OBV. The gap is that `ScoringHandler._get_technical()` currently falls through to a core/ import that expects a pre-computed indicators dict. The integration point is building a proper `CoreTechnicalAdapter` in `scoring/infrastructure/` that takes a ticker, fetches OHLCV from DuckDB, computes indicators via `core/data/indicators.py`, then computes technical score via `core/scoring/technical.py`.

2. **Regime Detection** -- Already its own bounded context (`src/regime/`). The domain service, entities, VOs, repository, and handler are all implemented. The gap is: (a) no infrastructure adapter to fetch live VIX/S&P500/ADX/yield curve data, (b) `RegimeChangedEvent` is defined but never published to the `AsyncEventBus`, (c) `RegimeWeightAdjuster` protocol exists in `scoring` but only `NoOpRegimeAdjuster` is implemented.

3. **Multi-Strategy Signal Fusion** -- The `signals` context already defines the 4-methodology fusion (CAN SLIM, Magic Formula, Dual Momentum, Trend Following) with `SignalFusionService`. The `core/signals/` has implementations for each. The gap is: individual methodology evaluators need to be wired as proper infrastructure adapters instead of lazy `from core.signals.xyz import` fallbacks in the handler. This is a wiring/stabilization task, not an architecture change.

4. **Korean Market Support** -- This DOES require architectural changes. The `data_ingest` context currently hardcodes US market assumptions (SEC EDGAR for financials, yfinance for OHLCV, uppercase-only tickers). Korean market needs: (a) a `KRXDataClient` infrastructure adapter alongside `YFinanceClient`, (b) a `KISBrokerAdapter` in `execution/infrastructure/` alongside `AlpacaAdapter`, (c) ticker format changes (Korean tickers are 6-digit numbers like `005930`), (d) financial data from KIS API instead of SEC EDGAR. The pattern is: add new infrastructure adapters, keep domain pure.

5. **Commercial FastAPI API** -- Already scaffolded at `commercial/api/` with routes for scoring, regime, and signals. The gap is: (a) missing signal fusion route in the v1 DDD-backed routers, (b) no rate limiting or Redis caching, (c) batch scoring needs optimization. The API is a thin presentation layer over existing DDD handlers -- no new bounded contexts needed.

**Key architectural conclusion: No new bounded contexts are needed. All v1.1 features are either extensions to existing contexts (technical scoring, signal fusion) or new infrastructure adapters within existing contexts (Korean market, regime data fetching). The commercial API is a presentation layer concern.**

---

## Current Architecture (As-Is)

### Bounded Contexts and Their States

| Context | DDD Layers | core/ Wrapper | Events Defined | Events Published | DB |
|---------|-----------|---------------|----------------|------------------|----|
| `data_ingest` | domain, infrastructure | `core/data/` | `DataIngestedEvent`, `QualityCheckFailedEvent` | Yes (in pipeline) | DuckDB |
| `scoring` | domain, application, infrastructure | `core/scoring/` | `ScoreUpdatedEvent` | No (defined only) | SQLite |
| `valuation` | domain, infrastructure | `core/valuation/` | None | N/A | DuckDB |
| `signals` | domain, application, infrastructure | `core/signals/` | `SignalGeneratedEvent` | No (defined only) | SQLite, DuckDB |
| `regime` | domain, application, infrastructure | `core/regime/` | `RegimeChangedEvent` | No (defined only) | SQLite |
| `portfolio` | domain, application, infrastructure | personal/ | `PositionOpenedEvent`, `PositionClosedEvent`, `DrawdownAlertEvent` | No (defined only) | SQLite |
| `execution` | domain, application, infrastructure | personal/ | None defined | N/A | SQLite |
| `backtest` | domain, application, infrastructure | `core/backtest/` | None defined | N/A | DuckDB |

### Key Architectural Patterns Already In Place

1. **Adapter Pattern**: `core/` provides mathematical logic; `src/*/infrastructure/*_adapter.py` wraps it for DDD compliance. Example: `CoreScoringAdapter` wraps `core/scoring/fundamental.py`.

2. **Repository Interface in Domain**: `IScoreRepository`, `ISignalRepository`, `IRegimeRepository` are ABCs defined in `domain/repositories.py`, implemented in `infrastructure/sqlite_repo.py`.

3. **Value Object Validation**: All VOs inherit from `ValueObject` base class with `_validate()` method called on construction. Frozen dataclasses enforce immutability.

4. **Command/Handler Pattern**: Application layer uses `Command` dataclasses dispatched to `Handler` classes. Handlers orchestrate: validate input -> call domain service -> save via repository -> return `Result[Ok, Err]`.

5. **Dual Database**: DuckDB for analytical queries (OHLCV screening, batch operations); SQLite for operational persistence (scores, signals, regimes, positions, trade plans).

6. **Protocol-Based Extension Points**: `RegimeWeightAdjuster(Protocol)` in `scoring/domain/services.py` is the designated hook for regime -> scoring integration.

### Data Flow (Current)

```
User (CLI)
    |
    v
DataPipeline.ingest_universe()
    |-- YFinanceClient.fetch_ohlcv() --> DuckDB (ohlcv table)
    |-- EdgartoolsClient.fetch_financials() --> DuckDB (financials table)
    |-- publishes DataIngestedEvent (but no subscribers wired)
    v
ScoreSymbolHandler.handle()
    |-- _get_fundamental() --> core/scoring/fundamental (lazy import)
    |-- _get_technical() --> core/scoring/technical (lazy import)
    |-- _get_sentiment() --> core/scoring/sentiment (lazy import)
    |-- SafetyFilterService.check() --> SafetyGate VO
    |-- CompositeScoringService.compute() --> CompositeScore VO
    |-- IScoreRepository.save() --> SQLite
    v
GenerateSignalHandler.handle()
    |-- CoreSignalAdapter.evaluate_all() or lazy core/ imports
    |-- SignalFusionService.fuse() --> (direction, strength)
    |-- ISignalRepository.save() --> SQLite
    v
TradePlanService.generate_plan()
    |-- personal/execution/planner.plan_entry()
    |-- Risk gates (drawdown, position limits)
    |-- TradePlan VO --> SQLite
    v
Human Approval --> AlpacaAdapter.submit_order()
```

**Critical observation**: The pipeline is currently procedural (each step calls the next). The `AsyncEventBus` exists but events are not published except in `DataPipeline`. This means scoring, signals, regime, and portfolio do NOT react to events -- they are called imperatively.

---

## Target Architecture (v1.1 To-Be)

### Component Boundary Changes

No new bounded contexts. Changes are within existing contexts:

```
EXISTING CONTEXTS (modified):
  data_ingest/
    infrastructure/
      + krx_data_client.py        # Korean OHLCV + financials via KIS API
      + market_adapter_factory.py  # Factory: market -> appropriate client
      ~ yfinance_client.py        # No change
      ~ duckdb_store.py           # Add market column to tables

  scoring/
    infrastructure/
      + core_technical_adapter.py  # Proper adapter: ticker -> OHLCV -> indicators -> score
      ~ core_scoring_adapter.py   # No change
    domain/
      ~ value_objects.py           # TechnicalScore already exists, no change

  regime/
    infrastructure/
      + regime_data_fetcher.py     # Fetch VIX, S&P500, ADX, yield curve from yfinance/FRED
    application/
      ~ handlers.py               # Wire data fetcher, publish RegimeChangedEvent

  signals/
    infrastructure/
      + methodology_adapters.py    # Proper adapters for each of 4 strategies
      ~ core_signal_adapter.py     # Already wraps all 4, may just need cleanup

  execution/
    infrastructure/
      + kis_broker_adapter.py      # Korean broker (KIS OpenAPI)
      ~ alpaca_adapter.py          # No change

  portfolio/
    domain/
      ~ value_objects.py           # Ticker validation must support Korean format

EXISTING LAYERS (modified):
  shared/
    domain/
      + market.py                  # Market enum (US, KR) used across contexts

  commercial/api/
    routers/
      + signals.py                 # v1 DDD-backed signal fusion endpoint
      ~ scoring.py                 # Add batch scoring optimization
      ~ regime.py                  # Add historical regime endpoint
    + middleware/
      + rate_limiter.py            # Token bucket rate limiting
      + cache.py                   # Redis cache layer
```

### Integration Point 1: Technical Scoring Engine

**Current state**: `TechnicalScore` VO exists in `scoring/domain/value_objects.py`. `core/scoring/technical.py` computes the score. `core/data/indicators.py` computes RSI, MACD, MA, ADX, OBV.

**Gap**: `ScoreSymbolHandler._get_technical()` does a lazy `from core.scoring.technical import compute_technical_score`, which expects `(df, indicators)` but the handler passes just a symbol string.

**Solution**: Create `CoreTechnicalAdapter` in `scoring/infrastructure/`:

```python
# scoring/infrastructure/core_technical_adapter.py
class CoreTechnicalAdapter:
    """Fetches OHLCV from DuckDB, computes indicators, returns technical score."""

    def __init__(self, duckdb_store: DuckDBStore):
        self._store = duckdb_store

    def compute(self, ticker: str) -> dict:
        # 1. Get OHLCV from DuckDB (already ingested)
        df = self._store.get_ohlcv(ticker)
        if df.empty:
            return {"technical_score": 50.0}  # neutral fallback

        # 2. Compute indicators via core/data/indicators.py
        from core.data.indicators import compute_all
        indicators = compute_all(df)

        # 3. Compute technical score via core/scoring/technical.py
        from core.scoring.technical import compute_technical_score
        return compute_technical_score(df, indicators)
```

**Modification to `ScoreSymbolHandler`**: Inject `CoreTechnicalAdapter` as `technical_client` parameter. Remove lazy import fallback.

**Data flow change**: None. Technical scoring already fits within the `scoring` handler's existing flow. The adapter just needs to be properly wired.

**Complexity**: LOW. This is a wiring task, not a design task. The math exists in `core/scoring/technical.py` and `core/data/indicators.py`.

### Integration Point 2: Regime Detection (Live Data + EventBus Wiring)

**Current state**: `regime/` context is complete: `RegimeDetectionService` classifies Bull/Bear/Sideways/Crisis from VIX, S&P500, ADX, YieldCurve. `DetectRegimeHandler` creates `MarketRegime` entity. `SqliteRegimeRepository` persists results. BUT: no way to fetch live indicator data, and `RegimeChangedEvent` is never published.

**Gap 1 -- Data Fetching**: Handler requires `vix`, `sp500_price`, `sp500_ma200`, `adx`, `yield_spread` as command inputs. No infrastructure adapter fetches these.

**Solution**: Create `RegimeDataFetcher` in `regime/infrastructure/`:

```python
# regime/infrastructure/regime_data_fetcher.py
class RegimeDataFetcher:
    """Fetches VIX, S&P 500 price/MA200, ADX, yield curve from market data."""

    def __init__(self, duckdb_store: DuckDBStore):
        self._store = duckdb_store

    async def fetch(self) -> DetectRegimeCommand:
        # VIX: fetch ^VIX from yfinance (or DuckDB if pre-ingested)
        # S&P 500: fetch ^GSPC, compute MA200
        # ADX: compute from S&P 500 OHLCV
        # Yield curve: fetch ^TNX (10Y) and ^IRX (3M) or use FRED API
        ...
```

**Gap 2 -- EventBus Publishing**: `MarketRegime.transition_to()` creates `RegimeChangedEvent` and calls `self.add_domain_event()`, but the handler never extracts and publishes domain events.

**Solution**: Modify `DetectRegimeHandler` to:
1. After saving, check if regime changed vs previous
2. If changed, publish `RegimeChangedEvent` to `AsyncEventBus`
3. Subscribers: `CompositeScoringService` adjusts weights via `RegimeWeightAdjuster`

**Gap 3 -- Regime -> Scoring Integration**: `RegimeWeightAdjuster(Protocol)` is defined. Only `NoOpRegimeAdjuster` exists. Need a real implementation.

**Solution**: Create `LiveRegimeAdjuster` implementing `RegimeWeightAdjuster`:

```python
# scoring/infrastructure/regime_weight_adjuster.py
class LiveRegimeAdjuster:
    """Adjusts scoring weights based on current market regime."""

    def __init__(self, regime_repo: IRegimeRepository):
        self._regime_repo = regime_repo

    def adjust_weights(self, strategy: str, regime_type: str | None = None) -> dict[str, float]:
        if regime_type is None:
            latest = self._regime_repo.find_latest()
            regime_type = latest.regime_type.value if latest else None

        base_weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS[DEFAULT_STRATEGY])

        if regime_type == "Crisis":
            # In crisis: boost fundamental weight, reduce technical
            return {"fundamental": 0.55, "technical": 0.20, "sentiment": 0.25}
        elif regime_type == "Bear":
            return {"fundamental": 0.45, "technical": 0.30, "sentiment": 0.25}
        elif regime_type == "Bull":
            return {"fundamental": 0.30, "technical": 0.45, "sentiment": 0.25}
        return base_weights
```

**Data flow change**: Regime detection becomes a prerequisite step in the scoring pipeline. Order: `DataIngest -> Regime -> Scoring -> Signals`.

**Complexity**: MEDIUM. Data fetching requires new infrastructure code. EventBus wiring requires modifying handlers. But all domain logic is already implemented.

### Integration Point 3: Multi-Strategy Signal Fusion

**Current state**: All 4 methodology evaluators exist in `core/signals/` (canslim.py, magic_formula.py, dual_momentum.py, trend_following.py). `SignalFusionService` in `signals/domain/services.py` performs 3/4 consensus voting. `GenerateSignalHandler` orchestrates the flow.

**Gap**: The handler has two code paths:
1. `_evaluate_via_adapter()` -- uses `CoreSignalAdapter`, requires `symbol_data` dict
2. `_evaluate_via_clients()` -- falls through to lazy `from core.signals.xyz import` calls

Neither path is cleanly wired. The handler mixes infrastructure concerns (core/ imports) into application logic.

**Solution**: Clean up `CoreSignalAdapter` to handle the full flow internally:

```python
# signals/infrastructure/core_signal_adapter.py (enhanced)
class CoreSignalAdapter:
    """Evaluates all 4 methodologies using core/ implementations."""

    def __init__(self, duckdb_store: DuckDBStore):
        self._store = duckdb_store

    def evaluate_all(self, ticker: str) -> list[dict]:
        # 1. Fetch OHLCV + financials from DuckDB
        # 2. Prepare symbol_data dict
        # 3. Run each evaluator (canslim, magic_formula, etc.)
        # 4. Return standardized results
        ...
```

**Modification to `GenerateSignalHandler`**: Simplify to single path -- always use adapter. Remove lazy imports.

**Data flow change**: None. Signal generation already follows scoring in the pipeline.

**Complexity**: LOW. This is adapter cleanup, not new logic.

### Integration Point 4: Korean Market Support

**Current state**: The system assumes US market exclusively:
- `data_ingest/domain/value_objects.py`: `Ticker` regex requires `^[A-Z]{1,10}$`
- `data_ingest/infrastructure/yfinance_client.py`: Wraps `CoreDataClient` (US-focused)
- `data_ingest/infrastructure/edgartools_client.py`: SEC EDGAR = US only
- `execution/infrastructure/alpaca_adapter.py`: Alpaca = US only
- `scoring/domain/value_objects.py`: `Symbol` requires uppercase letters only

**Changes needed**:

1. **Shared Market Enum** (new file in `shared/domain/`):
```python
# shared/domain/market.py
class Market(Enum):
    US = "US"      # NYSE, NASDAQ
    KR = "KR"      # KOSPI, KOSDAQ
```

2. **Ticker Validation** (modify `data_ingest/domain/value_objects.py`):
```python
# Korean tickers are 6-digit numbers: "005930" (Samsung)
# US tickers are 1-10 uppercase letters: "AAPL"
_US_TICKER_RE = re.compile(r"^[A-Z]{1,10}$")
_KR_TICKER_RE = re.compile(r"^\d{6}$")

@dataclass(frozen=True)
class Ticker(ValueObject):
    ticker: str
    market: str = "US"

    def _validate(self) -> None:
        if self.market == "KR":
            if not _KR_TICKER_RE.match(self.ticker):
                raise ValueError(f"KR ticker must be 6 digits: {self.ticker}")
        else:
            if not _US_TICKER_RE.match(self.ticker):
                raise ValueError(f"US ticker must be uppercase letters: {self.ticker}")
```

3. **KRX Data Client** (new file in `data_ingest/infrastructure/`):
```python
# data_ingest/infrastructure/krx_data_client.py
class KRXDataClient:
    """Fetches Korean market data via KIS OpenAPI or pykrx."""

    async def fetch_ohlcv(self, ticker: str, days: int = 756) -> pd.DataFrame:
        # KIS OpenAPI: domestic stock daily price
        # or pykrx library for historical data
        ...

    async def fetch_financials(self, ticker: str) -> list[dict]:
        # KIS API: financial statement data
        # Korean financials use different reporting standards (K-IFRS)
        ...
```

4. **Market-Aware Data Pipeline** (modify `data_ingest/infrastructure/pipeline.py`):
```python
class DataPipeline:
    def __init__(self, market: str = "US", ...):
        self._market = market
        if market == "KR":
            self._data_client = KRXDataClient(self._semaphore)
        else:
            self._data_client = YFinanceClient(self._semaphore)
```

5. **KIS Broker Adapter** (new file in `execution/infrastructure/`):
```python
# execution/infrastructure/kis_broker_adapter.py
class KISBrokerAdapter:
    """Korean Investment & Securities OpenAPI broker adapter."""

    def __init__(self, app_key: str, app_secret: str, paper: bool = True):
        self._base_url = "https://openapivts.koreainvestment.com:29443" if paper \
            else "https://openapi.koreainvestment.com:9443"
        ...

    async def submit_order(self, plan: TradePlan) -> OrderResult:
        # KIS API: domestic stock order
        ...
```

6. **DuckDB Schema** (modify `data_ingest/infrastructure/duckdb_store.py`):
```sql
-- Add market column to existing tables
ALTER TABLE ohlcv ADD COLUMN market VARCHAR DEFAULT 'US';
-- Update PRIMARY KEY to include market
-- (requires table recreation since DuckDB doesn't support ALTER PK)
```

**Data flow change**: The pipeline gains a `market` parameter that selects the appropriate infrastructure adapters. Domain logic (scoring, signals, regime) remains market-agnostic -- they operate on the same VOs regardless of market. Regime detection is US-specific (VIX, S&P 500) and should not apply to Korean stocks directly.

**Key constraint**: Korean market scoring works for technicals (OHLCV is universal) but NOT for fundamentals (no SEC EDGAR, different financial reporting). The fundamental scoring path needs a Korean-specific adapter or must gracefully degrade when SEC data is unavailable.

**Complexity**: HIGH. This touches data ingestion, ticker validation, broker integration, and financial data sources. But the DDD architecture handles it cleanly -- new infrastructure adapters, domain stays pure.

### Integration Point 5: Commercial FastAPI API

**Current state**: `commercial/api/` has:
- `main.py`: FastAPI app with health, legacy routes, v1 DDD routes
- `routers/scoring.py`: POST `/v1/score/{symbol}`, GET `/v1/score/{symbol}/latest`
- `routers/regime.py`: GET `/v1/regime/current`
- `schemas.py`: Pydantic models with disclaimer
- `dependencies.py`: DI for handlers and repos

**Gap**: Missing signal fusion v1 router, no rate limiting, no caching, no batch optimization, no API key management beyond basic verification.

**Changes needed**:

1. **Signal Fusion Router** (new file):
```python
# commercial/api/routers/signals.py
router = APIRouter(prefix="/v1/signals", tags=["Signals"])

@router.post("/{symbol}", response_model=SignalResponse)
async def generate_signal(symbol: str, ...):
    # Delegates to GenerateSignalHandler
    ...
```

2. **Rate Limiting Middleware**:
```python
# commercial/api/middleware/rate_limiter.py
# Token bucket per API key, configurable per plan tier
```

3. **Redis Caching**:
```python
# commercial/api/middleware/cache.py
# Cache scoring results by (symbol, strategy) with TTL
# Cache regime results with shorter TTL
```

4. **Batch Scoring Optimization**:
```python
@router.post("/batch", response_model=BatchScoreResponse)
async def batch_score(request: BatchScoreRequest):
    # Run scoring concurrently for up to 20 symbols
    results = await asyncio.gather(*[score_one(s) for s in request.symbols])
    ...
```

**Data flow change**: None. The API is a thin presentation layer. It calls the same DDD handlers that the CLI uses.

**Complexity**: LOW-MEDIUM. The API scaffolding exists. Adding routes is straightforward. Rate limiting and caching are infrastructure concerns.

---

## Data Flow (v1.1 Target)

### Daily Screening Pipeline

```
1. DataIngest
   |-- Market=US: YFinanceClient + EdgartoolsClient -> DuckDB
   |-- Market=KR: KRXDataClient -> DuckDB
   |-- Publishes DataIngestedEvent
   |
   v
2. Regime Detection (US market indicators)
   |-- RegimeDataFetcher: VIX, S&P500, ADX, YieldCurve
   |-- RegimeDetectionService.detect() -> RegimeType + confidence
   |-- Publishes RegimeChangedEvent
   |-- MarketRegime -> SQLite
   |
   v
3. Scoring (per ticker)
   |-- CoreScoringAdapter: fundamental score (F/Z/M/G-Score)
   |-- CoreTechnicalAdapter: technical score (RSI/MACD/MA/ADX/OBV)
   |-- Sentiment: neutral 50 (Phase 1), or external API later
   |-- LiveRegimeAdjuster: adjusts weights based on current regime
   |-- CompositeScoringService.compute() -> CompositeScore
   |-- Publishes ScoreUpdatedEvent
   |-- CompositeScore -> SQLite
   |
   v
4. Signal Fusion (per ticker with score >= threshold)
   |-- CoreSignalAdapter: 4 methodology evaluators
   |-- SignalFusionService.fuse() -> consensus direction + strength
   |-- Publishes SignalGeneratedEvent
   |-- Signal -> SQLite
   |
   v
5. Trade Plan (personal only, BUY signals)
   |-- TradePlanService.generate_plan()
   |-- Risk gates (drawdown, position limits, sector limits)
   |-- TradePlan -> SQLite
   |-- Human approval -> Execution
```

### EventBus Subscription Map (Target)

```
DataIngestedEvent
  -> RegimeDataFetcher (trigger regime check when new data arrives)
  -> (future: auto-score new tickers)

RegimeChangedEvent
  -> LiveRegimeAdjuster (update scoring weights for next scoring run)
  -> Portfolio context (adjust risk parameters in crisis)

ScoreUpdatedEvent
  -> SignalFusionService subscriber (auto-generate signals for scored tickers)
  -> (future: commercial API cache invalidation)

SignalGeneratedEvent
  -> TradePlanService (auto-generate plan for BUY signals)
  -> Portfolio context (update watchlist)

DrawdownAlertEvent
  -> Execution context (auto-pause or reduce orders)
  -> CLI notification
```

---

## Database Architecture (v1.1)

### DuckDB (Analytics -- Read-Heavy)

| Table | Contents | Changes in v1.1 |
|-------|----------|-----------------|
| `ohlcv` | Price bars | Add `market` column (US/KR) |
| `financials` | SEC filings / K-IFRS | Add `market` column, handle different field sets |
| `indicator_cache` | Pre-computed indicators | NEW: cache RSI/MACD/ADX per ticker to avoid recomputation |

### SQLite (Operational -- Write-Heavy)

| Table | Context | Changes in v1.1 |
|-------|---------|-----------------|
| `composite_scores` | scoring | No change |
| `signals` | signals | No change |
| `market_regimes` | regime | No change |
| `positions` | portfolio | No change |
| `trade_plans` | execution | No change |
| `watchlist` | portfolio | No change |
| `api_keys` | commercial | NEW: API key management |
| `rate_limits` | commercial | NEW: per-key rate tracking |

### Redis (Commercial API only -- Cache)

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `score:{symbol}:{strategy}` | 1 hour | Cache computed scores |
| `regime:current` | 15 min | Cache current regime |
| `signal:{symbol}` | 30 min | Cache signal results |

---

## Patterns to Follow

### Pattern 1: Infrastructure Adapter for External Data

**What**: Every external data source gets an adapter in `infrastructure/` that translates between external format and domain VOs.

**When**: Adding any new data source (KIS API, FRED API, new broker).

**Example** (from existing codebase):
```python
# This pattern is already proven in the codebase:
# src/scoring/infrastructure/core_scoring_adapter.py
class CoreScoringAdapter:
    """Infrastructure adapter wrapping core/scoring/ functions for DDD compliance."""

    def compute_altman_z(self, financial_data: dict[str, Any]) -> float:
        # Translates dict -> positional args for core function
        return altman_z_score(
            working_capital=financial_data.get("working_capital", 0.0),
            ...
        )
```

**Apply this pattern for**:
- `CoreTechnicalAdapter` (ticker -> OHLCV -> indicators -> technical score)
- `RegimeDataFetcher` (yfinance/FRED -> VIX/S&P500/ADX/YieldCurve)
- `KRXDataClient` (KIS API -> OHLCV + financials DataFrames)
- `KISBrokerAdapter` (KIS API -> order submission/tracking)

### Pattern 2: Protocol for Extension Points

**What**: Use `Protocol` (structural typing) for integration points between contexts, not ABCs. This avoids tight coupling.

**When**: One context needs to consume data from another context without direct import.

**Example** (from existing codebase):
```python
# scoring/domain/services.py
class RegimeWeightAdjuster(Protocol):
    def adjust_weights(self, strategy: str, regime_type: str | None = None) -> dict[str, float]: ...

# NoOpRegimeAdjuster (default) and LiveRegimeAdjuster (v1.1) both satisfy this
```

### Pattern 3: Market-Agnostic Domain, Market-Specific Infrastructure

**What**: Domain VOs and services should not contain market-specific logic. Market differences are handled in infrastructure adapters.

**When**: Adding Korean market support.

**Example**:
```python
# WRONG: Market logic in domain
class CompositeScoringService:
    def compute(self, ..., market: str = "US"):
        if market == "KR":
            # Korean-specific logic
            ...

# RIGHT: Domain stays pure, factory selects adapter
class DataAdapterFactory:
    @staticmethod
    def create(market: str) -> DataClient:
        if market == "KR":
            return KRXDataClient()
        return YFinanceClient()
```

### Pattern 4: Graceful Degradation for Missing Data

**What**: When a data source is unavailable (e.g., no SEC filings for Korean stocks), the scoring pipeline should produce partial results rather than failing.

**When**: Cross-market scoring where not all data sources exist.

**Example**:
```python
# In ScoringHandler, if fundamental data is unavailable:
fundamental = FundamentalScore(value=50.0)  # neutral default
# TechnicalScore computed from OHLCV (always available)
# SentimentScore neutral default
# Composite score will be lower quality but still valid
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: God Orchestrator

**What**: A single orchestrator class that imports from every bounded context and coordinates the entire pipeline imperatively.

**Why bad**: Already exists as `core/orchestrator.py`. Creates tight coupling, makes testing impossible in isolation, single point of failure.

**Instead**: Use EventBus-driven coordination. Each handler subscribes to relevant events and reacts independently. The CLI commands trigger the first event; the rest flows through subscriptions.

### Anti-Pattern 2: Cross-Context Direct Import

**What**: Importing a domain service from another bounded context directly.

**Why bad**: Already exists: `execution/domain/services.py` imports `from src.portfolio.domain.value_objects import TakeProfitLevels`. This violates DDD bounded context isolation.

**Instead**: Define shared VOs in `shared/domain/` or communicate via events. For `TakeProfitLevels`, it belongs in `shared/domain/` since both execution and portfolio need it, or execution should receive the take-profit price as a primitive in its command.

### Anti-Pattern 3: Lazy Core Imports in Application Layer

**What**: Handlers doing `from core.scoring.technical import compute_technical_score` inside methods.

**Why bad**: Mixes infrastructure concern (which implementation to use) with application orchestration. Untestable without the core/ package available.

**Instead**: Always inject adapters via constructor. The handler should never know about `core/`.

### Anti-Pattern 4: Market-Specific Logic in Domain

**What**: Adding `if market == "KR"` branches to domain services or value objects.

**Why bad**: Violates domain purity. Domain logic should be universal -- the same scoring algorithm works regardless of market.

**Instead**: Market differences are infrastructure concerns (different data clients, different financial statement formats). The domain receives normalized VOs.

---

## Component Boundaries

| Component | Responsibility | Communicates With | v1.1 Changes |
|-----------|---------------|-------------------|--------------|
| `data_ingest` | Fetch + validate + store market data | DuckDB, EventBus | Add KRX client, market column |
| `scoring` | Compute composite quality score | data_ingest (read DuckDB), regime (read latest) | Wire technical adapter, regime adjuster |
| `valuation` | Compute intrinsic value (DCF/EPV/Relative) | data_ingest (read DuckDB) | No changes |
| `signals` | Generate consensus buy/sell signals | scoring (read scores) | Clean up adapter wiring |
| `regime` | Detect market regime (Bull/Bear/Sideways/Crisis) | data_ingest (read DuckDB) | Add data fetcher, publish events |
| `portfolio` | Manage positions + risk | signals (read signals) | No changes |
| `execution` | Generate trade plans, submit orders | portfolio (risk check) | Add KIS adapter |
| `backtest` | Walk-forward backtesting | scoring, signals, data_ingest | No changes |
| `commercial` | REST API presentation layer | scoring, signals, regime handlers | Add signal router, rate limit, cache |
| `shared` | Base classes, event bus, market enum | All contexts | Add Market enum |

---

## Build Order (Dependency-Driven)

The features have the following dependency chain:

```
1. Technical Scoring Engine
   Dependencies: core/scoring/technical.py (exists), core/data/indicators.py (exists)
   Blocks: Nothing (enhances existing scoring)

2. Regime Detection (Live Data + EventBus)
   Dependencies: data_ingest (for market data)
   Blocks: Regime -> Scoring weight adjustment

3. Multi-Strategy Signal Fusion (Cleanup)
   Dependencies: scoring (composite score input)
   Blocks: Nothing (enhances existing signals)

4. Korean Market Support
   Dependencies: data_ingest pattern (to follow), scoring (to extend)
   Blocks: Nothing (additive feature)

5. Commercial API
   Dependencies: scoring, signals, regime handlers (all must be stable)
   Blocks: Nothing (presentation layer)
```

**Recommended build order**:

1. **Technical Scoring Engine** (LOW complexity, HIGH value) -- unlocks accurate composite scores
2. **Regime Detection Live Wiring** (MEDIUM complexity, HIGH value) -- unlocks regime-aware scoring
3. **Signal Fusion Cleanup** (LOW complexity, MEDIUM value) -- stabilizes signal generation
4. **Korean Market Data** (HIGH complexity, MEDIUM value) -- independent after data_ingest pattern is stable
5. **Commercial API Enhancement** (LOW-MEDIUM complexity, MEDIUM value) -- depends on all above being stable

**Rationale**: Technical scoring and regime wiring are prerequisites for accurate composite scores. Accurate scores are prerequisites for meaningful signals. Korean market is additive and independent. Commercial API should come last because it exposes the scoring/signals/regime results, which must be correct first.

---

## Scalability Considerations

| Concern | Current (100 tickers) | At 1,000 tickers | At 10,000 tickers |
|---------|----------------------|-------------------|---------------------|
| Data ingestion | Sequential yfinance calls, ~2 min | Semaphore-limited concurrent (5), ~20 min | Need batch API or paid data source |
| Scoring | Per-ticker sequential, ~30 sec total | DuckDB batch queries, ~5 min | Parallelize scoring, partition by sector |
| Signal generation | 4 evaluators per ticker, ~1 min total | Batch evaluator, ~10 min | Pre-filter by score threshold |
| DuckDB storage | In-memory fits easily | Persistent file, ~100MB | Partition by date, ~1GB |
| SQLite operations | Single writer, fine | WAL mode needed | Consider PostgreSQL migration |
| API response time | Direct computation, ~2s | Cache required, ~200ms with Redis | Read-replica pattern |

---

## Sources

- Direct codebase analysis of `/home/mqz/workspace/trading/src/` (8 bounded contexts, 80+ Python files)
- Direct codebase analysis of `/home/mqz/workspace/trading/core/` (proven mathematical implementations)
- Direct codebase analysis of `/home/mqz/workspace/trading/commercial/` (existing API scaffolding)
- `/home/mqz/workspace/trading/.planning/PROJECT.md` (project context and constraints)
- `/home/mqz/workspace/trading/docs/api-technical-feasibility.md` (Korean market API evaluation)
- `/home/mqz/workspace/trading/docs/strategy-recommendation.md` (personal/commercial split strategy)
- Confidence: HIGH -- all findings based on direct source code reading, not speculation
