# Pitfalls Research

**Domain:** Adding React+Next.js Bloomberg-style dashboard to existing Python trading system
**System:** Intrinsic Alpha Trader v1.2 -> v1.3 (Bloomberg Dashboard)
**Researched:** 2026-03-14
**Confidence:** HIGH (codebase analysis + official TradingView/Next.js docs + CVE advisories + prior v1.2 pitfalls)

---

## Critical Pitfalls

### Pitfall 1: TradingView Chart Memory Leaks on Page Navigation

**What goes wrong:**
TradingView Lightweight Charts creates canvas-based chart instances that hold GPU and memory resources. When users navigate between dashboard pages (Overview, Signals, Risk, Pipeline), React unmounts and remounts chart components. If `chart.remove()` is not called in the useEffect cleanup, the canvas and all associated data stay in memory. After 10-20 page transitions, the browser tab consumes 500MB+ and starts lagging. The existing system has no charts in React (Plotly is served via Jinja2 `<script>` tags), so this is entirely new territory.

**Why it happens:**
React's useEffect cleanup order is counterintuitive with parent-child charting components. Hooks run bottom-up during initialization (Series mounts before Chart) but top-down during cleanup (Chart cleans up before Series). If you use a parent `<ChartContainer>` with child `<CandlestickSeries>` components, the parent's cleanup removes the chart first, but the child's cleanup then tries to access a destroyed chart instance, causing errors. Developers remove the cleanup code to "fix" the errors, which introduces the leak.

**How to avoid:**
1. Store chart ref with `useRef()` and always call `chart.remove()` in `useLayoutEffect` cleanup (not `useEffect` -- layout effects clean up synchronously before DOM mutations)
2. Set an `isRemoved` flag before calling `chart.remove()` so child components can guard against accessing a destroyed chart
3. Use the `useImperativeHandle` + `Context.Provider` pattern from TradingView's official advanced React example
4. Wrap all chart components with `dynamic(() => import('./Chart'), { ssr: false })` since charts are canvas-based and cannot SSR

```typescript
// Correct cleanup pattern from TradingView docs
useLayoutEffect(() => {
  const chart = createChart(containerRef.current!, options);
  chartApiRef.current = { chart, isRemoved: false };
  return () => {
    chartApiRef.current.isRemoved = true;
    chart.remove();
  };
}, []);
```

**Warning signs:**
- Browser DevTools Memory tab shows monotonically increasing heap after page navigation cycles
- Canvas element count in DOM grows after each navigation (inspect with `document.querySelectorAll('canvas').length`)
- `MaxListenersExceededWarning` in Node.js console (SSR-side, if chart code leaks into server)

**Phase to address:**
Phase 1 (Project Setup) -- establish the chart wrapper component with correct cleanup from day one. Retrofitting cleanup into existing chart components is error-prone because the parent-child hook ordering bug is subtle.

---

### Pitfall 2: Next.js API Routes Spawning Python Subprocesses

**What goes wrong:**
The natural instinct is to have Next.js API routes invoke Python scripts via Node.js subprocess APIs to access the existing query handlers (`OverviewQueryHandler`, `SignalsQueryHandler`, etc.). This approach has two catastrophic problems:

1. **Security:** CVE-2025-55182 (React2Shell, CVSS 10/10) demonstrated that prototype pollution in React Server Components can lead to arbitrary command execution on the server. 59,000 Next.js servers were compromised in 48 hours. Any codebase that uses Node.js subprocess APIs expands the attack surface for this class of vulnerability.
2. **Performance:** Each subprocess call bootstraps the entire Python context -- `bootstrap()` in `src/bootstrap.py` wires 10+ bounded contexts, opens DuckDB connections, initializes repository instances. This adds 2-5 seconds latency per API call. The existing system takes ~3 seconds to bootstrap even for a simple query.

**Why it happens:**
The existing `create_dashboard_app()` in `src/dashboard/presentation/app.py` creates a FastAPI app with a fully bootstrapped context (`app.state.ctx = ctx`). Query handlers like `OverviewQueryHandler(ctx)` depend on this context dict containing live repository instances. Developers think "I'll just call Python from Node.js to reuse these handlers" instead of treating the FastAPI server as an HTTP API.

