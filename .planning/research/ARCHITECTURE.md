# Architecture Patterns

**Domain:** AI-assisted fundamental trading system (mid-term, US equities)
**Researched:** 2026-03-12
**Overall Confidence:** HIGH

## Executive Summary

The Intrinsic Alpha Trader is a pipeline-oriented, event-driven system built on DDD bounded contexts. The architecture follows the "Cosmic Python" patterns (message bus + Unit of Work + repository) adapted for a single-user CLI tool with synchronous event dispatch. Seven bounded contexts communicate exclusively through domain events on a synchronous in-process event bus, with each context maintaining strict layer separation (domain -> application -> infrastructure -> presentation).

The existing codebase in `trading/` already implements four bounded contexts (Scoring, Signals, Regime, Portfolio) with correct DDD structure. This architecture document formalizes the complete target state including the three missing contexts (Data Ingest, Valuation, Execution/Monitoring) and the shared infrastructure that connects them.

**Key architectural insight:** The existing `core/orchestrator.py` is a "God Orchestrator" anti-pattern that directly imports from every module. The target architecture replaces it with event-driven coordination where each bounded context reacts independently to domain events.

---

## Recommended Architecture

### System Overview

```
                    CLI (Typer + Rich)
                         |
                    [Message Bus]
                    /    |    \
            Commands  Events  Queries
               |        |       |
    +----------+--------+-------+-----------+
    |          |        |       |           |
 DataIngest Scoring Valuation Signals  Portfolio
    |          |        |       |      /       \
    |          |        |       |   Risk    Execution
    |          |        |       |              |
    +----------+--------+-------+---------+----+
                         |
                   [Event Bus]
                   (synchronous)
                         |
                    Monitoring
```

### Pipeline Data Flow (Daily Screening Workflow)

```
1. DataIngest  -- fetches OHLCV, financials, SEC data
       |
       | DataRefreshedEvent
       v
2. Regime      -- classifies market state (VIX, trend, yield curve)
       |
       | RegimeClassifiedEvent
       v
3. Scoring     -- Piotroski F + Altman Z + Beneish M + technical + sentiment
       |
       | ScoreUpdatedEvent
       v
4. Valuation   -- DCF + EPV + relative multiples -> intrinsic value range
       |
       | ValuationCompletedEvent
       v
5. Signals     -- combines quality score + valuation gap -> trade signal
       |
       | SignalGeneratedEvent
       v
6. Portfolio   -- position sizing (Kelly) + drawdown defense
       |
       | PositionSizedEvent / EntryPlanCreatedEvent
       v
7. Execution   -- generates trade plan, awaits human approval
       |
       | OrderSubmittedEvent / OrderFilledEvent
       v
8. Monitoring  -- tracks positions, alerts on stop-loss / target hits
       |
       | AlertTriggeredEvent / PositionClosedEvent
       v
       (feeds back to Portfolio for P&L tracking)
```

---

## Bounded Contexts (Component Boundaries)

### Existing Code vs. Target Architecture

The trading workspace has a dual structure (`core/` + `src/`) that must converge:

| Current Location | DDD Target | Status |
|-----------------|------------|--------|
| `core/data/` | `src/data_ingest/` | In core, needs DDD wrapping |
| `core/regime/` + `src/regime/` | `src/regime/` | DDD skeleton + core implementation exist |
| `core/scoring/` + `src/scoring/` | `src/scoring/` | DDD skeleton + core implementation exist |
| (does not exist) | `src/valuation/` | NEW -- build from scratch |
| `core/signals/` + `src/signals/` | `src/signals/` | DDD skeleton + core implementation exist |
| `personal/sizer/` + `personal/risk/` + `src/portfolio/` | `src/portfolio/` | DDD skeleton + personal implementation exist |
| `personal/execution/` | `src/execution/` | In personal, needs DDD wrapping |
| (does not exist) | `src/monitoring/` | NEW -- build from scratch |
| `core/backtest/` | `src/backtest/` | In core, needs DDD wrapping |

**Migration strategy:** Wrap existing `core/` and `personal/` implementations as infrastructure adapters within the DDD structure. Extract domain logic into pure domain layer gradually. Do NOT rewrite from scratch -- the existing code is functional and has test coverage.

---

### 1. Data Ingest Context

**Responsibility:** Fetch, normalize, and cache market data from external sources.

| Layer | Contents |
|-------|----------|
| domain/ | `DataPointEntity`, `TimeSeriesVO`, `DataSourceVO`, `DataRefreshedEvent` |
| application/ | `RefreshSymbolCommand`, `RefreshMarketCommand`, `FetchHistoricalQuery` |
| infrastructure/ | `YFinanceClient`, `SECEdgarClient`, `DuckDBTimeSeriesRepository` |
| presentation/ | CLI commands (`trading data refresh AAPL`) |

