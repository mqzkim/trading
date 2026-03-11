---
phase: 01-data-foundation
plan: 01
subsystem: database, domain
tags: [duckdb, sqlite, event-bus, value-objects, ddd, asyncio]

requires:
  - phase: none
    provides: first plan in project

provides:
  - Ticker, OHLCV, FinancialStatement, FilingDate, DataQualityReport domain VOs
  - DataIngestedEvent and QualityCheckFailedEvent domain events
  - DuckDBStore with point-in-time financial query support
  - SQLiteStore adapter wrapping core/data/cache.py
  - AsyncEventBus for cross-context communication

affects: [01-02, 01-03, scoring, signals]

tech-stack:
  added: [duckdb 1.5.0, edgartools 5.23.0, aiohttp 3.13.3]
  patterns: [frozen dataclass VOs, kw_only domain events, DuckDB point-in-time query, async event bus pub/sub]

key-files:
  created:
    - src/data_ingest/domain/value_objects.py
    - src/data_ingest/domain/events.py
    - src/data_ingest/infrastructure/duckdb_store.py
    - src/data_ingest/infrastructure/sqlite_store.py
    - src/shared/infrastructure/event_bus.py
    - src/data_ingest/DOMAIN.md
    - tests/unit/test_data_ingest_vos.py
    - tests/unit/test_duckdb_store.py
    - tests/unit/test_event_bus.py
  modified:
    - pyproject.toml
    - requirements.txt
    - src/data_ingest/domain/__init__.py

key-decisions:
  - "Used kw_only=True for domain events to solve dataclass inheritance with default fields"
  - "Fixed setuptools build backend from legacy to build_meta"
  - "Created .venv for dependency isolation (no venv existed)"
  - "DuckDB INSERT OR REPLACE for upsert semantics"

patterns-established:
  - "Domain events use @dataclass(frozen=True, kw_only=True) to inherit from DomainEvent"
  - "DuckDB store uses :memory: in tests, persistent file in production"
  - "Point-in-time queries filter by filing_date <= as_of_date (never period_end)"
  - "AsyncEventBus routes by event class __name__"

requirements-completed: [DATA-03]

duration: 7min
completed: 2026-03-12
---

# Phase 1 Plan 1: Data Foundation VOs, Stores, Event Bus Summary

**Frozen domain VOs (Ticker/OHLCV/FinancialStatement/FilingDate/DataQualityReport), DuckDB analytical store with point-in-time query, SQLite operational wrapper, and async event bus -- 53 tests passing**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-11T23:23:43Z
- **Completed:** 2026-03-11T23:31:28Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- Domain VOs with full invariant validation (immutable, frozen dataclasses)
- DuckDB store with OHLCV + financials tables, point-in-time financial queries
- Async event bus supporting both sync and async handlers
- All 3 new dependencies installed (duckdb 1.5.0, edgartools 5.23.0, aiohttp 3.13.3)

## Task Commits

Each task was committed atomically:

1. **Task 1: Domain VOs, events, dependency install** - `a420d6c` (feat)
2. **Task 2: DuckDB store, SQLite wrapper, async event bus** - `35a3ca4` (feat)

_Both tasks used TDD: RED (failing tests) -> GREEN (implementation) -> commit_

## Files Created/Modified
- `src/data_ingest/domain/value_objects.py` - Ticker, OHLCV, FinancialStatement, FilingDate, DataQualityReport VOs
- `src/data_ingest/domain/events.py` - DataIngestedEvent, QualityCheckFailedEvent
- `src/data_ingest/domain/__init__.py` - Public API exports
- `src/data_ingest/infrastructure/duckdb_store.py` - DuckDB analytical store with point-in-time queries
- `src/data_ingest/infrastructure/sqlite_store.py` - SQLite adapter wrapping core/data/cache.py
- `src/shared/infrastructure/event_bus.py` - Async in-process event bus
- `src/shared/infrastructure/__init__.py` - AsyncEventBus export
- `src/data_ingest/DOMAIN.md` - Bounded context documentation
- `tests/unit/test_data_ingest_vos.py` - 38 VO and event tests
- `tests/unit/test_duckdb_store.py` - 9 DuckDB store tests
- `tests/unit/test_event_bus.py` - 6 async event bus tests
- `pyproject.toml` - Added duckdb, edgartools, aiohttp deps; fixed build backend
- `requirements.txt` - Added new dependencies

## Decisions Made
- Used `kw_only=True` on domain event dataclasses (matches existing pattern in scoring/regime/signals events) to resolve Python dataclass inheritance issue with default-valued parent fields
- Fixed `setuptools.backends.legacy:build` to `setuptools.build_meta` (blocking build error)
- Created `.venv` virtual environment (none existed; system Python had PEP 668 restriction)
- Added `src*` to `[tool.setuptools.packages.find]` for src/ package discovery

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed setuptools build backend**
- **Found during:** Task 1 (dependency install)
- **Issue:** `setuptools.backends.legacy:build` doesn't exist, pip install failed
- **Fix:** Changed to `setuptools.build_meta` (standard backend)
- **Files modified:** pyproject.toml
- **Verification:** `pip install -e ".[dev]"` succeeds
- **Committed in:** a420d6c (Task 1 commit)

**2. [Rule 3 - Blocking] Created virtual environment**
- **Found during:** Task 1 (dependency install)
- **Issue:** No .venv existed, system Python blocked pip install (PEP 668)
- **Fix:** Created .venv with `python3 -m venv .venv`
- **Files modified:** .venv/ (not tracked in git)
- **Verification:** All imports work in venv
- **Committed in:** N/A (venv not committed)

**3. [Rule 1 - Bug] Added kw_only=True to domain events**
- **Found during:** Task 1 (domain events)
- **Issue:** `non-default argument follows default argument` error from DomainEvent.occurred_on having default
- **Fix:** Added `kw_only=True` (matches existing event pattern in codebase)
- **Files modified:** src/data_ingest/domain/events.py
- **Verification:** All event tests pass
- **Committed in:** a420d6c (Task 1 commit)

**4. [Rule 3 - Blocking] Added src* to setuptools packages.find**
- **Found during:** Task 1 (dependency install)
- **Issue:** `src/` packages not discoverable by setuptools
- **Fix:** Added `src*` to `[tool.setuptools.packages.find]` include list
- **Files modified:** pyproject.toml
- **Verification:** `from src.data_ingest.domain.value_objects import Ticker` works
- **Committed in:** a420d6c (Task 1 commit)

---

**Total deviations:** 4 auto-fixed (2 blocking, 1 bug, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correct build and import chain. No scope creep.

## Issues Encountered
- Pre-existing ruff error in `src/data_ingest/infrastructure/quality_checker.py` (unused numpy import) -- out of scope, not modified in this plan

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Domain VOs and events ready for Plans 01-02 (yfinance/edgartools clients) and 01-03 (scoring adapter)
- DuckDB store ready to receive ingested data from Plan 01-02 clients
- Event bus ready for cross-context communication
- All tests passing, lint clean on modified files

---
*Phase: 01-data-foundation*
*Completed: 2026-03-12*
