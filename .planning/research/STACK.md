# Technology Stack -- v1.3 Bloomberg Dashboard

**Project:** Intrinsic Alpha Trader -- Bloomberg-style Dashboard
**Researched:** 2026-03-14
**Confidence:** HIGH
**Scope:** NEW frontend stack for Next.js dashboard replacing HTMX+Jinja2. Python backend remains unchanged.

## Existing Stack (DO NOT change)

The Python backend is fully operational and stays as-is. The Next.js frontend consumes it.

| Already Have | Version | Relevant to v1.3 |
|-------------|---------|-------------------|
| FastAPI | 0.135.1 | Backend API server -- Next.js proxies to this |
| uvicorn | 0.41.0 | ASGI server hosting the FastAPI app |
| SSE (sse-starlette) | 2.0+ | Real-time event stream -- Next.js EventSource connects directly |
| SQLite + DuckDB | stdlib / 1.5.0 | Data stores -- no change, backend reads them |
| Alpaca TradingStream | alpaca-py 0.43.2 | WebSocket stream for order updates -- feeds SSE bridge |
| Plotly (server-side) | 6.5.0+ | **Replaced by TradingView Lightweight Charts on frontend** |
| HTMX + Jinja2 templates | 2.0.x CDN | **Replaced entirely by Next.js + React** |
| Tailwind CSS (CDN) | via cdn.tailwindcss.com | **Replaced by proper Tailwind v4 build** |

**Key architectural change:** The HTMX dashboard served HTML fragments from FastAPI. The Next.js dashboard serves a standalone React SPA that fetches JSON from the same FastAPI backend via `next.config.ts` rewrites (or `proxy.ts` in Next.js 16). The FastAPI dashboard routes (`/dashboard/*`) that return HTML become JSON API routes, or the existing query handlers are exposed as new JSON endpoints alongside the old HTML ones during migration.

---

## New Frontend Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js | 16.1.x | React meta-framework with App Router | Latest stable (released Oct 2025). Turbopack default for 2-5x faster builds. App Router for layouts, loading states, streaming. `proxy.ts` replaces middleware for cleaner API proxying to FastAPI. React Compiler support (stable) eliminates manual memoization. Node.js 20.9+ required (project runs 22.x). |
| React | 19.2.x | UI library | Bundled with Next.js 16. View Transitions for page animations. `<Activity>` for background rendering (sidebar state preservation). React Compiler auto-memoizes -- no more `useMemo`/`useCallback` boilerplate. |
| TypeScript | 5.x | Type safety | Enforced by `create-next-app` default. Catches integration bugs between API response shapes and component props. |

**Why Next.js 16 and not 15:** Next.js 16 ships Turbopack as default (no config), has stable React Compiler support, and the new `proxy.ts` is cleaner for API proxying to FastAPI than `next.config.ts` rewrites. Next.js 15 still works but requires explicit Turbopack opt-in and has experimental React Compiler.

### Charting

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| lightweight-charts | 5.1.x | TradingView candlestick charts | The industry standard for financial web charts. 45KB gzipped -- smallest performant charting library. HTML5 canvas rendering handles large datasets (1000+ candles) without DOM overhead. Built-in candlestick, line, area, histogram series. Plugin system for custom indicators. v5.1.0 added data conflation for very large datasets. Free and open-source (Apache 2.0). |

**Why NOT Plotly.js on the frontend:** Plotly.js is 1.2MB+ minified. `lightweight-charts` is 45KB. For a Bloomberg-style dashboard that renders multiple charts simultaneously, bundle size matters. Plotly's strength is Python-side generation (which we used in HTMX); for a React app, TradingView's library is purpose-built for this use case.

**Why NOT recharts or chart.js:** Neither has proper financial chart support (OHLC candlesticks, time-price axes, crosshair sync). TradingView Lightweight Charts is the only serious option for professional trading UIs.

**React integration pattern (from official docs, v5.1):**

```typescript
// Direct useRef + useEffect -- NO third-party wrapper needed
import { createChart, CandlestickSeries } from 'lightweight-charts';

function CandlestickChart({ data }: { data: OHLCData[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const chart = createChart(containerRef.current!, {
      layout: { background: { color: '#1a1a2e' }, textColor: '#e0e0e0' },
      grid: { vertLines: { color: '#2a2a3e' }, horzLines: { color: '#2a2a3e' } },
    });
    const series = chart.addSeries(CandlestickSeries);
    series.setData(data);

    return () => chart.remove();
  }, [data]);

  return <div ref={containerRef} style={{ width: '100%', height: '400px' }} />;
}
```