**Communicates With:**
- Publishes: `DataRefreshedEvent(symbol, data_types, as_of_date)`
- Subscribes to: nothing (entry point of pipeline)

**Key Design Decisions:**
- DuckDB for time-series storage (columnar, fast analytics, Parquet-compatible)
- SQLite for metadata/config (transactional, small records)
- Cache layer with TTL to avoid re-fetching within same day
- Rate limiter for yfinance/SEC EDGAR API calls
- Data quality validation (missing values, outliers, stale data) is a domain service

### 2. Regime Context (EXISTS)

**Responsibility:** Classify market regime from macro indicators. Determine risk adjustment weights.

| Layer | Contents |
|-------|----------|
| domain/ | `MarketRegime` entity, `RegimeType`/`VIXLevel`/`TrendStrength` VOs, `RegimeChangedEvent` |
| application/ | `ClassifyRegimeCommand`, `GetCurrentRegimeQuery` |
| infrastructure/ | `SqliteRegimeRepository`, macro data adapters |
| presentation/ | CLI command (`trading regime`) |

**Communicates With:**
- Publishes: `RegimeChangedEvent(previous, new, confidence)`
- Subscribes to: `DataRefreshedEvent` (re-classify when new data arrives)

**Regime Types (immutable):** Low-Vol Bull, High-Vol Bull, Low-Vol Range, High-Vol Bear, Transition

**Already Implemented:** Entity with `transition_to()` behavior, value objects (RegimeType, VIXLevel, TrendStrength, YieldCurve, SP500Position), events, SQLite repo, classifier in `core/regime/`. 3-day confirmation rule enforced in entity.

### 3. Scoring Context (EXISTS)

**Responsibility:** Compute composite quality scores for individual securities.

| Layer | Contents |
|-------|----------|
| domain/ | `CompositeScore`/`SafetyGate`/`FundamentalScore` VOs, `SafetyFilterService`, `CompositeScoringService`, `ScoreUpdatedEvent` |
| application/ | `ScoreSymbolCommand`, `GetTopScoresQuery`, `ScoreSymbolHandler` |
| infrastructure/ | `SqliteScoreRepository`, data client adapters |
| presentation/ | CLI command (`trading score AAPL`) |

**Communicates With:**
- Publishes: `ScoreUpdatedEvent(symbol, composite_score, risk_adjusted, safety_passed)`
- Subscribes to: `DataRefreshedEvent`, `RegimeChangedEvent` (regime affects strategy weights)

**Immutable Business Rules (verified in codebase):**
- SafetyGate: Z-Score > 1.81 AND M-Score < -1.78 (academic thresholds, never change)
- Strategy weights: swing (35/40/25 fundamental/technical/sentiment), position (50/30/20)
- Tail risk penalty: risk_adjusted = composite - 0.3 * tail_risk_penalty

**Already Implemented:** Value objects with validation, domain services, events, SQLite + in-memory repos, handlers with gradual core/ migration.

### 4. Valuation Context (NEW -- to build)

**Responsibility:** Compute intrinsic value ranges using ensemble valuation models.

| Layer | Contents |
|-------|----------|
| domain/ | `ValuationEntity`, `IntrinsicValueRangeVO`, `DCFResultVO`, `EPVResultVO`, `RelativeMultiplesResultVO`, `WACCVO`, `MarginOfSafetyVO`, `ValuationCompletedEvent` |
| application/ | `ValueSymbolCommand`, `BatchValuationCommand`, `GetValuationQuery`, `ValueSymbolHandler` |
| infrastructure/ | `SqliteValuationRepository`, treasury rate adapter |
| presentation/ | CLI command (`trading value AAPL`) |

**Communicates With:**
- Publishes: `ValuationCompletedEvent(symbol, intrinsic_low/mid/high, margin_of_safety, confidence)`
- Subscribes to: `DataRefreshedEvent` (needs financial data for DCF inputs)

**Valuation Ensemble (three models, weighted average):**

| Model | Weight | Inputs | Strengths |
|-------|--------|--------|-----------|
| DCF (Discounted Cash Flow) | 40% | FCF projections, WACC, terminal growth | Forward-looking |
| EPV (Earnings Power Value) | 35% | Normalized earnings, cost of capital | No growth assumption needed |
| Relative Multiples (PER/PBR/EV) | 25% | Peer group comparisons | Market-relative anchor |

**Key Value Objects:**
```python
@dataclass(frozen=True)
class IntrinsicValueRangeVO(ValueObject):
    low: float        # conservative estimate
    mid: float        # base case (weighted ensemble)
    high: float       # optimistic estimate
    confidence: float # 0-1, based on data completeness

@dataclass(frozen=True)
class MarginOfSafetyVO(ValueObject):
    value: float  # (intrinsic_mid - market_price) / intrinsic_mid
    # Positive = undervalued, Negative = overvalued
    # Threshold for signal: margin_of_safety > 0.20 (20%)
```

