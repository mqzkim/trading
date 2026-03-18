---
phase: 29
plan: 02
subsystem: self-improver, dashboard
tags: [ddd, self-improvement, proposals, dashboard, performance]
dependency_graph:
  requires:
    - 29-01  # performance DDD context, DuckDBProposalRepository, attribution endpoint
  provides:
    - DDD self-improver with proposal generation and walk-forward validation
    - Dashboard performance page with Brinson-Fachler table, per-axis IC, Parameter Proposals
    - BFF proxy routes for performance attribution and proposal approval
  affects:
    - personal/self_improver/ (full DDD restructure)
    - dashboard/src/app/(dashboard)/performance/page.tsx
    - dashboard/src/hooks/use-performance.ts
    - dashboard/src/types/api.ts
tech_stack:
  added: []
  patterns:
    - DDD domain/application/infrastructure in personal/ bounded context
    - WalkForwardAdapter wrapping core/backtest/walk_forward.py
    - BFF proxy API routes (Next.js) forwarding to FastAPI
    - React Query useMutation for approve/reject proposal flow
key_files:
  created:
    - personal/self_improver/domain/services.py
    - personal/self_improver/domain/value_objects.py
    - personal/self_improver/domain/__init__.py
    - personal/self_improver/application/handlers.py
    - personal/self_improver/application/__init__.py
    - personal/self_improver/infrastructure/walk_forward_adapter.py
    - personal/self_improver/infrastructure/__init__.py
    - tests/unit/test_self_improver_proposal.py
    - tests/unit/test_proposal_approval.py
    - dashboard/src/app/api/v1/dashboard/performance/route.ts
    - dashboard/src/app/api/v1/dashboard/performance/proposals/[id]/approve/route.ts
    - dashboard/src/app/api/v1/dashboard/performance/proposals/[id]/reject/route.ts
  modified:
    - dashboard/src/types/api.ts
    - dashboard/src/hooks/use-performance.ts
    - dashboard/src/app/(dashboard)/performance/page.tsx
    - .planning/phases/29-performance-self-improvement/29-VALIDATION.md
decisions:
  - WalkForwardAdapter converts flat trade_returns list into synthetic OHLCV DataFrame to satisfy run_walk_forward() signature
  - ImprovementAdvisorService only proposes scoring axis weights (fundamental/technical/sentiment); never risk params (ATR, Kelly)
  - GenerateProposalHandler.MINIMUM_TRADES = 50 guard returns [] immediately, no WF run
  - Parameter Proposals section conditionally rendered when tradeCount >= 50 (client-side guard)
  - Pre-existing advisor.py lint warning (F401 unused import) is out-of-scope; new DDD files are clean
metrics:
  duration_seconds: 186
  completed_date: "2026-03-17"
  tasks_completed: 3
  files_modified: 15
requirements_satisfied:
  - SELF-01
  - SELF-02
  - SELF-03
  - SELF-04
---

# Phase 29 Plan 02: Self-Improver DDD Refactor + Dashboard Performance Completion Summary

**One-liner:** DDD self-improver with walk-forward proposal generation (MINIMUM_TRADES=50 guard) and fully wired Performance dashboard (Brinson-Fachler table, per-axis IC/Kelly badges, Parameter Proposals with Approve/Reject).

## What Was Built

### Task 1 + 2: DDD Self-Improver Refactor (already in place, tests written and passing)

The `personal/self_improver/` bounded context was structured with full DDD layers:

- **`domain/value_objects.py`** — `WeightProposal` frozen dataclass (id, regime, axis, current_weight, proposed_weight, walk_forward_sharpe, status)
- **`domain/services.py`** — `ImprovementAdvisorService.suggest()` generates proposals based on OOS Sharpe:
  - Sharpe < 0.5 → equalize all 3 axes to 1/3 each
  - 0.5 ≤ Sharpe < 1.0 → shift 5% from weakest to strongest axis
  - Sharpe ≥ 1.0 AND overfitting ≤ 1.0 → no proposals
  - Overfitting > 1.0 → reduce fundamental weight by 5%
- **`infrastructure/walk_forward_adapter.py`** — `WalkForwardAdapter.run(trade_returns)` builds synthetic OHLCV from cumulative returns, calls `run_walk_forward()`
- **`application/handlers.py`** — `GenerateProposalHandler` with `MINIMUM_TRADES = 50` guard, orchestrates WF → advisor → save proposals as "pending"

### Task 3: Dashboard Performance Page

**TypeScript types** (`dashboard/src/types/api.ts`):
- Added `BrinsonFachlerRow`, `ProposalItem`, `ApprovalHistoryItem` interfaces
- Extended `PerformanceData` with `signal_ic_per_axis`, `proposals`, `approval_history`

**Hook** (`use-performance.ts`):
- Added `approveProposal` and `rejectProposal` `useMutation` calls via `useQueryClient` invalidation

**BFF routes** (3 new Next.js API routes):
- `GET /api/v1/dashboard/performance` → proxies to FastAPI `/api/v1/performance/attribution`
- `PUT .../proposals/[id]/approve` → proxies to FastAPI approve endpoint
- `PUT .../proposals/[id]/reject` → proxies to FastAPI reject endpoint

**Performance page** (full rewrite):
1. KPI Cards (Sharpe, Sortino, Win Rate, Max Drawdown)
2. Brinson-Fachler Attribution table with real data (empty state if no trades)
3. Equity Curve placeholder
4. Strategy Scorecard — Fundamental/Technical/Sentiment IC vs 0.03 threshold (green/red), Kelly Efficiency vs 70% (green/yellow/red)
5. Parameter Proposals section — **hidden when tradeCount < 50**, shows pending proposals with Approve/Reject buttons, Approval History table (last 5)

## Verification Results

```
pytest (26/26 passed):
  tests/unit/test_performance_trade_repo.py     5 passed
  tests/unit/test_brinson_fachler.py            3 passed
  tests/unit/test_ic_calculation.py             3 passed
  tests/unit/test_kelly_efficiency.py           2 passed
  tests/unit/test_position_score_snapshot.py    2 passed
  tests/unit/test_self_improver_proposal.py     5 passed
  tests/unit/test_proposal_approval.py          6 passed

mypy personal/self_improver/ --ignore-missing-imports: 0 errors
ruff check personal/self_improver/domain/ application/ infrastructure/: All checks passed
tsc --noEmit (dashboard): 0 errors
```

## Deviations from Plan

### Out-of-Scope Lint Warning (not fixed)

`personal/self_improver/advisor.py` has a pre-existing `F401` lint warning (`PerformanceMetrics` imported but unused). This file was not modified in this plan and is kept for reference per the plan spec ("advisor.py is NOT deleted"). Deferred to separate cleanup.

## Self-Check: PASSED

- `personal/self_improver/domain/services.py` — FOUND
- `personal/self_improver/application/handlers.py` — FOUND
- `personal/self_improver/infrastructure/walk_forward_adapter.py` — FOUND
- `dashboard/src/app/api/v1/dashboard/performance/route.ts` — FOUND
- `dashboard/src/app/(dashboard)/performance/page.tsx` — FOUND (contains "Parameter Proposals", tradeCount >= 50)
- All 26 unit tests — PASSED
- commit `0a72ead` — FOUND
