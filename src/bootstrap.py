"""Composition Root -- wires all bounded contexts into a single context dict.

This is the ONLY file that imports from multiple bounded contexts.
All other files import only from their own context.

Usage:
    from src.bootstrap import bootstrap

    ctx = bootstrap()
    result = ctx["score_handler"].handle(ScoreSymbolCommand(...))
"""
from __future__ import annotations

from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.shared.infrastructure.db_factory import DBFactory

# -- Repository implementations (Infrastructure layer) --
from src.scoring.infrastructure import SqliteScoreRepository
from src.signals.infrastructure import SqliteSignalRepository
from src.regime.infrastructure import SqliteRegimeRepository
from src.portfolio.infrastructure import (
    SqlitePortfolioRepository,
    SqlitePositionRepository,
)
from src.execution.infrastructure import SqliteTradePlanRepository

# -- Application handlers --
from src.scoring.application.handlers import ScoreSymbolHandler
from src.signals.application.handlers import GenerateSignalHandler
from src.regime.application.handlers import DetectRegimeHandler
from src.portfolio.application.handlers import PortfolioManagerHandler
from src.execution.application.handlers import TradePlanHandler

# -- Execution dependencies --
from src.execution.domain.services import TradePlanService
from src.execution.domain.value_objects import ExecutionMode
from src.execution.infrastructure import (
    AlpacaExecutionAdapter,
    SafeExecutionAdapter,
    SqliteCooldownRepository,
)


def bootstrap(
    db_factory: DBFactory | None = None,
    market: str = "us",
) -> dict:
    """Create a fully wired application context.

    Args:
        db_factory: Optional DBFactory for test injection.
                    If None, creates a default one with data_dir="data".
        market: Market to wire execution for ("us" or "kr").

    Returns:
        Dict with pre-wired handlers, event bus, and db_factory.
        Keys: bus, db_factory, score_handler, signal_handler,
              regime_handler, portfolio_handler, trade_plan_handler.
    """
    if db_factory is None:
        db_factory = DBFactory(data_dir="data")

    bus = SyncEventBus()

    # -- Repositories (wired with db_factory paths) --
    score_repo = SqliteScoreRepository(
        db_path=db_factory.sqlite_path("scoring"),
    )
    signal_repo = SqliteSignalRepository(
        db_path=db_factory.sqlite_path("signals"),
    )
    regime_repo = SqliteRegimeRepository(
        db_path=db_factory.sqlite_path("regime"),
    )
    portfolio_repo = SqlitePortfolioRepository(
        db_path=db_factory.sqlite_path("portfolio"),
    )
    position_repo = SqlitePositionRepository(
        db_path=db_factory.sqlite_path("portfolio"),
    )
    trade_plan_repo = SqliteTradePlanRepository(
        db_path=db_factory.sqlite_path("portfolio"),
    )

    # -- Regime weight adjuster (must be created before score_handler) --
    from src.scoring.domain.services import ConcreteRegimeWeightAdjuster

    regime_adjuster = ConcreteRegimeWeightAdjuster()

    # -- Signal adapter (wraps core/signals/ evaluators) --
    from src.signals.infrastructure.core_signal_adapter import CoreSignalAdapter

    signal_adapter = CoreSignalAdapter()

    # -- Handlers (wired with repos) --
    score_handler = ScoreSymbolHandler(score_repo=score_repo, regime_adjuster=regime_adjuster)
    signal_handler = GenerateSignalHandler(
        signal_repo=signal_repo,
        signal_adapter=signal_adapter,
    )
    regime_handler = DetectRegimeHandler(regime_repo=regime_repo, bus=bus)
    portfolio_handler = PortfolioManagerHandler(
        portfolio_repo=portfolio_repo,
        position_repo=position_repo,
    )

    # -- Broker adapter + capital (market-conditional) --
    from src.execution.domain.repositories import IBrokerAdapter as _IBrokerAdapter
    from src.settings import settings

    # Determine execution mode
    execution_mode = ExecutionMode(settings.EXECUTION_MODE)

    adapter: _IBrokerAdapter
    capital: float
    cooldown_repo = SqliteCooldownRepository(
        db_path=db_factory.sqlite_path("portfolio"),
    )

    if market == "kr":
        from src.execution.infrastructure.kis_adapter import KisExecutionAdapter

        adapter = KisExecutionAdapter(
            app_key=settings.KIS_APP_KEY,
            app_secret=settings.KIS_APP_SECRET,
            account_no=settings.KIS_ACCOUNT_NO,
        )
        capital = settings.KR_CAPITAL
    else:
        # Select API keys based on execution mode
        api_key: str | None
        secret_key: str | None
        if execution_mode == ExecutionMode.LIVE:
            if not settings.ALPACA_LIVE_KEY or not settings.ALPACA_LIVE_SECRET:
                raise ValueError(
                    "Live mode requires ALPACA_LIVE_KEY and ALPACA_LIVE_SECRET"
                )
            api_key = settings.ALPACA_LIVE_KEY
            secret_key = settings.ALPACA_LIVE_SECRET
        else:
            # Paper mode: prefer ALPACA_PAPER_KEY, fall back to legacy keys
            api_key = settings.ALPACA_PAPER_KEY or settings.ALPACA_API_KEY
            secret_key = settings.ALPACA_PAPER_SECRET or settings.ALPACA_SECRET_KEY

        raw_adapter = AlpacaExecutionAdapter(
            api_key=api_key,
            secret_key=secret_key,
            paper=(execution_mode == ExecutionMode.PAPER),
        )
        adapter = SafeExecutionAdapter(
            inner=raw_adapter,
            mode=execution_mode,
            cooldown_repo=cooldown_repo,
        )
        capital = settings.US_CAPITAL

    trade_plan_service = TradePlanService()
    trade_plan_handler = TradePlanHandler(
        trade_plan_service=trade_plan_service,
        trade_plan_repo=trade_plan_repo,
        execution_adapter=adapter,
    )

    # -- Event subscriptions --
    # Minimal logging handler to prove the event bus infrastructure works
    # end-to-end. Per RESEARCH pitfall 3: start with a no-op/logging handler,
    # verify with integration tests, then enable cross-context wiring in Phase 6+.
    from src.scoring.domain.events import ScoreUpdatedEvent

    score_events: list[ScoreUpdatedEvent] = []

    def _log_score_event(event: ScoreUpdatedEvent) -> None:
        """Track score events for observability. No side effects."""
        score_events.append(event)

    bus.subscribe(ScoreUpdatedEvent, _log_score_event)

    # Regime -> Scoring weight adjustment (cross-context subscription)
    # regime_adjuster already created above and injected into score_handler
    from src.regime.domain.events import RegimeChangedEvent

    bus.subscribe(RegimeChangedEvent, regime_adjuster.on_regime_changed)

    # Remaining cross-context subscriptions deactivated:
    # bus.subscribe(ScoreUpdatedEvent, signal_handler.on_score_updated)
    # bus.subscribe(SignalGeneratedEvent, portfolio_handler.on_signal_generated)

    return {
        "bus": bus,
        "db_factory": db_factory,
        "score_handler": score_handler,
        "signal_handler": signal_handler,
        "regime_handler": regime_handler,
        "portfolio_handler": portfolio_handler,
        "trade_plan_handler": trade_plan_handler,
        "score_events": score_events,
        "regime_adjuster": regime_adjuster,
        "capital": capital,
        "market": market,
        "cooldown_repo": cooldown_repo,
        "execution_mode": execution_mode,
    }