**Ensemble Weighting (immutable):**
```python
VALUATION_WEIGHTS = {
    "dcf": 0.40,
    "epv": 0.35,
    "relative": 0.25,
}
```

### 5. Signals Context (EXISTS)

**Responsibility:** Generate trade signals by combining quality score with valuation gap and strategy consensus.

| Layer | Contents |
|-------|----------|
| domain/ | `TradeSignal` entity, `SignalDirection`/`ConsensusVO` VOs, `SignalGeneratedEvent` |
| application/ | `GenerateSignalCommand`, `GetSignalsQuery`, handlers |
| infrastructure/ | `SqliteSignalRepository`, in-memory cache |
| presentation/ | CLI command (`trading signal AAPL`) |

**Communicates With:**
- Publishes: `SignalGeneratedEvent(symbol, direction, strength, consensus_count, composite_score)`
- Subscribes to: `ScoreUpdatedEvent`, `ValuationCompletedEvent`, `RegimeChangedEvent`

**Signal Logic Enhancement (V2 vs current):**
- Current: 4-strategy consensus (CAN SLIM, dual momentum, magic formula, trend following)
- V2 addition: valuation gap as 5th input (margin_of_safety from Valuation context)
- Signal strength = f(composite_score, valuation_gap, consensus_agreement, regime_adjustment)

**Already Implemented:** Value objects, events, repositories, handlers. Needs valuation gap integration.

### 6. Portfolio/Risk Context (EXISTS)

**Responsibility:** Position sizing, drawdown defense, portfolio-level risk management.

| Layer | Contents |
|-------|----------|
| domain/ | `Portfolio` aggregate, `Position` entity, `KellyFraction`/`ATRStop`/`DrawdownLevel` VOs, `PortfolioRiskService`, events |
| application/ | `OpenPositionCommand`, `ClosePositionCommand`, handlers |
| infrastructure/ | `SqlitePortfolioRepo`, `SqlitePositionRepo` |
| presentation/ | CLI commands (`trading portfolio`, `trading position`) |

**Communicates With:**
- Publishes: `PositionOpenedEvent`, `PositionClosedEvent`, `DrawdownAlertEvent`, `EntryPlanCreatedEvent`
- Subscribes to: `SignalGeneratedEvent` (triggers position sizing)

**Immutable Risk Rules (verified in codebase, NEVER change):**
- Max single position: 8% (MAX_SINGLE_WEIGHT = 0.08)
- Max sector: 25% (MAX_SECTOR_WEIGHT = 0.25)
- Fractional Kelly: 1/4 (FRACTION = 0.25, Full Kelly forbidden)
- ATR stop multiplier: 2.5-3.5x ATR(21)
- Drawdown tiers: 10% CAUTION (halt), 15% WARNING (50% reduce), 20% CRITICAL (liquidate)

**Already Implemented:** Portfolio aggregate with `can_open_position()`, `add_position()`. Position entity with `close()`. PortfolioRiskService with Kelly sizing, ATR stop, drawdown assessment. All events. SQLite + in-memory repos. Handler with full use case orchestration.

### 7. Execution Context (PARTIAL -- needs DDD migration)

**Responsibility:** Generate trade plans, manage human approval workflow, interface with broker.

| Layer | Contents |
|-------|----------|
| domain/ | `TradePlanEntity`, `OrderEntity`, `ApprovalStatusVO`, `OrderSubmittedEvent`, `OrderFilledEvent`, `OrderRejectedEvent` |
| application/ | `CreateTradePlanCommand`, `ApproveOrderCommand`, `SubmitOrderCommand` |
| infrastructure/ | `AlpacaBrokerAdapter`, `SqliteOrderRepository` |
| presentation/ | CLI commands (`trading plan`, `trading approve`, `trading execute`) |

**Communicates With:**
- Publishes: `OrderSubmittedEvent`, `OrderFilledEvent`, `OrderRejectedEvent`
- Subscribes to: `EntryPlanCreatedEvent` (creates pending trade plan)

**Human-in-the-Loop Workflow:**
```
SignalGeneratedEvent
    -> Portfolio sizes position
    -> EntryPlanCreatedEvent
    -> Execution creates TradePlan (status: PENDING_APPROVAL)
    -> CLI displays plan for human review
    -> Human approves/rejects via CLI
    -> If approved: submit to Alpaca Paper Trading
    -> OrderSubmittedEvent / OrderFilledEvent
```

**Existing Code:** `personal/execution/planner.py` (plan generation), `personal/execution/paper_trading.py` (Alpaca integration) -- needs migration to DDD structure.

### 8. Monitoring Context (NEW -- to build)

**Responsibility:** Track live positions, trigger alerts on price targets, manage stop-loss monitoring.

