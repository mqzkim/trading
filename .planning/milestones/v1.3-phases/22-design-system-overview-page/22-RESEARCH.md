# Phase 22: Design System & Overview Page - Research

**Researched:** 2026-03-14
**Domain:** Bloomberg-style dark theme design system (shadcn/ui + Tailwind v4), TradingView equity curve chart, data-dense financial dashboard components
**Confidence:** HIGH

## Summary

Phase 22 transforms the Phase 21 skeleton stubs into a professional Bloomberg terminal-style dashboard. This requires two distinct workstreams: (1) establishing a design system with dark theme tokens, monospace number fonts, semantic colors, and shadcn/ui components customized for Bloomberg aesthetics; and (2) building the Overview page with KPI cards, a holdings table, a TradingView equity curve chart with regime background coloring, and a trade history table.

The existing project already has Next.js 16.1.6, React 19.2.3, Tailwind CSS v4, and Biome 2.4.7 in place from Phase 21. Phase 22 adds shadcn/ui (CLI-based, vendored components), TradingView Lightweight Charts (lightweight-charts npm package), TanStack React Query v5 (server state management), and JetBrains Mono font (monospace numbers). The existing page stubs at `dashboard/src/app/(dashboard)/page.tsx` and layout at `dashboard/src/app/(dashboard)/layout.tsx` will be replaced with real components.

The API data contract is already defined by the FastAPI JSON endpoints from Phase 21. `OverviewQueryHandler.handle()` returns `total_value`, `today_pnl`, `drawdown_pct`, `last_pipeline`, `positions` (list), `trade_history` (list), `equity_curve` (dates + values), and `regime_periods` (list). The React components consume this exact shape.

**Primary recommendation:** Initialize shadcn/ui first (creates `components.json` and CSS variables), then customize the Bloomberg dark theme tokens in `globals.css`, then build reusable components (KPI card, data table), then assemble the Overview page. Use TanStack Query for all data fetching (replacing raw `useEffect` + `fetch`). Use `next/font/google` for JetBrains Mono to avoid FOUT.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DSGN-01 | Bloomberg dark theme color token system | shadcn/ui CSS custom properties in `:root` / `.dark` selectors with OKLCH values. Customize `--background`, `--foreground`, `--card`, etc. to Bloomberg palette (near-black bg, off-white text). |
| DSGN-02 | Monospace number font for financial data alignment | JetBrains Mono via `next/font/google`. Apply as CSS variable and Tailwind utility class `font-mono` for numeric displays. Tabular number OpenType feature (`font-variant-numeric: tabular-nums`) for column alignment. |
| DSGN-03 | Semantic colors (profit=cyan, loss=red, neutral=white, interactive=amber) | Extend shadcn/ui CSS variables with custom `--profit`, `--loss`, `--neutral`, `--interactive` tokens. Map to Tailwind utilities via `@theme inline`. |
| DSGN-04 | shadcn/ui components customized for Bloomberg style | `npx shadcn@latest init` then `add card table badge separator`. Components automatically use CSS variables. Customize border radius (small), reduce padding, increase data density. |
| OVER-01 | KPI cards (total assets, daily P&L, drawdown, pipeline status) | `OverviewQueryHandler.handle()` returns `total_value`, `today_pnl`, `drawdown_pct`, `last_pipeline`. Wrap in shadcn `Card` component with semantic color coding. |
| OVER-02 | Holdings table (ticker, qty, price, P&L, stop, target, score) | `positions` array from overview API. Use shadcn `Table` with monospace numbers. P&L cells color-coded with `--profit` / `--loss` tokens. |
| OVER-03 | TradingView equity curve with regime background coloring | `equity_curve` (dates/values) + `regime_periods` from API. Use `lightweight-charts` AreaSeries for equity curve. Regime backgrounds via Histogram overlay series with low opacity colors. |
| OVER-04 | Trade history table | `trade_history` array from overview API. shadcn `Table` displaying symbol, direction, entry price, stop, target, quantity, value, score, status, date. |
</phase_requirements>

## Standard Stack

