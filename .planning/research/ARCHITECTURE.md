# Architecture Patterns: v1.2 Production Trading & Dashboard

**Domain:** Automated trading pipeline, live execution, strategy/budget approval, and web dashboard integration into existing DDD architecture
**Researched:** 2026-03-13
**Overall Confidence:** HIGH (based on direct codebase analysis of existing 20K+ LOC system plus verified library research)

---

## Executive Summary

The v1.2 milestone introduces four capabilities -- automated pipeline scheduler, live trading, strategy/budget approval workflow, and web dashboard -- into an existing DDD system with 8 bounded contexts, a dual-database (DuckDB + SQLite) architecture, and a working but mostly unwired async event bus.

The critical architectural finding is that these four features require **one new bounded context** (`scheduler`), **one new presentation layer** (`dashboard`), and **significant modifications to two existing contexts** (`execution` for live trading + approval workflow, `portfolio` for real-time monitoring). The existing event bus, which was defined but largely dormant in v1.0-v1.1, becomes the backbone for v1.2 -- the scheduler publishes pipeline stage events, the execution context publishes order events, and the dashboard subscribes to all of them for real-time updates.

The AlpacaExecutionAdapter already has a `paper=True` flag. Switching to live is a one-line configuration change (`paper=False`), but the real work is the safeguards around it: budget enforcement, daily spending limits, circuit breakers, and error recovery. These safeguards are new domain logic in `execution/domain/` that wraps the existing IBrokerAdapter.

For the web dashboard, the recommended approach is **FastAPI + Jinja2 + HTMX + SSE** -- server-side rendered HTML with HTMX for partial updates and Server-Sent Events for real-time streaming. This avoids introducing a JavaScript SPA framework, stays within the Python-centric stack, and leverages the existing FastAPI infrastructure from the commercial API. The dashboard is a separate FastAPI app mounted alongside (not replacing) the commercial API.

**Key architectural decision: The pipeline scheduler, approval workflow, and live execution are personal-use features (not commercial). They share the same DDD handlers and domain logic as the CLI, but are orchestrated by a new `scheduler` bounded context instead of manual CLI commands.**

---

## Current Architecture (As-Is, post-v1.1)

### System Overview

```
User (CLI: Typer+Rich)
    |
    v
bootstrap.py (Composition Root)
    |-- SyncEventBus (CLI context, used for regime -> scoring weight adjustment)
    |-- DBFactory (DuckDB analytics + SQLite operational)
    |-- 5 handlers: score, signal, regime, portfolio, trade_plan
    |-- 1 broker adapter: AlpacaExecutionAdapter (paper=True) or KisExecutionAdapter
    v
Manual Pipeline: ingest -> score -> signal -> plan -> approve -> execute
    (each step is a separate CLI command)
```

### Key Existing Components

| Component | State | v1.2 Impact |
|-----------|-------|-------------|
| `SyncEventBus` | Active, wires RegimeChangedEvent -> scoring weights | Must support async for scheduler/dashboard |
| `AsyncEventBus` | Exists, unused in production | Becomes the primary bus for v1.2 |
| `TradePlanHandler` | generate -> approve -> execute lifecycle | Extend with budget/strategy approval workflow |
| `AlpacaExecutionAdapter` | paper=True, mock fallback | Add paper=False path with safeguards |
| `DataPipeline` | async ingest_universe() | Becomes first stage of automated pipeline |
| `ITradePlanRepository` | save/find_pending/find_by_symbol/update_status | Add find_by_date_range, budget tracking queries |
| `TradePlanStatus` | PENDING/APPROVED/REJECTED/MODIFIED/EXECUTED/FAILED | Add BUDGET_CHECK, AUTO_APPROVED states |

### Data Flow (Current -- Manual)

```
CLI: ingest AAPL MSFT GOOG  --> DataPipeline.ingest_universe()  --> DuckDB
CLI: score AAPL              --> ScoreSymbolHandler.handle()     --> SQLite
CLI: signal AAPL             --> GenerateSignalHandler.handle()  --> SQLite
CLI: plan AAPL               --> TradePlanHandler.generate()     --> SQLite (PENDING)
CLI: approve AAPL            --> TradePlanHandler.approve()      --> SQLite (APPROVED)
CLI: execute AAPL            --> TradePlanHandler.execute()      --> Alpaca (paper)
CLI: monitor                 --> Position/Portfolio read          --> Display
```

Each step is triggered manually by the user via CLI commands. There is no orchestration layer that chains these steps together.

---

## Target Architecture (v1.2 To-Be)

### New Components

