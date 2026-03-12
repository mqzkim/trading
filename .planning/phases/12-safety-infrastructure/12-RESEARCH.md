# Phase 12: Safety Infrastructure - Research

**Researched:** 2026-03-13
**Domain:** Execution safety, mode switching, state persistence, broker reconciliation
**Confidence:** HIGH

## Summary

Phase 12 transforms the existing execution layer from a development-friendly mock-fallback system into a production-safe trading system. The core changes are: (1) explicit paper/live mode switching via env config instead of implicit credential detection, (2) removing the dangerous mock-fallback pattern in live mode that silently returns phantom fills on failures, (3) persisting drawdown cooldown state in SQLite so it survives restarts, (4) reconciling local position records with broker state at startup, and (5) providing kill-switch CLI commands for emergency scenarios.

The existing codebase provides a solid foundation. The `IBrokerAdapter` ABC, `AlpacaExecutionAdapter`, `TradePlanHandler`, and portfolio domain (drawdown detection, `PortfolioRiskService`) are all in place. The primary work is wrapping `AlpacaExecutionAdapter` with safety checks, extending `Settings` with `EXECUTION_MODE` and separate key pairs, adding two new SQLite tables, and adding order status polling and bracket leg verification using the alpaca-py SDK's `get_order_by_id(nested=True)` and `Order.legs` field.

**Primary recommendation:** Use the Decorator pattern -- create `SafeExecutionAdapter` that wraps any `IBrokerAdapter`, adding mode enforcement, failure policy, cooldown checks, and order polling. This keeps `AlpacaExecutionAdapter` unchanged and testable independently.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- EXECUTION_MODE=paper|live enum in .env only -- CLI flag switching prohibited (accident prevention)
- Default is paper -- credentials alone cannot trigger live mode
- Live mode startup requires confirmation prompt ("Are you sure? yes/no") -- cron automation needs --confirm flag
- Separate API keys: ALPACA_PAPER_KEY/SECRET + ALPACA_LIVE_KEY/SECRET -- EXECUTION_MODE selects automatically
- Live mode order failure: log + skip symbol + continue next symbol
- Mock fallback absolutely prohibited in live mode -- _mock_bracket_order() call path completely removed
- Current `_real_bracket_order()` except block returning mock result MUST be removed
- Consecutive failure count deferred to Phase 15 circuit breaker (LIVE-06)
- Pipeline startup: 1-time SQLite vs broker position reconciliation check
- Mismatch found: detailed diff output + block new orders (halt pipeline)
- Resolution: `trade sync` CLI command syncs to broker state (user approves after reviewing diff)
- No dynamic check during execution -- startup check only
- SQLite cooldown table: triggered_at, expires_at (30 days), current_tier (10/15/20), re_entry_pct (0/25/50/75/100)
- Process restart restores cooldown state from SQLite
- --force-override flag for manual override (emergency) + warning message
- During cooldown: data collection/scoring/signals continue, only order submission blocked
- Post-cooldown re-entry: 25% capital in 4 stages (strategy-recommendation.md rule)
- Kill switch two modes:
  - `trade kill` -- cancel all open orders + halt pipeline immediately (no confirmation)
  - `trade kill --liquidate` -- cancel + market-sell all positions (confirmation required)
- Kill triggers automatic cooldown entry (reason + timestamp recorded)
- Kill prevents emotional re-entry

### Claude's Discretion
- SafeExecutionAdapter internal implementation pattern (wrap existing AlpacaExecutionAdapter vs new class)
- SQLite cooldown/reconciliation table schema details
- Order status polling interval and timeout values
- Bracket order leg verification implementation approach
- Confirmation prompt UX (Rich prompt vs simple input)

