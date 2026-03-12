# Phase 1: Data Foundation - Research

**Researched:** 2026-03-12
**Domain:** Financial data ingestion, storage, quality validation, point-in-time correctness
**Confidence:** HIGH

## Summary

Phase 1 builds the data backbone: ingest US equity prices (yfinance) and SEC financial statements (edgartools), store in a dual-DB architecture (DuckDB for analytics, SQLite for operations), enforce point-in-time correctness via SEC filing dates, run data quality checks, and verify existing safety gate scores (Altman Z, Beneish M, Piotroski F).

The existing codebase already has a working `DataClient` (yfinance prices), SQLite cache, and scoring functions (F/Z/M-Score). These must be **wrapped** in DDD-compliant infrastructure adapters, not rewritten. The major new work is: edgartools SEC client (filing date tracking), DuckDB analytical store, universe management (S&P 500+400 minus Financials/Utilities), data quality pipeline, and an async event bus.

**Primary recommendation:** Wrap existing `core/` code via thin adapter classes in `src/data_ingest/infrastructure/`, add edgartools for SEC data with filing_date as the primary temporal key, use DuckDB's columnar engine for analytical queries, and validate all data through a quality gate before downstream consumption.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Universe**: S&P 500 + S&P 400 (~900 tickers), exclude Financials + Utilities, weekly update, GICS 11 sectors
- **Data sources**: yfinance (prices only) + edgartools (SEC financials with filing dates) + asyncio parallel (5-10 concurrent)
- **Code strategy**: wrap core/ functions, lightweight DDD (domain/VOs + infrastructure/clients only, no handlers)
- **Event bus**: async (asyncio-based)
- **Point-in-time**: fully strict (SEC filing date mandatory, as-of-date filter on all queries)
- **Quality checks**: core validation (missing values, stale 3+ days, outliers 3 sigma+), exclude + log incomplete tickers
- **DB**: DuckDB (analytical) + SQLite (operational)
- **Existing code**: core/data/client.py WRAP, core/scoring/fundamental.py REUSE, core/scoring/safety.py REUSE

### Claude's Discretion
- Async concurrency implementation details (semaphore size, retry strategy)
- DuckDB schema design (table structure, partitioning)
- Data quality report format
- Universe source (Wikipedia scraping vs static list vs API)

### Deferred Ideas (OUT OF SCOPE)
- EODHD paid data source (removed, yfinance only for prices)
- Full DDD with handlers/commands/queries for data_ingest (lightweight only)
- Synchronous event bus (async decided)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | OHLCV data collection -- yfinance 3+ years daily price data | Existing DataClient wrapping + yfinance auto_adjust awareness |
| DATA-02 | Financial statements -- edgartools SEC data (income, balance sheet, cash flow) | edgartools 5.23.0 API with filing_date + MultiFinancials + XBRL |
| DATA-03 | Data cache/storage -- DuckDB (analytical) + SQLite (operational) dual-DB | DuckDB 1.5.0 persistent file + existing SQLite cache wrapping |
| DATA-04 | Data quality validation -- missing values, outliers, stale data, point-in-time | 3-sigma outlier detection + stale check + filing_date enforcement |
| SCOR-01 | Safety Gate -- Altman Z > 1.81 AND Beneish M < -1.78 hard gate | Existing core/scoring/safety.py reuse via adapter |
| SCOR-02 | Piotroski F-Score (0-9) | Existing core/scoring/fundamental.py piotroski_f_score() reuse |
| SCOR-03 | Altman Z-Score calculation | Existing core/scoring/safety.py altman_z_score() reuse |
| SCOR-04 | Beneish M-Score calculation | Existing core/scoring/safety.py beneish_m_score() reuse |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | >=0.2.36 | OHLCV price data from Yahoo Finance | Free, widely used, existing DataClient depends on it |
| edgartools | >=5.23.0 | SEC EDGAR financial statements with filing dates | Only free Python lib with XBRL standardization + filing_date tracking |
| duckdb | >=1.5.0 | Analytical DB for screening 500+ tickers | Columnar in-process, no server, SQL on DataFrames, sub-second aggregations |
| pandas | >=2.0 | Data manipulation, DataFrame interchange | Industry standard, already in project |
| numpy | >=1.26 | Numerical operations | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio | stdlib | Concurrent data fetching (5-10 parallel) | All data ingestion pipelines |
| aiohttp | >=3.9 | Async HTTP client for yfinance/edgartools parallelism | If edgartools doesn't natively support asyncio (wrap sync in executor) |
| sqlite3 | stdlib | Operational state (watchlists, logs, cache) | Existing cache.py already uses this |
| pydantic | >=2.0 | Data validation for API responses | Already in project, use for config/settings |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| edgartools | sec-api, secedgar | edgartools is free, has XBRL standardization, filing_date tracking; alternatives either paid or less featured |
| DuckDB | PostgreSQL, ClickHouse | DuckDB is in-process (no server), perfect for single-user analytical queries; Postgres needs server |
| Wikipedia scraping for universe | Static CSV, paid API | Wikipedia has both S&P 500 and S&P 400 lists with GICS sectors; free, auto-updated |

