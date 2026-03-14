# Phase 24: Real-Time & Integration - Research

**Researched:** 2026-03-14
**Domain:** SSE EventSource integration with React + TanStack Query for real-time dashboard updates
**Confidence:** HIGH

## Summary

Phase 24 wires the existing FastAPI SSE endpoint (`/api/v1/dashboard/events`) to the React dashboard so that domain events trigger automatic UI updates without page refresh. The backend infrastructure is fully in place: `SSEBridge` subscribes to 5 domain event types (`OrderFilledEvent`, `PipelineCompletedEvent`, `PipelineHaltedEvent`, `DrawdownAlertEvent`, `RegimeChangedEvent`) via `SyncEventBus`, serializes them, and fans them out to SSE consumers. The `api_routes.py` SSE endpoint emits named events using `sse-starlette`'s `ServerSentEvent(data=..., event=event_type)`. The `next.config.ts` rewrites already proxy `/api/*` to FastAPI, and SSE streams pass through without buffering in dev mode (confirmed in Phase 21 research).

The frontend currently uses TanStack Query hooks (`useOverview`, `useRisk`, `usePipeline`, `useSignals`) with `staleTime: 30_000` for data fetching. The real-time integration pattern is straightforward: create a single `useSSE` hook that opens an `EventSource` connection to `/api/v1/dashboard/events`, listens for named events, and calls `queryClient.invalidateQueries()` to trigger refetches of the affected query keys. This is the standard community pattern -- no new libraries needed. The browser's native `EventSource` API handles reconnection automatically (per SSE spec, reconnects after network drops with configurable retry interval).

The SSE endpoint sends named events (`event: OrderFilledEvent`, `event: RegimeChangedEvent`, etc.) so the EventSource client uses `addEventListener('OrderFilledEvent', handler)` to listen for specific event types. Each event type maps to one or more TanStack Query keys that should be invalidated.

**Primary recommendation:** Create a single `useSSE` custom hook in `dashboard/src/hooks/use-sse.ts` that opens an `EventSource` to `/api/v1/dashboard/events`, maps event types to query keys, and calls `invalidateQueries`. Mount it once in the `Providers` component. No new npm dependencies needed -- use the browser-native `EventSource` API.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RT-01 | SSE로 실시간 이벤트 (OrderFilled, PipelineCompleted, DrawdownAlert, RegimeChanged)가 UI 컴포넌트에 반영된다 | Backend SSE bridge already emits all 5 event types via `/api/v1/dashboard/events`. Frontend needs a single `useSSE` hook using native EventSource API that maps event types to TanStack Query invalidations. Next.js rewrites already proxy SSE without buffering. |
</phase_requirements>

## Standard Stack

### Core (Already Installed -- No New Dependencies)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| EventSource (browser API) | Native | SSE client with auto-reconnect | Built into all modern browsers |
| @tanstack/react-query | 5.90.21 | Server state + `invalidateQueries` | Already installed in dashboard |
| sse-starlette | 2.0+ | FastAPI SSE endpoint (backend) | Already installed and wired |
| SSEBridge (internal) | -- | SyncEventBus to async SSE fan-out | Already wired to 5 event types |

### No New Dependencies Required

This phase adds zero npm packages. The browser-native `EventSource` API provides:
- Auto-reconnection on disconnect (per SSE spec)
- Named event listeners via `addEventListener`
- Configurable retry interval (server can send `retry:` field)

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Native EventSource | `eventsource` npm package | npm package adds Node.js support and custom headers, but we only need browser support. Native API is sufficient. |
| Query invalidation | Direct cache update via `setQueryData` | Direct cache update would avoid a refetch but requires knowing the exact cache shape. Invalidation is simpler, safer, and acceptable for this use case (events are infrequent -- daily trading system, not tick-level). |
| SSE | WebSocket | SSE is one-way (server to client) which is exactly what we need. Already implemented on backend. WebSocket would require new backend infrastructure for no benefit. |

## Architecture Patterns

### Event Flow (End to End)

```
Domain Event (Python)
    |
SyncEventBus.publish()
    |
SSEBridge._on_event() -- serializes, fans out to asyncio.Queue(s)
    |
/api/v1/dashboard/events (SSE endpoint)
    |  event: OrderFilledEvent
    |  data: {"order_id": "...", "symbol": "AAPL", ...}
    |
next.config.ts rewrite (transparent proxy, no buffering)
    |
Browser EventSource (auto-reconnect)
    |
useSSE hook: addEventListener('OrderFilledEvent', ...)
    |
queryClient.invalidateQueries({ queryKey: ['overview'] })
    |
useOverview() refetches -> React re-renders
```

### Event-to-Query Mapping