### Deferred Ideas (OUT OF SCOPE)
- WebSocket real-time order monitoring -- Phase 15 (LIVE-04)
- Circuit breaker (3 consecutive failures auto-halt) -- Phase 15 (LIVE-06)
- Dashboard kill switch button -- Phase 16 (DASH-06)
- KIS broker safety -- future separate phase
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SAFE-01 | Explicit EXECUTION_MODE setting (paper/live enum, defaults paper), live cannot trigger by credentials alone | Settings extension with Literal enum, bootstrap mode branching |
| SAFE-02 | Live mode uses separate adapter with no mock fallback -- failures raise errors, never phantom fills | SafeExecutionAdapter wrapping pattern, remove except->mock path in _real_bracket_order |
| SAFE-03 | Paper and live Alpaca accounts use separate API key pairs | ALPACA_PAPER_KEY/SECRET + ALPACA_LIVE_KEY/SECRET in Settings, mode-based selection in bootstrap |
| SAFE-04 | Pipeline startup reconciles SQLite positions with Alpaca broker positions, flags divergences | Reconciliation service comparing position_repo.find_all_open() vs adapter.get_positions() |
| SAFE-05 | Drawdown cooldown persists in SQLite, survives restarts (30-day cooling period) | New cooldown_state SQLite table, CooldownRepository, startup restoration |
| SAFE-06 | Kill switch cancels all open orders and halts pipeline via CLI | `trade kill` and `trade kill --liquidate` using client.cancel_orders() and client.close_all_positions() |
| SAFE-07 | System polls order status until terminal state before proceeding | get_order_by_id() polling loop with configurable interval/timeout, terminal status detection |
| SAFE-08 | After bracket fill, verifies stop-loss and take-profit legs confirmed active | get_order_by_id(nested=True) to access Order.legs, verify leg statuses are "new" or "held" |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| alpaca-py | 0.43.2 (installed) | Broker API (orders, positions, cancel) | Already in use, TradingClient provides all needed methods |
| sqlite3 | stdlib | Cooldown state persistence, position storage | Already used throughout (SqliteTradePlanRepository pattern) |
| pydantic-settings | 2.x (installed) | EXECUTION_MODE config, API key management | Already used for Settings class |
| typer | 0.9+ (installed) | CLI kill/sync commands | Already used for all CLI commands |
| rich | 13.0+ (installed) | Confirmation prompts, diff output, tables | Already used throughout CLI |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| time.sleep | stdlib | Order polling interval | Between get_order_by_id calls |
| enum.Enum | stdlib | ExecutionMode enum | EXECUTION_MODE validation |
| logging | stdlib | Order failure logging, safety audit trail | All safety-critical operations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Decorator SafeExecutionAdapter | Subclass AlpacaExecutionAdapter | Decorator is cleaner -- keeps Alpaca adapter unchanged, works for both US/KR |
| SQLite cooldown table | JSON file | SQLite already established pattern, ACID transactions, query capability |
| Polling loop | WebSocket streaming | WebSocket deferred to Phase 15 (LIVE-04), polling sufficient for now |

**Installation:**
No new packages needed. All dependencies already installed.

## Architecture Patterns

### Recommended Project Structure
```
src/
  execution/
    domain/
      repositories.py       # IBrokerAdapter ABC (existing) + ICooldownRepository (new)
      value_objects.py       # ExecutionMode enum (new), existing VOs
      services.py            # TradePlanService (existing)
      events.py              # KillSwitchActivatedEvent, CooldownTriggeredEvent (new)
    application/
      handlers.py            # TradePlanHandler (existing, minimal changes)
      commands.py            # (existing, add KillSwitchCommand, SyncPositionsCommand)
      safety_service.py      # SafetyOrchestrationService (new) -- coordinates safety checks
    infrastructure/
      alpaca_adapter.py      # AlpacaExecutionAdapter (fix: remove mock fallback in except)
      safe_adapter.py        # SafeExecutionAdapter (new) -- wraps IBrokerAdapter
      sqlite_cooldown_repo.py  # SqliteCooldownRepository (new)
      reconciliation.py      # PositionReconciliationService (new)
  settings.py                # Add EXECUTION_MODE, ALPACA_PAPER_KEY/SECRET, ALPACA_LIVE_KEY/SECRET
  bootstrap.py               # Mode-based adapter selection
cli/
  main.py                    # Add `trade kill`, `trade sync` commands
```

