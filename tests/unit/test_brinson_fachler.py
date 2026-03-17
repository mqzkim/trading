"""PERF-02: Brinson-Fachler 4-level decomposition."""
from __future__ import annotations

from datetime import date

import pytest

try:
    from src.performance.domain.entities import ClosedTrade
    from src.performance.domain.services import BrinsonFachlerService
    from src.performance.domain.value_objects import AttributionLevel

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
        weights_json=None,
        signal_direction="BUY",
    )
    defaults.update(overrides)
    return ClosedTrade(**defaults)


@pytest.fixture()
def svc():
    return BrinsonFachlerService()


def test_returns_four_levels(svc):
    """compute(trades) returns list of 4 AttributionLevel objects."""
    trades = [
        _make_trade(strategy="swing", pnl_pct=0.10),
        _make_trade(strategy="position", pnl_pct=0.05),
    ]
    result = svc.compute(trades)
    assert len(result) == 4
    names = [level.name for level in result]
    assert names == ["portfolio", "strategy", "trade", "skill"]
    for level in result:
        assert isinstance(level, AttributionLevel)


def test_empty_trades_returns_zeros(svc):
    """compute([]) returns 4 levels each with 0.0 total_effect."""
    result = svc.compute([])
    assert len(result) == 4
    for level in result:
        assert level.total_effect == 0.0
        assert level.allocation_effect == 0.0
        assert level.selection_effect == 0.0
        assert level.interaction_effect == 0.0


def test_attribution_level_fields(svc):
    """Each AttributionLevel has all required fields."""
    trades = [_make_trade()]
    result = svc.compute(trades)
    for level in result:
        assert hasattr(level, "name")
        assert hasattr(level, "allocation_effect")
        assert hasattr(level, "selection_effect")
        assert hasattr(level, "interaction_effect")
        assert hasattr(level, "total_effect")