**Do NOT use community React wrappers** (`kaktana-react-lightweight-charts`, `lightweight-charts-react-wrapper`). They are unmaintained third-party packages that lag behind v5.x. The official TradingView docs recommend direct `useRef`+`useEffect` integration. It is 20 lines of code.

### State Management

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| @tanstack/react-query | 5.90.x | Server state (API data fetching, caching, refetching) | Handles all FastAPI data fetching with automatic caching, background refetch, stale-while-revalidate. Eliminates custom `useEffect` + `useState` data fetching patterns. ~5M weekly npm downloads. Provides `useQuery` for reads and `useMutation` for writes (trade approvals, pipeline triggers). |
| zustand | 5.0.x | Client state (UI state, dashboard layout, filter selections) | 2KB bundle. No boilerplate (no providers, no reducers). Perfect for UI-only state: active tab, sidebar collapse, selected ticker, filter preferences. Persists to localStorage for session continuity. |

**Why this combination:** TanStack Query owns server state (what comes from FastAPI). Zustand owns client state (what the user is doing in the UI). This is the dominant pattern in 2026 React apps. They do not overlap.

**Why NOT Redux:** Overkill for a single-user dashboard. Redux requires boilerplate (slices, actions, reducers, middleware). Zustand + TanStack Query achieves the same result with ~60% less code.

**Why NOT React Context alone:** Context triggers full re-renders on any state change. For a data-dense Bloomberg dashboard with multiple panels, this causes visible performance issues. Zustand uses external stores with selective subscriptions.

### Styling & Design System

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Tailwind CSS | 4.x | Utility-first CSS framework | v4 is CSS-first config (no `tailwind.config.js`). 5x faster full builds, 100x faster incremental. Ships with `create-next-app` default. Already familiar from existing HTMX dashboard (was using CDN version). Dark theme via CSS custom properties. |
| shadcn/ui | latest | Accessible React components (tables, dropdowns, dialogs, tabs) | NOT a dependency -- components are copied into the project source. Built on Radix UI primitives (fully accessible). Styled with Tailwind. Data Table component wraps TanStack Table for sortable/filterable data grids. Dark mode works out of the box via CSS variables. |
| next-themes | 0.4.x | Dark/light theme management | 2-line setup for dark mode. Prevents flash of wrong theme on load. System preference detection. We default to dark (Bloomberg style) but the toggle is trivial. |

**Bloomberg dark theme approach:** Define CSS custom properties in `globals.css` under `:root` (light) and `.dark` (dark) classes. Tailwind v4 reads these via `@theme`. shadcn/ui components automatically adapt.

```css
/* Bloomberg-style color tokens */
.dark {
  --background: 222.2 84% 4.9%;      /* near-black */
  --foreground: 210 40% 98%;          /* off-white text */
  --card: 222.2 84% 6.9%;            /* slightly lighter panels */
  --muted: 217.2 32.6% 17.5%;        /* disabled/secondary */
  --accent: 210 40% 45%;             /* Bloomberg blue */
  --destructive: 0 62.8% 60.6%;      /* red for losses */
  --success: 142 76% 36%;            /* green for gains */
}
```

**Why NOT Material UI / Chakra UI / Ant Design:** All are full component libraries with their own CSS-in-JS runtime. They add 100-300KB+ to the bundle and fight with Tailwind. shadcn/ui is zero-runtime -- it copies source code into your project. You own it, you customize it, no library overhead.

### Data Tables

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| @tanstack/react-table | 8.x | Headless table logic (sorting, filtering, pagination) | Headless -- renders nothing, provides logic only. shadcn/ui Data Table component wraps this. Handles column sorting, faceted filtering, row selection, column visibility for holdings tables, signal lists, scoring heatmaps. |

**This is pulled in by shadcn/ui Data Table**, not installed separately. When you run `npx shadcn@latest add data-table`, it installs `@tanstack/react-table` as a dependency.

### Real-Time Data

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Native EventSource API | Browser built-in | SSE client for real-time updates from FastAPI | No library needed. The browser's `EventSource` API connects to FastAPI's existing `/dashboard/events` SSE endpoint. Wrap in a custom React hook (`useSSE`) that parses events and feeds them to TanStack Query's cache via `queryClient.setQueryData()`. Auto-reconnect is built into the EventSource spec. |

