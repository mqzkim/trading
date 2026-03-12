# Phase 6: Live Data Pipeline & Korean Data - Research

**Researched:** 2026-03-12
**Domain:** Data ingestion (yfinance, edgartools, pykrx), data quality validation, regime data sources
**Confidence:** HIGH

## Summary

Phase 6 validates the existing US data pipeline against live APIs (yfinance for OHLCV, edgartools for SEC EDGAR financials), adds a data quality validation layer, builds a Korean market data adapter using pykrx, and ingests regime detection data sources (VIX, S&P 500, yield curve). The core infrastructure already exists from v1.0 Phase 1 -- `DataPipeline`, `YFinanceClient`, `EdgartoolsClient`, `QualityChecker`, and `DuckDBStore` are all implemented. The work is validation, bug fixes, extension (Korean market), and new regime data ingestion.

Key finding: the existing `DataClient` in `core/data/client.py` uses `auto_adjust=True` for yfinance, which since yfinance 0.2.28+ means ALL OHLCV columns (Open/High/Low/Close) are already adjusted for splits and dividends, and no separate "Adj Close" column is returned. This is the correct behavior for the trading system's use case (backtesting, scoring). The `edgartools_client.py` has a known bug on line 154 where `ticker` field is set to `str(filing_date)` instead of the actual ticker. Korean tickers are 6-digit numbers (e.g., "005930") which the current `Ticker` VO regex `^[A-Z]{1,10}$` rejects -- this must be addressed.

**Primary recommendation:** Fix known bugs first (edgartools ticker field, Ticker VO regex for Korean tickers), validate existing pipeline against live data with integration tests, then extend with pykrx adapter and regime data ingestion.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | yfinance OHLCV pipeline validation (adjusted close) | yfinance 1.2.0 installed; auto_adjust=True already applied; existing `DataClient._yfinance_price()` uses `auto_adjust=True`; need empirical validation that returned close matches Yahoo Finance website |
| DATA-02 | edgartools XBRL small-cap coverage validation | edgartools 5.23.0 installed; XBRL standardization covers 234 concepts from 32,240 filings; known ticker bug line 154; need empirical test with 5+ small-cap tickers |
| DATA-03 | Data quality validation layer (missing/outlier/stale) | `QualityChecker` already implemented with 3 checks (missing >5%, stale >3 days, outliers >1% 3-sigma); existing unit tests pass; need integration with pipeline to block scoring on failed quality |
| DATA-04 | pykrx KOSPI/KOSDAQ OHLCV adapter | pykrx not yet installed; API: `stock.get_market_ohlcv(start, end, ticker)`; date format "YYYYMMDD"; returns DataFrame with columns matching system needs |
| DATA-05 | pykrx Korean fundamentals (PER/PBR/DIV) | pykrx provides `stock.get_market_fundamental(start, end, ticker)` returning BPS/PER/PBR/EPS/DIV/DPS; different metric set than SEC EDGAR financials |
| DATA-06 | Regime data ingestion (VIX, S&P 500, yield curve) | `core/data/market.py` already fetches VIX (`^VIX`), S&P 500 vs 200MA (`^GSPC`), yield curve (`^TNX` - `^IRX`); need to store in DuckDB analytics table for regime context |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | 1.2.0 (installed) | US OHLCV + market index data | Already in use; free; covers ^VIX, ^GSPC, ^TNX, ^IRX |
| edgartools | 5.23.0 (installed) | SEC EDGAR XBRL financial data | Already in use; 234 standardized concepts from 32K filings |
| pykrx | latest (to install) | Korean KOSPI/KOSDAQ market data | De facto standard for Korean market data in Python; free; KRX direct source |
| duckdb | >=1.0 (installed) | Analytical storage for OHLCV + financials | Already in use; columnar storage optimized for screening queries |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | >=2.0 (installed) | Data manipulation and storage format | Used throughout pipeline |
| numpy | >=1.26 (installed) | Statistical calculations (outlier detection) | Quality checker outlier computation |
| typer | >=0.9 (installed) | CLI interface for ingest command | Already used for `ingest` command |
| rich | >=13.0 (installed) | CLI output formatting | Already used for table display |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pykrx | KRX Open API | pykrx is simpler (no API key), KRX Open API has more features but requires registration |
| yfinance for yield curve | fredapi (FRED) | yfinance ^TNX/^IRX works for yield data; FRED is more authoritative but requires API key |
| DuckDB for regime data | SQLite regime store | DuckDB is already used for OHLCV/financials analytical queries; consistency is better than adding another SQLite store |

