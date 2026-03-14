# Phase 23: Signals, Risk & Pipeline Pages - Research

**Researched:** 2026-03-14
**Domain:** React data tables with sorting (TanStack Table), CSS-based data visualization (donut charts, gauges), form-driven mutation patterns (TanStack Query mutations), Bloomberg-style financial dashboard pages
**Confidence:** HIGH

## Summary

Phase 23 replaces three stub pages (signals, risk, pipeline) with fully functional Bloomberg-style pages. Each stub currently renders raw JSON via `useEffect` + `fetch`. The replacement pages follow the patterns established in Phase 22: TanStack Query hooks for data fetching, shadcn/ui components for layout, Bloomberg dark theme tokens for colors, and `font-mono tabular-nums` for financial numbers.

The three pages have distinct technical profiles. The **Signals page** is read-heavy: a sortable data table (TanStack Table + shadcn DataTable pattern) displaying scoring results, plus signal recommendation cards. The **Risk page** is visualization-heavy: a CSS-based drawdown gauge with 3-tier coloring, a CSS `conic-gradient` donut chart for sector exposure, progress bars for position limits, and a regime badge. The **Pipeline page** is mutation-heavy: a form to trigger pipeline runs, approval controls (create/suspend/resume), and a trade review queue with approve/reject buttons -- all requiring TanStack Query `useMutation` hooks for POST requests.

All three pages already have working FastAPI JSON API endpoints from Phase 21 (`/api/v1/dashboard/signals`, `/api/v1/dashboard/risk`, `/api/v1/dashboard/pipeline`). The data contracts are fully defined in the backend `SignalsQueryHandler`, `RiskQueryHandler`, and `PipelineQueryHandler` classes. The frontend needs TypeScript types matching these response shapes, TanStack Query hooks for each endpoint, and React components that consume the data.

**Primary recommendation:** Add `@tanstack/react-table` for the Signals scoring table (SGNL-03 requires column sorting). Use CSS-only approaches for the drawdown gauge (`conic-gradient` arc) and sector donut chart (`conic-gradient` pie) -- no charting library needed. Add shadcn/ui `input`, `label`, `select`, and `progress` components for forms. Use TanStack Query `useMutation` for all POST actions (pipeline run, approval CRUD, review approve/reject).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SGNL-01 | Scoring table (symbol, composite, risk-adjusted, signal) | `SignalsQueryHandler.handle()` returns `scores` list with `symbol`, `composite`, `risk_adjusted`, `strategy`, `signal` fields. Use TanStack Table `useReactTable` + shadcn Table for rendering. |
| SGNL-02 | Signal recommendation cards (BUY/SELL/HOLD with strength) | `SignalsQueryHandler.handle()` returns `signals` list with `symbol`, `direction`, `strength`, `metadata`. Render as shadcn Card grid with Badge for direction and strength indicator. |
| SGNL-03 | Table column sorting | TanStack Table `getSortedRowModel()` + `column.toggleSorting()`. Column headers render as ghost Button with ArrowUpDown icon. Backend also supports `?sort=composite&desc=true` query params. |
| RISK-01 | Drawdown gauge (green/yellow/red 3-tier) | `RiskQueryHandler.handle()` returns `drawdown_pct` (0-100) and `drawdown_level` (normal/warning/critical). CSS `conic-gradient` arc gauge -- no library needed. 3-tier: <=10% green (profit token), <=15% yellow (interactive token), >15% red (loss token). |
| RISK-02 | Sector exposure donut chart | `RiskQueryHandler.handle()` returns `sector_weights` dict (sector name -> percentage). CSS `conic-gradient` donut -- build gradient string from sector data, inner circle cutout via pseudo-element. |
| RISK-03 | Position limit progress bars | `RiskQueryHandler.handle()` returns `position_count` and `max_positions` (20). shadcn Progress component for visual bar, show `N / 20` text. |
| RISK-04 | Market regime badge | `RiskQueryHandler.handle()` returns `regime` string (Bull/Bear/Accumulation/Distribution/Unknown). shadcn Badge with color mapped to regime type. |
| PIPE-01 | Pipeline run form and results | POST `/api/v1/dashboard/pipeline/run` with `{symbols: string[], dry_run: boolean}`. TanStack Query `useMutation` + shadcn Input for symbols, Checkbox for dry_run, Button to submit. Show immediate "running" status. |
| PIPE-02 | Pipeline status/history | `PipelineQueryHandler.handle()` returns `pipeline_runs` list with run_id, started_at, completed_at, status, stages. Render as shadcn Table. `next_scheduled` string displayed. |
| PIPE-03 | Strategy approval controls (create/suspend/resume) | POST endpoints: `/approval/create`, `/approval/suspend`, `/approval/resume`. `approval_status` from API has id, score_threshold, allowed_regimes, status (active/suspended). Create form with inputs, suspend/resume buttons. |
| PIPE-04 | Trade review queue (approve/reject) | `review_queue` list from API with id, symbol, strategy, score, reason, created_at. POST `/review/approve` and `/review/reject` with `{review_id: int}`. Render as table with action buttons. |
</phase_requirements>