**Why NOT Socket.IO / WebSocket client library:** The existing FastAPI backend uses SSE (Server-Sent Events) via `sse-starlette`. SSE is unidirectional (server to client), which is exactly what we need -- the dashboard receives order updates, regime changes, and pipeline status. The one bidirectional action (approve trade, trigger pipeline) uses regular HTTP POST via TanStack Query `useMutation`. No WebSocket complexity needed.

**SSE integration pattern:**

```typescript
// hooks/useSSE.ts
function useSSE(url: string) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const es = new EventSource(url);

    es.addEventListener('order_update', (e) => {
      const data = JSON.parse(e.data);
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    });

    es.addEventListener('regime_change', (e) => {
      const data = JSON.parse(e.data);
      queryClient.setQueryData(['regime'], data);
    });

    return () => es.close();
  }, [url, queryClient]);
}
```

### Build & Dev Tooling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Turbopack | (bundled with Next.js 16) | Dev server & production bundler | Default in Next.js 16 -- no configuration needed. 2-5x faster production builds than Webpack. Up to 10x faster Fast Refresh. File system caching (beta) for even faster subsequent starts. |
| Biome | 2.x | Linting + formatting (replaces ESLint + Prettier) | Next.js 16 removed the `next lint` command. Biome combines linting and formatting in one tool, is 35x faster than ESLint, and handles TypeScript/JSX natively. One config file, one tool. |

**Why Biome and not ESLint:** Next.js 16 explicitly removed `next lint` and recommends using Biome or ESLint directly. Biome is faster, requires less configuration, and handles both linting and formatting (replacing Prettier too). For a new project, Biome is the cleaner choice.

---

## Integration Architecture: Next.js <-> FastAPI

### API Proxying

The Next.js app proxies API requests to the FastAPI backend. Two approaches available in Next.js 16:

**Option A: `proxy.ts` (recommended for Next.js 16)**

```typescript
// src/proxy.ts
import { NextRequest, NextResponse } from 'next/server';

export default function proxy(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const url = new URL(request.nextUrl.pathname, 'http://127.0.0.1:8000');
    return NextResponse.rewrite(url);
  }
}
```

**Option B: `next.config.ts` rewrites (simpler, proven)**

```typescript
// next.config.ts
const nextConfig = {
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://127.0.0.1:8000/api/:path*' },
      { source: '/dashboard/events', destination: 'http://127.0.0.1:8000/dashboard/events' },
    ];
  },
};
```

**Recommendation:** Start with Option B (rewrites) because it is simpler and proven. Migrate to `proxy.ts` later if you need conditional logic (e.g., auth header injection).

### SSE Proxying

The SSE endpoint (`/dashboard/events`) must be proxied without buffering. Next.js rewrites handle this correctly for SSE because they are transparent HTTP proxies -- the response streams through without Next.js buffering it.

### Backend Changes Needed

The existing HTMX dashboard routes return HTML. For the Next.js frontend, the same query handlers need JSON endpoints:

| Existing Route | Returns | New Route | Returns |
|---------------|---------|-----------|---------|
| `GET /dashboard/` | HTML (overview page) | `GET /api/dashboard/overview` | JSON |
| `GET /dashboard/signals` | HTML (signals page) | `GET /api/dashboard/signals` | JSON |
| `GET /dashboard/risk` | HTML (risk page) | `GET /api/dashboard/risk` | JSON |
| `GET /dashboard/pipeline` | HTML (pipeline page) | `GET /api/dashboard/pipeline` | JSON |
| `POST /dashboard/pipeline/run` | HTML partial | `POST /api/dashboard/pipeline/run` | JSON |
| `POST /dashboard/pipeline/approve` | HTML partial | `POST /api/dashboard/pipeline/approve` | JSON |
| `GET /dashboard/events` (SSE) | SSE stream | `GET /dashboard/events` (SSE) | SSE stream (unchanged) |

The existing `OverviewQueryHandler`, `SignalsQueryHandler`, `RiskQueryHandler`, `PipelineQueryHandler` already produce Python dicts. The new JSON routes just call `handler.handle()` and return `JSONResponse(data)` instead of `templates.TemplateResponse(...)`. Minimal backend change.

---

## Project Structure