```
NEW BOUNDED CONTEXT:
  src/scheduler/
    domain/
      entities.py          # PipelineRun, ScheduleConfig
      value_objects.py     # PipelineStage, RunStatus, DailyBudget, StrategyApproval
      events.py            # PipelineStartedEvent, StageCompletedEvent, PipelineCompletedEvent
      services.py          # PipelineOrchestratorService (chains stages)
      repositories.py      # IPipelineRunRepository, IScheduleConfigRepository
      __init__.py
    application/
      commands.py          # RunPipelineCommand, ApproveStrategyCommand, SetBudgetCommand
      handlers.py          # PipelineRunHandler, StrategyApprovalHandler
      __init__.py
    infrastructure/
      apscheduler_adapter.py   # APScheduler integration
      sqlite_pipeline_repo.py  # Pipeline run history
      sqlite_config_repo.py    # Schedule + approval config
      __init__.py
    DOMAIN.md

NEW PRESENTATION LAYER:
  dashboard/
    app.py                 # FastAPI app (personal dashboard, not commercial)
    routes/
      overview.py          # Portfolio overview, P&L
      pipeline.py          # Pipeline status, history
      approval.py          # Strategy/budget approval forms
      trades.py            # Trade history, execution log
      risk.py              # Risk dashboard (drawdown, exposure)
      sse.py               # SSE endpoint for real-time updates
    templates/
      base.html            # Jinja2 base template (HTMX + DaisyUI/Tailwind)
      overview.html         # Portfolio overview page
      pipeline.html        # Pipeline status page
      approval.html        # Approval workflow page
      trades.html          # Trade history page
      risk.html            # Risk metrics page
      partials/            # HTMX partial templates for live updates
    static/
      css/                 # Tailwind output
      js/                  # Minimal JS (HTMX only, no framework)
    __init__.py

MODIFIED EXISTING CONTEXTS:
  src/execution/
    domain/
      value_objects.py     # + DailyBudget, BudgetStatus, ExecutionMode (PAPER/LIVE)
      events.py            # Already has OrderExecutedEvent, OrderFailedEvent
      services.py          # + BudgetEnforcementService, CircuitBreakerService
      repositories.py      # + IBudgetRepository
    application/
      commands.py          # + AutoExecuteWithBudgetCommand
      handlers.py          # + AutoExecutionHandler (budget-checked execution)
    infrastructure/
      alpaca_adapter.py    # paper=False support (already designed, add safeguards)
      sqlite_budget_repo.py  # NEW: daily budget tracking
      order_monitor.py       # NEW: real-time order status polling

  src/portfolio/
    domain/
      events.py            # Already has DrawdownAlertEvent (wire it to bus)
    application/
      handlers.py          # + get_dashboard_summary() query method

  src/shared/
    infrastructure/
      event_bus.py         # Already async-capable, no changes needed
```

### Component Boundaries (v1.2)

| Component | Responsibility | Communicates With | New/Modified |
|-----------|---------------|-------------------|--------------|
| `scheduler` | Pipeline orchestration, cron scheduling, strategy/budget config | All handlers via commands, event bus | **NEW** bounded context |
| `execution` (modified) | Live execution with budget enforcement, order monitoring | scheduler (receives auto-execute commands), portfolio (risk checks), broker (Alpaca live) | **Modified** -- budget service, live mode, circuit breaker |
| `portfolio` (modified) | Dashboard summary queries, real-time P&L | execution (receives order results), dashboard (serves summaries) | **Modified** -- dashboard query methods |
| `dashboard` | Web UI presentation layer | scheduler, execution, portfolio via handlers + SSE via event bus | **NEW** presentation layer |
| `data_ingest` | Unchanged | scheduler triggers ingest_universe() | Unchanged |
| `scoring` | Unchanged | scheduler triggers score commands | Unchanged |
| `signals` | Unchanged | scheduler triggers signal commands | Unchanged |
| `regime` | Unchanged | scheduler triggers regime detection | Unchanged |

---

## Integration Point 1: Automated Pipeline Scheduler

### Architecture Decision: APScheduler as In-Process Scheduler

**Use APScheduler** (v3.x stable, not v4 alpha) with `AsyncIOScheduler` running inside the same process as the FastAPI dashboard. APScheduler provides persistent job stores (SQLite-backed), cron-style scheduling, and misfire grace time -- all needed for a daily trading pipeline.

**Why not systemd cron / external scheduler:** The pipeline scheduler needs access to the same DDD handlers, event bus, and database connections as the rest of the system. Running it in-process avoids inter-process communication complexity. APScheduler's SQLite job store provides restart resilience.

**Why not Celery/Temporal:** Overkill for a single-user system with one daily pipeline run. The pipeline is sequential (ingest -> score -> signal -> plan -> execute), not a distributed workflow.

### Pipeline Orchestration Service

The `PipelineOrchestratorService` in `scheduler/domain/` defines the pipeline as a sequence of stages. Each stage maps to an existing DDD handler:

```python
# scheduler/domain/services.py
class PipelineOrchestratorService:
    """Orchestrates the daily trading pipeline as a sequence of stages.

    Each stage wraps an existing DDD handler. The service enforces
    stage ordering, tracks progress, and publishes stage events.
    """

    STAGES = [
        PipelineStage.DATA_INGEST,    # DataPipeline.ingest_universe()
        PipelineStage.REGIME_DETECT,   # DetectRegimeHandler.handle()
        PipelineStage.SCORE,           # ScoreSymbolHandler.handle() x N tickers
        PipelineStage.SIGNAL,          # GenerateSignalHandler.handle() x scored tickers
        PipelineStage.PLAN,            # TradePlanHandler.generate() x BUY signals
        PipelineStage.BUDGET_CHECK,    # BudgetEnforcementService.check()
        PipelineStage.AUTO_EXECUTE,    # TradePlanHandler.execute() within budget
    ]

    def run_pipeline(self, run_config: PipelineRunConfig) -> PipelineRun:
        """Execute all stages sequentially. Returns run summary."""
        ...
```

### Pipeline Run Entity

```python
# scheduler/domain/entities.py
@dataclass
class PipelineRun(Entity):
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus = RunStatus.RUNNING  # RUNNING, COMPLETED, FAILED, ABORTED
    stages: list[StageResult] = field(default_factory=list)
    tickers_processed: int = 0
    signals_generated: int = 0
    plans_created: int = 0
    orders_executed: int = 0
    budget_remaining: float = 0.0
```

### Schedule Configuration