**Installation:**
```bash
pip install edgartools>=5.23.0 duckdb>=1.5.0 aiohttp>=3.9
```

(yfinance, pandas, numpy, pydantic already in requirements.txt)

## Architecture Patterns

### Recommended Project Structure
```
src/
  data_ingest/                    # NEW bounded context (lightweight DDD)
    domain/
      value_objects.py            # Ticker, OHLCV, FinancialStatement, FilingDate, DataQualityReport
      events.py                   # DataIngestedEvent, QualityCheckFailedEvent
      __init__.py                 # Public API
    infrastructure/
      yfinance_client.py          # Wraps core/data/client.py DataClient
      edgartools_client.py        # NEW: SEC filing data with filing_date
      duckdb_store.py             # NEW: Analytical storage
      sqlite_store.py             # Wraps core/data/cache.py
      universe_provider.py        # NEW: S&P 500+400 ticker management
      quality_checker.py          # NEW: Data quality validation pipeline
      __init__.py
    DOMAIN.md
  scoring/                        # EXISTING bounded context
    domain/
      value_objects.py            # Existing SafetyGate, FundamentalScore, etc.
      ...
    infrastructure/
      core_scoring_adapter.py     # NEW: Wraps core/scoring/ functions
      __init__.py
  shared/
    domain/                       # EXISTING: Entity, ValueObject, DomainEvent, Result
    infrastructure/
      event_bus.py                # NEW: Async in-process event bus
```

### Pattern 1: Core Wrapping (Adapter Pattern)
**What:** Thin adapter classes that import and delegate to existing `core/` functions
**When to use:** For all existing code reuse (DataClient, scoring functions, cache)
**Example:**
```python
# src/data_ingest/infrastructure/yfinance_client.py
from core.data.client import DataClient as CoreDataClient

class YFinanceClient:
    """DDD infrastructure adapter wrapping core DataClient."""

    def __init__(self) -> None:
        self._client = CoreDataClient()  # uses yfinance internally

    async def fetch_ohlcv(self, ticker: str, days: int = 756) -> pd.DataFrame:
        """Fetch OHLCV data. Runs sync core client in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._client.get_price_history, ticker, days)
```

### Pattern 2: Point-in-Time Financial Data
**What:** Every financial data record tagged with SEC filing_date, not period_of_report
**When to use:** All financial statement storage and queries
**Example:**
```python
# src/data_ingest/domain/value_objects.py
@dataclass(frozen=True)
class FinancialStatement(ValueObject):
    """Financial statement with point-in-time awareness."""
    ticker: str
    period_end: date        # e.g., 2025-09-30 (fiscal quarter end)
    filing_date: date       # e.g., 2025-11-01 (SEC filing date -- THIS is the usable date)
    form_type: str          # "10-Q" or "10-K"
    # ... financial data fields

    def _validate(self) -> None:
        if self.filing_date < self.period_end:
            raise ValueError("filing_date cannot precede period_end")
```

