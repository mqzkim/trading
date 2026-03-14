# Milestones

## v1.2 Production Trading & Dashboard (Shipped: 2026-03-14)

**Phases completed:** 9 phases, 20 plans, 0 tasks

**Key accomplishments:**
- (none recorded)

---

## v1.1 Stabilization & Expansion (Shipped: 2026-03-12)

**Phases completed:** 7 phases, 17 plans, 0 tasks

**Key accomplishments:**
- (none recorded)

---

## v1.0 MVP (Shipped: 2026-03-12)

**Phases completed:** 4 phases, 12 plans
**Commits:** 106 | **Files:** 498 | **LOC:** 20,357 Python
**Timeline:** 10 days (2026-03-02 → 2026-03-12)
**Git range:** `7bd9402..ada1196`

**Key accomplishments:**
1. Data ingestion pipeline with DuckDB/SQLite dual-DB and SEC filing point-in-time awareness
2. Fundamental scoring (Piotroski F / Altman Z / Beneish M / Mohanram G) with safety gates and composite 0-100 scoring
3. Valuation ensemble (DCF 40% + EPV 35% + Relative 25%) with margin of safety calculation
4. Signal generation with BUY/HOLD/SELL reasoning traces and DuckDB screener/ranker
5. Risk management with Fractional Kelly (1/4) position sizing and 3-tier drawdown defense (10/15/20%)
6. Trade execution with Alpaca paper trading, human approval CLI, interactive dashboard, and monitoring alerts

**Delivered:** End-to-end quantitative trading system from raw data ingestion through risk-controlled trade execution, with DDD architecture (4 bounded contexts), 352+ behavioral tests, and full explainability chain.

**Known Tech Debt (16 items):**
- DuckDB/SQLite scoring store mismatch (screener queries DuckDB but scores written to SQLite)
- Table name/column mismatches in screener valuations join
- Missing CLI commands: ingest, generate-plan, backtest
- DDD path wiring gaps (legacy core/ path provides working alternatives)
- Cross-context domain import (execution → portfolio)
- Domain events defined but never published to EventBus
- See `milestones/v1.0-MILESTONE-AUDIT.md` for full details

---

