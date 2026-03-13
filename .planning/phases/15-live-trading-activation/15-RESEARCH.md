# Phase 15: Live Trading Activation - Research

**Researched:** 2026-03-13
**Domain:** Live order execution, circuit breaker, WebSocket streaming, capital allocation
**Confidence:** HIGH

## Summary

Phase 15 activates live trading through the existing Alpaca adapter infrastructure. The codebase already has strong foundations: `SafeExecutionAdapter` wraps broker calls with cooldown checks and order polling, `AlpacaExecutionAdapter` supports `paper=False`, `bootstrap.py` selects live credentials when `EXECUTION_MODE=live`, and `Settings` already defines `ALPACA_LIVE_KEY`/`ALPACA_LIVE_SECRET`. The remaining work is adding circuit breaker logic, background order monitoring, WebSocket fill streaming, and capital ratio enforcement.

The alpaca-py SDK (v0.43.2 installed) provides `TradingStream` with built-in WebSocket reconnection -- on `WebSocketException` it automatically reconnects and re-subscribes. The `TradeUpdate` model delivers event type, order object, filled price, quantity, and position quantity. This eliminates the need to hand-roll reconnection logic.

**Primary recommendation:** Extend `SafeExecutionAdapter` with circuit breaker state tracking and integrate `TradingStream` as a parallel fill receiver alongside the existing polling fallback. Add `LIVE_CAPITAL_RATIO` to Settings and enforce it in the execution path.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Circuit breaker trips after 3 consecutive order failures within a single pipeline execution
- Trip action: Slack alert + cancel all open orders (positions kept -- stop-loss protects)
- Reset: manual CLI reset + auto-reset on next pipeline run (daily cooldown effect)
- Failure count resets between pipeline executions
- Order monitor runs as background thread, active only during pipeline execution
- Stuck orders: 5-minute timeout then auto-cancel + Slack alert
- WebSocket (TradingStream) is primary fill channel; polling is fallback on disconnect
- WebSocket active only during pipeline execution (not a daemon)
- Fill events published as OrderFilledEvent via SyncEventBus
- LIVE_CAPITAL_RATIO env var (default 0.25), 4 stages: 25% -> 50% -> 75% -> 100%
- Capital ratio and approval budget are independent (dual safety)
- CLI command `trade config set-capital-ratio` with confirmation prompt

### Claude's Discretion
- Order monitor thread: threading.Thread vs concurrent.futures
- WebSocket reconnection interval and max retries
- Circuit breaker internal state: memory vs SQLite
- `trade config` CLI subcommand structure
- OrderFilledEvent domain event schema

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LIVE-01 | System connects to Alpaca live account when EXECUTION_MODE=live with valid live API credentials | Already implemented in bootstrap.py (lines 131-153): selects LIVE keys, creates AlpacaExecutionAdapter with paper=False. Needs LIVE_CAPITAL_RATIO enforcement. |
| LIVE-02 | SafeExecutionService wraps broker adapter with circuit breaker and budget enforcement pre-checks | SafeExecutionAdapter exists with cooldown check. Add circuit breaker counter + budget/capital-ratio pre-check in submit_order(). |
| LIVE-03 | AlpacaOrderMonitor runs as background task tracking all open orders until terminal state | New class. Use threading.Thread running poll loop (reuse existing _poll_order_status pattern). 5-min stuck timeout. |
| LIVE-04 | TradingStream WebSocket receives real-time fill events and publishes to event bus | alpaca-py TradingStream (v0.43.2) with subscribe_trade_updates(). Handler publishes OrderFilledEvent to SyncEventBus. |
| LIVE-05 | Initial live deployment uses max 25% capital allocation, increasing as reliability is demonstrated | LIVE_CAPITAL_RATIO in Settings (default 0.25). Applied in bootstrap when computing effective capital. CLI for adjustment. |
| LIVE-06 | Circuit breaker halts live trading after 3 consecutive order failures | In-memory counter in SafeExecutionAdapter, reset per pipeline run. On trip: notify + cancel orders via KillSwitchService. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| alpaca-py | 0.43.2 | Broker SDK (TradingClient + TradingStream) | Already installed, provides both REST and WebSocket |
| threading | stdlib | Background order monitor thread | Simpler than concurrent.futures for single long-running task |
| pydantic-settings | (existing) | LIVE_CAPITAL_RATIO setting | Already used for all Settings |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SyncEventBus | (existing) | OrderFilledEvent cross-context publish | Fill events from WebSocket/polling |
| KillSwitchService | (existing) | Cancel all orders on circuit breaker trip | Reuse existing cancel_orders logic |
| SlackNotifier/LogNotifier | (existing) | Circuit breaker and stuck order alerts | Reuse existing Notifier Protocol |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| threading.Thread | concurrent.futures.ThreadPoolExecutor | Overkill for single monitor thread; Thread is simpler |
| In-memory circuit breaker | SQLite-persisted | Memory sufficient since count resets per pipeline run |
| Custom WebSocket | alpaca-py TradingStream | TradingStream has built-in reconnect loop, no reason to hand-roll |