| Layer | Contents |
|-------|----------|
| domain/ | `MonitoredPositionEntity`, `AlertRuleVO`, `PriceTargetVO`, `AlertTriggeredEvent` |
| application/ | `SetAlertCommand`, `CheckPositionsCommand`, `GetAlertsQuery` |
| infrastructure/ | `SqliteAlertRepository`, price feed adapter, `ConsoleNotifier` |
| presentation/ | CLI commands (`trading monitor`, `trading alerts`) |

**Communicates With:**
- Publishes: `AlertTriggeredEvent(symbol, alert_type, current_price, trigger_price)`
- Subscribes to: `OrderFilledEvent` (auto-create monitoring rules), `DataRefreshedEvent` (check prices)

**Alert Types:** Stop-loss hit (ATR-based), take-profit target reached, trailing stop triggered, time-based review reminder (holding period check), drawdown threshold crossed.

---

## Shared Kernel

Kept minimal per DDD rules. Only truly cross-cutting concerns live here.

```
src/shared/
    domain/
        __init__.py          # Entity, ValueObject, DomainEvent, Result
        base_entity.py       # Generic Entity[TId] with event collection
        base_value_object.py # Frozen dataclass with _validate()
        domain_event.py      # DomainEvent ABC with occurred_on + event_type
        result.py            # Ok/Err Result type
    infrastructure/
        event_bus.py         # Synchronous event bus (NEW -- to build)
        db.py                # Database connection factory (NEW -- to build)
    utils/
        dates.py             # Date/timezone helpers
        money.py             # Decimal money arithmetic
```

**Already Implemented:** Entity (with `add_domain_event()` / `pull_domain_events()`), ValueObject, DomainEvent, Ok/Err Result.

**Missing (critical):** EventBus, DB connection factory.

---

## Event Bus Architecture

### Design: Synchronous In-Process Event Bus

For V1 (single user, CLI tool), a synchronous event bus following the Cosmic Python pattern. No message queues, async frameworks, or external message brokers.

**Reference implementation pattern (from Cosmic Python):**
```python
# src/shared/infrastructure/event_bus.py

from __future__ import annotations
from typing import Callable, Dict, List, Type
from src.shared.domain import DomainEvent

EventHandler = Callable[[DomainEvent], None]

class SyncEventBus:
    """Synchronous in-process event bus.

    V1: Single-threaded, synchronous dispatch.
    Handlers execute in registration order.
    Cascading events are queued and processed after current batch.
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
        self._processing = False
        self._queue: list[DomainEvent] = []

    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        if self._processing:
            self._queue.append(event)
            return
        self._processing = True
        try:
            self._dispatch(event)
            while self._queue:
                next_event = self._queue.pop(0)
                self._dispatch(next_event)
        finally:
            self._processing = False

    def _dispatch(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)
```

**Why custom over library:** bubus and pyventus are production-ready but add unnecessary dependency for a simple synchronous case. The bus is <30 lines. Building it avoids version coupling and keeps the shared kernel minimal.

### Event Contract Registry

All cross-context events are frozen dataclasses inheriting from `DomainEvent`. Events carry primitive types only (no entity references across contexts).

| Event | Publisher | Subscriber(s) | Key Payload Fields |
|-------|-----------|---------------|-------------------|
| `DataRefreshedEvent` | DataIngest | Regime, Scoring, Valuation, Monitoring | symbol, data_types[], as_of_date |
| `RegimeChangedEvent` | Regime | Scoring, Signals | previous_regime, new_regime, confidence, vix_value, adx_value |
| `ScoreUpdatedEvent` | Scoring | Signals | symbol, composite_score, risk_adjusted_score, safety_passed, strategy |
| `ValuationCompletedEvent` | Valuation | Signals | symbol, intrinsic_low/mid/high, margin_of_safety, confidence |
| `SignalGeneratedEvent` | Signals | Portfolio | symbol, direction, strength, consensus_count, composite_score, strategy |
| `EntryPlanCreatedEvent` | Portfolio | Execution | symbol, plan_id, shares, entry_price, stop_price, target_price |
| `OrderSubmittedEvent` | Execution | Monitoring | symbol, order_id, broker_order_id, side, quantity |
| `OrderFilledEvent` | Execution | Monitoring, Portfolio | symbol, fill_price, fill_quantity, filled_at |
| `AlertTriggeredEvent` | Monitoring | Portfolio, (CLI notification) | symbol, alert_type, current_price, trigger_price |
| `PositionClosedEvent` | Portfolio | Monitoring | symbol, pnl, pnl_pct |
| `DrawdownAlertEvent` | Portfolio | Execution (halt new orders) | portfolio_id, drawdown, level |

### Event Wiring (Composition Root)

