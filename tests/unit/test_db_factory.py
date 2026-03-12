"""Tests for DBFactory -- centralized database path and connection management."""
from __future__ import annotations

import os

from src.shared.infrastructure.db_factory import DBFactory


class TestDBFactory:
    def test_data_dir_created(self, tmp_path) -> None:
        target = str(tmp_path / "subdir" / "data")
        factory = DBFactory(data_dir=target)
        assert os.path.isdir(target)
        factory.close()

    def test_duckdb_conn_returns_connection(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        conn = factory.duckdb_conn()
        # Verify it is a working DuckDB connection
        result = conn.execute("SELECT 42 AS answer").fetchone()
        assert result is not None
        assert result[0] == 42
        factory.close()

    def test_duckdb_conn_singleton(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        conn1 = factory.duckdb_conn()
        conn2 = factory.duckdb_conn()
        assert conn1 is conn2
        factory.close()

    def test_sqlite_path(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        path = factory.sqlite_path("scoring")
        assert path == os.path.join(str(tmp_path), "scoring.db")
        factory.close()

    def test_close_and_recreate(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        conn1 = factory.duckdb_conn()
        factory.close()
        # After close, next call should create a new connection
        conn2 = factory.duckdb_conn()
        assert conn2 is not conn1
        result = conn2.execute("SELECT 1").fetchone()
        assert result[0] == 1
        factory.close()