```
trading/
  dashboard/                    # NEW: Next.js project root
    src/
      app/                      # App Router pages
        layout.tsx              # Root layout (dark theme, sidebar)
        page.tsx                # Overview page (redirects to /overview)
        overview/
          page.tsx              # Portfolio, P&L, equity curve
        signals/
          page.tsx              # Scoring heatmap, signal recommendations
        risk/
          page.tsx              # Drawdown, sector exposure, regime
        pipeline/
          page.tsx              # Pipeline runs, approval, review
      components/
        charts/
          CandlestickChart.tsx  # TradingView lightweight-charts wrapper
          EquityCurve.tsx       # Line chart for portfolio equity
          DrawdownGauge.tsx     # Visual drawdown indicator
        tables/
          HoldingsTable.tsx     # shadcn/ui DataTable for positions
          SignalsTable.tsx      # Scoring + signals data grid
        layout/
          Sidebar.tsx           # Navigation sidebar
          Header.tsx            # Mode banner (LIVE/PAPER), status
          KPICard.tsx           # Metric card component
        ui/                     # shadcn/ui generated components
          button.tsx
          card.tsx
          table.tsx
          tabs.tsx
          ...
      hooks/
        useSSE.ts               # SSE connection to FastAPI
        useDashboard.ts         # TanStack Query hooks for each page
      lib/
        api.ts                  # API client (fetch wrapper)
        utils.ts                # Formatting (currency, %, dates)
      stores/
        ui-store.ts             # Zustand store for UI state
      types/
        api.ts                  # TypeScript types matching FastAPI response shapes
    public/
      fonts/                    # JetBrains Mono or similar monospace
    next.config.ts
    tailwind.css                # Tailwind v4 CSS-first config
    tsconfig.json
    package.json
  src/                          # EXISTING: Python backend (unchanged)
    dashboard/                  # Existing HTMX dashboard (kept during migration, removed after)
    ...
```

---

## Installation

```bash
# Create Next.js project inside trading repo
cd /home/mqz/workspace/trading
npx create-next-app@latest dashboard \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --turbopack \
  --no-import-alias

# Core dependencies
cd dashboard
npm install lightweight-charts @tanstack/react-query zustand next-themes

# shadcn/ui initialization (copies components into project)
npx shadcn@latest init
# Select: dark theme, zinc color, CSS variables

# Add specific shadcn components
npx shadcn@latest add button card table tabs badge separator
npx shadcn@latest add data-table  # pulls in @tanstack/react-table

# Dev tooling
npm install -D @biomejs/biome
npx biome init
```

**Total npm packages added to `package.json`:**

| Package | Type | Size (gzipped) |
|---------|------|----------------|
| next | core | ~130KB (framework) |
| react + react-dom | core | ~45KB |
| lightweight-charts | runtime | ~45KB |
| @tanstack/react-query | runtime | ~40KB |
| zustand | runtime | ~2KB |
| next-themes | runtime | ~2KB |
| @tanstack/react-table | runtime | ~15KB (via shadcn) |
| @biomejs/biome | devDep | n/a (dev only) |
| tailwindcss + postcss | devDep | n/a (build only) |

