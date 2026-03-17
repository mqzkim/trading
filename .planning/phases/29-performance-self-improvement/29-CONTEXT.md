# Phase 29: Performance & Self-Improvement - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Trade P&L tracking with decision context snapshots at entry, Brinson-Fachler 4-level attribution, signal IC/Kelly efficiency validation, and parameter improvement proposals with human approval via Dashboard.

Excluded: new scoring logic changes (Phase 27), broker execution changes, new commercial API products. Self-improver only proposes scoring weight adjustments — not risk parameters.

</domain>

<decisions>
## Implementation Decisions

### Trade History Storage
- Store closed trade records in **DuckDB** (analytics DB, already used for walk-forward)
- `trades` table fields: symbol, entry_date, exit_date, entry_price, exit_price, quantity, pnl, pnl_pct, strategy, sector, composite_score, technical_score, fundamental_score, sentiment_score, regime, weights_json, signal_direction
- Decision context snapshot captured via **`PositionOpenedEvent`** — add `score_snapshot` field containing composite_score, technical_score, fundamental_score, sentiment_score, regime, weights at entry time
- `signal_direction` field added to both `PositionOpenedEvent` and `trades` table (required for IC calculation)

### Attribution Calculation Trigger
- Brinson-Fachler runs **on-demand** — computed when dashboard Performance page API is called
- Returns empty/zero state with "No performance data yet" message when fewer than 50 trades exist
- No scheduled caching — compute on request from DuckDB trade history

### Attribution API Location
- New endpoint: `GET /v1/performance/attribution` in `commercial/api/`
- Same FastAPI structure as existing routers (QuantScore, RegimeRadar, SignalFusion)
- Dashboard BFF proxies to this endpoint via existing Next.js API route pattern
- No separate personal API server

### Self-Improver Approval UX
- Proposals displayed in **Dashboard Performance page** — new "Parameter Proposals" section below Strategy Scorecard
- Section hidden (collapsed/empty) until 50+ trades accumulated
- Shows proposed weight changes: `Fundamental: 40% → 45%` format
- Approve / Reject buttons trigger PUT `/v1/performance/proposals/{id}/approve` or `/reject`
- Approval history shown below proposals (last 5 applied changes)

### Self-Improver Scope
- Only proposes **scoring axis weight adjustments**: fundamental/technical/sentiment weights per regime
- Does NOT propose risk parameter changes (ATR multiplier, Kelly fraction, sector limits)
- Walk-forward validation must complete before proposal is generated — no instant proposals
- 50+ closed trades threshold before self-improvement activates (SELF-04)

### Domain Architecture
- New **`src/performance/`** DDD bounded context (parallel to src/scoring/, src/regime/)
  - `domain/`: ClosedTrade entity, TradeHistory aggregate, PerformanceReport value object
  - `application/`: ComputeAttributionQuery, GenerateProposalCommand, handlers
  - `infrastructure/`: DuckDB trade history repository
- **`personal/self_improver/`** refactored to DDD structure — `domain/application/infrastructure/`
  - Existing `advisor.py` logic migrated to domain service
  - Proposal approval API added to `commercial/api/routers/`

### Brinson-Fachler "Skill" Level
- **Skill level = IC-based signal quality** — per-axis IC (fundamental signal IC, technical signal IC, sentiment signal IC)
- Measures which scoring axis better predicts actual trade returns
- Compared against IC ≥ 0.03 threshold (PERF-03)
- Kelly efficiency = actual position returns vs theoretical maximum (PERF-04)

### Dashboard Performance Page Completion
- Existing page shell (Phase 28) already has: KPI cards (Sharpe/Sortino/Win Rate/Max Drawdown), Brinson-Fachler table placeholder, `usePerformance()` hook
- This phase seeds real data via new `/v1/performance/attribution` endpoint
- Add Strategy Scorecard section: IC vs 0.03 threshold + Kelly efficiency vs 70% threshold
- Add Parameter Proposals section below scorecard (hidden until 50+ trades)

### Claude's Discretion
- Exact DuckDB schema migration approach (alembic vs raw SQL)
- Loading skeleton for Parameter Proposals section
- Approval history display depth and formatting

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Position.close()` in `src/portfolio/domain/entities.py` — already returns pnl/pnl_pct; extend to trigger trade persistence
- `PositionOpenedEvent` / `PositionClosedEvent` in `src/portfolio/domain/events.py` — extend PositionOpenedEvent with score_snapshot field
- `personal/self_improver/advisor.py` — `suggest_improvements(wf_result)` function; migrate to DDD domain service
- `commercial/api/` — FastAPI structure: routers/, schemas/, dependencies.py, middleware/ all reusable
- Dashboard `performance/page.tsx` — shell already built: KPI cards, Brinson-Fachler placeholder, `usePerformance()` hook
- `dashboard/src/hooks/use-performance.ts` — exists but likely hits mock/empty endpoint; wire to real API
- TradingView Lightweight Charts — already installed, available for equity curve

### Established Patterns
- DDD event bus: `src/shared/domain/EventBus` — use for PositionClosedEvent → performance context
- BFF proxy: dashboard → Next.js API routes → FastAPI (established in Phase 28)
- DI via `Depends()`: all existing commercial routers use dependency injection pattern
- DuckDB analytics: already used in walk-forward backtest — reuse connection pattern
- Bloomberg dark theme + shadcn/ui: design system established, use existing Card/Table components

### Integration Points
- `PositionOpenedEvent` publisher: `src/execution/` or `src/portfolio/application/` — add score_snapshot
- Performance attribution consumer: subscribe to `PositionClosedEvent` in `src/performance/infrastructure/`
- Dashboard BFF: add `/api/performance` proxy route in `dashboard/src/app/api/`
- Commercial API: add `performance` router to `commercial/api/main.py` routers list

</code_context>

<specifics>
## Specific Ideas

- Performance page layout (Phase 28 decision): KPI cards → Brinson-Fachler table → Strategy Scorecard (IC/Kelly) → Parameter Proposals (collapsible, hidden until 50+ trades)
- Parameter Proposals format: `Fundamental: 40% → 45% | Technical: 35% → 30% | Sentiment: 25% → 25%` per regime
- Empty state: "No performance data yet — generates after first closed trades" (no mock data)
- Approval history: last 5 applied changes with date + delta

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §PERF-01 through PERF-05, SELF-01 through SELF-04

### Existing Domain Code
- `src/portfolio/domain/entities.py` — Position entity with close() method
- `src/portfolio/domain/events.py` — PositionOpenedEvent, PositionClosedEvent (extend these)
- `personal/self_improver/advisor.py` — existing improvement logic to migrate

### Commercial API (extend)
- `commercial/api/main.py` — router registration
- `commercial/api/dependencies.py` — DI patterns
- `commercial/api/schemas/common.py` — DISCLAIMER constant, base patterns

### Dashboard (extend)
- `dashboard/src/app/(dashboard)/performance/page.tsx` — Phase 28 shell to complete
- `dashboard/src/hooks/use-performance.ts` — hook to wire to real endpoint

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md.

</canonical_refs>

<deferred>
## Deferred Ideas

- CLI `trading attribution` command — deferred, Dashboard-only for Phase 29
- Risk parameter adjustment proposals (ATR multiplier, Kelly fraction) — out of scope per user decision
- FinBERT upgrade for sentiment (ML-01) — separate future requirement

</deferred>

---

*Phase: 29-performance-self-improvement*
*Context gathered: 2026-03-18*
