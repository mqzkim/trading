# Roadmap: Intrinsic Alpha Trader

## Overview

From raw market data to risk-controlled trade execution in 4 phases. The pipeline follows the strict dependency chain: data ingestion feeds scoring, scoring feeds valuation, valuation feeds signals, signals feed risk-sized execution. Each phase delivers a verifiable, standalone capability that the next phase builds on. The CLI interface is integrated into the final phase alongside execution because neither is useful without the other -- a dashboard without trade plans is empty, and trade plans without a dashboard are invisible.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (e.g., 2.1): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Data Foundation** - Data ingestion pipeline with point-in-time awareness, dual-DB storage, and DDD shared kernel (completed 2026-03-12)
- [x] **Phase 2: Analysis Core** - Scoring engine (safety gates + composite) and valuation ensemble (DCF + EPV + relative multiples) (completed 2026-03-12)
- [x] **Phase 3: Decision Engine** - Signal generation, risk management, position sizing, and backtesting validation (completed 2026-03-12)
- [x] **Phase 4: Execution and Interface** - Trade plans, human approval, Alpaca paper trading, CLI dashboard, and monitoring (completed 2026-03-12)

## Phase Details

### Phase 1: Data Foundation
**Goal**: Users can ingest, store, and query reliable US equity data (price + fundamentals) with point-in-time correctness
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, SCOR-01, SCOR-02, SCOR-03, SCOR-04
**Success Criteria** (what must be TRUE):
  1. Running the data pipeline for a ticker returns 3+ years of daily OHLCV data and at least 3 years of quarterly financial statements
  2. All financial data is tagged with filing dates (not period-end dates), preventing look-ahead bias in any downstream query
  3. Data quality checks flag missing values, stale data, and outliers with a summary report before any data is consumed downstream
  4. Querying DuckDB for analytical workloads (screen 500+ tickers) completes in under 30 seconds; SQLite stores operational state (watchlists, logs)
  5. Safety gates (Altman Z-Score > 1.81 AND Beneish M-Score < -1.78) correctly filter out distressed/manipulative companies, and individual Piotroski F-Score and Altman Z-Score calculations match known reference values for test tickers
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Domain VOs, DuckDB/SQLite stores, async event bus, dependency install
- [x] 01-02-PLAN.md — YFinance adapter, edgartools SEC client, universe provider, quality checker
- [x] 01-03-PLAN.md — Core scoring adapter (F/Z/M-Score), end-to-end data pipeline

### Phase 2: Analysis Core
**Goal**: Users can score any US equity on fundamental quality and estimate its intrinsic value through an ensemble of valuation models
**Depends on**: Phase 1
**Requirements**: SCOR-05, SCOR-06, VALU-01, VALU-02, VALU-03, VALU-04, VALU-05
**Success Criteria** (what must be TRUE):
  1. Mohanram G-Score (0-8) calculates correctly for growth stocks, and the composite score (0-100) produces a single quality ranking that combines all four scoring models with configurable weights
  2. DCF model produces intrinsic value estimates with terminal value capped at 40% of total value, and results are within reasonable range for known test tickers
  3. EPV model produces normalized earnings-based valuations independent of growth assumptions
  4. Relative multiples (PER/PBR/EV-EBITDA) compare each stock against its sector peers, flagging those trading below sector median
  5. Ensemble valuation (DCF 40% + EPV 35% + Relative 25%) produces a single intrinsic value with confidence score, and margin of safety calculation correctly identifies stocks trading 20%+ below intrinsic value
**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md — G-Score (SCOR-05) + composite score update with regime interface (SCOR-06)
- [x] 02-02-PLAN.md — Valuation domain VOs/events + DCF/EPV/Relative pure math (VALU-01, VALU-02, VALU-03)
- [x] 02-03-PLAN.md — Ensemble valuation + margin of safety + infrastructure wiring (VALU-04, VALU-05)

### Phase 3: Decision Engine
**Goal**: Users can generate ranked buy/hold/sell signals backed by validated positive expectancy, with mathematically sized positions and portfolio-level risk controls
**Depends on**: Phase 2
**Requirements**: SIGN-01, SIGN-02, RISK-01, RISK-02, RISK-03, RISK-04, RISK-05, BACK-01, BACK-02
**Success Criteria** (what must be TRUE):
  1. Signal engine produces BUY/HOLD/SELL recommendations combining quality score and valuation gap, each with a plain-text reasoning trace citing specific data points
  2. Screener ranks the universe by composite score and filters by signal, producing a Top N list a user can review
  3. Fractional Kelly (1/4 Kelly) position sizing calculates optimal position size per stock, ATR-based stop-loss sets trailing stops at 2.5-3.5x ATR(21), and take-profit levels derive from intrinsic value targets
  4. Portfolio-level drawdown defense activates at 10%/15%/20% tiers with predefined responses, and hard limits enforce max 8% per position and 25% per sector
  5. Walk-forward backtesting validates strategy on out-of-sample data, producing a performance report with Sharpe ratio, max drawdown, win rate, and profit factor
**Plans:** 3 plans

Plans:
- [x] 03-01-PLAN.md — Signal engine with reasoning traces + DuckDB screener/ranker (SIGN-01, SIGN-02)
- [x] 03-02-PLAN.md — Risk management: CoreRiskAdapter, take-profit levels, sector limits (RISK-01 through RISK-05)
- [x] 03-03-PLAN.md — Backtest bounded context: walk-forward validation + performance reports (BACK-01, BACK-02)

### Phase 4: Execution and Interface
**Goal**: Users can review trade plans, approve orders through CLI, execute via Alpaca paper trading, and monitor positions through an interactive dashboard
**Depends on**: Phase 3
**Requirements**: EXEC-01, EXEC-02, EXEC-03, EXEC-04, INTF-01, INTF-02, INTF-03, INTF-04
**Success Criteria** (what must be TRUE):
  1. Trade plan generation produces structured plans with entry price, stop-loss, take-profit, position size, and reasoning -- all traceable back to scoring and valuation outputs
  2. Human approval CLI presents each pending trade plan and requires explicit Y/N confirmation (with option to modify parameters) before any order is sent
  3. Approved orders execute as bracket orders (entry + stop-loss + take-profit) on Alpaca paper trading, with execution status tracked and logged
  4. CLI dashboard displays portfolio overview (positions, P&L, drawdown status) and stock screener allows interactive filtering/ranking by score
  5. Watchlist management (add/remove/list) and monitoring alerts (stop hit, target reached, drawdown tier change) notify the user of actionable events
**Plans:** 3/3 plans complete

Plans:
- [x] 04-01-PLAN.md — Execution bounded context: TradePlan/BracketSpec VOs, TradePlanService, AlpacaExecutionAdapter with mock fallback (EXEC-01, EXEC-03, EXEC-04)
- [x] 04-02-PLAN.md — CLI dashboard, stock screener, watchlist management (INTF-01, INTF-02, INTF-03)
- [x] 04-03-PLAN.md — Human approval workflow, monitoring alerts, execution wiring (EXEC-02, INTF-04)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 3/3 | Complete | 2026-03-12 |
| 2. Analysis Core | 3/3 | Complete | 2026-03-12 |
| 3. Decision Engine | 3/3 | Complete | 2026-03-12 |
| 4. Execution and Interface | 3/3 | Complete   | 2026-03-12 |