```python
# src/bootstrap.py -- application composition root

def bootstrap(db_path: str = "data/trading.db") -> dict:
    """Wire all dependencies. Returns service container."""
    bus = SyncEventBus()

    # Repositories (infrastructure)
    score_repo = SqliteScoreRepository(db_path)
    signal_repo = SqliteSignalRepository(db_path)
    portfolio_repo = SqlitePortfolioRepository(db_path)
    position_repo = SqlitePositionRepository(db_path)
    valuation_repo = SqliteValuationRepository(db_path)

    # Handlers (application)
    regime_handler = ClassifyRegimeHandler(regime_repo, bus)
    score_handler = ScoreSymbolHandler(score_repo, bus)
    valuation_handler = ValueSymbolHandler(valuation_repo, bus)
    signal_handler = GenerateSignalHandler(signal_repo, bus)
    portfolio_handler = PortfolioManagerHandler(portfolio_repo, position_repo, bus)

    # Event wiring
    bus.subscribe(DataRefreshedEvent, regime_handler.on_data_refreshed)
    bus.subscribe(DataRefreshedEvent, score_handler.on_data_refreshed)
    bus.subscribe(DataRefreshedEvent, valuation_handler.on_data_refreshed)
    bus.subscribe(RegimeChangedEvent, score_handler.on_regime_changed)
    bus.subscribe(ScoreUpdatedEvent, signal_handler.on_score_updated)
    bus.subscribe(ValuationCompletedEvent, signal_handler.on_valuation_completed)
    bus.subscribe(SignalGeneratedEvent, portfolio_handler.on_signal_generated)

    return {
        "bus": bus,
        "handlers": {
            "regime": regime_handler,
            "scoring": score_handler,
            "valuation": valuation_handler,
            "signals": signal_handler,
            "portfolio": portfolio_handler,
        },
    }
```

---

## Database Architecture

### Dual-Database Strategy

| Database | Engine | Purpose | Access Pattern |
|----------|--------|---------|---------------|
| `data/timeseries.duckdb` | DuckDB | OHLCV, fundamentals, indicators | Bulk read, columnar analytics |
| `data/trading.db` | SQLite | Scores, signals, portfolio, orders, alerts, config | Transactional CRUD |

**Rationale:**
- DuckDB excels at analytical queries over time-series data (scanning millions of OHLCV rows, computing indicators, aggregations across stocks)
- SQLite excels at transactional operations (saving individual scores, tracking position state, order status updates)
- Both are embedded, zero-config, file-based -- perfect for CLI tool, no server process
- DuckDB can read Parquet files directly for future data import scenarios

### DuckDB Schema (timeseries.duckdb) -- DataIngest Context

```sql
CREATE TABLE ohlcv (
    symbol      VARCHAR NOT NULL,
    date        DATE NOT NULL,
    open        DOUBLE,
    high        DOUBLE,
    low         DOUBLE,
    close       DOUBLE,
    adj_close   DOUBLE,
    volume      BIGINT,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE fundamentals (
    symbol          VARCHAR NOT NULL,
    period_end      DATE NOT NULL,
    period_type     VARCHAR NOT NULL,  -- 'annual' | 'quarterly'
    revenue         DOUBLE,
    net_income      DOUBLE,
    total_assets    DOUBLE,
    total_liabilities DOUBLE,
    operating_cf    DOUBLE,
    capex           DOUBLE,
    free_cash_flow  DOUBLE,
    shares_outstanding BIGINT,
    roe             DOUBLE,
    pe_ratio        DOUBLE,
    current_ratio   DOUBLE,
    debt_equity     DOUBLE,
    fetched_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, period_end, period_type)
);

CREATE TABLE indicators (
    symbol      VARCHAR NOT NULL,
    date        DATE NOT NULL,
    ma50        DOUBLE,
    ma200       DOUBLE,
    rsi14       DOUBLE,
    macd        DOUBLE,
    macd_signal DOUBLE,
    macd_hist   DOUBLE,
    atr21       DOUBLE,
    adx14       DOUBLE,
    obv         DOUBLE,
    PRIMARY KEY (symbol, date)
);
```

### SQLite Schema (trading.db) -- All Other Contexts

Each bounded context owns its tables exclusively. Table prefix convention (2-letter context abbreviation) prevents collisions and makes ownership explicit.

