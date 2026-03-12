# Phase 4: Execution and Interface - Research

**Researched:** 2026-03-12
**Domain:** Trade execution (Alpaca paper trading), CLI interface (Typer + Rich), DDD bounded contexts (execution, interface)
**Confidence:** HIGH

## Summary

Phase 4 bridges the decision engine (Phase 3 output: signals, risk sizing, trade plans) to actual execution and user interaction. Two new bounded contexts are needed: `execution` (trade plan generation, Alpaca order management) and a CLI presentation layer that surfaces portfolio dashboards, screeners, watchlists, and monitoring alerts.

The existing codebase already has substantial infrastructure to build on: `personal/execution/planner.py` generates entry/exit plans, `personal/execution/paper_trading.py` wraps Alpaca with a mock fallback, `core/orchestrator.py` runs the 9-layer pipeline, `cli/main.py` has 5 working commands (version, regime, score, signal, analyze), and the `src/portfolio/` bounded context provides Position/Portfolio entities, SQLite repos, and risk services. The key work is: (1) creating an `execution` bounded context with DDD-compliant trade plan VOs, an Alpaca adapter using `alpaca-py` (the current official SDK), and bracket order support; (2) extending the CLI with human-approval workflow, dashboard, screener, watchlist, and alert commands; (3) wiring the execution domain to the existing portfolio/signals/valuation domains via the event bus.

**Primary recommendation:** Build the execution bounded context first (domain VOs + Alpaca adapter with bracket orders), then layer the CLI commands on top. Migrate from the legacy `alpaca-trade-api` to `alpaca-py` in the adapter. Keep mock fallback for offline/testing.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EXEC-01 | Trade Plan generation (entry/stop/target/size/reasoning) | Existing `personal/execution/planner.py` provides base logic; wrap as TradePlan VO in new execution bounded context with full audit trail linking back to scoring/valuation outputs |
| EXEC-02 | Human Approval CLI (Y/N + modify before order) | Typer `confirm()` + Rich table for plan display; TradePlanStatus enum (PENDING/APPROVED/REJECTED/MODIFIED) in domain |
| EXEC-03 | Alpaca Paper Trading execution | Migrate existing `PaperTradingClient` to use `alpaca-py` SDK (`TradingClient(paper=True)`); keep mock fallback for tests |
| EXEC-04 | Bracket Order (entry + stop-loss + take-profit) | `alpaca-py` supports `OrderClass.BRACKET` with `MarketOrderRequest`/`LimitOrderRequest` + `TakeProfitRequest` + `StopLossRequest` |
| INTF-01 | CLI Dashboard (portfolio view, P&L, drawdown) | Rich Table + Panel using existing `Portfolio` aggregate + `SqlitePositionRepository.find_all_open()` |
| INTF-02 | Stock Screener CLI (interactive filtering/ranking) | Existing `DuckDBSignalStore.query_top_n()` provides the query; wrap in CLI command with Rich table |
| INTF-03 | Watchlist management (CRUD + alert config) | New SQLite table for watchlists; simple CRUD commands via Typer |
| INTF-04 | Monitoring alerts (stop hit, target reached, drawdown tier) | Event bus subscription to `DrawdownAlertEvent`, `PositionClosedEvent`; new alert events for stop/target; Rich console output |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| alpaca-py | >=0.43 | Alpaca paper trading SDK | Official SDK, replaces deprecated alpaca-trade-api; pydantic-based models |
| typer | >=0.9 | CLI framework | Already in pyproject.toml; built-in confirm/prompt |
| rich | >=13.0 | Terminal UI (tables, panels, live display) | Already dependency of typer; provides Table, Panel, Confirm, Live |
| duckdb | >=1.0 | Analytics queries (screener) | Already used for scores/valuations/signals tables |
| sqlite3 | stdlib | Operational state (positions, portfolios, watchlists) | Already used for portfolio.db |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.0 | Settings for Alpaca credentials | Already in pyproject.toml; ALPACA_API_KEY/SECRET_KEY config |
| python-dotenv | >=1.0 | Environment variable loading | Already used in paper_trading.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| alpaca-py | alpaca-trade-api | Legacy, in maintenance mode; alpaca-py is official |
| Rich Live dashboard | Textual TUI | Textual is heavier; Rich Live is sufficient for CLI dashboard and already a dependency |
| sqlite3 watchlists | JSON file | SQLite handles concurrent access better; consistent with existing position/portfolio storage |

**Installation:**
```bash
pip install alpaca-py>=0.43
```

