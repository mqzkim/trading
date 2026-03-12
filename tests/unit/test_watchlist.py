"""Tests for WatchlistEntry VO and SqliteWatchlistRepository (INTF-03).

Tests:
  - WatchlistEntry creation with valid fields
  - WatchlistEntry validation rejects empty symbol
  - SqliteWatchlistRepository add/find_all round-trip
  - SqliteWatchlistRepository remove deletes entry
  - SqliteWatchlistRepository find_by_symbol returns None for missing
"""
from __future__ import annotations

import os
import tempfile
from datetime import date

import pytest

from src.portfolio.domain.value_objects import WatchlistEntry
from src.portfolio.domain.repositories import IWatchlistRepository
from src.portfolio.infrastructure.sqlite_watchlist_repo import SqliteWatchlistRepository


class TestWatchlistEntryVO:
    """WatchlistEntry value object tests."""

    def test_create_with_valid_fields(self) -> None:
        """WatchlistEntry with valid symbol creates successfully."""
        entry = WatchlistEntry(
            symbol="AAPL",
            added_date=date(2026, 3, 12),
            notes="Watching earnings",
            alert_above=200.0,
            alert_below=150.0,
        )
        assert entry.symbol == "AAPL"
        assert entry.added_date == date(2026, 3, 12)
        assert entry.notes == "Watching earnings"
        assert entry.alert_above == 200.0
        assert entry.alert_below == 150.0

    def test_create_with_defaults(self) -> None:
        """WatchlistEntry with only symbol uses defaults."""
        entry = WatchlistEntry(symbol="MSFT")
        assert entry.symbol == "MSFT"
        assert entry.added_date == date.today()
        assert entry.notes is None
        assert entry.alert_above is None
        assert entry.alert_below is None

    def test_validation_rejects_empty_symbol(self) -> None:
        """WatchlistEntry with empty symbol raises ValueError."""
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            WatchlistEntry(symbol="")

    def test_validation_rejects_whitespace_symbol(self) -> None:
        """WatchlistEntry with whitespace-only symbol raises ValueError."""
        with pytest.raises(ValueError, match="Symbol must not be empty"):
            WatchlistEntry(symbol="   ")

    def test_frozen_immutable(self) -> None:
        """WatchlistEntry is immutable (frozen dataclass)."""
        entry = WatchlistEntry(symbol="AAPL")
        with pytest.raises(AttributeError):
            entry.symbol = "MSFT"  # type: ignore[misc]


class TestSqliteWatchlistRepository:
    """SqliteWatchlistRepository persistence tests."""

    @pytest.fixture
    def repo(self, tmp_path: str) -> SqliteWatchlistRepository:
        """Create a temporary SQLite watchlist repo."""
        db_path = os.path.join(str(tmp_path), "test_watchlist.db")
        return SqliteWatchlistRepository(db_path=db_path)

    def test_add_and_find_all_round_trip(self, repo: SqliteWatchlistRepository) -> None:
        """Add entries and find_all returns them."""
        entry1 = WatchlistEntry(symbol="AAPL", notes="Tech leader")
        entry2 = WatchlistEntry(symbol="MSFT", alert_above=500.0)
        repo.add(entry1)
        repo.add(entry2)

        results = repo.find_all()
        assert len(results) == 2
        symbols = {e.symbol for e in results}
        assert symbols == {"AAPL", "MSFT"}

    def test_add_overwrites_existing(self, repo: SqliteWatchlistRepository) -> None:
        """Adding same symbol again overwrites (INSERT OR REPLACE)."""
        entry1 = WatchlistEntry(symbol="AAPL", notes="First")
        entry2 = WatchlistEntry(symbol="AAPL", notes="Updated")
        repo.add(entry1)
        repo.add(entry2)

        results = repo.find_all()
        assert len(results) == 1
        assert results[0].notes == "Updated"

    def test_remove_deletes_entry(self, repo: SqliteWatchlistRepository) -> None:
        """Remove deletes an entry by symbol."""
        repo.add(WatchlistEntry(symbol="AAPL"))
        repo.add(WatchlistEntry(symbol="MSFT"))
        repo.remove("AAPL")

        results = repo.find_all()
        assert len(results) == 1
        assert results[0].symbol == "MSFT"

    def test_remove_nonexistent_is_noop(self, repo: SqliteWatchlistRepository) -> None:
        """Remove on non-existent symbol does not raise."""
        repo.remove("NONEXISTENT")  # should not raise

    def test_find_by_symbol_returns_entry(self, repo: SqliteWatchlistRepository) -> None:
        """find_by_symbol returns the matching entry."""
        entry = WatchlistEntry(
            symbol="GOOG", notes="Search giant", alert_below=100.0
        )
        repo.add(entry)

        result = repo.find_by_symbol("GOOG")
        assert result is not None
        assert result.symbol == "GOOG"
        assert result.notes == "Search giant"
        assert result.alert_below == 100.0

    def test_find_by_symbol_returns_none_for_missing(
        self, repo: SqliteWatchlistRepository
    ) -> None:
        """find_by_symbol returns None for non-existent symbol."""
        result = repo.find_by_symbol("NVDA")
        assert result is None

    def test_implements_interface(self, repo: SqliteWatchlistRepository) -> None:
        """SqliteWatchlistRepository implements IWatchlistRepository."""
        assert isinstance(repo, IWatchlistRepository)