## Standard Stack

### Core (Phase 23 additions)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-table | 8.x (latest) | Headless table sorting/filtering for Signals scoring table | shadcn/ui DataTable pattern wraps this. Provides sorting state, sorted row model, toggle handlers. No UI -- uses existing shadcn Table markup. |

### shadcn/ui Components to Add

| Component | Install Command | Purpose |
|-----------|----------------|---------|
| progress | `npx shadcn@latest add progress` | Position limit bars (RISK-03) |
| input | `npx shadcn@latest add input` | Pipeline run form, approval create form (PIPE-01, PIPE-03) |
| label | `npx shadcn@latest add label` | Form field labels |
| checkbox | `npx shadcn@latest add checkbox` | Dry run toggle in pipeline form (PIPE-01) |
| select | `npx shadcn@latest add select` | Regime selection in approval form (PIPE-03) |

### Already Available (from Phase 22)

| Library/Component | Status |
|-------------------|--------|
| @tanstack/react-query 5.90.x | Installed -- use for all data fetching + mutations |
| shadcn/ui Card, Table, Badge, Button, Skeleton, Separator | Installed |
| lightweight-charts 5.1.x | Installed (not needed for Phase 23) |
| lucide-react | Installed -- ArrowUpDown, Check, X, Play icons |
| Bloomberg dark theme tokens | Configured in globals.css |
| formatters.ts (formatCurrency, formatPercent, formatScore, formatDate) | Available |

### Not Needed -- CSS-Only Approach

| Considered | Decision | Reason |
|------------|----------|--------|
| recharts | Skip | Donut chart and gauge are simple enough for CSS `conic-gradient`. Adding recharts (340kB) for two simple visualizations violates the simplicity principle. |
| react-minimal-pie-chart | Skip | 2kB library but CSS conic-gradient is zero-dependency and gives full control over Bloomberg styling. |
| react-gauge-chart | Skip | D3.js dependency for a simple arc gauge. CSS arc via `conic-gradient` + `border-radius: 50%` is simpler. |

**Installation:**

```bash
cd /home/mqz/workspace/trading/dashboard

# TanStack Table for sortable scoring table
npm install @tanstack/react-table

# shadcn/ui form components
npx shadcn@latest add progress input label checkbox select
```

## Architecture Patterns

### Recommended Project Structure (Phase 23 scope)

```
dashboard/src/
  app/(dashboard)/
    signals/page.tsx         # REPLACE stub -- Signals page with scoring table + signal cards
    risk/page.tsx            # REPLACE stub -- Risk page with gauge, donut, progress, badge
    pipeline/page.tsx        # REPLACE stub -- Pipeline page with forms, history, review queue
  components/
    ui/                      # shadcn/ui vendored (existing + new)
      progress.tsx           # NEW (shadcn add)
      input.tsx              # NEW (shadcn add)
      label.tsx              # NEW (shadcn add)
      checkbox.tsx           # NEW (shadcn add)
      select.tsx             # NEW (shadcn add)
      data-table.tsx         # NEW -- reusable DataTable wrapper for TanStack Table
    signals/                 # NEW
      scoring-table.tsx      # Sortable scoring DataTable
      signal-cards.tsx       # BUY/SELL/HOLD recommendation cards
    risk/                    # NEW
      drawdown-gauge.tsx     # CSS arc gauge with 3-tier coloring
      sector-donut.tsx       # CSS conic-gradient donut chart
      position-limits.tsx    # Progress bars for position count
      regime-badge.tsx       # Colored regime badge
    pipeline/                # NEW
      pipeline-run-form.tsx  # Form to trigger pipeline run
      pipeline-history.tsx   # Run history table
      approval-controls.tsx  # Create/suspend/resume approval
      review-queue.tsx       # Approve/reject trade review queue
  hooks/
    use-overview.ts          # Existing
    use-signals.ts           # NEW -- TanStack Query hook for /api/v1/dashboard/signals
    use-risk.ts              # NEW -- TanStack Query hook for /api/v1/dashboard/risk
    use-pipeline.ts          # NEW -- TanStack Query hook + mutations for /api/v1/dashboard/pipeline
  types/
    api.ts                   # EXTEND -- add SignalsData, RiskData, PipelineData types
```

