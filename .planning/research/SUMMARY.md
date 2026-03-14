# Project Research Summary

**Project:** Intrinsic Alpha Trader -- v1.3 Bloomberg Dashboard
**Domain:** Bloomberg terminal-style trading dashboard (Next.js + React replacing HTMX + Jinja2)
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

This project replaces the existing HTMX+Jinja2 dashboard with a Next.js+React Bloomberg-style trading terminal. The Python/FastAPI backend remains completely unchanged -- the frontend migration is a pure presentation layer swap. The existing query handlers (`OverviewQueryHandler`, `SignalsQueryHandler`, `RiskQueryHandler`, `PipelineQueryHandler`) already return Python dicts; the only backend change is a thin `api_routes.py` file (~150 lines) that wraps these handlers with `JSONResponse` instead of `templates.TemplateResponse`. The SSE bridge (`sse_bridge.py`) already sends JSON payloads and requires zero modification.

The recommended stack is Next.js 16 + TradingView Lightweight Charts (45KB) + TanStack Query + Zustand + shadcn/ui + Tailwind CSS v4. This combination delivers a professional financial dashboard at ~150KB client bundle -- smaller than Plotly.js alone (1.2MB), which the existing HTMX dashboard loads from CDN. The key architectural decision is that Next.js acts as a BFF proxy to FastAPI via `next.config.ts` rewrites, never directly accessing DuckDB or SQLite. This avoids the DuckDB file-lock conflicts that already caused bugs in this project (commit `e0c1c06`).

The three highest-risk pitfalls are: (1) TradingView chart memory leaks from missing `chart.remove()` cleanup on page navigation, (2) SSE response buffering in Next.js breaking real-time event delivery, and (3) SSR/hydration mismatches with dynamic financial data. All three are preventable through upfront architectural decisions in Phase 1: use `useLayoutEffect` cleanup for charts, use `next.config.ts` rewrites (not Next.js Route Handlers) for SSE proxying, and split components into Server Components (static layout) vs. Client Components (dynamic data). The dark theme is a foundational dependency -- every subsequent component inherits from the design token system, so building it first eliminates rework.

## Key Findings

### Recommended Stack

The frontend is an entirely new Next.js 16 project at `dashboard/` (sibling to `src/`, not inside it). No Python changes beyond one new file. All packages are current stable releases with zero version conflicts.

**Core technologies:**
- **Next.js 16.1.x**: App Router, Turbopack default, React Compiler, `proxy.ts`/rewrites for FastAPI proxying. Latest stable, Node.js 22.x compatible.
- **TradingView Lightweight Charts 5.1.x**: 45KB canvas-based financial charting. Industry standard for trading UIs. Replaces Plotly.js (1.2MB) entirely. Direct `useRef`+`useEffect` integration -- no third-party React wrappers.
- **TanStack Query 5.90.x + Zustand 5.0.x**: Server state (API caching, refetch) + client state (UI preferences). Replaces Redux with ~60% less code.
- **shadcn/ui + Tailwind CSS 4.x**: Zero-runtime component library with dark mode via CSS custom properties. Data Table wraps TanStack Table for sortable/filterable grids.
- **Biome 2.x**: Linting + formatting (Next.js 16 removed `next lint`). Single tool replaces ESLint + Prettier.
- **Native EventSource API**: SSE client for real-time updates. Zero dependencies -- browser built-in connects to existing FastAPI SSE endpoint.

### Expected Features

**Must have (v1.3.0 -- table stakes):**
- Dark theme with Bloomberg color palette (amber, cyan, blue, red on black)
- Data-dense holdings table with color-coded P&L (24-28px rows, monospace numbers)
- Equity curve with TradingView Lightweight Charts + regime period overlays
- Scoring heatmap table with gradient coloring (red 0 -> amber 50 -> green 100)
- Drawdown gauge with 10%/15%/20% tier indicators
- Pipeline status timeline with stage-by-stage dots
- Approval panel with budget bar + review queue (approve/reject)
- SSE event consumption (OrderFilled, DrawdownAlert, RegimeChanged, PipelineCompleted)
- Navigation sidebar + system status bar (SSE connection, execution mode, last update)
- LIVE/PAPER mode banner (red/green, matching existing behavior)

**Should have (v1.3.x -- after validation):**
- Keyboard navigation (arrow keys, 1-4 page switching)
- Command palette (Cmd+K or `/`)
- Alert toast system for SSE events
- Flash/pulse animation on data update
- System activity feed

**Defer (v1.4+):**
- TradingView candlestick charts (requires new OHLCV endpoint)
- Multi-panel draggable layout (react-grid-layout)
- Linked security context (cross-panel symbol selection)
- Ticker tape header, mini-sparklines (require price feed data)