### Core (Phase 22 additions to existing project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shadcn/ui | CLI-based (latest) | Accessible React components (Card, Table, Badge) | Zero runtime -- copies source into project. Tailwind-native. Dark mode via CSS variables. All components updated for Tailwind v4 + React 19. |
| lightweight-charts | 5.1.x | TradingView equity curve chart | 35-45KB gzipped. Canvas-based. Industry standard for financial charts. Official React integration via useRef + useEffect. |
| @tanstack/react-query | 5.90.x | Server state (API data fetching, caching) | Handles all FastAPI data fetching with automatic caching, background refetch, stale-while-revalidate. Replaces manual useEffect + fetch pattern from Phase 21 stubs. |
| next-themes | 0.4.x | Dark/light theme management | Prevents flash of wrong theme on load. System preference detection. Default to dark (Bloomberg style). |
| tw-animate-css | latest | Tailwind animation utilities | Replaces deprecated tailwindcss-animate. Required by shadcn/ui components for transitions. |

### Fonts

| Font | Source | Purpose | How |
|------|--------|---------|-----|
| Inter | next/font/google | UI text (labels, navigation, headers) | Already in root layout from Phase 21. Body text font. |
| JetBrains Mono | next/font/google | Monospace numbers (prices, P&L, scores, table data) | Financial data alignment. Tabular nums for column alignment. Apply via CSS variable `--font-mono`. |

### Already Installed (Phase 21)

| Library | Version | Status |
|---------|---------|--------|
| Next.js | 16.1.6 | Installed |
| React | 19.2.3 | Installed |
| Tailwind CSS | 4.x | Installed |
| @biomejs/biome | 2.4.7 | Installed |
| TypeScript | 5.x | Installed |

### Not Yet Needed (Later Phases)

| Library | Phase | Purpose |
|---------|-------|---------|
| zustand | 23+ | Client state (filter selections, UI state) |
| @tanstack/react-table | 23 | Headless table sorting/filtering (for Signals page) |
| @tanstack/react-virtual | 23+ | Virtual scrolling for 200+ row tables |

**Installation:**

```bash
cd /home/mqz/workspace/trading/dashboard

# shadcn/ui initialization
npx shadcn@latest init
# Select: New York style, neutral base color

# Add shadcn components needed for Phase 22
npx shadcn@latest add card table badge separator skeleton

# Core dependencies
npm install lightweight-charts @tanstack/react-query next-themes

# tw-animate-css (installed by shadcn init, but verify)
npm install -D tw-animate-css
```

## Architecture Patterns

### Recommended Project Structure (Phase 22 scope)

```
dashboard/src/
  app/
    (dashboard)/
      page.tsx              # Overview page (replaced - uses real components)
      layout.tsx            # Dashboard layout (replaced - Bloomberg nav + theme)
      signals/page.tsx      # Stub (unchanged in Phase 22)
      risk/page.tsx         # Stub (unchanged in Phase 22)
      pipeline/page.tsx     # Stub (unchanged in Phase 22)
    layout.tsx              # Root layout (updated - fonts, providers, ThemeProvider)
    globals.css             # Theme tokens (Bloomberg dark palette + shadcn vars)
    providers.tsx           # NEW: QueryClientProvider + ThemeProvider wrapper
  components/
    ui/                     # shadcn/ui vendored components (auto-generated)
      card.tsx
      table.tsx
      badge.tsx
      separator.tsx
      skeleton.tsx
    overview/               # NEW: Overview page components
      kpi-cards.tsx         # 4 KPI metric cards
      holdings-table.tsx    # Positions table
      equity-curve.tsx      # TradingView chart wrapper
      trade-history.tsx     # Executed trades table
  hooks/
    use-overview.ts         # NEW: TanStack Query hook for overview data
  lib/
    utils.ts                # shadcn cn() utility (auto-generated by init)
    formatters.ts           # NEW: Currency, percentage, date formatting
  types/
    api.ts                  # NEW: TypeScript types matching FastAPI response
```

### Pattern 1: shadcn/ui Theming with Bloomberg Dark Palette

**What:** Define CSS custom properties in `globals.css` using OKLCH values. shadcn/ui components automatically consume these variables. Extend with custom financial tokens (`--profit`, `--loss`, `--interactive`).

**Why:** shadcn/ui's theming is built on CSS custom properties. The Bloomberg look comes from customizing these variables, not overriding component styles. All components inherit the theme automatically.