| SSE Event Type | Query Keys to Invalidate | UI Components Updated |
|----------------|--------------------------|----------------------|
| `OrderFilledEvent` | `['overview']` | KPI cards (P&L, total value), holdings table |
| `DrawdownAlertEvent` | `['risk']`, `['overview']` | Drawdown gauge, risk indicators, KPI drawdown card |
| `RegimeChangedEvent` | `['risk']`, `['overview']`, `['signals']` | Regime badge (risk page), equity curve regime overlay (overview), signal weights |
| `PipelineCompletedEvent` | `['pipeline']`, `['overview']` | Pipeline history, pipeline status KPI, review queue |
| `PipelineHaltedEvent` | `['pipeline']`, `['overview']` | Pipeline history, pipeline status KPI |

### Pattern: useSSE Hook

**What:** A custom React hook that manages a single EventSource connection and invalidates TanStack Query caches on events.
**When to use:** Mount once at the provider level to cover all pages.
**Key design decisions:**
- Mount in `Providers` component (not per-page) so the connection persists across navigation
- Use `useQueryClient()` inside the hook to access the shared query client
- Use `useEffect` with cleanup that calls `eventSource.close()`
- No `useRef` needed -- EventSource is created and torn down in the effect

**Example:**
```typescript
// Source: Community pattern verified via TanStack Query docs + MDN EventSource API
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const EVENT_QUERY_MAP: Record<string, string[][]> = {
  OrderFilledEvent: [['overview']],
  DrawdownAlertEvent: [['risk'], ['overview']],
  RegimeChangedEvent: [['risk'], ['overview'], ['signals']],
  PipelineCompletedEvent: [['pipeline'], ['overview']],
  PipelineHaltedEvent: [['pipeline'], ['overview']],
};

export function useSSE() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const es = new EventSource('/api/v1/dashboard/events');

    for (const [eventType, queryKeys] of Object.entries(EVENT_QUERY_MAP)) {
      es.addEventListener(eventType, () => {
        for (const key of queryKeys) {
          queryClient.invalidateQueries({ queryKey: key });
        }
      });
    }

    es.onerror = () => {
      // EventSource auto-reconnects per spec.
      // No manual reconnect logic needed.
    };

    return () => es.close();
  }, [queryClient]);
}
```

### Pattern: Provider-Level SSE Mounting

**What:** Call `useSSE()` from a component rendered inside the `QueryClientProvider` so it has access to `useQueryClient()`.
**Why:** Hooks cannot be called directly in `Providers` because `QueryClientProvider` wraps the children. Create a small `SSEListener` component.

**Example:**
```typescript
// Source: React hook rules -- hooks need QueryClientProvider ancestor
function SSEListener() {
  useSSE();
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({...}));

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider ...>
        <SSEListener />
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
```

### Anti-Patterns to Avoid

- **Per-page EventSource connections:** Opening a new EventSource on each page creates multiple connections and misses events during navigation. Use one connection at the provider level.
- **Manual reconnection logic:** EventSource auto-reconnects per the SSE spec. Adding `setTimeout` reconnect loops is redundant and creates race conditions.
- **Direct cache mutation with `setQueryData`:** The SSE event payloads contain partial data (e.g., `OrderFilledEvent` has `symbol` and `filled_price` but not the full positions list). Updating the cache directly would require complex merge logic. Invalidation triggers a clean refetch which is simpler and correct.
- **WebSocket for SSE:** The backend already has SSE infrastructure. Adding WebSocket would duplicate functionality with more complexity (connection management, protocol overhead).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE client | Custom fetch + ReadableStream parser | Browser native `EventSource` | EventSource handles connection lifecycle, auto-reconnect, and event parsing per SSE spec. Custom implementations miss edge cases (retry, incomplete chunks). |
| Query refetch coordination | Manual `fetch()` calls in event handlers | `queryClient.invalidateQueries()` | TanStack Query deduplicates concurrent invalidations, respects component mount state, and handles race conditions automatically. |
| Event type routing | `if/else` chain on `event.type` | `EVENT_QUERY_MAP` lookup table | Declarative mapping is easier to maintain and extend. Adding a new event type is one line. |

**Key insight:** The entire real-time pipeline is already built on both ends (Python SSEBridge on backend, TanStack Query on frontend). This phase is pure wiring -- connecting the two with ~40 lines of TypeScript.

## Common Pitfalls

### Pitfall 1: SSE Buffering Through Next.js Proxy
**What goes wrong:** SSE events are delayed or batched instead of streaming in real-time.
**Why it happens:** Some proxy configurations buffer responses. Next.js Route Handlers can compress/buffer SSE streams.
**How to avoid:** Use `next.config.ts` rewrites (already configured) instead of Next.js Route Handlers. The rewrite acts as a transparent TCP proxy and does not buffer. This was a locked decision from Phase 21 research.
**Warning signs:** Events arrive in batches instead of one-by-one, or long delays between event emission and UI update.