**Installation:**
```bash
pip install pykrx
```

## Architecture Patterns

### Existing Project Structure (data_ingest context)
```
src/
  data_ingest/
    domain/
      events.py              # DataIngestedEvent, QualityCheckFailedEvent
      value_objects.py        # Ticker, OHLCV, FinancialStatement, DataQualityReport
      __init__.py
    infrastructure/
      yfinance_client.py     # US OHLCV via core DataClient wrapper
      edgartools_client.py   # SEC EDGAR financials
      quality_checker.py     # OHLCV + financial validation
      duckdb_store.py        # Analytical store (OHLCV + financials)
      pipeline.py            # DataPipeline orchestrator
      universe_provider.py   # S&P 500/400 ticker lists
      sqlite_store.py        # Operational cache
      __init__.py
    __init__.py
```

### Recommended Extensions for Phase 6
```
src/
  data_ingest/
    domain/
      value_objects.py        # ADD: KoreanTicker VO, MarketType enum, RegimeDataPoint VO
    infrastructure/
      pykrx_client.py         # NEW: Korean market OHLCV + fundamentals adapter
      regime_data_client.py   # NEW: VIX/S&P500/yield curve fetcher + DuckDB storage
      quality_checker.py      # EXTEND: Korean market quality validation rules
      duckdb_store.py         # EXTEND: regime_data table, Korean OHLCV table schema
      pipeline.py             # EXTEND: --market kr support, regime data ingestion
```

### Pattern 1: Market-Aware Data Adapter
**What:** Abstract the market-specific data fetching behind a common interface so the pipeline can handle both US and Korean data.
**When to use:** Any time data sources differ by market but downstream consumers expect the same shape.
**Example:**
```python
# In data_ingest/domain/value_objects.py
class MarketType(Enum):
    US = "us"
    KR = "kr"

# In pipeline.py -- the pipeline routes to the correct client based on market
async def ingest_ticker(self, ticker: str, market: MarketType = MarketType.US):
    if market == MarketType.US:
        ohlcv_df = await self._yfinance.fetch_ohlcv(ticker)
        financials = await self._edgartools.fetch_financials(ticker)
    elif market == MarketType.KR:
        ohlcv_df = await self._pykrx.fetch_ohlcv(ticker)
        financials = await self._pykrx.fetch_fundamentals(ticker)
```

### Pattern 2: Sync-to-Async Wrapper for pykrx
**What:** pykrx is synchronous (scrapes KRX website). Wrap in asyncio executor like YFinanceClient does.
**When to use:** Any sync library integrated into the async DataPipeline.
**Example:**
```python
# In pykrx_client.py
class PyKRXClient:
    async def fetch_ohlcv(self, ticker: str, days: int = 756) -> pd.DataFrame:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_ohlcv_sync, ticker, days)

    def _fetch_ohlcv_sync(self, ticker: str, days: int) -> pd.DataFrame:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=int(days * 1.4))).strftime("%Y%m%d")
        return stock.get_market_ohlcv(start_date, end_date, ticker)
```

### Pattern 3: Regime Data as DuckDB Table
**What:** Store regime indicator snapshots (VIX, S&P 500 ratio, yield spread) in DuckDB for historical queries.
**When to use:** Regime detection (Phase 8) needs historical regime data, not just point-in-time.
**Example:**
```python
# In duckdb_store.py -- add regime_data table
CREATE TABLE IF NOT EXISTS regime_data (
    date DATE PRIMARY KEY,
    vix DOUBLE,
    sp500_close DOUBLE,
    sp500_ma200 DOUBLE,
    sp500_ratio DOUBLE,
    yield_10y DOUBLE,
    yield_3m DOUBLE,
    yield_spread_bps DOUBLE
)
```

