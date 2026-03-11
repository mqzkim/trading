# Intrinsic Alpha Trader

## What This Is

AI-assisted mid-term trading system that identifies undervalued US companies through fundamental analysis and valuation models, then generates rule-based trading plans with entry, take-profit, stop-loss, and monitoring workflows for disciplined execution. Targeting serious retail investors and independent traders who want systematic, explainable, risk-controlled investing.

## Core Value

Every recommendation must be explainable and risk-controlled — the system prioritizes capital preservation and positive expectancy over maximizing returns.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Data ingestion pipeline for US market (OHLCV, financials, SEC filings, news)
- [ ] Fundamental scoring engine (Piotroski F-Score, Altman Z-Score, Beneish M-Score, Mohanram G-Score)
- [ ] Valuation engine with ensemble model (DCF, EPV, relative multiples)
- [ ] Signal engine combining quality score + valuation gap
- [ ] Risk management engine (Fractional Kelly position sizing + portfolio drawdown control)
- [ ] Monitoring and alerting engine (price targets, stop-loss triggers, position status)
- [ ] Backtesting engine for strategy validation
- [ ] Alpaca broker integration (Paper Trading first)
- [ ] CLI-based dashboard for stock ranking, watchlist, and trade plans
- [ ] Daily screening workflow
- [ ] Trading plan generation (entry, take-profit, stop-loss levels)
- [ ] Human approval workflow before order execution

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Full auto-execution in V1 — requires paper trading validation first
- Korean market (KOSPI/KOSDAQ) — MVP focuses on US only, add later
- Web/GUI dashboard — CLI first, Streamlit/Next.js in v2
- Real-time intraday trading — daily granularity for mid-term holding
- Options/derivatives — stock-only for MVP
- Social/sentiment scoring in V1 — focus on fundamentals first

## Context

- Existing workspace has trading-related agents (fundamental-analyst, technical-analyst, regime-analyst, sentiment-analyst, risk-auditor, execution-ops, performance-attribution, data-engineer, trading-orchestrator-lead)
- Existing skills include data-ingest, scoring-engine, signal-generate, risk-manager, position-sizer, regime-detect, paper-trading-ops, execution-planner, backtest-validator, integration-tester
- Alpaca API selected for broker integration — free API with built-in Paper Trading
- Target holding period: 1-3 months (position trading)
- Valuation ensemble: DCF + Earnings Power Value + relative multiples (PER/PBR/EV), weighted average
- Scoring extends existing Piotroski F / Altman Z / Beneish M / Mohanram G framework
- Risk control: dual-layer (individual position via Fractional Kelly + ATR, portfolio via drawdown tiers)

## Constraints

- **Explainability**: Every score, signal, and recommendation must trace back to specific data points
- **Risk-first**: No position without defined stop-loss; drawdown defense protocol (10/15/20% tiers)
- **Paper-first**: All strategies must pass paper trading validation before live consideration
- **Human-in-the-loop**: V1 requires explicit human approval before any live order
- **Data reliability**: Free data sources (yfinance, SEC EDGAR) preferred; paid APIs only if free sources insufficient
- **Tech stack**: Python-centric (pandas, SQLite, FastAPI for internal APIs)
- **Positive expectancy**: System must demonstrate statistical edge via backtesting before deployment

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| US market only for MVP | Data accessibility highest, Alpaca supports US | — Pending |
| CLI-based dashboard | Fastest to build, matches terminal workflow | — Pending |
| Valuation ensemble (DCF+EPV+Relative) | No single model is reliable alone; ensemble reduces model risk | — Pending |
| Alpaca for broker integration | Free API, Paper Trading built-in, good Python SDK | — Pending |
| Python-centric stack | Best ecosystem for financial analysis (pandas, numpy, scipy) | — Pending |
| Daily screening granularity | Mid-term holding period doesn't need intraday data | — Pending |
| Fractional Kelly + ATR for position sizing | Mathematically grounded, prevents over-concentration | — Pending |

---
*Last updated: 2026-03-12 after initialization*
