# Technology Stack

**Project:** Intrinsic Alpha Trader
**Researched:** 2026-03-12
**Overall confidence:** HIGH

## Recommended Stack

### Python Runtime & Project Management

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12.x | Runtime | NumPy 2.4 requires >=3.11. Python 3.12 is the sweet spot: stable, all financial libs tested against it, no C-extension edge cases. 3.13 is compatible but 3.12 has the deepest testing coverage across the ecosystem. edgartools requires >=3.10. | HIGH |
| uv | >=0.10.9 | Package/project manager | 10-100x faster than pip (cold install: ~3s vs pip-tools ~33s). Lockfile support, venv management, Python version management. 2026 community consensus for new projects. Replaces pip + venv + pip-tools. Same team as Ruff (Astral). | HIGH |

### Data Acquisition

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| yfinance | >=1.2.0 | OHLCV + fundamentals | Free, no API key, covers price data + financial statements + earnings calendars + balance sheets. v1.0+ (Dec 2025) is a major rewrite with better architecture. De facto standard for retail quant. Returns pandas DataFrames natively. | HIGH |
| edgartools | >=5.23.0 | SEC EDGAR filings | Best-in-class SEC parser as of 2026. No API key, no rate limits, no subscriptions. Parses 10-K/10-Q/8-K XBRL into structured Python objects and DataFrames. Supports all SEC form types. Built-in MCP server for Claude integration. v5.0 complete HTML parser rewrite. Released 2026-03-11. Requires Python >=3.10. | HIGH |
| alpaca-py | >=0.43.2 | Broker API (market data + trading) | Official Alpaca SDK. OOP design with pydantic validation. Covers Trading API + Market Data API in a single package. Paper trading built-in (base URL switch). Free tier sufficient for daily screening. Supports Python 3.8-3.14. | HIGH |

### Data Processing & Analysis

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pandas | >=2.2.0,<3.0 | Core data manipulation | Industry standard for financial time series. All upstream libs (yfinance, vectorbt, edgartools, quantstats) return DataFrames. **Pin to <3.0 for V1** -- pandas 3.0 (Jan 2026) introduces breaking Copy-on-Write semantics and string dtype changes. VectorBT and QuantStats have known compatibility issues with 3.0. Migrate to 3.x after upstream libs confirm support. | HIGH |
| numpy | >=2.0.0,<2.4 | Numerical computation | Foundation for all scientific Python. Required by pandas, vectorbt, scipy. **Pin below 2.4 to stay compatible with pandas <3.0.** NumPy 2.4.3 requires Python >=3.11 which is fine, but its release timeline aligns with pandas 3.0. Use 2.2.x for maximum stability. | HIGH |
| scipy | >=1.14.0 | Statistical functions | WACC calculations, probability distributions for Kelly criterion (scipy.stats.norm), optimization for portfolio weights (scipy.optimize.minimize_scalar), integration (scipy.integrate.quad). No alternative for this breadth of statistical tools. | HIGH |

**CRITICAL: pandas 3.0 migration risk.** Pandas 3.0 (released Jan 21, 2026) introduces Copy-on-Write as default and new string dtype inference. VectorBT, QuantStats, and other financial libs have documented compatibility issues. The safe path for V1 is to pin pandas <3.0. Plan migration for V2 after upstream ecosystem catches up. First upgrade to pandas 2.3 to get deprecation warnings, then to 3.0.

### Data Storage

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| DuckDB | >=1.5.0 | Primary analytical database | Columnar storage is 10-50x faster than SQLite for aggregation queries (screening 3000+ stocks, computing financial ratios, window functions). Zero-copy pandas integration. Single file, no server. Native Parquet read/write. SQL interface. Released 2026-03-09. | HIGH |
| SQLite | built-in | Operational data store | Zero-dependency (Python stdlib). Best for transactional CRUD: watchlists, trade plans, execution logs, audit trail. Use for row-level read/write, not analytics. | HIGH |

**Rationale for dual-database architecture:** DuckDB for OLAP (analytical queries: stock screening, ratio calculations, backtesting data), SQLite for OLTP (operational state: watchlists, trade plans, execution logs). Both are embedded, single-file, zero-config -- identical deployment simplicity. The project constraint mentions SQLite, but daily screening of 3000+ stocks with financial ratios is an OLAP workload where DuckDB is 10-50x faster.

