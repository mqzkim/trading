---
phase: 06-live-data-pipeline-korean-data
verified: 2026-03-12T07:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: null
gaps: []
human_verification:
  - test: "Run `ingest --market kr 005930` against live KRX API"
    expected: "Fetches Samsung OHLCV and fundamentals, stores them in DuckDB, completes without error"
    why_human: "pykrx calls real KRX servers; rate-limit and live data unavailable in unit tests"
  - test: "Run `ingest --regime` against live yfinance API"
    expected: "Backfills 2 years of VIX/S&P500/yield-curve data, displays row count and date range"
    why_human: "RegimeDataClient calls real yfinance endpoints; live API latency and response shape not testable in unit tests"
---

# Phase 6: Live Data Pipeline (Korean Data) Verification Report

**Phase Goal:** Users can ingest real market data from live APIs (yfinance, SEC EDGAR, pykrx) with automatic quality validation, for both US and Korean equities
**Verified:** 2026-03-12T07:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | edgartools_client stores the actual ticker symbol (not filing_date) in financial records | VERIFIED | `src/data_ingest/infrastructure/edgartools_client.py` line 154: `"ticker": ticker` — the bug fix is present and confirmed |
| 2 | Ticker VO accepts Korean 6-digit numeric tickers alongside US uppercase tickers | VERIFIED | `_TICKER_RE = re.compile(r"^[A-Z0-9]{1,10}$")` in `src/data_ingest/domain/value_objects.py` — pattern extended from `[A-Z]` to `[A-Z0-9]` |
| 3 | scoring Symbol VO accepts Korean numeric tickers without raising ValueError | VERIFIED | `src/scoring/domain/value_objects.py` line 27: `self.ticker.isupper() or self.ticker.isdigit()` |
| 4 | QualityChecker staleness uses business-day-aware logic (no false positives on weekends/holidays) with configurable threshold | VERIFIED | `src/data_ingest/infrastructure/quality_checker.py` lines 73-81: uses `numpy.busday_count`, `max_stale_days` parameter present, injectable `now` for testing |
| 5 | pykrx adapter fetches KOSPI/KOSDAQ OHLCV and fundamentals with Korean-to-English column mapping, 1-second rate limit enforced | VERIFIED | `src/data_ingest/infrastructure/pykrx_client.py` — `_OHLCV_COLUMN_MAP` maps 시가/고가/저가/종가/거래량; `time.sleep(1.0)` in both sync methods |
| 6 | Korean data is routed through pykrx in the pipeline, stored in DuckDB (OHLCV in `ohlcv`, fundamentals in `kr_fundamentals`), and CLI `ingest --market kr` works end-to-end | VERIFIED | `src/data_ingest/infrastructure/pipeline.py` — `_ingest_kr_ticker` method routes to pykrx; `DuckDBStore` has `kr_fundamentals` table, `store_kr_fundamentals`/`get_kr_fundamentals`; `cli/main.py` has `--market kr` wired |
| 7 | VIX, S&P 500 close/MA200/ratio, and yield curve spread are fetched as time series and stored in DuckDB `regime_data` table; CLI `ingest --regime` works and rejects `--market kr` | VERIFIED | `src/data_ingest/infrastructure/regime_data_client.py` — `fetch_regime_history(years=2)` returns all 8 columns; `DuckDBStore._create_tables` creates `regime_data` table with date primary key; `cli/main.py` `_ingest_regime` rejects `--market kr` |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/data_ingest/infrastructure/edgartools_client.py` | Fixed ticker field on line 154 | VERIFIED | Line 154: `"ticker": ticker` — actual ticker parameter stored |
| `src/data_ingest/domain/value_objects.py` | Ticker VO extended for Korean tickers, MarketType enum | VERIFIED | `_TICKER_RE = r"^[A-Z0-9]{1,10}$"`, `class MarketType(Enum): US="us", KR="kr"` |
| `src/data_ingest/domain/__init__.py` | MarketType exported from domain public API | VERIFIED | `MarketType` in `__all__` |
| `src/scoring/domain/value_objects.py` | Symbol VO accepting numeric Korean tickers | VERIFIED | `self.ticker.isupper() or self.ticker.isdigit()` |
| `src/data_ingest/infrastructure/quality_checker.py` | Business-day-aware staleness with max_stale_days | VERIFIED | `numpy.busday_count`, configurable `max_stale_days=3` default, injectable `now` |
| `src/data_ingest/infrastructure/pykrx_client.py` | Korean market data adapter (>60 lines) | VERIFIED | 133 lines — `fetch_ohlcv`, `fetch_fundamentals`, Korean column mapping, 1s rate limit |
| `src/data_ingest/infrastructure/duckdb_store.py` | kr_fundamentals and regime_data tables | VERIFIED | `_create_tables` creates both tables; `store_kr_fundamentals`, `store_regime_data`, `get_kr_fundamentals`, `get_regime_data` methods present |
| `src/data_ingest/infrastructure/regime_data_client.py` | Regime indicator fetcher using yfinance (>40 lines) | VERIFIED | 118 lines — `fetch_regime_snapshot` and `fetch_regime_history(years)` implemented |
| `src/data_ingest/infrastructure/pipeline.py` | Market-aware routing: KR to pykrx | VERIFIED | `ingest_ticker(ticker, market=MarketType.US)` dispatches to `_ingest_us_ticker` or `_ingest_kr_ticker`; `max_stale_days=5` for KR |
| `src/data_ingest/infrastructure/__init__.py` | PyKRXClient and RegimeDataClient exported | VERIFIED | Both present in `__all__` |
| `cli/main.py` | `--market kr` and `--regime` flags on `ingest` command | VERIFIED | `market: str = typer.Option("us", "--market", "-m")`, `regime: bool = typer.Option(False, "--regime")` |
| `tests/unit/test_yfinance_adapter.py` | auto_adjust=True validation tests | VERIFIED | `auto_adjust` pattern present; tests for no Adj Close column, lowercase columns |
| `tests/unit/test_pykrx_client.py` | Unit tests for pykrx adapter (>40 lines) | VERIFIED | 7 tests covering OHLCV column mapping, fundamentals mapping, empty DataFrame, rate limit |
| `tests/unit/test_regime_data_client.py` | Unit tests for regime data fetching (>30 lines) | VERIFIED | 5 tests covering snapshot keys, history columns, 2-year backfill |
| `tests/unit/test_pipeline_kr.py` | Unit tests for pipeline KR routing | VERIFIED | 5 tests: pykrx routing, OHLCV storage, fundamentals storage, max_stale_days=5, US path unchanged |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `edgartools_client.py` | DuckDB financials table | `"ticker": ticker` in returned dict | VERIFIED | Line 154 confirmed: `"ticker": ticker` |
| `value_objects.py (Ticker)` | `pipeline.py` | Ticker VO construction | VERIFIED | Pipeline imports `MarketType` from `src.data_ingest.domain.value_objects` |
| `yfinance_client.py` | `core/data/client.py` | CoreDataClient with auto_adjust=True | VERIFIED | Tests confirm no Adj Close column returned |
| `pykrx_client.py` | `pykrx.stock` | `stock.get_market_ohlcv` and `stock.get_market_fundamental` | VERIFIED | Line 93: `stock.get_market_ohlcv(...)`, line 119: `stock.get_market_fundamental(...)` |
| `pipeline.py` | `pykrx_client.py` | `_ingest_kr_ticker` method, `MarketType.KR` dispatch | VERIFIED | Lines 83-85 dispatch on `MarketType.KR`; `_ingest_kr_ticker` calls `self._pykrx.fetch_ohlcv` and `fetch_fundamentals` |
| `cli/main.py` | `pipeline.py` | `ingest` command `--market` flag | VERIFIED | Lines 718-726: `MarketType.KR` constructed and passed to `DataPipeline(pykrx_client=...)` |
| `regime_data_client.py` | yfinance (^VIX, ^GSPC, ^TNX, ^IRX) | `yf.Ticker` calls | VERIFIED | Lines 30-33, 68-71: all four yf.Ticker calls present |
| `regime_data_client.py` | `duckdb_store.py` | `store_regime_data` method | VERIFIED | `cli/main.py` line 772: `store.store_regime_data(df)` after `client.fetch_regime_history(years=2)` |
| `cli/main.py` | `regime_data_client.py` | `ingest --regime` flag | VERIFIED | Lines 707-708: `if regime: _ingest_regime(tickers, market); return` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DATA-01 | 06-01-PLAN.md | yfinance 실제 API 데이터 파이프라인 검증 (adjusted close 동작 포함) | SATISFIED | `test_yfinance_adapter.py` validates `auto_adjust=True` returns `{open,high,low,close,volume}` with no Adj Close column; `core/data/client.py` uses `auto_adjust=True` |
| DATA-02 | 06-01-PLAN.md | edgartools XBRL 커버리지 소형주 검증 | SATISFIED | `test_edgartools_client.py` validates small-cap scenarios: missing XBRL fields return 0.0 defaults (not exception), Company not found returns empty list |
| DATA-03 | 06-01-PLAN.md | 데이터 품질 검증 레이어 (결측/이상치 탐지) | SATISFIED | `QualityChecker` has business-day staleness (`numpy.busday_count`), configurable `max_stale_days`, missing-values check (>5%), outlier check (3-sigma); `test_quality_checker.py` covers all cases |
| DATA-04 | 06-02-PLAN.md | pykrx 기반 KOSPI/KOSDAQ OHLCV 데이터 수집 어댑터 | SATISFIED | `PyKRXClient.fetch_ohlcv` maps 시가/고가/저가/종가/거래량 to English; pipeline routes KR tickers to pykrx; 7 unit tests pass |
| DATA-05 | 06-02-PLAN.md | pykrx 기반 한국 시장 재무제표 수집 (PER/PBR/DIV) | SATISFIED | `PyKRXClient.fetch_fundamentals` maps BPS/PER/PBR/EPS/DIV/DPS; `kr_fundamentals` DuckDB table stores them separately from SEC EDGAR financials |
| DATA-06 | 06-03-PLAN.md | 레짐 감지용 데이터 수집 (VIX, S&P 500, 수익률 곡선) | SATISFIED | `RegimeDataClient.fetch_regime_history(years=2)` returns all 8 columns; `regime_data` DuckDB table with date primary key; `ingest --regime` CLI command works; 5 unit tests pass |

**All 6 requirements satisfied. No orphaned requirements.**

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `cli/main.py` | 834 | `entry_price=100.0,  # placeholder -- real price from data client` | Info | Pre-existing placeholder in `generate-plan` command (Phase 5 artifact, not Phase 6 scope). Does not affect any Phase 6 data ingestion path. |

