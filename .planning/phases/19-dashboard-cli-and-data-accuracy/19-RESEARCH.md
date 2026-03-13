# Phase 19: Dashboard CLI & Data Accuracy - Research

**Researched:** 2026-03-14
**Domain:** CLI serve command, dashboard data accuracy (drawdown, equity curve)
**Confidence:** HIGH

## Summary

Phase 19 closes three integration gaps (INT-01, INT-02, INT-03) identified in the v1.2 milestone audit. All three are well-scoped fixes to existing, working infrastructure rather than greenfield development.

**INT-01** (Medium): No `trade serve` CLI command. The `create_dashboard_app(ctx)` factory works correctly (verified by 34 TestClient tests), but users must manually run `uvicorn`. The fix is a new Typer command that calls `uvicorn.run()` programmatically with settings from `src/settings.py` (which already has `DASHBOARD_HOST` and `DASHBOARD_PORT`).

**INT-02** (Low): `RiskQueryHandler.handle()` hardcodes `drawdown_pct = 0.0` on line 461 of `queries.py`. The portfolio_repo is already in the bootstrap ctx dict and `SqlitePortfolioRepository.find_by_id("default")` returns the Portfolio aggregate with its `.drawdown` property. The `OverviewQueryHandler._get_drawdown_pct()` already demonstrates the correct pattern -- RiskQueryHandler simply needs to replicate it.

**INT-03** (Low): `OverviewQueryHandler._build_equity_curve()` always yields flat values because the trade_plans table has no exit_price column. The P&L data flow exists via `Position.close(exit_price)` and `PositionClosedEvent(pnl, pnl_pct)`, but trade_plans only stores entry-side data. The fix requires either: (a) adding an exit_price/realized_pnl column to trade_plans, or (b) computing P&L from stop_loss_price/take_profit_price as approximation. Option (a) is correct but requires schema migration; option (b) is pragmatic for v1 since executed trades have known stop/target levels.

**Primary recommendation:** Fix all three gaps in a single plan. Use `uvicorn.run()` for the serve command, query portfolio_repo for real drawdown in RiskQueryHandler, and approximate equity curve P&L from take_profit_price minus entry_price for executed trades.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Dashboard shows portfolio overview with holdings, per-position P&L, and allocation chart | INT-01 fix: `trade serve` command makes dashboard accessible without manual uvicorn |
| DASH-04 | Dashboard displays risk metrics (drawdown gauge, sector exposure, position limit utilization) | INT-02 fix: RiskQueryHandler queries portfolio_repo for real drawdown_pct instead of hardcoded 0.0 |
| DASH-08 | Dashboard displays equity curve chart with regime overlay | INT-03 fix: _build_equity_curve() computes actual P&L accumulation from trade history |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.24.1 | CLI framework | Already the project CLI framework; `@app.command()` pattern |
| uvicorn | 0.41.0 | ASGI server | Already a dependency; `uvicorn.run()` for programmatic launch |
| fastapi | 0.135.1 | Web framework | Already the dashboard framework; `create_dashboard_app()` exists |
| plotly | 6.x | Charts | Already used for gauge and equity curve charts |
| webbrowser | stdlib | Browser launch | Python stdlib; `webbrowser.open()` for auto-open |

### No New Dependencies Required
This phase modifies existing code only. No new packages needed.

## Architecture Patterns

### Recommended Project Structure (Changes Only)
```
cli/
  main.py                    # ADD: serve() command (lines ~590+)
src/
  dashboard/
    application/
      queries.py             # MODIFY: RiskQueryHandler.handle() and _build_equity_curve()
tests/
  unit/
    test_dashboard_web.py    # ADD: tests for drawdown and equity curve accuracy
    test_cli_serve.py        # ADD: test for serve command (or extend test_cli_commands.py)
```

