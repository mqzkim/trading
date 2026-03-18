# Intrinsic Alpha Trader

## What This Is

AI-assisted mid-term trading system that identifies undervalued US companies through 3-axis scoring (fundamental F/Z/M/G-Score + technical RSI/MACD/MA/ADX/OBV + sentiment news/insider/institutional/analyst), ensemble valuation (DCF + EPV + Relative), and rule-based signal generation — then produces risk-controlled trade plans with human approval, Alpaca live trading execution, Bloomberg-style dashboard, commercial REST API (QuantScore/RegimeRadar/SignalFusion), and Brinson-Fachler performance attribution. Built on DDD architecture with full explainability chain from raw data to trade execution.

## Core Value

Every recommendation must be explainable and risk-controlled — the system prioritizes capital preservation and positive expectancy over maximizing returns.

## Requirements

### Validated

- ✓ Data ingestion pipeline for US market (OHLCV, financials, SEC filings) — v1.0
- ✓ Fundamental scoring engine (Piotroski F-Score, Altman Z-Score, Beneish M-Score, Mohanram G-Score) — v1.0
- ✓ Safety gates (Z > 1.81, M < -1.78) filtering distressed/manipulative companies — v1.0
- ✓ Composite scoring (0-100) with configurable weights — v1.0
- ✓ Valuation engine with ensemble model (DCF 40% + EPV 35% + Relative 25%) — v1.0
- ✓ Margin of safety calculation (20%+ threshold) — v1.0
- ✓ Signal engine combining quality score + valuation gap with reasoning traces — v1.0
- ✓ Risk management engine (Fractional Kelly 1/4 + 3-tier drawdown defense) — v1.0
- ✓ ATR-based stop-loss (2.5-3.5x ATR(21)) and take-profit levels — v1.0
- ✓ Position/sector hard limits (8% position, 25% sector) — v1.0
- ✓ Walk-forward backtesting with performance reports — v1.0
- ✓ Alpaca broker integration (Paper Trading) with bracket orders — v1.0
- ✓ CLI dashboard with portfolio view, screener, and watchlist — v1.0
- ✓ Trade plan generation with entry/stop/target/size/reasoning — v1.0
- ✓ Human approval workflow before order execution — v1.0
- ✓ Monitoring alerts (stop hit, target reached, drawdown tier change) — v1.0
- ✓ Daily automated screening → scoring → signal → execution pipeline — v1.2
- ✓ Strategy/budget approval workflow (human approves strategy + daily budget) — v1.2
- ✓ Scheduler daemon (APScheduler + market calendar) — v1.2
- ✓ Alpaca live account integration (paper → live migration) — v1.2
- ✓ Auto-execution within approved budget/risk limits — v1.2
- ✓ Real-time order monitoring and error recovery — v1.2
- ✓ Web Dashboard HTMX (portfolio, scoring, signals, risk, pipeline) — v1.2
- ✓ Kill switch, cooldown, circuit breaker safety infrastructure — v1.2
- ✓ SSE real-time event wiring — v1.2
- ✓ Drawdown defense wiring (3-tier auto-suspension) — v1.2
- ✓ Next.js 16 + React Bloomberg dashboard with BFF proxy architecture — v1.3
- ✓ Bloomberg OKLCH dark theme design system with shadcn/ui — v1.3
- ✓ TradingView Lightweight Charts equity curve with regime overlay — v1.3
- ✓ 4-page dashboard (Overview, Signals, Risk, Pipeline) with data-dense layout — v1.3
- ✓ SSE real-time updates via EventSource-to-TanStack-Query mapping — v1.3
- ✓ Legacy HTMX/Jinja2/Plotly complete removal — v1.3
- ✓ Pipeline stabilization (DDD event bus, unified SQLite/DuckDB stores, real prices) — v1.4
- ✓ Technical scoring axis (RSI/MACD ATR-norm/MA golden-death cross/ADX/OBV) — v1.4
- ✓ Sentiment scoring (Alpaca+VADER news, yfinance insider/institutional/analyst + SentimentConfidence) — v1.4
- ✓ 3-axis composite score with confidence-aware weight renormalization — v1.4
- ✓ Commercial REST API — QuantScore (sub-score breakdown) / RegimeRadar (probabilities) / SignalFusion (reasoning traces) — v1.4
- ✓ JWT auth + tier-based rate limiting + legal disclaimer on all commercial endpoints — v1.4
- ✓ Dashboard: expandable signal rows (F/T/S breakdown), regime probability bars, 5-link nav — v1.4
- ✓ Performance DDD context: Brinson-Fachler 4-level attribution, IC (Spearman ≥ 0.03), Kelly efficiency (≥ 70%) — v1.4
- ✓ Self-improver DDD: 50-trade threshold + walk-forward validation + propose-then-approve workflow — v1.4

### Active (Known Gaps from v1.4 — Next Milestone)

- [ ] **signal_direction propagation** — Position.close() never sets signal_direction; IC calculation always returns None (PERF-03/04)
- [ ] **Proposal trigger** — proposal_gen_handler has no caller; self-improvement never fires automatically (SELF-02)
- [ ] **sentiment_confidence persistence** — scored_symbols SQLite table missing column; dashboard always shows "NONE" (DASH-01)
- [ ] **Phase 26 formal verification** — VERIFICATION.md never written; pipeline wiring confirmed correct by integration checker but artifact missing
- [ ] **Nyquist validation** — Phases 26/27 missing VALIDATION.md; Phase 28 VALIDATION.md not completed