```css
/* globals.css - Bloomberg Dark Theme */
@import "tailwindcss";
@import "tw-animate-css";

:root {
  --radius: 0.375rem;
  /* Light mode tokens (minimal - default to dark) */
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
}

.dark {
  /* Bloomberg deep black background */
  --background: oklch(0.08 0.005 250);
  --foreground: oklch(0.93 0 0);

  /* Card surfaces - slightly lighter than background */
  --card: oklch(0.12 0.005 250);
  --card-foreground: oklch(0.93 0 0);

  /* Muted elements */
  --muted: oklch(0.2 0.005 250);
  --muted-foreground: oklch(0.6 0 0);

  /* Interactive amber (Bloomberg signature) */
  --primary: oklch(0.78 0.15 75);
  --primary-foreground: oklch(0.1 0 0);

  /* Secondary - subtle surface */
  --secondary: oklch(0.18 0.005 250);
  --secondary-foreground: oklch(0.9 0 0);

  /* Accent - hover states */
  --accent: oklch(0.22 0.01 250);
  --accent-foreground: oklch(0.93 0 0);

  /* Destructive - losses */
  --destructive: oklch(0.6 0.2 25);
  --destructive-foreground: oklch(0.93 0 0);

  /* Borders */
  --border: oklch(0.22 0.005 250);
  --input: oklch(0.22 0.005 250);
  --ring: oklch(0.78 0.15 75);

  /* Chart palette */
  --chart-1: oklch(0.7 0.15 200);
  --chart-2: oklch(0.78 0.15 75);
  --chart-3: oklch(0.65 0.15 150);
  --chart-4: oklch(0.6 0.2 25);
  --chart-5: oklch(0.7 0.12 300);

  /* Financial semantic tokens (custom extension) */
  --profit: oklch(0.75 0.18 180);
  --loss: oklch(0.65 0.22 25);
  --neutral: oklch(0.85 0 0);
  --interactive: oklch(0.78 0.15 75);
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);
  --color-profit: var(--profit);
  --color-loss: var(--loss);
  --color-neutral: var(--neutral);
  --color-interactive: var(--interactive);
  --radius-sm: calc(var(--radius) - 0.125rem);
  --radius-md: var(--radius);
  --radius-lg: calc(var(--radius) + 0.125rem);
  --radius-xl: calc(var(--radius) + 0.25rem);

  --font-mono: var(--font-jetbrains-mono);
}
```

### Pattern 2: JetBrains Mono for Financial Numbers

**What:** Load JetBrains Mono via `next/font/google` and apply as a CSS variable. Use `font-mono` Tailwind class for numeric displays. Enable `tabular-nums` for column alignment.

**Why:** Monospace fonts ensure numbers of different lengths (e.g. $1,234.56 vs $123.45) occupy the same width, making columns of financial data scannable. Tabular figures prevent layout shifts when numbers change.

```typescript
// dashboard/src/app/layout.tsx
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

```css
/* In component usage -- monospace for numbers */
.tabular-nums {
  font-variant-numeric: tabular-nums;
}
```

### Pattern 3: TanStack Query Provider + next-themes Setup

**What:** Create a client-side Providers component that wraps children with `QueryClientProvider` and `ThemeProvider`. Mount in root layout.

**Why:** Both TanStack Query and next-themes require context providers. Grouping them in a single `'use client'` component keeps the root layout as a Server Component.

```typescript
// dashboard/src/app/providers.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,       // 30 seconds before refetch
            refetchOnWindowFocus: true,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
```

### Pattern 4: TradingView Equity Curve with Regime Backgrounds

**What:** Use `lightweight-charts` AreaSeries for the equity curve line. For regime background coloring, use a Histogram series overlay with very low opacity colors covering the full price range during each regime period.

**Why:** Lightweight Charts does not have a native "background region" feature. The standard workaround is to add a Histogram series on a separate price scale that fills the chart area with colored bars for each time period. Each bar's color represents the regime (e.g., green for Bull, red for Bear, blue for Accumulation).

```typescript
// dashboard/src/components/overview/equity-curve.tsx
'use client';

import { useEffect, useLayoutEffect, useRef } from 'react';
import { createChart, ColorType, AreaSeries, HistogramSeries } from 'lightweight-charts';

interface EquityCurveProps {
  data: { time: string; value: number }[];
  regimePeriods: { start: string; end: string; regime: string }[];
}

