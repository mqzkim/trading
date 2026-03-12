---
phase: 06-live-data-pipeline-korean-data
plan: 01
subsystem: data-ingest
tags: [edgartools, yfinance, korean-market, value-objects, quality-checker, xbrl]

# Dependency graph
requires:
  - phase: 05-tech-debt-infrastructure-foundation
    provides: DDD architecture, event bus, CLI bootstrap
provides:
  - Fixed edgartools ticker field (was storing filing_date as ticker)
  - MarketType enum (US/KR) in data_ingest domain
  - Ticker VO accepting Korean 6-digit numeric tickers
  - Symbol VO accepting Korean numeric tickers
  - Business-day-aware QualityChecker staleness (configurable threshold)
  - Validated yfinance auto_adjust=True returns adjusted OHLCV (DATA-01)
  - Validated edgartools small-cap XBRL graceful handling (DATA-02)
affects: [06-02 pykrx adapter, 06-03 regime data, scoring pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [business-day staleness via numpy.busday_count, MarketType enum for multi-market support]

key-files:
  created: []
  modified:
    - src/data_ingest/infrastructure/edgartools_client.py
    - src/data_ingest/domain/value_objects.py
    - src/data_ingest/domain/__init__.py
    - src/scoring/domain/value_objects.py
    - src/data_ingest/infrastructure/quality_checker.py
    - tests/unit/test_edgartools_client.py
    - tests/unit/test_data_ingest_vos.py
    - tests/unit/test_quality_checker.py
    - tests/unit/test_yfinance_adapter.py

key-decisions:
  - "Ticker regex changed from [A-Z]{1,10} to [A-Z0-9]{1,10} to accept Korean numeric tickers alongside US alpha tickers"
  - "QualityChecker staleness now uses numpy.busday_count for business-day counting, with optional now parameter for testability"
  - "Symbol VO validation uses isupper() or isdigit() to accept both US and Korean formats"

patterns-established:
  - "MarketType enum pattern: US='us', KR='kr' for multi-market dispatching"
  - "Business-day-aware staleness: configurable max_stale_days for market-specific thresholds (US=3, KR=5)"
  - "Injectable now parameter in QualityChecker for deterministic testing"

requirements-completed: [DATA-01, DATA-02, DATA-03]

# Metrics
duration: 6min
completed: 2026-03-12
---

# Phase 6 Plan 01: US Pipeline Bug Fixes & Multi-Market VO Hardening Summary

**Fixed edgartools ticker corruption bug, extended Ticker/Symbol VOs for Korean 6-digit tickers, business-day-aware staleness checking, validated yfinance adjusted OHLCV and edgartools small-cap XBRL coverage**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-12T06:00:09Z
- **Completed:** 2026-03-12T06:06:44Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Fixed critical ticker corruption bug in edgartools_client.py (line 154 stored filing_date as ticker string)
- Extended Ticker VO and Symbol VO to accept Korean 6-digit numeric tickers (e.g., "005930")
- Added MarketType enum (US/KR) to data_ingest domain for multi-market dispatch
- QualityChecker now uses business-day counting (Friday-to-Monday gap no longer triggers false positives)
- Validated yfinance auto_adjust=True returns {open, high, low, close, volume} with no Adj Close (DATA-01)
- Validated edgartools handles small-cap sparse/missing XBRL gracefully (DATA-02)

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1 RED: Failing tests for ticker bug, Korean VOs, small-cap XBRL** - `bd9042d` (test)
2. **Task 1 GREEN: Fix edgartools ticker, extend VOs, validate small-cap** - `bda3cef` (feat)
3. **Task 2 RED: Failing tests for business-day staleness** - `3ccc1a4` (test)
4. **Task 2 GREEN: Business-day-aware QualityChecker** - `69268a7` (feat)
5. **Task 3: Validate yfinance auto_adjust=True (DATA-01)** - `9d9a09f` (test)

## Files Created/Modified
- `src/data_ingest/infrastructure/edgartools_client.py` - Fixed ticker field bug, added ticker parameter to _extract_filing
- `src/data_ingest/domain/value_objects.py` - Extended Ticker regex for Korean tickers, added MarketType enum
- `src/data_ingest/domain/__init__.py` - Exported MarketType from domain public API
- `src/scoring/domain/value_objects.py` - Symbol VO accepts digits-only tickers via isdigit() check
- `src/data_ingest/infrastructure/quality_checker.py` - Business-day-aware staleness via numpy.busday_count
- `tests/unit/test_edgartools_client.py` - Ticker fix tests, small-cap XBRL coverage tests
- `tests/unit/test_data_ingest_vos.py` - Korean Ticker tests, MarketType tests, Symbol Korean tests
- `tests/unit/test_quality_checker.py` - Business-day staleness tests (weekend gap, custom threshold)
- `tests/unit/test_yfinance_adapter.py` - auto_adjust=True validation tests (no Adj Close, lowercase columns)

## Decisions Made
- Ticker regex changed from `[A-Z]{1,10}` to `[A-Z0-9]{1,10}` -- minimal change that supports both formats
- Symbol VO validation uses `isupper() or isdigit()` -- preserves existing uppercase requirement for US tickers
- QualityChecker staleness uses `numpy.busday_count` -- numpy already a project dependency, no new deps
- Added optional `now` parameter to `validate_ohlcv` for deterministic business-day testing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification Results

```
- typecheck: Pre-existing mypy config issue (duplicate module names) -- not in modified files
- test: PASS (596/596 passed, 0 failed)
- lint: PASS (0 errors in modified files; 4 pre-existing in unrelated files)
```

## Next Phase Readiness
- Ticker and Symbol VOs now accept Korean numeric tickers -- ready for Plan 02 (pykrx adapter)
- MarketType enum available for market-specific dispatching
- QualityChecker configurable max_stale_days=5 can be used for Korean market data
- Resolved STATE.md blockers: yfinance adjusted close validated (DATA-01), edgartools XBRL coverage validated (DATA-02)

## Self-Check: PASSED

- All 10 files verified present
- All 5 commits verified in git log

---
*Phase: 06-live-data-pipeline-korean-data*
*Completed: 2026-03-12*
