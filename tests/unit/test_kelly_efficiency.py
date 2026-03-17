"""PERF-04: Kelly efficiency calculation."""
from __future__ import annotations

from datetime import date

import pytest

try:
    from src.performance.domain.entities import ClosedTrade
    from src.performance.domain.services import KellyEfficiencyService

    _HAS_IMPL = True
except ImportError:
    _HAS_IMPL = False

pytestmark = pytest.mark.skipif(not _HAS_IMPL, reason="implementation pending")


def _make_trade(pnl_pct=0.10, **overrides) -> "ClosedTrade":
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
        fundamental_score=75.0,
        sentiment_score=70.0,
        regime="bull",
        weights_json=None,
        signal_direction="BUY",
    )
    defaults.update(overrides)
    return ClosedTrade(**defaults)


@pytest.fixture()
def svc():
    return KellyEfficiencyService()


def test_returns_none_below_20_trades(svc):
    """Returns None when fewer than 20 trades."""
    trades = [_make_trade() for _ in range(19)]
    result = svc.compute(trades)
    assert result is None


def test_computes_efficiency(svc):
    """Returns float >= 0 with sufficient data."""
    # Mix of winners and losers
    trades = (
        [_make_trade(pnl_pct=0.08) for _ in range(14)]
        + [_make_trade(pnl_pct=-0.04) for _ in range(6)]
    )
    assert len(trades) == 20
    result = svc.compute(trades)
    assert result is not None
    assert result >= 0


def test_returns_none_all_losers(svc):
    """Returns None when all trades are losers."""
    trades = [_make_trade(pnl_pct=-0.05) for _ in range(25)]
    result = svc.compute(trades)
    assert result is None
