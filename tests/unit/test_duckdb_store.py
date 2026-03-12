"""Tests for DuckDB analytical store."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from src.data_ingest.infrastructure.duckdb_store import DuckDBStore


class TestDuckDBStoreConnection:
    def test_connect_creates_tables(self) -> None:
        store = DuckDBStore()
        store.connect(":memory:")
        try:
            tables = store._conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchall()
            table_names = {t[0] for t in tables}
            assert "ohlcv" in table_names
            assert "financials" in table_names
        finally:
            store.close()


class TestDuckDBStoreOHLCV:
    @pytest.fixture()
    def store(self):
        s = DuckDBStore()
        s.connect(":memory:")
        yield s
        s.close()

    def test_store_and_get_ohlcv(self, store: DuckDBStore) -> None:
        df = pd.DataFrame(
            {
                "ticker": ["AAPL", "AAPL", "AAPL"],
                "date": [date(2025, 1, 13), date(2025, 1, 14), date(2025, 1, 15)],
                "open": [150.0, 151.0, 152.0],
                "high": [155.0, 156.0, 157.0],
                "low": [149.0, 150.0, 151.0],
                "close": [153.0, 154.0, 155.0],
                "volume": [1000000, 1100000, 1200000],
            }
        )
        store.store_ohlcv("AAPL", df)
        result = store.get_ohlcv("AAPL")
        assert len(result) == 3
        assert result["close"].tolist() == [153.0, 154.0, 155.0]

    def test_get_ohlcv_with_date_range(self, store: DuckDBStore) -> None:
        df = pd.DataFrame(
            {
                "ticker": ["AAPL"] * 5,
                "date": [
                    date(2025, 1, 13),
                    date(2025, 1, 14),
                    date(2025, 1, 15),
                    date(2025, 1, 16),
                    date(2025, 1, 17),
                ],
                "open": [150.0] * 5,
                "high": [155.0] * 5,
                "low": [149.0] * 5,
                "close": [153.0] * 5,
                "volume": [1000000] * 5,
            }
        )
        store.store_ohlcv("AAPL", df)
        result = store.get_ohlcv("AAPL", start_date=date(2025, 1, 14), end_date=date(2025, 1, 16))
        assert len(result) == 3  # 14, 15, 16

    def test_get_ohlcv_empty_ticker(self, store: DuckDBStore) -> None:
        result = store.get_ohlcv("NONEXIST")
        assert len(result) == 0

    def test_store_ohlcv_upsert(self, store: DuckDBStore) -> None:
        df1 = pd.DataFrame(
            {
                "ticker": ["AAPL"],
                "date": [date(2025, 1, 15)],
                "open": [150.0],
                "high": [155.0],
                "low": [149.0],
                "close": [153.0],
                "volume": [1000000],
            }
        )
        df2 = pd.DataFrame(
            {
                "ticker": ["AAPL"],
                "date": [date(2025, 1, 15)],
                "open": [150.0],
                "high": [155.0],
                "low": [149.0],
                "close": [999.0],  # updated close
                "volume": [1000000],
            }
        )
        store.store_ohlcv("AAPL", df1)
        store.store_ohlcv("AAPL", df2)
        result = store.get_ohlcv("AAPL")
        assert len(result) == 1
        assert result["close"].iloc[0] == 999.0


class TestDuckDBStoreFinancials:
    @pytest.fixture()
    def store(self):
        s = DuckDBStore()
        s.connect(":memory:")
        yield s
        s.close()

    def _make_record(
        self,
        ticker: str = "AAPL",
        period_end: date = date(2025, 9, 30),
        filing_date: date = date(2025, 11, 1),
        form_type: str = "10-Q",
        **overrides,
    ) -> dict:
        defaults = dict(
            ticker=ticker,
            period_end=period_end,
            filing_date=filing_date,
            form_type=form_type,
            revenue=100_000.0,
            net_income=25_000.0,
            total_assets=500_000.0,
            total_liabilities=200_000.0,
            working_capital=50_000.0,
            retained_earnings=150_000.0,
            ebit=35_000.0,
            operating_cashflow=40_000.0,
            free_cashflow=30_000.0,
            current_ratio=2.5,
            debt_to_equity=0.4,
            roa=0.05,
            roe=0.12,
        )
        defaults.update(overrides)
        return defaults

    def test_store_and_get_financials(self, store: DuckDBStore) -> None:
        records = [self._make_record()]
        store.store_financials("AAPL", records)
        result = store.get_latest_financials("AAPL", as_of_date=date(2025, 12, 31))
        assert len(result) == 1
        assert result["revenue"].iloc[0] == 100_000.0

    def test_point_in_time_correctness(self, store: DuckDBStore) -> None:
        """Querying before filing_date should NOT return the record."""
        records = [
            self._make_record(
                period_end=date(2025, 9, 30),
                filing_date=date(2025, 11, 1),
            )
        ]
        store.store_financials("AAPL", records)

        # Query as of Oct 15 (before filing_date Nov 1)
        result_before = store.get_latest_financials("AAPL", as_of_date=date(2025, 10, 15))
        assert len(result_before) == 0

        # Query as of Nov 15 (after filing_date Nov 1)
        result_after = store.get_latest_financials("AAPL", as_of_date=date(2025, 11, 15))
        assert len(result_after) == 1

    def test_get_latest_returns_most_recent(self, store: DuckDBStore) -> None:
        """Multiple quarters stored, get_latest returns only the most recent."""
        records = [
            self._make_record(
                period_end=date(2025, 6, 30),
                filing_date=date(2025, 8, 1),
                revenue=80_000.0,
            ),
            self._make_record(
                period_end=date(2025, 9, 30),
                filing_date=date(2025, 11, 1),
                revenue=100_000.0,
            ),
        ]
        store.store_financials("AAPL", records)

        # As of Dec 31, both available, but latest should be Q3
        result = store.get_latest_financials("AAPL", as_of_date=date(2025, 12, 31))
        assert len(result) == 1
        assert result["revenue"].iloc[0] == 100_000.0

    def test_batch_insert(self, store: DuckDBStore) -> None:
        """Verify multiple records are inserted in a single batch."""
        records = [
            self._make_record(period_end=date(2025, 3, 31), filing_date=date(2025, 5, 1)),
            self._make_record(period_end=date(2025, 6, 30), filing_date=date(2025, 8, 1)),
            self._make_record(period_end=date(2025, 9, 30), filing_date=date(2025, 11, 1)),
        ]
        store.store_financials("AAPL", records)
        all_rows = store._conn.execute(
            "SELECT COUNT(*) FROM financials WHERE ticker = 'AAPL'"
        ).fetchone()
        assert all_rows[0] == 3


class TestDuckDBStoreRegimeData:
    """Tests for regime_data table storage and retrieval."""

    @pytest.fixture()
    def store(self):
        s = DuckDBStore()
        s.connect(":memory:")
        yield s
        s.close()

    def test_create_tables_includes_regime_data(self) -> None:
        """_create_tables should create regime_data table."""
        store = DuckDBStore()
        store.connect(":memory:")
        try:
            tables = store._conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchall()
            table_names = {t[0] for t in tables}
            assert "regime_data" in table_names
        finally:
            store.close()

    def test_store_regime_data(self, store: DuckDBStore) -> None:
        """store_regime_data inserts regime snapshot records."""
        df = pd.DataFrame({
            "date": [date(2026, 3, 10), date(2026, 3, 11)],
            "vix": [18.5, 19.0],
            "sp500_close": [5800.0, 5810.0],
            "sp500_ma200": [5600.0, 5605.0],
            "sp500_ratio": [1.0357, 1.0366],
            "yield_10y": [4.25, 4.28],
            "yield_3m": [4.10, 4.12],
            "yield_spread_bps": [15.0, 16.0],
        })
        store.store_regime_data(df)

        result = store._conn.execute("SELECT COUNT(*) FROM regime_data").fetchone()
        assert result[0] == 2

    def test_get_regime_data_no_filter(self, store: DuckDBStore) -> None:
        """get_regime_data with no filter returns all rows ordered by date."""
        df = pd.DataFrame({
            "date": [date(2026, 3, 12), date(2026, 3, 10), date(2026, 3, 11)],
            "vix": [20.0, 18.5, 19.0],
            "sp500_close": [5820.0, 5800.0, 5810.0],
            "sp500_ma200": [5610.0, 5600.0, 5605.0],
            "sp500_ratio": [1.037, 1.036, 1.037],
            "yield_10y": [4.30, 4.25, 4.28],
            "yield_3m": [4.13, 4.10, 4.12],
            "yield_spread_bps": [17.0, 15.0, 16.0],
        })
        store.store_regime_data(df)

        result = store.get_regime_data()
        assert len(result) == 3
        # Check ordered by date ascending
        dates = result["date"].tolist()
        assert dates == sorted(dates)

    def test_get_regime_data_with_date_range(self, store: DuckDBStore) -> None:
        """get_regime_data with start/end filters correctly."""
        df = pd.DataFrame({
            "date": [date(2026, 3, 10), date(2026, 3, 11), date(2026, 3, 12)],
            "vix": [18.5, 19.0, 20.0],
            "sp500_close": [5800.0, 5810.0, 5820.0],
            "sp500_ma200": [5600.0, 5605.0, 5610.0],
            "sp500_ratio": [1.036, 1.037, 1.034],
            "yield_10y": [4.25, 4.28, 4.30],
            "yield_3m": [4.10, 4.12, 4.13],
            "yield_spread_bps": [15.0, 16.0, 17.0],
        })
        store.store_regime_data(df)

        result = store.get_regime_data(
            start_date=date(2026, 3, 11),
            end_date=date(2026, 3, 11),
        )
        assert len(result) == 1
        assert result["vix"].iloc[0] == 19.0

    def test_regime_data_upsert(self, store: DuckDBStore) -> None:
        """Duplicate date INSERT OR REPLACE updates existing row."""
        df1 = pd.DataFrame({
            "date": [date(2026, 3, 10)],
            "vix": [18.5],
            "sp500_close": [5800.0],
            "sp500_ma200": [5600.0],
            "sp500_ratio": [1.036],
            "yield_10y": [4.25],
            "yield_3m": [4.10],
            "yield_spread_bps": [15.0],
        })
        df2 = pd.DataFrame({
            "date": [date(2026, 3, 10)],
            "vix": [22.0],  # updated value
            "sp500_close": [5750.0],
            "sp500_ma200": [5600.0],
            "sp500_ratio": [1.027],
            "yield_10y": [4.25],
            "yield_3m": [4.10],
            "yield_spread_bps": [15.0],
        })
        store.store_regime_data(df1)
        store.store_regime_data(df2)

        result = store.get_regime_data()
        assert len(result) == 1
        assert result["vix"].iloc[0] == 22.0
