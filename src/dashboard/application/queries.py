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


class PipelineQueryHandler:
    """Aggregates pipeline, approval, budget, and review data for the pipeline page."""

    def __init__(self, ctx: dict) -> None:
        self._ctx = ctx

    def handle(self) -> dict[str, Any]:
        """Query all repos and build pipeline page data."""
        return {
            "pipeline_runs": self._get_pipeline_runs(),
            "next_scheduled": self._get_next_scheduled(),
            "approval_status": self._get_approval_status(),
            "daily_budget": self._get_daily_budget(),
            "review_queue": self._get_review_queue(),
        }

    def _get_pipeline_runs(self) -> list[dict]:
        """Get recent pipeline runs with stage results."""
        repo = self._ctx.get("pipeline_run_repo")
        if repo is None:
            return []
        try:
            runs = repo.get_recent(10)
        except Exception:
            return []

        result = []
        for run in runs:
            stages = []
            for s in run.stages:
                stages.append({
                    "name": s.stage_name,
                    "status": s.status,
                    "symbol_count": s.symbols_processed,
                })
            result.append({
                "run_id": run.run_id,
                "started_at": run.started_at.strftime("%Y-%m-%d %H:%M") if run.started_at else "",
                "completed_at": run.finished_at.strftime("%Y-%m-%d %H:%M") if run.finished_at else "--",
                "status": run.status.value,
                "stages": stages,
            })
        return result

    def _get_next_scheduled(self) -> str:
        """Get next scheduled run time from scheduler service."""
        scheduler = self._ctx.get("scheduler_service")
        if scheduler is None:
            return "Not scheduled"
        try:
            next_time = scheduler.get_next_run_time()
            if next_time is None:
                return "Not scheduled"
            return next_time.strftime("%Y-%m-%d %H:%M %Z")
        except Exception:
            return "Not scheduled"

    def _get_approval_status(self) -> dict | None:
        """Get current active approval status."""
        handler = self._ctx.get("approval_handler")
        if handler is None:
            return None
        try:
            status = handler.get_status()
            approval = status.get("approval")
            if approval is None:
                return None
            return {
                "id": approval.id,
                "score_threshold": approval.score_threshold,
                "allowed_regimes": approval.allowed_regimes,
                "max_per_trade_pct": approval.max_per_trade_pct,
                "daily_budget_cap": approval.daily_budget_cap,
                "expires_at": approval.expires_at.strftime("%Y-%m-%d %H:%M"),
                "is_active": approval.is_active,
                "is_suspended": approval.is_suspended,
                "suspended_reasons": list(approval.suspended_reasons),
                "status": "suspended" if approval.is_suspended else "active",
            }
        except Exception:
            return None

    def _get_daily_budget(self) -> dict:
        """Get today's budget from approval handler status."""
        handler = self._ctx.get("approval_handler")
        if handler is None:
            return {"spent": 0.0, "limit": 0.0, "remaining": 0.0}
        try:
            status = handler.get_status()
            budget = status.get("budget")
            if budget is None:
                return {"spent": 0.0, "limit": 0.0, "remaining": 0.0}
            return {
                "spent": budget.spent,
                "limit": budget.budget_cap,
                "remaining": budget.remaining,
            }
        except Exception:
            return {"spent": 0.0, "limit": 0.0, "remaining": 0.0}

    def _get_review_queue(self) -> list[dict]:
        """Get pending trade reviews from review queue repo."""
        repo = self._ctx.get("review_queue_repo")
        if repo is None:
            return []
        try:
            items = repo.list_pending()
            result = []
            for item in items:
                # Parse plan_json for trade details
                plan_data: dict = {}
                try:
                    plan_data = json.loads(item.plan_json) if item.plan_json else {}
                except (json.JSONDecodeError, TypeError):
                    pass
                result.append({
                    "id": item.id,
                    "symbol": item.symbol,
                    "strategy": plan_data.get("strategy", "--"),
                    "score": plan_data.get("composite_score", 0.0),
                    "reason": item.rejection_reason,
                    "created_at": item.created_at.strftime("%Y-%m-%d %H:%M"),
                })
            return result
        except Exception:
            return []


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