**Installation:**
```bash
# No new dependencies needed -- all libraries already installed
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  execution/
    domain/
      events.py              # Add OrderFilledEvent
      value_objects.py        # (no changes needed)
      repositories.py         # (no changes needed)
    infrastructure/
      safe_adapter.py         # Add circuit breaker logic
      order_monitor.py        # NEW: background thread order tracker
      trading_stream.py       # NEW: WebSocket fill receiver
      kill_switch.py          # (reuse, no changes)
      alpaca_adapter.py       # (no changes needed)
  settings.py                 # Add LIVE_CAPITAL_RATIO
  bootstrap.py                # Wire monitor, stream, capital ratio
  cli/
    trade_commands.py          # Add config subcommands, circuit-breaker reset
```

### Pattern 1: Circuit Breaker in SafeExecutionAdapter
**What:** Track consecutive failure count as instance state. Increment on order error/rejection, reset on success. Trip at threshold.
**When to use:** Every submit_order() call in LIVE mode.
**Example:**
```python
# In SafeExecutionAdapter
class SafeExecutionAdapter(IBrokerAdapter):
    def __init__(self, ..., max_failures: int = 3, notifier=None, kill_switch=None):
        self._consecutive_failures = 0
        self._circuit_tripped = False
        self._max_failures = max_failures
        self._notifier = notifier
        self._kill_switch = kill_switch

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        if self._circuit_tripped:
            raise CircuitBreakerTrippedError(self._consecutive_failures)

        # ... existing cooldown check ...
        result = self._inner.submit_order(spec)

        if result.status == "error":
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                self._trip_circuit_breaker()
        else:
            self._consecutive_failures = 0  # reset on success
        return result

    def _trip_circuit_breaker(self):
        self._circuit_tripped = True
        if self._kill_switch:
            self._kill_switch.execute(liquidate=False)  # cancel orders only
        if self._notifier:
            self._notifier.notify(f"Circuit breaker tripped after {self._consecutive_failures} failures")

    def reset_circuit_breaker(self):
        self._consecutive_failures = 0
        self._circuit_tripped = False
```

### Pattern 2: Background Order Monitor Thread
**What:** Thread that polls open order statuses until all reach terminal state or timeout.
**When to use:** Started after order submissions in pipeline execute stage.
**Example:**
```python
class AlpacaOrderMonitor:
    STUCK_TIMEOUT = 300  # 5 minutes

    def __init__(self, client, notifier=None, bus=None, poll_interval=5.0):
        self._client = client
        self._notifier = notifier
        self._bus = bus
        self._poll_interval = poll_interval
        self._tracked_orders: dict[str, float] = {}  # order_id -> first_seen_time
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def track(self, order_id: str):
        self._tracked_orders[order_id] = time.monotonic()

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 30.0):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _monitor_loop(self):
        while not self._stop_event.is_set() and self._tracked_orders:
            for order_id in list(self._tracked_orders):
                status = self._poll_status(order_id)
                if status in TERMINAL_STATUSES:
                    del self._tracked_orders[order_id]
                elif time.monotonic() - self._tracked_orders[order_id] > self.STUCK_TIMEOUT:
                    self._cancel_stuck(order_id)
                    del self._tracked_orders[order_id]
            self._stop_event.wait(self._poll_interval)
```