### Anti-Patterns to Avoid
- **Sharing YFinanceClient for Korean tickers:** yfinance uses `.KS`/`.KQ` suffixes for Korean tickers but this is unreliable for fundamentals -- use pykrx for all Korean data
- **Creating a new bounded context for Korean data:** Korean market data belongs in `data_ingest`, not a separate context. The difference is in the infrastructure adapter, not the domain
- **Bypassing QualityChecker for Korean data:** Korean data needs the same quality gates. Adapt thresholds if needed (e.g., stale_days may differ due to Korean holidays) but do not skip validation

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Korean OHLCV data | Custom KRX web scraper | pykrx `stock.get_market_ohlcv()` | KRX website structure changes; pykrx handles it |
| Korean fundamentals | Custom DART API parser | pykrx `stock.get_market_fundamental()` | Returns PER/PBR/EPS/BPS/DIV directly |
| Korean ticker lookup | Manual ticker-to-name mapping | pykrx `stock.get_market_ticker_list()` / `get_market_ticker_name()` | pykrx maintains current mappings |
| SEC EDGAR parsing | Custom XBRL parser | edgartools `Company().get_filings()` | 234 standardized concepts, XBRL namespace resolution |
| VIX/index data | CBOE website scraping | yfinance `Ticker("^VIX").history()` | Already works in `core/data/market.py` |
| Yield curve data | Treasury.gov scraping | yfinance `^TNX` and `^IRX` | Already works in `core/data/market.py` |

**Key insight:** All data source integrations are already partially implemented or have well-maintained libraries. The work is wiring, validation, and extension -- not building from scratch.

## Common Pitfalls

### Pitfall 1: edgartools Ticker Field Bug (Line 154)
**What goes wrong:** `edgartools_client.py:154` sets `"ticker": str(filing_date)` -- the ticker field contains a date string, not the actual ticker symbol. When stored in DuckDB financials table, queries by ticker return nothing.
**Why it happens:** Copy-paste error from v1.0 -- the field was meant to be overridden by context but never is.
**How to avoid:** Fix line 154 to use the actual ticker parameter: `"ticker": ticker`. Verify with integration test that stored financials have correct ticker value.
**Warning signs:** `duckdb_store.get_latest_financials("AAPL", ...)` returns empty DataFrame despite successful ingestion.

### Pitfall 2: Korean Ticker Format Rejected by Ticker VO
**What goes wrong:** Korean stock tickers are 6-digit numbers (e.g., "005930" for Samsung). The `Ticker` VO in `data_ingest/domain/value_objects.py` uses regex `^[A-Z]{1,10}$` which rejects digits. The `scoring/domain/value_objects.py` `Symbol` VO uses `ticker.isupper()` check which also rejects numeric strings.
**Why it happens:** VOs were designed for US equities only.
**How to avoid:** Extend the `Ticker` VO to accept Korean format: `^[A-Z0-9]{1,10}$` or add a market-aware validation. Alternatively, create a separate `KoreanTicker` VO with its own regex `^[0-9]{6}$`.
**Warning signs:** `ValueError` when constructing `Ticker("005930")`.

### Pitfall 3: pykrx Date Format Must Be "YYYYMMDD" Strings
**What goes wrong:** pykrx requires date strings in `"YYYYMMDD"` format (no dashes). Passing `"2024-01-01"` or `datetime.date` objects causes errors or returns empty DataFrames silently.
**Why it happens:** pykrx scrapes KRX website which expects this specific format.
**How to avoid:** Always format dates with `strftime("%Y%m%d")` before passing to pykrx. Add a validation step in the adapter.
**Warning signs:** Empty DataFrame returned with no error from pykrx.

