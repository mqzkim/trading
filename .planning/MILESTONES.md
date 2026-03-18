# Milestones

## v1.4 Full Stack Trading Platform (Shipped: 2026-03-18)

**Phases completed:** 4 phases, 9 plans, 6 tasks

**Key accomplishments:**
- (none recorded)

---

## v1.3 Bloomberg Dashboard (Shipped: 2026-03-14)

**Phases completed:** 5 phases, 9 plans
**Commits:** 40 | **Files:** 178 | **LOC:** 2,430 TypeScript + 13,008 Python
**Timeline:** 1 day (2026-03-14)
**Git range:** `7dbf877..764adc9`

**Key accomplishments:**
1. Next.js 16 + FastAPI BFF proxy architecture with JSON API endpoints
2. Bloomberg OKLCH dark theme design system with shadcn/ui and JetBrains Mono
3. 4-page professional trading dashboard (Overview, Signals, Risk, Pipeline)
4. TradingView Lightweight Charts equity curve with regime histogram overlay
5. SSE real-time updates via EventSource-to-TanStack-Query invalidation mapping
6. Legacy HTMX/Jinja2/Plotly complete removal with DDD violation fix

**Delivered:** Bloomberg terminal-style React dashboard replacing legacy HTMX, with data-dense dark theme, TradingView charts, sortable tables, CSS-only visualizations (drawdown gauge, sector donut), real-time SSE updates, and pipeline approval queue.

**Tech Debt:**
- 4 visual verification items pending human browser confirmation (Phase 22)
- target_price always 0.0 (Position entity has no target field)
- current_price uses entry_price proxy (no live price feed in daily-frequency system)

---

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