const REGIME_COLORS: Record<string, string> = {
  Bull: 'rgba(0, 200, 83, 0.08)',
  Bear: 'rgba(255, 82, 82, 0.08)',
  Accumulation: 'rgba(79, 195, 247, 0.08)',
  Distribution: 'rgba(255, 183, 77, 0.08)',
  Unknown: 'rgba(128, 128, 128, 0.05)',
};

export function EquityCurve({ data, regimePeriods }: EquityCurveProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<{ isRemoved: boolean } | null>(null);

  useLayoutEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9ca3af',
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
      },
      width: containerRef.current.clientWidth,
      height: 300,
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: 'rgba(255, 255, 255, 0.1)' },
      timeScale: { borderColor: 'rgba(255, 255, 255, 0.1)' },
    });

    chartRef.current = { isRemoved: false };

    // Equity curve line
    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: '#4fc3f7',
      topColor: 'rgba(79, 195, 247, 0.25)',
      bottomColor: 'rgba(79, 195, 247, 0.0)',
      lineWidth: 2,
    });
    areaSeries.setData(data);

    // Regime background coloring via histogram overlay
    if (regimePeriods.length > 0) {
      const histogramSeries = chart.addSeries(HistogramSeries, {
        priceScaleId: '',
        color: 'transparent',
        priceFormat: { type: 'volume' },
        lastValueVisible: false,
        priceLineVisible: false,
      });

      // Build regime data for each equity curve date
      const regimeData = data.map((point) => {
        const regime = regimePeriods.find(
          (r) => point.time >= r.start && point.time <= r.end,
        );
        return {
          time: point.time,
          value: 1,
          color: regime ? REGIME_COLORS[regime.regime] || REGIME_COLORS.Unknown : 'transparent',
        };
      });
      histogramSeries.setData(regimeData);
      histogramSeries.priceScale().applyOptions({
        scaleMargins: { top: 0, bottom: 0 },
      });
    }

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current && !chartRef.current?.isRemoved) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      if (chartRef.current) chartRef.current.isRemoved = true;
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [data, regimePeriods]);

  return <div ref={containerRef} className="w-full" />;
}
```

### Pattern 5: TanStack Query Hook for Overview Data

**What:** Replace the Phase 21 raw `useEffect` + `fetch` with a typed TanStack Query hook. This handles loading, error, caching, and refetching automatically.

```typescript
// dashboard/src/hooks/use-overview.ts
import { useQuery } from '@tanstack/react-query';
import type { OverviewData } from '@/types/api';

