"""PERF-03: IC (Information Coefficient) calculation."""
from __future__ import annotations

from datetime import date

import pytest

try:
    from src.performance.domain.entities import ClosedTrade
    from src.performance.domain.services import ICCalculationService

    _HAS_IMPL = True
except ImportError:
    _HAS_IMPL = False

pytestmark = pytest.mark.skipif(not _HAS_IMPL, reason="implementation pending")


def _make_trade(fundamental_score=75.0, pnl_pct=0.10, **overrides) -> "ClosedTrade":
    defaults = dict(
        id=None,
        symbol="AAPL",
        entry_date=date(2025, 1, 10),
        exit_date=date(2025, 2, 15),
        entry_price=150.0,
        exit_price=165.0,
        quantity=10,
        pnl=150.0,
        pnl_pct=pnl_pct,
        strategy="swing",
        sector="technology",
        composite_score=78.5,
        technical_score=82.0,
        fundamental_score=fundamental_score,
        sentiment_score=70.0,
        regime="bull",
        weights_json=None,
        signal_direction="BUY",
    )
    defaults.update(overrides)
    return ClosedTrade(**defaults)


@pytest.fixture()
def svc():
    return ICCalculationService()


def test_returns_none_below_20_trades(svc):
    """IC returns None when fewer than 20 trades."""
    trades = [_make_trade() for _ in range(19)]
    result = svc.compute_axis_ic(trades, "fundamental")
    assert result is None


def test_computes_ic_above_20_trades(svc):
    """IC returns a float in [-1.0, 1.0] with 20+ trades."""
    trades = [
        _make_trade(fundamental_score=50.0 + i * 2.0, pnl_pct=-0.05 + i * 0.01)
        for i in range(25)
    ]
    result = svc.compute_axis_ic(trades, "fundamental")
    assert result is not None
    assert -1.0 <= result <= 1.0


def test_returns_none_no_variance(svc):
    """Returns None when all scores are identical (no variance)."""
    trades = [_make_trade(fundamental_score=75.0) for _ in range(25)]
    result = svc.compute_axis_ic(trades, "fundamental")
    assert result is None
