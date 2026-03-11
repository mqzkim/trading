"""DuckDB analytical store for OHLCV and financial data.

Persistent columnar storage optimized for analytical queries
(screening 500+ tickers). Uses point-in-time filtering via filing_date.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import duckdb
import pandas as pd


class DuckDBStore:
    """Analytical data store backed by DuckDB.

    Usage:
        store = DuckDBStore()
        store.connect(":memory:")  # or "data/analytics.duckdb" for persistent
        store.store_ohlcv("AAPL", df)
        result = store.get_ohlcv("AAPL")
        store.close()
    """

    def __init__(self) -> None:
        self._conn: duckdb.DuckDBPyConnection | None = None

    def connect(self, db_path: str = "data/analytics.duckdb") -> None:
        """Open connection and create tables if they don't exist."""
        self._conn = duckdb.connect(db_path)
        self._create_tables()

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _create_tables(self) -> None:
        assert self._conn is not None
        self._conn.execute("""
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
        self._conn.execute("""
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

    # ── OHLCV ────────────────────────────────────────────────────────

    def store_ohlcv(self, ticker: str, df: pd.DataFrame) -> None:
        """Batch insert/upsert OHLCV rows from a DataFrame.

        DataFrame must have columns: ticker, date, open, high, low, close, volume.
        Uses INSERT OR REPLACE for upsert semantics.
        """
        assert self._conn is not None
        if df.empty:
            return
        self._conn.execute(
            "INSERT OR REPLACE INTO ohlcv SELECT * FROM df"
        )

    def get_ohlcv(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Query OHLCV data for a ticker, optionally filtered by date range."""
        assert self._conn is not None
        query = "SELECT * FROM ohlcv WHERE ticker = ?"
        params: list = [ticker]

        if start_date is not None:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date is not None:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date"
        return self._conn.execute(query, params).fetchdf()

    # ── Financials ───────────────────────────────────────────────────

    def store_financials(self, ticker: str, records: list[dict]) -> None:
        """Batch insert/upsert financial records.

        Each record dict must match the financials table schema.
        Uses a single transaction for all records.
        """
        assert self._conn is not None
        if not records:
            return
        df = pd.DataFrame(records)  # noqa: F841 — referenced by DuckDB SQL
        self._conn.execute(
            "INSERT OR REPLACE INTO financials SELECT * FROM df"
        )

    def get_latest_financials(
        self, ticker: str, as_of_date: date
    ) -> pd.DataFrame:
        """Get the most recent financial record available as of a given date.

        Point-in-time correctness: only returns records where
        filing_date <= as_of_date, preventing look-ahead bias.
        """
        assert self._conn is not None
        return self._conn.execute(
            """
            SELECT * FROM financials
            WHERE ticker = ?
              AND filing_date <= ?
              AND filing_date = (
                  SELECT MAX(f2.filing_date) FROM financials f2
                  WHERE f2.ticker = financials.ticker
                    AND f2.filing_date <= ?
              )
            """,
            [ticker, as_of_date, as_of_date],
        ).fetchdf()
