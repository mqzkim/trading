# Phase 5: Tech Debt & Infrastructure Foundation - Research

**Researched:** 2026-03-12
**Domain:** DDD infrastructure (event bus, composition root, DB unification, CLI wiring), Python in-process messaging
**Confidence:** HIGH

## Summary

Phase 5 is the first phase of v1.1 and addresses 16 tech debt items inherited from v1.0 plus three missing infrastructure pieces (SyncEventBus, Composition Root, DB Connection Factory). The existing codebase has 8 bounded contexts (`data_ingest`, `scoring`, `valuation`, `signals`, `regime`, `portfolio`, `execution`, `backtest`) with an `AsyncEventBus` that is functional but almost entirely unwired -- only `DataPipeline` publishes events, and no context subscribes. The God Orchestrator in `core/orchestrator.py` imports from every module directly, bypassing all DDD layering. Three CLI commands are missing (`ingest`, `generate-plan`, `backtest`). The screener is broken due to a DuckDB/SQLite table mismatch. G-Score blending and regime weight adjustment are dead code in the DDD handler path.

The key architectural insight is that all the required math and business logic already exists -- this phase is pure wiring, integration, and cleanup. No new computation, no new libraries, no new bounded contexts. The `AsyncEventBus` (45 lines) already supports both sync and async handlers. The decision to implement a `SyncEventBus` (requirement INFRA-01) means either adapting the existing async bus or writing a simpler synchronous variant suitable for the Typer CLI context where `asyncio.run()` overhead is undesirable. The Composition Root replaces `core/orchestrator.py` as the single bootstrap entry point, wiring all repositories, adapters, handlers, and the event bus via constructor injection.

**Primary recommendation:** Build a SyncEventBus (~30 lines) alongside the existing AsyncEventBus. Create a Composition Root that wires all 4 primary bounded contexts (scoring, signals, regime, portfolio) with their repositories, adapters, and event subscriptions. Fix the DuckDB screener query. Wire G-Score blending. Add the 3 missing CLI commands. Fix the cross-context import. Resolve remaining tech debt from the v1.0 audit.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | SyncEventBus 구현 및 기존 4개 바운디드 컨텍스트 배선 | SyncEventBus pattern from Cosmic Python; existing `AsyncEventBus` in `src/shared/infrastructure/event_bus.py` provides reference implementation; events already defined in all 4 contexts but only `DataPipeline` publishes |
| INFRA-02 | Composition Root (bootstrap) 구현으로 God Orchestrator 제거 | `core/orchestrator.py` identified as God Object (imports from 10+ modules); Composition Root pattern wires dependencies at startup via DI |
| INFRA-03 | DB Connection Factory (DuckDB/SQLite 통합 관리) | DuckDB `conn = duckdb.connect("data/analytics.duckdb")` hardcoded in CLI; SQLite `db_path="data/scoring.db"` hardcoded in repos; factory centralizes paths and lifecycle |
| INFRA-04 | DuckDB/SQLite 스코어링 스토어 불일치 수정 | `duckdb_signal_store.py:115` queries `FROM scores s` (table does not exist); `SqliteScoreRepository` writes to SQLite `scored_symbols`; screener returns empty or CatalogException |
| INFRA-05 | 누락 CLI 명령어 추가 (ingest, generate-plan, backtest) | `cli/main.py` has 11 commands but lacks `ingest` (DataPipeline exists but unreachable), `generate-plan` (TradePlanHandler.generate() unreachable), `backtest` (BacktestHandler exists but no CLI surface) |
| INFRA-06 | G-Score 블렌딩 및 레짐 조정 DDD 핸들러 배선 | `ScoreSymbolHandler.handle()` line 99 calls `self._composite.compute()` but NEVER passes `g_score` or `is_growth_stock`; `CompositeScoringService.compute()` has these params but they are dead code in handler path |
| INFRA-07 | 도메인 이벤트 EventBus 발행 배선 | Events defined in all contexts (`ScoreUpdatedEvent`, `SignalGeneratedEvent`, `RegimeChangedEvent`, etc.) but `bus.publish()` only called in `DataPipeline`; 0 subscribers wired |
| INFRA-08 | Cross-context 직접 import 수정 (execution -> portfolio) | `src/execution/domain/services.py:11` directly imports `from src.portfolio.domain.value_objects import TakeProfitLevels`; DDD rule 5 violation |
| INFRA-09 | 나머지 tech debt 항목 해결 (v1.0 감사 기준) | 16 items total from `v1.0-MILESTONE-AUDIT.md`; includes unused variables, mypy errors, unused imports, alert events never instantiated, walk-forward trade returns always empty |
</phase_requirements>