```python
# scheduler/domain/value_objects.py
@dataclass(frozen=True)
class ScheduleConfig(ValueObject):
    """Daily pipeline schedule configuration."""
    cron_expression: str = "0 10 * * 1-5"  # 10:00 AM, weekdays (after market open)
    market: str = "US"
    universe: str = "sp500"
    enabled: bool = True
    max_tickers: int = 100  # limit per run to control duration
```

### APScheduler Integration

```python
# scheduler/infrastructure/apscheduler_adapter.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

class APSchedulerAdapter:
    """Wraps APScheduler for pipeline scheduling."""

    def __init__(self, db_path: str, pipeline_handler: PipelineRunHandler):
        jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{db_path}")}
        self._scheduler = AsyncIOScheduler(jobstores=jobstores)
        self._handler = pipeline_handler

    async def start(self) -> None:
        self._scheduler.start()

    async def stop(self) -> None:
        self._scheduler.shutdown()

    def schedule_daily_pipeline(self, config: ScheduleConfig) -> None:
        self._scheduler.add_job(
            self._handler.run_daily,
            trigger=CronTrigger.from_crontab(config.cron_expression),
            id="daily_pipeline",
            replace_existing=True,
            misfire_grace_time=3600,  # 1 hour grace for missed runs
        )
```

### Data Flow Change

```
BEFORE (v1.1): User manually runs each CLI command in sequence
AFTER  (v1.2): APScheduler triggers PipelineOrchestratorService daily

APScheduler (cron: "0 10 * * 1-5")
    |
    v
PipelineOrchestratorService.run_pipeline()
    |
    |-- Stage 1: DataPipeline.ingest_universe()        --> DuckDB
    |   publishes: StageCompletedEvent(DATA_INGEST)
    |
    |-- Stage 2: DetectRegimeHandler.handle()           --> SQLite
    |   publishes: StageCompletedEvent(REGIME_DETECT)
    |
    |-- Stage 3: ScoreSymbolHandler.handle() x N        --> SQLite
    |   publishes: StageCompletedEvent(SCORE)
    |
    |-- Stage 4: GenerateSignalHandler.handle() x M     --> SQLite
    |   publishes: StageCompletedEvent(SIGNAL)
    |
    |-- Stage 5: TradePlanHandler.generate() x BUY      --> SQLite
    |   publishes: StageCompletedEvent(PLAN)
    |
    |-- Stage 6: BudgetEnforcementService.check()
    |   filters plans within daily budget
    |
    |-- Stage 7: AutoExecutionHandler.execute() x approved
    |   publishes: OrderExecutedEvent / OrderFailedEvent
    |
    v
PipelineRun (COMPLETED) --> SQLite (pipeline history)
    |
    publishes: PipelineCompletedEvent
    |
    v
Dashboard SSE --> Browser update
```

**Complexity:** MEDIUM. The orchestration logic is new but each stage delegates to existing handlers. The main risk is error handling between stages (what happens if scoring fails for 50% of tickers -- does the pipeline continue or abort?).

---

## Integration Point 2: Strategy/Budget Approval Workflow

### Architecture Decision: Approval as Domain State, Not External Workflow

The approval workflow is a domain concept in the `scheduler` bounded context, not an external workflow engine. The user approves a **strategy configuration** (which strategies to use, risk parameters) and a **daily budget** (max capital to deploy per day). Individual trade plans are then auto-approved within these constraints.

This is deliberately different from v1.0's per-trade approval. In v1.2, the human approves the _rules_, not each _trade_.

### Strategy Approval Value Objects

```python
# scheduler/domain/value_objects.py
@dataclass(frozen=True)
class StrategyApproval(ValueObject):
    """Human-approved strategy configuration for automated pipeline."""
    strategy: str = "swing"                # swing | position
    min_composite_score: float = 65.0      # minimum score to generate signal
    min_signal_strength: float = 0.6       # minimum fusion strength for trade plan
    max_positions: int = 10                # maximum concurrent positions
    max_sector_exposure: float = 0.25      # 25% sector cap
    approved_at: datetime | None = None
    approved_by: str = "owner"             # single-user system
    valid_until: datetime | None = None    # expiry for re-approval

    def is_valid(self) -> bool:
        if self.valid_until is None:
            return self.approved_at is not None
        return self.approved_at is not None and datetime.now(UTC) < self.valid_until

@dataclass(frozen=True)
class DailyBudget(ValueObject):
    """Daily capital deployment limit for automated execution."""
    max_daily_capital: float = 5000.0      # max USD to deploy per day
    max_orders_per_day: int = 3            # max number of orders per day
    max_single_order: float = 2500.0       # max capital per single order
    approved_at: datetime | None = None
    valid_until: datetime | None = None

    def is_valid(self) -> bool:
        if self.valid_until is None:
            return self.approved_at is not None
        return self.approved_at is not None and datetime.now(UTC) < self.valid_until
```

### Approval State Machine

```
StrategyApproval lifecycle:
  DRAFT --> [user reviews] --> APPROVED --> [time passes or user revokes] --> EXPIRED/REVOKED
                          |
                          +--> REJECTED

DailyBudget lifecycle:
  DRAFT --> [user sets amount] --> ACTIVE --> [daily reset at market open] --> ACTIVE (reset)
                              |                                          |
                              +--> PAUSED [user pauses]                  +--> EXHAUSTED (daily limit hit)

TradePlan lifecycle (v1.2 extended):
  PENDING --> BUDGET_CHECK --> AUTO_APPROVED --> EXECUTED
                           |                |
                           +--> BUDGET_EXCEEDED (deferred to next day)
                                            |
                                            +--> FAILED
```

### Budget Enforcement Service

