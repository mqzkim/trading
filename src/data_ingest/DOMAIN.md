# Data Ingest

## Responsibilities

This bounded context handles all external data acquisition, validation, and storage for US equity market data. It manages OHLCV price data (via yfinance) and SEC financial statements (via edgartools), enforcing point-in-time correctness through filing date tracking.

## Core Value Objects

- **Ticker**: Validated stock ticker symbol (uppercase, 1-10 chars)
- **OHLCV**: Single price bar with date, open/high/low/close/volume
- **FinancialStatement**: SEC financial data with period_end and filing_date for point-in-time awareness
- **FilingDate**: Validated date that cannot be in the future
- **DataQualityReport**: Quality check results (missing %, stale days, outlier count, pass/fail)

## Domain Events

- **DataIngestedEvent**: Published when a ticker's data is successfully ingested
- **QualityCheckFailedEvent**: Published when quality validation fails

## External Dependencies

- scoring context (via domain events only): Receives ingested data notifications

## Key Use Cases

1. Ingest OHLCV price data for a ticker (yfinance)
2. Ingest SEC financial statements with filing dates (edgartools)
3. Store analytical data in DuckDB for screening queries
4. Validate data quality before downstream consumption
5. Manage universe of S&P 500 + S&P 400 tickers

## Invariant Rules

- Filing date must always be >= period end date (SEC files after period closes)
- All financial queries MUST filter by filing_date (not period_end) to prevent look-ahead bias
- DuckDB is for analytical reads only; SQLite handles operational writes
- Data failing quality checks is excluded from downstream consumption