**How to avoid:**
Keep the existing FastAPI server running as the Python backend. Next.js API routes act as a Backend-for-Frontend (BFF) proxy -- they call the FastAPI endpoints via HTTP (`fetch('http://localhost:8000/dashboard/...')`), transform the response shape for the React frontend, and never use subprocess APIs.

Architecture: `Browser -> Next.js (port 3000, BFF) -> FastAPI (port 8000, Python backend) -> DuckDB/SQLite`

Never: `Browser -> Next.js -> subprocess('python') -> DuckDB/SQLite`

The FastAPI server already has: bootstrapped context, SSE bridge, all 4 query handlers, pipeline/approval POST endpoints.

**Warning signs:**
- Any Node.js subprocess API imports in Next.js codebase
- API route files containing `export const runtime = 'nodejs'` specifically to enable subprocess calls
- Python import statements appearing in TypeScript template strings
- No running FastAPI process required for the dashboard to work

**Phase to address:**
Phase 1 (Project Setup) -- define the BFF architecture boundary before any API route is written. This is a foundational decision that affects every subsequent phase.

---

### Pitfall 3: DuckDB File Lock Conflicts Between Python and Node.js Processes

**What goes wrong:**
DuckDB enforces single-writer, multiple-reader semantics at the OS file level. The existing Python trading system holds a DuckDB connection open for analytics (scoring, signals, regime data). If a Node.js process (directly or via spawned Python subprocess) tries to open the same DuckDB file for writing, it blocks indefinitely or fails with a lock error. **This already happened in this project** -- commit `e0c1c06` fixed "DuckDB lock conflicts and pipeline bugs."

**Why it happens:**
DuckDB is an embedded database designed for single-process analytics. Unlike PostgreSQL's client-server model, DuckDB locks the file at the OS level. The official DuckDB docs state: "Writing to DuckDB from multiple processes is not supported automatically and is not a primary design goal." Even read-only access from a second process can conflict if the first process is mid-write.

**How to avoid:**
1. All DuckDB/SQLite access goes through the Python FastAPI server -- never from Node.js directly
2. Next.js API routes are pure HTTP proxies to FastAPI; they never import DuckDB client libraries
3. The project's `DBFactory` in `src/shared/infrastructure/db_factory.py` manages all connections within the single Python process
4. If analytics queries are needed from Node.js (never recommended), export results to JSON files that Next.js can read without database access

**Warning signs:**
- `IOError: Could not set lock on file` errors in Python logs during dashboard usage
- Dashboard pages showing stale data while pipeline is running
- `duckdb`, `duckdb-async`, or `better-sqlite3` appearing in `package.json`
- Intermittent 500 errors on dashboard API routes that correlate with pipeline run times

**Phase to address:**
Phase 1 (Project Setup) -- establish the rule that Node.js never directly accesses DuckDB or SQLite. This constraint shapes the entire API route design.

---

### Pitfall 4: SSR/Hydration Mismatch with Real-Time Financial Data

**What goes wrong:**
Next.js server-renders pages with data fetched at request time (e.g., portfolio value = $47,231). By the time the browser hydrates the page (~100-500ms later), the real-time data may have changed (portfolio value = $47,245). React detects the mismatch between server HTML and client HTML, throws a hydration error, and falls back to full client-side rendering. This causes a visible flash of content and console warnings that pollute error monitoring.

**Why it happens:**
Financial dashboards show inherently dynamic data: prices, P&L, drawdown percentages, regime status. SSR assumes data is stable between server render and client hydration. The existing HTMX dashboard in `base.html` avoids this entirely because HTMX uses CSR with server-rendered HTML fragments (no hydration step). Migrating to Next.js introduces hydration as a new failure mode that did not exist before.

**How to avoid:**
Split components into two strict categories:

1. **SSR-safe (static structure):** Page layout, sidebar navigation, column headers, section titles. These render identically on server and client. Use Server Components.
2. **Client-only (dynamic data):** Portfolio values, P&L numbers, price tickers, chart canvases, drawdown gauges, regime badges. Use `"use client"` directive and fetch data on mount via `useEffect` or React Query/SWR.

```typescript
// SSR-safe shell + client-only dynamic data
export default function OverviewPage() {
  return (
    <DashboardLayout>           {/* Server Component -- static structure */}
      <Suspense fallback={<KpiSkeleton />}>
        <KpiCards />            {/* Client Component -- fetches on mount */}
      </Suspense>
      <EquityChart />           {/* dynamic import, ssr: false */}
      <HoldingsTable />         {/* Client Component -- fetches on mount */}
    </DashboardLayout>
  );
}
```

**Warning signs:**
- `Text content does not match server-rendered HTML` errors in browser console
- Visible flash of different numbers when page loads (price flicker)
- `suppressHydrationWarning` appearing on data-bearing elements (band-aid, not fix)
- Server Components importing hooks like `useState`, `useEffect`

**Phase to address:**
Phase 1 (Project Setup) -- define the SSR/CSR boundary as part of the component architecture. The `DashboardLayout` Server Component vs. data-bearing Client Components split must be decided before any page is built.

---

### Pitfall 5: SSE Streaming Broken by Next.js Response Buffering

**What goes wrong:**
The existing system uses SSE via `sse_starlette` to push domain events (`OrderFilledEvent`, `PipelineCompletedEvent`, `DrawdownAlertEvent`, `RegimeChangedEvent`) from `SSEBridge` in `src/dashboard/infrastructure/sse_bridge.py`. When migrating to Next.js, developers implement an SSE route handler that proxies the Python SSE stream. Next.js buffers the entire response until the handler function completes -- which for SSE is never. The client connects (200 status) but never receives events.

**Why it happens:**
Next.js Route Handlers default to buffering responses. SSE requires streaming: the response must be sent immediately and events pushed incrementally. The existing SSE endpoint at `/dashboard/events` works because FastAPI/Starlette has native streaming support via `EventSourceResponse`. Next.js requires explicit `ReadableStream` usage and specific headers to achieve the same behavior.

**How to avoid:**
Two options, in order of preference:

**Option A (Recommended): Direct browser-to-FastAPI SSE connection.**
Skip the Next.js SSE proxy entirely. The browser connects directly to `http://localhost:8000/dashboard/events`. This is the simplest approach with the fewest failure points. Requires CORS configuration on FastAPI to allow the Next.js origin.

**Option B: Next.js SSE proxy with ReadableStream.**
```typescript
// app/api/events/route.ts
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs'; // SSE does not work in Edge Runtime

export async function GET() {
  const stream = new ReadableStream({
    async start(controller) {
      const res = await fetch(process.env.INTERNAL_API_URL + '/dashboard/events');
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        controller.enqueue(new TextEncoder().encode(decoder.decode(value)));
      }
      controller.close();
    }
  });
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',  // Prevents nginx buffering
    },
  });
}
```

**Warning signs:**
- SSE connection established (200 status) but no events arrive in browser
- Events arrive all at once when the connection drops instead of incrementally
- `MaxListenersExceededWarning` on the Node.js server (memory leak from uncleaned event listeners)
- SSE works in development but breaks in production (nginx buffering, serverless timeout)

**Phase to address:**
Phase 1 (Project Setup) -- decide SSE architecture (direct vs. proxy). Phase 3 (Page Implementation) -- wire the actual event handling.

---

### Pitfall 6: Bundle Size Explosion from Multiple Charting Libraries

**What goes wrong:**
The existing dashboard loads Plotly.js from CDN (`plotly-3.4.0.min.js` -- 3.4 MB uncompressed, ~1 MB gzipped) for equity curves, drawdown gauges, and sector donuts (see `src/dashboard/presentation/charts.py`). The migration instinct is to `npm install plotly.js-dist` and import it alongside TradingView Lightweight Charts. Plotly alone is 1MB+ minified. Combined with TradingView (45KB), React (45KB), and Next.js framework code, the total JS bundle exceeds 1.5MB. Initial page load takes 3+ seconds.