### Pattern 1: TanStack Query Hooks for Each Page

**What:** Each page gets its own TanStack Query hook following the `useOverview` pattern. The hook encapsulates the fetch URL, query key, and return type.

**When to use:** Every page data fetch. Mutations use `useMutation` from the same hook file.

```typescript
// dashboard/src/hooks/use-signals.ts
import { useQuery } from '@tanstack/react-query';
import type { SignalsData } from '@/types/api';

export function useSignals() {
  return useQuery<SignalsData>({
    queryKey: ['signals'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/signals');
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    retry: 1,
  });
}
```

### Pattern 2: TanStack Query Mutations for POST Actions

**What:** POST actions (pipeline run, approval create/suspend/resume, review approve/reject) use `useMutation`. On success, invalidate the relevant query key to refetch fresh data.

**When to use:** Every button/form that sends data to the backend.

```typescript
// dashboard/src/hooks/use-pipeline.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { PipelineData } from '@/types/api';

export function usePipeline() {
  return useQuery<PipelineData>({
    queryKey: ['pipeline'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/pipeline');
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    retry: 1,
  });
}

export function usePipelineRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { symbols: string[]; dry_run: boolean }) => {
      const res = await fetch('/api/v1/dashboard/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
  });
}
```

### Pattern 3: DataTable with Sortable Columns (shadcn/ui + TanStack Table)

**What:** A generic `DataTable<TData>` component wrapping `useReactTable` with the existing shadcn `Table` component. Column definitions use `ColumnDef<T>` with header render functions for sortable headers.

**When to use:** The Signals scoring table (SGNL-01, SGNL-03).

```typescript
// dashboard/src/components/ui/data-table.tsx
'use client';

import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { useState } from 'react';

import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
}

export function DataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    state: { sorting },
  });

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((headerGroup) => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <TableHead key={header.id}>
                {header.isPlaceholder
                  ? null
                  : flexRender(header.column.columnDef.header, header.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.length ? (
          table.getRowModel().rows.map((row) => (
            <TableRow key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={columns.length} className="h-24 text-center">
              No results.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
```

### Pattern 4: CSS conic-gradient Donut Chart

**What:** Pure CSS donut chart using `conic-gradient()` for sector exposure. Build the gradient string dynamically from sector weight data. Inner circle via pseudo-element or nested div.

**When to use:** Risk page sector exposure (RISK-02). Avoids adding recharts (340kB) for a single donut.