```sql
-- === Scoring Context (sc_) ===
CREATE TABLE sc_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    composite_score REAL NOT NULL,
    risk_adjusted   REAL NOT NULL DEFAULT 0.0,
    strategy        TEXT NOT NULL DEFAULT 'swing',
    fundamental_score REAL,
    technical_score   REAL,
    sentiment_score   REAL,
    f_score         REAL,
    z_score         REAL,
    m_score         REAL,
    scored_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sc_symbol ON sc_scores(symbol);
CREATE INDEX idx_sc_composite ON sc_scores(composite_score DESC);

-- === Valuation Context (vl_) ===
CREATE TABLE vl_valuations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol           TEXT NOT NULL,
    dcf_value        REAL,
    epv_value        REAL,
    relative_value   REAL,
    ensemble_low     REAL NOT NULL,
    ensemble_mid     REAL NOT NULL,
    ensemble_high    REAL NOT NULL,
    margin_of_safety REAL NOT NULL,
    market_price     REAL NOT NULL,
    confidence       REAL NOT NULL DEFAULT 0.5,
    valued_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_vl_symbol ON vl_valuations(symbol);

-- === Signals Context (sg_) ===
CREATE TABLE sg_signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,  -- 'BUY' | 'SELL' | 'HOLD'
    strength        REAL NOT NULL,
    consensus_count INTEGER NOT NULL,
    composite_score REAL,
    valuation_gap   REAL,
    strategy        TEXT NOT NULL DEFAULT 'swing',
    generated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sg_symbol ON sg_signals(symbol);

-- === Portfolio Context (pf_) ===
CREATE TABLE pf_portfolios (
    portfolio_id    TEXT PRIMARY KEY,
    initial_value   REAL NOT NULL,
    peak_value      REAL NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pf_positions (
    symbol          TEXT PRIMARY KEY,
    portfolio_id    TEXT NOT NULL,
    entry_price     REAL NOT NULL,
    quantity        INTEGER NOT NULL,
    entry_date      DATE NOT NULL,
    strategy        TEXT NOT NULL DEFAULT 'swing',
    stop_price      REAL,
    target_price    REAL,
    sector          TEXT DEFAULT 'unknown',
    risk_tier       TEXT DEFAULT 'medium',
    FOREIGN KEY (portfolio_id) REFERENCES pf_portfolios(portfolio_id)
);

-- === Execution Context (ex_) ===
CREATE TABLE ex_trade_plans (
    plan_id         TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,
    order_type      TEXT NOT NULL,  -- 'LIMIT' | 'MARKET'
    entry_price     REAL NOT NULL,
    stop_price      REAL NOT NULL,
    target_price    REAL,
    shares          INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
    -- 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'SUBMITTED' | 'FILLED'
    approved_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ex_orders (
    order_id        TEXT PRIMARY KEY,
    plan_id         TEXT NOT NULL,
    broker_order_id TEXT,           -- Alpaca order ID
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,  -- 'buy' | 'sell'
    quantity        INTEGER NOT NULL,
    order_type      TEXT NOT NULL,
    limit_price     REAL,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    filled_price    REAL,
    filled_at       TIMESTAMP,
    submitted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES ex_trade_plans(plan_id)
);

-- === Monitoring Context (mn_) ===
CREATE TABLE mn_alert_rules (
    alert_id        TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    alert_type      TEXT NOT NULL,
    -- 'STOP_LOSS' | 'TAKE_PROFIT' | 'TRAILING' | 'TIME_REVIEW' | 'DRAWDOWN'
    trigger_price   REAL,
    trigger_date    DATE,
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mn_alert_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    alert_type      TEXT NOT NULL,
    trigger_price   REAL,
    current_price   REAL NOT NULL,
    triggered_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES mn_alert_rules(alert_id)
);

-- === Regime Context (rg_) ===
CREATE TABLE rg_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    regime_type     TEXT NOT NULL,
    confidence      REAL NOT NULL,
    vix_value       REAL,
    trend_adx       REAL,
    yield_curve     REAL,
    sp500_ratio     REAL,
    detected_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === Backtest Context (bt_) -- future ===
CREATE TABLE bt_runs (
    run_id          TEXT PRIMARY KEY,
    strategy        TEXT NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    initial_capital REAL NOT NULL,
    final_value     REAL NOT NULL,
    total_return    REAL NOT NULL,
    sharpe_ratio    REAL,
    max_drawdown    REAL,
    win_rate        REAL,
    trade_count     INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Database Connection Factory

```python
# src/shared/infrastructure/db.py

import sqlite3
import os
from pathlib import Path

DATA_DIR = Path("data")

def get_sqlite_connection(db_name: str = "trading.db") -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DATA_DIR / db_name)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def get_duckdb_connection(db_name: str = "timeseries.duckdb"):
    import duckdb
    DATA_DIR.mkdir(exist_ok=True)
    return duckdb.connect(str(DATA_DIR / db_name))
```

---

## Patterns to Follow

### Pattern 1: Entity with Domain Event Collection

Entities collect domain events internally. Application layer pulls events after operation completes and publishes to bus. This is already correctly implemented in the existing codebase (`Entity.add_domain_event()` / `pull_domain_events()`).

```python
# Application handler pulls events and publishes to bus
class ClosePositionHandler:
    def handle(self, cmd: ClosePositionCommand) -> Result:
        position = self._repo.find_by_symbol(cmd.symbol)
        result = position.close(cmd.exit_price)
        events = position.pull_domain_events()
        for event in events:
            self._event_bus.publish(event)
        return Ok(result)
