---
phase: 06-live-data-pipeline-korean-data
plan: 02
subsystem: data-ingest
tags: [pykrx, korean-market, kospi, kosdaq, duckdb, kr-fundamentals, pipeline]

# Dependency graph
requires:
  - phase: 06-live-data-pipeline-korean-data
    provides: MarketType enum, Ticker VO accepting Korean 6-digit tickers, business-day QualityChecker
provides:
  - PyKRXClient adapter fetching KOSPI/KOSDAQ OHLCV and fundamentals
  - Korean column mapping (시가->open, 고가->high, etc.)
  - DuckDB kr_fundamentals table for Korean market snapshot data
  - Pipeline market routing (US via yfinance, KR via pykrx)
  - CLI ingest --market kr end-to-end command
  - 1-second KRX rate limiting in sync fetch methods
affects: [scoring pipeline Korean expansion, future KOSPI universe provider]

# Tech tracking
tech-stack:
  added: [pykrx>=1.0]
  patterns: [market-aware pipeline routing via MarketType enum, sync-to-async pykrx wrapper via executor, separate kr_fundamentals table for market snapshot data]

key-files:
  created:
    - src/data_ingest/infrastructure/pykrx_client.py
    - tests/unit/test_pykrx_client.py
    - tests/unit/test_pipeline_kr.py
  modified:
    - src/data_ingest/infrastructure/duckdb_store.py
    - src/data_ingest/infrastructure/pipeline.py
    - src/data_ingest/infrastructure/__init__.py
    - cli/main.py
    - pyproject.toml
    - tests/unit/test_duckdb_store.py
    - tests/unit/test_cli_ingest.py

key-decisions:
  - "Korean fundamentals stored in separate kr_fundamentals table (not forced into SEC EDGAR financials schema) per RESEARCH pitfall 5"
  - "PyKRXClient uses time.sleep(1.0) in sync methods for KRX rate limiting, wrapped in asyncio executor"
  - "Pipeline split into _ingest_us_ticker and _ingest_kr_ticker for clean market routing"
  - "Korean OHLCV stored in same ohlcv table as US data (same schema, different ticker format)"
  - "CLI lazy-imports PyKRXClient only when --market kr is used"

patterns-established:
  - "Market routing: DataPipeline.ingest_ticker(ticker, market=MarketType.KR) dispatches to market-specific method"
  - "Korean data quality: max_stale_days=5 for Korean holiday tolerance"
  - "Korean fundamental columns: bps, per, pbr, eps, div_yield (renamed from DIV), dps"

requirements-completed: [DATA-04, DATA-05]

# Metrics
duration: 10min
completed: 2026-03-12
---

# Phase 6 Plan 02: Korean Market Data Adapter (pykrx) and Pipeline Wiring Summary

**pykrx adapter for KOSPI/KOSDAQ OHLCV and fundamentals with Korean-to-English column mapping, separate kr_fundamentals DuckDB table, pipeline market routing, and CLI --market kr support**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-12T06:17:33Z
- **Completed:** 2026-03-12T06:27:38Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Built PyKRXClient adapter wrapping pykrx sync calls via asyncio executor with 1-second rate limiting
- Korean OHLCV column mapping: 시가->open, 고가->high, 저가->low, 종가->close, 거래량->volume
- Korean fundamental column mapping: BPS->bps, PER->per, PBR->pbr, EPS->eps, DIV->div_yield, DPS->dps
- DuckDB kr_fundamentals table with store/get methods and upsert semantics
- Pipeline routes Korean tickers to pykrx, US tickers to yfinance (unchanged)
- CLI `ingest --market kr 005930` works end-to-end with lazy PyKRXClient import

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1 RED: Failing tests for pykrx adapter and kr_fundamentals** - `b8ccc07` (test)
2. **Task 1 GREEN: Implement pykrx adapter and kr_fundamentals store** - `30b1970` (feat)
3. **Task 2 RED: Failing tests for pipeline KR routing and CLI --market kr** - `ff6690f` (test)
4. **Task 2 GREEN: Wire Korean data into pipeline and CLI** - `e195349` (feat)

## Files Created/Modified
- `src/data_ingest/infrastructure/pykrx_client.py` - NEW: PyKRXClient with fetch_ohlcv and fetch_fundamentals
- `src/data_ingest/infrastructure/duckdb_store.py` - Added kr_fundamentals table, store_kr_fundamentals, get_kr_fundamentals
- `src/data_ingest/infrastructure/pipeline.py` - Market-aware routing, pykrx_client param, _ingest_kr_ticker method
- `src/data_ingest/infrastructure/__init__.py` - Exported PyKRXClient
- `cli/main.py` - ingest command passes MarketType.KR to pipeline, lazy PyKRXClient import
- `pyproject.toml` - Added pykrx>=1.0 to dependencies
- `tests/unit/test_pykrx_client.py` - NEW: 7 tests for pykrx adapter
- `tests/unit/test_duckdb_store.py` - Added 6 kr_fundamentals tests
- `tests/unit/test_pipeline_kr.py` - NEW: 5 tests for pipeline KR routing
- `tests/unit/test_cli_ingest.py` - Added 2 Korean market tests, updated mock signatures

## Decisions Made
- Korean fundamentals stored in separate `kr_fundamentals` table rather than forcing into SEC EDGAR `financials` schema -- pykrx data is market snapshots (PER/PBR/EPS from current price), not filing-based data
- PyKRXClient uses `time.sleep(1.0)` in sync methods (not asyncio.sleep) since pykrx is sync and runs in executor thread
- Pipeline split `ingest_ticker` into `_ingest_us_ticker` and `_ingest_kr_ticker` for clean separation
- Korean OHLCV goes into same `ohlcv` table as US data -- same schema, different ticker format (e.g., "005930")
- CLI lazy-imports PyKRXClient only when `--market kr` to avoid loading pykrx for US-only usage

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing CLI test mock signatures for market parameter**
- **Found during:** Task 2 (CLI wiring)
- **Issue:** Existing `mock_ingest` functions in test_cli_ingest.py didn't accept `market` keyword, causing TypeError after pipeline.ingest_universe gained market parameter
- **Fix:** Added `market=None` parameter to all existing mock_ingest async functions
- **Files modified:** tests/unit/test_cli_ingest.py
- **Verification:** All 11 CLI tests pass
- **Committed in:** e195349 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary to keep existing tests working with new API signature. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - pykrx requires no API key (uses KRX public data).

## Verification Results

```
- test: PASS (621/621 passed, 0 failed)
- lint: PASS (0 errors on modified files)
```

## Next Phase Readiness
- PyKRXClient ready for Korean market data ingestion
- Pipeline supports both US and KR markets via `--market` flag
- kr_fundamentals DuckDB table stores Korean market snapshot data
- Phase 6 fully complete (Plans 01, 02, 03 all done)

## Self-Check: PASSED

- All 11 files verified present
- All 4 commits verified in git log (b8ccc07, 30b1970, ff6690f, e195349)

---
*Phase: 06-live-data-pipeline-korean-data*
*Completed: 2026-03-12*
