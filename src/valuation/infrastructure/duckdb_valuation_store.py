"""DuckDB persistence for valuation results.

Implements IValuationRepository with point-in-time querying.
Accepts DuckDB connection via dependency injection.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

import duckdb

from src.valuation.domain.repositories import IValuationRepository


class DuckDBValuationStore(IValuationRepository):
    """DuckDB-backed store for valuation results.

    Usage:
        conn = duckdb.connect("data/analytics.duckdb")
        store = DuckDBValuationStore(conn)
        store.save_valuation("AAPL", result_dict)
        latest = store.get_valuation("AAPL", as_of_date=date(2024, 1, 15))
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._create_tables()

    def _create_tables(self) -> None:
        """Create valuation_results table if not exists."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS valuation_results (
                ticker VARCHAR,
                valuation_date DATE,
                dcf_value DOUBLE,
                epv_value DOUBLE,
                relative_value DOUBLE,
                intrinsic_value DOUBLE,
                confidence DOUBLE,
                margin_of_safety DOUBLE,
                sector VARCHAR,
                has_margin BOOLEAN,
                sector_threshold DOUBLE,
                effective_weight_dcf DOUBLE,
                effective_weight_epv DOUBLE,
                effective_weight_relative DOUBLE,
                PRIMARY KEY (ticker, valuation_date)
            )
        """)

    def save_valuation(self, ticker: str, result_dict: dict[str, Any]) -> None:
        """Persist valuation result. Uses INSERT OR REPLACE for upsert semantics."""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO valuation_results (
                ticker, valuation_date, dcf_value, epv_value, relative_value,
                intrinsic_value, confidence, margin_of_safety, sector,
                has_margin, sector_threshold,
                effective_weight_dcf, effective_weight_epv, effective_weight_relative
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ticker,
                result_dict.get("valuation_date", date.today()),
                result_dict.get("dcf_value", 0.0),
                result_dict.get("epv_value", 0.0),
                result_dict.get("relative_value", 0.0),
                result_dict.get("intrinsic_value", 0.0),
                result_dict.get("confidence", 0.0),
                result_dict.get("margin_of_safety", 0.0),
                result_dict.get("sector", ""),
                result_dict.get("has_margin", False),
                result_dict.get("sector_threshold", 0.20),
                result_dict.get("effective_weight_dcf", 0.0),
                result_dict.get("effective_weight_epv", 0.0),
                result_dict.get("effective_weight_relative", 0.0),
            ],
        )

    def get_valuation(
        self, ticker: str, as_of_date: Optional[date] = None
    ) -> Optional[dict[str, Any]]:
        """Retrieve latest valuation for a ticker as of a given date.

        Point-in-time correctness: only returns records where
        valuation_date <= as_of_date.
        """
        if as_of_date is None:
            as_of_date = date.today()

        result = self._conn.execute(
            """
            SELECT * FROM valuation_results
            WHERE ticker = ?
              AND valuation_date <= ?
            ORDER BY valuation_date DESC
            LIMIT 1
            """,
            [ticker, as_of_date],
        ).fetchone()

        if result is None:
            return None

        columns = [
            "ticker", "valuation_date", "dcf_value", "epv_value", "relative_value",
            "intrinsic_value", "confidence", "margin_of_safety", "sector",
            "has_margin", "sector_threshold",
            "effective_weight_dcf", "effective_weight_epv", "effective_weight_relative",
        ]
        return dict(zip(columns, result))
