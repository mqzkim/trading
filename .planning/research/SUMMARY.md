# Research Summary: Intrinsic Alpha Trader

**Domain:** AI-assisted mid-term fundamental trading system (US equities)
**Researched:** 2026-03-12
**Overall confidence:** HIGH

## Executive Summary

The Intrinsic Alpha Trader occupies a well-defined niche in the trading tool ecosystem: an opinionated, end-to-end pipeline from financial data ingestion to risk-controlled execution, targeting serious retail investors who want systematic fundamental analysis with full explainability. The competitive landscape reveals that existing tools are either research-only (Stock Rover, Koyfin, Alpha Spread) or execution-only (broker APIs), with QuantConnect being the only bridge -- but it requires users to code everything from scratch. This system's differentiation lies in combining multi-score quality assessment (Piotroski F / Altman Z / Beneish M / Mohanram G), valuation ensemble (DCF + EPV + relative multiples), automatic position sizing, drawdown defense, and paper-validated execution into a single CLI tool with reasoning at every step.

The Python ecosystem for this domain is mature and well-established. The recommended stack centers on yfinance (1.2.0, free OHLCV + fundamentals), edgartools (5.23.0, best-in-class SEC EDGAR parser), and alpaca-py (0.43.2, official broker SDK with paper trading). For data processing, pandas remains the correct choice despite Polars' speed advantages, because every financial library (yfinance, vectorbt, edgartools) returns pandas DataFrames. The storage recommendation is a dual-database approach: DuckDB (1.5.0) for analytical workloads (screening 3000+ stocks, computing financial ratios) and SQLite for operational state (watchlists, trade plans, execution logs). For backtesting, vectorbt (0.28.4) is the clear winner over Backtrader and Zipline due to its vectorized execution speed and native pandas integration.

The architecture follows DDD with 8-10 bounded contexts communicating via an in-process event bus, fully compliant with the workspace's DDD rules. The critical dependency chain -- `data_ingest -> scoring -> valuation -> signals -> risk -> execution` -- is strictly unidirectional and determines the build order. All scoring and valuation logic must be custom-built; no production-quality library exists for the specific ensemble approach.

The domain has several critical pitfalls that must be addressed from day one: look-ahead bias in fundamental data (using financial statements before their filing date), survivorship bias in the stock universe (only backtesting against currently-traded stocks), value trap blindness in scoring (high F-Score stocks that are structurally declining), and DCF model brittleness (terminal value dominating the calculation). These are not "nice to address later" -- they are data integrity issues that invalidate all downstream analysis if present.

## Key Findings

**Stack:** Python 3.12 + uv + yfinance + edgartools + alpaca-py + pandas + DuckDB/SQLite + vectorbt + Textual CLI + loguru + pydantic-settings. All versions verified against PyPI as of 2026-03-12.

**Features:** 14 table stakes features, 14 differentiators, 11 explicit anti-features. No retail tool combines multi-score quality assessment + valuation ensemble + automatic position sizing + drawdown defense + paper-validated execution with full audit trail.

**Architecture:** DDD with 8-10 bounded contexts, synchronous in-process event bus, dual-database (DuckDB analytics + SQLite operational), safety-gate-first pipeline pattern. Follows workspace DDD rules exactly.

**Critical pitfall:** Look-ahead bias in fundamental data. If financial statement filing dates are not tracked from day one, every backtest result and every scoring calculation is untrustworthy. This is a Phase 1 requirement, not a "refinement."

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Foundation: Data Ingestion + Shared Kernel** - Everything depends on data. Must include point-in-time awareness (filing dates), data validation, and the DDD shared infrastructure (event bus, base classes, configuration). This phase has the highest pitfall density.
   - Addresses: Financial data ingestion, data validation, securities master database
   - Avoids: Look-ahead bias (Pitfall 1), survivorship bias (Pitfall 2), data source fragility (Pitfall 7)

2. **Analysis Core: Scoring + Valuation** - The core analytical pipeline. Safety gates (Z-Score, M-Score) run first to filter the universe, then quality scoring (F-Score), then valuation ensemble (DCF + EPV + relative). Most complex domain logic lives here.
   - Addresses: Fundamental scoring, valuation engine, safety filters, margin of safety
   - Avoids: Value trap blindness (Pitfall 3), DCF model brittleness (Pitfall 4)

3. **Decision Engine: Signals + Risk + Backtesting** - Combines scores and valuations into ranked signals. Position sizing with Fractional Kelly + ATR. Walk-forward backtesting to prove positive expectancy before any execution.
   - Addresses: Signal generation, position sizing, backtesting, drawdown defense
   - Avoids: Kelly blow-up risk (Pitfall 5), backtesting overfitting (Pitfall 6)

