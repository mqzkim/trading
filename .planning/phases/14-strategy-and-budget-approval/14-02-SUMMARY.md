---
phase: 14-strategy-and-budget-approval
plan: 02
subsystem: execution
tags: [approval-gate, pipeline, cli, budget-tracking, regime-suspension, typer, rich]

requires:
  - phase: 14-01
    provides: "Approval domain layer (entity, VOs, gate service, SQLite repos)"
provides:
  - "ApprovalHandler application layer (CRUD, regime/drawdown suspension)"
  - "Pipeline _run_execute with approval gate check (approved/rejected/queued)"
  - "Bootstrap wiring for approval context + RegimeChangedEvent subscription"
  - "CLI commands: approval create/status/revoke/resume, review list/approve/reject"
affects: [15-paper-automated-trading, 16-live-preparation]

tech-stack:
  added: []
  patterns: ["handlers dict injection for DDD cross-context access", "RegimeChangedEvent-driven suspension"]

key-files:
  created:
    - src/approval/application/__init__.py
    - src/approval/application/commands.py
    - src/approval/application/handlers.py
    - tests/unit/test_approval_integration.py
    - tests/unit/test_cli_approval.py
  modified:
    - src/pipeline/domain/services.py
    - src/bootstrap.py
    - cli/main.py
    - tests/unit/test_pipeline_orchestrator.py

key-decisions:
  - "Approval subgroup named 'approval' (not 'approve') to avoid conflict with existing trade plan approve command"
  - "RegimeChangedEvent handler normalizes RegimeType enum via .value for string comparison"
  - "Pipeline _run_execute backward compatible: no approval_gate key = skip execution with log"

patterns-established:
  - "Approval gate check pattern: handlers dict passes gate + repos without domain cross-import"
  - "Budget tracking sequential per-trade: record_spend + save after each approved trade"

requirements-completed: [APPR-03, APPR-04, APPR-05]

duration: 9min
completed: 2026-03-13
---

# Phase 14 Plan 02: Pipeline Gate Integration and CLI Summary

**Approval gate wired into pipeline execute stage with regime/drawdown auto-suspension, budget tracking, CLI commands for approval CRUD and trade review queue**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-13T12:53:54Z
- **Completed:** 2026-03-13T13:03:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Pipeline _run_execute gates on approval: approved trades execute, rejected trades queue for manual review
- RegimeChangedEvent auto-suspends approval when regime leaves allow-list; auto-removes when it returns
- Budget 80% warning and 24h expiration warning in pipeline execute stage
- CLI: approval create/status/revoke/resume and review list/approve/reject with Rich output
- All 1020 tests pass (77 approval + 8 CLI approval + 935 existing)

## Task Commits

Each task was committed atomically:

1. **Task 1: Application layer handlers and pipeline gate integration** - `0d32eb8` (feat)
2. **Task 2: CLI commands for approval CRUD and trade review** - `b6855a1` (feat)

## Files Created/Modified
- `src/approval/application/__init__.py` - Public API for approval application layer
- `src/approval/application/commands.py` - Command dataclasses (CreateApproval, Revoke, Resume, ReviewTrade)
- `src/approval/application/handlers.py` - ApprovalHandler with CRUD + regime/drawdown suspension
- `src/pipeline/domain/services.py` - _run_execute with approval gate, budget tracking, review queue
- `src/bootstrap.py` - Approval context wiring + RegimeChangedEvent subscription
- `cli/main.py` - approval and review CLI subcommands
- `tests/unit/test_approval_integration.py` - 18 integration tests
- `tests/unit/test_cli_approval.py` - 8 CLI tests
- `tests/unit/test_pipeline_orchestrator.py` - Updated mock handlers with approval gate

## Decisions Made
- Named CLI subgroup "approval" instead of "approve" to avoid conflict with existing trade plan approve command
- RegimeChangedEvent handler normalizes RegimeType enum via .value attribute for string comparison against allowed_regimes list
- Pipeline _run_execute is backward compatible: missing approval_gate key returns "skipped" StageResult

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pipeline orchestrator test regression**
- **Found during:** Task 2 (CLI commands)
- **Issue:** Existing pipeline tests failed because _run_execute now requires approval_gate in handlers dict
- **Fix:** Updated _make_handlers() in test_pipeline_orchestrator.py to include approval gate components
- **Files modified:** tests/unit/test_pipeline_orchestrator.py
- **Verification:** All 22 pipeline orchestrator tests pass
- **Committed in:** b6855a1 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed CLI naming conflict**
- **Found during:** Task 2 (CLI commands)
- **Issue:** Adding typer subgroup named "approve" conflicted with existing `approve` command for trade plan approval
- **Fix:** Renamed new subgroup to "approval" (approval create, approval status, etc.)
- **Files modified:** cli/main.py, tests/unit/test_cli_approval.py
- **Verification:** Both old approve command and new approval subgroup work correctly
- **Committed in:** b6855a1 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_api_routes.py (unrelated to this plan) -- not in scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 14 complete: approval domain + application + pipeline integration + CLI
- Ready for Phase 15 (paper automated trading) -- approval gate is the safety mechanism
- Drawdown tier 2+ auto-suspends approval; manual resume required (safety by design)

---
*Phase: 14-strategy-and-budget-approval*
*Completed: 2026-03-13*
