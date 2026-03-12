"""Centralized database path and connection management.

Provides a single data directory for all stores, lazy DuckDB
connections, and consistent SQLite path generation.
"""
from __future__ import annotations

import os
from typing import Optional

import duckdb


class DBFactory:
    """Centralized database path and connection factory.

    Usage:
        factory = DBFactory(data_dir="data")
        conn = factory.duckdb_conn()           # analytics DuckDB
        path = factory.sqlite_path("scoring")  # "data/scoring.db"
        factory.close()
    """

    def __init__(self, data_dir: str = "data") -> None:
        self._data_dir = data_dir
        self._duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None
        os.makedirs(data_dir, exist_ok=True)

    @property
    def data_dir(self) -> str:
        return self._data_dir

    def duckdb_conn(self) -> duckdb.DuckDBPyConnection:
        """Return a lazily-created DuckDB connection (singleton per factory)."""
        if self._duckdb_conn is None:
            db_path = os.path.join(self._data_dir, "analytics.duckdb")
            self._duckdb_conn = duckdb.connect(db_path)
        return self._duckdb_conn

    def sqlite_path(self, name: str) -> str:
        """Return the SQLite database path for the given store name."""
        return os.path.join(self._data_dir, f"{name}.db")

    def close(self) -> None:
        """Close the DuckDB connection if open."""
        if self._duckdb_conn is not None:
            self._duckdb_conn.close()
            self._duckdb_conn = None