```python
# execution/domain/services.py (new addition)
class BudgetEnforcementService:
    """Enforces daily budget limits on trade plan auto-execution."""

    def check_budget(
        self,
        plan: TradePlan,
        budget: DailyBudget,
        today_spent: float,
        today_orders: int,
    ) -> BudgetCheckResult:
        if not budget.is_valid():
            return BudgetCheckResult(allowed=False, reason="Budget not approved")
        if today_spent + plan.position_value > budget.max_daily_capital:
            return BudgetCheckResult(allowed=False, reason="Daily capital limit exceeded")
        if today_orders >= budget.max_orders_per_day:
            return BudgetCheckResult(allowed=False, reason="Daily order count limit exceeded")
        if plan.position_value > budget.max_single_order:
            return BudgetCheckResult(allowed=False, reason="Single order limit exceeded")
        return BudgetCheckResult(allowed=True, remaining=budget.max_daily_capital - today_spent - plan.position_value)
```

### Dashboard Approval Flow

```
User opens Dashboard --> Approval page
    |
    v
Sees current strategy config + daily budget
    |-- Modifies parameters (score threshold, budget, etc.)
    |-- Clicks "Approve Strategy" or "Set Daily Budget"
    |
    v
POST /dashboard/api/approve-strategy  --> StrategyApprovalHandler.approve()
POST /dashboard/api/set-budget        --> StrategyApprovalHandler.set_budget()
    |
    v
Config stored in SQLite --> Scheduler reads at next pipeline run
```

**Complexity:** MEDIUM. The approval logic is straightforward state management. The main design challenge is defining the right granularity -- approving a strategy vs. approving individual trades vs. approving a daily budget. The recommended approach (approve rules, auto-execute within rules) matches the project constraint: "human approves strategy + daily budget, execution is automatic."

---

## Integration Point 3: Alpaca Live Trading

### Architecture Decision: Same Adapter, Configuration Switch + Safeguard Layer

The existing `AlpacaExecutionAdapter` already parameterizes `paper=True`. Live trading changes this to `paper=False`. However, live trading requires a safeguard layer that does not exist in v1.0.

**What changes for live:**

```python
# settings.py (extended)
class Settings(BaseSettings):
    # Existing
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None

    # NEW for v1.2
    ALPACA_LIVE_API_KEY: Optional[str] = None    # separate live keys
    ALPACA_LIVE_SECRET_KEY: Optional[str] = None
    EXECUTION_MODE: str = "paper"                 # "paper" | "live"
    LIVE_MAX_DAILY_CAPITAL: float = 5000.0
    LIVE_MAX_SINGLE_ORDER: float = 2500.0
    LIVE_CIRCUIT_BREAKER_LOSS: float = 0.03       # 3% daily loss triggers halt
```

### Safeguard Architecture

The safeguard layer wraps `IBrokerAdapter` with pre-execution checks:

```python
# execution/domain/services.py (new)
class SafeExecutionService:
    """Wraps broker adapter with safety checks for live trading.

    Enforces: budget limits, circuit breaker, position limits, drawdown defense.
    All checks happen BEFORE the order reaches the broker adapter.
    """

    def __init__(
        self,
        broker: IBrokerAdapter,
        budget_service: BudgetEnforcementService,
        circuit_breaker: CircuitBreakerService,
    ):
        self._broker = broker
        self._budget = budget_service
        self._breaker = circuit_breaker

    def execute_safely(self, spec: OrderSpec, budget: DailyBudget, ...) -> OrderResult:
        # 1. Circuit breaker check (daily loss limit)
        if self._breaker.is_tripped():
            return OrderResult(status="CIRCUIT_BREAKER_TRIPPED", ...)

        # 2. Budget enforcement
        budget_check = self._budget.check_budget(...)
        if not budget_check.allowed:
            return OrderResult(status="BUDGET_EXCEEDED", ...)

        # 3. Execute via broker
        result = self._broker.submit_order(spec)

        # 4. Update circuit breaker state
        self._breaker.record_execution(result)

        return result
```

### Circuit Breaker Service

```python
# execution/domain/services.py (new)
class CircuitBreakerService:
    """Halts all execution if daily losses exceed threshold.

    Implements the 3-tier drawdown defense from project constraints:
    - Tier 1 (10%): no new entries, monitoring only
    - Tier 2 (15%): reduce positions 50%
    - Tier 3 (20%): full liquidation, 1-month cooldown
    """

    def __init__(self, loss_threshold: float = 0.03):
        self._daily_loss_threshold = loss_threshold
        self._tripped = False
        self._daily_pnl = 0.0

    def is_tripped(self) -> bool:
        return self._tripped

    def record_execution(self, result: OrderResult) -> None:
        # Track daily P&L from filled orders
        ...

    def reset_daily(self) -> None:
        """Called at market open to reset daily circuit breaker."""
        self._tripped = False
        self._daily_pnl = 0.0
```

### Order Monitoring

For live trading, the system needs to poll Alpaca for order status updates (fills, partial fills, rejections). This is a new infrastructure concern:

```python
# execution/infrastructure/order_monitor.py
class AlpacaOrderMonitor:
    """Polls Alpaca for order status updates and publishes events.

    Runs as a background task in the FastAPI/scheduler process.
    Polling interval: every 30 seconds during market hours.
    """

    def __init__(self, adapter: AlpacaExecutionAdapter, bus: AsyncEventBus):
        self._adapter = adapter
        self._bus = bus

    async def poll_orders(self) -> None:
        """Check pending orders for status changes."""
        # Get open orders from Alpaca
        # Compare with local state
        # Publish OrderExecutedEvent / OrderFailedEvent for changes
        ...
```

### Paper-to-Live Migration Path