### Pitfall 2: EventSource Connection Not Cleaned Up
**What goes wrong:** Memory leak and stale connections accumulate.
**Why it happens:** Forgetting `eventSource.close()` in the useEffect cleanup function, or component remounts without cleanup.
**How to avoid:** Always return `() => es.close()` from the useEffect. React Strict Mode in dev may double-mount, causing two connections briefly -- this is expected and harmless (the first closes on unmount).
**Warning signs:** Browser DevTools Network tab shows multiple open SSE connections.

### Pitfall 3: Named Events vs. Generic "message" Event
**What goes wrong:** Event listeners never fire despite events being sent.
**Why it happens:** The backend sends named events (`event: OrderFilledEvent`), but the client listens with `es.onmessage` which only catches unnamed events. Must use `es.addEventListener('OrderFilledEvent', handler)`.
**How to avoid:** Use `addEventListener` for each named event type, not `onmessage`.
**Warning signs:** `onmessage` handler fires for nothing, but Network tab shows events arriving.

### Pitfall 4: Invalidating Too Aggressively
**What goes wrong:** Multiple simultaneous refetches cause flickering or unnecessary load.
**Why it happens:** One SSE event invalidates 3+ query keys, each triggering a separate refetch.
**How to avoid:** TanStack Query deduplicates concurrent invalidations within the same render cycle. The staleTime of 30s means only active queries (mounted components) will refetch. No additional batching needed for this trading system (events are infrequent -- maximum a few per pipeline run).
**Warning signs:** Backend receiving dozens of API requests per event.

### Pitfall 5: SSE Connection During Server Downtime
**What goes wrong:** Rapid reconnection attempts flood the server during restarts.
**Why it happens:** EventSource reconnects with the server's retry interval (default ~3s). If the server is down, reconnect attempts fail immediately and retry.
**How to avoid:** The FastAPI SSE endpoint can send `retry: 10000` (10 seconds) to slow reconnects. For this use case, the default behavior is acceptable -- the trading server is typically always running during market hours.
**Warning signs:** Console flooded with EventSource error messages during server restart.

## Code Examples

### Backend SSE Event Format (Already Working)

The backend `api_routes.py` endpoint sends events in this format:
```
event: OrderFilledEvent
data: {"order_id": "abc123", "symbol": "AAPL", "quantity": "10", "filled_price": "175.50", "position_qty": "10.0"}

event: RegimeChangedEvent
data: {"previous_regime": "Bull", "new_regime": "Bear", "confidence": "0.85", "vix_value": "28.5", "adx_value": "35.2"}

event: DrawdownAlertEvent
data: {"portfolio_id": "main", "drawdown": "0.12", "level": "caution"}

event: PipelineCompletedEvent
data: {"run_id": "run-001", "duration_seconds": "45.2", "symbols_succeeded": "5", "mode": "manual"}
```

Note: All payload values are stringified by `SSEBridge._on_event()` via `str(v)`. The React frontend does not need to parse these values -- it only uses the event type for invalidation, not the payload data.

### Complete useSSE Hook
```typescript
// Source: Browser EventSource API (MDN) + TanStack Query invalidateQueries pattern
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const EVENT_QUERY_MAP: Record<string, string[][]> = {
  OrderFilledEvent: [['overview']],
  DrawdownAlertEvent: [['risk'], ['overview']],
  RegimeChangedEvent: [['risk'], ['overview'], ['signals']],
  PipelineCompletedEvent: [['pipeline'], ['overview']],
  PipelineHaltedEvent: [['pipeline'], ['overview']],
};

export function useSSE() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const es = new EventSource('/api/v1/dashboard/events');

    for (const [eventType, queryKeys] of Object.entries(EVENT_QUERY_MAP)) {
      es.addEventListener(eventType, () => {
        for (const key of queryKeys) {
          queryClient.invalidateQueries({ queryKey: key });
        }
      });
    }

    return () => es.close();
  }, [queryClient]);
}
```

