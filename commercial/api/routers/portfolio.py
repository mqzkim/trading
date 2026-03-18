"""Portfolio router -- live positions, account overview, risk data.

GET /api/v1/portfolio/overview -- portfolio value, positions, PnL from Alpaca.
GET /api/v1/portfolio/risk -- drawdown, regime, sector weights.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from commercial.api.dependencies import get_context, verify_dashboard_secret

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


def _get_broker_adapter():
    """Get the raw Alpaca adapter (not SafeExecutionAdapter) for read queries."""
    ctx = get_context()
    safe = ctx.get("safe_adapter")
    if safe is not None and hasattr(safe, "_inner"):
        return safe._inner
    # Fallback: mock adapter
    from src.execution.infrastructure import AlpacaExecutionAdapter

    return AlpacaExecutionAdapter()


@router.get("/overview")
def get_overview(_: None = Depends(verify_dashboard_secret)):
    """Portfolio overview with live Alpaca data."""
    ctx = get_context()
    adapter = _get_broker_adapter()

    # Account data from Alpaca
    account = adapter.get_account()
    positions_raw = adapter.get_positions()

    # Enrich positions with score data
    score_repo = ctx.get("score_repo")
    positions = []
    for p in positions_raw:
        symbol = p.get("symbol", "")
        composite_score = None
        if score_repo is not None:
            latest = score_repo.find_latest(symbol)
            if latest is not None:
                composite_score = latest.value

        positions.append({
            "symbol": symbol,
            "qty": p.get("qty", 0),
            "current_price": round(
                p.get("market_value", 0) / max(p.get("qty", 1), 1), 2
            ),
            "pnl_pct": round(
                p.get("unrealized_pl", 0)
                / max(p.get("market_value", 1) - p.get("unrealized_pl", 0), 1)
                * 100,
                2,
            ),
            "pnl_dollar": p.get("unrealized_pl", 0),
            "stop_price": None,
            "target_price": None,
            "composite_score": composite_score,
            "market_value": p.get("market_value", 0),
        })

    # Last pipeline run
    pipeline_status_handler = ctx.get("pipeline_status_handler")
    last_pipeline = None
    if pipeline_status_handler is not None:
        from src.pipeline.application.commands import GetPipelineStatusQuery

        runs = pipeline_status_handler.handle(GetPipelineStatusQuery(limit=1))
        if runs:
            run = runs[0]
            last_pipeline = {
                "run_id": run.run_id,
                "status": run.status.value,
                "started_at": run.started_at.isoformat(),
                "finished_at": run.finished_at.isoformat()
                if run.finished_at
                else None,
            }

    return {
        "total_value": account.get("portfolio_value", 0),
        "today_pnl": sum(p.get("pnl_dollar", 0) for p in positions),
        "drawdown_pct": 0,
        "last_pipeline": last_pipeline,
        "positions": positions,
        "trade_history": [],
        "equity_curve": {"dates": [], "values": []},
        "regime_periods": [],
    }


@router.get("/risk")
def get_risk(_: None = Depends(verify_dashboard_secret)):
    """Risk overview: drawdown, regime, position counts."""
    ctx = get_context()

    # Regime data
    regime_repo = ctx.get("regime_repo")
    regime = "unknown"
    regime_confidence = 0.0
    regime_probabilities: dict[str, float] = {}
    if regime_repo is not None:
        latest = regime_repo.find_latest()
        if latest is not None:
            regime = latest.regime_type.value if hasattr(latest, "regime_type") else "unknown"
            regime_confidence = latest.confidence if hasattr(latest, "confidence") else 0.0

    # Portfolio drawdown
    portfolio_repo = ctx.get("portfolio_repo")
    drawdown_pct = 0.0
    drawdown_level = "normal"
    if portfolio_repo is not None:
        portfolio = portfolio_repo.find_by_id("default")
        if portfolio is not None:
            drawdown_pct = getattr(portfolio, "drawdown_pct", 0.0)
            drawdown_level = (
                portfolio.drawdown_level.value
                if hasattr(portfolio, "drawdown_level")
                else "normal"
            )

    # Position count
    position_count = len(_get_broker_adapter().get_positions())

    return {
        "drawdown_pct": drawdown_pct,
        "drawdown_level": drawdown_level,
        "sector_weights": {},
        "position_count": position_count,
        "max_positions": 10,
        "regime": regime,
        "regime_confidence": regime_confidence,
        "regime_probabilities": regime_probabilities,
    }