### Pattern 3: Async Concurrent Ingestion with Semaphore
**What:** asyncio.Semaphore limits concurrent API calls to 5-10
**When to use:** Batch ingestion of 900 tickers
**Example:**
```python
# src/data_ingest/infrastructure/pipeline.py
import asyncio

class DataPipeline:
    def __init__(self, max_concurrent: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def ingest_ticker(self, ticker: str) -> None:
        async with self._semaphore:
            ohlcv = await self._yfinance.fetch_ohlcv(ticker)
            financials = await self._edgartools.fetch_financials(ticker)
            quality = self._checker.validate(ohlcv, financials)
            if quality.passed:
                await self._duckdb.store(ticker, ohlcv, financials)
            else:
                self._logger.warning(f"Excluded {ticker}: {quality.failures}")

    async def ingest_universe(self, tickers: list[str]) -> None:
        tasks = [self.ingest_ticker(t) for t in tickers]
        await asyncio.gather(*tasks, return_exceptions=True)
```

### Pattern 4: Dual-DB Separation
**What:** DuckDB for analytical queries, SQLite for operational state
**When to use:** All data storage decisions
**Rules:**
- DuckDB: OHLCV history, financial statements, screening queries (read-heavy, columnar)
- SQLite: Cache TTL, watchlists, ingestion logs, pipeline state (write-heavy, row-oriented)
- Never query SQLite for analytics, never use DuckDB for operational state

### Anti-Patterns to Avoid
- **Rewriting core/ functions:** WRAP them, never rewrite. The scoring math is tested and validated.
- **Storing period_end as the query date:** Always use filing_date for as-of queries. Period_end creates look-ahead bias.
- **Full DDD for data_ingest:** This context is lightweight (VOs + infra only). No application layer, no handlers, no commands/queries.
- **Synchronous batch ingestion:** 900 tickers sequentially would take hours. Use asyncio with semaphore.
- **Single DB:** DuckDB excels at analytical queries but is not ideal for high-frequency operational writes. Keep SQLite for cache/logs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SEC EDGAR parsing | Custom XBRL parser | edgartools `Company.get_financials()` | XBRL standardization covers 32,000+ filing patterns; 6+ months of work to replicate |
| S&P 500/400 ticker list | Manual CSV maintenance | Wikipedia scraping via `pd.read_html()` | Auto-updated, includes GICS sectors, 5 lines of code |
| Columnar analytics engine | Custom pandas aggregation loops | DuckDB SQL queries on stored data | DuckDB is 10-100x faster than pandas for grouped aggregations on 500+ tickers |
| Financial data quality checks | Custom validation from scratch | Structured validation pipeline with numpy (mean +/- 3 sigma) | Standard statistical approach; pandas/numpy already handle edge cases |
| Async concurrency control | Custom thread pool | `asyncio.Semaphore` + `run_in_executor` | stdlib, well-tested, handles backpressure correctly |
| Filing date extraction | Manual SEC page scraping | edgartools `filing.filing_date` property | edgartools parses SGML headers, handles edge cases (amendments, restatements) |

**Key insight:** The hardest part of this phase is SEC data with filing dates. edgartools is the only free Python library that provides this. Don't attempt to parse EDGAR directly.

## Common Pitfalls

