# Roadmap: Intrinsic Alpha Trader

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-03-12)
- ✅ **v1.1 Stabilization & Expansion** — Phases 5-11 (shipped 2026-03-12)
- ✅ **v1.2 Production Trading & Dashboard** — Phases 12-20 (shipped 2026-03-14)
- ✅ **v1.3 Bloomberg Dashboard** — Phases 21-25 (shipped 2026-03-14)
- 📋 **v1.4 Full Stack Trading Platform** — Phases 26-29 (planned)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-03-12</summary>

Delivered: End-to-end quantitative trading system from raw data ingestion through risk-controlled trade execution.

</details>

<details>
<summary>✅ v1.1 Stabilization & Expansion (Phases 5-11) — SHIPPED 2026-03-12</summary>

Delivered: Tech debt fixes, live data, technical scoring, regime detection, signal fusion, Korean broker, commercial API.

</details>

<details>
<summary>✅ v1.2 Production Trading & Dashboard (Phases 12-20) — SHIPPED 2026-03-14</summary>

Delivered: Safety infrastructure, automated pipeline, strategy approval, live trading, HTMX dashboard, SSE events, drawdown defense.

</details>

<details>
<summary>✅ v1.3 Bloomberg Dashboard (Phases 21-25) — SHIPPED 2026-03-14</summary>

- [x] Phase 21: Foundation (2/2 plans) — completed 2026-03-14
- [x] Phase 22: Design System & Overview Page (2/2 plans) — completed 2026-03-14
- [x] Phase 23: Signals, Risk & Pipeline Pages (3/3 plans) — completed 2026-03-14
- [x] Phase 24: Real-Time & Integration (1/1 plan) — completed 2026-03-14
- [x] Phase 25: Cleanup (1/1 plan) — completed 2026-03-14

Delivered: Bloomberg terminal-style React dashboard with TradingView charts, data-dense dark theme, SSE real-time updates, 4 redesigned pages, legacy HTMX/Plotly removed.

</details>

### v1.4 Full Stack Trading Platform (In Progress)

**Milestone Goal:** Complete the trading system with technical/sentiment scoring, regime enhancement, commercial API, performance analysis, and self-improvement loop -- transforming from MVP to production-grade platform.

- [ ] **Phase 26: Pipeline Stabilization** - Fix DDD wiring gaps, unify scoring stores, verify event bus, populate real prices
- [ ] **Phase 27: Scoring Expansion** - Technical indicators (RSI/MACD/MA/ADX/OBV) and sentiment scoring (news/insider/institutional/analyst) integrated into composite
- [ ] **Phase 28: Commercial API & Dashboard** - Three API products (QuantScore/RegimeRadar/SignalFusion) with auth/rate-limiting, plus dashboard updates showing new scoring and regime data
- [ ] **Phase 29: Performance & Self-Improvement** - Trade P&L tracking, Brinson-Fachler attribution, signal validation, and propose-then-approve parameter optimization

## Phase Details

### Phase 26: Pipeline Stabilization
**Goal**: Pipeline runs reliably end-to-end through DDD path with unified data stores and verified event delivery
**Depends on**: Nothing (first phase of v1.4)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06
**Success Criteria** (what must be TRUE):
  1. Running the daily pipeline (screening -> scoring -> signal -> execution) completes without errors and produces scored results
  2. Scoring data lives in a single store -- querying scores from the screener returns the same data the scoring engine wrote
  3. Domain events (e.g., ScoringCompletedEvent) are published by producers and received by consumers through the EventBus
  4. Trade plans show a real target_price from the valuation engine and a current_price from latest market data (not 0.0 or entry_price)
  5. All pipeline operations route through src/ DDD path; legacy core/ wrappers are fallback only
**Plans**: 2 plans

Plans:
- [ ] 26-01-PLAN.md — Unify scoring store, wire event bus, inject DDD adapters
- [ ] 26-02-PLAN.md — Wire real prices (current_price, target_price) and verify pipeline E2E

