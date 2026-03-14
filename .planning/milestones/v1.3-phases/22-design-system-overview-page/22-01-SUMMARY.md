---
phase: 22-design-system-overview-page
plan: 01
subsystem: ui
tags: [shadcn-ui, tailwind-v4, bloomberg-dark-theme, tanstack-query, next-themes, jetbrains-mono, oklch]

# Dependency graph
requires:
  - phase: 21
    provides: Next.js 16 project scaffold with Biome, Tailwind v4, API proxy
provides:
  - shadcn/ui vendored components (Card, Table, Badge, Separator, Skeleton)
  - Bloomberg OKLCH dark theme with financial semantic tokens
  - JetBrains Mono monospace font for number alignment
  - QueryClientProvider + ThemeProvider infrastructure
  - TypeScript interfaces matching FastAPI OverviewQueryHandler response
  - Number formatting utilities (currency, percent, score, date)
  - useOverview TanStack Query hook for /api/v1/dashboard/overview
affects: [22-02-overview-page, 23-signals-risk-pipeline, 24-realtime]

# Tech tracking
tech-stack:
  added: [shadcn@4.0.6, "@tanstack/react-query@5.90.21", next-themes@0.4.6, lightweight-charts@5.1.0, tw-animate-css@1.4.0, clsx@2.1.1, tailwind-merge@3.5.0, class-variance-authority@0.7.1, lucide-react@0.577.0, "@base-ui/react@1.3.0"]
  patterns: [OKLCH CSS custom properties for theming, "@theme inline" Tailwind v4 configuration, useState QueryClient for stable instances, financial semantic color tokens]

key-files:
  created:
    - dashboard/components.json
    - dashboard/src/app/providers.tsx
    - dashboard/src/components/ui/card.tsx
    - dashboard/src/components/ui/table.tsx
    - dashboard/src/components/ui/badge.tsx
    - dashboard/src/components/ui/separator.tsx
    - dashboard/src/components/ui/skeleton.tsx
    - dashboard/src/lib/utils.ts
    - dashboard/src/types/api.ts
    - dashboard/src/lib/formatters.ts
    - dashboard/src/hooks/use-overview.ts
  modified:
    - dashboard/package.json
    - dashboard/biome.json
    - dashboard/src/app/globals.css
    - dashboard/src/app/layout.tsx
    - dashboard/src/app/(dashboard)/layout.tsx

key-decisions:
  - "Biome 2.4.7 requires css.parser.tailwindDirectives: true for Tailwind v4 @custom-variant, @theme, @apply syntax"
  - "shadcn/ui base-nova style ships double-quote components -- auto-formatted to project single-quote convention via biome check --write"
  - "Keep shadcn radius calculations (0.6/0.8/1.0/1.4x multipliers) instead of plan's additive approach (radius +/- 0.125rem)"

patterns-established:
  - "Bloomberg dark theme: oklch(0.08) background, oklch(0.12) card, oklch(0.78 0.15 75) amber primary"
  - "Financial semantic tokens: --profit (cyan), --loss (red), --neutral (white), --interactive (amber) mapped to Tailwind via @theme inline"
  - "Providers pattern: single 'use client' wrapper with QueryClient + ThemeProvider, mounted in Server Component layout"
  - "font-mono class resolves to JetBrains Mono via --font-jetbrains-mono CSS variable"
  - "Intl.NumberFormat-based formatters with NaN/Infinity guards"

requirements-completed: [DSGN-01, DSGN-02, DSGN-03, DSGN-04]

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 22 Plan 01: Design System Foundation Summary

**Bloomberg OKLCH dark theme with shadcn/ui components, JetBrains Mono font, financial semantic tokens, TanStack Query provider, and typed API data layer**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T10:26:10Z
- **Completed:** 2026-03-14T10:30:15Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- shadcn/ui initialized with 6 vendored components (Card, Table, Badge, Separator, Skeleton, Button)
- Bloomberg dark theme via OKLCH color tokens with financial semantic colors (profit=cyan, loss=red, neutral=white, interactive=amber)
- JetBrains Mono monospace font loaded via next/font/google for number alignment
- QueryClientProvider + ThemeProvider wrapping the app through providers.tsx
- TypeScript interfaces matching FastAPI OverviewQueryHandler.handle() response shape exactly
- Number formatting utilities using Intl.NumberFormat with non-finite value guards
- useOverview TanStack Query hook ready for Overview page components

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies, init shadcn/ui, and create design system infrastructure** - `41f0694` (feat)
2. **Task 2: Create TypeScript API types, formatting utilities, and overview data hook** - `e9ee0de` (feat)