### Backtesting & Performance Analytics

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| vectorbt | >=0.28.0 | Strategy backtesting | Fastest Python backtester: vectorized NumPy/Numba execution (1M simulated orders in ~70-100ms). Native pandas integration. Portfolio-level analysis with Sharpe, Sortino, max drawdown built-in. Plotly visualization. Best for systematic fundamental strategies with daily bars. | MEDIUM |
| quantstats | >=0.0.81 | Portfolio analytics & reporting | Comprehensive tear sheet generation (HTML reports). Sharpe, Sortino, Calmar ratios, drawdown analysis, monthly returns heatmap, Monte Carlo simulation. Complements vectorbt for performance reporting. Same author as yfinance (Ran Aroussi). | MEDIUM |

**VectorBT maintenance risk (MEDIUM confidence):** The free open-source version (0.28.x) is in maintenance mode -- only critical fixes, no new features. Active development has moved to VectorBT PRO (paid). For V1, the free version is sufficient for daily-bar fundamental backtesting. If the project outgrows it, evaluate VectorBT PRO or custom vectorized backtesting with NumPy. Pin pandas <3.0 to avoid known compatibility issues.

**Why not Backtrader:** Event-driven architecture is overkill for daily-bar fundamental strategies. No active development since ~2018. VectorBT is 10-100x faster for batch backtesting.

**Why not Zipline:** Legacy Quantopian framework. Installation issues on modern Python. Active community has moved on.

**Walk-forward validation:** No off-the-shelf library handles this well for fundamental strategies. Implement custom walk-forward with rolling train/test windows using vectorbt's core portfolio simulation. The pattern is: train scoring weights on N years, validate on next year, roll forward. ~200-300 lines of custom code on top of vectorbt.

### Broker Integration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| alpaca-py | >=0.43.2 | Order execution + paper trading | Single SDK covers market data + trading. Paper trading by switching base URL. Pydantic models for type-safe order construction (MarketOrderRequest, LimitOrderRequest, StopOrderRequest, TrailingStopOrderRequest). Free tier includes real-time market data for 5000+ US stocks. | HIGH |

### Scoring & Valuation (Custom Implementation)

No production-quality library exists for the specific scoring ensemble. API services (Financial Modeling Prep, EODHD) provide pre-calculated scores but introduce paid dependencies and remove explainability. Custom implementation ensures full control over every calculation step -- critical for the "every recommendation must be traceable" constraint.

| Component | Complexity | Dependencies | Why Custom | Confidence |
|-----------|-----------|--------------|------------|------------|
| Piotroski F-Score | Low (~80 lines) | pandas | 9-point binary scoring from financial statements. Pure arithmetic on balance sheet / income / cash flow data. | HIGH |
| Altman Z-Score | Low (~40 lines) | pandas | 5-ratio weighted formula. Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E. Pure math. | HIGH |
| Beneish M-Score | Low (~60 lines) | pandas | 8-variable formula for earnings manipulation detection. Pure math. | HIGH |
| Mohanram G-Score | Low (~80 lines) | pandas | 8-point binary scoring for growth stocks. Pure math on financial data. | HIGH |
| DCF Valuation | Medium (~250 lines) | pandas, scipy | Free cash flow projection + WACC discounting + terminal value. scipy.optimize for sensitivity analysis. | HIGH |
| EPV (Earnings Power) | Low (~60 lines) | pandas | Normalized earnings / cost of capital. Simpler than DCF. | HIGH |
| Relative Valuation | Low (~80 lines) | pandas | P/E, P/B, EV/EBITDA percentile ranking against sector peers. pandas groupby + rank. | HIGH |
| Ensemble Weighting | Medium (~150 lines) | pandas, scipy | Weighted average of all models with configurable weights. scipy for optimization of ensemble weights during backtesting. | HIGH |

**Total custom scoring/valuation code:** ~800-1000 lines of well-tested pure Python with pandas. More maintainable than fighting toy library abstractions with hardcoded assumptions.

### Risk Management (Custom Implementation)

| Component | Complexity | Dependencies | Why Custom | Confidence |
|-----------|-----------|--------------|------------|------------|
| Fractional Kelly | Low (~60 lines) | scipy | Kelly fraction = (bp - q) / b. scipy.optimize.minimize_scalar for multi-asset Kelly. Use half-Kelly or quarter-Kelly for safety. | HIGH |
| ATR-based Stop Loss | Low (~40 lines) | pandas | Average True Range for volatility-adjusted stops. Pure pandas rolling calculation. | HIGH |
| Portfolio Drawdown Tiers | Medium (~100 lines) | pandas | 10/15/20% drawdown defense protocol. Reduces position sizes at each tier. | HIGH |