```typescript
// dashboard/src/components/risk/sector-donut.tsx
'use client';

const SECTOR_COLORS = [
  'oklch(0.7 0.15 200)',  // cyan
  'oklch(0.78 0.15 75)',  // amber
  'oklch(0.65 0.15 150)', // green
  'oklch(0.6 0.2 25)',    // red
  'oklch(0.7 0.12 300)',  // purple
  'oklch(0.6 0.12 60)',   // orange
];

interface SectorDonutProps {
  sectors: Record<string, number>; // sector name -> percentage
}

export function SectorDonut({ sectors }: SectorDonutProps) {
  const entries = Object.entries(sectors);
  if (entries.length === 0) {
    return <p className="text-muted-foreground text-sm">No positions</p>;
  }

  // Build conic-gradient segments
  let accumulated = 0;
  const segments = entries.map(([, pct], i) => {
    const start = accumulated;
    accumulated += pct;
    const color = SECTOR_COLORS[i % SECTOR_COLORS.length];
    return `${color} ${start}% ${accumulated}%`;
  });
  const gradient = `conic-gradient(${segments.join(', ')})`;

  return (
    <div className="flex items-center gap-6">
      <div className="relative h-32 w-32 shrink-0">
        <div
          className="h-full w-full rounded-full"
          style={{ background: gradient }}
        />
        {/* Inner cutout for donut effect */}
        <div className="absolute inset-4 rounded-full bg-card" />
      </div>
      <div className="space-y-1">
        {entries.map(([sector, pct], i) => (
          <div key={sector} className="flex items-center gap-2 text-sm">
            <div
              className="h-3 w-3 rounded-sm"
              style={{ backgroundColor: SECTOR_COLORS[i % SECTOR_COLORS.length] }}
            />
            <span className="text-muted-foreground">{sector}</span>
            <span className="font-mono tabular-nums">{pct.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Pattern 5: CSS Arc Gauge for Drawdown

**What:** CSS-only drawdown gauge using a semicircle arc. Uses `conic-gradient` for the filled portion, rotated to start from the left. 3-tier coloring matches the established theme tokens.

**When to use:** Risk page drawdown gauge (RISK-01).

```typescript
// dashboard/src/components/risk/drawdown-gauge.tsx
'use client';

interface DrawdownGaugeProps {
  pct: number;       // 0-100
  level: string;     // "normal" | "warning" | "critical"
}

function gaugeColor(level: string): string {
  switch (level) {
    case 'normal': return 'text-profit';
    case 'warning': return 'text-interactive';
    case 'critical': return 'text-loss';
    default: return 'text-muted-foreground';
  }
}

function gaugeTrackColor(level: string): string {
  switch (level) {
    case 'normal': return 'oklch(0.75 0.18 180)';   // profit
    case 'warning': return 'oklch(0.78 0.15 75)';   // interactive/amber
    case 'critical': return 'oklch(0.65 0.22 25)';  // loss/red
    default: return 'oklch(0.6 0 0)';
  }
}

export function DrawdownGauge({ pct, level }: DrawdownGaugeProps) {
  // Map 0-30% drawdown to 0-180 degrees (semicircle)
  const clampedPct = Math.min(pct, 30);
  const degrees = (clampedPct / 30) * 180;
  const fillColor = gaugeTrackColor(level);
  const trackColor = 'oklch(0.2 0.005 250)';  // muted bg

  const gradient = `conic-gradient(from 180deg, ${fillColor} ${degrees}deg, ${trackColor} ${degrees}deg 180deg, transparent 180deg)`;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-20 w-40 overflow-hidden">
        <div
          className="h-40 w-40 rounded-full"
          style={{ background: gradient }}
        />
        {/* Inner cutout */}
        <div className="absolute top-2 left-2 h-36 w-36 rounded-full bg-card" />
        {/* Center label */}
        <div className="absolute inset-0 flex items-end justify-center pb-1">
          <span className={`text-2xl font-mono tabular-nums font-bold ${gaugeColor(level)}`}>
            {pct.toFixed(1)}%
          </span>
        </div>
      </div>
      <span className="text-xs text-muted-foreground uppercase tracking-wider">
        Drawdown
      </span>
    </div>
  );
}
```

### Anti-Patterns to Avoid

- **Client-side sorting when backend supports it:** The API supports `?sort=composite&desc=true`. However, use client-side sorting (TanStack Table) for immediate UX. The dataset is small (typically <50 symbols), so client-side sorting is faster than a round-trip. Do not implement both -- pick TanStack Table client-side sorting.
- **Adding recharts or chart.js for simple visualizations:** The donut and gauge are simple enough for CSS. Adding a charting library for these two components is over-engineering.
- **Using raw `fetch` in `onClick` handlers:** Every POST must go through `useMutation` for proper loading state, error handling, and cache invalidation. Never `fetch()` directly in a click handler.
- **Putting mutation logic in components:** Keep mutations in hook files (`use-pipeline.ts`). Components call `mutate()` from the returned mutation object.
- **Mixing `useEffect`+`fetch` with TanStack Query:** The stubs currently use `useEffect`+`fetch`. Phase 23 replaces this entirely with `useQuery`/`useMutation`. Do not leave any raw fetch patterns.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table sorting logic | Custom sort state + Array.sort in component | @tanstack/react-table `getSortedRowModel` | Handles multi-column sort, sort direction toggling, stable sort. Edge cases with null/undefined values. |
| Form mutation state (loading, error, success) | useState for isLoading, error, etc. | TanStack Query `useMutation` | Handles loading state, error state, retry, cache invalidation. Prevents double-submit. |
| Progress bar component | Custom div with width percentage | shadcn/ui Progress | Accessible (aria-valuenow), animated, theme-aware. |
| Sortable column header UI | Custom clickable th with sort arrow | shadcn Button variant="ghost" + lucide ArrowUpDown | Consistent with shadcn design system, keyboard accessible. |

**Key insight:** Phase 23 has more interactive elements than Phase 22. The pattern shifts from "display data" to "display data + accept user input." TanStack Query mutations are the critical pattern for handling POST requests cleanly without duplicating loading/error state management across every form.

## Common Pitfalls

### Pitfall 1: Mutation Cache Invalidation Timing

**What goes wrong:** After a POST action (e.g., approve trade), the UI still shows the old data until the next automatic refetch. User clicks "approve," the button responds, but the review queue does not update.
**Why it happens:** `useMutation` does not automatically invalidate queries. Without `onSuccess` invalidation, the cached query data remains stale.
**How to avoid:** Every `useMutation` must include `onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline'] })` to trigger an immediate refetch of the pipeline data.
**Warning signs:** Data not updating after form submission. User needing to refresh the page.