### Pattern 1: Decorator Adapter (SafeExecutionAdapter)
**What:** SafeExecutionAdapter wraps any IBrokerAdapter, intercepting submit_order to enforce safety policies (mode check, cooldown check, order polling, leg verification).
**When to use:** Always in production -- bootstrap.py wraps the raw adapter with SafeExecutionAdapter.
**Example:**
```python
# Source: project DDD pattern from IBrokerAdapter
class SafeExecutionAdapter(IBrokerAdapter):
    """Safety wrapper around any broker adapter.

    Enforces: mode validation, no-mock-in-live, cooldown blocking,
    order polling, bracket leg verification.
    """
    def __init__(
        self,
        inner: IBrokerAdapter,
        mode: ExecutionMode,
        cooldown_repo: ICooldownRepository,
        poll_interval: float = 2.0,
        poll_timeout: float = 60.0,
    ) -> None:
        self._inner = inner
        self._mode = mode
        self._cooldown_repo = cooldown_repo
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        # 1. Check cooldown blocks order submission
        cooldown = self._cooldown_repo.get_active()
        if cooldown and not cooldown.is_expired():
            raise CooldownActiveError(cooldown)

        # 2. Submit via inner adapter
        result = self._inner.submit_order(spec)

        # 3. Poll until terminal state (SAFE-07)
        if self._mode == ExecutionMode.LIVE:
            result = self._poll_order_status(result.order_id)
            # 4. Verify bracket legs (SAFE-08)
            self._verify_bracket_legs(result.order_id)

        return result
```

### Pattern 2: Mode-Based Bootstrap Wiring
**What:** bootstrap.py reads EXECUTION_MODE and wires the correct adapter with correct credentials.
**When to use:** Application startup.
**Example:**
```python
# Source: existing bootstrap.py pattern at line 102-128
from src.settings import settings

mode = settings.EXECUTION_MODE  # "paper" | "live"

if mode == ExecutionMode.LIVE:
    raw_adapter = AlpacaExecutionAdapter(
        api_key=settings.ALPACA_LIVE_KEY,
        secret_key=settings.ALPACA_LIVE_SECRET,
    )
else:
    raw_adapter = AlpacaExecutionAdapter(
        api_key=settings.ALPACA_PAPER_KEY,
        secret_key=settings.ALPACA_PAPER_SECRET,
    )

# Wrap with safety layer
adapter = SafeExecutionAdapter(
    inner=raw_adapter,
    mode=mode,
    cooldown_repo=cooldown_repo,
)
```

### Pattern 3: Order Status Polling
**What:** After order submission, poll `get_order_by_id()` until terminal state.
**When to use:** SAFE-07 -- every order in live mode.
**Example:**
```python
# Source: alpaca-py 0.43.2 TradingClient API
from alpaca.trading.requests import GetOrderByIdRequest

TERMINAL_STATUSES = {
    OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.EXPIRED,
    OrderStatus.REJECTED, OrderStatus.REPLACED,
}

def _poll_order_status(self, order_id: str) -> OrderResult:
    """Poll until order reaches terminal state."""
    start = time.monotonic()
    while time.monotonic() - start < self._poll_timeout:
        order = self._client.get_order_by_id(
            order_id,
            filter=GetOrderByIdRequest(nested=True),
        )
        if order.status in TERMINAL_STATUSES:
            return self._order_to_result(order)
        time.sleep(self._poll_interval)
    raise OrderTimeoutError(f"Order {order_id} did not reach terminal state")
```

### Pattern 4: Bracket Leg Verification
**What:** After parent order fills, verify stop-loss and take-profit child orders exist and are active.
**When to use:** SAFE-08 -- after bracket order fill confirmation.
**Example:**
```python
# Source: alpaca-py Order model -- legs: Optional[List[Order]]
def _verify_bracket_legs(self, order_id: str) -> None:
    """Verify bracket order has active stop-loss and take-profit legs."""
    order = self._client.get_order_by_id(
        order_id,
        filter=GetOrderByIdRequest(nested=True),
    )
    if order.order_class != OrderClass.BRACKET:
        return  # Not a bracket order, nothing to verify

    if not order.legs or len(order.legs) < 2:
        raise BracketLegError(
            f"Bracket order {order_id} missing legs "
            f"(expected 2, got {len(order.legs) if order.legs else 0})"
        )

    # Legs should be in "new" or "held" status after parent fills
    ACTIVE_LEG_STATUSES = {"new", "held", "accepted"}
    for leg in order.legs:
        if leg.status.value not in ACTIVE_LEG_STATUSES:
            logger.warning(
                "Bracket leg %s has unexpected status: %s",
                leg.id, leg.status.value,
            )
```

