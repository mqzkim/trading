## Output

- Structured data payload conforming to the `data-ingest` skill output schema
- Data quality report: record count, null counts per field, outlier flags, source used
- Cache status: HIT / MISS / EXPIRED with cache key and timestamp
- Any provider failover events (primary unavailable, fallback used)

## Data Collection Specification

### Price Data
- Minimum history: 756 trading days (3 years) for indicator reliability
- Frequency: daily OHLCV; weekly and monthly derived from daily
- Adjustment: fully adjusted (dividend + split) using adjusted close

### Technical Indicators
| Indicator | Parameters | Purpose |
|-----------|-----------|---------|
| MA | 50, 200 periods | Trend baseline |
| RSI | 14 periods | Momentum oscillator |
| ATR | 21 periods | Volatility for stop sizing |
| ADX | 14 periods | Trend strength |
| OBV | — | Volume trend confirmation |
| MACD | 12/26/9 | Momentum direction |

### Financial Statements
- Income statement: revenue, gross profit, EBIT, net income, EPS (4Q + 3Y annual)
- Balance sheet: total assets, working capital, retained earnings, total liabilities, market cap (latest + prior year)
- Cash flow: operating cash flow (CFO), capex (latest + prior year)

### Market Indicators
- VIX: current level
- S&P 500 vs 200MA: percentage above or below
- Yield curve slope: 10Y minus 2Y Treasury spread

## Data Quality Rules

- Reject any OHLCV record where High < Low or Close outside [Low, High]
- Flag volume = 0 for non-holiday trading days
- Winsorize returns at 1st/99th percentile before indicator calculation
- Use forward fill for gaps up to 3 days; drop beyond that
- All calculations use adjusted close — never unadjusted close

## Cache Schema (SQLite)

```
Table: price_cache
  symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER
  PRIMARY KEY (symbol, date)

Table: fundamentals_cache
  symbol TEXT, period TEXT, field TEXT, value REAL, fetched_at TEXT
  PRIMARY KEY (symbol, period, field)

Table: indicators_cache
  symbol TEXT, date TEXT, indicator TEXT, value REAL, fetched_at TEXT
  PRIMARY KEY (symbol, date, indicator)
```

## Reference Documents

- `.claude/skills/data-ingest/SKILL.md` — data collection workflow and CLI commands
- `docs/quantitative-scoring-methodologies.md` — required data fields per scoring model
- `docs/cli-skill-implementation-plan.md` §2.5 — DataClient interface specification
- `.claude/CLAUDE.md` — technology stack (EODHD, Twelve Data, FMP, SQLite, Redis)