Note: typer, rich, duckdb, pydantic, python-dotenv are already in pyproject.toml. Only `alpaca-py` needs to be added. The legacy `alpaca-trade-api` import in `personal/execution/paper_trading.py` will be replaced.

## Architecture Patterns

### Recommended Project Structure
```
src/
  execution/                    # NEW bounded context
    domain/
      value_objects.py          # TradePlan, OrderResult, BracketSpec, TradePlanStatus
      events.py                 # TradePlanCreatedEvent, OrderExecutedEvent, OrderFailedEvent
      services.py               # TradePlanService (pure: plan generation from scoring+risk data)
      repositories.py           # ITradePlanRepository, IOrderLogRepository (ABC)
      __init__.py               # Public API
    application/
      commands.py               # GenerateTradePlanCommand, ApproveTradePlanCommand, ExecuteOrderCommand
      handlers.py               # TradePlanHandler (orchestrates plan->approve->execute flow)
      __init__.py
    infrastructure/
      alpaca_adapter.py         # AlpacaExecutionAdapter (alpaca-py TradingClient wrapper)
      sqlite_trade_plan_repo.py # SQLite trade plan persistence
      sqlite_order_log.py       # SQLite order execution log
      __init__.py
    DOMAIN.md
  portfolio/                    # EXTEND existing context
    infrastructure/
      sqlite_watchlist_repo.py  # NEW: watchlist CRUD
    domain/
      value_objects.py          # ADD: WatchlistEntry VO (or separate watchlist module)
      repositories.py           # ADD: IWatchlistRepository
cli/
  main.py                       # EXTEND: add new commands
```

### Pattern 1: Adapter-Only Delegation (Established Pattern)
**What:** Infrastructure adapters delegate to existing `personal/` and `core/` functions without rewriting math.
**When to use:** Connecting DDD bounded context to existing business logic.
**Example:**
```python
# Source: established pattern from CoreRiskAdapter, CoreSignalAdapter
class AlpacaExecutionAdapter:
    """Wraps alpaca-py TradingClient. Falls back to mock when no credentials."""
    def __init__(self, api_key: str | None = None, secret_key: str | None = None):
        self._use_mock = not (api_key and secret_key)
        if not self._use_mock:
            from alpaca.trading.client import TradingClient
            self._client = TradingClient(api_key, secret_key, paper=True)

    def submit_bracket_order(self, spec: BracketSpec) -> OrderResult:
        if self._use_mock:
            return self._mock_bracket(spec)
        from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
        req = MarketOrderRequest(
            symbol=spec.symbol,
            qty=spec.quantity,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=spec.take_profit_price),
            stop_loss=StopLossRequest(stop_price=spec.stop_loss_price),
        )
        order = self._client.submit_order(order_data=req)
        return OrderResult(order_id=order.id, status=order.status.value, ...)
```

### Pattern 2: Frozen Dataclass Value Objects (Established Pattern)
**What:** All VOs are `@dataclass(frozen=True)` with `_validate()` method called by `ValueObject.__post_init__`.
**When to use:** Every domain value object in this project.
**Example:**
```python
# Source: established pattern from ATRStop, TakeProfitLevels, KellyFraction
@dataclass(frozen=True)
class TradePlan(ValueObject):
    symbol: str
    direction: str                # "BUY" | "SELL"
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    quantity: int
    position_value: float
    reasoning_trace: str          # links back to scoring/valuation
    composite_score: float
    margin_of_safety: float
    signal_direction: str

    def _validate(self) -> None:
        if self.entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.stop_loss_price >= self.entry_price:
            raise ValueError("Stop-loss must be below entry for BUY")
```

### Pattern 3: Human-in-the-Loop Approval Flow
**What:** CLI presents trade plan, user approves/rejects/modifies, only then execute.
**When to use:** EXEC-02 requirement.
**Example:**
```python
# Source: Typer official docs (https://typer.tiangolo.com/tutorial/prompt/)
import typer
from rich.table import Table
from rich.console import Console

def approve_trade_plan(plan: dict) -> dict:
    console = Console()
    table = Table(title=f"Trade Plan: {plan['symbol']}")
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Entry Price", f"${plan['entry_price']:,.2f}")
    table.add_row("Stop-Loss", f"${plan['stop_loss']:,.2f}")
    table.add_row("Take-Profit", f"${plan['take_profit']:,.2f}")
    table.add_row("Shares", str(plan['shares']))
    console.print(table)

    approved = typer.confirm("Execute this trade?", default=False)
    if not approved:
        return {"status": "REJECTED", **plan}
    return {"status": "APPROVED", **plan}
```