**Client bundle overhead:** ~150KB gzipped for all runtime deps. This is smaller than Plotly.js alone (1.2MB).

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Framework | Next.js 16 | Vite + React | Vite lacks SSR, layouts, file-based routing, proxy built-in. Next.js provides all of these out of the box. For a dashboard that will eventually have SEO needs (commercial product), Next.js is the better foundation. |
| Framework | Next.js 16 | Next.js 15 | Still works, but 15 requires explicit Turbopack opt-in, has experimental React Compiler, and uses `middleware.ts` instead of cleaner `proxy.ts`. Since this is a new project (not migration), start with 16. |
| Charts | lightweight-charts 5.1 | Plotly.js | 1.2MB bundle vs 45KB. Plotly excels in Python-side generation (HTMX pattern); lightweight-charts excels in client-side React rendering. Different tools for different architectures. |
| Charts | lightweight-charts 5.1 | recharts | No OHLC candlestick support. Not designed for financial charts. Fine for generic dashboards, wrong for trading terminals. |
| Charts | lightweight-charts 5.1 | D3.js | Low-level -- would need to build every chart type from scratch. Lightweight Charts provides financial charts out of the box. |
| State | TanStack Query + Zustand | Redux Toolkit | RTK requires ~3x more boilerplate (slices, thunks, selectors). TanStack Query handles the server-state part better than RTK Query for simple API consumption. |
| State | TanStack Query + Zustand | React Context | Context re-renders all consumers on any change. For a dashboard with 10+ data panels, this is a performance problem. Zustand has selective subscriptions. |
| Styling | Tailwind + shadcn/ui | Material UI (MUI) | MUI adds 200KB+ runtime, has its own CSS-in-JS engine (Emotion), and fights with Tailwind. shadcn/ui is zero-runtime, Tailwind-native. |
| Styling | Tailwind + shadcn/ui | Chakra UI | Same problem as MUI -- runtime CSS-in-JS, conflicts with Tailwind. Also less actively maintained in 2026. |
| Tables | @tanstack/react-table (via shadcn) | AG-Grid | AG-Grid Community is 500KB+. Overkill for 4 tables in a personal dashboard. TanStack Table is headless, 15KB, and integrated with shadcn/ui. |
| Real-time | Native EventSource | Socket.IO | Socket.IO requires a Node.js server component. Our backend is Python+FastAPI using SSE. EventSource API is the native browser client for SSE. Zero additional dependencies. |
| Real-time | Native EventSource | Custom WebSocket | Would require rewriting the FastAPI SSE infrastructure to WebSocket. SSE is sufficient for server-push (order updates, regime changes). No bidirectional need. |
| Dark theme | next-themes | CSS prefers-color-scheme only | next-themes prevents flash of wrong theme on page load (injects script before React hydration). Pure CSS approach causes visible theme flash. |
| Linting | Biome | ESLint + Prettier | Next.js 16 removed `next lint`. Biome is 35x faster, combines linting and formatting, single config. For a new project, Biome is simpler. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Plotly.js (frontend) | 1.2MB bundle. Wrong tool for client-side React charts. Was correct for HTMX (server-side generation). | lightweight-charts (45KB) |
| Redux / Redux Toolkit | Boilerplate overhead for a single-user dashboard. No shared state across browser tabs. | Zustand (UI state) + TanStack Query (server state) |
| Socket.IO / ws | Backend uses SSE, not WebSocket. Adding WebSocket requires rewriting the SSE bridge. | Native EventSource API |
| Material UI / Chakra UI | CSS-in-JS runtime conflicts with Tailwind. Large bundles. | shadcn/ui (zero runtime, Tailwind-native) |
| AG-Grid | 500KB+ for a library when we have 4 tables. | @tanstack/react-table via shadcn Data Table |
| Storybook | Overhead for a personal dashboard. Component library design tool for teams, not solo projects. | Develop components directly in pages |
| Jest | Next.js 16 recommends Vitest for App Router testing. | Vitest (if frontend tests needed) |
| Prisma / Drizzle | No database on the frontend. All data comes from FastAPI backend. | FastAPI JSON endpoints via TanStack Query |
| NextAuth.js | Single-user personal dashboard. Auth is unnecessary. If commercial later, add then. | None -- or simple API key header if needed |
| Docker (for Next.js) | Single-instance personal deployment. `npm run build && npm start` is sufficient. | Direct Node.js process |
| Framer Motion | Animation library. Bloomberg terminals are not animated -- they are data-dense and static. | CSS transitions for minimal UI feedback |

---

## Version Compatibility Matrix

| Package | Version | Requires | Compatible With |
|---------|---------|----------|-----------------|
| Next.js 16.1.x | latest | Node.js 20.9+ | Node.js 22.x (project) |
| React 19.2.x | bundled with Next.js 16 | -- | Next.js 16 |
| TypeScript 5.x | bundled with create-next-app | -- | Next.js 16 |
| lightweight-charts 5.1.x | latest | -- | Any React (DOM rendering) |
| @tanstack/react-query 5.90.x | latest | React 18+ | React 19.2 |
| zustand 5.0.x | latest | React 18+ | React 19.2 |
| Tailwind CSS 4.x | latest | PostCSS | Next.js 16 (via @tailwindcss/postcss) |
| next-themes 0.4.x | latest | Next.js 13+ | Next.js 16 |
| @biomejs/biome 2.x | latest | -- | Any project |
| shadcn/ui | CLI-based, no version | Tailwind CSS, React | Tailwind v4 + React 19 |

**No version conflicts identified.** All packages are current stable releases compatible with each other.

---

## Key Stack Decisions for v1.3

1. **Next.js 16 over keeping HTMX** -- The HTMX dashboard works but cannot achieve Bloomberg-level data density, synchronized multi-panel layouts, client-side chart interactions (zoom, crosshair, time range selection), or smooth loading states. Next.js provides the component model, routing, and streaming needed for a professional trading UI.

2. **Lightweight Charts over Plotly.js** -- Plotly.js was the right choice for HTMX (generate chart HTML on the server). For a React app, TradingView Lightweight Charts is 26x smaller, renders directly in the browser via canvas, and is the industry standard for financial charting.