No blocker anti-patterns found in Phase 6 files.

---

### Test Suite Results

**Phase-relevant tests (139):** PASS — 0 failed
- `test_edgartools_client.py` — ticker bug fix, small-cap XBRL coverage
- `test_data_ingest_vos.py` — Korean Ticker VO, MarketType enum, Symbol KR
- `test_quality_checker.py` — business-day staleness, weekend gap, custom threshold
- `test_yfinance_adapter.py` — auto_adjust=True, no Adj Close, lowercase columns
- `test_pykrx_client.py` — OHLCV column mapping, fundamentals mapping, rate limit
- `test_duckdb_store.py` — kr_fundamentals and regime_data table operations
- `test_regime_data_client.py` — snapshot keys, history columns, 2-year backfill
- `test_pipeline_kr.py` — KR market routing, OHLCV/fundamentals storage, max_stale_days=5
- `test_cli_ingest.py` — `--market kr`, `--regime`, error cases, US regression

**Full test suite (621):** PASS — 0 failed (excluding pre-existing `test_api_routes.py` import error for missing `fastapi` dependency, unrelated to Phase 6)

**Git commits verified (all present in git log):**
- Plan 01: `bd9042d`, `bda3cef`, `3ccc1a4`, `69268a7`, `9d9a09f`
- Plan 02: `b8ccc07`, `30b1970`, `ff6690f`, `e195349`
- Plan 03: `d2dfa41`, `32e208d`, `9a3dea8`, `dca69ca`

---

### Human Verification Required

#### 1. Live Korean Market Ingestion

**Test:** Run `cd /home/mqz/workspace/trading && python -m trading ingest --market kr 005930`
**Expected:** Fetches Samsung Electronics (005930) OHLCV and PER/PBR/EPS/DIV/BPS/DPS data from KRX, stores in DuckDB, displays results table with row counts
**Why human:** pykrx makes live HTTP requests to KRX servers with 1-second rate limiting. Real-API behavior (response format, network latency, trading calendar) cannot be tested in unit tests.

#### 2. Live Regime Data Backfill

**Test:** Run `cd /home/mqz/workspace/trading && python -m trading ingest --regime`
**Expected:** Fetches ~500 rows of VIX/S&P500/yield-curve data covering 2 years, displays "Rows Stored: ~500", date range spanning 2 years, columns listed
**Why human:** RegimeDataClient calls live yfinance endpoints for ^VIX, ^GSPC, ^TNX, ^IRX. The exact row count and date range depend on live market data availability.

---

### Gaps Summary

No gaps. All 7 observable truths verified, all 6 requirements satisfied, all key links wired, all artifacts substantive and tested.

---

_Verified: 2026-03-12T07:00:00Z_
_Verifier: Claude (gsd-verifier)_
