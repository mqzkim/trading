---
phase: 01-data-foundation
plan: 03
subsystem: scoring, data-ingestion
tags: [adapter-pattern, altman-z-score, beneish-m-score, piotroski-f-score, safety-gate, duckdb, asyncio, pipeline, data-quality]

requires:
  - phase: 01-01
    provides: "Domain VOs, DuckDB store, async event bus"
  - phase: 01-02
    provides: "YFinanceClient, EdgartoolsClient, UniverseProvider, QualityChecker"
provides:
  - "CoreScoringAdapter: DDD adapter wrapping core scoring functions (Z/M/F-Score)"
  - "DataPipeline: end-to-end async ingestion pipeline (fetch -> validate -> store -> event)"
affects: [scoring, signals, regime, backtest]

tech-stack:
  added: []
  patterns: [adapter-pattern-for-core-wrapping, dependency-injection-pipeline, ohlcv-format-conversion]

key-files:
  created:
    - src/scoring/infrastructure/core_scoring_adapter.py
    - src/data_ingest/infrastructure/pipeline.py
    - tests/unit/test_core_scoring_adapter.py
    - tests/integration/test_data_ingest.py
  modified:
    - src/scoring/infrastructure/__init__.py
    - src/data_ingest/infrastructure/__init__.py

key-decisions:
  - "CoreScoringAdapter delegates to core functions without rewriting math -- adapter pattern only"
  - "DataPipeline converts DatetimeIndex OHLCV to flat DataFrame before DuckDB storage"
  - "Pipeline uses dependency injection for all clients enabling easy test mocking"

patterns-established:
  - "Adapter Pattern: infrastructure adapters wrap core/ functions for DDD compliance"
  - "DataFrame format conversion: pipeline handles YFinance -> DuckDB schema transformation"
  - "Integration tests use DuckDB :memory: + AsyncMock clients (no network I/O)"

requirements-completed: [SCOR-01, SCOR-02, SCOR-03, SCOR-04]

duration: 6min
completed: 2026-03-12
---

# Phase 1 Plan 3: Core Scoring Adapter + Data Ingestion Pipeline Summary

**CoreScoringAdapter wrapping Altman Z/Beneish M/Piotroski F-Score with SafetyGate VO, and DataPipeline orchestrating fetch-validate-store-event with 19 tests passing**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-11T23:35:22Z
- **Completed:** 2026-03-11T23:41:31Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- CoreScoringAdapter wraps all core scoring functions (Z-Score, M-Score, F-Score, SafetyGate) via adapter pattern
- DataPipeline orchestrates full ingestion flow: fetch OHLCV/financials -> quality check -> DuckDB store -> domain event publish
- Safety gate correctly filters: Z > 1.81 AND M < -1.78 (boundary tests pass)
- Pipeline handles DataFrame format conversion from YFinance DatetimeIndex to DuckDB flat schema

## Task Commits

Each task was committed atomically:

1. **Task 1: CoreScoringAdapter (TDD)**
   - `8442552` (test: failing tests for CoreScoringAdapter)
   - `e393b3d` (feat: implement CoreScoringAdapter wrapping core scoring)
2. **Task 2: DataPipeline + integration tests**
   - `75d1c51` (feat: implement DataPipeline with end-to-end ingestion)

_Task 1 used TDD: RED (failing tests) -> GREEN (implementation)_

## Files Created/Modified
- `src/scoring/infrastructure/core_scoring_adapter.py` - DDD adapter wrapping core scoring functions
- `src/data_ingest/infrastructure/pipeline.py` - End-to-end async data ingestion pipeline
- `tests/unit/test_core_scoring_adapter.py` - 15 reference-value tests for scoring adapter
- `tests/integration/test_data_ingest.py` - 4 pipeline integration tests
- `src/scoring/infrastructure/__init__.py` - Added CoreScoringAdapter export
- `src/data_ingest/infrastructure/__init__.py` - Added all infrastructure exports

## Decisions Made
- CoreScoringAdapter delegates to core functions without rewriting math -- validates both adapter and core in tests
- DataPipeline converts DatetimeIndex OHLCV (from YFinanceClient) to flat DataFrame for DuckDB storage
- Pipeline uses constructor dependency injection for all clients, enabling test mocking without monkeypatch

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed OHLCV DataFrame format mismatch between YFinance and DuckDB**
- **Found during:** Task 2 (integration test failure)
- **Issue:** YFinanceClient returns DataFrame with DatetimeIndex (no ticker column, date as index), but DuckDB `store_ohlcv` expects flat DataFrame with 7 columns (ticker, date, open, high, low, close, volume)
- **Fix:** Added `_prepare_ohlcv_for_storage()` method in DataPipeline to reset index, add ticker column, normalize column names
- **Files modified:** src/data_ingest/infrastructure/pipeline.py
- **Verification:** All 4 integration tests pass
- **Committed in:** 75d1c51 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correct pipeline flow. No scope creep.

## Issues Encountered
- Pre-existing mypy dual module name issue (src.X vs X) -- out of scope, noted in Plan 01-02 summary
- Pre-existing types-requests stub missing in core/data/client.py -- out of scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 Data Foundation is complete: all 3 plans executed
- Domain VOs, stores, event bus, data clients, quality checker, scoring adapter, and pipeline all integrated
- Ready for Phase 2: Scoring/Valuation (regime detection, signal generation)
- CoreScoringAdapter provides the scoring interface for downstream phases
- DataPipeline is the user entry point for data ingestion

## Self-Check: PASSED

- All 6 created/modified files: FOUND
- All 3 commits (8442552, e393b3d, 75d1c51): FOUND
- Tests: 262 unit + 4 integration = 266 passed
- Ruff: 0 errors
- Mypy: 0 errors in plan files (pre-existing dual-module and types-requests issues in core/)

---
*Phase: 01-data-foundation*
*Completed: 2026-03-12*