```

### Pattern 2: Repository Interface in Domain, Implementation in Infrastructure

Already established. All repository ABCs live in `domain/repositories.py`. Implementations in `infrastructure/`.

### Pattern 3: Command/Query Separation (Lightweight CQRS)

Commands change state, queries read state. Both are frozen dataclasses. No separate read models for V1.

### Pattern 4: Composition Root for Dependency Injection

No DI framework. Manual wiring in `src/bootstrap.py`. All dependencies flow downward. CLI commands call bootstrap to get wired handlers.

### Pattern 5: Safety-Gate-First Pipeline

Every analysis pipeline runs the safety gate (Z > 1.81, M < -1.78) before expensive operations. This saves computation: ~40% of universe may fail safety gate and skip scoring + valuation entirely.

```
Input: 500 stocks
  -> Safety Gate: ~300 pass (60%)
  -> Full scoring: top 50 by composite score
  -> Valuation (expensive): only top 50
  -> Signal generation: only valued stocks
```

### Pattern 6: CLI as Thin Presentation Layer

CLI commands parse arguments, invoke application handlers, format output. No business logic in CLI.

```python
@app.command()
def score(symbol: str, strategy: str = "swing"):
    container = bootstrap()
    handler = container["handlers"]["scoring"]
    result = handler.handle(ScoreSymbolCommand(symbol=symbol, strategy=strategy))
    if isinstance(result, Ok):
        render_score_table(result.value)
    else:
        console.print(f"[red]Error: {result.error}[/red]")
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: God Orchestrator
**What:** All pipeline logic in `core/orchestrator.py` that directly imports from every module.
**Why bad:** The current orchestrator imports from `core.data`, `core.regime`, `core.scoring`, `core.signals`, `personal.sizer`, `personal.risk`, `personal.execution` -- violating bounded context isolation. Testing requires all modules present. Any change can cascade.
**Instead:** Event bus coordinates the pipeline. Each context reacts independently.

### Anti-Pattern 2: Domain Layer with External Dependencies
**What:** Importing pandas, yfinance, sqlite3, or any framework in domain/ files.
**Why bad:** Makes domain untestable without infrastructure. Existing codebase correctly avoids this.
**Instead:** Domain services accept plain Python types. Infrastructure adapters convert.

### Anti-Pattern 3: Cross-Context Direct Import
**What:** Importing entities/services from another bounded context directly.
**Why bad:** Creates tight coupling, violates DDD boundary rules.
**Instead:** Communicate through domain events only. Subscribe to events and maintain local state if needed.

### Anti-Pattern 4: Premature Async/Distributed Architecture
**What:** Using Redis, RabbitMQ, async event buses for V1.
**Why bad:** Single-user CLI tool. Daily batch processing. Distributed infra adds complexity without benefit.
**Instead:** Synchronous event bus + SQLite. DDD boundaries make later migration possible.

### Anti-Pattern 5: Shared Database Tables Between Contexts
**What:** Multiple contexts reading/writing the same table.
**Why bad:** Implicit coupling, unclear ownership, breaking changes cascade.
**Instead:** Each context owns its prefixed tables. Cross-context data via events only.

---

## Migration Path: core/ -> src/ (DDD)

### Phase 1: Shared Infrastructure Foundation
- Build `SyncEventBus` in `src/shared/infrastructure/`
- Build DB connection factory
- Create `src/bootstrap.py` composition root
- Wire existing DDD contexts (Scoring, Signals, Regime, Portfolio) to event bus

### Phase 2: Event-Driven Flow
- Replace direct function calls with event subscriptions
- Update CLI to use bootstrap instead of `core/orchestrator.py`
- Validate all cross-context communication uses events

### Phase 3: New Contexts
- DataIngest (wraps `core/data/`, adds DuckDB)
- Valuation (new, DCF + EPV + relative)
- Execution (migrates `personal/execution/`)
- Monitoring (new)

### Phase 4: Retire core/ Orchestrator
- Once all contexts wired through event bus, `core/orchestrator.py` is unnecessary
- Keep `core/` algorithm implementations referenced as infrastructure adapters
- Eventually move remaining `core/` logic into bounded contexts

---

## Suggested Build Order

Build order follows the critical dependency chain. Upstream contexts must exist before downstream consumers.