3. **TanStack Query + Zustand over Redux** -- Server state (API data) and client state (UI preferences) are separate concerns. TanStack Query handles caching, refetching, and loading states for API calls. Zustand handles which tab is active, sidebar state, and filter selections. Together they replace Redux with less code.

4. **shadcn/ui over full component library** -- shadcn/ui copies component source code into the project. No library dependency, no version conflicts, full customization control. The Data Table component wraps TanStack Table for sortable/filterable grids. Dark mode via CSS variables matches the Bloomberg aesthetic.

5. **Native EventSource over WebSocket library** -- The existing FastAPI SSE bridge (`SSEBridge` class in `src/dashboard/infrastructure/sse_bridge.py`) already broadcasts domain events. The React frontend connects via the browser's built-in `EventSource` API. Zero additional dependencies on either side.

6. **Biome over ESLint + Prettier** -- Next.js 16 removed `next lint`. Starting fresh with Biome gives a single fast tool for both linting and formatting.

7. **API proxy via `next.config.ts` rewrites** -- The Next.js dev server proxies `/api/*` requests to FastAPI at `http://127.0.0.1:8000`. In production, both run on the same machine. This is simpler than CORS configuration and matches the existing single-process deployment model.

---

## Sources

- [Next.js 16 Release Blog](https://nextjs.org/blog/next-16) -- Turbopack stable, React Compiler, proxy.ts, React 19.2 (HIGH confidence)
- [Next.js 16.1 Release Blog](https://nextjs.org/blog/next-16-1) -- Latest patch (HIGH confidence)
- [Next.js 16 Upgrade Guide](https://nextjs.org/docs/app/guides/upgrading/version-16) -- Breaking changes, Node.js 20.9+ requirement (HIGH confidence)
- [TradingView Lightweight Charts Official Docs](https://tradingview.github.io/lightweight-charts/) -- v5.1, React integration tutorials (HIGH confidence)
- [TradingView Lightweight Charts npm](https://www.npmjs.com/package/lightweight-charts) -- v5.1.0, published ~3 months ago (HIGH confidence)
- [TradingView Lightweight Charts React Basic Tutorial](https://tradingview.github.io/lightweight-charts/tutorials/react/simple) -- useRef+useEffect pattern (HIGH confidence)
- [TradingView Lightweight Charts React Advanced Tutorial](https://tradingview.github.io/lightweight-charts/tutorials/react/advanced) -- Component-based architecture (HIGH confidence)
- [@tanstack/react-query npm](https://www.npmjs.com/package/@tanstack/react-query) -- v5.90.21, published ~1 month ago (HIGH confidence)
- [zustand npm](https://www.npmjs.com/package/zustand) -- v5.0.11, published ~1 month ago (HIGH confidence)
- [shadcn/ui Dark Mode Next.js Guide](https://ui.shadcn.com/docs/dark-mode/next) -- next-themes integration (HIGH confidence)
- [shadcn/ui Data Table Component](https://ui.shadcn.com/docs/components/radix/data-table) -- TanStack Table integration (HIGH confidence)
- [Tailwind CSS v4 Release](https://tailwindcss.com/blog/tailwindcss-v4) -- CSS-first config, performance improvements (HIGH confidence)
- [next-themes GitHub](https://github.com/pacocoursey/next-themes) -- Flash prevention, system preference (HIGH confidence)
- [State of React State Management 2026](https://www.pkgpulse.com/blog/state-of-react-state-management-2026) -- TanStack Query + Zustand dominant pattern (MEDIUM confidence)
- [Next.js 16 Proxy Architecture](https://learnwebcraft.com/learn/nextjs/nextjs-16-proxy-ts-changes-everything) -- proxy.ts patterns (MEDIUM confidence)
- Direct codebase analysis: `src/dashboard/infrastructure/sse_bridge.py` confirms SSEBridge with asyncio queues (HIGH confidence)
- Direct codebase analysis: `src/dashboard/presentation/routes.py` confirms HTMX template rendering with query handlers (HIGH confidence)
- Direct codebase analysis: `src/dashboard/presentation/templates/base.html` confirms Tailwind CDN + HTMX + Plotly.js CDN (HIGH confidence)

---
*Stack research for: v1.3 Bloomberg Dashboard (Next.js)*
*Researched: 2026-03-14*
*All versions verified against npm registry + official documentation on 2026-03-14*