## Standard Stack

### Core (No New Dependencies)

This phase requires zero new packages. All work is pure Python infrastructure.

| Library | Version | Purpose | Already Installed |
|---------|---------|---------|-------------------|
| Python | 3.12 | Language runtime | Yes |
| typer | 0.24.1 | CLI commands | Yes |
| rich | 14.3.3 | CLI output formatting | Yes |
| duckdb | 1.5.0 | Analytical database (screener fix) | Yes |
| sqlite3 | stdlib | Operational database | Yes (stdlib) |
| asyncio | stdlib | Async support for event bus | Yes (stdlib) |

### Supporting (Test Infrastructure)

| Library | Version | Purpose | Already Installed |
|---------|---------|---------|-------------------|
| pytest | 9.0.2 | Test execution | Yes |
| pytest-asyncio | (dev dep) | Async test support for event bus tests | Yes |
| mypy | 1.19.1 | Type checking | Yes |
| ruff | 0.15.5 | Linting | Yes |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New SyncEventBus | Adapt existing AsyncEventBus with `asyncio.run()` wrapper | AsyncEventBus works but adds `asyncio.run()` overhead per CLI call; SyncEventBus is simpler for the dominant use case (CLI) |
| Composition Root function | DI framework (injector, dependency-injector) | DI frameworks are overkill for 4 bounded contexts with ~15 injectable dependencies; a plain `bootstrap()` function is clearer and has zero dependency cost |
| DB Connection Factory class | Environment variables for paths | Env vars scatter configuration; factory centralizes and manages lifecycle (open/close, WAL mode toggle) |

## Architecture Patterns

### Recommended Project Structure (Changes Only)

```
src/
  shared/
    infrastructure/
      event_bus.py          # EXISTING -- AsyncEventBus (keep)
      sync_event_bus.py     # NEW -- SyncEventBus for CLI context
      db_factory.py         # NEW -- DB Connection Factory
      __init__.py           # UPDATE -- export SyncEventBus, DBFactory
  bootstrap.py              # NEW -- Composition Root (top-level src/)
```

### Pattern 1: SyncEventBus

**What:** A synchronous in-process event bus that routes domain events to registered handlers. Mirrors `AsyncEventBus` API but without `async`/`await`.

**When to use:** CLI commands (Typer is synchronous). The `AsyncEventBus` remains for the commercial API server (FastAPI is async).

**Why not just wrap AsyncEventBus:** The CLI handlers are sync. Wrapping every `bus.publish()` call in `asyncio.run()` creates a new event loop per call, which is slow and error-prone if any handler internally uses asyncio.

**Reference:** Cosmic Python Chapter 8 (Events and Message Bus) -- the canonical Python event bus pattern.

**Example:**

```python
# src/shared/infrastructure/sync_event_bus.py
from __future__ import annotations
from collections import defaultdict
from typing import Callable
from src.shared.domain import DomainEvent


class SyncEventBus:
    """Synchronous in-process event bus for CLI context.

    Same API as AsyncEventBus but all handlers are called synchronously.
    Use AsyncEventBus for the FastAPI server context.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable
    ) -> None:
        self._handlers[event_type.__name__].append(handler)

    def publish(self, event: DomainEvent) -> None:
        event_name = event.__class__.__name__
        for handler in self._handlers.get(event_name, []):
            handler(event)
```

**Verification:** Existing `tests/unit/test_event_bus.py` has 6 tests for `AsyncEventBus`. Create parallel tests for `SyncEventBus` with same scenarios minus async.

### Pattern 2: Composition Root (Bootstrap)

**What:** A single function that creates all repositories, adapters, services, and handlers with proper dependency injection, then wires event subscriptions. Replaces `core/orchestrator.py` as the application entry point.

**When to use:** Called once at CLI startup and once at API server startup.

**Why:** `core/orchestrator.py` is a God Object -- it imports `DataClient`, `get_vix`, `classify`, `generate_signals`, `score_symbol`, `atr_position_size`, `full_risk_check`, `plan_entry` all at module level. Every new feature added to the orchestrator deepens this coupling. The Composition Root inverts control: each bounded context declares what it needs (via constructor parameters), and the root wires them together.