### Pitfall 4: pykrx Rate Limiting (1 second between requests)
**What goes wrong:** Rapid successive pykrx calls (especially for bulk KOSPI universe) get blocked by KRX servers. No error is raised -- empty DataFrames are returned silently.
**Why it happens:** KRX website has anti-scraping protection. pykrx docs recommend 1-second delay between requests.
**How to avoid:** Use `asyncio.Semaphore(1)` for pykrx calls (not the shared semaphore from the US pipeline). Add explicit `time.sleep(1.0)` in the sync fetch method.
**Warning signs:** First few tickers return data, later ones return empty.

### Pitfall 5: pykrx Fundamental Data is Point-in-Time Market Snapshots, Not Filing Data
**What goes wrong:** pykrx `get_market_fundamental()` returns PER/PBR/EPS/BPS/DIV as market-derived metrics for a specific date, NOT historical filing data like SEC EDGAR provides. These are calculated by KRX from the latest available financial statements and current stock price. This is fundamentally different from SEC EDGAR's filing-date-based point-in-time data.
**Why it happens:** Korean market data infrastructure (KRX/DART) works differently from SEC EDGAR.
**How to avoid:** Do not try to force pykrx fundamental data into the same schema as SEC EDGAR data. Store Korean fundamentals in a separate table or with a different schema that reflects what pykrx actually provides: date-keyed market valuation metrics rather than filing-date-keyed financial statements.
**Warning signs:** Trying to populate `filing_date`, `form_type`, `revenue`, `net_income` columns from pykrx data -- these fields don't exist in pykrx output.

### Pitfall 6: yfinance auto_adjust=True Already Applied in Existing Code
**What goes wrong:** Attempting to "fix" adjusted close handling by adding `auto_adjust=False` or adding an "Adj Close" column when the system already correctly uses `auto_adjust=True`. All OHLCV columns are already adjusted.
**Why it happens:** The validation requirement "adjusted close values matching the source" may lead to unnecessary changes.
**How to avoid:** Validate by comparing `DataClient._yfinance_price()` output with Yahoo Finance website values. The existing `auto_adjust=True` in `core/data/client.py:82` is correct for this system's use case. Do not change it.
**Warning signs:** Discrepancy investigation that leads to adding a separate "adj_close" column when one isn't needed.

### Pitfall 7: Weekend/Holiday Stale Data False Positives
**What goes wrong:** `QualityChecker.validate_ohlcv()` uses calendar days for staleness check (`max_stale_days=3`). On Monday morning, data from Friday is 3 days old. During holidays (e.g., Korean Chuseok -- 3+ days), data appears "stale" when it's simply the last trading day.
**Why it happens:** Staleness check uses `pd.Timestamp.now() - last_date` without accounting for non-trading days.
**How to avoid:** Change staleness to count business days, or increase threshold for Korean market data (which has more holidays). At minimum, use `max_stale_days=5` for weekend tolerance.
**Warning signs:** Quality check failures every Monday or after public holidays.

## Code Examples

### pykrx OHLCV Fetch (verified from pykrx GitHub)
```python
# Source: https://github.com/sharebook-kr/pykrx
from pykrx import stock

# Get OHLCV for Samsung Electronics (005930)
df = stock.get_market_ohlcv("20240101", "20240301", "005930")
# Returns DataFrame with columns: 시가, 고가, 저가, 종가, 거래량
# Column names are in Korean; need to rename for system compatibility

# Get all KOSPI tickers
tickers = stock.get_market_ticker_list(market="KOSPI")
# Returns: ['005930', '000660', '005380', ...]

# Get ticker name
name = stock.get_market_ticker_name("005930")
# Returns: '삼성전자'
```

### pykrx Fundamental Fetch (verified from pykrx GitHub)
```python
from pykrx import stock

# Get fundamentals for Samsung over a date range
df = stock.get_market_fundamental("20240101", "20240301", "005930")
# Returns DataFrame with columns: BPS, PER, PBR, EPS, DIV, DPS
# BPS: Book value Per Share
# PER: Price-to-Earnings Ratio
# PBR: Price-to-Book Ratio
# EPS: Earnings Per Share
# DIV: Dividend Yield (%)
# DPS: Dividend Per Share

# Get fundamentals for all KOSPI stocks on a specific date
df_all = stock.get_market_fundamental("20240301", market="KOSPI")
# Returns DataFrame indexed by ticker
```