### Pattern 3: WebSocket TradingStream Integration
**What:** Wrap alpaca-py TradingStream to publish fill events to SyncEventBus.
**When to use:** During pipeline execution alongside order monitor (dual channel).
**Example:**
```python
class TradingStreamAdapter:
    def __init__(self, api_key, secret_key, paper, bus: SyncEventBus):
        from alpaca.trading.stream import TradingStream
        self._stream = TradingStream(api_key, secret_key, paper=paper)
        self._bus = bus
        self._thread: threading.Thread | None = None

    def start(self):
        self._stream.subscribe_trade_updates(self._on_trade_update)
        self._thread = threading.Thread(target=self._stream.run, daemon=True)
        self._thread.start()

    async def _on_trade_update(self, data):
        if data.event in ("fill", "partial_fill"):
            event = OrderFilledEvent(
                order_id=str(data.order.id),
                symbol=data.order.symbol,
                quantity=int(data.qty or 0),
                filled_price=float(data.price or 0),
            )
            self._bus.publish(event)

    def stop(self):
        self._stream.stop()
        if self._thread:
            self._thread.join(timeout=10)
```

### Anti-Patterns to Avoid
- **Global circuit breaker state across pipeline runs:** Per CONTEXT.md, failure count resets each pipeline execution. Do NOT persist to SQLite.
- **Blocking WebSocket in main thread:** TradingStream.run() blocks the event loop. Must run in a daemon thread.
- **Applying capital ratio after position sizing:** Capital ratio must be applied BEFORE position sizing to correctly limit order sizes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket reconnection | Custom reconnect loop | TradingStream built-in | alpaca-py _run_forever catches WebSocketException and auto-reconnects |
| Order cancellation | Custom cancel loop | KillSwitchService.execute() | Already handles cancel_orders + error handling |
| Slack notifications | Custom HTTP client | Existing Notifier (SlackNotifier/LogNotifier) | Already wired in bootstrap |
| Settings management | Custom config loader | pydantic-settings Settings | All existing config uses this pattern |

**Key insight:** alpaca-py's TradingStream has a `_run_forever` loop that catches `WebSocketException`, closes the socket, sets `_running = False`, and reconnects on next iteration. No custom reconnection needed. The only gap is there's no backoff between reconnects (just 0.01s sleep), which is acceptable for the pipeline-duration-only usage.

## Common Pitfalls

### Pitfall 1: TradingStream handler must be async
**What goes wrong:** Passing a sync function to `subscribe_trade_updates` fails silently or crashes.
**Why it happens:** `_ensure_coroutine(handler)` validates the handler is a coroutine function.
**How to avoid:** Define handler as `async def _on_trade_update(self, data: TradeUpdate):`
**Warning signs:** `TypeError: 'coroutine' object is not callable` or similar

### Pitfall 2: SyncEventBus called from async context
**What goes wrong:** `SyncEventBus.publish()` is synchronous but WebSocket handler is async. Thread safety concern.
**Why it happens:** TradingStream runs in its own thread with its own event loop.
**How to avoid:** Since SyncEventBus uses simple list iteration with no locks, publishing from the WebSocket thread is safe for append-only subscriber lists. The handlers themselves run in the WebSocket thread. If handlers need to interact with SQLite (same-thread constraint), use `threading.Event` or a queue to signal the main thread.
**Warning signs:** SQLite "database is locked" errors from WebSocket thread