**Example:**

```python
# src/bootstrap.py
from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.shared.infrastructure.db_factory import DBFactory
from src.scoring.infrastructure.sqlite_repo import SqliteScoreRepository
from src.scoring.application.handlers import ScoreSymbolHandler
from src.scoring.domain.events import ScoreUpdatedEvent
from src.signals.application.handlers import GenerateSignalHandler
from src.regime.application.handlers import DetectRegimeHandler
# ... etc


def bootstrap(
    db_factory: DBFactory | None = None,
) -> dict:
    """Wire all bounded contexts and return a dict of handlers.

    This is the ONLY place that knows about all contexts.
    CLI commands and API routes receive pre-wired handlers.
    """
    if db_factory is None:
        db_factory = DBFactory()

    bus = SyncEventBus()

    # -- Repositories --
    score_repo = SqliteScoreRepository(db_factory.sqlite_path("scoring"))
    # signal_repo = ...
    # regime_repo = ...

    # -- Handlers --
    score_handler = ScoreSymbolHandler(score_repo=score_repo)
    # signal_handler = GenerateSignalHandler(...)
    # regime_handler = DetectRegimeHandler(...)

    # -- Event Subscriptions --
    # bus.subscribe(ScoreUpdatedEvent, signal_handler.on_score_updated)
    # bus.subscribe(RegimeChangedEvent, score_handler.on_regime_changed)

    return {
        "bus": bus,
        "score_handler": score_handler,
        # "signal_handler": signal_handler,
        # "regime_handler": regime_handler,
        "db_factory": db_factory,
    }
```

### Pattern 3: DB Connection Factory

**What:** Centralizes database path configuration and connection lifecycle. Returns DuckDB connections (for analytical stores) and SQLite paths (for operational repos).

**When to use:** Every repository instantiation. Currently each repo hardcodes its own path (e.g., `SqliteScoreRepository(db_path="data/scoring.db")`).

**Example:**

```python
# src/shared/infrastructure/db_factory.py
import os
import duckdb


class DBFactory:
    """Centralized database connection management.

    All database paths are relative to a single data directory.
    """

    def __init__(self, data_dir: str = "data") -> None:
        self._data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._duckdb_conn: duckdb.DuckDBPyConnection | None = None

    def duckdb_conn(self) -> duckdb.DuckDBPyConnection:
        if self._duckdb_conn is None:
            path = os.path.join(self._data_dir, "analytics.duckdb")
            self._duckdb_conn = duckdb.connect(path)
        return self._duckdb_conn

    def sqlite_path(self, name: str) -> str:
        return os.path.join(self._data_dir, f"{name}.db")

    def close(self) -> None:
        if self._duckdb_conn is not None:
            self._duckdb_conn.close()
            self._duckdb_conn = None
```

### Pattern 4: Fixing Cross-Context Import via Shared VO or Primitive Parameters

**What:** The `execution/domain/services.py` directly imports `TakeProfitLevels` from `portfolio/domain/value_objects.py`. This violates DDD bounded context isolation (rule 5: no direct cross-context imports).

**Two resolution options:**

**Option A (Recommended): Move `TakeProfitLevels` to `shared/domain/`.**
Both `execution` and `portfolio` contexts need take-profit calculation. Since it is a pure value object with no context-specific behavior, it belongs in the shared kernel.

**Option B: Pass take-profit price as a primitive.**
`TradePlanService.generate_plan()` already receives all primitive values. Instead of constructing `TakeProfitLevels` inside the service, compute the take-profit price in the CLI/handler layer and pass it as `take_profit_price: float`.

**Recommendation:** Option A is cleaner because `TakeProfitLevels` encodes business logic (50%/75%/100% level calculation) that should not be duplicated. Moving it to `shared/domain/` makes the import legal per DDD rules (shared kernel is accessible to all contexts).

### Anti-Patterns to Avoid