**Explicitly rejected (anti-features):**
- Real-time tick-by-tick streaming (daily granularity system, no day trading)
- Drag-and-drop trade execution (bypasses approval-gated safety)
- Mobile-responsive design (trading is desktop-only, min-width 1280px)
- Paper/live mode toggle in UI (dangerous -- stays CLI-only)

### Architecture Approach

Two-process architecture: Next.js (port 3000) proxies to FastAPI (port 8000) via `next.config.ts` rewrites. The browser never contacts FastAPI directly (except optionally for SSE). Server Components render static layout (sidebar, headers, column labels); Client Components render dynamic data (P&L, charts, gauges). The existing `dashboard/application/queries.py` handlers are reused without modification -- a new `api_routes.py` wraps them with JSON responses.

**Major components:**
1. **Next.js App (4 pages)** -- Overview, Signals, Risk, Pipeline. Server Component shell + Client Component data panels.
2. **FastAPI JSON API (`api_routes.py`)** -- New thin layer (~150 LOC) wrapping existing query handlers with JSONResponse. Coexists with HTMX routes during migration.
3. **SSE Hook (`useSSE`)** -- React hook consuming `/dashboard/events`. Dispatches typed events to components. Connection lives at root layout level (persists across page navigation).
4. **TradingView Charts** -- `"use client"` components with `useRef`+`useLayoutEffect`. Equity curve (AreaSeries), drawdown gauge (CSS), sector exposure (SVG/CSS).
5. **Design System** -- CSS custom properties as single source of truth. Bloomberg dark tokens consumed by all components. shadcn/ui primitives for tables, cards, badges.

### Critical Pitfalls

1. **TradingView chart memory leaks** -- Must call `chart.remove()` in `useLayoutEffect` cleanup. Set `isRemoved` flag to guard child component cleanup. Navigate 20 times, verify flat heap in DevTools.
2. **SSE buffering through Next.js** -- Use `next.config.ts` rewrites to proxy SSE (transparent HTTP proxy, no buffering). Avoid Next.js Route Handlers for SSE. In production, set `X-Accel-Buffering: no` on nginx/Caddy.
3. **SSR/hydration mismatch** -- Split into Server Components (static layout) and Client Components (dynamic data). Never SSR financial values that change between render and hydration. Use `Suspense` with skeleton fallbacks.
4. **DuckDB file lock conflicts** -- Node.js must NEVER directly access DuckDB or SQLite. All data through FastAPI HTTP. No `duckdb` or `better-sqlite3` in `package.json`. Already caused real bugs (commit `e0c1c06`).
5. **Bundle size explosion from Plotly** -- Do NOT add Plotly.js to the React app. Replace all 3 Plotly charts: equity curve (TradingView LineSeries), drawdown gauge (CSS conic-gradient), sector donut (SVG/CSS). Target total JS under 300KB gzipped.
6. **Dark theme incomplete** -- CSS custom properties for all colors, explicit TradingView chart options (not CSS), scrollbar styling, form element reset, focus ring visibility. Audit every interactive state.
7. **Security: subprocess APIs** -- Zero subprocess imports in Next.js codebase. CVE-2025-55182 (React2Shell, CVSS 10/10) compromised 59,000 servers. All backend access through HTTP.

## Implications for Roadmap

Based on research, 7 phases ordered by dependency chain and risk mitigation.

### Phase 1: Project Setup + BFF Architecture
**Rationale:** Every subsequent phase depends on the Next.js project existing, the proxy to FastAPI working, and the SSE architecture decided. Foundational pitfalls (subprocess architecture, DuckDB access, SSE buffering) must be prevented here.
**Delivers:** Working Next.js 16 project at `dashboard/`, `next.config.ts` rewrites proxying to FastAPI, environment variables configured, Biome initialized, SSE connection verified end-to-end.
**Addresses:** Navigation sidebar (partial), LIVE/PAPER mode banner (partial).
**Avoids:** Pitfalls 2 (subprocess architecture), 3 (DuckDB locks), 5 (SSE buffering), security mistakes (key exposure, unauthenticated routes).

### Phase 2: Design System + Dark Theme
**Rationale:** The Bloomberg aesthetic is the entire point of v1.3. Every component inherits from the design token system. Building components on a light theme then switching creates rework. Dark theme CSS conflicts (Pitfall 7) are easier to fix when no components exist yet.
**Delivers:** CSS custom properties (Bloomberg color palette), Tailwind v4 configuration, shadcn/ui initialization with dark theme, monospace font for numbers, compact spacing system, skeleton loading components, drawdown gauge (CSS), sector exposure (SVG/CSS).
**Addresses:** Dark theme, color-coded P&L system, monospace number alignment, compact component boundaries.
**Avoids:** Pitfall 7 (dark theme gaps), Pitfall 6 (bundle size -- CSS charts replace Plotly).

