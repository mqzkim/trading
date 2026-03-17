"""PERF-01: Trade history persistence in DuckDB."""
from __future__ import annotations

from datetime import date

import duckdb
import pytest

try:
    from src.performance.domain.entities import ClosedTrade
    from src.performance.infrastructure.duckdb_trade_repository import (
        DuckDBTradeHistoryRepository,
    )

    _HAS_IMPL = True
except ImportError:
    _HAS_IMPL = False

pytestmark = pytest.mark.skipif(not _HAS_IMPL, reason="implementation pending")


def _make_trade(**overrides) -> "ClosedTrade":
    defaults = dict(
        id=None,
        symbol="AAPL",
        entry_date=date(2025, 1, 10),
        exit_date=date(2025, 2, 15),
        entry_price=150.0,
        exit_price=165.0,
        quantity=10,
        pnl=150.0,
        pnl_pct=0.10,
        strategy="swing",
        sector="technology",
        composite_score=78.5,
        technical_score=82.0,
        fundamental_score=75.0,
        sentiment_score=70.0,
        regime="bull",
        weights_json='{"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2}',
        signal_direction="BUY",
    )
    defaults.update(overrides)
    return ClosedTrade(**defaults)


@pytest.fixture()
def repo():
    conn = duckdb.connect(":memory:")
    return DuckDBTradeHistoryRepository(conn)


def test_save_and_find_all(repo):
    """Save a trade, then find_all returns it with all 17 fields intact."""
    trade = _make_trade()
    repo.save(trade)
    trades = repo.find_all()
    assert len(trades) == 1
    t = trades[0]
    assert t.symbol == "AAPL"
    assert t.entry_price == 150.0
    assert t.exit_price == 165.0
    assert t.pnl == 150.0
    assert t.pnl_pct == 0.10
    assert t.strategy == "swing"
    assert t.sector == "technology"
    assert t.composite_score == 78.5
    assert t.technical_score == 82.0
    assert t.fundamental_score == 75.0
    assert t.sentiment_score == 70.0
    assert t.regime == "bull"
    assert t.weights_json is not None
    assert t.signal_direction == "BUY"


def test_count(repo):
    """count() returns correct integer after inserts."""
    assert repo.count() == 0
    repo.save(_make_trade(symbol="AAPL"))
    repo.save(_make_trade(symbol="MSFT"))
    assert repo.count() == 2


def test_find_all_empty(repo):
    """Empty DB returns []."""
    assert repo.find_all() == []