### Pattern 1: CLI Serve Command (uvicorn.run)
**What:** Typer command that bootstraps context, creates dashboard app, and launches uvicorn programmatically.
**When to use:** When the CLI needs to start a long-running server process.
**Example:**
```python
# Source: uvicorn docs + existing cli/main.py patterns
@app.command()
def serve(
    host: str = typer.Option(None, "--host", help="Bind host"),
    port: int = typer.Option(None, "--port", help="Bind port"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser"),
):
    """Launch the dashboard web server."""
    import uvicorn
    import webbrowser
    from src.settings import settings
    from src.dashboard.presentation.app import create_dashboard_app

    _host = host or settings.DASHBOARD_HOST
    _port = port or settings.DASHBOARD_PORT

    ctx = _get_ctx()
    dashboard_app = create_dashboard_app(ctx)

    if not no_browser:
        # Open browser after short delay (uvicorn not yet started)
        import threading
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{_port}/dashboard/")).start()

    console.print(f"[bold green]Dashboard starting at http://localhost:{_port}/dashboard/[/bold green]")
    uvicorn.run(dashboard_app, host=_host, port=_port, log_level="info")
```

### Pattern 2: Portfolio Drawdown Query (RiskQueryHandler)
**What:** Query portfolio_repo for actual drawdown instead of hardcoded 0.0.
**When to use:** RiskQueryHandler.handle() initial page load.
**Example:**
```python
# Source: OverviewQueryHandler._get_drawdown_pct() pattern (already exists at line 315)
# Apply same pattern to RiskQueryHandler
def handle(self) -> dict:
    # ... existing code ...

    # Replace hardcoded drawdown with actual query
    drawdown_pct = 0.0
    drawdown_level = "normal"
    portfolio_handler = self._ctx.get("portfolio_handler")  # needs ctx injected
    if portfolio_handler is not None:
        try:
            repo = portfolio_handler._portfolio_repo
            portfolio = repo.find_by_id("default")
            if portfolio is not None:
                drawdown_pct = portfolio.drawdown * 100  # Convert 0-1 to percentage
                drawdown_level = portfolio.drawdown_level.value
        except Exception:
            pass
```

### Pattern 3: Equity Curve P&L Accumulation
**What:** Compute actual cumulative P&L from executed trades.
**When to use:** `_build_equity_curve()` in OverviewQueryHandler.
**Key insight:** The trade_plans table has `entry_price`, `stop_loss_price`, `take_profit_price` but no `exit_price`. For executed trades, the actual fill price is unknown from trade_plans alone.
**Pragmatic approach:** Use `take_profit_price - entry_price` * `quantity` as approximate realized P&L for EXECUTED trades (optimistic upper bound). Alternative: use position close events (PositionClosedEvent has pnl), but those are transient events not persisted.
**Better approach:** Add `exit_price` and `realized_pnl` columns to trade_plans table, populated when execution completes. This is the correct long-term fix but requires SQLite schema migration.

```python
# Pragmatic v1: approximate P&L from entry/target spread
def _build_equity_curve(self, trade_history: list[dict]) -> dict:
    if not trade_history:
        return {"dates": [], "values": []}

    trades = list(reversed(trade_history))  # chronological
    dates: list[str] = []
    values: list[float] = []
    cumulative = 0.0

    for trade in trades:
        date_str = str(trade.get("created_at", ""))[:10]
        entry = trade.get("entry_price", 0.0)
        target = trade.get("take_profit_price", 0.0)
        qty = trade.get("quantity", 0)
        direction = trade.get("direction", "BUY")

        if entry > 0 and target > 0 and qty > 0:
            if direction == "BUY":
                trade_pnl = (target - entry) * qty
            else:
                trade_pnl = (entry - target) * qty
            cumulative += trade_pnl

        dates.append(date_str)
        values.append(cumulative)

    return {"dates": dates, "values": values}
```