**Why it happens:**
The three existing chart types (`build_equity_curve`, `build_drawdown_gauge`, `build_sector_donut`) are built with Plotly because the HTMX dashboard used CDN-loaded Plotly. Porting this to React means bundling Plotly into the JS payload instead of loading from CDN. The CDN approach hid the true cost.

**How to avoid:**
Replace ALL Plotly charts. Do not add Plotly to `package.json` at all.

| Current (Plotly) | Replacement | Size |
|-----------------|-------------|------|
| Equity curve (line chart) | TradingView Lightweight Charts `LineSeries` | 0KB additional (already needed) |
| Drawdown gauge | Pure CSS radial gauge with `conic-gradient` | 0KB JS |
| Sector donut | SVG `<circle>` with `stroke-dasharray` or CSS `conic-gradient` | 0KB JS |
| Candlestick chart | TradingView Lightweight Charts `CandlestickSeries` | 45KB total |

TradingView Lightweight Charts v5 bundle is 35-45KB and supports line, area, histogram, candlestick, and bar series. This covers all charting needs.

**Warning signs:**
- `plotly.js`, `plotly.js-dist`, or `react-plotly.js` in `package.json`
- `@next/bundle-analyzer` showing any single chunk > 200KB
- Lighthouse Performance score < 70 on dashboard pages
- Multiple charting library imports in the component tree

**Phase to address:**
Phase 1 (Project Setup) -- lock down the charting library decision to TradingView-only. Phase 2 (Design System) -- build CSS-based gauge and donut components.

---

### Pitfall 7: Dark Theme CSS Conflicts and Incomplete Styling

**What goes wrong:**
Building a Bloomberg-style dark theme requires every element to use dark colors: tables, inputs, scrollbars, chart tooltips, select dropdowns, focus rings, error messages. Developers set `bg-gray-900 text-white` on the body and assume everything inherits. Then TradingView chart tooltips render with white backgrounds, form inputs have browser-default light styling, scrollbars are white on Windows, and focus rings are invisible against dark backgrounds. The dashboard looks 90% dark with jarring light patches.

**Why it happens:**
Three layers of styling conflict:
1. **Browser defaults (user-agent stylesheet):** Light-themed. Form inputs, select dropdowns, scrollbars follow OS theme.
2. **Tailwind utilities:** Only apply to elements you explicitly style. Missing a single element leaves a light-colored gap.
3. **TradingView internal styles:** Charts have their own theming API separate from CSS. The `createChart()` options include `layout.background`, `layout.textColor`, etc. CSS classes do not affect canvas-rendered elements.

The existing HTMX dashboard uses `bg-gray-100 text-gray-900` (light theme, see `base.html` line 16). The Bloomberg redesign inverts this entirely. Every component must be re-evaluated.

**How to avoid:**
1. Define CSS custom properties as the single source of truth for all colors:
```css
:root {
  --bg-primary: #0a0e17;      /* Bloomberg deep navy */
  --bg-secondary: #111827;
  --bg-surface: #1a1f2e;
  --text-primary: #e5e7eb;
  --text-secondary: #9ca3af;
  --accent-green: #00c853;     /* Profit */
  --accent-red: #ff5252;       /* Loss */
  --border-color: #1f2937;
}
```
2. Configure TradingView chart colors explicitly in chart creation options (not CSS):
```typescript
createChart(container, {
  layout: { background: { color: '#0a0e17' }, textColor: '#e5e7eb' },
  grid: { vertLines: { color: '#1f2937' }, horzLines: { color: '#1f2937' } },
});
```
3. Style scrollbars: `::-webkit-scrollbar` for Chrome/Edge, `scrollbar-color` for Firefox
4. Override form element defaults with a CSS reset targeting `input`, `select`, `textarea`, `button`
5. Test every interactive state: hover, focus, active, disabled -- all must be visible on dark backgrounds
6. Use color accessibility guidelines from Bloomberg's own terminal design: avoid relying solely on red/green (8% of males are color-blind). Use directional arrows + text labels.

