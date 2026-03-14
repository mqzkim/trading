"""Infrastructure adapter for reading valuation data from DuckDB.

This keeps the DuckDB dependency in the infrastructure layer,
allowing the domain service (PipelineOrchestrator) to remain
free of infrastructure imports.
"""
from __future__ import annotations

import os
from typing import Optional


class ValuationAdapter:
    """Reads intrinsic_value from DuckDB valuation_results table.

    Injected into PipelineOrchestrator via handlers dict as
    'valuation_reader' callable. The domain service calls
    self._valuation_reader(symbol) with no infrastructure import.
    """

    def __init__(self, db_factory) -> None:
        self._db_factory = db_factory

    def get_intrinsic_value(self, symbol: str) -> Optional[float]:
        """Return intrinsic_value for symbol, or None if not found.

        Reads from DuckDB valuation_results table populated by
        EnsembleValuationService during the scoring pipeline.
        """
        try:
            import duckdb

            db_path = os.path.join(self._db_factory.data_dir, "analytics.duckdb")
            conn = duckdb.connect(str(db_path), read_only=True)
            row = conn.execute(
                "SELECT intrinsic_value FROM valuation_results WHERE ticker = ?",
                [symbol],
            ).fetchone()
            conn.close()
            if row is not None and row[0] is not None and row[0] > 0:
                return float(row[0])
        except Exception:
            pass  # Graceful fallback -- caller uses heuristic
        return None