### Pitfall 2: Form Double-Submit

**What goes wrong:** User clicks "Run Pipeline" twice, triggering two background pipeline runs. Or clicks "Approve" twice on the same trade review.
**Why it happens:** No disabled state on the button during mutation, or the mutation is still pending when the user clicks again.
**How to avoid:** Destructure `isPending` from `useMutation` return value. Pass `disabled={isPending}` to the submit button. Show a loading spinner when pending.
**Warning signs:** Duplicate pipeline runs in history. Console errors about already-processed reviews.

### Pitfall 3: TanStack Table Column Definitions Recreated Every Render

**What goes wrong:** Defining `columns` array inside the component body causes it to be recreated on every render, which resets TanStack Table's internal state (including sort state).
**Why it happens:** JavaScript creates a new array reference on each render. TanStack Table detects the column change and resets.
**How to avoid:** Define `columns` outside the component, or wrap in `useMemo`. The shadcn/ui DataTable example defines columns in a separate file.
**Warning signs:** Sort state resetting after any re-render. Columns flickering.

### Pitfall 4: CSS conic-gradient Not Updating

**What goes wrong:** The donut chart or gauge appears correct on first render but does not update when data changes.
**Why it happens:** Inline `style={{ background: gradient }}` with a computed string may not trigger React's diff if the string reference changes but the DOM is not updated by the browser.
**How to avoid:** Use a `key` prop that changes when the data changes (e.g., `key={JSON.stringify(sectors)}`), or ensure the gradient string is genuinely new.
**Warning signs:** Chart showing stale data after a refetch.

### Pitfall 5: Signal Strength Indicator Accessibility

**What goes wrong:** Signal strength shown only as a colored bar is inaccessible to colorblind users.
**Why it happens:** Using only color (green/red/amber) to convey signal strength without text or shape.
**How to avoid:** Always pair color with text or numeric value. Show strength as both a colored indicator AND a numeric value (e.g., "0.85"). Use aria-label for screen readers.
**Warning signs:** Information lost in grayscale mode.

## Code Examples

### Example 1: TypeScript Types for Phase 23 API Responses