### CLI & Dashboard

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Textual | >=8.0.0 | Interactive terminal UI | Full TUI framework built on Rich. Layouts, widgets, data tables, mouse events, CSS-like styling. Perfect for stock ranking dashboard, watchlist management, trade plan review. Async-native. v8.1.1 released 2026-03-10. | HIGH |
| Rich | >=14.0.0 | Terminal formatting | Tables, progress bars, syntax highlighting, panels. Used by Textual under the hood. Also standalone for non-interactive output (reports, CLI output). v14.3.3 released 2026-02-19. | HIGH |
| Typer | >=0.24.0 | CLI argument parsing | Built on Click with type-hint-based API. Auto-generated help, auto-completion, validation from Python type annotations. Modern alternative to Click -- uses Click internally so full backward compatibility. v0.24.1 released 2026-02-21. | HIGH |

**Why Typer over Click:** Typer wraps Click with a type-hint-first API that eliminates decorator boilerplate. Since the project already uses Pydantic (type-hint heavy), Typer's approach is consistent. You can still drop down to raw Click when needed.

**Why Textual over Streamlit:** Project scope explicitly states "CLI first, Streamlit in v2." Textual delivers interactive dashboards in the terminal without a browser. Faster development loop, no web server dependency.

### Configuration & Settings

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pydantic | >=2.10.0 | Data models & validation | Domain entities, DTOs, API request/response models. v2 rewrite with Rust core is 5-50x faster than v1. Already a dependency of alpaca-py, pydantic-settings, and Typer. | HIGH |
| pydantic-settings | >=2.13.0 | Configuration management | Type-safe config with validation. Reads from .env files + environment variables. Integrates naturally with alpaca-py (also pydantic-based). Catches config errors at startup, not at runtime. v2.13.1 released 2026-02-19. | HIGH |

### Scheduling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| APScheduler | >=3.11.0,<4.0.0 | Daily screening workflow | Cron-style scheduling for daily market screening, monitoring checks, alert evaluation. In-process, lightweight. No external scheduler needed. Production-stable (v3.11.2, Dec 2025). v4 alpha exists but 3.x is the stable choice. | HIGH |

**Why not system cron:** APScheduler keeps scheduling logic co-located with application code. Easier to test, debug, and deploy. Supports missed job recovery and persistence.

### Internal APIs

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI | deferred | Internal REST API | **Not needed for V1** (CLI-only). Reserve for V2 when web dashboard is added. Already listed in project constraints. Will integrate naturally with pydantic models and Typer (same author: tiangolo). | N/A |

**V1 approach:** Direct function calls between modules. No HTTP overhead needed when everything runs in one process. FastAPI adds value only when you need a web UI or external integrations in V2.

### Logging & Observability

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| loguru | >=0.7.3 | Application logging | Zero-config, beautiful output, file rotation/retention built-in. Every trade decision, score calculation, and alert must be logged with full context for auditability. Single `add()` function for configuration. | HIGH |

**Why not structlog:** Structlog excels in distributed systems with log aggregation pipelines (2.6x throughput advantage in async). This is a single-process CLI application -- loguru's simplicity wins. If V2 adds a web API, reconsider structlog.

**Why not stdlib logging:** Verbose configuration, poor defaults. Loguru is a strict upgrade for application logging.

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | >=9.0.0 | Test framework | Industry standard. Fixtures for test data setup. Parametrize for testing scoring logic across multiple stocks. v9.0.2 released 2025-12-06. | HIGH |
| pytest-cov | latest | Coverage reporting | Ensure scoring/valuation logic has >90% coverage. Financial calculation bugs are expensive. | HIGH |
| pytest-mock | latest | Mocking | Mock API calls (yfinance, Alpaca, SEC) in tests. Never hit real APIs in CI. | HIGH |
| pytest-asyncio | latest | Async test support | Required for testing Textual UI and any async data fetching. | HIGH |

