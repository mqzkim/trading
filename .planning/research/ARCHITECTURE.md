# Architecture Research: v1.3 Bloomberg Dashboard (Next.js + React)

**Domain:** Bloomberg-style trading dashboard replacing HTMX+Jinja2 with Next.js+React, integrating with existing Python/FastAPI backend
**Researched:** 2026-03-14
**Confidence:** HIGH

---

## Standard Architecture

### System Overview

```
                          v1.3 Target Architecture
 ======================================================================

  Browser (React SPA)
  +---------------------------------------------------------+
  | Next.js App (localhost:3000)                             |
  |                                                         |
  |  /overview    /signals     /risk      /pipeline         |
  |  [React]      [React]      [React]    [React]           |
  |                                                         |
  |  TradingView     shadcn/ui         Recharts/            |
  |  Lightweight     Data Tables       Lightweight          |
  |  Charts                            Charts               |
  |                                                         |
  |  EventSource (SSE) ----+                                |
  +--------------------------|----- |-----------------------+
                             |      |
            next.config.js rewrites (proxy)
              /api/* --> localhost:8000/api/*
              /dashboard/events --> localhost:8000/dashboard/events
                             |      |
  +--------------------------|----- |-----------------------+
  | FastAPI (localhost:8000)  |      |                      |
  |                          v      v                       |
  |  /api/dashboard/*    /dashboard/events (SSE)            |
  |  [JSON REST]         [SSE stream]                       |
  |                                                         |
  |  DashboardQueryHandlers  -->  bootstrap ctx             |
  |  (overview, signals,         (repos, handlers,          |
  |   risk, pipeline)             bus, adapters)            |
  |                                                         |
  |  Commercial API (/api/v1/*)                             |
  |  [Unchanged]                                            |
  +---------------------------------------------------------+
                             |
  +--------------------------+------------------------------+
  |  Data Layer                                             |
  |  SQLite (operational)    DuckDB (analytics)             |
  |  Alpaca (broker)         yfinance/EDGAR (data)          |
  +---------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Next.js App | UI rendering, client-side interactivity, route management | App Router with pages for each dashboard view |
| Next.js API Routes | Proxy layer to FastAPI, optional BFF (Backend-for-Frontend) transforms | Route handlers calling FastAPI via `fetch()` |
| FastAPI Dashboard API | JSON REST endpoints replacing Jinja2 template rendering | New `/api/dashboard/*` routes returning JSON |
| FastAPI SSE Bridge | Real-time domain event streaming to browser | Existing SSEBridge, unchanged |
| TradingView Charts | Candlestick charts, equity curves, technical indicators | `lightweight-charts` v5.x with React wrapper |
| shadcn/ui Components | Data tables, gauges, badges, cards, dark theme | Vendored components with Tailwind CSS |
| Dashboard Query Handlers | Aggregate data from multiple bounded contexts | Existing `OverviewQueryHandler`, `SignalsQueryHandler`, etc. |
| Bootstrap Context | Composition root wiring all repos and handlers | Existing `bootstrap.py`, no changes needed |

---

## Recommended Project Structure

The dashboard is a **separate directory at the project root**, not inside `src/` (which is the Python DDD codebase). This keeps the TypeScript/Node.js toolchain completely isolated from the Python toolchain.

```
trading/                          # Project root
├── dashboard/                    # NEW: Next.js frontend
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── .env.local                # NEXT_PUBLIC_API_URL=http://localhost:8000
│   ├── public/
│   │   └── favicon.ico
│   └── src/
│       ├── app/                  # App Router pages
│       │   ├── layout.tsx        # Root layout (dark theme, sidebar nav)
│       │   ├── page.tsx          # Overview page (redirect or default)
│       │   ├── overview/
│       │   │   └── page.tsx      # Portfolio overview
│       │   ├── signals/
│       │   │   └── page.tsx      # Scoring + signal recommendations
│       │   ├── risk/
│       │   │   └── page.tsx      # Drawdown, sector exposure, regime
│       │   └── pipeline/
│       │       └── page.tsx      # Pipeline runs, approval, review
│       ├── components/           # Shared React components
│       │   ├── ui/               # shadcn/ui vendored primitives
│       │   │   ├── button.tsx
│       │   │   ├── card.tsx
│       │   │   ├── data-table.tsx
│       │   │   ├── badge.tsx
│       │   │   └── ...
│       │   ├── layout/           # Layout components
│       │   │   ├── sidebar.tsx
│       │   │   ├── header.tsx
│       │   │   └── mode-banner.tsx
│       │   ├── charts/           # Chart components
│       │   │   ├── equity-curve.tsx
│       │   │   ├── candlestick-chart.tsx
│       │   │   ├── drawdown-gauge.tsx
│       │   │   └── sector-donut.tsx
│       │   ├── overview/         # Page-specific components
│       │   │   ├── kpi-cards.tsx
│       │   │   ├── holdings-table.tsx
│       │   │   └── trade-history.tsx
│       │   ├── signals/
│       │   │   ├── scoring-table.tsx
│       │   │   └── signal-cards.tsx
│       │   ├── risk/
│       │   │   ├── risk-metrics.tsx
│       │   │   └── regime-badge.tsx
│       │   └── pipeline/
│       │       ├── pipeline-runs.tsx
│       │       ├── approval-panel.tsx
│       │       └── review-queue.tsx
│       ├── hooks/                # Custom React hooks
│       │   ├── use-sse.ts        # SSE EventSource hook
│       │   ├── use-api.ts        # Fetch wrapper with error handling
│       │   └── use-interval.ts   # Polling fallback
│       ├── lib/                  # Utilities
│       │   ├── api-client.ts     # Typed fetch wrapper
│       │   ├── formatters.ts     # Currency, percentage, date formatting
│       │   └── constants.ts      # API URLs, refresh intervals
│       └── types/                # TypeScript types
│           ├── overview.ts       # OverviewData, Position, TradeHistory
│           ├── signals.ts        # ScoreRow, SignalData
│           ├── risk.ts           # RiskMetrics, SectorWeight
│           └── pipeline.ts       # PipelineRun, ApprovalStatus, ReviewItem
├── src/                          # Python DDD codebase (UNCHANGED)
│   ├── dashboard/                # MODIFIED: add JSON API routes
│   │   ├── presentation/
│   │   │   ├── api_routes.py     # NEW: JSON REST endpoints
│   │   │   ├── routes.py         # KEEP: HTMX routes (deprecated, remove later)
│   │   │   ├── app.py            # MODIFIED: mount api_routes
│   │   │   └── templates/        # KEEP temporarily, remove after migration
│   │   ├── application/
│   │   │   └── queries.py        # UNCHANGED: reuse query handlers
│   │   └── infrastructure/
│   │       └── sse_bridge.py     # UNCHANGED: SSE streaming
│   ├── scoring/                  # UNCHANGED
│   ├── signals/                  # UNCHANGED
│   ├── portfolio/                # UNCHANGED
│   ├── execution/                # UNCHANGED
│   ├── regime/                   # UNCHANGED
│   ├── pipeline/                 # UNCHANGED
│   ├── approval/                 # UNCHANGED
│   └── bootstrap.py              # UNCHANGED
├── commercial/                   # UNCHANGED
├── cli/                          # UNCHANGED
├── pyproject.toml                # UNCHANGED
└── .gitignore                    # ADD: dashboard/node_modules, dashboard/.next
```

### Structure Rationale

- **`dashboard/` at root, not inside `src/`:** The Python `src/` directory has its own package resolution, mypy configuration, and ruff rules. Mixing Node.js files into it would break Python tooling. A sibling directory keeps toolchains isolated while sharing the same Git repo.
- **Not a Turborepo/monorepo tool:** This project has exactly two units (Python backend, Next.js frontend). Turborepo adds complexity for no benefit at this scale. A simple `package.json` with scripts is sufficient.
- **`src/dashboard/presentation/api_routes.py` (new):** The existing `queries.py` handlers return Python dicts. Currently these dicts feed Jinja2 templates. The new `api_routes.py` wraps the same handlers but returns JSON via FastAPI's `JSONResponse`. Zero business logic duplication.
- **`components/ui/` for shadcn:** shadcn/ui components are vendored (copied into project), not installed as a package. This is by design -- you own the code and can customize it freely.
- **Page-specific component folders:** Each page (`overview/`, `signals/`, `risk/`, `pipeline/`) gets its own component subfolder. This matches the existing 4-page structure and keeps components close to their consumers.

---

## Architectural Patterns

### Pattern 1: Next.js Rewrites as API Proxy

**What:** `next.config.ts` rewrites forward `/api/*` requests from the Next.js dev server to the FastAPI backend at `localhost:8000`. The browser never contacts FastAPI directly.

**When to use:** Always in development. In production, use the same pattern or a reverse proxy (nginx/Caddy).

**Trade-offs:**
- Pro: Single origin for the browser (no CORS issues), API keys stay server-side
- Pro: Can add BFF transforms in Next.js Route Handlers before proxying
- Con: Adds one network hop in production if not colocated
- Con: SSE streams through the proxy need special care (no response buffering)

**Configuration:**

```typescript
// dashboard/next.config.ts
import type { NextConfig } from 'next';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/dashboard/:path*',
        destination: `${FASTAPI_URL}/api/dashboard/:path*`,
      },
      {
        source: '/dashboard/events',
        destination: `${FASTAPI_URL}/dashboard/events`,
      },
    ];
  },
};

export default nextConfig;
```

### Pattern 2: JSON API Routes Wrapping Existing Query Handlers

**What:** New FastAPI routes in `api_routes.py` that call the same `OverviewQueryHandler`, `SignalsQueryHandler`, `RiskQueryHandler`, `PipelineQueryHandler` but return JSON instead of HTML templates.

**When to use:** For every dashboard data endpoint. The query handlers already aggregate data from multiple bounded contexts -- this pattern reuses them.

**Trade-offs:**
- Pro: Zero business logic duplication -- same query handlers, different serialization
- Pro: The HTMX dashboard can run in parallel during migration (both routes coexist)
- Con: Must ensure dict shapes are JSON-serializable (they already are)

**Example:**

```python
# src/dashboard/presentation/api_routes.py
from fastapi import APIRouter, Request
from src.dashboard.application.queries import OverviewQueryHandler

api_router = APIRouter(prefix="/api/dashboard")

@api_router.get("/overview")
def overview_data(request: Request):
    ctx = request.app.state.ctx
    handler = OverviewQueryHandler(ctx)
    data = handler.handle()
    # Equity curve chart data moves to frontend (React builds the chart)
    # No more Plotly JSON -- return raw data, let TradingView/Recharts render
    return data

@api_router.get("/signals")
def signals_data(request: Request, sort: str = "composite", desc: bool = True):
    ctx = request.app.state.ctx
    handler = SignalsQueryHandler(ctx)
    return handler.handle(sort_by=sort, sort_desc=desc)

@api_router.get("/risk")
def risk_data(request: Request):
    ctx = request.app.state.ctx
    handler = RiskQueryHandler(ctx)
    data = handler.handle()
    # Remove Plotly chart JSON -- frontend renders its own charts
    data.pop("gauge_json", None)
    data.pop("donut_json", None)
    return data

@api_router.get("/pipeline")
def pipeline_data(request: Request):
    ctx = request.app.state.ctx
    handler = PipelineQueryHandler(ctx)
    return handler.handle()
```

### Pattern 3: SSE Hook for Real-Time Updates

**What:** A React hook that connects to the existing `/dashboard/events` SSE endpoint and dispatches typed events to components.

**When to use:** For all real-time updates (order fills, pipeline completion, drawdown alerts, regime changes).

**Trade-offs:**
- Pro: SSE is simpler than WebSocket (one-directional, auto-reconnect via EventSource)
- Pro: The Python SSEBridge already works -- no backend changes needed
- Pro: EventSource is supported in all modern browsers
- Con: SSE is unidirectional (server-to-client only). For client-to-server actions (approve trade, run pipeline), use POST requests.

**Example:**

```typescript
// dashboard/src/hooks/use-sse.ts
import { useEffect, useCallback, useRef } from 'react';

type SSEEventType =
  | 'OrderFilledEvent'
  | 'PipelineCompletedEvent'
  | 'PipelineHaltedEvent'
  | 'DrawdownAlertEvent'
  | 'RegimeChangedEvent';

type SSEHandler = (payload: Record<string, string>) => void;

export function useSSE(handlers: Partial<Record<SSEEventType, SSEHandler>>) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  useEffect(() => {
    const eventSource = new EventSource('/dashboard/events');

    const eventTypes: SSEEventType[] = [
      'OrderFilledEvent',
      'PipelineCompletedEvent',
      'PipelineHaltedEvent',
      'DrawdownAlertEvent',
      'RegimeChangedEvent',
    ];

    for (const eventType of eventTypes) {
      eventSource.addEventListener(eventType, (event) => {
        const handler = handlersRef.current[eventType];
        if (handler) {
          // The SSE bridge sends JSON payload
          try {
            const data = JSON.parse(event.data);
            handler(data);
          } catch {
            // Bridge may send HTML (legacy) -- ignore
          }
        }
      });
    }

    eventSource.onerror = () => {
      // EventSource auto-reconnects; no manual handling needed
    };

    return () => eventSource.close();
  }, []);
}
```

### Pattern 4: TradingView Lightweight Charts as Client Components

**What:** Use `lightweight-charts` v5.x directly (no wrapper library) in `"use client"` components. TradingView's official React tutorial shows using `useEffect` + `useRef` to manage the chart lifecycle.

**When to use:** For candlestick charts, equity curves, and any financial chart that needs zoom/pan/crosshair.

**Trade-offs:**
- Pro: 45KB bundle size, extremely performant canvas-based rendering
- Pro: Native candlestick, area, histogram, baseline chart types
- Pro: No wrapper library dependency (wrappers are unmaintained; latest is 2+ years old)
- Con: Requires manual lifecycle management (create/destroy in useEffect)
- Con: No SSR -- must be `"use client"` components

**Example:**

```typescript
// dashboard/src/components/charts/equity-curve.tsx
'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType, AreaSeries } from 'lightweight-charts';

interface EquityCurveProps {
  data: { time: string; value: number }[];
}

export function EquityCurve({ data }: EquityCurveProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a2e' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2d2d44' },
        horzLines: { color: '#2d2d44' },
      },
      width: containerRef.current.clientWidth,
      height: 350,
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: '#4fc3f7',
      topColor: 'rgba(79, 195, 247, 0.3)',
      bottomColor: 'rgba(79, 195, 247, 0.0)',
    });

    series.setData(data);
    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [data]);

  return <div ref={containerRef} />;
}
```

---

## Data Flow

### Page Load Flow (Initial Data)

```
Browser navigates to /overview
    |
Next.js App Router renders overview/page.tsx (Server Component)
    |
    +--> fetch('/api/dashboard/overview')
              |
              +--> next.config.ts rewrite --> FastAPI :8000
                        |
                        +--> OverviewQueryHandler(ctx).handle()
                                  |
                                  +--> position_repo.find_all_open()     --> SQLite
                                  +--> score_repo.find_all_latest()      --> SQLite
                                  +--> trade_plan_repo (direct SQL)      --> SQLite
                                  +--> regime_repo.find_latest()         --> SQLite
                                  +--> portfolio_repo.find_by_id()       --> SQLite
                                  |
                        <-- JSON response (positions, kpis, equity_curve, ...)
              |
    <-- Rendered HTML with hydrated data
    |
Client Components hydrate (charts mount, SSE connects)
```

### Real-Time Update Flow (SSE)

```
Domain Event fires (e.g., OrderFilledEvent from Alpaca monitor)
    |
SyncEventBus.publish(OrderFilledEvent)
    |
SSEBridge._on_event() --> serializes to JSON, fans out to asyncio queues
    |
EventSourceResponse yields ServerSentEvent
    |
    +--> Browser EventSource receives event
              |
              +--> useSSE hook dispatches to registered handler
                        |
                        +--> Handler calls React state setter
                                  |
                                  +--> Component re-renders with new data
                                  |
                                  +--> (Optional) Refetch full data from API
```

### Action Flow (User Mutations)

```
User clicks "Run Pipeline" button
    |
React onClick handler
    |
    +--> fetch('/api/dashboard/pipeline/run', { method: 'POST', body: ... })
              |
              +--> next.config.ts rewrite --> FastAPI :8000
                        |
                        +--> RunPipelineHandler.handle(cmd)
                                  |
                                  +--> Background thread executes pipeline
                                  |
                        <-- JSON { status: "running", ... }
              |
    <-- Update UI to show "running" state
    |
    ... SSE event (PipelineCompletedEvent) arrives later ...
    |
    +--> useSSE handler triggers refetch of pipeline data
```

### Key Data Flows

1. **Initial page data:** Server Component `fetch()` -> rewrite -> FastAPI -> Query Handler -> Repos -> JSON response. The existing query handlers return Python dicts that are already JSON-serializable. No transformation needed.

2. **Real-time events:** Domain event -> SyncEventBus -> SSEBridge -> EventSource -> React state update. The SSE bridge must change from sending HTML partials to sending JSON payloads. The `_render_partial()` function in `routes.py` becomes unnecessary for React -- the bridge sends raw event data and the React components re-render themselves.

3. **User actions (POST):** React form -> fetch POST -> rewrite -> FastAPI -> Command Handler -> side effects + event publication. The existing HTMX POST handlers return HTML partials; the new JSON API routes return JSON status responses instead.

---

## Integration Points

### What Changes in the Python Backend

| Component | Change | Scope |
|-----------|--------|-------|
| `src/dashboard/presentation/api_routes.py` | **NEW file.** JSON REST endpoints wrapping existing query handlers. ~150 lines. | New file |
| `src/dashboard/presentation/app.py` | **ADD 1 line.** `app.include_router(api_router)` to mount JSON routes alongside existing HTMX routes. | 1 line change |
| `src/dashboard/infrastructure/sse_bridge.py` | **NO CHANGE.** The SSE bridge already sends JSON payloads. The `_render_partial()` in routes.py added HTML wrapping, but the bridge itself sends `{"type": "...", "payload": {...}}`. React EventSource reads this directly. | No change |
| `src/dashboard/application/queries.py` | **MINOR CHANGE.** Remove Plotly chart JSON generation from return dicts (gauge_json, donut_json). These were for Plotly.js rendering; React will render its own charts. | ~10 lines removed |
| All other `src/` modules | **NO CHANGE.** Scoring, signals, portfolio, execution, regime, pipeline, approval -- all untouched. | No change |
| `commercial/` | **NO CHANGE.** The commercial API is completely separate. | No change |

### What Is New in the Frontend

| Component | Description | Complexity |
|-----------|-------------|------------|
| Next.js project setup | App Router, TypeScript, Tailwind CSS, shadcn/ui init | Low |
| 4 page components | Overview, Signals, Risk, Pipeline (Server Components fetching data) | Medium |
| ~15 client components | KPI cards, tables, charts, forms, badges | Medium |
| TradingView chart integration | Candlestick, equity curve, volume histogram | Medium |
| SSE hook | EventSource connection with typed event dispatch | Low |
| Design system | Bloomberg dark theme tokens, typography, spacing | Medium |
| API client | Typed fetch wrapper with error handling | Low |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| FastAPI backend | HTTP fetch via Next.js rewrites | Same machine, no auth needed (personal dashboard) |
| SSE event stream | Browser EventSource to `/dashboard/events` | Proxy must not buffer the response (streaming) |
| TradingView Lightweight Charts | npm package, canvas-based rendering | Client-only, no SSR |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Next.js <-> FastAPI | JSON REST + SSE | Rewrites proxy in dev; reverse proxy (Caddy/nginx) in prod |
| FastAPI <-> DDD handlers | Direct Python function calls via `ctx` dict | No change from current architecture |
| DDD handlers <-> Repos | Direct method calls | No change |
| Bounded contexts <-> each other | SyncEventBus domain events | No change |

---

## Scaling Considerations

This is a single-user personal trading dashboard. "Scaling" means "what if the data grows."

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user, <50 positions | Current architecture is fine. Full page data loads in <100ms from SQLite. |
| 1 user, 200+ positions | Paginate holdings table. Add virtual scrolling to data tables (TanStack Table supports this). SQLite queries remain fast. |
| 1 user, 2+ years of history | Equity curve chart needs date-range filtering (don't load 500+ data points). Add query params for date range. |
| Multiple users (if ever) | Would need auth, per-user context, and database isolation. Out of scope for v1.3. |

### Scaling Priorities

1. **First bottleneck:** Chart rendering with large datasets. Lightweight Charts handles 10K+ candles well, but equity curve with hundreds of trade points might need aggregation. Solution: server-side date-range filtering.
2. **Second bottleneck:** SSE connection limits. Browsers allow 6 concurrent connections per domain (HTTP/1.1). With only 1 user and 1 SSE connection, this is not a concern.

---

## Anti-Patterns

### Anti-Pattern 1: Duplicating Business Logic in Next.js API Routes

**What people do:** Rewrite query logic in TypeScript Route Handlers instead of proxying to FastAPI.
**Why it is wrong:** Creates two sources of truth for data aggregation. When a Python query handler changes, the TypeScript version diverges silently.
**Do this instead:** Next.js Route Handlers should only proxy to FastAPI or do light BFF transforms (renaming fields, filtering response data). All aggregation stays in Python `QueryHandler` classes.

### Anti-Pattern 2: Using WebSocket Instead of SSE

**What people do:** Replace the working SSE bridge with WebSocket for "bidirectional" communication.
**Why it is wrong:** The dashboard only needs server-to-client streaming. User actions (approve, run pipeline) are standard POST requests. WebSocket adds complexity (connection management, heartbeats, protocol upgrade) with no benefit for this use case.
**Do this instead:** Keep SSE for server-to-client events. Use POST requests for client-to-server actions. This is exactly what the existing architecture does.

### Anti-Pattern 3: SSR for Chart Components

**What people do:** Try to server-render TradingView charts or other canvas-based components.
**Why it is wrong:** Canvas-based chart libraries require browser APIs (`document`, `window`, `ResizeObserver`). Server rendering them is impossible and causes hydration mismatches.
**Do this instead:** Mark chart components as `"use client"`. Fetch data in a parent Server Component and pass it as props. The chart renders client-side only.

### Anti-Pattern 4: Installing a React Wrapper for Lightweight Charts

**What people do:** Use `lightweight-charts-react-wrapper` or `kaktana-react-lightweight-charts` npm packages.
**Why it is wrong:** These wrappers are unmaintained (last published 2+ years ago). They may not support Lightweight Charts v5.x and add a dependency risk.
**Do this instead:** Use `lightweight-charts` directly with `useEffect` + `useRef`. TradingView provides official React tutorials for this exact pattern. It is ~30 lines of code per chart type.

### Anti-Pattern 5: Separate Git Repositories for Frontend and Backend

**What people do:** Create a new repo for the Next.js frontend.
**Why it is wrong:** Adds deployment coordination overhead, makes it harder to ensure API contract compatibility, and complicates development (switching between repos to trace a data flow).
**Do this instead:** Keep frontend in the same repo as `dashboard/` directory. Python tooling (mypy, ruff, pytest) is scoped to `src/` and ignores `dashboard/`. Node.js tooling is scoped to `dashboard/`. Each has its own config files.

### Anti-Pattern 6: Response Buffering Breaking SSE Proxy

**What people do:** Use Next.js rewrites for SSE without disabling compression/buffering.
**Why it is wrong:** Next.js (and nginx) may buffer streamed responses, causing SSE events to arrive in batches instead of real-time.
**Do this instead:** In development, Next.js rewrites handle SSE fine. In production with nginx, add `proxy_buffering off; X-Accel-Buffering: no;` to the SSE endpoint configuration. Or connect SSE directly to FastAPI (skip the proxy for this one endpoint).

---

## Deployment Strategy

### Development

```bash
# Terminal 1: Python backend
cd /home/mqz/workspace/trading
uvicorn src.dashboard.presentation.app:create_dashboard_app --reload --port 8000

# Terminal 2: Next.js frontend
cd /home/mqz/workspace/trading/dashboard
npm run dev  # localhost:3000, proxies /api/* to :8000
```

Both servers run simultaneously. The developer accesses `localhost:3000` for the React dashboard. All API calls are transparently proxied to `localhost:8000`.

### Production (Single Machine)

Use **Caddy** as reverse proxy (simpler than nginx, automatic HTTPS):

```
# Caddyfile
:80 {
    # Next.js frontend (static + SSR)
    reverse_proxy /api/dashboard/* localhost:8000
    reverse_proxy /dashboard/events localhost:8000 {
        flush_interval -1   # Disable buffering for SSE
    }
    reverse_proxy /* localhost:3000
}
```

Or use `output: 'standalone'` in `next.config.ts` to build a self-contained Node.js server, then run both processes via `systemd` or `pm2`:

```bash
# Build Next.js standalone
cd dashboard && npm run build
# Run: node dashboard/.next/standalone/server.js (port 3000)
# Run: uvicorn src.dashboard.presentation.app:create_dashboard_app (port 8000)
```

### Why Not Docker (For Now)

This is a personal trading system running on a single WSL2 machine. Docker adds indirection without benefit. If deployment moves to a cloud server later, Dockerize both services then. For now, two systemd services are sufficient.

---

## SSE Bridge Modification Detail

The existing SSE bridge sends events in this format:

```python
# Current SSEBridge._on_event output:
{"type": "OrderFilledEvent", "payload": {"symbol": "AAPL", "quantity": "10", ...}}
```

The current `routes.py` has `_render_partial()` which converts these to HTML for HTMX `sse-swap`. For the React frontend, the raw JSON format is exactly what we need. The React `useSSE` hook parses this JSON directly.

**Migration approach:** Keep the existing `/dashboard/events` SSE endpoint as-is. It sends JSON-wrapped events. The HTMX `_render_partial()` layer is in `routes.py` (the old HTMX route handler), not in the SSE bridge. The new React frontend connects to the same SSE endpoint and reads the JSON directly.

This means both HTMX and React dashboards can run simultaneously during migration -- they share the same SSE stream but interpret it differently.

---

## Build Order Recommendation

Based on dependency analysis:

1. **Phase 1: Project Setup + Design System** -- Next.js init, Tailwind, shadcn/ui, dark theme tokens, layout (sidebar + header). No API connection yet; use mock data.
2. **Phase 2: FastAPI JSON API** -- Add `api_routes.py` to Python backend. Test with curl. This is the integration point.
3. **Phase 3: Overview Page** -- Connect to live API. KPI cards, holdings table, equity curve (TradingView).
4. **Phase 4: Signals Page** -- Scoring data table, signal cards. TradingView candlestick chart for selected symbol.
5. **Phase 5: Risk Page** -- Drawdown gauge, sector donut, regime badge.
6. **Phase 6: Pipeline Page** -- Pipeline runs table, approval form, review queue. POST actions (run, approve, reject).
7. **Phase 7: SSE Integration** -- Wire useSSE hook to all pages. Real-time updates.
8. **Phase 8: Cleanup** -- Remove HTMX templates and routes. Remove Plotly dependency from backend.

**Rationale:** The Overview page has the most data complexity (multiple repos, equity curve). Building it first validates the entire integration path. The Pipeline page has the most interactivity (forms, mutations). Deferring it to Phase 6 allows the team to establish patterns on simpler pages first.

---

## Sources

- [Next.js Rewrites Documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites) -- Official, confirmed v16.1.6 (2026-02-27)
- [TradingView Lightweight Charts React Tutorial](https://tradingview.github.io/lightweight-charts/tutorials/react/simple) -- Official, v5.x
- [TradingView Lightweight Charts GitHub](https://github.com/tradingview/lightweight-charts) -- 45KB, canvas-based
- [Next.js Server vs Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components) -- Official
- [shadcn/ui Data Table](https://ui.shadcn.com/docs/components/radix/data-table) -- TanStack Table based
- [Next.js + FastAPI Discussion](https://github.com/vercel/next.js/discussions/43724) -- Community patterns
- [Vinta Next.js FastAPI Template](https://github.com/vintasoftware/nextjs-fastapi-template) -- Reference architecture
- [Next.js SSE Discussion](https://github.com/vercel/next.js/discussions/48427) -- Known buffering caveats

---
*Architecture research for: v1.3 Bloomberg Dashboard (Next.js + React)*
*Researched: 2026-03-14*
