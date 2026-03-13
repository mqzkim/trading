"""Plotly chart builders for the dashboard.

Each function returns a JSON-serializable dict (via fig.to_json()).
"""
from __future__ import annotations

import json

import plotly.graph_objects as go


def build_equity_curve(
    values: list[float],
    dates: list[str],
    regime_periods: list[dict],
) -> dict:
    """Line chart of portfolio equity with regime background colors.

    Args:
        values: Equity values over time.
        dates: Corresponding date strings.
        regime_periods: List of dicts with keys "start", "end", "regime"
            where regime is one of "Bull", "Bear", "Sideways", "Crisis".

    Returns:
        JSON-serializable Plotly figure dict.
    """
    regime_colors = {
        "Bull": "rgba(0, 200, 83, 0.15)",
        "Bear": "rgba(255, 82, 82, 0.15)",
        "Sideways": "rgba(255, 235, 59, 0.15)",
        "Crisis": "rgba(158, 158, 158, 0.15)",
    }

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            name="Equity",
            line={"color": "#4fc3f7", "width": 2},
        )
    )

    for period in regime_periods:
        color = regime_colors.get(period["regime"], "rgba(158, 158, 158, 0.1)")
        fig.add_vrect(
            x0=period["start"],
            x1=period["end"],
            fillcolor=color,
            layer="below",
            line_width=0,
        )

    fig.update_layout(
        template="plotly_dark",
        margin={"l": 40, "r": 20, "t": 30, "b": 40},
        height=350,
        xaxis_title="Date",
        yaxis_title="Equity ($)",
    )

    return json.loads(fig.to_json())


def build_drawdown_gauge(current_drawdown_pct: float) -> dict:
    """Gauge chart for current drawdown percentage.

    Axis range is 0-20% matching the 3-tier drawdown defense:
    - 0-10%: green (monitoring)
    - 10-15%: yellow (position reduction)
    - 15-20%: red (full liquidation zone)

    Args:
        current_drawdown_pct: Current drawdown as percentage (0-20).

    Returns:
        JSON-serializable Plotly figure dict.
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=min(current_drawdown_pct, 20.0),
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 20], "tickvals": [0, 10, 15, 20]},
                "bar": {"color": "#263238"},
                "steps": [
                    {"range": [0, 10], "color": "#43a047"},
                    {"range": [10, 15], "color": "#fdd835"},
                    {"range": [15, 20], "color": "#e53935"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 2},
                    "thickness": 0.75,
                    "value": current_drawdown_pct,
                },
            },
            title={"text": "Drawdown"},
        )
    )

    fig.update_layout(
        template="plotly_dark",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        height=250,
    )

    return json.loads(fig.to_json())


def build_sector_donut(sectors: dict[str, float]) -> dict:
    """Donut chart of sector exposure.

    Args:
        sectors: Mapping of sector name to allocation percentage.

    Returns:
        JSON-serializable Plotly figure dict.
    """
    fig = go.Figure(
        go.Pie(
            labels=list(sectors.keys()),
            values=list(sectors.values()),
            hole=0.5,
            textinfo="label+percent",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        height=300,
        showlegend=False,
    )

    return json.loads(fig.to_json())