**Warning signs:**
- White flashes when hovering over interactive elements
- Form inputs with light backgrounds inside dark containers
- Chart tooltips unreadable (light text on light tooltip, or dark text on dark background)
- Focus rings invisible (default blue on dark blue background)
- Scrollbars appearing as white bars on Windows

**Phase to address:**
Phase 2 (Design System) -- build the complete design token system and dark CSS reset before any page component. Every component must consume tokens, never hardcode hex values.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `suppressHydrationWarning` on data elements | Silences console errors | Hides real bugs; data inconsistency between server/client goes unnoticed | Never for data-bearing elements; only for timestamps/dates |
| Importing Plotly.js alongside TradingView | Reuse existing Python chart code in React | 1MB+ bundle bloat, two chart APIs to maintain, two theming systems | Never -- replace Plotly entirely with TradingView + CSS |
| Polling FastAPI every second instead of SSE | Simpler to implement than SSE proxy | Unnecessary server load (4 endpoints x 1 req/sec = 240 req/min), delayed updates, battery drain | Only as fallback when SSE connection fails; use 30-second interval |
| `any` types for Python API response data | Faster initial TypeScript development | No compile-time safety; refactoring breaks silently; runtime errors in production | Only in prototype phase; replace with Zod schemas before Phase 3 |
| Single monolithic API route file | Quick to get all endpoints working | Untestable, hard to add per-route middleware, violates separation of concerns | Never -- one route handler per endpoint from the start |
| Hardcoded `http://localhost:8000` in components | Works immediately in development | Different URLs per environment; breaks in any non-local deployment | Never -- use `NEXT_PUBLIC_API_URL` and `INTERNAL_API_URL` environment variables |
| `"use client"` on every component | Avoids hydration errors entirely | Defeats SSR benefits; larger client bundle; slower initial page load | Never as a blanket approach; only on components that genuinely need browser APIs |

## Integration Gotchas

Common mistakes when connecting the Next.js frontend to the existing Python backend.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastAPI backend from SSR | Calling `localhost:8000` from Server Components -- fails in containerized/production environments where frontend and backend are on different hosts | Use env var `INTERNAL_API_URL` for server-side calls (can be Docker service name), `NEXT_PUBLIC_API_URL` for client-side calls |
| TradingView Lightweight Charts | Importing at module top level -- breaks SSR because it accesses `window` and `document` | Always use `dynamic(() => import('./Chart'), { ssr: false })` or guard with `typeof window !== 'undefined'` |
| SSE from Python backend | Proxying SSE through Next.js without streaming headers or `ReadableStream` | Either proxy with `ReadableStream` + correct headers (`X-Accel-Buffering: no`), or connect browser directly to FastAPI SSE endpoint |
| Alpaca WebSocket for live prices | Opening WebSocket connection in each React component independently | Use a singleton WebSocket manager at the app layout level; share data via React Context; reconnect with exponential backoff |
| DuckDB analytics data | Trying to query DuckDB from Node.js process (via npm package or subprocess) | All DuckDB access goes through FastAPI HTTP endpoints only; Next.js is a pure frontend/BFF consumer |
| SQLite operational data | Opening `.db` files from Node.js while Python FastAPI has them open | Same rule: all SQLite access through FastAPI; Node.js never touches `.db` files directly |
| CORS for direct SSE | Browser blocks direct SSE to FastAPI due to cross-origin (port 3000 -> port 8000) | Add CORS middleware to FastAPI: `allow_origins=["http://localhost:3000"]` for development |
| Pipeline POST actions | Sending form data (HTMX pattern) instead of JSON from React | Convert all POST endpoints to accept JSON body; the existing `Form(...)` parameters in routes.py need JSON alternatives |

## Performance Traps