export function useOverview() {
  return useQuery<OverviewData>({
    queryKey: ['overview'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/overview');
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    retry: 1,
  });
}
```

### Pattern 6: TypeScript Types Matching FastAPI Response

**What:** Define TypeScript interfaces that mirror the Python dict shapes returned by `OverviewQueryHandler.handle()`.

```typescript
// dashboard/src/types/api.ts
export interface Position {
  symbol: string;
  qty: number;
  current_price: number;
  pnl_pct: number;
  pnl_dollar: number;
  stop_price: number;
  target_price: number;
  composite_score: number;
  market_value: number;
}

export interface TradeHistoryItem {
  symbol: string;
  direction: string;
  entry_price: number;
  stop_loss_price: number;
  take_profit_price: number;
  quantity: number;
  position_value: number;
  composite_score: number;
  signal_direction: string;
  status: string;
  created_at: string;
}

export interface EquityCurve {
  dates: string[];
  values: number[];
}

export interface RegimePeriod {
  start: string;
  end: string;
  regime: string;
}

export interface LastPipeline {
  run_id: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface OverviewData {
  total_value: number;
  today_pnl: number;
  drawdown_pct: number;
  last_pipeline: LastPipeline | null;
  positions: Position[];
  trade_history: TradeHistoryItem[];
  equity_curve: EquityCurve;
  regime_periods: RegimePeriod[];
}
```

### Anti-Patterns to Avoid

- **Hardcoding hex colors in components:** Every color must come from CSS variables. Components use Tailwind classes like `bg-card`, `text-profit`, `text-loss`. Never `#ff5252` in TSX files.
- **Installing plotly.js or react-plotly.js:** All charts use TradingView Lightweight Charts or CSS/SVG. Zero Plotly in the frontend.
- **Using `useState` + `useEffect` for data fetching:** TanStack Query handles caching, loading states, error states, refetching. Raw fetch in useEffect is the Phase 21 stub pattern that gets replaced.
- **SSR for chart components:** TradingView charts require browser APIs (canvas, ResizeObserver). Always use `'use client'` directive. Wrap with loading skeleton.
- **Importing lightweight-charts at module top level in Server Components:** This causes SSR errors because the library accesses `window`. Keep all chart code in `'use client'` components.
- **Using `suppressHydrationWarning` on data elements:** This hides real bugs. Use Client Components for dynamic data instead.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark theme toggle | Custom CSS class switching logic | next-themes ThemeProvider | Prevents FOUC, handles system preference, persists to localStorage |
| Data tables | Custom `<table>` with manual sorting | shadcn/ui Table component | Accessible, styled, dark-mode-ready. Sorting comes in Phase 23 via @tanstack/react-table. |
| Loading skeletons | Custom div + animation | shadcn/ui Skeleton component | Matches theme automatically, pulse animation from tw-animate-css |
| Number formatting | Manual `.toFixed()` + string concat | Intl.NumberFormat with formatters.ts | Handles currency ($), percentage (%), locale, edge cases (NaN, Infinity) |
| Card component | Custom div wrapper | shadcn/ui Card + CardHeader + CardContent | Accessible, consistent spacing, theme-aware borders |
| cn() utility | Manual className concatenation | shadcn/ui lib/utils.ts (clsx + tailwind-merge) | Handles conditional classes, resolves Tailwind conflicts |
| Chart resize handling | window.addEventListener resize | ResizeObserver in useLayoutEffect | Per-element resize, more efficient, handles CSS layout changes |

## Common Pitfalls

### Pitfall 1: shadcn/ui Init Overwrites globals.css

**What goes wrong:** Running `npx shadcn@latest init` overwrites the existing `globals.css` file with shadcn's default theme variables, losing any custom Tailwind imports or configurations from Phase 21.
**Why it happens:** The shadcn CLI replaces `globals.css` entirely during initialization. The Phase 21 file has `@import "tailwindcss"` and nothing else, so the loss is minimal, but the init adds new CSS variable blocks.
**How to avoid:** Run `npx shadcn@latest init` first, then customize the generated `globals.css` with Bloomberg dark theme tokens. Do not add custom CSS before running init.
**Warning signs:** Missing `@import "tailwindcss"` after init. Build errors about unknown utilities.

### Pitfall 2: TradingView Chart Memory Leaks on Navigation

**What goes wrong:** Chart canvas and GPU resources leak if `chart.remove()` is not called in cleanup. After 10-20 page transitions, browser consumes 500MB+.
**Why it happens:** React useEffect cleanup runs async, allowing parent chart to be destroyed before child series cleanup. Developers remove cleanup code to "fix" errors, introducing the leak.
**How to avoid:** Use `useLayoutEffect` (synchronous cleanup). Set `isRemoved` flag before calling `chart.remove()`. Guard child operations with the flag. This is the TradingView official recommended pattern.
**Warning signs:** DevTools Memory tab shows monotonically increasing heap. Canvas element count grows after each navigation.

### Pitfall 3: OKLCH vs HSL Color Format Confusion

**What goes wrong:** Older shadcn/ui examples use HSL format (`hsl(222.2 84% 4.9%)`). Current shadcn/ui with Tailwind v4 uses OKLCH format (`oklch(0.145 0 0)`). Mixing formats causes invisible or garbled colors.
**Why it happens:** shadcn/ui migrated from HSL to OKLCH in their Tailwind v4 update (February 2025). Many tutorials and blog posts still show HSL.
**How to avoid:** Use OKLCH values exclusively. The shadcn CLI generates OKLCH by default when initialized with Tailwind v4 projects. Convert any custom Bloomberg colors to OKLCH using browser DevTools color picker or oklch.com.
**Warning signs:** Colors appearing washed out, wrong hue, or invisible. Browser DevTools showing `invalid color` warnings.

### Pitfall 4: QueryClient Re-creation on Every Render

**What goes wrong:** Creating `new QueryClient()` inside the component body (not in useState) causes a new client on every render. All cached data is lost, queries re-fire, and the UI flashes.
**Why it happens:** React strict mode and App Router re-render components. Without `useState` to stabilize the instance, it is recreated.
**How to avoid:** Always wrap `new QueryClient()` in `useState(() => new QueryClient(...))` inside the Providers component. Never create QueryClient at module scope in a client component (risks shared state across users in SSR).
**Warning signs:** API calls firing twice on every navigation. Loading spinners appearing where data was already cached.

### Pitfall 5: Font Flash (FOUT) with Custom Monospace Font

**What goes wrong:** JetBrains Mono loads after the initial render, causing numbers to shift width as the font swaps from fallback to custom.
**Why it happens:** Web fonts load asynchronously. Without preloading, the browser renders with a system fallback first.
**How to avoid:** Use `next/font/google` which automatically handles font preloading, `font-display: swap`, and generates CSS variables. Apply the font variable to `<body>` so it is available immediately.
**Warning signs:** Numbers visibly jumping/shifting width on initial page load. Table columns misaligning then correcting.

### Pitfall 6: Dark Theme Incomplete (Scrollbars, Focus Rings, Inputs)

**What goes wrong:** Setting dark background on body leaves scrollbars white (Windows), focus rings invisible (blue on dark blue), and browser-default form inputs light-styled.
**Why it happens:** OS-level UI elements (scrollbars, form inputs) follow system theme. Dark CSS backgrounds do not cascade to browser chrome.
**How to avoid:** Add scrollbar styling (`::-webkit-scrollbar` + `scrollbar-color` for Firefox). Set `color-scheme: dark` on `html` element. shadcn/ui components handle focus rings via the `--ring` CSS variable. Test on Windows (scrollbars differ from macOS).
**Warning signs:** White scrollbars on Windows. Invisible focus rings on buttons/inputs. Light-colored file picker or date inputs.

## Code Examples

### Example 1: KPI Card Component

```typescript
// dashboard/src/components/overview/kpi-cards.tsx
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatPercent } from '@/lib/formatters';
import type { OverviewData } from '@/types/api';

interface KpiCardsProps {
  data: OverviewData;
}

export function KpiCards({ data }: KpiCardsProps) {
  const pnlColor = data.today_pnl >= 0 ? 'text-profit' : 'text-loss';
  const pnlSign = data.today_pnl >= 0 ? '+' : '';
  const drawdownColor =
    data.drawdown_pct <= 10 ? 'text-profit' :
    data.drawdown_pct <= 15 ? 'text-interactive' :
    'text-loss';

  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Total Value</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-mono tabular-nums">
            {formatCurrency(data.total_value)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Daily P&L</CardTitle>
        </CardHeader>
        <CardContent>
          <p className={`text-2xl font-mono tabular-nums ${pnlColor}`}>
            {pnlSign}{formatCurrency(data.today_pnl)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Drawdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className={`text-2xl font-mono tabular-nums ${drawdownColor}`}>
            {formatPercent(data.drawdown_pct)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-lg font-mono">
            {data.last_pipeline?.status ?? 'No runs'}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Example 2: Number Formatting Utilities

```typescript
// dashboard/src/lib/formatters.ts
const currencyFmt = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percentFmt = new Intl.NumberFormat('en-US', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const scoreFmt = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatCurrency(value: number): string {
  if (!Number.isFinite(value)) return '$0.00';
  return currencyFmt.format(value);
}

export function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return '0.0%';
  return percentFmt.format(value / 100);
}

export function formatScore(value: number): string {
  if (!Number.isFinite(value)) return '0.0';
  return scoreFmt.format(value);
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '--';
  return dateStr.slice(0, 10);
}
```

### Example 3: Holdings Table with Semantic Colors

```typescript
// dashboard/src/components/overview/holdings-table.tsx
'use client';

import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { formatCurrency, formatPercent, formatScore } from '@/lib/formatters';
import type { Position } from '@/types/api';

export function HoldingsTable({ positions }: { positions: Position[] }) {
  if (positions.length === 0) {
    return <p className="text-muted-foreground text-sm py-4">No open positions</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Ticker</TableHead>
          <TableHead className="text-right">Qty</TableHead>
          <TableHead className="text-right">Price</TableHead>
          <TableHead className="text-right">P&L</TableHead>
          <TableHead className="text-right">Stop</TableHead>
          <TableHead className="text-right">Target</TableHead>
          <TableHead className="text-right">Score</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {positions.map((pos) => {
          const pnlColor = pos.pnl_dollar >= 0 ? 'text-profit' : 'text-loss';
          return (
            <TableRow key={pos.symbol}>
              <TableCell className="font-medium">{pos.symbol}</TableCell>
              <TableCell className="text-right font-mono tabular-nums">
                {pos.qty}
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">
                {formatCurrency(pos.current_price)}
              </TableCell>
              <TableCell className={`text-right font-mono tabular-nums ${pnlColor}`}>
                {formatCurrency(pos.pnl_dollar)}
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">
                {formatCurrency(pos.stop_price)}
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">
                {formatCurrency(pos.target_price)}
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">
                {formatScore(pos.composite_score)}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| shadcn/ui HSL color format | OKLCH color format | Feb 2025 (Tailwind v4 update) | All color variables must use `oklch()` not `hsl()`. |
| tailwindcss-animate | tw-animate-css | Feb 2025 | `tailwindcss-animate` deprecated. New projects use `tw-animate-css`. |
| `forwardRef` in shadcn components | Direct ref prop (React 19) | Oct 2025 (Next.js 16) | shadcn components updated for React 19. No `forwardRef` wrapper needed. |
| `lightweight-charts` v4 API | v5 API (modular imports) | Late 2024 | Series created via `chart.addSeries(AreaSeries)` not `chart.addAreaSeries()`. Markers via `createSeriesMarkers`. |
| `useMemo`/`useCallback` manual | React Compiler auto-memoization | Next.js 16 | React Compiler handles memoization. Manual `useMemo` is unnecessary but harmless. |
| Tailwind `tailwind.config.js` | CSS-first `@theme inline` | Tailwind v4 (2025) | No config file. Theme defined in CSS via `@theme inline` directive. |

## Open Questions

1. **Regime Background Coloring Fidelity**
   - What we know: Lightweight Charts does not have native "background region" support. A Histogram overlay with low opacity is the community standard workaround.
   - What is unclear: Whether the histogram approach provides sufficient visual clarity for regime coloring, or if a CSS overlay (positioned absolutely behind the chart container) would look better.
   - Recommendation: Start with the Histogram overlay approach. If visual quality is insufficient, fall back to a CSS gradient overlay positioned absolutely behind the chart container, driven by the regime period data.

2. **shadcn/ui Data Table vs Plain Table for Phase 22**
   - What we know: OVER-02 (holdings) and OVER-04 (trade history) need tables. shadcn/ui offers both a simple `Table` component and a full `DataTable` component (wrapping @tanstack/react-table).
   - What is unclear: Whether Phase 22 tables need sorting/filtering, or if that is Phase 23 scope.
   - Recommendation: Use the simpler `Table` component for Phase 22 (DSGN-04 says "customized components," not "interactive data grids"). Add DataTable with sorting in Phase 23 when SGNL-03 requires column sorting.

3. **TanStack Query vs Simple Fetch for Phase 22**
   - What we know: Phase 22 only has one API call (overview). TanStack Query adds a provider and library overhead.
   - What is unclear: Whether it is premature to add TanStack Query when only one endpoint is used.
   - Recommendation: Install TanStack Query now. Phase 23 adds 3 more endpoints, and Phase 24 adds SSE integration via `queryClient.setQueryData()`. Setting up the provider infrastructure once is cheaper than retrofitting later. The Overview page validates the pattern before scaling it.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Biome 2.4.7 (lint + format) + TypeScript tsc (type check) |
| Config file | `dashboard/biome.json` + `dashboard/tsconfig.json` |
| Quick run command | `cd /home/mqz/workspace/trading/dashboard && npx tsc --noEmit && npx biome check .` |
| Full suite command | `cd /home/mqz/workspace/trading/dashboard && npm run build` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DSGN-01 | Bloomberg dark theme renders (black bg, correct colors) | manual | `npm run build` (build validates CSS processing) | -- Wave 0 |
| DSGN-02 | Monospace numbers render aligned in tables | manual | `npx tsc --noEmit` (validates font variable usage) | -- Wave 0 |
| DSGN-03 | Semantic colors apply (cyan=profit, red=loss) | manual | `npm run build` (validates CSS variable references) | -- Wave 0 |
| DSGN-04 | shadcn/ui components render with Bloomberg styling | manual | `npm run build` (validates component imports) | -- Wave 0 |
| OVER-01 | KPI cards display total value, P&L, drawdown, pipeline | smoke | `npx tsc --noEmit` (type-checks component props against API types) | -- Wave 0 |
| OVER-02 | Holdings table renders positions with correct columns | smoke | `npx tsc --noEmit` | -- Wave 0 |
| OVER-03 | Equity curve chart renders with regime coloring | manual | `npm run build` (validates lightweight-charts import) | -- Wave 0 |
| OVER-04 | Trade history table displays executed trades | smoke | `npx tsc --noEmit` | -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd /home/mqz/workspace/trading/dashboard && npx tsc --noEmit && npx biome check .`
- **Per wave merge:** `cd /home/mqz/workspace/trading/dashboard && npm run build`
- **Phase gate:** Full build green + manual visual verification of dark theme + all Overview page sections rendering

### Wave 0 Gaps
- [ ] `dashboard/src/types/api.ts` -- TypeScript types matching FastAPI OverviewQueryHandler response shape
- [ ] `dashboard/src/lib/formatters.ts` -- Currency/percentage/score formatting utilities
- [ ] `npm run build` passing with all new components and dependencies
- [ ] shadcn/ui initialized (`components.json` exists)
- [ ] Manual: Overview page renders Bloomberg dark theme with all 4 sections visible

## Sources

### Primary (HIGH confidence)
- [shadcn/ui Tailwind v4 Docs](https://ui.shadcn.com/docs/tailwind-v4) -- OKLCH color format, @theme inline directive, tw-animate-css
- [shadcn/ui Next.js Installation](https://ui.shadcn.com/docs/installation/next) -- CLI init command, component add workflow
- [shadcn/ui Theming](https://ui.shadcn.com/docs/theming) -- Complete CSS custom property list, dark mode variable definitions
- [shadcn/ui components.json](https://ui.shadcn.com/docs/components-json) -- Configuration structure for Tailwind v4 projects
- [TradingView Lightweight Charts Official Docs](https://tradingview.github.io/lightweight-charts/) -- Series types, React integration patterns
- [TradingView Advanced React Tutorial](https://tradingview.github.io/lightweight-charts/tutorials/react/advanced) -- Context + ref lifecycle management, cleanup patterns
- [TanStack React Query v5 Next.js Example](https://tanstack.com/query/v5/docs/framework/react/examples/nextjs) -- QueryClientProvider setup with App Router
- Codebase: `src/dashboard/application/queries.py` -- OverviewQueryHandler.handle() return shape (verified all field names and types)
- Codebase: `dashboard/package.json` -- Current dependencies (Next.js 16.1.6, React 19.2.3, Tailwind 4.x)
- Codebase: `dashboard/src/app/(dashboard)/page.tsx` -- Phase 21 stub to replace
- Codebase: `dashboard/biome.json` -- Current Biome config with files.includes whitelist

### Secondary (MEDIUM confidence)
- [JetBrains Mono on Google Fonts](https://fonts.google.com/specimen/JetBrains+Mono) -- Font availability, OpenType features
- [Next.js Font Optimization Docs](https://nextjs.org/docs/app/getting-started/fonts) -- next/font/google usage, CSS variable approach
- [Bloomberg Terminal Color Accessibility](https://www.bloomberg.com/company/stories/designing-the-terminal-for-color-accessibility/) -- Red/green accessibility guidance for financial terminals
- [Bloomberg Color Palette Reference](https://www.color-hex.com/color-palette/111776) -- #000000, #ff433d, #0068ff, #4af6c3, #fb8b1e
- Project research: `.planning/research/STACK.md` -- v1.3 stack decisions (lightweight-charts, TanStack Query, shadcn/ui, next-themes)
- Project research: `.planning/research/PITFALLS.md` -- Chart memory leaks, dark theme gaps, hydration mismatch patterns

### Tertiary (LOW confidence)
- Histogram overlay approach for regime backgrounds -- community pattern, not officially documented by TradingView. May need CSS overlay fallback.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries verified from Phase 21 research + current official docs. Versions confirmed compatible.
- Architecture: HIGH -- shadcn/ui + Tailwind v4 CSS variable system is well-documented. TradingView React integration follows official tutorials. API data shapes read directly from Python source code.
- Pitfalls: HIGH -- Dark theme pitfalls from PITFALLS.md research + shadcn/ui HSL-to-OKLCH migration verified in official changelog. Chart memory leak pattern from TradingView official docs.
- Regime background coloring: MEDIUM -- Histogram overlay is a community workaround, not a first-class TradingView feature. May need CSS alternative.

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days -- stable technologies, shadcn/ui and lightweight-charts have slow release cadence)