### Phase 27: Scoring Expansion
**Goal**: Composite score reflects three real axes -- fundamental (existing), technical (5 indicators), and sentiment (4 data sources) -- with proper normalization and confidence tracking
**Depends on**: Phase 26 (needs working pipeline and event bus)
**Requirements**: TECH-01, TECH-02, TECH-03, TECH-04, TECH-05, TECH-06, TECH-07, SENT-01, SENT-02, SENT-03, SENT-04, SENT-05, SENT-06
**Success Criteria** (what must be TRUE):
  1. Running the screener produces a TechnicalScore with real RSI/MACD/MA/ADX/OBV sub-scores (not defaults) for every scored stock
  2. Running the screener produces a SentimentScore with real news/insider/institutional/analyst sub-scores and a confidence indicator showing data freshness
  3. MACD normalization works correctly across all price ranges (not hardcoded [-5,+5])
  4. Composite score reflects configurable 3-axis weights (fundamental + technical + sentiment) and when sentiment confidence is NONE, weights re-normalize to fundamental + technical only
  5. SentimentUpdatedEvent flows from sentiment context to scoring context via EventBus
**Plans**: TBD

Plans:
- [ ] 27-01: TBD
- [ ] 27-02: TBD
- [ ] 27-03: TBD

### Phase 28: Commercial API & Dashboard
**Goal**: Three commercial API products serve real 3-axis scoring data behind authentication and rate limiting, and the dashboard displays all new scoring and regime data
**Depends on**: Phase 27 (needs complete 3-axis scoring to sell)
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, API-07, DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. Calling /api/v1/quantscore/{ticker} with a valid API key returns composite score with fundamental/technical/sentiment sub-component breakdown
  2. Calling /api/v1/regime with a valid API key returns current market regime with probability and indicator values
  3. Calling /api/v1/signals with a valid API key returns consensus signals with reasoning traces
  4. Requests without a valid JWT are rejected with 401; requests exceeding tier rate limits are rejected with 429; all responses include legal disclaimer
  5. Dashboard Signals page shows technical and sentiment sub-scores; a Performance Attribution page exists; all pages display real data when available; regime view shows enhanced HMM probabilities
**Plans**: TBD

Plans:
- [ ] 28-01: TBD
- [ ] 28-02: TBD
- [ ] 28-03: TBD

### Phase 29: Performance & Self-Improvement
**Goal**: System tracks trade performance with 4-level attribution, validates signal quality, and proposes parameter improvements (with human approval) after sufficient trade history
**Depends on**: Phase 28 (needs trade history accumulation and dashboard for attribution display)
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04, PERF-05, SELF-01, SELF-02, SELF-03, SELF-04
**Success Criteria** (what must be TRUE):
  1. Every closed trade has P&L tracked with entry/exit prices, dates, and the decision context snapshot (composite score, regime, weights) captured at entry time
  2. Performance report shows 4-level Brinson-Fachler decomposition (portfolio/strategy/trade/skill) with Sharpe, Sortino, win rate, and max drawdown
  3. Signal IC (information coefficient) is computed and compared against 0.03 threshold; Kelly efficiency is computed and compared against 70% threshold
  4. After 50+ trades, the system generates parameter adjustment proposals with walk-forward validation results, and no changes apply without explicit human approval
**Plans**: TBD

Plans:
- [ ] 29-01: TBD
- [ ] 29-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 26 -> 27 -> 28 -> 29

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-4 | v1.0 | 12/12 | Complete | 2026-03-12 |
| 5-11 | v1.1 | 17/17 | Complete | 2026-03-12 |
| 12-20 | v1.2 | 20/20 | Complete | 2026-03-14 |
| 21-25 | v1.3 | 9/9 | Complete | 2026-03-14 |
| 26. Pipeline Stabilization | v1.4 | 0/2 | Not started | - |
| 27. Scoring Expansion | v1.4 | 0/? | Not started | - |
| 28. Commercial API & Dashboard | v1.4 | 0/? | Not started | - |
| 29. Performance & Self-Improvement | v1.4 | 0/? | Not started | - |