### Out of Scope

- Full auto-execution without any human oversight — strategy/budget approval still required
- Mobile app — web dashboard first
- Real-time intraday trading — daily granularity for mid-term holding
- Options/derivatives — stock-only
- Korean market (KIS broker) — deferred, may require Korean brokerage account
- FinBERT upgrade for news sentiment — VADER accuracy 56% on financial headlines acceptable for now

## Current State

Shipped v1.4 Full Stack Trading Platform (2026-03-18). 5 complete milestones. ~209,832 LOC total.

**System capabilities:**
- Full 3-axis scoring pipeline (fundamental + technical + sentiment) running end-to-end
- Commercial API serving real scoring data to external consumers
- Bloomberg-style dashboard with live data, real-time SSE updates, and performance attribution page
- Brinson-Fachler attribution framework in place (needs 50+ trades to activate self-improvement)

**Known gaps carried to next milestone:** IC calculation broken (signal_direction not propagated), proposal trigger missing, sentiment_confidence not persisted. See `.planning/milestones/v1.4-MILESTONE-AUDIT.md`.

## Context

~209,832 LOC Python + TypeScript across 5 bounded contexts (scoring, pipeline, portfolio, regime, performance) + personal/ self-improver + commercial/ FastAPI + Next.js 16 dashboard.
Tech stack: Python 3.12, DuckDB (analytics), SQLite (operational), yfinance + edgartools + Alpaca News (data), Alpaca (broker), Typer + Rich (CLI), Next.js 16 + React + TanStack Query + shadcn/ui (dashboard), FastAPI (commercial API), scipy (IC calculation).
DDD architecture with domain VOs, sync event bus, adapter pattern, and BFF proxy architecture.
Bloomberg terminal-style dark theme dashboard with TradingView charts, SSE real-time updates, expandable data tables.
352+ behavioral tests passing.

## Constraints

- **Explainability**: Every score, signal, and recommendation must trace back to specific data points
- **Risk-first**: No position without defined stop-loss; drawdown defense protocol (10/15/20% tiers)
- **Paper-first**: All strategies must pass paper trading validation before live consideration
- **Human-in-the-loop**: Requires explicit human approval before any order
- **Data reliability**: Free data sources (yfinance, SEC EDGAR) preferred; paid APIs only if free sources insufficient
- **Tech stack**: Python-centric (pandas, DuckDB, SQLite, Typer CLI)
- **Positive expectancy**: System must demonstrate statistical edge via backtesting before deployment

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| US market only for MVP | Data accessibility highest, Alpaca supports US | ✓ Good — focused scope enabled 10-day delivery |
| CLI-based dashboard | Fastest to build, matches terminal workflow | ✓ Good — Typer+Rich dashboard works well |
| Valuation ensemble (DCF+EPV+Relative) | No single model is reliable alone; ensemble reduces model risk | ✓ Good — confidence scoring adds transparency |
| Alpaca for broker integration | Free API, Paper Trading built-in, good Python SDK | ✓ Good — mock fallback enables offline dev |
| Python-centric stack | Best ecosystem for financial analysis | ✓ Good — 20K+ LOC in 7 days |
| Daily screening granularity | Mid-term holding period doesn't need intraday data | ✓ Good — simplifies data pipeline |
| Fractional Kelly + ATR for position sizing | Mathematically grounded, prevents over-concentration | ✓ Good — conservative 1/4 Kelly appropriate |
| DDD architecture with bounded contexts | Clean separation of concerns, testable domains | ✓ Resolved — v1.4 fixed wiring gaps with adapter pattern |
| DuckDB for analytics + SQLite for operational | Separation of analytical and transactional workloads | ✓ Resolved — v1.4 unified scoring store with event-driven DuckDB sync |
| core/ wrapper + DDD adapter pattern | Reuse existing scoring/signal math without rewriting | ✓ Good — reduced implementation time significantly |
| Coarse 4-phase roadmap | Strict dependency chain, each phase standalone | ✓ Good — clean execution pattern across all milestones |
| Next.js 16 + React for dashboard | HTMX+Jinja2 too limited for Bloomberg-style data density | ✓ Good — professional UI with ~5K LOC TypeScript |
| TradingView Lightweight Charts | Professional trading charts with candlestick, indicators, real-time | ✓ Good — equity curve with regime overlay works well |
| BFF proxy via next.config.ts rewrites | Avoid direct DB access from Node.js, single proxy point | ✓ Good — clean separation, SSE proxied without buffering |
| MACD ATR-scaled normalization [-2×ATR21, +2×ATR21] | Hardcoded [-5,+5] range caused saturation at extreme values | ✓ Good — dynamic range prevents score saturation |
| SentimentConfidence.NONE triggers weight renorm | When sentiment data unavailable, 20% weight redistributed to fundamental+technical | ✓ Good — graceful degradation preserves scoring quality |
| Brinson-Fachler 4-level attribution | Industry standard, maps directly to scoring axes | ✓ Good — framework ready, needs trade history to activate |
| WalkForwardAdapter synthetic OHLCV conversion | run_walk_forward() requires OHLCV format; convert trade_returns at adapter boundary | ✓ Good — clean adapter isolation |
| proposal_gen_handler stored in ctx, no trigger | Wired but not called — no pipeline post-run hook implemented | ⚠️ Gap — SELF-02 deferred to next milestone |

---
*Last updated: 2026-03-18 after v1.4 milestone completion*