### SSEListener Component (Provider Integration)
```typescript
// Source: React hook composition pattern
'use client';

function SSEListener() {
  useSSE();
  return null;
}

// Inside Providers component, after QueryClientProvider:
<QueryClientProvider client={queryClient}>
  <ThemeProvider ...>
    <SSEListener />
    {children}
  </ThemeProvider>
</QueryClientProvider>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HTMX `sse-swap` with HTML partials | EventSource + query invalidation | Phase 24 (this phase) | Clean separation: SSE carries event signals, React Query fetches fresh data |
| WebSocket for real-time | SSE for server-to-client pushes | 2024-2025 trend | SSE is simpler, HTTP-native, auto-reconnects. WebSocket only needed for bidirectional. |
| Polling with `refetchInterval` | Event-driven invalidation | -- | Eliminates unnecessary polling. Updates happen immediately when events occur. |

**Deprecated/outdated:**
- HTMX SSE integration (Phase 25 removes HTMX entirely)
- `sse-swap` attribute matching (replaced by `addEventListener` with TanStack Query)

## Open Questions

1. **SSE reconnection interval in production**
   - What we know: Browser EventSource auto-reconnects with default ~3s retry. Server can override via `retry:` field.
   - What's unclear: Optimal retry interval for this trading system (market hours only, events are infrequent).
   - Recommendation: Use default for now. If needed, add `retry: 10000` to the SSE endpoint later. Not blocking for Phase 24.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (Python backend) + TypeScript type checking (frontend) |
| Config file | `pyproject.toml` (pytest), `tsconfig.json` (TS), `biome.json` (lint) |
| Quick run command | `cd /home/mqz/workspace/trading && pytest tests/unit/test_dashboard_sse.py tests/unit/test_sse_event_wiring.py -x` |
| Full suite command | `cd /home/mqz/workspace/trading && pytest tests/ -x` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RT-01a | useSSE hook creates EventSource to correct URL | manual-only | TypeScript typecheck via `cd dashboard && npx tsc --noEmit` | No - Wave 0 |
| RT-01b | OrderFilledEvent invalidates overview query | manual-only | Browser DevTools verification (EventSource is browser-only API) | No |
| RT-01c | DrawdownAlertEvent invalidates risk + overview queries | manual-only | Browser DevTools verification | No |
| RT-01d | RegimeChangedEvent invalidates risk + overview + signals queries | manual-only | Browser DevTools verification | No |
| RT-01e | PipelineCompletedEvent invalidates pipeline + overview queries | manual-only | Browser DevTools verification | No |
| RT-01f | SSE connection re-established after disconnect | manual-only | Browser DevTools Network tab | No |

**Manual-only justification:** The useSSE hook uses the browser-native `EventSource` API which requires a DOM environment. The hook is ~40 lines of declarative mapping (event type to query keys). Type checking (`tsc --noEmit`) verifies the hook compiles correctly. Runtime behavior verification requires a running FastAPI backend + Next.js dev server + browser.

### Sampling Rate
- **Per task commit:** `cd /home/mqz/workspace/trading/dashboard && npx tsc --noEmit` (typecheck) + `npx biome check .` (lint)
- **Per wave merge:** Full typecheck + lint
- **Phase gate:** TypeScript typecheck passes, Biome lint passes, manual SSE verification with running servers

### Wave 0 Gaps
- None -- no automated test files needed. This phase is pure frontend wiring (~40 lines). TypeScript type checking is the primary automated validation. Existing backend SSE tests (`test_dashboard_sse.py`, `test_sse_event_wiring.py`) already verify the Python side.

## Sources

### Primary (HIGH confidence)
- **MDN EventSource API** - [developer.mozilla.org/en-US/docs/Web/API/EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource) - Named events, addEventListener, auto-reconnect behavior
- **MDN Server-Sent Events Guide** - [developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) - SSE protocol format, event naming
- **TanStack Query Invalidation Docs** - [tanstack.dev/query/latest/docs/framework/react/guides/query-invalidation](https://tanstack.dev/query/latest/docs/framework/react/guides/query-invalidation) - invalidateQueries API, stale state behavior
- **Existing codebase** - `src/dashboard/infrastructure/sse_bridge.py`, `src/dashboard/presentation/api_routes.py`, `src/dashboard/presentation/app.py` - Backend SSE already fully wired

### Secondary (MEDIUM confidence)
- **TanStack Query SSE Discussion** - [github.com/TanStack/query/discussions/418](https://github.com/TanStack/query/discussions/418) - Community patterns for SSE + React Query
- **Phase 21 Research** - Confirmed SSE proxy works through `next.config.ts` rewrites without buffering
- **Phase 17 Research** - SSE event name matching, backend event publication verification

### Tertiary (LOW confidence)
- None -- all findings verified with primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies. Browser EventSource + existing TanStack Query.
- Architecture: HIGH - Pattern is well-established (EventSource + invalidateQueries). Backend fully wired. Only ~40 lines of new TypeScript.
- Pitfalls: HIGH - Verified via Phase 17 experience (SSE name matching), Phase 21 research (proxy buffering), and MDN docs (named events vs onmessage).

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable -- no fast-moving dependencies)