### Pitfall 1: yfinance auto_adjust Breaking Change
**What goes wrong:** yfinance 0.2.28+ defaults `auto_adjust=True`, removing the `Adj Close` column and adjusting OHLCV directly. Existing `DataClient._yfinance_price()` uses `auto_adjust=True` already, but downstream code may expect `adj_close` column.
**Why it happens:** Breaking change in February 2025.
**How to avoid:** The existing DataClient already uses `auto_adjust=True` in `ticker.history()`. Verify the preprocessor still works (it checks for `adj_close` column which won't exist). The `preprocess_ohlcv()` function handles this gracefully (the `adj_close` check is a no-op when absent).
**Warning signs:** Missing `adj_close` column errors, unexpected price values.

### Pitfall 2: edgartools Filing Date vs Period of Report
**What goes wrong:** Using `period_of_report` (fiscal quarter end) instead of `filing_date` (SEC submission date) for as-of queries, creating look-ahead bias.
**Why it happens:** Period end dates look more "natural" to query by. A company's Q3 ends Sep 30 but files Nov 1 -- the data wasn't available until Nov 1.
**How to avoid:** Store BOTH dates, but ONLY filter by `filing_date` in all downstream queries. The `filing_date` from edgartools `Filing` object is the authoritative date.
**Warning signs:** Abnormally high backtest returns, scoring using data before it was publicly available.

### Pitfall 3: edgartools XBRL Coverage Gaps for Smaller Companies
**What goes wrong:** Some S&P 400 (mid-cap) companies may have incomplete or non-standard XBRL filings.
**Why it happens:** XBRL standardization depends on filing quality; smaller companies sometimes use non-standard taxonomies.
**How to avoid:** Implement fallback: try edgartools XBRL first, fall back to yfinance `ticker.quarterly_financials` for basic data (without filing_date). Log the fallback for visibility. Accept that fallback data lacks filing_date precision.
**Warning signs:** `None` returns from `Company.get_financials()`, missing balance sheet items.

### Pitfall 4: DuckDB Concurrent Access
**What goes wrong:** DuckDB allows only ONE writer at a time. Multiple async tasks writing simultaneously will deadlock or error.
**Why it happens:** DuckDB is designed for analytical (read-heavy) workloads, not OLTP.
**How to avoid:** Batch all writes: collect data in memory (or temp list), then write to DuckDB in a single transaction after all tickers are fetched. Use SQLite for intermediate operational writes.
**Warning signs:** `duckdb.IOException`, hanging writes, lock contention errors.

### Pitfall 5: Wikipedia S&P 400 Table Structure Differences
**What goes wrong:** S&P 400 Wikipedia page may have different column names or table structure than S&P 500 page.
**Why it happens:** Wikipedia editors maintain each list independently.
**How to avoid:** Validate column names after `pd.read_html()`, normalize to a standard schema (symbol, name, sector). Test with both pages before hardcoding column indices.
**Warning signs:** KeyError on column access, empty dataframes.

### Pitfall 6: Rate Limiting from SEC EDGAR
**What goes wrong:** SEC EDGAR enforces 10 requests/second. Exceeding this causes IP-level blocking.
**Why it happens:** edgartools handles caching but parallel requests can overwhelm the limit.
**How to avoid:** Set semaphore to 5 (conservative). edgartools has built-in rate-limiting ("rate-limit aware" per docs), but add a small delay (0.2s) between requests as insurance. Set SEC-required User-Agent header.
**Warning signs:** HTTP 403/429 errors, IP blocks from SEC.

## Code Examples

Verified patterns from official sources and existing codebase:

### edgartools: Get Financial Statements with Filing Date
```python
# Source: edgartools docs (https://edgartools.readthedocs.io/en/latest/guides/extract-statements/)
from edgar import Company

company = Company("AAPL")

# Get multiple quarters of financials
filings = company.get_filings(form="10-Q").head(12)  # ~3 years of quarterly

for filing in filings:
    filing_date = filing.filing_date     # SEC submission date (point-in-time key)
    period_end = filing.period_of_report  # Fiscal quarter end

    tenq = filing.obj()
    if tenq and tenq.financials:
        income = tenq.financials.income_statement()
        balance = tenq.financials.balance_sheet
        cashflow = tenq.financials.cashflow_statement()
```

### edgartools: Standardized Financial Metrics
```python
# Source: edgartools docs (https://edgartools.readthedocs.io/en/latest/guides/extract-statements/)
from edgar import Company

company = Company("AAPL")
financials = company.get_financials()

# Standardized getters (cross-company comparable)
revenue = financials.get_revenue()
net_income = financials.get_net_income()
total_assets = financials.get_total_assets()
operating_cf = financials.get_operating_cash_flow()
free_cf = financials.get_free_cash_flow()

# Historical comparison
current_rev = financials.get_revenue(0)   # Most recent
prev_rev = financials.get_revenue(1)      # Previous period
```

### DuckDB: Create Persistent Database and Query
```python
# Source: DuckDB docs (https://duckdb.org/docs/stable/clients/python/overview)
import duckdb

con = duckdb.connect("data/analytics.duckdb")  # Persistent file

# Create tables
con.execute("""
    CREATE TABLE IF NOT EXISTS ohlcv (
        ticker VARCHAR,
        date DATE,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume BIGINT,
        PRIMARY KEY (ticker, date)
    )
""")

con.execute("""
    CREATE TABLE IF NOT EXISTS financials (
        ticker VARCHAR,
        period_end DATE,
        filing_date DATE,
        form_type VARCHAR,
        revenue DOUBLE,
        net_income DOUBLE,
        total_assets DOUBLE,
        total_liabilities DOUBLE,
        working_capital DOUBLE,
        retained_earnings DOUBLE,
        ebit DOUBLE,
        operating_cashflow DOUBLE,
        free_cashflow DOUBLE,
        current_ratio DOUBLE,
        debt_to_equity DOUBLE,
        roa DOUBLE,
        roe DOUBLE,
        PRIMARY KEY (ticker, period_end, form_type)
    )
""")

# Insert from DataFrame
con.execute("INSERT INTO ohlcv SELECT * FROM df_ohlcv")

# Analytical query: screen 500+ tickers
result = con.execute("""
    SELECT f.ticker, f.revenue, f.net_income, f.total_assets,
           o.close as latest_price
    FROM financials f
    JOIN (
        SELECT ticker, close, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
        FROM ohlcv
    ) o ON f.ticker = o.ticker AND o.rn = 1
    WHERE f.filing_date <= CURRENT_DATE  -- point-in-time filter
      AND f.filing_date = (
          SELECT MAX(f2.filing_date) FROM financials f2
          WHERE f2.ticker = f.ticker AND f2.filing_date <= CURRENT_DATE
      )
""").fetchdf()
```

### Universe Management: Wikipedia Scraping
```python
# Source: Wikipedia + pandas (standard pattern)
import pandas as pd

def get_sp500_tickers() -> pd.DataFrame:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0][["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]]
    return df.rename(columns={
        "Symbol": "ticker", "Security": "name",
        "GICS Sector": "sector", "GICS Sub-Industry": "sub_industry",
    })

def get_sp400_tickers() -> pd.DataFrame:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
    tables = pd.read_html(url)
    df = tables[0]
    # Column names may differ -- normalize
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    return df

def get_universe() -> pd.DataFrame:
    sp500 = get_sp500_tickers()
    sp400 = get_sp400_tickers()
    combined = pd.concat([sp500, sp400], ignore_index=True)
    # Exclude Financials and Utilities
    excluded_sectors = {"Financials", "Utilities"}
    return combined[~combined["sector"].isin(excluded_sectors)]
```

### Async Event Bus (Simple In-Process)
```python
# Source: Python asyncio stdlib pattern
import asyncio
from collections import defaultdict
from typing import Callable, Any
from src.shared.domain import DomainEvent

class AsyncEventBus:
    """Simple async in-process event bus for bounded context communication."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: Callable) -> None:
        self._handlers[event_type.__name__].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        event_name = event.__class__.__name__
        for handler in self._handlers.get(event_name, []):
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
```

### Data Quality Validation
```python
# Source: Standard statistical validation pattern
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class QualityReport:
    ticker: str
    passed: bool
    missing_pct: float
    stale_days: int
    outlier_count: int
    failures: list[str]

def validate_ohlcv(ticker: str, df: pd.DataFrame, max_stale_days: int = 3) -> QualityReport:
    failures = []

    # Missing values
    missing_pct = df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100
    if missing_pct > 5.0:
        failures.append(f"Missing values: {missing_pct:.1f}%")

    # Stale data (days since last record)
    last_date = df.index.max()
    stale_days = (pd.Timestamp.now().normalize() - last_date).days
    if stale_days > max_stale_days:
        failures.append(f"Stale data: {stale_days} days since last update")

    # Outliers (3-sigma)
    outlier_count = 0
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            mean, std = df[col].mean(), df[col].std()
            outliers = ((df[col] - mean).abs() > 3 * std).sum()
            outlier_count += outliers
    if outlier_count > len(df) * 0.01:  # >1% outliers
        failures.append(f"Excessive outliers: {outlier_count}")

    return QualityReport(
        ticker=ticker,
        passed=len(failures) == 0,
        missing_pct=missing_pct,
        stale_days=stale_days,
        outlier_count=outlier_count,
        failures=failures,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance auto_adjust=False default | auto_adjust=True default | Feb 2025 (v0.2.28) | Existing DataClient already uses auto_adjust=True, no impact |
| Manual XBRL parsing | edgartools XBRL standardization from 32K filings | 2025 (v5.22+) | No need to build custom XBRL parser |
| Pandas-only analytics | DuckDB SQL on persistent columnar store | DuckDB 1.0+ (2024) | 10-100x faster for multi-ticker screening |
| EODHD as primary data source | yfinance (prices) + edgartools (financials) | Project decision 2026-03-12 | No paid API key needed, SEC data is authoritative |

**Deprecated/outdated:**
- EODHD integration in DataClient: still in code but user decided yfinance-only for prices
- `adj_close` column handling in preprocessor: auto_adjust=True means no separate adj_close column, but preprocessor handles this gracefully

## Open Questions

1. **edgartools Rate Limiting Behavior Under Parallel Load**
   - What we know: edgartools claims "rate-limit aware" and "smart caching"
   - What's unclear: Exact behavior when 5-10 concurrent requests hit SEC EDGAR
   - Recommendation: Start with semaphore=5, add 0.2s delay, monitor for 429 errors. Increase if stable.

2. **S&P 400 Wikipedia Table Reliability**
   - What we know: S&P 500 Wikipedia scraping is well-established; S&P 400 less documented
   - What's unclear: Whether the S&P 400 Wikipedia page has consistent table structure
   - Recommendation: Test `pd.read_html()` on the S&P 400 page early. Fallback: use a static CSV with periodic manual updates.

3. **edgartools XBRL Coverage for Mid-Cap Stocks**
   - What we know: Works well for large-cap (S&P 500). Mid-cap (S&P 400) coverage is untested.
   - What's unclear: What percentage of S&P 400 companies have parseable XBRL financials
   - Recommendation: Sample-test 20 random S&P 400 tickers in Wave 0. If >90% coverage, proceed; otherwise implement yfinance fallback for financial data.

4. **DuckDB File Size for 3+ Years of 900 Tickers**
   - What we know: ~900 tickers x 756 trading days x 6 columns (OHLCV + volume) = ~4M rows for prices
   - What's unclear: Exact file size and query performance at this scale
   - Recommendation: DuckDB handles this trivially (sub-GB file, sub-second queries). Not a real concern but validate during implementation.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 7.4 + pytest-asyncio >= 0.21 |
| Config file | `trading/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd C:/workspace/trading && python -m pytest tests/unit/ -x -q` |
| Full suite command | `cd C:/workspace/trading && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | yfinance OHLCV 3+ years fetch | integration | `pytest tests/integration/test_data_ingest.py::test_ohlcv_fetch -x` | No -- Wave 0 |
| DATA-02 | edgartools SEC financials with filing_date | integration | `pytest tests/integration/test_data_ingest.py::test_sec_financials -x` | No -- Wave 0 |
| DATA-03 | DuckDB + SQLite dual storage | unit | `pytest tests/unit/test_duckdb_store.py -x` | No -- Wave 0 |
| DATA-04 | Data quality checks (missing/stale/outlier) | unit | `pytest tests/unit/test_quality_checker.py -x` | No -- Wave 0 |
| SCOR-01 | Safety gate Z > 1.81 AND M < -1.78 | unit | `pytest tests/unit/test_scoring_safety.py -x` | Yes -- existing |
| SCOR-02 | Piotroski F-Score 0-9 | unit | `pytest tests/unit/test_scoring_fundamental.py -x` | Yes -- existing |
| SCOR-03 | Altman Z-Score calculation | unit | `pytest tests/unit/test_scoring_safety.py::test_altman_healthy_company -x` | Yes -- existing |
| SCOR-04 | Beneish M-Score calculation | unit | `pytest tests/unit/test_scoring_safety.py::test_beneish_clean_company -x` | Yes -- existing |

### Sampling Rate
- **Per task commit:** `cd C:/workspace/trading && python -m pytest tests/unit/ -x -q`
- **Per wave merge:** `cd C:/workspace/trading && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_duckdb_store.py` -- covers DATA-03
- [ ] `tests/unit/test_quality_checker.py` -- covers DATA-04
- [ ] `tests/unit/test_edgartools_client.py` -- covers DATA-02 (unit with mocks)
- [ ] `tests/unit/test_universe_provider.py` -- covers universe management
- [ ] `tests/unit/test_event_bus.py` -- covers async event bus
- [ ] `tests/unit/test_yfinance_adapter.py` -- covers DATA-01 adapter wrapping
- [ ] `tests/integration/test_data_ingest.py` -- covers DATA-01 + DATA-02 end-to-end
- [ ] `tests/unit/test_core_scoring_adapter.py` -- covers SCOR-01~04 adapter wrapping
- [ ] Framework install: `pip install duckdb>=1.5.0 edgartools>=5.23.0 aiohttp>=3.9` -- new dependencies

*(Existing tests for SCOR-01~04 already pass via core/scoring/ -- new adapter tests verify DDD wrapping)*

## Sources

### Primary (HIGH confidence)
- [edgartools PyPI](https://pypi.org/project/edgartools/) -- v5.23.0, Python >=3.10, filing_date + XBRL
- [edgartools Docs: Extract Statements](https://edgartools.readthedocs.io/en/latest/guides/extract-statements/) -- MultiFinancials, XBRL, DataFrame output
- [edgartools Docs: Filing API](https://edgartools.readthedocs.io/en/latest/api/filing/) -- filing_date, period_of_report properties
- [edgartools GitHub](https://github.com/dgunning/edgartools) -- Repository, examples, XBRL standardization from 32K filings
- [DuckDB Docs: Python API](https://duckdb.org/docs/stable/clients/python/overview) -- v1.5.0, persistent DB, DataFrame integration
- [DuckDB Docs: Import from Pandas](https://duckdb.org/docs/stable/guides/python/import_pandas) -- Direct DataFrame reference in SQL
- [DuckDB Announcement 1.5.0](https://duckdb.org/2026/03/09/announcing-duckdb-150) -- Latest stable version
- Existing codebase: `core/data/client.py`, `core/scoring/safety.py`, `core/scoring/fundamental.py` -- verified via file reads

### Secondary (MEDIUM confidence)
- [yfinance auto_adjust change](https://softhints.com/understanding-yfinance-auto_adjust-true-what-changed-and-how-to-fix-it/) -- auto_adjust=True default in v0.2.28+
- [Wikipedia S&P 500 list](https://en.wikipedia.org/wiki/List_of_S&P_500_companies) -- ticker + GICS sector data
- [asyncio Semaphore pattern](https://medium.com/@mr.sourav.raj/mastering-asyncio-semaphores-in-python-a-complete-guide-to-concurrency-control-6b4dd940e10e) -- concurrency control pattern

### Tertiary (LOW confidence)
- S&P 400 Wikipedia scraping reliability -- not directly verified, needs testing
- edgartools XBRL coverage for S&P 400 mid-caps -- claimed but untested for this specific universe

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified via PyPI and official docs with current versions
- Architecture: HIGH -- patterns based on existing codebase structure (DDD), existing shared domain classes, and well-established adapter patterns
- Pitfalls: HIGH -- yfinance breaking change documented widely, DuckDB write limitations documented, SEC rate limits well-known
- edgartools API: MEDIUM -- docs verified but actual XBRL coverage for mid-caps is untested
- S&P 400 universe source: LOW -- Wikipedia scraping not tested for this specific page

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (30 days -- libraries are stable, edgartools updates frequently but API is stable)
