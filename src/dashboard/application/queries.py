"""Dashboard query dataclasses -- placeholders for Plan 02-04 to implement handlers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OverviewQuery:
    """Query for overview page data (KPI cards, holdings, equity curve)."""


@dataclass(frozen=True)
class SignalsQuery:
    """Query for signals page data (scoring heatmap, signal recommendations)."""


@dataclass(frozen=True)
class RiskQuery:
    """Query for risk page data (drawdown gauge, sector exposure, position limits)."""


@dataclass(frozen=True)
class PipelineQuery:
    """Query for pipeline page data (run history, approval status, budget)."""