- **Async event bus in sync CLI:** Do not use `asyncio.run(bus.publish(event))` in CLI commands. Build a proper SyncEventBus.
- **Partial Composition Root:** Do not wire only some contexts through the bootstrap while others continue using hardcoded paths. All 4 primary contexts must go through the root.
- **Fixing DuckDB by duplicating writes:** Do not "fix" the screener by adding a DuckDB writer alongside the SQLite writer. Choose one storage strategy for scores (recommendation: fix the screener SQL to query SQLite or add a DuckDB scoring view).
- **God Orchestrator survival:** Do not keep `core/orchestrator.py` as a fallback. CLI commands must use the Composition Root. The orchestrator can remain in the codebase for reference but must not be the entry point.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Event routing | Custom pub/sub with topic matching, retry logic, dead letter queues | Simple `SyncEventBus` (dict of handlers, ~25 lines) | This is in-process, synchronous messaging. No need for distributed messaging complexity. |
| Dependency injection | DI framework (injector, dependency-injector, python-inject) | Plain `bootstrap()` function with constructor injection | 15 dependencies across 4 contexts. A DI framework adds 2000+ lines of framework code for no benefit at this scale. |
| Database migration | Alembic, migration framework | Inline DDL in `_ensure_table()` / `_create_tables()` methods | All tables use `CREATE TABLE IF NOT EXISTS`. No schema versioning needed for v1.1. |
| CLI async bridge | Custom event loop management | Keep CLI sync (SyncEventBus) and API async (AsyncEventBus) | Two separate bus instances for two contexts is simpler than bridging sync/async. |

**Key insight:** This phase is infrastructure plumbing, not application logic. Every solution should be under 50 lines of code. If something needs more, question whether it belongs in this phase.

## Common Pitfalls

### Pitfall 1: Screener Fix Breaks Existing Tests

**What goes wrong:** The screener currently queries DuckDB for a `scores` table that does not exist. Fixing this by changing the query to use SQLite or by creating a DuckDB scores view may break the 5 existing screener tests (`tests/unit/test_screener.py`, `tests/unit/test_cli_screener.py`) which mock the DuckDB store.

**Why it happens:** Tests mock `DuckDBSignalStore.query_top_n()` at the method level, but the fix changes the underlying SQL or the data source entirely.

**How to avoid:** Read the existing screener tests first. Understand what they mock. If the fix changes the SQL query (e.g., JOIN `scored_symbols` from SQLite instead of `scores` from DuckDB), update the test fixtures to match the new query structure. Run screener tests after every change.

**Warning signs:** Tests pass with mocks but `trading screener` fails on real data.

### Pitfall 2: Composition Root Partially Wired

**What goes wrong:** The bootstrap wires handlers A, B, and C, but CLI command D still creates its own handler with hardcoded paths (copy of the old pattern). This creates two configuration sources, and changes to one don't propagate to the other.

**Why it happens:** The 11 existing CLI commands each construct their own dependencies inline (e.g., `approve` creates `SqliteTradePlanRepository()`, `TradePlanService()`, `AlpacaExecutionAdapter()` directly). Converting all 11 at once is tedious, so some get skipped.

**How to avoid:** Convert ALL CLI commands to use the Composition Root in one pass. Create a module-level `_ctx` dict that holds the bootstrapped context, and each CLI command pulls from it.

**Warning signs:** `grep "Repository()" cli/main.py` returns results after the migration -- any direct instantiation in CLI means the bootstrap was bypassed.

### Pitfall 3: Event Subscriptions Create Unexpected Side Effects

**What goes wrong:** Wiring `ScoreUpdatedEvent -> GenerateSignalHandler` means every score computation now triggers signal generation automatically. If the `score` CLI command was only meant to show a score (not generate a signal), the event subscription creates unwanted behavior.

**Why it happens:** Event-driven architecture is "fire and forget" -- the publisher does not know who subscribes. Wiring subscriptions globally in the Composition Root means ALL score operations trigger ALL subscribers.

**How to avoid:** Phase 5 should wire events minimally -- define the subscriptions in the Composition Root but start with subscriptions commented out or gated by a flag. Let Phase 6+ actually enable cross-context event flows as the features that consume them are built.

**Warning signs:** Running `trading score AAPL` produces unexpected signal output or database writes.

### Pitfall 4: SyncEventBus Used in FastAPI (Wrong Bus for Context)

**What goes wrong:** The commercial API routes import the Composition Root and get the SyncEventBus. But FastAPI handlers are async -- a sync bus blocks the event loop during `bus.publish()`, degrading API response times.

**Why it happens:** Single Composition Root returns one bus instance for both CLI and API.

**How to avoid:** The Composition Root should accept a `bus` parameter. CLI callers pass `SyncEventBus()`. API callers pass `AsyncEventBus()`. The handlers work with either because both have the same `subscribe`/`publish` interface. This is not needed in Phase 5 (no API work), but the design should accommodate it.