Patterns that work at small scale but fail as data grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-rendering entire data table on every SSE event | Page freezes when multiple events fire rapidly (e.g., during pipeline run -- `PipelineCompletedEvent` + `OrderFilledEvent` + `RegimeChangedEvent` in seconds) | Use `React.memo` on row components; debounce SSE event processing to 100ms; only update rows whose data changed | > 5 SSE events per second |
| Creating new TradingView chart instance on every data update | Memory grows ~10MB per recreate; browser becomes sluggish after 10 updates | Use `series.update()` or `series.setData()` to update existing chart; never destroy and recreate | > 1 data update per minute |
| Fetching all holdings + all scores + all signals on every page load | API response grows linearly with portfolio size; 500ms+ response for 50+ holdings | Implement pagination; cache with SWR/React Query (30-second `staleTime`); fetch only visible data | > 50 holdings or > 200 scored symbols |
| Not virtualizing large scoring/signal tables | Signals page renders 400+ DOM rows (one per scored symbol); scrolling lags; layout paint takes 200ms+ | Use `@tanstack/react-virtual` for tables with > 50 rows | > 100 visible rows |
| Reconnecting SSE on every page navigation | Unnecessary connection churn; missed events during reconnection gap; server-side listener leak | Keep SSE connection at the root layout level (persists across page navigations within the `DashboardLayout`) | Every page transition |
| Fetching chart data (OHLCV) for every symbol on Signals page | Each symbol's mini-chart triggers a separate API call; 200 symbols = 200 concurrent requests | Only fetch chart data for visible/expanded rows; use intersection observer for lazy loading | > 20 visible charts |

## Security Mistakes

Domain-specific security issues for a trading dashboard.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Exposing Alpaca API keys via `NEXT_PUBLIC_` env vars | Key theft via browser DevTools -> unauthorized trades on live account | Keys stay in server-side env vars only (`ALPACA_PAPER_KEY`, `ALPACA_LIVE_KEY`); never prefix with `NEXT_PUBLIC_`; all broker calls through FastAPI |
| Allowing unauthenticated access to pipeline/approval API routes | Unauthorized user triggers pipeline run, approves trading strategy, or modifies budget | Add authentication middleware to all Next.js API routes, even for single-user deployment (prevents CSRF and network exposure) |
| Exposing internal FastAPI URL to browser | Attacker bypasses Next.js auth layer and directly accesses Python backend | `INTERNAL_API_URL` for Server Components/API routes only; `NEXT_PUBLIC_API_URL` points to Next.js, not FastAPI |
| Using Node.js subprocess APIs in API routes | Expands CVE-2025-55182 (React2Shell) attack surface; enables RCE via prototype pollution | Zero subprocess API imports in the codebase; use HTTP calls to FastAPI exclusively |
| Rendering full API keys/secrets in settings page | Keys visible in DOM, screenshots, screen-sharing sessions | Display only last 4 characters; mask rest with asterisks; never include keys in API responses |
| Serving dashboard on 0.0.0.0 without auth | Dashboard accessible to anyone on the network (WSL2 shares host network) | Bind to `127.0.0.1` for development; require authentication for any non-localhost binding |

## UX Pitfalls

