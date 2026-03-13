---
phase: 13-automated-pipeline-scheduler
plan: 02
subsystem: pipeline
tags: [pipeline, orchestrator, apscheduler, cli, retry, halt, ddd]

requires:
  - phase: 13-automated-pipeline-scheduler
    plan: 01
    provides: PipelineRun entity, StageResult VOs, SqlitePipelineRunRepository, MarketCalendarService, Notifiers

provides:
  - PipelineOrchestrator domain service with 6-stage sequential execution
  - RunPipelineHandler with reconciliation pre-check
  - PipelineStatusHandler for run history queries
  - SchedulerService wrapping APScheduler with SQLite job persistence
  - CLI trade pipeline run/status subcommands
  - Bootstrap wiring for all pipeline components

affects: [14-strategy-approval, 15-live-trading, 16-web-dashboard]

tech-stack:
  added: [apscheduler-3.11, sqlalchemy-2.0]
  patterns: [module-level-job-registration, retry-exponential-backoff, halt-gate-pattern, typer-subcommand-group]

key-files:
  created:
    - src/pipeline/domain/services.py
    - src/pipeline/application/commands.py
    - src/pipeline/application/handlers.py
    - src/pipeline/application/__init__.py
    - src/pipeline/infrastructure/scheduler_service.py
    - tests/unit/test_pipeline_orchestrator.py
    - tests/unit/test_scheduler_service.py
  modified:
    - src/pipeline/domain/__init__.py
    - src/pipeline/infrastructure/__init__.py
    - src/bootstrap.py
    - cli/main.py

key-decisions:
  - "Module-level function registration for APScheduler job targets (avoids serialization of scheduler instance)"
  - "Orchestrator receives handlers dict via run() params -- no cross-context imports"
  - "Reconciliation check is application layer responsibility (RunPipelineHandler), not domain"
  - "Drawdown halt maps tier>=2 to WARNING/CRITICAL enum string values"

patterns-established:
  - "PipelineOrchestrator as pure domain service with retry/halt"
  - "Typer subcommand group for CLI pipeline commands"
  - "Module-level global registration for APScheduler-compatible job functions"

requirements-completed: [PIPE-01, PIPE-04, PIPE-05, PIPE-06]

duration: 8min
completed: 2026-03-13
---

# Phase 13 Plan 02: Pipeline Orchestrator Summary

**PipelineOrchestrator chains 6 stages with retry/halt logic, APScheduler daily schedule via SchedulerService, and CLI trade pipeline run/status commands**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-13T07:03:08Z
- **Completed:** 2026-03-13T07:11:30Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- PipelineOrchestrator domain service executing 6 stages sequentially (ingest->regime->score->signal->plan->execute) with 3x exponential backoff retry and halt gate
- RunPipelineHandler performs reconciliation check before invoking orchestrator (DDD-compliant application layer)
- SchedulerService wrapping APScheduler BackgroundScheduler with SQLite job persistence and market calendar guard
- CLI subcommands: `trade pipeline run [--dry-run]` with Rich stage table, `trade pipeline status` with run history
- Bootstrap wiring: DataPipeline, pipeline repos, orchestrator, reconciliation, handlers fully connected
- 23 tests passing across orchestrator (15) and scheduler (8) test files

## Task Commits

Each task was committed atomically:

1. **Task 1: PipelineOrchestrator with retry, halt, and application handlers** - `8914264` (feat)
2. **Task 2: SchedulerService, bootstrap wiring, CLI pipeline commands** - `3805a35` (feat)

## Files Created/Modified

- `src/pipeline/domain/services.py` - PipelineOrchestrator with 6 stages, retry, halt logic
- `src/pipeline/domain/__init__.py` - Added PipelineOrchestrator export
- `src/pipeline/application/commands.py` - RunPipelineCommand, GetPipelineStatusQuery
- `src/pipeline/application/handlers.py` - RunPipelineHandler (reconciliation + orchestrator), PipelineStatusHandler
- `src/pipeline/application/__init__.py` - Application public API exports
- `src/pipeline/infrastructure/scheduler_service.py` - APScheduler wrapper with SQLite persistence and calendar guard
- `src/pipeline/infrastructure/__init__.py` - Added SchedulerService export
- `src/bootstrap.py` - Wired pipeline repos, DataPipeline, orchestrator, reconciliation, handlers
- `cli/main.py` - Added pipeline_app Typer subcommand group with run and status commands
- `tests/unit/test_pipeline_orchestrator.py` - 15 tests for orchestrator and application handlers
- `tests/unit/test_scheduler_service.py` - 8 tests for scheduler service

## Decisions Made

- **Module-level function registration** for APScheduler -- APScheduler's SQLAlchemy job store serializes job targets; instance methods referencing the scheduler cannot be serialized, so we register the pipeline function at module level
- **Reconciliation in application layer** -- PipelineOrchestrator (domain) stays pure; RunPipelineHandler (application) calls reconciliation_service.check_and_halt() before invoking orchestrator
- **Drawdown halt mapping** -- "tier >= 2" from strategy docs maps to DrawdownLevel.WARNING and DrawdownLevel.CRITICAL string values
- **DataPipeline added to bootstrap context** -- orchestrator's ingest stage calls handlers["data_pipeline"].ingest_universe() via asyncio.run()

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed APScheduler and SQLAlchemy packages**
- **Found during:** Task 2 (SchedulerService implementation)
- **Issue:** APScheduler and SQLAlchemy not installed in environment
- **Fix:** pip install "APScheduler>=3.11,<4" and "sqlalchemy>=2.0"
- **Files modified:** None (system packages)
- **Verification:** import apscheduler succeeds, all scheduler tests pass

**2. [Rule 1 - Bug] Refactored SchedulerService to use module-level job function**
- **Found during:** Task 2 (test_scheduler_creates_job failing)
- **Issue:** APScheduler cannot serialize instance methods that reference scheduler
- **Fix:** Created module-level _scheduled_pipeline_run() and global registry pattern
- **Files modified:** src/pipeline/infrastructure/scheduler_service.py
- **Commit:** included in 3805a35

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Package installation and serialization pattern change required for correct operation. No scope creep.

## Verification Results

```
- typecheck: PASS (0 new errors; pre-existing errors in scoring/signals/core unchanged)
- test: PASS (23/23 pipeline tests; 77/78 full suite -- 1 pre-existing API version assertion failure)
- lint: PASS (0 errors after f-string fix)
```

## Next Phase Readiness

- Full pipeline orchestration chain ready for Phase 14 (Strategy and Budget Approval)
- SchedulerService ready for FastAPI lifespan integration in Phase 16
- CLI pipeline commands provide manual execution and monitoring capability
- Reconciliation pre-check ensures position consistency before automated trading

---
*Phase: 13-automated-pipeline-scheduler*
*Completed: 2026-03-13*