4. **Execution: Trade Plans + Alpaca + Monitoring** - Trade plan generation with entry/stop/target levels, human approval workflow, Alpaca paper trading integration, and position monitoring with alerts.
   - Addresses: Trade plan generation, paper trading, human approval, monitoring
   - Avoids: Paper-to-live gap (Pitfall 8)

5. **Interface: CLI Dashboard** - Textual TUI for interactive stock screening, portfolio view, trade plan review, and alert management. Builds on top of all previous phases.
   - Addresses: Stock screener, portfolio view, watchlist management, daily screening workflow

6. **Enhancement: Regime Detection + Multi-Strategy** - Market regime detection (bull/bear/crisis), regime-adaptive strategy weighting, multi-methodology signal consensus. Only after core pipeline is validated.
   - Addresses: Regime detection, multi-methodology signals, sector-neutral normalization

**Phase ordering rationale:**
- Phases 1-2 are strictly sequential: scoring requires data, valuation requires scoring output
- Phase 3 (signals + risk + backtesting) can start in parallel with late Phase 2 work, since basic signals only need F-Score + relative valuation
- Phase 4 depends on Phase 3 (cannot execute without validated signals and position sizing)
- Phase 5 (CLI) can be developed incrementally alongside Phases 2-4, adding views as data becomes available
- Phase 6 (regime + multi-strategy) is additive enhancement, not a dependency for core functionality

**Research flags for phases:**
- Phase 1: HIGH risk -- yfinance data quality edge cases, edgartools XBRL tag mapping coverage, point-in-time data model design. Likely needs deeper research.
- Phase 2: MEDIUM risk -- DCF terminal value capping approach and sector-specific model weighting need empirical validation. May need deeper research.
- Phase 3: MEDIUM risk -- walk-forward validation parameters, Deflated Sharpe Ratio implementation, vectorbt integration with fundamental signals. May need deeper research.
- Phase 4: LOW risk -- Standard Alpaca API integration patterns, well-documented.
- Phase 5: LOW risk -- Standard Textual TUI patterns, well-documented.
- Phase 6: MEDIUM risk -- Regime detection indicator selection and confirmation periods need research.

## Divergences Between Research Files

**Storage architecture:** STACK.md recommends DuckDB + SQLite; ARCHITECTURE.md recommends SQLite-only.
- **Resolution:** Use DuckDB + SQLite dual-database. DuckDB is 10-50x faster for the primary analytical workload. Both are embedded single-file databases with identical deployment simplicity. The DDD repository interfaces are storage-agnostic, so this is purely an infrastructure-layer decision.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI on 2026-03-12. Libraries are mature, widely-used, and well-documented. |
| Features | HIGH | Well-established domain. 14 table stakes confirmed via competitor analysis. |
| Architecture | HIGH | DDD patterns are well-established. Event bus appropriate for single-process CLI. Bounded contexts align naturally with trading domain. |
| Pitfalls | HIGH | All 8 critical pitfalls documented with multiple authoritative sources. Look-ahead bias and survivorship bias are the most dangerous. |
| Scoring/Valuation | MEDIUM | Custom implementation required. No off-the-shelf validation. Sector-specific model weighting needs empirical testing. |
| Data Quality | MEDIUM | yfinance is an unofficial scraper with no SLA. edgartools is actively maintained but XBRL coverage may have gaps. |

## Gaps to Address

- **yfinance adjusted close behavior:** Recent versions changed stock split adjustment methodology. Need empirical validation during Phase 1 implementation.
- **edgartools XBRL coverage:** What percentage of US-listed companies have parseable XBRL financial statements? Need to test against a sample.
- **Sector classification data source:** Neither yfinance nor edgartools clearly provides GICS sector classification. Need a free source for sector-neutral scoring.
- **VectorBT + fundamental strategy integration:** Most vectorbt examples are technical strategies. Need to verify fundamental signal-driven strategies can be expressed naturally.
- **Alpaca paper trading dividends:** Confirmed that Alpaca paper trading does NOT simulate dividends. For mid-term holding, dividend income is material (1-2% for high-yield stocks). Need separate dividend tracking.
- **Windows-specific DuckDB behavior:** Workspace runs on Windows 11. Need to verify file locking and concurrent access work correctly.
- **US market universe definition:** Which stocks to screen (Russell 3000? S&P 500 + midcap?) affects data costs and compute. Needs definition before Phase 1.
- **Valuation ensemble weights:** DCF vs EPV vs relative weighting needs backtesting-driven calibration during Phase 3.