### Anti-Patterns to Avoid
- **Mock fallback in live mode:** The current `_real_bracket_order` except block returns `self._mock_bracket_order(spec)` -- this is the exact bug SAFE-02 must fix. Live mode failures MUST raise or return error status, never phantom fills.
- **Credential-based mode detection:** Current pattern (`self._use_mock = not (api_key and secret_key)`) conflates "missing credentials" with "should use mock". Mode must be explicit via EXECUTION_MODE.
- **In-memory cooldown state:** Cooldown must survive process restarts. Never store cooldown only in Python memory.
- **Fire-and-forget orders:** Never submit an order and assume success without polling for terminal status.
- **Swallowing exceptions in live mode:** The current `_real_get_positions` and `_real_get_account` return empty/default values on exception. This is acceptable for paper mode but dangerous for live mode reconciliation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Order cancellation | Custom cancel loop per order | `client.cancel_orders()` (cancels ALL) | Alpaca's atomic bulk cancel, race-condition-safe |
| Position liquidation | Loop through positions manually | `client.close_all_positions(cancel_orders=True)` | Atomic operation, handles edge cases |
| Order status monitoring | Custom state machine | `get_order_by_id()` + `OrderStatus` enum | Alpaca maintains authoritative state, 18 possible states |
| Bracket leg access | Parse order IDs manually | `GetOrderByIdRequest(nested=True)` returns `Order.legs` | SDK handles parent-child relationship |
| Confirmation prompt | Custom input() parsing | `typer.confirm()` or `rich.prompt.Confirm.ask()` | Handles edge cases, consistent UX |
| Env config validation | Manual .env parsing | `pydantic-settings` with `Literal["paper", "live"]` | Type validation, defaults, env file loading |

**Key insight:** The alpaca-py SDK already provides all safety primitives (cancel_orders, close_all_positions, get_order_by_id with nested legs, OrderStatus enums). The work is in wiring these correctly, not reimplementing them.

## Common Pitfalls

### Pitfall 1: Bracket Order Legs Status "held"
**What goes wrong:** After parent bracket order fills, child orders (stop-loss, take-profit) may appear with status "held" instead of "new". This is normal Alpaca behavior, not an error.
**Why it happens:** Alpaca stages bracket legs as "held" until the parent order fills completely. After fill, one leg may transition to "new" while the other stays "held" briefly.
**How to avoid:** Accept both "new" and "held" as valid active states for bracket legs. Do not treat "held" as an error.
**Warning signs:** Test with paper trading first. Check `order.legs[i].status` values.

### Pitfall 2: Race Condition Between Cancel and Fill
**What goes wrong:** Kill switch calls `cancel_orders()` but some orders may have filled between the list and cancel operations.
**Why it happens:** Markets are real-time; orders can fill between API calls.
**How to avoid:** After `cancel_orders()`, re-check `get_orders(status="open")` to verify none remain. The `--liquidate` flag handles already-filled positions by closing them as well.
**Warning signs:** Open orders appearing after cancel_orders returns.

### Pitfall 3: SQLite Concurrent Access
**What goes wrong:** Multiple processes accessing the same SQLite cooldown table can cause locking issues.
**Why it happens:** Only one writer at a time for SQLite. Kill switch CLI and running pipeline may conflict.
**How to avoid:** Use WAL mode (`PRAGMA journal_mode=WAL`), keep transactions short. The trading system is single-process by design (STATE.md: "Single FastAPI process").
**Warning signs:** "database is locked" errors.

### Pitfall 4: Timezone Handling for Cooldown Expiry
**What goes wrong:** Cooldown expires_at stored without timezone, compared with local time, leading to premature or delayed cooldown end.
**Why it happens:** SQLite stores text, naive vs aware datetime confusion.
**How to avoid:** Always store UTC ISO format. Always compare in UTC. Use `datetime.now(timezone.utc)`.
**Warning signs:** Cooldown ending at unexpected times.

