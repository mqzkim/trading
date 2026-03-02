"""Tests for self-improvement advisor."""
import pytest

from core.backtest.metrics import PerformanceMetrics
from core.backtest.walk_forward import WalkForwardResult
from personal.self_improver.advisor import (
    ImprovementAdvice,
    suggest_improvements,
    analyze_strategy_performance,
)


def _make_metrics(
    sharpe: float = 1.0,
    max_dd: float = -0.10,
    cagr: float = 0.15,
    total_return: float = 0.15,
) -> PerformanceMetrics:
    """Helper: build a PerformanceMetrics with controllable fields."""
    return PerformanceMetrics(
        cagr=cagr,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        win_rate=0.55,
        total_return=total_return,
        num_trades=10,
        avg_return_per_trade=0.02,
    )


def _make_wf_result(
    oos_sharpe: float = 1.0,
    is_sharpe: float = 1.2,
    oos_max_dd: float = -0.10,
    n_splits: int = 3,
) -> WalkForwardResult:
    """Helper: build a WalkForwardResult with controllable key values."""
    return WalkForwardResult(
        n_splits=n_splits,
        splits=[{}] * n_splits,
        oos_metrics=_make_metrics(sharpe=oos_sharpe, max_dd=oos_max_dd),
        is_metrics=_make_metrics(sharpe=is_sharpe),
        overfitting_score=is_sharpe - oos_sharpe,
    )


# --- Tests ---


def test_improvement_advice_structure():
    """ImprovementAdvice has all expected fields."""
    advice = ImprovementAdvice(current_sharpe=1.5)
    assert hasattr(advice, "current_sharpe")
    assert hasattr(advice, "suggested_regime_weights")
    assert hasattr(advice, "suggested_risk_adjustment")
    assert hasattr(advice, "recommendations")
    assert hasattr(advice, "priority")


def test_high_sharpe_low_priority():
    """Sharpe=2.0 triggers 'high' priority (excellent performance)."""
    wf = _make_wf_result(oos_sharpe=2.0, is_sharpe=2.1)
    advice = suggest_improvements(wf)

    assert advice.priority == "high"
    assert advice.current_sharpe == 2.0
    assert any("maintain" in r.lower() or "excellent" in r.lower() for r in advice.recommendations)


def test_low_sharpe_triggers_adjustment():
    """Sharpe=0.3 triggers risk adjustment suggestion."""
    wf = _make_wf_result(oos_sharpe=0.3, is_sharpe=1.5)
    advice = suggest_improvements(wf)

    assert advice.suggested_risk_adjustment is not None
    assert advice.suggested_risk_adjustment <= 0.5
    assert advice.priority == "high"


def test_overfitting_detected():
    """Overfitting score > 1.0 generates overfitting warning in recommendations."""
    wf = _make_wf_result(oos_sharpe=0.8, is_sharpe=2.8)  # overfitting = 2.0
    advice = suggest_improvements(wf)

    assert any("overfitting" in r.lower() for r in advice.recommendations)


def test_high_drawdown_triggers_risk_reduction():
    """Max DD of -0.35 triggers risk adjustment reduction."""
    wf = _make_wf_result(oos_sharpe=1.2, oos_max_dd=-0.35)
    advice = suggest_improvements(wf)

    assert advice.suggested_risk_adjustment is not None
    # Should be reduced below the default
    assert advice.suggested_risk_adjustment < 1.0
    assert any("drawdown" in r.lower() for r in advice.recommendations)


def test_recommendations_list_not_empty():
    """suggest_improvements always returns at least one recommendation."""
    wf = _make_wf_result(oos_sharpe=1.0, is_sharpe=1.0)
    advice = suggest_improvements(wf)

    assert len(advice.recommendations) > 0


def test_analyze_strategy_performance_keys():
    """analyze_strategy_performance returns dict with expected keys."""
    returns = [0.05, -0.02, 0.08, -0.01, 0.03]
    result = analyze_strategy_performance(returns)

    assert "win_rate" in result
    assert "avg_return" in result
    assert "consistency" in result
    assert result["win_rate"] == pytest.approx(0.6, abs=0.01)