```
Phase 1: Infrastructure Foundation
    shared/infrastructure/event_bus.py
    shared/infrastructure/db.py
    src/bootstrap.py (composition root)
    Wire existing 4 contexts to event bus

Phase 2: Data Pipeline
    data_ingest context (DuckDB + yfinance/SEC EDGAR)
    Migrate core/data/ logic as infrastructure adapter

Phase 3: Analysis Core Completion
    regime context (wire to event bus, already implemented)
    scoring context (wire to event bus, already implemented)

Phase 4: Valuation Engine (NEW)
    valuation context (DCF + EPV + relative models)
    Domain services for each model
    Ensemble weighting

Phase 5: Enhanced Signals
    Integrate valuation gap into signal generation
    Subscribe to ValuationCompletedEvent
    Update signal strength formula

Phase 6: Execution & Monitoring
    execution context (migrate personal/execution/)
    monitoring context (new)
    Alpaca paper trading integration
    Human approval workflow

Phase 7: Backtesting & Polish
    backtest context (wrap core/backtest/)
    Unified CLI dashboard
    Daily screening workflow automation
```

**Critical dependency chain:** DataIngest -> Scoring + Valuation -> Signals -> Portfolio -> Execution -> Monitoring

**Parallelizable within phases:**
- Phase 3: Regime and Scoring can be wired simultaneously (both depend on DataIngest only)
- Phase 4-5: Valuation can start while existing signals work without it, then enhance

---

## DDD Compliance Verification

Verified against `.claude/rules/ddd.md`:

| Rule | Status | Evidence |
|------|--------|----------|
| Layer dependency unidirectional | COMPLIANT | All existing contexts: presentation -> application -> domain |
| Domain is pure (no frameworks) | COMPLIANT | No framework imports in any domain/ files (verified: scoring, portfolio, regime, signals) |
| Interfaces in domain | COMPLIANT | `IScoreRepository`, `IPortfolioRepository`, `IPositionRepository` as ABCs in domain/repositories.py |
| Public API via __init__.py only | COMPLIANT | Each context exposes through `__init__.py` |
| Cross-context via events only | **GAP** | Events defined correctly, but no event bus exists yet. CLI uses core/orchestrator.py with direct imports |
| Naming conventions | COMPLIANT | Entity/VO/Event/Service/Repository suffixes used consistently |
| DOMAIN.md in each context | **PARTIAL** | Only portfolio has one (placeholder). All contexts need proper DOMAIN.md |

**Highest priority gap:** Build the event bus and composition root to eliminate the God Orchestrator anti-pattern.

---

## Scalability Considerations

| Concern | Single User (V1) | 100 API Users (V2) | 1000+ Users (V3) |
|---------|-------------------|---------------------|-------------------|
| Event Bus | Synchronous in-process | Async in-process (asyncio) | Redis Pub/Sub |
| Database | SQLite + DuckDB files | PostgreSQL + DuckDB | PostgreSQL + TimescaleDB |
| Data Fetch | Sequential, rate-limited | Async with connection pool | Distributed workers |
| Caching | DuckDB implicit | Redis per-user | Redis cluster |
| Computation | Single-threaded | ProcessPoolExecutor | Celery workers |
| Deployment | CLI on local machine | FastAPI server | Kubernetes pods |

The DDD architecture ensures each transition is incremental. Replacing `SqliteScoreRepository` with `PostgresScoreRepository` requires only a new infrastructure implementation -- domain and application layers remain unchanged.

---

## Sources

- [Cosmic Python - Events and the Message Bus](https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html) -- HIGH confidence, authoritative reference for Python DDD event patterns
- [Cosmic Python - Going to Town on the Message Bus](https://www.cosmicpython.com/book/chapter_09_all_messagebus.html) -- HIGH confidence, command/event unification pattern
- [Cosmic Python - Repository Pattern](https://www.cosmicpython.com/book/chapter_02_repository.html) -- HIGH confidence, repository abstraction pattern
- [DuckDB vs SQLite Comparison (Jan 2026)](https://www.analyticsvidhya.com/blog/2026/01/duckdb-vs-sqlite/) -- MEDIUM confidence, dual database rationale
- [From SQLite to DuckDB: Embedded Analytics (Jan 2026)](https://medium.com/@Quaxel/from-sqlite-to-duckdb-embedded-analytics-is-here-da79263a7fea) -- MEDIUM confidence
- [Alpaca-py SDK Documentation](https://alpaca.markets/sdks/python/) -- HIGH confidence, official broker SDK
- [Python DDD Example (pgorecki)](https://github.com/pgorecki/python-ddd) -- MEDIUM confidence, community reference implementation
- [Crafting Maintainable Python Applications with DDD](https://thinhdanggroup.github.io/python-code-structure/) -- MEDIUM confidence
- [Events in DDD: Event Propagation Strategies](https://medium.com/@dkraczkowski/events-in-domain-driven-design-event-propagation-strategies-b30d8df046e2) -- MEDIUM confidence
- `.claude/rules/ddd.md` -- HIGH confidence, mandatory project rules (verified against codebase)
- Existing codebase analysis: `trading/src/`, `trading/core/`, `trading/personal/` -- HIGH confidence, direct code review