```
Phase 1 (current): paper=True, manual CLI execution
Phase 2 (v1.2a):   paper=True, automated pipeline with budget enforcement
Phase 3 (v1.2b):   paper=False, automated pipeline with full safeguards
```

The migration is progressive. First, validate the automated pipeline works correctly with paper trading. Only then switch to live with real money. The budget enforcement and circuit breaker work identically in both modes.

**Complexity:** MEDIUM-HIGH. The Alpaca API change is trivial, but the safeguard layer (budget enforcement, circuit breaker, order monitoring) is new domain logic that must be correct -- errors mean real money loss.

---

## Integration Point 4: Web Dashboard

### Architecture Decision: FastAPI + Jinja2 + HTMX + SSE

**Use FastAPI + Jinja2 templates + HTMX for interactions + SSE for real-time updates.** This approach:

1. **Stays Python-centric** -- no JavaScript framework to learn, build, or maintain
2. **Leverages existing FastAPI** -- the commercial API already runs FastAPI; the dashboard is a second FastAPI app
3. **HTMX handles interactions** -- form submissions, partial page updates, polling -- without client-side state management
4. **SSE for real-time** -- pipeline progress, order fills, portfolio P&L updates stream to the browser without WebSocket complexity
5. **DaisyUI/Tailwind for styling** -- pre-built component library, no custom CSS design needed

**Why not React/Vue/Svelte:** The project is Python-centric (20K+ LOC Python, zero JS). Adding a JavaScript SPA framework doubles the technology surface, requires a build pipeline (node, npm, webpack/vite), and introduces client-side state management complexity. HTMX achieves 90% of the interactivity with zero JavaScript framework code.

**Why not Streamlit/Gradio:** These are designed for ML demos, not production dashboards. They lack fine-grained layout control, cannot handle complex forms (approval workflows), and have poor real-time streaming support.

**Why SSE over WebSocket:** The dashboard is server-push-only (pipeline status, order updates, P&L changes). The browser never sends data back through the real-time channel -- form submissions use standard HTTP POST via HTMX. SSE is simpler (standard HTTP, auto-reconnect, no connection upgrade negotiation).

### Dashboard Architecture

```
Browser (HTMX + SSE)
    |
    |-- HTTP GET/POST --> FastAPI routes --> Jinja2 templates
    |                         |
    |                         |-- Read: handlers, repositories (same as CLI/API)
    |                         |-- Write: approval commands, budget commands
    |
    |-- SSE stream    --> /dashboard/sse/events
                            |
                            |-- Subscribes to AsyncEventBus
                            |-- Streams: PipelineStageEvent, OrderEvent, PortfolioEvent
```

### Dashboard Pages

| Page | URL | Data Source | Real-Time? |
|------|-----|------------|------------|
| Portfolio Overview | `/dashboard/` | PortfolioManagerHandler, AlpacaAdapter.get_positions() | Yes (SSE: P&L, position changes) |
| Pipeline Status | `/dashboard/pipeline` | IPipelineRunRepository | Yes (SSE: stage progress) |
| Strategy Approval | `/dashboard/approval` | IScheduleConfigRepository | No (form submission) |
| Trade History | `/dashboard/trades` | ITradePlanRepository | Yes (SSE: new executions) |
| Risk Dashboard | `/dashboard/risk` | Portfolio aggregate, drawdown calculations | Yes (SSE: drawdown alerts) |
| Scoring Results | `/dashboard/scores` | IScoreRepository | No (batch display) |

### SSE Event Stream

```python
# dashboard/routes/sse.py
from sse_starlette.sse import EventSourceResponse

@router.get("/sse/events")
async def event_stream(request: Request):
    """Server-Sent Events endpoint for real-time dashboard updates."""
    async def generate():
        queue = asyncio.Queue()

        # Subscribe to relevant events
        bus = get_event_bus()
        bus.subscribe(PipelineStageCompletedEvent, lambda e: queue.put_nowait(e))
        bus.subscribe(OrderExecutedEvent, lambda e: queue.put_nowait(e))
        bus.subscribe(OrderFailedEvent, lambda e: queue.put_nowait(e))
        bus.subscribe(DrawdownAlertEvent, lambda e: queue.put_nowait(e))

        try:
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                yield {
                    "event": event.__class__.__name__,
                    "data": json.dumps(event_to_dict(event)),
                }
        finally:
            # Unsubscribe cleanup
            ...

    return EventSourceResponse(generate())
```

### HTMX Partial Updates

Each dashboard page has a full-page template and partial templates. HTMX swaps partials on user interaction (tab click, form submit) and on SSE events:

```html
<!-- templates/partials/portfolio_summary.html -->
<div id="portfolio-summary" hx-swap-oob="true">
  <div class="stat">
    <div class="stat-title">Portfolio Value</div>
    <div class="stat-value">${{ portfolio.total_value | format_currency }}</div>
    <div class="stat-desc {{ 'text-success' if portfolio.daily_pnl >= 0 else 'text-error' }}">
      {{ portfolio.daily_pnl | format_currency }} ({{ portfolio.daily_pnl_pct | format_pct }})
    </div>
  </div>
</div>
```

### Dashboard Mounting

The dashboard is a separate FastAPI app, mounted alongside the commercial API. This keeps personal dashboard features separate from commercial API endpoints:

```python
# main.py (top-level)
from commercial.api.main import app as commercial_app
from dashboard.app import app as dashboard_app

root_app = FastAPI()
root_app.mount("/api", commercial_app)       # Commercial API at /api/v1/...
root_app.mount("/dashboard", dashboard_app)  # Personal dashboard at /dashboard/...
```