### Phase 3: FastAPI JSON API
**Rationale:** The React pages need data endpoints. The existing query handlers return Python dicts -- wrapping them with JSONResponse is ~150 lines of code. This unlocks all subsequent page work.
**Delivers:** `api_routes.py` with GET endpoints for overview, signals, risk, pipeline. POST endpoints for pipeline/run and pipeline/approve. Remove Plotly chart JSON from responses (gauge_json, donut_json). Both HTMX and React dashboards operational simultaneously.
**Addresses:** Backend integration point.
**Avoids:** Anti-pattern 1 (duplicating business logic in TypeScript).

### Phase 4: Overview Page
**Rationale:** Overview has the most data complexity (portfolio KPIs, holdings table, equity curve chart). Building it first validates the entire integration path: fetch -> proxy -> query handler -> JSON -> React rendering. The equity curve establishes the TradingView chart pattern reused on other pages.
**Delivers:** KPI cards (portfolio value, P&L, drawdown, position count), holdings/positions data table with color-coded P&L, equity curve with TradingView AreaSeries + regime overlays.
**Uses:** TanStack Query for data fetching, shadcn/ui Data Table, TradingView Lightweight Charts.
**Avoids:** Pitfall 1 (chart memory leaks -- establish correct cleanup pattern), Pitfall 4 (hydration -- establish Server/Client split).

### Phase 5: Signals + Risk + Pipeline Pages
**Rationale:** These three pages are simpler than Overview and follow established patterns from Phase 4 (table component, chart component, data fetching). Grouping them reduces phase count without increasing complexity. Each page is ~2-4 components reusing the table and card primitives.
**Delivers:** Scoring heatmap table with gradient colors, signal direction indicators, drawdown gauge with tier markers, sector exposure bars, regime badge, pipeline timeline with status dots, approval panel with budget bar, review queue with approve/reject buttons.
**Addresses:** All remaining table stakes features.
**Avoids:** Pitfall 4 (hydration -- same pattern as Phase 4).

### Phase 6: SSE Integration + Real-Time Updates
**Rationale:** SSE is deferred until all 4 pages render correctly with static data. Adding real-time updates to broken pages makes debugging harder. The `useSSE` hook connects at root layout level and dispatches to page-specific handlers.
**Delivers:** `useSSE` hook with typed event dispatch. Holdings update on OrderFilled, drawdown update on DrawdownAlert, regime badge update on RegimeChanged, pipeline status update on PipelineCompleted/PipelineHalted. System status bar with SSE connection indicator and last-update timestamp.
**Addresses:** Real-time data streaming, system status bar.
**Avoids:** Pitfall 5 (SSE buffering -- verified in Phase 1, wired here), performance trap (SSE reconnection on page navigation -- single connection at layout level).

### Phase 7: Cleanup + Production Readiness
**Rationale:** Remove the old HTMX dashboard code and Plotly dependency once the React dashboard is verified functional through daily use. Run the "Looks Done But Isn't" checklist.
**Delivers:** Remove `src/dashboard/presentation/routes.py` (HTMX routes), `src/dashboard/presentation/templates/` directory, `src/dashboard/presentation/charts.py` (Plotly). Remove Plotly from `pyproject.toml`. Update `.gitignore` with `dashboard/node_modules`, `dashboard/.next`. Production deployment configuration (Caddy or systemd).
**Addresses:** Technical debt cleanup, bundle size verification (<300KB gzipped).
**Avoids:** Running two dashboard systems indefinitely.

### Phase Ordering Rationale

- **Phases 1-2 before any page work:** The proxy architecture and design system are foundational. Building a page on top of wrong architecture or wrong theme creates costly rework.
- **Phase 3 (JSON API) is a 1-hour task** but is a separate phase because it touches the Python backend -- different toolchain, different testing. Keep it isolated.
- **Phase 4 (Overview) before Phase 5 (other pages):** Overview validates the hardest integration path (multiple data sources, chart rendering, table component). Once this works, remaining pages are pattern replication.
- **Phase 6 (SSE) after all pages:** SSE events fire infrequently (trades, pipeline runs, regime changes). Pages must work with static data first. SSE is an enhancement layer, not a dependency.
- **Phase 7 (Cleanup) is separate:** Do not delete old code until the new dashboard has been used for real trading for at least a few days.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Setup):** SSE proxy architecture decision needs validation -- test both `next.config.ts` rewrites and direct browser-to-FastAPI connection. Confirm Turbopack handles the rewrite correctly.
- **Phase 4 (Overview):** TradingView Lightweight Charts v5.1 React integration -- the official advanced tutorial covers the pattern, but regime overlay (colored bands) may need custom plugin work.

