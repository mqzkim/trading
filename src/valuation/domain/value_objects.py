"""Valuation domain Value Objects.

Immutable VOs for valuation models: WACC, DCFResult, EPVResult,
RelativeMultiplesResult, IntrinsicValue, MarginOfSafety.
Each validates invariants on construction.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import ValueObject


@dataclass(frozen=True)
class WACC(ValueObject):
    """Weighted Average Cost of Capital.

    WACC = We*Ke + Wd*Kd*(1-T), clipped to [0.06, 0.14] per locked decision.
    """

    value: float
    beta: float
    risk_free_rate: float
    equity_risk_premium: float
    cost_of_equity: float
    cost_of_debt: float
    weight_equity: float
    weight_debt: float
    clipped: bool = False

    def _validate(self) -> None:
        if not 0.01 <= self.value <= 0.30:
            raise ValueError(
                f"WACC must be in [0.01, 0.30], got {self.value}"
            )


@dataclass(frozen=True)
class DCFResult(ValueObject):
    """Discounted Cash Flow valuation result.

    Terminal value capped at 40% of total. Confidence penalty applied when cap triggers.
    """

    dcf_value: float
    per_share: float
    tv_pct: float
    tv_capped: bool
    wacc: WACC
    projected_fcfs: tuple[float, ...]
    confidence_penalty: float = 0.0

    def _validate(self) -> None:
        if self.dcf_value < 0:
            raise ValueError(
                f"dcf_value must be >= 0, got {self.dcf_value}"
            )


@dataclass(frozen=True)
class EPVResult(ValueObject):
    """Earnings Power Value result (Greenwald method).

    Uses 5-year averaged operating margin applied to current revenue.
    """

    epv_total: float
    per_share: float
    normalized_margin: float
    adjusted_earnings: float
    earnings_cv: float | None = None

    def _validate(self) -> None:
        if self.epv_total < 0:
            raise ValueError(
                f"epv_total must be >= 0, got {self.epv_total}"
            )


@dataclass(frozen=True)
class RelativeMultiplesResult(ValueObject):
    """Relative multiples percentile ranking within GICS sector.

    PER/PBR/EV-EBITDA percentiles (0-100). None when metric is unavailable.
    """

    per_percentile: float | None
    pbr_percentile: float | None
    ev_ebitda_percentile: float | None
    composite_percentile: float | None
    sector: str
    peer_count: int

    def _validate(self) -> None:
        for name, val in [
            ("per_percentile", self.per_percentile),
            ("pbr_percentile", self.pbr_percentile),
            ("ev_ebitda_percentile", self.ev_ebitda_percentile),
            ("composite_percentile", self.composite_percentile),
        ]:
            if val is not None and not 0 <= val <= 100:
                raise ValueError(f"{name} must be 0-100, got {val}")


@dataclass(frozen=True)
class IntrinsicValue(ValueObject):
    """Ensemble intrinsic value from DCF + EPV + Relative models.

    Confidence-weighted combination with effective weights reflecting
    model reliability.
    """

    mid: float
    dcf_component: float
    epv_component: float
    relative_component: float
    confidence: float
    effective_weights: dict[str, float]

    def _validate(self) -> None:
        if self.mid < 0:
            raise ValueError(f"mid must be >= 0, got {self.mid}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(
                f"confidence must be in [0, 1], got {self.confidence}"
            )


@dataclass(frozen=True)
class MarginOfSafety(ValueObject):
    """Margin of Safety -- (intrinsic - market) / intrinsic.

    Sector-specific thresholds: Tech ~25%, Consumer Staples ~15%, default 20%.
    """

    value: float
    intrinsic_mid: float
    market_price: float
    sector_threshold: float
    has_margin: bool

    def _validate(self) -> None:
        if self.market_price <= 0:
            raise ValueError(
                f"market_price must be > 0, got {self.market_price}"
            )