Common user experience mistakes in Bloomberg-style financial dashboards.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Using red/green only for profit/loss | 8% of males are color-blind; cannot distinguish profit from loss | Red/green + directional arrows (up/down) + position shift + text labels ("PROFIT"/"LOSS"); follow Bloomberg's own accessibility guidelines |
| Tiny monospace text everywhere to maximize data density | Information-dense but unreadable; eye strain during extended monitoring | Minimum 12px for data cells, 14px for labels; provide 3 density modes (compact/normal/comfortable) via user toggle |
| Auto-refreshing entire page for real-time updates | Layout shift, scroll position lost, user loses context mid-analysis | SSE for incremental DOM updates; animate number transitions; never full-page reload for data refresh |
| Modal dialogs for trade approval | Blocks view of portfolio and risk data needed for approval decision | Use inline expansion or side panel; user needs portfolio context visible while approving trades |
| Loading states showing blank white space in dark theme | Jarring flash of light; user thinks dashboard is broken | Show skeleton screens using dark-themed pulsing animations (e.g., `bg-gray-800 animate-pulse`) matching expected data layout |
| No visual distinction between paper and live mode | User acts on paper data thinking it is real (or vice versa) | Persistent header banner: red `LIVE TRADING` or green `PAPER TRADING` (the existing HTMX dashboard already has this pattern in `base.html` lines 19-27; preserve it) |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Chart cleanup:** Chart renders correctly -- verify it also calls `chart.remove()` on unmount (navigate between all pages 20 times; DevTools Memory tab should show flat heap)
- [ ] **SSE reconnection:** SSE events arrive -- verify reconnection after network drop (disconnect WiFi for 5 seconds, reconnect; events should resume within 5 seconds)
- [ ] **Dark theme completeness:** Dashboard looks dark -- verify form inputs, select dropdowns, date pickers, scrollbars, chart tooltips, error toasts, loading skeletons are ALL dark-themed (screenshot every interactive state on both Chrome and Firefox)
- [ ] **Mobile responsiveness:** Pages render on desktop -- verify tables do not overflow on 768px width; charts resize; touch targets are minimum 44px
- [ ] **Error states:** Happy path works -- verify what happens when FastAPI is down (graceful "Backend unavailable" message, not white screen or infinite spinner); when SSE disconnects; when API returns 500
- [ ] **Loading states:** Data renders after load -- verify skeleton screens appear during initial fetch and during data refetch (SWR revalidation)
- [ ] **Browser compatibility:** Works in Chrome -- verify Firefox (scrollbar styling differs), Safari (SSE `EventSource` behavior differs), Edge
- [ ] **Stale data indicator:** Numbers display -- verify "Last updated: 2 min ago" timestamp so user knows if data is stale (especially critical if SSE connection drops silently)
- [ ] **Pipeline run during dashboard viewing:** Dashboard shows data -- verify dashboard remains functional and responsive while pipeline is actively running (potential DuckDB lock contention)
- [ ] **Paper/Live mode banner:** Banner exists -- verify it reads from actual execution mode via API, not from a hardcoded value; test with both modes
- [ ] **Bundle size:** Dashboard loads -- verify total JS payload is under 300KB gzipped (run `npx @next/bundle-analyzer` and check)

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Chart memory leaks shipped | LOW | Add `chart.remove()` to `useLayoutEffect` cleanup; deploy fix; memory recovers on next page load without data loss |
| Subprocess-based API architecture shipped | HIGH | Rewrite all API routes to HTTP proxy pattern; rebuild error handling; add authentication layer; 3-5 day effort |
| DuckDB lock conflicts in production | MEDIUM | Add retry logic with exponential backoff to Python query handlers; add read-only fallback mode; ensure WAL mode on SQLite files; schedule pipeline runs during low-dashboard-usage periods |
| Hydration errors across pages | LOW | Convert affected components to client-only with `dynamic(() => ..., { ssr: false })`; no data migration needed; deploy within hours |
| SSE not streaming through Next.js | MEDIUM | Switch from Next.js SSE proxy to direct browser-to-FastAPI SSE connection; requires adding CORS to FastAPI; 1-day effort |
| Bundle size too large (>500KB) | MEDIUM | Remove Plotly dependency; replace with CSS/SVG alternatives; code-split all chart components with dynamic imports; analyze with `@next/bundle-analyzer`; 1-2 day effort |
| Dark theme incomplete (light patches) | LOW | Audit all components with browser DevTools; add missing CSS custom property references; test on Windows (scrollbars) and Mac; incremental fix over 1-2 days |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Chart memory leaks (1) | Phase 1: Setup + Phase 2: Chart Components | Navigate between all 4 pages 20 times; DevTools Memory shows flat heap |
| Subprocess architecture (2) | Phase 1: Setup | Zero subprocess API imports: `grep -r 'child_process\|execSync\|spawn' frontend/` returns nothing |
| DuckDB lock conflicts (3) | Phase 1: Setup | No `duckdb` or `better-sqlite3` in `package.json`; all data via HTTP to FastAPI |
| SSR hydration mismatch (4) | Phase 1: Setup + Phase 3: Pages | Zero hydration warnings in browser console across all 4 pages |
| SSE buffering (5) | Phase 1: Architecture Decision + Phase 3: Pages | SSE events arrive within 1 second of domain event firing on Python side |
| Bundle size explosion (6) | Phase 1: Setup + Phase 2: Components | `next build` shows no chunk > 200KB; total JS < 300KB gzipped |
| Dark theme gaps (7) | Phase 2: Design System | Full visual audit: screenshot every component in every state; zero light-colored elements |
| Security: key exposure | Phase 1: Setup | `grep -r 'NEXT_PUBLIC_ALPACA' .` returns nothing; keys only in server-side env |
| Security: unauthenticated routes | Phase 1: Setup | All POST routes require authentication; test with unauthenticated requests |
| SSE reconnection | Phase 3: Pages | Disconnect network 10 seconds; SSE resumes within 5 seconds of reconnection |
| Large table performance | Phase 3: Pages | Render 200+ row signals table; scroll remains 60fps in Chrome DevTools Performance |
| Color accessibility | Phase 2: Design System | All profit/loss indicators have non-color differentiators (arrows, labels) |