### Pitfall 5: Paper Mode Credentials Missing is OK
**What goes wrong:** System fails to start in paper mode because ALPACA_PAPER_KEY is not set.
**Why it happens:** Not all users have Alpaca credentials, especially in development.
**How to avoid:** Paper mode without credentials should fall back to mock gracefully. Only live mode requires valid credentials. The mock fallback is ONLY prohibited in live mode.
**Warning signs:** Dev/test environments breaking.

### Pitfall 6: Polling Timeout for Market-Hours Orders
**What goes wrong:** Order polling times out because the order was submitted outside market hours.
**Why it happens:** Market orders submitted before open sit as "accepted" or "new" until market opens.
**How to avoid:** Set reasonable timeout based on market hours. Consider making timeout configurable. Log a clear warning if timeout occurs.
**Warning signs:** OrderTimeoutError in logs around market open/close.

## Code Examples

Verified patterns from existing codebase and official SDK:

### AlpacaExecutionAdapter Fix (SAFE-02 Critical)
```python
# BEFORE (dangerous -- returns phantom fill on failure):
def _real_bracket_order(self, spec: BracketSpec) -> OrderResult:
    try:
        # ... submit order ...
    except Exception as e:
        logger.error("Alpaca bracket order failed for %s: %s", spec.symbol, e)
        return self._mock_bracket_order(spec)  # <-- PHANTOM FILL

# AFTER (safe -- raises error on failure):
def _real_bracket_order(self, spec: BracketSpec) -> OrderResult:
    try:
        # ... submit order ...
    except Exception as e:
        logger.error("Alpaca bracket order failed for %s: %s", spec.symbol, e)
        return OrderResult(
            order_id="",
            status="error",
            symbol=spec.symbol,
            quantity=spec.quantity,
            filled_price=None,
            error_message=str(e),
        )
```

### Settings Extension (SAFE-01, SAFE-03)
```python
# Source: existing src/settings.py pattern
from typing import Literal

class Settings(BaseSettings):
    # Execution mode (paper default, explicit setting required for live)
    EXECUTION_MODE: Literal["paper", "live"] = "paper"

    # Alpaca paper trading
    ALPACA_PAPER_KEY: Optional[str] = None
    ALPACA_PAPER_SECRET: Optional[str] = None

    # Alpaca live trading
    ALPACA_LIVE_KEY: Optional[str] = None
    ALPACA_LIVE_SECRET: Optional[str] = None

    # Legacy (backward compat, mapped to paper)
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
```

### Kill Switch (SAFE-06)
```python
# Source: alpaca-py 0.43.2 TradingClient API
# trade kill
@app.command()
def kill(
    liquidate: bool = typer.Option(False, "--liquidate", help="Also liquidate all positions"),
    market: str = typer.Option("us", "--market", "-m"),
):
    """Emergency kill switch -- cancel all orders, optionally liquidate."""
    if liquidate:
        if not typer.confirm("LIQUIDATE all positions? This cannot be undone."):
            raise typer.Exit()

    # Cancel all open orders
    client.cancel_orders()  # Returns List[CancelOrderResponse]

    if liquidate:
        # Close all positions with market orders
        client.close_all_positions(cancel_orders=True)

    # Record cooldown
    cooldown_repo.save(CooldownState(
        triggered_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        current_tier=20,
        re_entry_pct=0,
        reason="kill_switch",
    ))
```

### Position Reconciliation (SAFE-04)
```python
# Compare SQLite vs broker positions
def reconcile(
    local_positions: list[Position],
    broker_positions: list[dict],
) -> list[Discrepancy]:
    """Compare local SQLite positions with broker positions."""
    local_map = {p.symbol: p for p in local_positions}
    broker_map = {p["symbol"]: p for p in broker_positions}

    discrepancies = []
    all_symbols = set(local_map) | set(broker_map)

    for sym in all_symbols:
        local = local_map.get(sym)
        broker = broker_map.get(sym)

        if local and not broker:
            discrepancies.append(Discrepancy(sym, "local_only", local_qty=local.quantity))
        elif broker and not local:
            discrepancies.append(Discrepancy(sym, "broker_only", broker_qty=broker["qty"]))
        elif local and broker and local.quantity != broker["qty"]:
            discrepancies.append(Discrepancy(
                sym, "qty_mismatch",
                local_qty=local.quantity, broker_qty=broker["qty"],
            ))

    return discrepancies
```

