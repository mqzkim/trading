"""Tests for valuation domain Value Objects and events.

Covers: WACC, DCFResult, EPVResult, RelativeMultiplesResult,
IntrinsicValue, MarginOfSafety, ValuationCompletedEvent.
"""
from __future__ import annotations

import pytest

from src.valuation.domain.value_objects import (
    WACC,
    DCFResult,
    EPVResult,
    RelativeMultiplesResult,
    IntrinsicValue,
    MarginOfSafety,
)
from src.valuation.domain.events import ValuationCompletedEvent


# ── WACC ──────────────────────────────────────────────────────


class TestWACC:
    def test_valid_wacc(self) -> None:
        w = WACC(
            value=0.10,
            beta=1.2,
            risk_free_rate=0.04,
            equity_risk_premium=0.055,
            cost_of_equity=0.106,
            cost_of_debt=0.05,
            weight_equity=0.7,
            weight_debt=0.3,
        )
        assert w.value == 0.10
        assert w.clipped is False

    def test_clipped_flag(self) -> None:
        w = WACC(
            value=0.06,
            beta=0.5,
            risk_free_rate=0.03,
            equity_risk_premium=0.055,
            cost_of_equity=0.0575,
            cost_of_debt=0.04,
            weight_equity=0.8,
            weight_debt=0.2,
            clipped=True,
        )
        assert w.clipped is True

    def test_wacc_below_minimum_raises(self) -> None:
        with pytest.raises(ValueError, match="WACC must be in"):
            WACC(
                value=0.005,
                beta=1.0,
                risk_free_rate=0.04,
                equity_risk_premium=0.055,
                cost_of_equity=0.095,
                cost_of_debt=0.05,
                weight_equity=0.7,
                weight_debt=0.3,
            )

    def test_wacc_above_maximum_raises(self) -> None:
        with pytest.raises(ValueError, match="WACC must be in"):
            WACC(
                value=0.35,
                beta=2.0,
                risk_free_rate=0.04,
                equity_risk_premium=0.055,
                cost_of_equity=0.15,
                cost_of_debt=0.08,
                weight_equity=0.6,
                weight_debt=0.4,
            )


# ── DCFResult ─────────────────────────────────────────────────


class TestDCFResult:
    def _make_wacc(self) -> WACC:
        return WACC(
            value=0.10,
            beta=1.2,
            risk_free_rate=0.04,
            equity_risk_premium=0.055,
            cost_of_equity=0.106,
            cost_of_debt=0.05,
            weight_equity=0.7,
            weight_debt=0.3,
        )

    def test_valid_dcf(self) -> None:
        d = DCFResult(
            dcf_value=1_000_000.0,
            per_share=50.0,
            tv_pct=0.35,
            tv_capped=False,
            wacc=self._make_wacc(),
            projected_fcfs=(100.0, 110.0, 121.0, 133.1, 146.4),
        )
        assert d.dcf_value == 1_000_000.0
        assert d.tv_capped is False
        assert d.confidence_penalty == 0.0

    def test_tv_capped_flag(self) -> None:
        d = DCFResult(
            dcf_value=800_000.0,
            per_share=40.0,
            tv_pct=0.40,
            tv_capped=True,
            wacc=self._make_wacc(),
            projected_fcfs=(100.0, 110.0),
            confidence_penalty=0.2,
        )
        assert d.tv_capped is True
        assert d.confidence_penalty == 0.2

    def test_negative_dcf_raises(self) -> None:
        with pytest.raises(ValueError, match="dcf_value must be >= 0"):
            DCFResult(
                dcf_value=-100.0,
                per_share=-5.0,
                tv_pct=0.0,
                tv_capped=False,
                wacc=self._make_wacc(),
                projected_fcfs=(),
            )


# ── EPVResult ─────────────────────────────────────────────────


class TestEPVResult:
    def test_valid_epv(self) -> None:
        e = EPVResult(
            epv_total=500_000.0,
            per_share=25.0,
            normalized_margin=0.12,
            adjusted_earnings=50_000.0,
        )
        assert e.epv_total == 500_000.0
        assert e.earnings_cv is None

    def test_with_earnings_cv(self) -> None:
        e = EPVResult(
            epv_total=300_000.0,
            per_share=15.0,
            normalized_margin=0.08,
            adjusted_earnings=30_000.0,
            earnings_cv=0.65,
        )
        assert e.earnings_cv == 0.65

    def test_negative_epv_raises(self) -> None:
        with pytest.raises(ValueError, match="epv_total must be >= 0"):
            EPVResult(
                epv_total=-1.0,
                per_share=-0.05,
                normalized_margin=0.10,
                adjusted_earnings=-10.0,
            )


# ── RelativeMultiplesResult ───────────────────────────────────