### Pattern 4: Event-Driven Cross-Context Communication
**What:** Bounded contexts communicate only via domain events published through AsyncEventBus.
**When to use:** When execution results need to update portfolio state, or drawdown changes need to trigger alerts.
**Example:**
```python
# Source: established pattern from shared/infrastructure/event_bus.py
# execution context publishes -> portfolio context subscribes
bus.subscribe(OrderExecutedEvent, portfolio_handler.on_order_executed)
bus.subscribe(DrawdownAlertEvent, alert_handler.on_drawdown_alert)
```

### Anti-Patterns to Avoid
- **Direct cross-context imports:** execution/ must NOT import from portfolio/domain directly. Use events or shared kernel types.
- **Rewriting math:** Do NOT reimplement Kelly/ATR/drawdown logic in execution domain. Delegate via adapters to personal/ modules.
- **Live API calls in domain layer:** Alpaca SDK calls belong ONLY in infrastructure/. Domain stays pure.
- **Blocking CLI for real-time data:** Do NOT use Rich Live for main commands. Use one-shot table rendering. Live display only if explicitly building a monitoring mode.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bracket orders | Manual 3-order submission + tracking | alpaca-py `OrderClass.BRACKET` | Alpaca handles order lifecycle atomically |
| CLI confirmation | Custom input() loops | `typer.confirm()` | Handles Y/N/abort gracefully |
| Terminal tables | print() formatting | `rich.Table` + `rich.Panel` | Consistent with existing CLI |
| Position tracking | Custom dict-based state | Existing `SqlitePositionRepository` | Already built and tested |
| Drawdown calculation | New math | Existing `Portfolio.drawdown` + `PortfolioRiskService` | Already validated in Phase 3 |
| Trade plan sizing | New Kelly/ATR code | Existing `personal/sizer/kelly.py` + `personal/execution/planner.py` | Phase 3 tested this |

**Key insight:** Phase 4 is primarily an integration phase. Almost all business logic already exists in `personal/` and `src/portfolio/domain/`. The new work is (1) a thin DDD execution context wrapping the existing planner/paper_trading, (2) Alpaca SDK migration, and (3) CLI commands wiring everything together.

## Common Pitfalls

### Pitfall 1: alpaca-py Import at Module Level
**What goes wrong:** Importing alpaca-py at module top level breaks the entire system when credentials are not set or package not installed.
**Why it happens:** Unlike requests/httpx, alpaca-py may try to validate credentials on import.
**How to avoid:** Use lazy imports inside methods (already established pattern in `paper_trading.py`). Only import alpaca-py inside the `if not self._use_mock` branch.
**Warning signs:** ImportError or ValidationError on `import alpaca`

### Pitfall 2: Bracket Order Time-in-Force
**What goes wrong:** Bracket orders with `TimeInForce.GTC` (Good Til Cancel) may behave differently than expected.
**Why it happens:** Alpaca bracket orders require `TimeInForce.DAY` for the legs; GTC on the parent + DAY on legs is the standard pattern.
**How to avoid:** Always use `TimeInForce.DAY` for bracket orders. The parent market order fills immediately; the stop/take-profit legs persist as DAY orders.
**Warning signs:** Orders rejected with "invalid time_in_force for bracket"

### Pitfall 3: Paper Trading Does Not Simulate Dividends
**What goes wrong:** Mid-term holds (weeks to months) show incorrect P&L because paper trading ignores dividends.
**Why it happens:** Alpaca paper trading is execution simulation only.
**How to avoid:** This is a known limitation (documented in STATE.md blockers). Accept it for v1. Separate dividend tracking can be added later.
**Warning signs:** P&L divergence from expected for dividend stocks

### Pitfall 4: Mock Mode Breaking Real Execution Path
**What goes wrong:** Tests pass with mock but real Alpaca execution fails because code paths diverge.
**Why it happens:** Mock returns immediately; real API is async and may reject orders.
**How to avoid:** Adapter should normalize Order/Position dataclasses identically for both paths. Mock should simulate realistic responses (partial fills, rejections).
**Warning signs:** Different return types from mock vs real path

### Pitfall 5: Orphaned Domain Events
**What goes wrong:** Events published but never consumed, leading to silent failures.
**Why it happens:** Event subscriptions not wired up in the composition root.
**How to avoid:** Explicit subscription registration at app startup. Test that each event type has at least one subscriber.
**Warning signs:** Events silently dropped with no error