```typescript
// Additions to dashboard/src/types/api.ts

// -- Signals Page --
export interface ScoreRow {
  symbol: string;
  composite: number;
  risk_adjusted: number;
  strategy: string;
  signal: string;  // "BUY" | "SELL" | "HOLD" | "--"
}

export interface SignalItem {
  symbol: string;
  direction: string;  // "BUY" | "SELL" | "HOLD"
  strength: number;   // 0.0 - 1.0
  metadata: Record<string, unknown> | string;
}

export interface SignalsData {
  scores: ScoreRow[];
  signals: SignalItem[];
}

// -- Risk Page --
export interface RiskData {
  drawdown_pct: number;
  drawdown_level: string;  // "normal" | "warning" | "critical"
  sector_weights: Record<string, number>;
  position_count: number;
  max_positions: number;
  regime: string;
}

// -- Pipeline Page --
export interface PipelineStage {
  name: string;
  status: string;
  symbol_count: number;
}

export interface PipelineRun {
  run_id: string;
  started_at: string;
  completed_at: string;
  status: string;
  stages: PipelineStage[];
}

export interface ApprovalStatus {
  id: string;
  score_threshold: number;
  allowed_regimes: string[];
  max_per_trade_pct: number;
  daily_budget_cap: number;
  expires_at: string;
  is_active: boolean;
  is_suspended: boolean;
  suspended_reasons: string[];
  status: string;  // "active" | "suspended"
}

export interface DailyBudget {
  spent: number;
  limit: number;
  remaining: number;
}

export interface ReviewItem {
  id: number;
  symbol: string;
  strategy: string;
  score: number;
  reason: string | null;
  created_at: string;
}

export interface PipelineData {
  pipeline_runs: PipelineRun[];
  next_scheduled: string;
  approval_status: ApprovalStatus | null;
  daily_budget: DailyBudget;
  review_queue: ReviewItem[];
}
```

### Example 2: Sortable Column Definition for Scoring Table

```typescript
// dashboard/src/components/signals/columns.tsx
'use client';

import type { ColumnDef } from '@tanstack/react-table';
import { ArrowUpDown } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatScore } from '@/lib/formatters';
import type { ScoreRow } from '@/types/api';

function signalVariant(signal: string) {
  switch (signal) {
    case 'BUY': return 'default' as const;      // amber bg (primary)
    case 'SELL': return 'destructive' as const;  // red
    default: return 'secondary' as const;        // muted
  }
}

export const scoringColumns: ColumnDef<ScoreRow>[] = [
  {
    accessorKey: 'symbol',
    header: 'Symbol',
    cell: ({ row }) => (
      <span className="font-medium">{row.getValue('symbol')}</span>
    ),
  },
  {
    accessorKey: 'composite',
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        className="px-0 hover:bg-transparent"
      >
        Composite
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row }) => (
      <span className="font-mono tabular-nums text-right">
        {formatScore(row.getValue('composite'))}
      </span>
    ),
  },
  {
    accessorKey: 'risk_adjusted',
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        className="px-0 hover:bg-transparent"
      >
        Risk-Adj
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row }) => (
      <span className="font-mono tabular-nums text-right">
        {formatScore(row.getValue('risk_adjusted'))}
      </span>
    ),
  },
  {
    accessorKey: 'signal',
    header: 'Signal',
    cell: ({ row }) => {
      const signal = row.getValue('signal') as string;
      return <Badge variant={signalVariant(signal)}>{signal}</Badge>;
    },
  },
];
```

### Example 3: Review Queue with Approve/Reject Mutations

```typescript
// dashboard/src/components/pipeline/review-queue.tsx (pattern)
'use client';

import { Button } from '@/components/ui/button';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { useReviewAction } from '@/hooks/use-pipeline';
import { formatScore } from '@/lib/formatters';
import type { ReviewItem } from '@/types/api';
import { Check, X } from 'lucide-react';

export function ReviewQueue({ items }: { items: ReviewItem[] }) {
  const approve = useReviewAction('approve');
  const reject = useReviewAction('reject');

  if (items.length === 0) {
    return <p className="py-4 text-sm text-muted-foreground">No pending reviews</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Symbol</TableHead>
          <TableHead>Strategy</TableHead>
          <TableHead className="text-right">Score</TableHead>
          <TableHead>Date</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="font-medium">{item.symbol}</TableCell>
            <TableCell>{item.strategy}</TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatScore(item.score)}
            </TableCell>
            <TableCell>{item.created_at}</TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <Button
                  size="icon-xs"
                  variant="ghost"
                  onClick={() => approve.mutate(item.id)}
                  disabled={approve.isPending}
                >
                  <Check className="h-3 w-3 text-profit" />
                </Button>
                <Button
                  size="icon-xs"
                  variant="ghost"
                  onClick={() => reject.mutate(item.id)}
                  disabled={reject.isPending}
                >
                  <X className="h-3 w-3 text-loss" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Example 4: Regime Badge with Color Mapping

```typescript
// dashboard/src/components/risk/regime-badge.tsx
'use client';