### Code Quality

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ruff | >=0.15.0 | Linter + formatter | Replaces flake8 + isort + black in one tool. Written in Rust, 10-100x faster. 800+ built-in lint rules. From same team as uv (Astral). v0.15.5 released 2026-03-05. | HIGH |
| mypy | >=1.19.0 | Type checking | Catch type errors in financial calculations before runtime. Critical for scoring/valuation correctness. Supports Python 3.9-3.14. v1.19.1 released 2025-12-15. | HIGH |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Package manager | uv | Poetry | Poetry is mature but 3-10x slower. uv handles everything Poetry does. Community moving to uv in 2026. |
| Package manager | uv | pip + venv | No lockfile, no dependency resolution, no project management. uv is a drop-in replacement. |
| Data processing | pandas (<3.0) | Polars | Polars is 10-50x faster but ecosystem interop (yfinance, vectorbt, edgartools, quantstats) all assume pandas. Daily data volumes (<10K rows per query) don't need Polars speed. Revisit if batch screening >5000 tickers becomes slow. |
| Data processing | pandas (<3.0) | pandas 3.0 | Copy-on-Write breaking changes + string dtype changes. VectorBT and QuantStats have known issues. Migrate after ecosystem stabilizes (target: V2). |
| Database | DuckDB + SQLite | PostgreSQL | Overkill for single-user CLI application. No server to manage. DuckDB matches analytical performance. |
| Database | DuckDB + SQLite | SQLite only | SQLite is slow for analytical queries (aggregation, window functions across 3000+ rows). DuckDB is purpose-built for OLAP. |
| Backtesting | vectorbt | Backtrader | Event-driven overhead unnecessary for daily-bar fundamental strategies. VectorBT is 10-100x faster. Not actively maintained since ~2018. |
| Backtesting | vectorbt | Zipline | Legacy Quantopian framework. Installation issues on modern Python. Inactive community. |
| Backtesting | vectorbt | backtesting.py (0.6.5) | Lighter weight but less capable for portfolio-level analysis. No walk-forward built-in. VectorBT's portfolio simulation is more complete. |
| CLI framework | Textual + Typer | Streamlit | Project scope says CLI-first. Streamlit requires browser. |
| CLI framework | Textual + Typer | curses | Low-level, no widgets, painful to maintain. Textual is the modern replacement. |
| CLI parsing | Typer | Click | Typer wraps Click with type-hint API. Less boilerplate, same power. Can use Click directly when needed. |
| CLI parsing | Typer | argparse | stdlib but verbose. No auto-completion, poor help generation. |
| Logging | loguru | structlog | Structlog better for distributed/async systems. This is single-process. Loguru is simpler. |
| Logging | loguru | stdlib logging | Verbose configuration, poor defaults. Loguru is a strict upgrade. |
| Linting | ruff | flake8 + black + isort | Three tools vs one. Ruff is 10-100x faster and replaces all three. |
| SEC data | edgartools | sec-api.io | Paid service ($39/mo+). edgartools is free with better structured data output. |
| SEC data | edgartools | sec-edgar-downloader | Only downloads raw files to disk. edgartools parses XBRL into structured Python objects. |
| SEC data | edgartools | OpenBB | OpenBB (4.7.1) is comprehensive but AGPL-licensed. Heavy dependency for just SEC data. Better for full research terminal needs. |
| Portfolio analytics | quantstats | pyfolio | pyfolio is Quantopian legacy, unmaintained. quantstats is actively maintained by yfinance author. |
| Portfolio optimization | Custom Kelly | Riskfolio-Lib | Riskfolio-Lib (7.0.1) is powerful but overkill -- project needs Fractional Kelly, not full mean-variance optimization with 24 risk measures. 60 lines of custom code vs heavy dependency. |
| Type checking | mypy | pyright | Both are excellent. mypy is more widely adopted in data science ecosystem. pyright is 3-5x faster but requires Node.js. mypy is pure Python. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pandas >= 3.0 (in V1) | Breaking Copy-on-Write semantics. VectorBT, QuantStats have known compatibility issues. String dtype inference changes data handling patterns. | pandas >= 2.2.0, < 3.0 |
| alpaca-trade-api | Legacy SDK, replaced by alpaca-py. No longer the recommended client. | alpaca-py >= 0.43.0 |
| TA-Lib (for V1) | Requires C compilation, painful Windows install. Project is fundamental analysis focused -- technical indicators are not V1 scope. | pandas-ta if needed later (pure Python, but note: may be archived July 2026 due to funding) |
| yfinance < 1.0 | Pre-rewrite versions have reliability issues and different API surface. | yfinance >= 1.2.0 |
| OpenBB Platform | AGPL license is viral -- would require open-sourcing entire project. Heavy dependency (100+ data provider integrations). Use individual focused libs instead. | yfinance + edgartools + alpaca-py |
| Jupyter for production | Fine for exploration/research, but not for production CLI system. | Textual for dashboard, scripts for automation |
| Redis/Celery for scheduling | Massive overkill for single-process daily cron job. External infrastructure dependencies. | APScheduler (in-process) |
| MongoDB | Document store is wrong model for tabular financial data. No analytical query performance. | DuckDB (analytics) + SQLite (operational) |

