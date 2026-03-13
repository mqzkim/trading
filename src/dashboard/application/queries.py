"""Dashboard query handlers -- aggregate data from multiple bounded contexts."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from src.dashboard.presentation.charts import build_drawdown_gauge, build_sector_donut


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


class OverviewQueryHandler:
    """Aggregates data from portfolio, scoring, pipeline, and regime repos.

    Returns a dict suitable for rendering the overview template.
    """

    def __init__(self, ctx: dict) -> None:
        self._ctx = ctx

    def handle(self) -> dict[str, Any]:
        """Query all repos and build overview page data."""
        positions = self._get_positions()
        trade_history = self._get_trade_history()
        equity_curve = self._build_equity_curve(trade_history)
        regime_periods = self._get_regime_periods()
        last_pipeline = self._get_last_pipeline()

        # Compute KPIs from positions
        total_value = sum(p["market_value"] for p in positions)
        today_pnl = sum(p["pnl_dollar"] for p in positions)
        drawdown_pct = self._get_drawdown_pct()

        return {
            "total_value": total_value,
            "today_pnl": today_pnl,
            "drawdown_pct": drawdown_pct,
            "last_pipeline": last_pipeline,
            "positions": positions,
            "trade_history": trade_history,
            "equity_curve": equity_curve,
            "regime_periods": regime_periods,
        }

    def _get_positions(self) -> list[dict]:
        """Get open positions with composite scores joined from score_repo."""
        position_repo = self._ctx.get("position_repo")
        if position_repo is None:
            return []

        try:
            raw_positions = position_repo.find_all_open()
        except Exception:
            return []

        if not raw_positions:
            return []

        # Get latest scores for all symbols
        score_repo = self._ctx.get("score_repo")
        scores: dict = {}
        if score_repo is not None:
            try:
                scores = score_repo.find_all_latest()
            except Exception:
                pass

        result = []
        for pos in raw_positions:
            symbol = pos.symbol
            score_vo = scores.get(symbol)
            composite_score = score_vo.value if score_vo else 0.0

            # Position has entry_price and quantity but no current_price
            # Use entry_price as proxy (no live price feed in v1)
            current_price = pos.entry_price
            pnl_pct = 0.0
            pnl_dollar = 0.0

            stop_price = pos.atr_stop.stop_price if pos.atr_stop else 0.0
            target_price = 0.0  # No target in Position entity

            result.append({
                "symbol": symbol,
                "qty": pos.quantity,
                "current_price": current_price,
                "pnl_pct": pnl_pct,
                "pnl_dollar": pnl_dollar,
                "stop_price": stop_price,
                "target_price": target_price,
                "composite_score": composite_score,
                "market_value": current_price * pos.quantity,
            })

        return result

    def _get_trade_history(self) -> list[dict]:
        """Get executed trade plans from trade_plan_repo.

        Queries SQLite directly for executed trades since the repo
        only exposes find_pending() and find_by_symbol().
        """
        trade_plan_repo = self._ctx.get("trade_plan_repo")
        if trade_plan_repo is None:
            return []

        try:
            db_path = trade_plan_repo._db_path
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """SELECT symbol, direction, entry_price, stop_loss_price,
                              take_profit_price, quantity, position_value,
                              composite_score, signal_direction, status,
                              created_at
                       FROM trade_plans
                       WHERE status = 'EXECUTED'
                       ORDER BY created_at DESC
                       LIMIT 50"""
                ).fetchall()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def _build_equity_curve(self, trade_history: list[dict]) -> dict:
        """Derive equity curve from trade history P&L accumulation.

        V1 strategy: iterate executed trades ordered by date,
        accumulate realized P&L into running total starting from 0.
        """
        if not trade_history:
            return {"dates": [], "values": []}

        # Reverse to chronological order (trade_history is DESC)
        trades = list(reversed(trade_history))

        dates: list[str] = []
        values: list[float] = []
        cumulative = 0.0

        for trade in trades:
            date_str = str(trade.get("created_at", ""))[:10]
            # position_value is total trade value; approximate realized P&L as 0
            # since we don't have exit price in trade_plans table
            dates.append(date_str)
            values.append(cumulative)

        return {"dates": dates, "values": values}

    def _get_regime_periods(self) -> list[dict]:
        """Get regime periods for equity curve overlay."""
        regime_repo = self._ctx.get("regime_repo")
        if regime_repo is None:
            return []

        try:
            latest = regime_repo.find_latest()
            if latest is None:
                return []
            # Return the current regime as a single period
            regime_name = latest.regime_type.value
            detected = latest.detected_at.isoformat()[:10]
            return [{"start": detected, "end": detected, "regime": regime_name}]
        except Exception:
            return []

    def _get_drawdown_pct(self) -> float:
        """Get current drawdown percentage from portfolio aggregate."""
        handler = self._ctx.get("portfolio_handler")
        if handler is None:
            return 0.0

        try:
            repo = handler._portfolio_repo
            portfolio = repo.find_by_id("default")
            if portfolio is None:
                return 0.0
            return portfolio.drawdown
        except Exception:
            return 0.0

    def _get_last_pipeline(self) -> dict | None:
        """Get latest pipeline run status."""
        pipeline_run_repo = self._ctx.get("pipeline_run_repo")
        if pipeline_run_repo is None:
            return None

        try:
            runs = pipeline_run_repo.get_recent(1)
            if not runs:
                return None
            run = runs[0]
            return {
                "run_id": run.run_id,
                "status": run.status.value,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            }
        except Exception:
            return None