## Code Examples

Verified patterns from the existing codebase and official documentation:

### Bracket Order with alpaca-py
```python
# Source: https://docs.alpaca.markets/docs/working-with-orders
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

client = TradingClient('api-key', 'secret-key', paper=True)

bracket = MarketOrderRequest(
    symbol="AAPL",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY,
    order_class=OrderClass.BRACKET,
    take_profit=TakeProfitRequest(limit_price=180.00),
    stop_loss=StopLossRequest(stop_price=140.00),
)
order = client.submit_order(order_data=bracket)
```

### Limit Entry Bracket Order
```python
# Source: https://docs.alpaca.markets/docs/working-with-orders
from alpaca.trading.requests import LimitOrderRequest

limit_bracket = LimitOrderRequest(
    symbol="AAPL",
    qty=10,
    limit_price=150.00,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY,
    order_class=OrderClass.BRACKET,
    take_profit=TakeProfitRequest(limit_price=180.00),
    stop_loss=StopLossRequest(stop_price=140.00),
)
order = client.submit_order(order_data=limit_bracket)
```

### Position and Account Retrieval
```python
# Source: https://alpaca.markets/sdks/python/trading.html
positions = client.get_all_positions()  # list[Position]
account = client.get_account()          # TradeAccount
orders = client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
```

### Typer Confirm + Rich Table (CLI Approval)
```python
# Source: https://typer.tiangolo.com/tutorial/prompt/
import typer
from rich.console import Console
from rich.table import Table

console = Console()

@app.command()
def approve(symbol: str):
    """Review and approve a pending trade plan."""
    # ... load plan from repo ...
    table = Table(title=f"Trade Plan: {symbol}")
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Direction", "BUY")
    table.add_row("Entry", "$150.00")
    table.add_row("Stop-Loss", "$140.00")
    table.add_row("Take-Profit", "$180.00")
    table.add_row("Shares", "22")
    table.add_row("Risk %", "0.23%")
    console.print(table)

    if typer.confirm("Execute this trade?", default=False):
        # ... execute order ...
        console.print("[bold green]Order submitted.[/bold green]")
    else:
        console.print("[yellow]Trade plan rejected.[/yellow]")
```

### Rich Dashboard Table (Portfolio View)
```python
# Source: established pattern from cli/main.py + Rich docs
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

console = Console()

def render_dashboard(positions: list, portfolio_value: float, drawdown: float, drawdown_level: str):
    # Header panel
    dd_color = {"normal": "green", "caution": "yellow", "warning": "red", "critical": "bold red"}.get(drawdown_level, "white")
    console.print(Panel(
        f"Portfolio: ${portfolio_value:,.2f} | Drawdown: [{dd_color}]{drawdown:.1%}[/{dd_color}] ({drawdown_level})",
        title="Portfolio Dashboard",
    ))

    # Positions table
    table = Table(title="Open Positions", show_header=True, header_style="bold cyan")
    table.add_column("Symbol", style="bold")
    table.add_column("Qty", justify="right")
    table.add_column("Entry", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("Stop", justify="right")
    for pos in positions:
        pnl = (pos.current_price - pos.avg_entry_price) * pos.qty
        pnl_color = "green" if pnl >= 0 else "red"
        table.add_row(
            pos.symbol, str(pos.qty),
            f"${pos.avg_entry_price:,.2f}", f"${pos.current_price:,.2f}",
            f"[{pnl_color}]${pnl:,.2f}[/{pnl_color}]",
            f"${pos.stop_price:,.2f}" if hasattr(pos, 'stop_price') else "N/A",
        )
    console.print(table)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| alpaca-trade-api | alpaca-py | 2023 (maintenance mode) | Must migrate; new SDK uses pydantic models, OOP request objects |
| Manual 3-order bracket | `OrderClass.BRACKET` | Available since alpaca-py launch | Single API call handles entry+stop+target atomically |
| print() CLI output | Rich Table/Panel | Already adopted | Consistent with existing CLI |
| Imperative API calls | TradingClient OOP | alpaca-py design | Request objects (MarketOrderRequest, etc.) instead of kwargs |

**Deprecated/outdated:**
- `alpaca-trade-api` (alpaca_trade_api package): In maintenance mode. Current codebase in `paper_trading.py` uses this. Must migrate to `alpaca-py`.
- `api.submit_order(**kwargs)` pattern: Replaced by `client.submit_order(order_data=RequestObject)` in alpaca-py.

## Open Questions

1. **Alpaca Paper Account Credentials**
   - What we know: Environment vars `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are expected. Mock mode activates when absent.
   - What's unclear: Whether user has paper account set up.
   - Recommendation: Keep mock fallback as primary development path. Real Alpaca integration is opt-in via env vars.