## Full Dependency List

```toml
# pyproject.toml
[project]
name = "intrinsic-alpha-trader"
requires-python = ">=3.12,<3.13"

dependencies = [
    # Data Acquisition
    "yfinance>=1.2.0",
    "edgartools>=5.23.0",
    "alpaca-py>=0.43.0",

    # Data Processing
    "pandas>=2.2.0,<3.0",
    "numpy>=2.0.0,<2.4",
    "scipy>=1.14.0",

    # Storage
    "duckdb>=1.5.0",

    # Backtesting & Analytics
    "vectorbt>=0.28.0",
    "quantstats>=0.0.81",

    # CLI & Dashboard
    "textual>=8.0.0",
    "rich>=14.0.0",
    "typer>=0.24.0",

    # Configuration
    "pydantic>=2.10.0",
    "pydantic-settings>=2.13.0",

    # Scheduling
    "apscheduler>=3.11.0,<4.0.0",

    # Logging
    "loguru>=0.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.0",
    "pytest-cov>=5.0.0",
    "pytest-mock>=3.14.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.15.0",
    "mypy>=1.19.0",
    "pandas-stubs>=2.2.0",
]
```

## Project Initialization

```bash
# Install uv (if not already installed)
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project
uv init intrinsic-alpha-trader
cd intrinsic-alpha-trader

# Set Python version
uv python pin 3.12

# Add core dependencies
uv add yfinance edgartools alpaca-py "pandas>=2.2.0,<3.0" "numpy>=2.0.0,<2.4" scipy duckdb vectorbt quantstats textual rich typer pydantic pydantic-settings "apscheduler>=3.11.0,<4.0.0" loguru

# Add dev dependencies
uv add --dev pytest pytest-cov pytest-mock pytest-asyncio ruff mypy pandas-stubs
```

## Version Compatibility Matrix

| Package | Pinned Range | Reason for Pin | Upgrade Path |
|---------|-------------|----------------|--------------|
| Python | >=3.12,<3.13 | NumPy 2.4 requires >=3.11. 3.12 is stable across entire stack. | Move to 3.13 when all deps confirmed compatible. |
| pandas | >=2.2.0,<3.0 | Pandas 3.0 CoW breaks vectorbt/quantstats. | Migrate to 3.x in V2 after upstream fixes. First upgrade to 2.3 for deprecation warnings. |
| numpy | >=2.0.0,<2.4 | NumPy 2.4 aligns with pandas 3.0 ecosystem. Stay on 2.2.x for stability. | Upgrade alongside pandas 3.0 migration. |
| APScheduler | >=3.11.0,<4.0.0 | v4 is alpha with breaking API changes. 3.x is production-stable. | Evaluate v4 when it reaches stable. |

## Version Verification Sources