### Cooldown State Table Schema
```sql
-- Source: project SQLite pattern from sqlite_trade_plan_repo.py
CREATE TABLE IF NOT EXISTS cooldown_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at    TEXT NOT NULL,           -- UTC ISO format
    expires_at      TEXT NOT NULL,           -- UTC ISO format (30 days after trigger)
    current_tier    INTEGER NOT NULL,        -- 10, 15, or 20 (drawdown %)
    re_entry_pct    INTEGER NOT NULL DEFAULT 0, -- 0, 25, 50, 75, 100
    reason          TEXT NOT NULL DEFAULT 'drawdown',  -- drawdown | kill_switch
    is_active       INTEGER NOT NULL DEFAULT 1,
    force_overridden INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `paper=True` hardcoded | EXECUTION_MODE env-based switching | This phase | paper/live mode separation |
| Credential detection for mock | Explicit mode + mock only in paper | This phase | No phantom fills in live |
| In-memory drawdown check | SQLite-persisted cooldown state | This phase | Survives restarts |
| Fire-and-forget orders | Poll until terminal state | This phase | No untracked orders |
| No kill switch | CLI kill + liquidate | This phase | Emergency response capability |

**Deprecated/outdated:**
- `self._use_mock = not (api_key and secret_key)` pattern: replaced by explicit EXECUTION_MODE
- `_real_bracket_order` except -> mock fallback: replaced by error return/raise
- `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` single key pair: replaced by separate paper/live key pairs (backward compat maintained)

## Open Questions

1. **Order polling interval in paper vs live mode**
   - What we know: Paper trading may have different latency characteristics than live
   - What's unclear: Optimal poll_interval for paper mode (Alpaca paper may fill instantly)
   - Recommendation: Default 2s interval, 60s timeout; make configurable. Paper mode can use shorter interval (0.5s) since fills are near-instant.

2. **Bracket leg "held" status duration**
   - What we know: Legs transition from "held" to "new" after parent fills. Forum reports show legs can stay "held" temporarily.
   - What's unclear: Exact timing -- how long can a leg stay "held" before it should be considered problematic
   - Recommendation: After parent fills, poll legs with 5s interval for up to 30s. Log warning if legs remain "held" after 30s but do not treat as error.

3. **Kill switch during non-market hours**
   - What we know: cancel_orders() works any time. close_all_positions() submits market orders that execute at next open.
   - What's unclear: Whether pending-market-open orders from close_all_positions could be canceled before execution
   - Recommendation: Kill switch should work at any time. If --liquidate is used outside market hours, warn user that liquidation orders will execute at next market open.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/test_alpaca_adapter.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SAFE-01 | EXECUTION_MODE defaults paper, live needs explicit setting | unit | `pytest tests/unit/test_safe_execution.py::test_default_paper_mode -x` | Wave 0 |
| SAFE-01 | Credentials alone do not trigger live mode | unit | `pytest tests/unit/test_safe_execution.py::test_credentials_alone_not_live -x` | Wave 0 |
| SAFE-02 | Live mode order failure raises error, no mock fallback | unit | `pytest tests/unit/test_safe_execution.py::test_live_no_mock_fallback -x` | Wave 0 |
| SAFE-02 | AlpacaExecutionAdapter _real_bracket_order returns error on exception | unit | `pytest tests/unit/test_alpaca_adapter.py::test_real_bracket_order_error -x` | Wave 0 |
| SAFE-03 | Paper and live use separate API key pairs | unit | `pytest tests/unit/test_safe_execution.py::test_separate_key_pairs -x` | Wave 0 |
| SAFE-04 | Reconciliation detects missing/extra/mismatched positions | unit | `pytest tests/unit/test_reconciliation.py -x` | Wave 0 |
| SAFE-04 | Pipeline halts on reconciliation mismatch | unit | `pytest tests/unit/test_reconciliation.py::test_halt_on_mismatch -x` | Wave 0 |
| SAFE-05 | Cooldown state persists and restores from SQLite | unit | `pytest tests/unit/test_cooldown_persistence.py -x` | Wave 0 |
| SAFE-05 | Cooldown survives process restart (read after write) | unit | `pytest tests/unit/test_cooldown_persistence.py::test_survives_restart -x` | Wave 0 |
| SAFE-05 | 30-day expiry calculated correctly | unit | `pytest tests/unit/test_cooldown_persistence.py::test_expiry_30_days -x` | Wave 0 |
| SAFE-05 | --force-override bypasses cooldown | unit | `pytest tests/unit/test_cooldown_persistence.py::test_force_override -x` | Wave 0 |
| SAFE-06 | Kill switch cancels all orders | unit | `pytest tests/unit/test_kill_switch.py::test_cancel_all_orders -x` | Wave 0 |
| SAFE-06 | Kill switch with --liquidate closes positions | unit | `pytest tests/unit/test_kill_switch.py::test_liquidate -x` | Wave 0 |
| SAFE-06 | Kill triggers cooldown entry | unit | `pytest tests/unit/test_kill_switch.py::test_kill_triggers_cooldown -x` | Wave 0 |
| SAFE-07 | Order polling reaches terminal state | unit | `pytest tests/unit/test_order_polling.py -x` | Wave 0 |
| SAFE-07 | Order polling timeout raises error | unit | `pytest tests/unit/test_order_polling.py::test_timeout -x` | Wave 0 |
| SAFE-08 | Bracket leg verification passes when legs active | unit | `pytest tests/unit/test_order_polling.py::test_bracket_legs_verified -x` | Wave 0 |
| SAFE-08 | Bracket leg verification warns when legs missing | unit | `pytest tests/unit/test_order_polling.py::test_bracket_legs_missing -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_safe_execution.py tests/unit/test_cooldown_persistence.py tests/unit/test_reconciliation.py tests/unit/test_kill_switch.py tests/unit/test_order_polling.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_safe_execution.py` -- covers SAFE-01, SAFE-02, SAFE-03
- [ ] `tests/unit/test_reconciliation.py` -- covers SAFE-04
- [ ] `tests/unit/test_cooldown_persistence.py` -- covers SAFE-05
- [ ] `tests/unit/test_kill_switch.py` -- covers SAFE-06
- [ ] `tests/unit/test_order_polling.py` -- covers SAFE-07, SAFE-08

## Sources

### Primary (HIGH confidence)
- alpaca-py 0.43.2 installed SDK -- introspected TradingClient methods, Order model fields, OrderStatus/OrderClass enums directly from installed package
- Existing codebase: `src/execution/infrastructure/alpaca_adapter.py` -- confirmed mock fallback bug (line 127)
- Existing codebase: `src/settings.py` -- confirmed current Settings structure
- Existing codebase: `src/bootstrap.py` -- confirmed adapter wiring pattern (lines 102-128)
- Existing codebase: `src/portfolio/domain/services.py` -- confirmed drawdown assessment logic
- Existing codebase: `src/execution/infrastructure/sqlite_trade_plan_repo.py` -- confirmed SQLite repository pattern

### Secondary (MEDIUM confidence)
- [Alpaca Orders API Docs](https://docs.alpaca.markets/docs/working-with-orders) -- bracket order lifecycle, child order behavior
- [Alpaca SDK Python Reference](https://alpaca.markets/sdks/python/api_reference/trading/orders.html) -- method signatures verified against installed SDK
- [Alpaca Forum: Bracket Order Example](https://forum.alpaca.markets/t/bracket-order-code-example-with-alpaca-py-library/12110) -- bracket order code pattern
- [Alpaca Blog: Cancel Orders & Liquidation](https://alpaca.markets/blog/position-liquidation-cancel-orders/) -- cancel_orders + close_all_positions
- [Alpaca Forum: Bracket Leg "held" Status](https://forum.alpaca.markets/t/half-of-bracket-order-held/2727) -- bracket leg status behavior

### Tertiary (LOW confidence)
- None -- all findings verified against installed SDK or official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and in use, no new dependencies
- Architecture: HIGH -- decorator adapter pattern follows existing IBrokerAdapter ABC, SQLite repos follow existing pattern
- Pitfalls: HIGH -- bracket leg behavior verified against SDK enums and forum reports; mock fallback bug confirmed in source code (line 127 of alpaca_adapter.py)

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable -- alpaca-py 0.43.x, established patterns)