## Sources

- [TradingView Lightweight Charts Advanced React Example](https://tradingview.github.io/lightweight-charts/tutorials/react/advanced) -- official cleanup patterns, parent-child hook ordering (HIGH confidence)
- [TradingView Memory Leak Issue #552](https://github.com/tradingview/lightweight-charts/issues/552) -- chart.remove() requirement (HIGH confidence)
- [TradingView Lightweight Charts v5 Release](https://www.tradingview.com/blog/en/tradingview-lightweight-charts-version-5-50837/) -- bundle size 35KB, enhanced tree-shaking (HIGH confidence)
- [DuckDB Concurrency Documentation](https://duckdb.org/docs/stable/connect/concurrency) -- single-writer model, no multi-process write support (HIGH confidence)
- [Next.js SSE Discussion #48427](https://github.com/vercel/next.js/discussions/48427) -- SSE buffering issues in Route Handlers (HIGH confidence)
- [Fixing Slow SSE Streaming in Next.js (Jan 2026)](https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996) -- X-Accel-Buffering header fix (MEDIUM confidence)
- [CVE-2025-55182 React2Shell Analysis (Datadog)](https://securitylabs.datadoghq.com/articles/cve-2025-55182-react2shell-remote-code-execution-react-server-components/) -- subprocess RCE, CVSS 10/10 (HIGH confidence)
- [CVE-2025-66478 Next.js RCE Advisory](https://nextjs.org/blog/CVE-2025-66478) -- additional Next.js security vulnerability (HIGH confidence)
- [Operation PCPcat: 59,000 Next.js Servers Hacked](https://thehgtech.com/articles/operation-pcpcat-nextjs-hack-2025.html) -- real-world exploitation of React2Shell (HIGH confidence)
- [Next.js Hydration Error Documentation](https://nextjs.org/docs/messages/react-hydration-error) -- official hydration mismatch guide (HIGH confidence)
- [Next.js Building APIs Guide (Feb 2025)](https://nextjs.org/blog/building-apis-with-nextjs) -- BFF pattern, Route Handler best practices (HIGH confidence)
- [Bloomberg Terminal Color Accessibility](https://www.bloomberg.com/company/stories/designing-the-terminal-for-color-accessibility/) -- red/green accessibility in financial terminals (HIGH confidence)
- [Tailwind CSS Dark Mode Documentation](https://tailwindcss.com/docs/dark-mode) -- class-based dark mode configuration (HIGH confidence)
- Project commit `e0c1c06`: "fix: resolve DuckDB lock conflicts and pipeline bugs" -- real-world evidence of Pitfall 3 in this codebase
- Project file `src/dashboard/presentation/app.py` -- existing SSE bridge, FastAPI bootstrap pattern
- Project file `src/dashboard/presentation/charts.py` -- existing Plotly dependency for 3 chart types
- Project file `src/dashboard/presentation/templates/base.html` -- existing Tailwind CDN, HTMX, light theme, paper/live banner

---
*Pitfalls research for: Bloomberg Dashboard (Next.js + TradingView) added to existing Python trading system*
*Researched: 2026-03-14*