| Package | Version Verified | Source | Verified Date |
|---------|-----------------|--------|---------------|
| yfinance | 1.2.0 | [PyPI](https://pypi.org/project/yfinance/) | 2026-03-12 |
| edgartools | 5.23.0 | [PyPI](https://pypi.org/project/edgartools/) | 2026-03-12 |
| alpaca-py | 0.43.2 | [PyPI](https://pypi.org/project/alpaca-py/) | 2026-03-12 |
| pandas | 3.0.1 (latest); using 2.2.x | [PyPI](https://pypi.org/project/pandas/) | 2026-03-12 |
| numpy | 2.4.3 (latest); using 2.2.x | [PyPI](https://pypi.org/project/numpy/) | 2026-03-12 |
| scipy | 1.17.1 | [PyPI](https://pypi.org/project/scipy/) | 2026-03-12 |
| DuckDB | 1.5.0 | [PyPI](https://pypi.org/project/duckdb/) | 2026-03-12 |
| polars | 1.38.1 (not used in V1) | [PyPI](https://pypi.org/project/polars/) | 2026-03-12 |
| vectorbt | 0.28.4 | [PyPI](https://pypi.org/project/vectorbt/) | 2026-03-12 |
| quantstats | 0.0.81 | [PyPI](https://pypi.org/project/quantstats/) | 2026-03-12 |
| Textual | 8.1.1 | [PyPI](https://pypi.org/project/textual/) | 2026-03-12 |
| Rich | 14.3.3 | [PyPI](https://pypi.org/project/rich/) | 2026-03-12 |
| Typer | 0.24.1 | [PyPI](https://pypi.org/project/typer/) | 2026-03-12 |
| pydantic | 2.12.5 | [PyPI](https://pypi.org/project/pydantic/) | 2026-03-12 |
| pydantic-settings | 2.13.1 | [PyPI](https://pypi.org/project/pydantic-settings/) | 2026-03-12 |
| APScheduler | 3.11.2 | [PyPI](https://pypi.org/project/APScheduler/) | 2026-03-12 |
| loguru | 0.7.3 | [PyPI](https://pypi.org/project/loguru/) | 2026-03-12 |
| ruff | 0.15.5 | [PyPI](https://pypi.org/project/ruff/) | 2026-03-12 |
| mypy | 1.19.1 | [PyPI](https://pypi.org/project/mypy/) | 2026-03-12 |
| pytest | 9.0.2 | [PyPI](https://pypi.org/project/pytest/) | 2026-03-12 |
| uv | 0.10.9 | [PyPI](https://pypi.org/project/uv/) | 2026-03-12 |

## Stack Architecture Diagram

```
+--------------------------------------------------+
|                  CLI Layer                        |
|  Textual (dashboard) + Typer (commands) + Rich   |
+--------------------------------------------------+
         |                    |
+--------v--------+  +-------v---------+
| Scheduling      |  | Configuration   |
| APScheduler     |  | pydantic-settings|
+-----------------+  +-----------------+
         |
+--------v-----------------------------------------+
|              Application Layer                    |
|  Scoring Engine | Valuation Engine | Signal Engine |
|  Risk Manager   | Trade Planner   | Monitor       |
+--------------------------------------------------+
         |                    |
+--------v--------+  +-------v---------+
| Data Acquisition|  | Broker API      |
| yfinance        |  | alpaca-py       |
| edgartools      |  | (Paper + Live)  |
+-----------------+  +-----------------+
         |
+--------v-----------------------------------------+
|              Data Layer                           |
|  DuckDB (analytics: prices, financials, scores)  |
|  SQLite (operational: watchlists, trades, logs)   |
+--------------------------------------------------+
         |
+--------v-----------------------------------------+
|              Cross-cutting                        |
|  loguru (logging) | pandas/numpy (computation)    |
|  vectorbt (backtesting) | quantstats (analytics)  |
|  scipy (statistics)                               |
+--------------------------------------------------+
```

## Key Stack Decisions

1. **Pin pandas <3.0 for V1** -- Pandas 3.0 Copy-on-Write breaking changes cause issues in vectorbt and quantstats. Safe migration path: stay on 2.2.x, upgrade to 2.3 for deprecation warnings, then 3.0 after upstream libs confirm support.

2. **DuckDB + SQLite dual-database** -- DuckDB for OLAP (stock screening, ratio calculations), SQLite for OLTP (watchlists, trade plans, audit logs). Both embedded, single-file, zero-config. DuckDB is 10-50x faster for analytical queries.

3. **Custom scoring/valuation over libraries** -- No production-quality library exists for the specific scoring ensemble. ~800-1000 lines of well-tested custom Python code is more maintainable than adapting toy libraries with wrong assumptions. Full explainability for every calculation.

4. **VectorBT (free) with exit plan** -- Free version is in maintenance mode but sufficient for daily-bar fundamental backtesting in V1. Monitor pandas 3.0 compatibility. Exit plan: VectorBT PRO or custom vectorized backtesting.

5. **Typer over Click** -- Same power (Click underneath) with type-hint-first API. Consistent with pydantic-heavy codebase style.

6. **uv over Poetry/pip** -- 2026 consensus tool. 10-100x faster, handles everything, same ecosystem as ruff.

7. **FastAPI deferred to V2** -- CLI-first means no HTTP server needed. Direct function calls between modules.

8. **pandas over Polars for V1** -- Ecosystem compatibility (yfinance, vectorbt, edgartools) trumps raw speed at daily-granularity data scale.

---
*Stack research for: AI-assisted mid-term fundamental analysis trading system*
*Researched: 2026-03-12*
*All versions verified against PyPI on 2026-03-12*
