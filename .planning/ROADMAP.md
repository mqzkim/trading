# Roadmap: Intrinsic Alpha Trader

## Milestones

- ✅ **v1.0 MVP** -- Phases 1-4 (shipped 2026-03-12)
- 🚧 **v1.1 Stabilization & Expansion** -- Phases 5-11 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) -- SHIPPED 2026-03-12</summary>

- [x] Phase 1: Data Foundation (3/3 plans) -- completed 2026-03-12
- [x] Phase 2: Analysis Core (3/3 plans) -- completed 2026-03-12
- [x] Phase 3: Decision Engine (3/3 plans) -- completed 2026-03-12
- [x] Phase 4: Execution and Interface (3/3 plans) -- completed 2026-03-12

Full details: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

### 🚧 v1.1 Stabilization & Expansion

**Milestone Goal:** Stabilize v1.0 tech debt, validate with live data, and expand with technical scoring, regime detection, multi-strategy signal fusion, Korean market support, and commercial API products.

- [x] **Phase 5: Tech Debt & Infrastructure Foundation** - Resolve 16 tech debt items, build event bus + composition root + DB factory
- [ ] **Phase 6: Live Data Pipeline & Korean Data** - Validate US live data, add data quality layer, build Korean market data adapter
- [ ] **Phase 7: Technical Scoring Engine** - Integrate 5 technical indicators into DDD scoring, combine with fundamental scores
- [ ] **Phase 8: Market Regime Detection** - Wire regime classifier with live data, publish regime events, auto-adjust scoring weights
- [ ] **Phase 9: Multi-Strategy Signal Fusion** - Implement 4 strategies, build consensus engine, add regime-weighted aggregation
- [ ] **Phase 10: Korean Broker Integration** - KIS broker adapter with paper trading, KRW currency handling
- [ ] **Phase 11: Commercial FastAPI REST API** - QuantScore + RegimeRadar + SignalFusion endpoints with JWT auth and rate limiting

## Phase Details

### Phase 5: Tech Debt & Infrastructure Foundation
**Goal**: The system's internal architecture is clean, testable, and ready for feature expansion -- event bus connects all contexts, no God Orchestrator, no cross-context import violations
**Depends on**: Phase 4 (v1.0 complete)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07, INFRA-08, INFRA-09
**Success Criteria** (what must be TRUE):
  1. All 4 bounded contexts communicate via SyncEventBus -- no direct cross-context imports remain
  2. Application bootstraps through a single Composition Root -- the God Orchestrator (core/orchestrator.py) is no longer the entry point
  3. CLI commands `ingest`, `generate-plan`, and `backtest` execute end-to-end and produce visible output
  4. Screener queries return scored results with valuations -- the DuckDB/SQLite store mismatch is resolved
  5. G-Score blending and regime adjustment produce different composite scores when toggled on/off via CLI
**Plans:** 3 plans

Plans:
- [x] 05-01-PLAN.md -- SyncEventBus + DBFactory + Composition Root (infrastructure primitives)
- [x] 05-02-PLAN.md -- DuckDB screener fix, cross-context import fix, G-Score wiring, event creation
- [x] 05-03-PLAN.md -- Missing CLI commands (ingest, generate-plan, backtest) + event bus wiring

### Phase 6: Live Data Pipeline & Korean Data
**Goal**: Users can ingest real market data from live APIs (yfinance, SEC EDGAR, pykrx) with automatic quality validation, for both US and Korean equities
**Depends on**: Phase 5
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06
**Success Criteria** (what must be TRUE):
  1. `ingest` CLI command fetches live OHLCV + financials from yfinance and SEC EDGAR for a given US ticker, with adjusted close values matching the source
  2. Data quality layer detects and reports missing values, outliers, and stale data before any scoring proceeds
  3. `ingest --market kr` fetches KOSPI/KOSDAQ OHLCV and fundamentals (PER/PBR/DIV) from pykrx for a given Korean ticker
  4. Regime detection data sources (VIX, S&P 500 index, yield curve) are ingested and stored in the analytics DB
**Plans:** 3 plans

Plans:
- [ ] 06-01-PLAN.md -- Fix edgartools ticker bug, extend Ticker/Symbol VOs for Korean format, business-day staleness
- [ ] 06-02-PLAN.md -- pykrx Korean market adapter, DuckDB kr_fundamentals table, pipeline --market kr, CLI wiring
- [ ] 06-03-PLAN.md -- Regime data client (VIX/S&P500/yield), DuckDB regime_data table, CLI ingest --regime

### Phase 7: Technical Scoring Engine
**Goal**: Users see a composite score that blends fundamental quality with technical momentum -- each sub-score is individually visible and explained
**Depends on**: Phase 6
**Requirements**: TECH-01, TECH-02, TECH-03, TECH-04
**Success Criteria** (what must be TRUE):
  1. CLI `score` command shows 5 individual technical indicator scores (RSI, MACD, MA, ADX, OBV) with plain-text explanations for each
  2. Technical composite score (0-100) is computed from the 5 indicators with configurable weights
  3. Overall CompositeScore now combines fundamental (40%), technical (40%), and sentiment (20% placeholder) sub-scores
  4. Scoring a ticker with strong fundamentals but bearish technicals produces a visibly lower composite than one with aligned signals
