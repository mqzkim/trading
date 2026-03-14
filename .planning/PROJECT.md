# Intrinsic Alpha Trader

## What This Is

AI-assisted mid-term trading system that identifies undervalued US companies through fundamental scoring (F/Z/M/G-Score), ensemble valuation (DCF + EPV + Relative), and rule-based signal generation — then produces risk-controlled trade plans with human approval, Alpaca paper trading execution, and interactive CLI dashboard. Built on DDD architecture with full explainability chain from raw data to trade execution.

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

### Active

- [ ] Pipeline stabilization and tech debt resolution (DDD wiring, store mismatch, failed runs)
- [ ] Technical scoring axis (RSI/MACD/MA/ADX/OBV) integrated into composite score
- [ ] Regime detection enhancement (VIX/yield curve/HMM-based)
- [ ] Sentiment scoring (news sentiment, insider trades, institutional holdings, analyst revisions)
- [ ] Performance attribution (4-level P&L decomposition)
- [ ] Self-improver (parameter optimization from performance analysis)
- [ ] Commercial REST API (QuantScore/RegimeRadar/SignalFusion with auth/billing/rate-limiting)
- [ ] Dashboard enhancement (real data display, new feature UIs)

### Out of Scope

- Full auto-execution without any human oversight — strategy/budget approval still required
- Mobile app — web dashboard first
- Real-time intraday trading — daily granularity for mid-term holding
- Options/derivatives — stock-only
- Korean market (KIS broker) — deferred, may require Korean brokerage account

## Current Milestone: v1.4 Full Stack Trading Platform

**Goal:** Complete the trading system with technical/sentiment scoring, regime enhancement, commercial API, performance analysis, and self-improvement loop — transforming from MVP to production-grade platform.

**Target features:**
- Pipeline stabilization + tech debt resolution
- Technical & sentiment scoring axes
- Enhanced regime detection
- Commercial FastAPI REST API (3 products)
- Performance analyst + self-improver
- Dashboard with real data

## Current State

Shipped v1.3 Bloomberg Dashboard (2026-03-14). Starting v1.4 Full Stack Trading Platform.

## Context

Shipped v1.3 Bloomberg Dashboard with 13,008 LOC Python + 2,430 LOC TypeScript across 4 bounded contexts + Next.js dashboard.
Tech stack: Python 3.12, DuckDB (analytics), SQLite (operational), yfinance + edgartools (data), Alpaca (broker), Typer + Rich (CLI), Next.js 16 + React + TanStack Query + shadcn/ui (dashboard).
DDD architecture with domain VOs, async event bus, and adapter pattern wrapping core/ functions.
Bloomberg terminal-style dark theme dashboard with TradingView charts and SSE real-time updates.
352+ behavioral tests passing. Legacy core/ path provides working alternatives where DDD path has wiring gaps.

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
| Python-centric stack | Best ecosystem for financial analysis | ✓ Good — 20K LOC in 10 days |
| Daily screening granularity | Mid-term holding period doesn't need intraday data | ✓ Good — simplifies data pipeline |
| Fractional Kelly + ATR for position sizing | Mathematically grounded, prevents over-concentration | ✓ Good — conservative 1/4 Kelly appropriate |
| DDD architecture with bounded contexts | Clean separation of concerns, testable domains | ⚠️ Revisit — cross-context wiring gaps need fixing |
| DuckDB for analytics + SQLite for operational | Separation of analytical and transactional workloads | ⚠️ Revisit — scoring store mismatch needs resolution |
| core/ wrapper + DDD adapter pattern | Reuse existing scoring/signal math without rewriting | ✓ Good — reduced implementation time significantly |
| Coarse 4-phase roadmap | Strict dependency chain, each phase standalone | ✓ Good — clean execution, 12 plans in 10 days |

| Next.js 16 + React for dashboard | HTMX+Jinja2 too limited for Bloomberg-style data density and interactions | ✓ Good — professional UI with 2,430 LOC TypeScript |
| TradingView Lightweight Charts | Professional trading charts with candlestick, indicators, real-time | ✓ Good — equity curve with regime overlay works well |
| BFF proxy via next.config.ts rewrites | Avoid direct DB access from Node.js, single proxy point | ✓ Good — clean separation, SSE proxied without buffering |
| Biome 2.x replacing ESLint+Prettier | Next.js 16 removed next lint, Biome faster and simpler | ✓ Good — single tool for lint+format |
| CSS conic-gradient for visualizations | No chart library needed for gauges and donuts | ✓ Good — zero dependencies for risk visualizations |
| EventSource-to-TanStack-Query mapping | Native browser API, no WebSocket library needed | ✓ Good — simple and reliable real-time updates |

---
*Last updated: 2026-03-14 after v1.3 milestone completion*