### Pitfall 3: Capital ratio not applied consistently
**What goes wrong:** Orders use full capital despite LIVE_CAPITAL_RATIO being set.
**Why it happens:** Ratio applied at wrong level (e.g., only in CLI display, not in position sizing).
**How to avoid:** Apply ratio in bootstrap.py when computing `capital` value: `capital = settings.US_CAPITAL * settings.LIVE_CAPITAL_RATIO`. This flows through to all position sizing since `capital` is passed to trade_plan_handler via ctx dict.
**Warning signs:** Orders larger than expected ratio would allow

### Pitfall 4: WebSocket and polling monitor conflict
**What goes wrong:** Both WebSocket and polling detect the same fill, causing duplicate OrderFilledEvent.
**Why it happens:** Both channels track the same orders.
**How to avoid:** Order monitor tracks order IDs in a set. WebSocket handler removes filled orders from the monitor's tracked set. Monitor only publishes events for orders it detects as filled (not already removed by WebSocket).
**Warning signs:** Duplicate events in event bus, double-counted budget spend

### Pitfall 5: Circuit breaker not wired to existing pipeline execute
**What goes wrong:** Circuit breaker exists in SafeExecutionAdapter but _run_execute catches exceptions and continues.
**Why it happens:** Current _run_execute has try/except per trade that logs and increments failed count.
**How to avoid:** Let CircuitBreakerTrippedError propagate from submit_order through _run_execute. The SafeExecutionAdapter is the enforcement point -- _run_execute should catch the error, log it, and break out of the trade loop.
**Warning signs:** Pipeline continues submitting orders after circuit breaker trips

## Code Examples

### OrderFilledEvent Domain Event
```python
# src/execution/domain/events.py
@dataclass(frozen=True)
class OrderFilledEvent(DomainEvent):
    """Order fill confirmation from WebSocket or polling."""
    order_id: str = ""
    symbol: str = ""
    quantity: int = 0
    filled_price: float = 0.0
    position_qty: float = 0.0  # post-fill position size
```

### CircuitBreakerTrippedError
```python
# src/execution/infrastructure/safe_adapter.py
class CircuitBreakerTrippedError(Exception):
    """Raised when circuit breaker is tripped."""
    def __init__(self, failure_count: int) -> None:
        self.failure_count = failure_count
        super().__init__(f"Circuit breaker tripped after {failure_count} consecutive failures")
```

### Settings Addition
```python
# src/settings.py -- add to Settings class
LIVE_CAPITAL_RATIO: float = 0.25  # 25% default, range 0.0-1.0
```

### Bootstrap Capital Ratio Application
```python
# In bootstrap(), after determining capital:
if execution_mode == ExecutionMode.LIVE:
    effective_capital = capital * settings.LIVE_CAPITAL_RATIO
    capital = effective_capital
```