Phases with standard patterns (skip deep research):
- **Phase 2 (Design System):** Well-documented -- shadcn/ui dark mode guide + Bloomberg color palette specs are comprehensive.
- **Phase 3 (JSON API):** Trivial -- wrapping existing Python query handlers with JSONResponse. The handlers already return dicts.
- **Phase 5 (Signals/Risk/Pipeline):** Pattern replication from Phase 4. No new architectural decisions.
- **Phase 6 (SSE):** EventSource API is browser-standard. The SSE bridge already works.
- **Phase 7 (Cleanup):** Deletion only. No new code.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against npm registry and official docs (2026-03-14). Next.js 16.1.x, TradingView 5.1.x, TanStack Query 5.90.x all current stable. Zero version conflicts. |
| Features | HIGH | Bloomberg UX patterns well-documented. Existing backend data availability verified from `dashboard/application/queries.py`. Feature dependencies mapped. Anti-features clearly identified. |
| Architecture | HIGH | Two-process BFF proxy is standard Next.js + external API pattern. Existing codebase analysis confirms query handlers return JSON-serializable dicts. SSE bridge confirmed JSON payload format. |
| Pitfalls | HIGH | All pitfalls grounded in official docs, CVE advisories, or actual project history (DuckDB lock bug in commit e0c1c06). TradingView memory leak documented in GitHub issue #552. SSE buffering documented in Next.js discussion #48427. |

**Overall confidence:** HIGH

### Gaps to Address

- **OHLCV price data endpoint:** TradingView candlestick charts (deferred to v1.4+) require a new API endpoint querying DuckDB OHLCV tables. Not needed for v1.3.0 but design the data model now.
- **Production deployment:** The research covers Caddy reverse proxy configuration but does not specify systemd service files, process monitoring, or log aggregation. Address during Phase 7 planning.
- **Authentication:** The single-user personal dashboard currently has no auth. The security pitfalls research flags unauthenticated POST routes as a risk. Decide on simple API key header or skip for v1.3.0 (localhost-only binding).
- **Next.js 16 `proxy.ts`:** Research recommends starting with `next.config.ts` rewrites (proven) over `proxy.ts` (new in 16). Validate `proxy.ts` later if conditional logic is needed.
- **React Compiler impact:** Next.js 16 includes stable React Compiler which auto-memoizes. Verify this does not conflict with TradingView chart `useRef` patterns during Phase 4.

## Sources

### Primary (HIGH confidence)
- [Next.js 16 Release Blog](https://nextjs.org/blog/next-16) -- Turbopack stable, React Compiler, proxy.ts
- [Next.js 16.1 Release Blog](https://nextjs.org/blog/next-16-1) -- Latest patch release
- [TradingView Lightweight Charts Official Docs](https://tradingview.github.io/lightweight-charts/) -- v5.1, React tutorials
- [TradingView Lightweight Charts React Advanced Tutorial](https://tradingview.github.io/lightweight-charts/tutorials/react/advanced) -- Cleanup patterns
- [TradingView Memory Leak Issue #552](https://github.com/tradingview/lightweight-charts/issues/552) -- chart.remove() requirement
- [DuckDB Concurrency Documentation](https://duckdb.org/docs/stable/connect/concurrency) -- Single-writer model
- [CVE-2025-55182 React2Shell (Datadog)](https://securitylabs.datadoghq.com/articles/cve-2025-55182-react2shell-remote-code-execution-react-server-components/) -- CVSS 10/10 RCE
- [Bloomberg UX Color Accessibility](https://www.bloomberg.com/ux/2021/10/14/designing-the-terminal-for-color-accessibility/) -- Color system
- [shadcn/ui Dark Mode Guide](https://ui.shadcn.com/docs/dark-mode/next) -- next-themes integration
- [shadcn/ui Data Table](https://ui.shadcn.com/docs/components/radix/data-table) -- TanStack Table integration
- Project codebase: `src/dashboard/application/queries.py`, `src/dashboard/infrastructure/sse_bridge.py`, `src/dashboard/presentation/routes.py`, `src/dashboard/presentation/charts.py`
- Project commit `e0c1c06`: DuckDB lock conflict evidence

### Secondary (MEDIUM confidence)
- [Next.js SSE Discussion #48427](https://github.com/vercel/next.js/discussions/48427) -- SSE buffering caveats
- [State of React State Management 2026](https://www.pkgpulse.com/blog/state-of-react-state-management-2026) -- TanStack Query + Zustand dominance
- [Next.js 16 Proxy Architecture](https://learnwebcraft.com/learn/nextjs/nextjs-16-proxy-ts-changes-everything) -- proxy.ts patterns
- [Fixing Slow SSE in Next.js](https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996) -- X-Accel-Buffering fix

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*