### yfinance Regime Data Fetch (existing in core/data/market.py)
```python
# Source: core/data/market.py (already implemented)
import yfinance as yf

# VIX
vix_df = yf.Ticker("^VIX").history(period="5d")
vix = float(vix_df["Close"].iloc[-1])

# S&P 500 vs 200MA
sp500_df = yf.Ticker("^GSPC").history(period="2y")
close = sp500_df["Close"]
ma200 = close.rolling(200).mean()
ratio = float(close.iloc[-1] / ma200.iloc[-1])

# Yield Curve (10Y - 3M)
ten_year = yf.Ticker("^TNX").history(period="5d")["Close"].iloc[-1]
three_month = yf.Ticker("^IRX").history(period="5d")["Close"].iloc[-1]
spread_bps = float((ten_year - three_month) * 100)
```

### edgartools Corrected Ticker Field
```python
# Fix for edgartools_client.py line 154
# BEFORE (bug):
"ticker": str(filing_date),  # Will be overridden by caller context
# AFTER (fix):
"ticker": ticker,  # Actual stock ticker symbol
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance returns separate Adj Close | auto_adjust=True adjusts all OHLC | yfinance 0.2.28+ | Close column IS adjusted; no Adj Close column returned |
| edgartools basic XBRL parsing | 234 standardized concepts from 32K filings | edgartools 5.22.0+ | Much better small-cap coverage; industry-aware mappings |
| pykrx `get_market_ohlcv_by_date` | `get_market_ohlcv` (renamed) | pykrx recent versions | Same functionality, cleaner API name |
| Yahoo Finance free historical data concern | Issue resolved (was ad-blocker/rate-limit, not paywall) | March 2025 | yfinance works fine; need rate-limit awareness |

**Deprecated/outdated:**
- yfinance `auto_adjust=False` as default: now defaults to True; the existing code already uses True explicitly, which is correct
- pykrx `get_market_ohlcv_by_date`: renamed to `get_market_ohlcv` in newer versions; the old name may still work as alias

## Open Questions

1. **pykrx Column Name Language**
   - What we know: pykrx returns DataFrame with Korean column names (시가, 고가, 저가, 종가, 거래량)
   - What's unclear: Whether this is configurable or always Korean
   - Recommendation: Build a column rename mapping in the adapter; verify empirically during implementation

2. **Korean Market Holiday Calendar**
   - What we know: Korean market has different holidays than US (Chuseok, Lunar New Year, etc.)
   - What's unclear: Whether pykrx handles holiday gaps gracefully or returns errors
   - Recommendation: Use wider stale_days threshold for Korean data (5+ days); test with known holiday periods

3. **edgartools Small-Cap XBRL Coverage Empirical Validation**
   - What we know: edgartools 5.23.0 has expanded XBRL coverage with 234 standardized concepts
   - What's unclear: Whether specific small-cap companies have XBRL data or just return empty
   - Recommendation: Test with 5 small-cap tickers (market cap < $1B); record which ones have data, which don't

4. **Regime Data Historical Depth**
   - What we know: VIX, S&P 500, yield data are fetchable from yfinance
   - What's unclear: How much historical regime data to backfill for Phase 8 (Regime Detection) needs
   - Recommendation: Store 2 years of daily snapshots to support 200-day MA calculation and regime history

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ with pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_quality_checker.py tests/unit/test_yfinance_adapter.py tests/unit/test_edgartools_client.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | yfinance OHLCV with auto_adjust=True returns correct adjusted close | unit | `pytest tests/unit/test_yfinance_adapter.py -x` | Exists (mock-based) |
| DATA-01 | ingest CLI fetches and stores live OHLCV for US ticker | integration | `pytest tests/integration/test_data_ingest.py -x` | Exists (mock-based) |
| DATA-02 | edgartools returns financials for small-cap tickers | unit | `pytest tests/unit/test_edgartools_client.py -x` | Exists (mock-based) |
| DATA-03 | QualityChecker detects missing/stale/outlier data | unit | `pytest tests/unit/test_quality_checker.py -x` | Exists |
| DATA-03 | Quality check blocks bad data from scoring pipeline | integration | `pytest tests/integration/test_data_ingest.py::test_pipeline_quality_failure -x` | Exists |
| DATA-04 | pykrx adapter fetches KOSPI/KOSDAQ OHLCV | unit | `pytest tests/unit/test_pykrx_client.py -x` | Wave 0 |
| DATA-05 | pykrx adapter fetches Korean fundamentals (PER/PBR/DIV) | unit | `pytest tests/unit/test_pykrx_client.py -x` | Wave 0 |
| DATA-04/05 | ingest --market kr CLI end-to-end | unit | `pytest tests/unit/test_cli_ingest_kr.py -x` | Wave 0 |
| DATA-06 | Regime data (VIX, S&P, yield) stored in DuckDB | unit | `pytest tests/unit/test_regime_data_store.py -x` | Wave 0 |
| DATA-06 | Regime data table schema + queries | unit | `pytest tests/unit/test_duckdb_store.py -x` | Exists (needs extension) |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_quality_checker.py tests/unit/test_yfinance_adapter.py tests/unit/test_edgartools_client.py tests/unit/test_duckdb_store.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_pykrx_client.py` -- covers DATA-04, DATA-05 (pykrx OHLCV + fundamentals)
- [ ] `tests/unit/test_cli_ingest_kr.py` -- covers DATA-04/05 CLI integration (ingest --market kr)
- [ ] `tests/unit/test_regime_data_store.py` -- covers DATA-06 (regime data DuckDB storage)
- [ ] Framework install: `pip install pykrx` -- pykrx not yet in dependencies

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `src/data_ingest/` complete directory structure and all files
- `core/data/client.py` -- yfinance integration with auto_adjust=True on line 82
- `core/data/market.py` -- regime data fetching (VIX, S&P 500, yield curve)
- `src/data_ingest/infrastructure/edgartools_client.py` -- known ticker bug line 154
- `src/data_ingest/domain/value_objects.py` -- Ticker VO regex `^[A-Z]{1,10}$`
- `src/data_ingest/infrastructure/quality_checker.py` -- complete quality validation
- `.planning/research/PITFALLS.md` -- Pitfall 5 (Korean market assumptions), Pitfall 10 (data source limitations)
- pyproject.toml -- dependencies (yfinance 1.2.0, edgartools 5.23.0 installed; pykrx not installed)