## Files Created/Modified
- `dashboard/components.json` - shadcn/ui configuration (base-nova style, neutral base color)
- `dashboard/src/app/globals.css` - Bloomberg OKLCH dark theme tokens + financial semantic tokens + tabular-nums utility
- `dashboard/src/app/layout.tsx` - Inter + JetBrains Mono fonts, dark class, Providers wrapper
- `dashboard/src/app/providers.tsx` - QueryClientProvider + ThemeProvider (use client)
- `dashboard/src/app/(dashboard)/layout.tsx` - Theme token classes replacing hardcoded colors
- `dashboard/src/components/ui/card.tsx` - shadcn Card component (vendored)
- `dashboard/src/components/ui/table.tsx` - shadcn Table component (vendored)
- `dashboard/src/components/ui/badge.tsx` - shadcn Badge component (vendored)
- `dashboard/src/components/ui/separator.tsx` - shadcn Separator component (vendored)
- `dashboard/src/components/ui/skeleton.tsx` - shadcn Skeleton component (vendored)
- `dashboard/src/lib/utils.ts` - cn() utility (clsx + tailwind-merge)
- `dashboard/src/types/api.ts` - OverviewData, Position, TradeHistoryItem, EquityCurve, RegimePeriod, LastPipeline
- `dashboard/src/lib/formatters.ts` - formatCurrency, formatPercent, formatScore, formatDate
- `dashboard/src/hooks/use-overview.ts` - useOverview TanStack Query hook
- `dashboard/biome.json` - Added CSS tailwindDirectives parser + components.json to includes
- `dashboard/package.json` - Added shadcn/ui, TanStack Query, next-themes, lightweight-charts dependencies

## Decisions Made
- **Biome CSS parser config:** Biome 2.4.7 requires `css.parser.tailwindDirectives: true` to parse Tailwind v4 `@custom-variant`, `@theme inline`, and `@apply` directives without errors. Added to biome.json.
- **shadcn formatting:** shadcn/ui base-nova style generates components with double quotes and no semicolons. Auto-formatted to project convention (single quotes, semicolons) via `biome check --write`.
- **Radius calculations:** Kept shadcn's generated radius multiplier approach (`calc(var(--radius) * 0.6)`) instead of research's additive approach (`calc(var(--radius) - 0.125rem)`) since shadcn components expect this convention.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Biome CSS tailwindDirectives parser option**
- **Found during:** Task 1 (Biome check after shadcn init)
- **Issue:** Biome 2.4.7 could not parse Tailwind v4 directives (`@custom-variant`, `@theme inline`, `@apply`) generated by shadcn/ui init. 12 CSS parse errors.
- **Fix:** Added `css.parser.tailwindDirectives: true` to biome.json
- **Files modified:** dashboard/biome.json
- **Verification:** `npx biome check .` passes with 0 errors
- **Committed in:** 41f0694 (Task 1 commit)

**2. [Rule 3 - Blocking] shadcn component formatting mismatch**
- **Found during:** Task 1 (Biome check after adding components)
- **Issue:** shadcn/ui generates components with double quotes and no semicolons, conflicting with project's single-quote + semicolons Biome config
- **Fix:** Ran `npx biome check --write .` to auto-format all vendored components
- **Files modified:** 6 component files + utils.ts
- **Verification:** `npx biome check .` passes with 0 errors
- **Committed in:** 41f0694 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes were necessary for Biome tooling compatibility. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Design system foundation complete, ready for Phase 22 Plan 02 (Overview page components)
- shadcn Card, Table, Badge, Separator, Skeleton available for KPI cards, holdings table, trade history
- Theme tokens and semantic colors ready for profit/loss color coding
- useOverview hook ready for data fetching
- formatCurrency, formatPercent, formatScore, formatDate ready for number display
- Full build passes (tsc + biome + next build)

---
*Phase: 22-design-system-overview-page*
*Completed: 2026-03-14*