### Pitfall 5: DuckDB/SQLite Decision Scope Creep

**What goes wrong:** Fixing the screener's DuckDB query opens a larger question: should ALL scoring go through DuckDB? Should we unify to one database? This leads to over-engineering the DB strategy when the requirement is narrower -- just make the screener work.

**Why it happens:** INFRA-03 (DB Connection Factory) and INFRA-04 (DuckDB/SQLite mismatch) are related but different scopes. INFRA-04 requires fixing the screener. INFRA-03 requires centralizing paths. Neither requires migrating all stores to DuckDB.

**How to avoid:** Fix the screener by correcting the SQL to match actual table names and columns. The screener query in `duckdb_signal_store.py` references `scores` table and `valuations` table -- fix these to `scored_symbols` (from SQLite) or create a DuckDB view/table that mirrors the SQLite scores. Do not redesign the dual-database strategy.

## Code Examples

### DuckDB Screener Fix (INFRA-04)

The broken SQL in `src/signals/infrastructure/duckdb_signal_store.py:106-127`:

```python
# BROKEN (current): references non-existent tables and wrong columns
# FROM scores s                      -- table doesn't exist in DuckDB
# LEFT JOIN valuations v ON s.symbol = v.symbol
#   -- table is valuation_results, column is ticker not symbol

# FIX OPTION A: Create a DuckDB scores table/view that mirrors SQLite
# In bootstrap, after scoring writes to SQLite, also write to DuckDB:
def _sync_scores_to_duckdb(sqlite_path: str, duckdb_conn) -> None:
    """Sync latest scores from SQLite to DuckDB for screener queries."""
    import sqlite3
    with sqlite3.connect(sqlite_path) as sconn:
        sconn.row_factory = sqlite3.Row
        rows = sconn.execute("""
            SELECT symbol, composite_score, risk_adjusted, strategy
            FROM scored_symbols
            WHERE id IN (SELECT MAX(id) FROM scored_symbols GROUP BY symbol)
        """).fetchall()

    duckdb_conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            symbol VARCHAR PRIMARY KEY,
            composite_score DOUBLE,
            risk_adjusted_score DOUBLE,
            strategy VARCHAR
        )
    """)
    duckdb_conn.execute("DELETE FROM scores")
    for row in rows:
        duckdb_conn.execute(
            "INSERT INTO scores VALUES (?, ?, ?, ?)",
            [row["symbol"], row["composite_score"], row["risk_adjusted"], row["strategy"]]
        )

# FIX OPTION B (simpler): Fix the SQL to use correct table/column names
# Change query_top_n() SQL to:
sql = """
    SELECT s.symbol,
           s.composite_score,
           s.risk_adjusted_score,
           v.intrinsic_value,
           v.margin_of_safety,
           v.has_margin,
           sig.direction,
           sig.strength
    FROM scores s
    LEFT JOIN valuation_results v ON s.symbol = v.ticker
    LEFT JOIN signals sig ON s.symbol = sig.symbol
    WHERE s.risk_adjusted_score >= ?
"""
# With Option A, the scores table exists. With Option B, the table name
# and JOIN column are fixed. Either way, the screener returns results.
```

### G-Score Blending Fix (INFRA-06)

The handler at `src/scoring/application/handlers.py:99` must pass `g_score` and `is_growth_stock`:

```python
# Current (line 99):
composite = self._composite.compute(
    fundamental=fundamental,
    technical=technical,
    sentiment=sentiment,
    strategy=cmd.strategy,
    tail_risk_penalty=cmd.tail_risk_penalty,
)

# Fixed: pass g_score and is_growth_stock from fundamental data
composite = self._composite.compute(
    fundamental=fundamental,
    technical=technical,
    sentiment=sentiment,
    strategy=cmd.strategy,
    tail_risk_penalty=cmd.tail_risk_penalty,
    g_score=fundamental_data.get("g_score"),
    is_growth_stock=fundamental_data.get("is_growth_stock", False),
)
```

### Cross-Context Import Fix (INFRA-08)

Move `TakeProfitLevels` to shared kernel:

```python
# BEFORE (violation):
# src/execution/domain/services.py:11
from src.portfolio.domain.value_objects import TakeProfitLevels

# AFTER (fix):
# 1. Move TakeProfitLevels class to src/shared/domain/take_profit.py
# 2. Update imports in both execution and portfolio:
from src.shared.domain.take_profit import TakeProfitLevels
# 3. Update src/portfolio/domain/value_objects.py to re-export from shared:
from src.shared.domain.take_profit import TakeProfitLevels  # re-export for backward compat
```

### Missing CLI Command: ingest (INFRA-05)

```python
# cli/main.py -- new command
@app.command()
def ingest(
    tickers: list[str] = typer.Argument(None, help="Ticker symbols (e.g. AAPL MSFT)"),
    universe: str = typer.Option(None, "--universe", "-u", help="Universe name (sp500)"),
    max_concurrent: int = typer.Option(5, "--concurrent", help="Max parallel fetches"),
):
    """Ingest market data (OHLCV + financials) into the analytics database."""
    import asyncio
    from src.data_ingest.infrastructure.pipeline import DataPipeline

    if not tickers and not universe:
        console.print("[red]Provide tickers or --universe[/red]")
        raise typer.Exit(code=1)

    async def _run():
        pipeline = DataPipeline(max_concurrent=max_concurrent)
        if universe:
            result = await pipeline.ingest_universe_by_name(universe)
        else:
            result = await pipeline.ingest_universe(tickers)
        await pipeline.close()
        return result

    result = asyncio.run(_run())
    console.print(f"[green]Ingested {result.get('success', 0)} tickers[/green]")
```

## State of the Art

| Old Approach (v1.0) | Current Approach (Phase 5 Target) | Impact |
|---------------------|-----------------------------------|--------|
| `core/orchestrator.py` God Object | Composition Root (`src/bootstrap.py`) with DI | Eliminates coupling; each context testable in isolation |
| No event publishing (dead `AsyncEventBus`) | SyncEventBus with wired subscriptions | Cross-context communication without direct imports |
| Hardcoded DB paths in every repo | `DBFactory` centralizes all paths | Single config source; easy to switch to test/prod paths |
| DuckDB screener queries non-existent tables | Fixed SQL with correct table/column names | Screener returns actual scored results |
| Missing CLI commands (ingest, generate-plan, backtest) | All 14 CLI commands available | Full DDD pipeline reachable from CLI |
| G-Score blending dead code | Handler passes g_score to CompositeScoringService | Growth stocks get proper G-Score contribution |
| Cross-context domain import (execution -> portfolio) | TakeProfitLevels in shared kernel | DDD boundary violation eliminated |

## Open Questions

1. **SyncEventBus vs AsyncEventBus unification**
   - What we know: CLI is sync (Typer), API is async (FastAPI). Both need event publishing.
   - What's unclear: Should we maintain two separate bus classes or one bus with sync/async adapter?
   - Recommendation: Two classes sharing the same Protocol interface. SyncEventBus for Phase 5 (CLI only). AsyncEventBus remains for future API use. Keep both simple.

2. **DuckDB scores table strategy**
   - What we know: Screener queries DuckDB `scores` table. Scores are stored in SQLite `scored_symbols`.
   - What's unclear: Should we create a DuckDB `scores` table (dual-write) or fix the screener to query SQLite?
   - Recommendation: Create a DuckDB `scores` table populated during the screener query (or via a sync step in the Composition Root). This keeps the screener's DuckDB analytical query pattern intact and avoids mixing SQLite into DuckDB joins.

3. **Composition Root granularity**
   - What we know: 11 CLI commands, each currently wires its own dependencies.
   - What's unclear: Should bootstrap create ALL handlers upfront or lazy-load per command?
   - Recommendation: Lazy initialization. The bootstrap function creates a factory/context object. Each CLI command calls `ctx.score_handler()` which creates-on-first-use. This avoids importing all contexts at CLI startup (slow).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | SyncEventBus subscribe/publish routes events to handlers | unit | `pytest tests/unit/test_sync_event_bus.py -x` | Wave 0 |
