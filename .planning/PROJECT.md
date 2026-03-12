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

#### Automated Pipeline
- [ ] Daily automated screening → scoring → signal → execution pipeline
- [ ] Strategy/budget approval workflow (human approves strategy + daily budget)
- [ ] Scheduler daemon (cron or persistent process)

#### Live Trading
- [ ] Alpaca live account integration (paper → live migration)
- [ ] Auto-execution within approved budget/risk limits
- [ ] Real-time order monitoring and error recovery

#### Web Dashboard
- [ ] Portfolio overview (holdings, P&L, allocation)
- [ ] Scoring/signal results visualization
- [ ] Trade history and execution log
- [ ] Risk dashboard (drawdown, sector exposure, position limits)

### Out of Scope

- Full auto-execution without any human oversight — strategy/budget approval still required
- Mobile app — web dashboard first
- Real-time intraday trading — daily granularity for mid-term holding
- Options/derivatives — stock-only
- Social/sentiment scoring — focus on fundamentals + technicals first

## Current Milestone: v1.2 Production Trading & Dashboard

**Goal:** 전체 파이프라인을 자동화하고, 라이브 트레이딩과 웹 대시보드를 통해 실제로 동작하는 프로덕션 시스템을 완성한다. 핵심은 견고함과 positive expectancy.

**Target features:**
- 자동 파이프라인 스케줄러 (매일 스크리닝 → 스코어링 → 시그널 → 주문 실행)
- 전략/일일 예산 승인 워크플로 (사람은 전략만 승인, 실행은 자동)
- Alpaca 라이브 트레이딩 (소액 실전 매매, 리스크 한도 내 자동 실행)
- 웹 대시보드 (포트폴리오, P&L, 스코어, 시그널, 매매 히스토리, 리스크 현황)

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
*Last updated: 2026-03-13 after v1.2 milestone start*