class SignalsQueryHandler:
    """Fetches latest scores and active signals for the signals page."""

    def __init__(self, ctx: dict) -> None:
        self._score_repo = ctx["score_repo"]
        self._signal_repo = ctx["signal_repo"]

    def handle(self, sort_by: str = "composite", sort_desc: bool = True) -> dict:
        """Return scores and signals for the signals page.

        Returns:
            dict with keys:
                scores: list of dicts with symbol, composite, risk_adjusted, strategy, signal
                signals: list of dicts with symbol, direction, strength, metadata
        """
        # Fetch latest scores per symbol: dict[str, CompositeScore]
        try:
            raw_scores = self._score_repo.find_all_latest()
        except Exception:
            raw_scores = {}

        # Build score rows
        scores = []
        for symbol, cs in raw_scores.items():
            scores.append({
                "symbol": symbol,
                "composite": round(cs.value, 1),
                "risk_adjusted": round(cs.risk_adjusted, 1),
                "strategy": cs.strategy,
            })

        # Sort scores
        sort_key = "composite" if sort_by == "composite" else sort_by
        if sort_key in ("composite", "risk_adjusted"):
            scores.sort(key=lambda s: s.get(sort_key, 0), reverse=sort_desc)
        else:
            scores.sort(key=lambda s: s.get("composite", 0), reverse=True)

        # Fetch active signals
        try:
            raw_signals = self._signal_repo.find_all_active()
        except Exception:
            raw_signals = []

        signals = []
        signal_by_symbol: dict[str, dict] = {}
        for sig in raw_signals:
            meta = sig.get("metadata", "")
            if isinstance(meta, str) and meta:
                try:
                    meta = json.loads(meta)
                except (json.JSONDecodeError, TypeError):
                    pass
            entry = {
                "symbol": sig["symbol"],
                "direction": sig["direction"],
                "strength": round(sig.get("strength", 0.0), 2),
                "metadata": meta,
            }
            signals.append(entry)
            signal_by_symbol[sig["symbol"]] = entry

        # Attach signal direction to each score row
        for score_row in scores:
            sig = signal_by_symbol.get(score_row["symbol"])
            score_row["signal"] = sig["direction"] if sig else "--"

        return {"scores": scores, "signals": signals}


class RiskQueryHandler:
    """Fetches risk metrics for the risk page."""

    MAX_POSITIONS = 20

    def __init__(self, ctx: dict) -> None:
        self._position_repo = ctx["position_repo"]
        self._regime_repo = ctx["regime_repo"]

    def handle(self) -> dict:
        """Return risk metrics for the risk page.

        Returns:
            dict with keys: drawdown_pct, drawdown_level, sector_weights,
                position_count, max_positions, regime, gauge_json, donut_json
        """
        # Get open positions
        try:
            positions = self._position_repo.find_all_open()
        except Exception:
            positions = []

        position_count = len(positions)

        # Calculate sector weights from positions
        sector_totals: dict[str, float] = {}
        total_value = 0.0
        for pos in positions:
            mv = pos.entry_price * pos.quantity
            total_value += mv
            sector = pos.sector if pos.sector else "Unknown"
            sector_totals[sector] = sector_totals.get(sector, 0.0) + mv

        sector_weights: dict[str, float] = {}
        if total_value > 0:
            sector_weights = {
                s: round(v / total_value * 100, 1) for s, v in sector_totals.items()
            }

        # Drawdown -- simplified: report 0 without Portfolio aggregate in ctx
        drawdown_pct = 0.0
        drawdown_level = "normal"

        # Regime
        try:
            regime_obj = self._regime_repo.find_latest()
        except Exception:
            regime_obj = None

        regime = regime_obj.regime_type.value if regime_obj is not None else "Unknown"

        # Build chart JSON
        gauge_json = build_drawdown_gauge(drawdown_pct)
        donut_json = build_sector_donut(
            sector_weights if sector_weights else {"No positions": 100}
        )

        return {
            "drawdown_pct": drawdown_pct,
            "drawdown_level": drawdown_level,
            "sector_weights": sector_weights,
            "position_count": position_count,
            "max_positions": self.MAX_POSITIONS,
            "regime": regime,
            "gauge_json": gauge_json,
            "donut_json": donut_json,
        }