### Secondary (MEDIUM confidence)
- [pykrx GitHub](https://github.com/sharebook-kr/pykrx) -- API documentation and function signatures
- [yfinance auto_adjust behavior](https://softhints.com/understanding-yfinance-auto_adjust-true-what-changed-and-how-to-fix-it/) -- auto_adjust=True changes in 0.2.28+
- [edgartools XBRL improvements](https://www.edgartools.io/i-learnt-xbrl-mappings-from-32-000-sec-filings/) -- 234 standardized concepts from 32,240 filings
- [yfinance issue #2340](https://github.com/ranaroussi/yfinance/issues/2340) -- resolved; Yahoo Finance data still free (was ad-blocker/rate-limit issue)

### Tertiary (LOW confidence)
- pykrx column names (Korean vs English) -- needs empirical validation during implementation
- pykrx rate limiting behavior -- 1 second recommended delay from docs, but actual server response unverified
- edgartools small-cap XBRL coverage -- improved but not empirically validated for this system's target tickers

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries are already installed/tested except pykrx which has well-documented API
- Architecture: HIGH -- existing pipeline architecture is proven; extensions follow established patterns
- Pitfalls: HIGH -- identified from direct codebase analysis and PITFALLS.md research
- Korean market data: MEDIUM -- pykrx API is documented but column names and edge cases need empirical validation

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable libraries, no fast-moving changes expected)