**Complexity:** MEDIUM. The FastAPI + Jinja2 + HTMX stack is well-documented. The SSE integration with the event bus is the novel part. The main effort is building 5-6 HTML templates with Tailwind styling and wiring them to existing handler queries.

---

## Data Flow (v1.2 Target -- Automated)

### Daily Pipeline (Automated)

```
APScheduler (10:00 AM EST, weekdays)
    |
    v
PipelineOrchestratorService
    |
    |-- [CHECK] StrategyApproval.is_valid()?
    |   NO  --> PipelineAbortedEvent --> Dashboard SSE --> "Approval expired" alert
    |   YES |
    |       v
    |-- Stage 1: DataPipeline.ingest_universe(universe="sp500", market="US")
    |   --> DuckDB (ohlcv, financials)
    |   --> StageCompletedEvent(DATA_INGEST, tickers=100)
    |   --> Dashboard SSE update
    |
    |-- Stage 2: DetectRegimeHandler.handle(auto_fetch=True)
    |   --> SQLite (market_regimes)
    |   --> RegimeChangedEvent (if regime changed) --> scoring weight update
    |   --> StageCompletedEvent(REGIME_DETECT)
    |
    |-- Stage 3: ScoreSymbolHandler.handle() x 100 tickers
    |   --> SQLite (composite_scores)
    |   --> StageCompletedEvent(SCORE, scored=100, above_threshold=25)
    |
    |-- Stage 4: GenerateSignalHandler.handle() x 25 above-threshold
    |   --> SQLite (signals)
    |   --> StageCompletedEvent(SIGNAL, buy=5, hold=15, sell=5)
    |
    |-- Stage 5: TradePlanHandler.generate() x 5 BUY signals
    |   --> SQLite (trade_plans, status=PENDING)
    |   --> TradePlanCreatedEvent x 5
    |   --> StageCompletedEvent(PLAN, plans=5)
    |
    |-- Stage 6: BudgetEnforcementService.check() x 5 plans
    |   --> Filter: 3 plans within budget, 2 exceed
    |   --> StageCompletedEvent(BUDGET_CHECK, approved=3, deferred=2)
    |
    |-- Stage 7: SafeExecutionService.execute_safely() x 3 plans
    |   --> Alpaca API (paper or live)
    |   --> OrderExecutedEvent x 3 (or OrderFailedEvent)
    |   --> SQLite (trade_plans, status=EXECUTED)
    |   --> StageCompletedEvent(AUTO_EXECUTE, executed=3)
    |
    v
PipelineCompletedEvent(run_id, summary)
    --> Dashboard SSE --> "Pipeline complete: 3 orders executed"
    --> Pipeline history stored in SQLite
```

### Real-Time Dashboard Updates

```
AsyncEventBus (in-process)
    |
    |-- PipelineStageCompletedEvent --> SSE --> Dashboard pipeline progress bar
    |-- OrderExecutedEvent          --> SSE --> Dashboard trade log + portfolio update
    |-- OrderFailedEvent            --> SSE --> Dashboard error notification
    |-- DrawdownAlertEvent          --> SSE --> Dashboard risk alert banner
    |-- RegimeChangedEvent          --> SSE --> Dashboard regime indicator update
```

---

## EventBus Subscription Map (v1.2 Complete)

```
PipelineStartedEvent
  --> Dashboard SSE (show pipeline running indicator)

StageCompletedEvent
  --> Dashboard SSE (update pipeline progress bar)
  --> PipelineRunRepository (log stage results)

PipelineCompletedEvent
  --> Dashboard SSE (show completion summary)
  --> PipelineRunRepository (close run record)

RegimeChangedEvent
  --> ConcreteRegimeWeightAdjuster (update scoring weights)  [EXISTING, already wired]
  --> Dashboard SSE (update regime indicator)                 [NEW]

ScoreUpdatedEvent
  --> (future: auto-trigger signal generation)

TradePlanCreatedEvent
  --> Dashboard SSE (show new pending plans)

OrderExecutedEvent
  --> PortfolioManagerHandler.on_order_executed() (sync portfolio)  [NEW]
  --> Dashboard SSE (update trade log + portfolio)                  [NEW]
  --> CircuitBreakerService.record_execution()                     [NEW]

OrderFailedEvent
  --> Dashboard SSE (show error notification)  [NEW]
  --> CircuitBreakerService.record_failure()   [NEW]

DrawdownAlertEvent
  --> Dashboard SSE (show risk alert)                [NEW]
  --> CircuitBreakerService.check_drawdown_tier()    [NEW]
```

---

## Database Architecture (v1.2)

### SQLite (Operational -- Extended)

| Table | Context | Status | Purpose |
|-------|---------|--------|---------|
| `composite_scores` | scoring | Existing | Score results |
| `signals` | signals | Existing | Signal results |
| `market_regimes` | regime | Existing | Regime history |
| `positions` | portfolio | Existing | Open positions |
| `trade_plans` | execution | Existing | Trade plan lifecycle |
| `watchlist` | portfolio | Existing | Watchlist entries |
| `pipeline_runs` | scheduler | **NEW** | Pipeline run history |
| `pipeline_stages` | scheduler | **NEW** | Per-stage results |
| `schedule_config` | scheduler | **NEW** | Cron config + enabled flag |
| `strategy_approvals` | scheduler | **NEW** | Approved strategy configs |
| `daily_budgets` | scheduler | **NEW** | Daily budget config + spending |
| `budget_transactions` | execution | **NEW** | Per-order capital spent |
| `circuit_breaker_state` | execution | **NEW** | Daily P&L tracking for circuit breaker |
| `api_keys` | commercial | Existing | API key management |