import { Badge } from '@/components/ui/badge';

const REGIME_STYLES: Record<string, string> = {
  Bull: 'bg-profit/20 text-profit border-profit/30',
  Bear: 'bg-loss/20 text-loss border-loss/30',
  Accumulation: 'bg-chart-1/20 text-chart-1 border-chart-1/30',
  Distribution: 'bg-interactive/20 text-interactive border-interactive/30',
};

export function RegimeBadge({ regime }: { regime: string }) {
  const style = REGIME_STYLES[regime] ?? 'bg-muted text-muted-foreground';
  return (
    <Badge variant="outline" className={style}>
      {regime}
    </Badge>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw `useEffect` + `fetch` in page stubs | TanStack Query `useQuery` + `useMutation` | Phase 22 (current project) | All data fetching uses query hooks. Stubs are the last holdout. |
| Plotly.js for charts in Python backend | CSS `conic-gradient` + TradingView Lightweight Charts | Phase 22 (current project) | Plotly JSON stripped from API responses. React frontend uses CSS or lightweight-charts. |
| shadcn/ui DataTable via `@radix-ui` | shadcn/ui DataTable via `@base-ui/react` | shadcn v4 (base-nova style, 2025) | Components use `@base-ui/react` primitives. Project already uses this (`badge.tsx`, `button.tsx`). |
| TanStack Table v8 `addSortingFns` | TanStack Table v8 `getSortedRowModel` | Stable since v8.10+ | No migration needed. Same API pattern as official docs. |

## Open Questions

1. **Backend sort vs client-side sort for Signals table**
   - What we know: Backend `SignalsQueryHandler.handle()` accepts `sort_by` and `sort_desc` params. TanStack Table provides client-side sorting.
   - What's unclear: Whether to use backend sorting (pass query params to API) or client-side sorting (TanStack Table).
   - Recommendation: Use **client-side sorting only** (TanStack Table). The scoring data is small (<50 rows). Client-side sort gives instant feedback without network latency. Server-side sort params exist for the legacy HTMX dashboard. Do not pass sort params from the React frontend.

2. **Approval form field defaults**
   - What we know: `ApprovalCreateRequest` has defaults: `score_threshold=70.0`, `allowed_regimes=["Bull", "Accumulation"]`, `max_per_trade_pct=8.0`, `daily_budget_cap=10000.0`, `expires_in_days=30`.
   - What's unclear: Whether the form should expose all 5 fields or just the most important ones.
   - Recommendation: Expose all 5 fields with the backend defaults pre-populated. The form is for power users (the trader) who need full control. Hiding fields would reduce transparency, which conflicts with the core value of explainability.

3. **Signal card layout for variable number of signals**
   - What we know: The number of active signals varies (0 to potentially 20+).
   - What's unclear: Whether to use a scrollable container or paginate.
   - Recommendation: Use a responsive CSS grid (2-3 columns) with all signal cards visible. If the count exceeds ~12, add a collapsible "Show all" pattern. For v1.3, render all cards in a grid -- the typical count is <10.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Biome 2.4.7 (lint + format) + TypeScript tsc (type check) |
| Config file | `dashboard/biome.json` + `dashboard/tsconfig.json` |
| Quick run command | `cd /home/mqz/workspace/trading/dashboard && npx tsc --noEmit && npx biome check .` |
| Full suite command | `cd /home/mqz/workspace/trading/dashboard && npm run build` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SGNL-01 | Scoring table renders with correct columns | smoke | `npx tsc --noEmit` (validates types against API shape) | -- Wave 0 |
| SGNL-02 | Signal cards render BUY/SELL/HOLD with strength | smoke | `npx tsc --noEmit` | -- Wave 0 |
| SGNL-03 | Column sorting works on composite and risk_adjusted | manual | `npm run build` (validates TanStack Table integration) | -- Wave 0 |
| RISK-01 | Drawdown gauge renders with 3-tier color | manual | `npx tsc --noEmit` | -- Wave 0 |
| RISK-02 | Sector donut chart renders from sector_weights | manual | `npx tsc --noEmit` | -- Wave 0 |
| RISK-03 | Position limit progress bars render | smoke | `npx tsc --noEmit` | -- Wave 0 |
| RISK-04 | Regime badge shows regime with correct color | smoke | `npx tsc --noEmit` | -- Wave 0 |
| PIPE-01 | Pipeline run form submits to backend | manual | `npm run build` (validates mutation hook types) | -- Wave 0 |
| PIPE-02 | Pipeline history table renders runs | smoke | `npx tsc --noEmit` | -- Wave 0 |
| PIPE-03 | Approval create/suspend/resume forms work | manual | `npm run build` | -- Wave 0 |
| PIPE-04 | Review queue approve/reject buttons work | manual | `npm run build` | -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd /home/mqz/workspace/trading/dashboard && npx tsc --noEmit && npx biome check .`
- **Per wave merge:** `cd /home/mqz/workspace/trading/dashboard && npm run build`
- **Phase gate:** Full build green + manual visual verification of all three pages rendering with correct data display and interactive elements

### Wave 0 Gaps
- [ ] `@tanstack/react-table` -- install: `npm install @tanstack/react-table`
- [ ] shadcn/ui form components -- install: `npx shadcn@latest add progress input label checkbox select`
- [ ] `dashboard/src/types/api.ts` -- extend with SignalsData, RiskData, PipelineData types
- [ ] `dashboard/src/hooks/use-signals.ts` -- TanStack Query hook for signals
- [ ] `dashboard/src/hooks/use-risk.ts` -- TanStack Query hook for risk
- [ ] `dashboard/src/hooks/use-pipeline.ts` -- TanStack Query hook + mutations for pipeline
- [ ] `npm run build` passing with all new components and dependencies

## Sources

### Primary (HIGH confidence)
- Codebase: `src/dashboard/application/queries.py` -- SignalsQueryHandler, RiskQueryHandler, PipelineQueryHandler return shapes (verified all field names and types directly from source code)
- Codebase: `src/dashboard/presentation/api_routes.py` -- All REST API endpoints, request/response contracts, Pydantic models
- Codebase: `dashboard/src/types/api.ts` -- Existing TypeScript types from Phase 22
- Codebase: `dashboard/src/hooks/use-overview.ts` -- Established TanStack Query hook pattern
- Codebase: `dashboard/src/components/overview/*.tsx` -- Established component patterns (shadcn Table, Card, Badge, formatters)
- Codebase: `dashboard/package.json` -- Current dependencies (confirms @tanstack/react-query 5.90.x installed, no @tanstack/react-table yet)
- [shadcn/ui DataTable Docs](https://ui.shadcn.com/docs/components/radix/data-table) -- TanStack Table integration pattern, sortable columns, column definitions
- [TanStack Table Sorting Guide](https://tanstack.com/table/v8/docs/guide/sorting) -- getSortedRowModel, SortingState, toggleSorting API

### Secondary (MEDIUM confidence)
- [Smashing Magazine: Dynamic Donut Charts with TailwindCSS and React](https://www.smashingmagazine.com/2023/03/dynamic-donut-charts-tailwind-css-react/) -- CSS conic-gradient donut pattern
- [CSS conic-gradient charts repository](https://github.com/PaulieScanlon/css-conic-gradient-charts) -- Zero-dependency donut implementation pattern
- [shadcn/ui Tailwind v4 changelog](https://ui.shadcn.com/docs/changelog/2025-02-tailwind-v4) -- Component compatibility with Tailwind v4 and React 19

### Tertiary (LOW confidence)
- CSS arc gauge approach (semicircle via overflow:hidden + conic-gradient) -- community pattern, not standardized. Verified visually but implementation details may need adjustment during development.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Only new dependency is @tanstack/react-table, which is the official companion to the already-installed @tanstack/react-query. shadcn/ui components are well-established.
- Architecture: HIGH -- Following exact patterns from Phase 22 (hooks, components, types). Data contracts read directly from Python source code. All API endpoints verified in api_routes.py.
- Pitfalls: HIGH -- Mutation cache invalidation and double-submit are well-documented TanStack Query patterns. Column definition recreation is documented in TanStack Table docs.
- CSS visualizations (donut, gauge): MEDIUM -- CSS conic-gradient is reliable for donut charts but the arc gauge semicircle approach may need CSS tweaking during implementation.

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days -- stable technologies, patterns established in Phase 22)