**Plans:** 2 plans

Plans:
- [ ] 07-01-PLAN.md -- TechnicalScore VO extension, TechnicalScoringService domain service, STRATEGY_WEIGHTS 40/40/20, infrastructure adapter
- [ ] 07-02-PLAN.md -- Wire TechnicalScoringService into handler, CLI score sub-score display with explanations

### Phase 8: Market Regime Detection
**Goal**: The system knows the current market regime (Bull/Bear/Sideways/Crisis) and automatically adjusts its behavior -- scoring weights shift, signals adapt, and users can see regime history
**Depends on**: Phase 6
**Requirements**: REGIME-01, REGIME-02, REGIME-03, REGIME-04, REGIME-05
**Success Criteria** (what must be TRUE):
  1. CLI `regime` command displays the current market regime with confidence level and the data points that determined it
  2. Regime changes require 3 consecutive days of confirmation before the system transitions -- premature flips are suppressed
  3. RegimeChangedEvent is published to EventBus and consumed by scoring context to adjust weights
  4. CLI `regime --history 90` shows regime transitions over the past 90 days with dates and durations
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

### Phase 9: Multi-Strategy Signal Fusion
**Goal**: Users receive consensus-based trade signals where 4 independent strategies vote, weighted by current market regime -- with full reasoning for every recommendation
**Depends on**: Phase 7, Phase 8
**Requirements**: SIGNAL-01, SIGNAL-02, SIGNAL-03, SIGNAL-04, SIGNAL-05, SIGNAL-06, SIGNAL-07
**Success Criteria** (what must be TRUE):
  1. Each of the 4 strategies (CAN SLIM, Magic Formula, Dual Momentum, Trend Following) independently produces BUY/HOLD/SELL for a given ticker with strategy-specific reasoning
  2. Consensus engine outputs a fused signal with agreement level (e.g., "3/4 strategies agree: BUY") and overall confidence
  3. In Bear regime, quality/value strategies receive higher weight; in Bull regime, momentum strategies receive higher weight -- and the weighting is visible in output
  4. CLI `signal` command shows per-strategy breakdown, regime-adjusted weights, and the final fused recommendation with full reasoning chain
**Plans**: TBD

Plans:
- [ ] 09-01: TBD
- [ ] 09-02: TBD
- [ ] 09-03: TBD

### Phase 10: Korean Broker Integration
**Goal**: Users can execute paper trades on KOSPI/KOSDAQ through the KIS broker with the same risk controls and approval workflow as US equities
**Depends on**: Phase 6
**Requirements**: KR-01, KR-02, KR-03
**Success Criteria** (what must be TRUE):
  1. KIS broker adapter implements IBrokerRepository and connects to KIS paper trading environment
  2. Trade plans for Korean stocks show position sizes in KRW with proper lot sizing (Korean market minimums)
  3. The full workflow (score -> signal -> plan -> approve -> execute) works end-to-end for a KOSPI ticker in paper trading mode
**Plans**: TBD

Plans:
- [ ] 10-01: TBD

### Phase 11: Commercial FastAPI REST API
**Goal**: External users can query QuantScore, RegimeRadar, and SignalFusion through authenticated REST endpoints with tiered rate limiting and legal disclaimers
**Depends on**: Phase 7, Phase 8, Phase 9
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06
**Success Criteria** (what must be TRUE):
  1. `GET /api/v1/quantscore/{ticker}` returns composite score breakdown with sub-scores and a legal disclaimer
  2. `GET /api/v1/regime/current` returns current regime with confidence, and `/api/v1/regime/history` returns transition history
  3. `GET /api/v1/signals/{ticker}` returns consensus signal with per-strategy votes -- but never includes position sizing or buy/sell recommendations (information only)
  4. Requests without valid JWT are rejected; free-tier users are rate-limited more aggressively than pro-tier users
  5. API key management endpoint allows creating, revoking, and listing API keys
**Plans**: TBD

Plans:
- [ ] 11-01: TBD
- [ ] 11-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11
Note: Phases 7 and 8 both depend on Phase 6 (not on each other). Phase 9 depends on both 7 and 8. Phase 10 depends on Phase 6 only.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Foundation | v1.0 | 3/3 | Complete | 2026-03-12 |
| 2. Analysis Core | v1.0 | 3/3 | Complete | 2026-03-12 |
| 3. Decision Engine | v1.0 | 3/3 | Complete | 2026-03-12 |
| 4. Execution and Interface | v1.0 | 3/3 | Complete | 2026-03-12 |
| 5. Tech Debt & Infrastructure Foundation | v1.1 | 3/3 | Complete | 2026-03-12 |
| 6. Live Data Pipeline & Korean Data | 1/3 | In Progress|  | - |
| 7. Technical Scoring Engine | v1.1 | 0/2 | Not started | - |
| 8. Market Regime Detection | v1.1 | 0/2 | Not started | - |
| 9. Multi-Strategy Signal Fusion | v1.1 | 0/3 | Not started | - |
| 10. Korean Broker Integration | v1.1 | 0/1 | Not started | - |
| 11. Commercial FastAPI REST API | v1.1 | 0/2 | Not started | - |