class TestRelativeMultiplesResult:
    def test_valid_all_percentiles(self) -> None:
        r = RelativeMultiplesResult(
            per_percentile=60.0,
            pbr_percentile=45.0,
            ev_ebitda_percentile=55.0,
            composite_percentile=53.3,
            sector="Technology",
            peer_count=42,
        )
        assert r.composite_percentile == 53.3

    def test_none_per_valid(self) -> None:
        r = RelativeMultiplesResult(
            per_percentile=None,
            pbr_percentile=50.0,
            ev_ebitda_percentile=50.0,
            composite_percentile=50.0,
            sector="Energy",
            peer_count=30,
        )
        assert r.per_percentile is None

    def test_all_none_composite_none(self) -> None:
        r = RelativeMultiplesResult(
            per_percentile=None,
            pbr_percentile=None,
            ev_ebitda_percentile=None,
            composite_percentile=None,
            sector="Materials",
            peer_count=0,
        )
        assert r.composite_percentile is None

    def test_percentile_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="per_percentile must be 0-100"):
            RelativeMultiplesResult(
                per_percentile=105.0,
                pbr_percentile=50.0,
                ev_ebitda_percentile=50.0,
                composite_percentile=50.0,
                sector="Tech",
                peer_count=10,
            )

    def test_negative_percentile_raises(self) -> None:
        with pytest.raises(
            ValueError, match="ev_ebitda_percentile must be 0-100"
        ):
            RelativeMultiplesResult(
                per_percentile=50.0,
                pbr_percentile=50.0,
                ev_ebitda_percentile=-5.0,
                composite_percentile=50.0,
                sector="Tech",
                peer_count=10,
            )


# ── IntrinsicValue ────────────────────────────────────────────


class TestIntrinsicValue:
    def test_valid_intrinsic(self) -> None:
        iv = IntrinsicValue(
            mid=150.0,
            dcf_component=160.0,
            epv_component=140.0,
            relative_component=145.0,
            confidence=0.85,
            effective_weights={"dcf": 0.42, "epv": 0.35, "relative": 0.23},
        )
        assert iv.mid == 150.0
        assert iv.confidence == 0.85

    def test_negative_mid_raises(self) -> None:
        with pytest.raises(ValueError, match="mid must be >= 0"):
            IntrinsicValue(
                mid=-10.0,
                dcf_component=0.0,
                epv_component=0.0,
                relative_component=0.0,
                confidence=0.5,
                effective_weights={},
            )

    def test_confidence_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence must be in"):
            IntrinsicValue(
                mid=100.0,
                dcf_component=100.0,
                epv_component=100.0,
                relative_component=100.0,
                confidence=1.5,
                effective_weights={},
            )


# ── MarginOfSafety ────────────────────────────────────────────


class TestMarginOfSafety:
    def test_valid_margin(self) -> None:
        m = MarginOfSafety(
            value=0.25,
            intrinsic_mid=150.0,
            market_price=112.5,
            sector_threshold=0.20,
            has_margin=True,
        )
        assert m.has_margin is True

    def test_no_margin(self) -> None:
        m = MarginOfSafety(
            value=0.05,
            intrinsic_mid=100.0,
            market_price=95.0,
            sector_threshold=0.20,
            has_margin=False,
        )
        assert m.has_margin is False

    def test_zero_market_price_raises(self) -> None:
        with pytest.raises(ValueError, match="market_price must be > 0"):
            MarginOfSafety(
                value=0.0,
                intrinsic_mid=100.0,
                market_price=0.0,
                sector_threshold=0.20,
                has_margin=False,
            )

    def test_negative_market_price_raises(self) -> None:
        with pytest.raises(ValueError, match="market_price must be > 0"):
            MarginOfSafety(
                value=0.0,
                intrinsic_mid=100.0,
                market_price=-10.0,
                sector_threshold=0.20,
                has_margin=False,
            )


# ── ValuationCompletedEvent ───────────────────────────────────


class TestValuationCompletedEvent:
    def test_kw_only_construction(self) -> None:
        evt = ValuationCompletedEvent(
            ticker="AAPL",
            intrinsic_value=175.0,
            margin_of_safety=0.15,
            confidence=0.80,
            dcf_value=180.0,
            epv_value=170.0,
            relative_value=165.0,
            sector="Technology",
        )
        assert evt.ticker == "AAPL"
        assert evt.sector == "Technology"
        assert evt.occurred_on is not None

    def test_kw_only_enforced(self) -> None:
        """Positional args must raise TypeError because kw_only=True."""
        with pytest.raises(TypeError):
            ValuationCompletedEvent(  # type: ignore[misc]
                "AAPL", 175.0, 0.15, 0.80, 180.0, 170.0, 165.0, "Tech"
            )
