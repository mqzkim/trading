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

### Active

- [ ] Fix DuckDB/SQLite scoring store mismatch (screener integration)
- [ ] Add missing CLI commands (ingest, generate-plan, backtest)
- [ ] Wire G-Score blending and regime adjustment in DDD handler path
- [ ] Publish domain events to EventBus (currently defined but unused)
- [ ] Live data pipeline validation with real APIs
- [ ] Korean market support (KOSPI/KOSDAQ)

### Out of Scope

- Full auto-execution — requires paper trading validation first
- Web/GUI dashboard — CLI first, Streamlit/Next.js in future version
- Real-time intraday trading — daily granularity for mid-term holding
- Options/derivatives — stock-only
- Social/sentiment scoring — focus on fundamentals first

## Context

Shipped v1.0 MVP with 20,357 LOC Python across 4 bounded contexts (data_ingest, scoring, signals, portfolio + execution).
Tech stack: Python 3.12, DuckDB (analytics), SQLite (operational), yfinance + edgartools (data), Alpaca (broker), Typer + Rich (CLI).
DDD architecture with domain VOs, async event bus, and adapter pattern wrapping core/ functions.
352+ behavioral tests passing. 16 tech debt items documented in milestone audit.
Legacy core/ path provides working alternatives where DDD path has wiring gaps.

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

---
*Last updated: 2026-03-12 after v1.0 milestone*