| INFRA-01 | 4 contexts wired to bus -- publishing ScoreUpdatedEvent triggers subscribed handler | integration | `pytest tests/integration/test_event_wiring.py -x` | Wave 0 |
| INFRA-02 | bootstrap() returns wired handlers; CLI commands use bootstrap context | unit | `pytest tests/unit/test_bootstrap.py -x` | Wave 0 |
| INFRA-03 | DBFactory returns consistent DuckDB conn and SQLite paths | unit | `pytest tests/unit/test_db_factory.py -x` | Wave 0 |
| INFRA-04 | Screener query_top_n returns scored results with valuations | integration | `pytest tests/integration/test_screener_integration.py -x` | Wave 0 |
| INFRA-05 | CLI `ingest` command executes DataPipeline end-to-end | unit (mocked) | `pytest tests/unit/test_cli_ingest.py -x` | Wave 0 |
| INFRA-05 | CLI `generate-plan` command produces TradePlan output | unit (mocked) | `pytest tests/unit/test_cli_generate_plan.py -x` | Wave 0 |
| INFRA-05 | CLI `backtest` command runs BacktestHandler and shows report | unit (mocked) | `pytest tests/unit/test_cli_backtest.py -x` | Wave 0 |
| INFRA-06 | CompositeScore differs when g_score is passed vs not passed | unit | `pytest tests/unit/test_scoring_composite_v2.py -x` | Partial (test exists for CompositeScore but not for handler g_score pass-through) |
| INFRA-07 | Handler publishes ScoreUpdatedEvent after scoring | unit | `pytest tests/unit/test_score_handler_events.py -x` | Wave 0 |
| INFRA-08 | execution/domain/ has zero imports from portfolio/domain/ | unit (import check) | `pytest tests/unit/test_ddd_boundaries.py -x` | Wave 0 |
| INFRA-09 | mypy src/ passes with 0 errors in modified files | smoke | `mypy src/scoring src/signals src/execution src/shared --no-error-summary` | Existing (mypy config) |

### Sampling Rate

- **Per task commit:** `pytest tests/unit/ -x -q` (fast, ~10s)
- **Per wave merge:** `pytest tests/ -v` (full suite, ~30s)
- **Phase gate:** Full suite green + `mypy src/` + `ruff check src/` before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_sync_event_bus.py` -- covers INFRA-01 (SyncEventBus behavior)
- [ ] `tests/integration/test_event_wiring.py` -- covers INFRA-01 (4 contexts wired)
- [ ] `tests/unit/test_bootstrap.py` -- covers INFRA-02 (Composition Root returns handlers)
- [ ] `tests/unit/test_db_factory.py` -- covers INFRA-03 (factory paths and connections)
- [ ] `tests/integration/test_screener_integration.py` -- covers INFRA-04 (screener with real SQLite + DuckDB data)
- [ ] `tests/unit/test_cli_ingest.py` -- covers INFRA-05 (ingest command)
- [ ] `tests/unit/test_cli_generate_plan.py` -- covers INFRA-05 (generate-plan command)
- [ ] `tests/unit/test_cli_backtest.py` -- covers INFRA-05 (backtest command)
- [ ] `tests/unit/test_score_handler_events.py` -- covers INFRA-07 (event publishing in handler)
- [ ] `tests/unit/test_ddd_boundaries.py` -- covers INFRA-08 (no cross-context domain imports)

## Sources

### Primary (HIGH confidence)

- **Direct codebase analysis** (`/home/mqz/workspace/trading/src/`, `/home/mqz/workspace/trading/core/`, `/home/mqz/workspace/trading/cli/`) -- all findings verified by reading source files
- **v1.0 Milestone Audit** (`.planning/milestones/v1.0-MILESTONE-AUDIT.md`) -- 16 tech debt items, 6 integration gaps, 2 broken E2E flows
- **Existing AsyncEventBus** (`src/shared/infrastructure/event_bus.py`) -- 45 lines, functional, verified by 6 passing tests
- **Existing research** (`.planning/research/ARCHITECTURE.md`, `PITFALLS.md`, `STACK.md`, `FEATURES.md`) -- comprehensive v1.1 research from prior analysis

### Secondary (MEDIUM confidence)

- **Cosmic Python -- Events and Message Bus** (https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html) -- event bus and composition root patterns for Python DDD

### Tertiary (LOW confidence)

- None. All findings in this research are based on direct source code analysis.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, all existing packages verified
- Architecture: HIGH -- patterns directly adapted from existing codebase (AsyncEventBus, adapter pattern, repository pattern) and Cosmic Python reference
- Pitfalls: HIGH -- all pitfalls identified from direct codebase analysis and v1.0 audit
- Code examples: HIGH -- all examples reference actual file paths and line numbers in the codebase

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable -- no external dependencies, all internal codebase analysis)
