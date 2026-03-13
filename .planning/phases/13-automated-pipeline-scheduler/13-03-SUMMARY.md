---
phase: 13-automated-pipeline-scheduler
plan: 03
subsystem: pipeline
tags: [pipeline, orchestrator, scheduler, apscheduler, trade-plan, execution]

requires:
  - phase: 13-01
    provides: PipelineRun entity, StageResult, MarketCalendarService, SqlitePipelineRunRepository
  - phase: 13-02
    provides: PipelineOrchestrator, SchedulerService, RunPipelineHandler, CLI pipeline commands
provides:
  - Fully wired _run_plan stage generating TradePlan objects from signal results via DataClient
  - Fully wired _run_execute stage submitting orders via trade_plan_handler approve+execute
  - SchedulerService instantiated in bootstrap as ctx["scheduler_service"]
  - CLI daemon command for background pipeline scheduling
affects: [phase-14-strategy-approval, phase-15-live-trading]

tech-stack:
  added: []
  patterns: [inline-import-for-cross-context, per-symbol-failure-resilience]

key-files:
  created: []
  modified:
    - src/pipeline/domain/services.py
    - src/bootstrap.py
    - cli/main.py
    - tests/unit/test_pipeline_orchestrator.py

key-decisions:
  - "DataClient import inline in _run_plan (matches existing pattern for cross-context imports in orchestrator)"
  - "Auto-approve trade plans in _run_execute (pipeline automation path -- manual approval via Phase 14)"
  - "Bootstrap creates SchedulerService but does NOT auto-start (caller responsibility)"

patterns-established:
  - "Per-symbol failure resilience: plan/execute stages log and skip failures, never abort"

requirements-completed: [PIPE-01, PIPE-04, PIPE-07]

duration: 5min
completed: 2026-03-13
---

# Phase 13 Plan 03: Gap Closure Summary

**Wired _run_plan with DataClient+TradePlanHandler.generate(), _run_execute with approve+execute, and SchedulerService in bootstrap with CLI daemon**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-13T07:31:56Z
- **Completed:** 2026-03-13T07:37:18Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- _run_plan now fetches market data via DataClient and generates TradePlan objects through trade_plan_handler.generate()
- _run_execute auto-approves and submits orders through trade_plan_handler for each generated plan
- SchedulerService wired in bootstrap with db_path, run_pipeline_fn, calendar, and schedule settings
- CLI `trade pipeline daemon` starts APScheduler as foreground process with Ctrl+C shutdown
- All 3 verification gaps from 13-VERIFICATION.md are closed

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement _run_plan and _run_execute (TDD)** - `1ba979c` (test: RED), `64d494d` (feat: GREEN)
2. **Task 2: Wire SchedulerService in bootstrap and add daemon command** - `3494a76` (feat)

_Note: Task 1 used TDD with RED/GREEN commits_

## Files Created/Modified
- `src/pipeline/domain/services.py` - Replaced _run_plan and _run_execute stubs with real implementations
- `src/bootstrap.py` - Added SchedulerService instantiation and ctx["scheduler_service"]
- `cli/main.py` - Added `trade pipeline daemon` command
- `tests/unit/test_pipeline_orchestrator.py` - 7 new tests for plan/execute stages

## Decisions Made
- DataClient imported inline in _run_plan (matches existing pattern for DetectRegimeCommand, ScoreSymbolCommand imports in the same file)
- Auto-approve trade plans in _run_execute -- full manual approval workflow deferred to Phase 14
- Bootstrap creates SchedulerService but does NOT auto-start it -- starting is the caller's responsibility (CLI daemon or FastAPI lifespan)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full pipeline chain (ingest -> regime -> score -> signal -> plan -> execute) is now functional
- SchedulerService can be started via CLI daemon for daily automated runs
- Phase 14 (Strategy and Budget Approval) can gate the auto-approve step in _run_execute
- Pre-existing test_api_routes health endpoint failure is unrelated to this plan

---
*Phase: 13-automated-pipeline-scheduler*
*Completed: 2026-03-13*