### DuckDB (Analytics -- No Changes)

DuckDB remains unchanged. All new v1.2 data is operational (pipeline runs, budgets, approvals) and belongs in SQLite. DuckDB continues to serve analytical queries (OHLCV, financials, screening).

---

## Patterns to Follow

### Pattern 1: Orchestrator Service as Pipeline Stage Runner

**What:** The `PipelineOrchestratorService` runs stages sequentially, each delegating to an existing DDD handler. It does NOT import domain objects from other contexts -- it passes primitive values between stages via command parameters.

**When:** Building the automated pipeline.

**Why this matters:** This avoids the "God Orchestrator" anti-pattern identified in v1.1 research. Each stage is independently testable because it uses the same handler interface as the CLI.

```python
# scheduler/application/handlers.py
class PipelineRunHandler:
    def __init__(self, score_handler, signal_handler, regime_handler, ...):
        # All handlers injected via bootstrap.py
        self._score_handler = score_handler
        ...

    async def run_stage_score(self, tickers: list[str]) -> StageResult:
        results = []
        for ticker in tickers:
            result = self._score_handler.handle(ScoreSymbolCommand(symbol=ticker))
            results.append(result)
        return StageResult(stage=PipelineStage.SCORE, results=results)
```

### Pattern 2: SSE as EventBus Consumer

**What:** The SSE endpoint subscribes to the `AsyncEventBus` via an asyncio.Queue bridge. Events flow: domain handler -> bus.publish() -> queue -> SSE yield -> browser.

**When:** Building real-time dashboard updates.

**Why this matters:** The event bus already exists and events are already defined. SSE just becomes another subscriber, no architectural changes needed.

### Pattern 3: Budget as Pre-Execution Gate

**What:** Budget enforcement happens BEFORE the order reaches the broker adapter, not after. The `SafeExecutionService` wraps `IBrokerAdapter` and rejects orders that exceed budget.

**When:** Building live execution with budget limits.

**Why this matters:** Checking budget after execution is too late -- the money is already deployed. The gate must be synchronous and blocking.

### Pattern 4: Approval Config as Value Object, Not Workflow State

**What:** Strategy approval and daily budget are immutable VOs stored in SQLite. The pipeline reads the latest approved config at the start of each run. There is no complex workflow engine -- the user either approves or does not.

**When:** Building the approval workflow.

**Why this matters:** Trading system approval is simple (approved/not approved) unlike enterprise approval chains (multiple reviewers, escalation). Over-engineering this with a workflow engine adds complexity without value.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Scheduler Directly Calling Core/ Functions

**What:** The pipeline scheduler bypasses DDD handlers and calls `core/scoring/fundamental.py` directly "for efficiency."

**Why bad:** Creates a third execution path (CLI -> handlers, API -> handlers, scheduler -> core/) with different behavior. Bugs fixed in handlers don't get fixed in scheduler.

**Instead:** The scheduler MUST call the same DDD handlers as the CLI and API. If performance is an issue, optimize the handlers, not the caller.

### Anti-Pattern 2: WebSocket for Dashboard When SSE Suffices

**What:** Using WebSocket for the dashboard real-time connection because "it's more powerful."

**Why bad:** WebSocket requires connection upgrade, has no auto-reconnect in the browser, requires explicit ping/pong for keepalive, and adds bidirectional complexity when the dashboard only needs server-to-client push.

**Instead:** Use SSE. It auto-reconnects, works over standard HTTP, and HTMX has native SSE support via `hx-sse="connect:/dashboard/sse/events"`.

### Anti-Pattern 3: Shared Database Writes Between Scheduler and Dashboard

**What:** Both the scheduler (writing pipeline results) and the dashboard (writing approval configs) write to the same SQLite tables concurrently.

**Why bad:** SQLite has a single-writer lock. Concurrent writes from scheduler and dashboard will cause "database is locked" errors.

**Instead:** Use WAL mode (`PRAGMA journal_mode=WAL`) for all SQLite databases. The scheduler writes to `pipeline_runs`/`budget_transactions`, and the dashboard writes to `strategy_approvals`/`daily_budgets` -- these are different tables, so WAL mode handles it fine. Only contention arises if both write to the same database file simultaneously, which WAL mode resolves.

### Anti-Pattern 4: Live Trading Without Paper Validation

**What:** Switching to `paper=False` without first validating the automated pipeline works correctly in paper mode.

**Why bad:** Bugs in pipeline orchestration (wrong ticker format, budget calculation error, circuit breaker not triggering) cause real money loss.

**Instead:** The migration path is: manual paper -> automated paper -> automated live. Each transition requires a validation period (minimum 2 weeks of successful automated paper runs before switching to live).

---

## Scalability Considerations

| Concern | Current State (v1.1) | v1.2 (100 tickers/day) | Future (500 tickers/day) |
|---------|---------------------|----------------------|------------------------|
| Pipeline duration | N/A (manual) | ~15 min (100 tickers, sequential scoring) | ~45 min (need parallel scoring) |
| SQLite writes | Low frequency (CLI) | Burst during pipeline (~500 writes in 15 min) | WAL mode + connection pooling |
| Event bus throughput | <10 events/day | ~200 events/day (stages + orders) | In-process queue, no bottleneck |
| SSE connections | N/A | 1-2 browser tabs | 1-2 browser tabs (personal use) |
| Alpaca API rate | Manual orders | 3-5 orders/day | 10-15 orders/day (well within Alpaca limits) |
| Dashboard response time | N/A | <200ms (Jinja2 rendering) | Redis cache for expensive queries |