### TradeUpdate Event Fields (alpaca-py v0.43.2)
```python
# alpaca.trading.models.TradeUpdate fields:
#   event: TradeEvent (fill, partial_fill, new, canceled, rejected, etc.)
#   execution_id: Optional[UUID]
#   order: Order (full order object with id, symbol, status, etc.)
#   timestamp: datetime
#   position_qty: Optional[float]
#   price: Optional[float] (fill price)
#   qty: Optional[float] (fill quantity)

# TradeEvent enum values:
# ACCEPTED, CANCELED, EXPIRED, FILL, PARTIAL_FILL, PENDING_CANCEL,
# PENDING_NEW, PENDING_REPLACE, REJECTED, REPLACED, RESTATED, NEW
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| alpaca-trade-api (v1) | alpaca-py (v0.43.2) | 2023 | New SDK, TradingStream replaces StreamConn |
| Manual WebSocket | TradingStream class | alpaca-py launch | Built-in auth, dispatch, reconnect |

**Already implemented (no changes needed):**
- EXECUTION_MODE paper/live enum (SAFE-01)
- Separate PAPER/LIVE key pairs (SAFE-03)
- Bootstrap live credential validation (raises ValueError if missing)
- SafeExecutionAdapter cooldown enforcement

## Open Questions

1. **TradingStream thread safety with SyncEventBus**
   - What we know: SyncEventBus is not thread-safe (no locks), but append-only subscriber lists are safe for concurrent reads
   - What's unclear: Whether downstream handlers (budget recording, portfolio updates) are safe to call from WebSocket thread
   - Recommendation: Keep WebSocket handler lightweight (just publish event). If handlers do SQLite writes, verify they use separate connections. The existing per-repository SQLite connection pattern should handle this.

2. **Order monitor thread cleanup on pipeline crash**
   - What we know: Monitor thread is daemon=True, so it dies with the process
   - What's unclear: Whether in-flight orders need cleanup if pipeline crashes mid-execution
   - Recommendation: Daemon thread is sufficient. Stuck orders will be caught by next pipeline run's reconciliation (Phase 12 SAFE-04).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml |
| Quick run command | `python3 -m pytest tests/unit/ -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LIVE-01 | Bootstrap selects live keys + paper=False when EXECUTION_MODE=live | unit | `python3 -m pytest tests/unit/test_live_activation.py::test_live_mode_bootstrap -x` | Wave 0 |
| LIVE-02 | SafeExecutionAdapter enforces circuit breaker + capital ratio pre-check | unit | `python3 -m pytest tests/unit/test_circuit_breaker.py -x` | Wave 0 |
| LIVE-03 | OrderMonitor tracks orders, detects stuck, auto-cancels after timeout | unit | `python3 -m pytest tests/unit/test_order_monitor.py -x` | Wave 0 |
| LIVE-04 | TradingStreamAdapter publishes OrderFilledEvent on fill | unit | `python3 -m pytest tests/unit/test_trading_stream.py -x` | Wave 0 |
| LIVE-05 | Capital = US_CAPITAL * LIVE_CAPITAL_RATIO, CLI set-capital-ratio works | unit | `python3 -m pytest tests/unit/test_capital_ratio.py -x` | Wave 0 |
| LIVE-06 | 3 consecutive failures trips breaker, cancels orders, sends alert | unit | `python3 -m pytest tests/unit/test_circuit_breaker.py::test_trip_after_3_failures -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/unit/ -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_circuit_breaker.py` -- covers LIVE-02, LIVE-06
- [ ] `tests/unit/test_order_monitor.py` -- covers LIVE-03
- [ ] `tests/unit/test_trading_stream.py` -- covers LIVE-04
- [ ] `tests/unit/test_capital_ratio.py` -- covers LIVE-05
- [ ] `tests/unit/test_live_activation.py` -- covers LIVE-01

## Sources

### Primary (HIGH confidence)
- alpaca-py source code (v0.43.2 installed) -- TradingStream, TradeUpdate, TradeEvent inspected directly
- Project codebase -- SafeExecutionAdapter, AlpacaExecutionAdapter, bootstrap.py, Settings, KillSwitchService, SyncEventBus
- Phase 15 CONTEXT.md -- locked decisions and discretion areas

### Secondary (MEDIUM confidence)
- [Alpaca TradingStream API reference](https://alpaca.markets/sdks/python/api_reference/trading/stream.html)
- [Alpaca WebSocket Streaming docs](https://docs.alpaca.markets/docs/websocket-streaming)
- [Alpaca trade_updates event documentation](https://forum.alpaca.markets/t/documentation-for-the-tradeupdate-web-socket-event/6696)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed and in use
- Architecture: HIGH - extends existing patterns (SafeExecutionAdapter decorator, SyncEventBus events, threading for background tasks)
- Pitfalls: HIGH - verified through source code inspection (TradingStream handler must be async, thread safety of SyncEventBus, capital ratio application point)

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable -- alpaca-py rarely has breaking changes)