### Anti-Patterns to Avoid
- **Spawning uvicorn in subprocess:** Do not use `subprocess.Popen()` to launch uvicorn. Use `uvicorn.run()` directly -- it's in-process, handles signals correctly, and shares the bootstrap context.
- **Adding asyncio.run() in serve command:** `uvicorn.run()` manages its own event loop. Do not wrap it in `asyncio.run()`.
- **Opening browser before server starts:** The browser open must be delayed (threading.Timer) because `uvicorn.run()` blocks. Opening before the server is ready shows an error page.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ASGI server launch | Custom socket listener | `uvicorn.run(app, host, port)` | Signal handling, graceful shutdown, reload |
| Browser auto-open | Custom platform detection | `webbrowser.open(url)` | stdlib, cross-platform |
| Drawdown calculation | Custom drawdown math | `Portfolio.drawdown` property | Already tested, handles peak tracking |
| Gauge chart | Custom SVG/canvas | `build_drawdown_gauge()` in charts.py | Already exists, Plotly-based |

## Common Pitfalls

### Pitfall 1: uvicorn.run() Blocks the Thread
**What goes wrong:** `uvicorn.run()` is a blocking call. Any code after it (like `webbrowser.open()`) never executes.
**Why it happens:** uvicorn runs the event loop until shutdown signal.
**How to avoid:** Use `threading.Timer(delay, callback)` to schedule browser open before calling `uvicorn.run()`.
**Warning signs:** "Browser never opens" or "serve command never returns."

### Pitfall 2: Drawdown as Fraction vs Percentage
**What goes wrong:** `Portfolio.drawdown` returns 0.0-1.0 (fraction). Dashboard gauge expects 0-20 (percentage).
**Why it happens:** Different scales in domain vs presentation.
**How to avoid:** Multiply by 100 when converting domain drawdown to display percentage: `drawdown_pct = portfolio.drawdown * 100`.
**Warning signs:** Gauge shows 0.12 instead of 12.0%.

### Pitfall 3: RiskQueryHandler Constructor Signature
**What goes wrong:** Current `RiskQueryHandler.__init__` takes `(self, ctx: dict)` but only extracts `position_repo` and `regime_repo`. Adding portfolio_repo access requires either changing the constructor or accessing via ctx.
**Why it happens:** Original implementation deferred drawdown to SSE.
**How to avoid:** The `ctx` dict is already available (passed in constructor). Access `portfolio_handler` or `portfolio_repo` from ctx, consistent with `OverviewQueryHandler` pattern.
**Warning signs:** AttributeError on missing repo attribute.

### Pitfall 4: Empty Trade History Edge Case
**What goes wrong:** Equity curve with zero trades should show empty chart, not error.
**Why it happens:** Division by zero or empty list iteration.
**How to avoid:** Guard with `if not trade_history: return {"dates": [], "values": []}` (already exists).
**Warning signs:** 500 error on overview page for fresh installs.

### Pitfall 5: SQLite Schema Migration for exit_price
**What goes wrong:** Adding exit_price column to trade_plans requires ALTER TABLE, but existing rows have NULL.
**Why it happens:** SQLite ALTER TABLE ADD COLUMN with default value is non-destructive but requires careful handling.
**How to avoid:** Use `ALTER TABLE trade_plans ADD COLUMN exit_price REAL DEFAULT NULL` with IF NOT EXISTS pattern. Or use the pragmatic P&L approximation from entry/target spread to avoid schema changes entirely.
**Warning signs:** "table already has column" errors on second run.

### Pitfall 6: Context Sharing Between CLI and Dashboard
**What goes wrong:** The CLI `_get_ctx()` caches context per market. The dashboard app also needs context. If both create separate contexts, they use different DB connections.
**Why it happens:** Lazy context creation in multiple places.
**How to avoid:** Pass the CLI-cached context to `create_dashboard_app(ctx)` (already the design -- `serve` command should call `_get_ctx()` then pass to factory).
**Warning signs:** Dashboard shows stale data, CLI and dashboard disagree on state.

## Code Examples

### Existing Pattern: OverviewQueryHandler._get_drawdown_pct()
```python
# Source: src/dashboard/application/queries.py lines 315-328
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
```

### Existing Pattern: CLI Command with Options
```python
# Source: cli/main.py -- all commands follow this pattern
@app.command()
def regime(
    history: int = typer.Option(0, "--history", help="Show N days"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Detect the current market regime."""
    ctx = _get_ctx()
    # ... handler logic ...
```