---

## Build Order (Dependency-Driven)

The four v1.2 features have the following dependency chain:

```
1. scheduler bounded context (domain + infrastructure)
   Dependencies: existing handlers (all stable from v1.1)
   Blocks: automated pipeline, approval workflow

2. Strategy/budget approval workflow
   Dependencies: scheduler domain (approval VOs)
   Blocks: auto-execution (needs approved budget)

3. Live trading safeguards (budget enforcement, circuit breaker)
   Dependencies: approval workflow (budget config), existing execution context
   Blocks: live execution

4. Automated pipeline orchestration
   Dependencies: scheduler + approval + safeguards all in place
   Blocks: nothing (this is the integration point)

5. Web dashboard (presentation layer)
   Dependencies: all of the above (displays their state)
   Blocks: nothing (purely additive)
```

**Recommended build order:**

1. **Scheduler bounded context** (LOW-MEDIUM complexity, HIGH value) -- foundation for everything else. Domain entities, VOs, repository interfaces.

2. **Strategy/budget approval** (LOW complexity, HIGH value) -- simple CRUD for approval configs. Enables automated execution.

3. **Pipeline orchestration** (MEDIUM complexity, HIGH value) -- chains existing handlers. Validates the scheduler works with paper trading.

4. **Live trading safeguards** (MEDIUM-HIGH complexity, CRITICAL value) -- budget enforcement, circuit breaker, order monitoring. Must be correct before live money.

5. **Web dashboard** (MEDIUM complexity, HIGH value) -- visualization of all the above. Can be built incrementally (start with portfolio overview, add pages one by one).

**Rationale:** The scheduler and approval workflow are prerequisites for automated execution. Live safeguards must exist before any auto-execution (even paper). The dashboard comes last because it is a read-only view of state managed by the other components -- it does not block any functionality. However, the dashboard approval page is needed for the approval workflow to be usable beyond CLI, so a minimal dashboard with just the approval form could be built alongside phase 2.

---

## Bootstrap.py Changes (Composition Root)

The existing `bootstrap.py` returns a dict of handlers. For v1.2, it needs to also wire the scheduler and dashboard components:

```python
# bootstrap.py (extended for v1.2)
def bootstrap(
    db_factory: DBFactory | None = None,
    market: str = "us",
    mode: str = "cli",  # "cli" | "scheduler" | "dashboard"
) -> dict:
    """Create a fully wired application context.

    mode="cli":       SyncEventBus, no scheduler
    mode="scheduler": AsyncEventBus, APScheduler, SafeExecutionService
    mode="dashboard": AsyncEventBus, SSE subscriptions, read-heavy
    """
    # ... existing wiring ...

    if mode in ("scheduler", "dashboard"):
        bus = AsyncEventBus()  # Use async bus for scheduler/dashboard

        # Scheduler-specific wiring
        pipeline_repo = SqlitePipelineRunRepository(db_factory.sqlite_path("scheduler"))
        config_repo = SqliteScheduleConfigRepository(db_factory.sqlite_path("scheduler"))
        budget_repo = SqliteBudgetRepository(db_factory.sqlite_path("scheduler"))

        budget_service = BudgetEnforcementService()
        circuit_breaker = CircuitBreakerService(loss_threshold=settings.LIVE_CIRCUIT_BREAKER_LOSS)
        safe_execution = SafeExecutionService(adapter, budget_service, circuit_breaker)

        pipeline_handler = PipelineRunHandler(
            score_handler=score_handler,
            signal_handler=signal_handler,
            regime_handler=regime_handler,
            portfolio_handler=portfolio_handler,
            trade_plan_handler=trade_plan_handler,
            safe_execution=safe_execution,
            pipeline_repo=pipeline_repo,
            config_repo=config_repo,
            budget_repo=budget_repo,
            bus=bus,
        )

        # ... return extended context dict ...
```

---

## Sources

- Direct codebase analysis of `/home/mqz/workspace/trading/src/` (8 bounded contexts, 116 Python files) -- HIGH confidence
- Direct codebase analysis of `/home/mqz/workspace/trading/cli/main.py` (existing CLI commands and handler usage) -- HIGH confidence
- Direct codebase analysis of `/home/mqz/workspace/trading/commercial/api/` (existing FastAPI infrastructure) -- HIGH confidence
- Direct codebase analysis of `/home/mqz/workspace/trading/src/execution/` (existing broker adapter, trade plan lifecycle) -- HIGH confidence
- APScheduler documentation: [APScheduler User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) -- HIGH confidence (stable v3.x)
- Alpaca Python SDK: [Alpaca-py Getting Started](https://alpaca.markets/sdks/python/getting_started.html) -- HIGH confidence (paper=True/False switch verified)
- FastAPI SSE: [FastAPI SSE Tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/) -- HIGH confidence (official docs)
- sse-starlette: [PyPI sse-starlette](https://pypi.org/project/sse-starlette/) -- MEDIUM confidence (community package, production-used)
- HTMX + FastAPI: [TestDriven.io HTMX FastAPI](https://testdriven.io/blog/fastapi-htmx/) -- MEDIUM confidence (tutorial, not official docs)
- [FastHX GitHub](https://github.com/volfpeter/fasthx) -- MEDIUM confidence (server-side rendering library for FastAPI+HTMX)
- v1.1 Architecture research: `.planning/research/ARCHITECTURE.md` (previous milestone) -- HIGH confidence
- v1.1 Pitfalls research: `.planning/research/PITFALLS.md` (previous milestone) -- HIGH confidence
- Project constraints: `.planning/PROJECT.md` -- HIGH confidence