2. **Watchlist Storage Location**
   - What we know: SQLite is used for operational state (portfolio.db). DuckDB for analytics.
   - What's unclear: Should watchlists go in portfolio.db or a separate file?
   - Recommendation: Add watchlists table to existing `data/portfolio.db` for consistency with positions/portfolios.

3. **Alert Delivery Mechanism**
   - What we know: INTF-04 requires alerts for stop hit, target reached, drawdown tier change.
   - What's unclear: How to deliver alerts (terminal output? log file? push notification?).
   - Recommendation: For v1, alerts are Rich console output during monitoring commands. Log to SQLite for audit. No push notifications in v1.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 7.4 + pytest-asyncio >= 0.21 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_FILE.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXEC-01 | TradePlan VO creation with valid fields + reasoning trace | unit | `pytest tests/unit/test_trade_plan.py -x` | Wave 0 |
| EXEC-02 | Human approval flow (approve/reject/modify) | unit | `pytest tests/unit/test_trade_approval.py -x` | Wave 0 |
| EXEC-03 | AlpacaExecutionAdapter mock mode + bracket order | unit | `pytest tests/unit/test_alpaca_adapter.py -x` | Wave 0 |
| EXEC-04 | Bracket order spec creation + validation | unit | `pytest tests/unit/test_bracket_order.py -x` | Wave 0 |
| INTF-01 | Dashboard command renders portfolio table | unit | `pytest tests/unit/test_cli_dashboard.py -x` | Wave 0 |
| INTF-02 | Screener command renders top-N results | unit | `pytest tests/unit/test_cli_screener.py -x` | Wave 0 |
| INTF-03 | Watchlist CRUD operations | unit | `pytest tests/unit/test_watchlist.py -x` | Wave 0 |
| INTF-04 | Alert events fire on stop/target/drawdown | unit | `pytest tests/unit/test_alerts.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_CHANGED_FILE.py -x`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_trade_plan.py` -- covers EXEC-01
- [ ] `tests/unit/test_trade_approval.py` -- covers EXEC-02
- [ ] `tests/unit/test_alpaca_adapter.py` -- covers EXEC-03 (replaces/extends test_paper_trading.py)
- [ ] `tests/unit/test_bracket_order.py` -- covers EXEC-04
- [ ] `tests/unit/test_cli_dashboard.py` -- covers INTF-01
- [ ] `tests/unit/test_cli_screener.py` -- covers INTF-02 (extends existing test_screener.py)
- [ ] `tests/unit/test_watchlist.py` -- covers INTF-03
- [ ] `tests/unit/test_alerts.py` -- covers INTF-04

Note: `tests/unit/test_execution_planner.py`, `tests/unit/test_paper_trading.py`, and `tests/unit/test_cli_commands.py` already exist and test the legacy `personal/` layer. New tests will test the DDD-compliant `src/execution/` and extended `cli/` layers.

## Sources

### Primary (HIGH confidence)
- Alpaca official docs: https://docs.alpaca.markets/docs/working-with-orders -- bracket order API, request classes
- Alpaca-py SDK docs: https://alpaca.markets/sdks/python/trading.html -- TradingClient, positions, account
- Alpaca-py PyPI: https://pypi.org/project/alpaca-py/ -- version 0.43.2, Python 3.8+
- Typer official docs: https://typer.tiangolo.com/tutorial/prompt/ -- confirm(), prompt()
- Rich docs: https://rich.readthedocs.io/en/stable/live.html -- Live display, Table, Panel

### Secondary (MEDIUM confidence)
- Alpaca community forum: https://forum.alpaca.markets/t/bracket-order-code-example-with-alpaca-py-library/12110 -- bracket order examples verified against official docs
- Rich dashboard guide: https://www.willmcgugan.com/blog/tech/post/building-rich-terminal-dashboards/ -- Layout + Live patterns

### Tertiary (LOW confidence)
- None -- all findings verified against official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project or official Alpaca SDK
- Architecture: HIGH -- follows established DDD patterns from Phases 1-3 exactly
- Pitfalls: HIGH -- based on official docs + existing codebase patterns + STATE.md blockers
- Alpaca bracket API: HIGH -- verified against official docs

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable -- alpaca-py, typer, rich are mature libraries)