### Existing Pattern: Settings for Dashboard Config
```python
# Source: src/settings.py lines 44-46
DASHBOARD_HOST: str = "0.0.0.0"
DASHBOARD_PORT: int = 8000
```

### Existing Pattern: Test with Mock Context
```python
# Source: tests/unit/test_dashboard_web.py lines 14-68
def _make_ctx(execution_mode=ExecutionMode.PAPER) -> dict:
    # ... mocks for all repos ...
    return {
        "bus": SyncEventBus(),
        "execution_mode": execution_mode,
        "position_repo": position_repo,
        # ... etc ...
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `uvicorn src.dashboard.presentation.app:app` | `uvicorn.run(app_instance)` programmatic | Stable since uvicorn 0.20+ | Shares bootstrap context, handles signals |
| Hardcoded drawdown 0.0 | Query SqlitePortfolioRepository | This phase | Real drawdown on initial page load |
| Flat equity curve (cumulative=0) | P&L accumulation from trades | This phase | Meaningful equity visualization |

## Open Questions

1. **Equity curve P&L precision**
   - What we know: trade_plans has entry_price and take_profit_price but no exit_price. The PositionClosedEvent carries real pnl but is transient.
   - What's unclear: Should we add exit_price column (correct but migration) or approximate from targets (pragmatic but optimistic)?
   - Recommendation: Use target-based approximation for now. Add exit_price tracking in a future phase when order monitoring fills the column on fill events. This avoids schema migration complexity in a gap-closure phase.

2. **Browser auto-open in WSL2**
   - What we know: `webbrowser.open()` works on WSL2 if a browser is configured. The system is running WSL2 on Windows 11.
   - What's unclear: Whether the default browser opener works reliably in all WSL2 configurations.
   - Recommendation: Provide `--no-browser` flag. Default to auto-open but fail gracefully (try/except around webbrowser.open).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ with pytest-asyncio |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/test_dashboard_web.py tests/unit/test_cli_dashboard.py -x -v` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 (INT-01) | `trade serve` launches uvicorn with dashboard | unit | `pytest tests/unit/test_cli_serve.py -x` | No -- Wave 0 |
| DASH-04 (INT-02) | Risk gauge shows real drawdown from SQLite | unit | `pytest tests/unit/test_dashboard_web.py::test_risk_drawdown_from_portfolio -x` | No -- Wave 0 |
| DASH-08 (INT-03) | Equity curve accumulates P&L from trade history | unit | `pytest tests/unit/test_dashboard_web.py::test_equity_curve_accumulates_pnl -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_dashboard_web.py tests/unit/test_cli_dashboard.py -x -v`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_cli_serve.py` -- covers DASH-01/INT-01 (serve command unit test with mock uvicorn)
- [ ] `tests/unit/test_dashboard_web.py::test_risk_drawdown_from_portfolio` -- covers DASH-04/INT-02
- [ ] `tests/unit/test_dashboard_web.py::test_equity_curve_accumulates_pnl` -- covers DASH-08/INT-03

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `src/dashboard/application/queries.py` (lines 315-328, 273-296, 460-487)
- Codebase inspection: `src/dashboard/presentation/app.py` (create_dashboard_app factory)
- Codebase inspection: `cli/main.py` (existing command patterns, _get_ctx caching)
- Codebase inspection: `src/settings.py` (DASHBOARD_HOST, DASHBOARD_PORT)
- Codebase inspection: `src/portfolio/domain/aggregates.py` (Portfolio.drawdown property)
- Codebase inspection: `src/execution/infrastructure/sqlite_trade_plan_repo.py` (table schema)
- Codebase inspection: `pyproject.toml` (project.scripts = "cli.main:app", dependencies)

### Secondary (MEDIUM confidence)
- [uvicorn.run() documentation](https://www.uvicorn.org/) -- programmatic server launch API
- [FastAPI deployment docs](https://fastapi.tiangolo.com/deployment/manually/) -- uvicorn integration patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and in use
- Architecture: HIGH -- all patterns already established in codebase (OverviewQueryHandler, CLI commands)
- Pitfalls: HIGH -- identified from direct code inspection, not hypothetical

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable -- no library upgrades needed)
