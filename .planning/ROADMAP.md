# Roadmap: Intrinsic Alpha Trader

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2026-03-12)
- ✅ **v1.1 Stabilization & Expansion** - Phases 5-11 (shipped 2026-03-12)
- ✅ **v1.2 Production Trading & Dashboard** - Phases 12-20 (shipped 2026-03-14)
- 🚧 **v1.3 Bloomberg Dashboard** - Phases 21-25 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) - SHIPPED 2026-03-12</summary>

Delivered: End-to-end quantitative trading system from raw data ingestion through risk-controlled trade execution.

</details>

<details>
<summary>✅ v1.1 Stabilization & Expansion (Phases 5-11) - SHIPPED 2026-03-12</summary>

Delivered: Tech debt fixes, live data, technical scoring, regime detection, signal fusion, Korean broker, commercial API.

</details>

<details>
<summary>✅ v1.2 Production Trading & Dashboard (Phases 12-20) - SHIPPED 2026-03-14</summary>

Delivered: Safety infrastructure, automated pipeline, strategy approval, live trading, HTMX dashboard, SSE events, drawdown defense.

</details>

### 🚧 v1.3 Bloomberg Dashboard (In Progress)

**Milestone Goal:** Replace HTMX+Jinja2 dashboard with a Next.js+React Bloomberg terminal-style professional trading dashboard. TradingView charts, data-dense dark theme, real-time SSE updates, 4 redesigned pages.

- [x] **Phase 21: Foundation** - Next.js project setup, FastAPI JSON API, BFF proxy architecture (completed 2026-03-14)
- [x] **Phase 22: Design System & Overview Page** - Bloomberg dark theme tokens, shadcn/ui components, Overview page with KPI cards, holdings table, equity curve chart (completed 2026-03-14)
- [ ] **Phase 23: Signals, Risk & Pipeline Pages** - Scoring tables, signal cards, drawdown gauge, sector chart, pipeline controls, approval queue
- [ ] **Phase 24: Real-Time & Integration** - SSE event wiring to React components, live UI updates across all pages
- [ ] **Phase 25: Cleanup** - Remove HTMX/Jinja2 templates and Plotly dependency

## Phase Details

### Phase 21: Foundation
**Goal**: Developer can run the Next.js dashboard alongside FastAPI and all data flows through the BFF proxy
**Depends on**: Phase 20 (v1.2 complete)
**Requirements**: SETUP-01, SETUP-02, SETUP-03
**Success Criteria** (what must be TRUE):
  1. Running `npm run dev` in `dashboard/` starts the Next.js app at localhost:3000
  2. Browser requests to `/api/*` on the Next.js dev server are proxied to FastAPI at localhost:8000 and return JSON data
  3. FastAPI serves JSON responses for overview, signals, risk, and pipeline data at `/api/v1/dashboard/*` endpoints
**Plans**: 2 plans

Plans:
- [ ] 21-01-PLAN.md -- FastAPI JSON API endpoints (4 GET + 5 POST + SSE) with unit tests
- [ ] 21-02-PLAN.md -- Next.js 16 project setup, Biome config, API proxy rewrites, page stubs

### Phase 22: Design System & Overview Page
**Goal**: User sees a Bloomberg-style dark dashboard with Overview page showing portfolio KPIs, holdings, equity curve, and trade history
**Depends on**: Phase 21
**Requirements**: DSGN-01, DSGN-02, DSGN-03, DSGN-04, OVER-01, OVER-02, OVER-03, OVER-04
**Success Criteria** (what must be TRUE):
  1. All UI renders with Bloomberg dark theme (black background, amber/cyan/red semantic colors, monospace numbers)
  2. KPI cards display total portfolio value, daily P&L, current drawdown tier, and pipeline status
  3. Holdings table shows each position with ticker, quantity, price, P&L (color-coded), stop, target, and composite score
  4. TradingView equity curve chart renders with regime background coloring
  5. Trade history table displays past executed trades
**Plans**: 2 plans

Plans:
- [x] 22-01-PLAN.md -- Design system infrastructure: shadcn/ui init, Bloomberg dark theme tokens, JetBrains Mono font, providers, TypeScript API types, formatters
- [x] 22-02-PLAN.md -- Overview page: KPI cards, holdings table, TradingView equity curve chart, trade history table, page assembly

### Phase 23: Signals, Risk & Pipeline Pages
**Goal**: User can view scoring results, review signal recommendations, monitor risk exposure, run the pipeline, and approve/reject trade plans
**Depends on**: Phase 22
**Requirements**: SGNL-01, SGNL-02, SGNL-03, RISK-01, RISK-02, RISK-03, RISK-04, PIPE-01, PIPE-02, PIPE-03, PIPE-04
**Success Criteria** (what must be TRUE):
  1. Signals page displays scoring table (symbol, composite score, risk-adjusted score, signal) with sortable columns and signal recommendation cards (BUY/SELL/HOLD with strength indicator)
  2. Risk page shows drawdown gauge with 3-tier coloring (green/yellow/red), sector exposure donut chart, position limit progress bars, and market regime badge
  3. Pipeline page allows running the pipeline via form, displays pipeline run history, and provides strategy approval controls (create/suspend/resume)
  4. Trade review queue shows pending trade plans with approve/reject buttons that submit to the backend
**Plans**: TBD

Plans:
- [ ] 23-01: TBD
- [ ] 23-02: TBD
- [ ] 23-03: TBD

### Phase 24: Real-Time & Integration
**Goal**: Dashboard UI updates in real-time when trading events occur without requiring page refresh
**Depends on**: Phase 23
**Requirements**: RT-01
**Success Criteria** (what must be TRUE):
  1. When an order fills (OrderFilled), the holdings table and P&L KPI update without page refresh
  2. When drawdown tier changes (DrawdownAlert), the drawdown gauge and risk indicators update automatically
  3. When market regime changes (RegimeChanged), the regime badge updates across relevant pages
  4. When a pipeline run completes (PipelineCompleted), the pipeline status and history update automatically
**Plans**: TBD

Plans:
- [ ] 24-01: TBD

### Phase 25: Cleanup
**Goal**: Legacy HTMX dashboard code and Plotly dependency are removed, leaving only the React dashboard
**Depends on**: Phase 24
**Requirements**: CLNP-01, CLNP-02
**Success Criteria** (what must be TRUE):
  1. HTMX templates directory and Jinja2 template routes no longer exist in the codebase
  2. Plotly is removed from pyproject.toml dependencies and no Python code imports it
**Plans**: TBD

Plans:
- [ ] 25-01: TBD

## Progress

**Execution Order:** Phases execute in numeric order: 21 → 22 → 23 → 24 → 25

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 21. Foundation | 2/2 | Complete    | 2026-03-14 | - |
| 22. Design System & Overview Page | 2/2 | Complete    | 2026-03-14 | - |
| 23. Signals, Risk & Pipeline Pages | v1.3 | 0/3 | Not started | - |
| 24. Real-Time & Integration | v1.3 | 0/1 | Not started | - |
| 25. Cleanup | v1.3 | 0/1 | Not started | - |
