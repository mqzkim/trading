# Phase 29: Performance & Self-Improvement - Research

**Researched:** 2026-03-18
**Domain:** Trade P&L tracking, Brinson-Fachler attribution, signal IC validation, parameter self-improvement
**Confidence:** HIGH

## Summary

Phase 29 builds two new capabilities on top of the existing trading system: (1) a performance attribution engine that tracks closed trade P&L with decision context snapshots and decomposes returns via Brinson-Fachler 4-level attribution, and (2) a self-improvement system that proposes scoring weight adjustments after sufficient trade history (50+ trades) with walk-forward validation and human approval.

The codebase already has strong foundations: `Position.close()` returns P&L, `PositionOpenedEvent`/`PositionClosedEvent` exist in portfolio events, `core/backtest/metrics.py` provides Sharpe/max-drawdown/win-rate computations, `core/backtest/walk_forward.py` provides walk-forward validation, and `personal/self_improver/advisor.py` has improvement logic to migrate. DuckDB is already used for analytics (signals, scores, valuations) via `DBFactory.duckdb_conn()`. The dashboard performance page shell exists with KPI cards, Brinson-Fachler placeholder, and Strategy Scorecard section.

**Primary recommendation:** Create a new `src/performance/` DDD bounded context for trade history and attribution, extend `PositionOpenedEvent` with score snapshot, add DuckDB `trades` and `proposals` tables, wire a new `/api/v1/performance/` router in commercial API, and complete the dashboard Performance page with real data + Parameter Proposals section.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Trade history stored in **DuckDB** (analytics DB, `data/analytics.duckdb`)
- `trades` table fields: symbol, entry_date, exit_date, entry_price, exit_price, quantity, pnl, pnl_pct, strategy, sector, composite_score, technical_score, fundamental_score, sentiment_score, regime, weights_json, signal_direction
- Decision context snapshot via `PositionOpenedEvent` with `score_snapshot` field
- `signal_direction` field added to both `PositionOpenedEvent` and `trades` table
- Brinson-Fachler runs **on-demand** (computed when dashboard Performance page API is called)
- Returns empty/zero state with "No performance data yet" when < 50 trades
- New endpoint: `GET /v1/performance/attribution` in `commercial/api/`
- Dashboard BFF proxies via existing Next.js API route pattern
- Proposals displayed in Dashboard Performance page "Parameter Proposals" section
- Only proposes **scoring axis weight adjustments** (fundamental/technical/sentiment per regime)
- Does NOT propose risk parameter changes
- Walk-forward validation must complete before proposal generation
- 50+ closed trades threshold before self-improvement activates
- New `src/performance/` DDD bounded context
- `personal/self_improver/` refactored to DDD structure
- Skill level = IC-based signal quality (per-axis IC)

### Claude's Discretion
- Exact DuckDB schema migration approach (alembic vs raw SQL)
- Loading skeleton for Parameter Proposals section
- Approval history display depth and formatting

### Deferred Ideas (OUT OF SCOPE)
- CLI `trading attribution` command -- Dashboard-only for Phase 29
- Risk parameter adjustment proposals (ATR multiplier, Kelly fraction)
- FinBERT upgrade for sentiment (ML-01)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PERF-01 | Trade-level P&L tracking with entry/exit context | DuckDB `trades` table + PositionClosedEvent handler persists closed trade records |
| PERF-02 | Brinson-Fachler 4-level decomposition (portfolio/strategy/trade/skill) | On-demand computation from DuckDB trade history; skill level = per-axis IC |
| PERF-03 | Signal IC validation (>= 0.03 threshold) | IC = correlation(signal_direction, forward_return) per scoring axis |
| PERF-04 | Kelly efficiency monitoring (>= 70% threshold) | Kelly efficiency = actual_geometric_return / kelly_optimal_return |
| PERF-05 | Decision context snapshot captured at trade entry time | Extend PositionOpenedEvent with score_snapshot dataclass field |
| SELF-01 | Parameter adjustment proposals generated from performance analysis | Migrate advisor.py logic to DDD domain service, propose regime-specific weight changes |
| SELF-02 | Propose-then-approve workflow (no auto-modification) | PUT `/v1/performance/proposals/{id}/approve` and `/reject` endpoints |
| SELF-03 | Walk-forward validation before parameter changes applied | Reuse `core/backtest/walk_forward.py` to validate proposed weights before showing proposal |
| SELF-04 | Minimum 50 trades threshold before self-improvement activates | Guard in application handler: count trades in DuckDB, skip if < 50 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| duckdb | 1.5.0 | Trade history analytics DB | Already used for analytics; fast columnar queries on trade data |
| pandas | 2.3.3 | Return series computation, IC calculation | Already used in backtest metrics |
| numpy | 1.26.4 | Correlation, statistical computations | Already used in backtest |
| scipy.stats | (bundled) | Spearman rank correlation for IC | Standard for information coefficient computation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fastapi | >=0.104 | Performance attribution API router | New router in commercial/api/ |
| pydantic | >=2.0 | Request/response schemas for performance API | Schemas for attribution and proposals |

### Alternatives Considered
None -- all decisions locked. Stack fully determined by existing codebase choices.

**No new installations needed.** All required packages already in pyproject.toml.

## Architecture Patterns

### New Bounded Context: `src/performance/`
```
src/performance/
  domain/
    entities.py         # ClosedTrade entity
    value_objects.py    # PerformanceReport, AttributionResult, ProposalStatus
    events.py           # ProposalGeneratedEvent
    services.py         # BrinsonFachlerService, ICCalculationService, KellyEfficiencyService
    repositories.py     # ITradeHistoryRepository, IProposalRepository (ABC)
    __init__.py
  application/
    commands.py         # ApproveProposalCommand, RejectProposalCommand
    queries.py          # ComputeAttributionQuery, GenerateProposalQuery
    handlers.py         # AttributionHandler, ProposalHandler
    __init__.py
  infrastructure/
    duckdb_trade_repository.py   # DuckDB implementation of ITradeHistoryRepository
    duckdb_proposal_repository.py # DuckDB implementation of IProposalRepository
    __init__.py
  DOMAIN.md
```

### Refactored Self-Improver: `personal/self_improver/`
```
personal/self_improver/
  domain/
    services.py         # ImprovementAdvisorService (migrated from advisor.py)
    value_objects.py     # WeightProposal, ImprovementAdvice
    __init__.py
  application/
    handlers.py         # GenerateProposalHandler
    __init__.py
  infrastructure/
    walk_forward_adapter.py  # Wraps core/backtest/walk_forward.py
    __init__.py
```

### Pattern 1: Event-Driven Trade Persistence
**What:** When `PositionClosedEvent` fires, a handler in `src/performance/infrastructure/` persists the closed trade to DuckDB's `trades` table, using the score snapshot from the corresponding `PositionOpenedEvent`.
**When to use:** Every position close.
**Example:**
```python
# src/performance/infrastructure/trade_persistence_handler.py
from src.portfolio.domain.events import PositionClosedEvent

class TradePersistenceHandler:
    def __init__(self, trade_repo: ITradeHistoryRepository):
        self._trade_repo = trade_repo

    def on_position_closed(self, event: PositionClosedEvent) -> None:
        # event now carries score_snapshot + signal_direction from PositionOpenedEvent extension
        trade = ClosedTrade(
            symbol=event.symbol,
            entry_price=event.entry_price,
            exit_price=event.exit_price,
            # ... remaining fields from event
        )
        self._trade_repo.save(trade)
```

### Pattern 2: On-Demand Attribution Computation
**What:** The attribution endpoint queries DuckDB trade history and computes Brinson-Fachler decomposition in real-time. No caching.
**When to use:** Dashboard performance page load.

### Pattern 3: Score Snapshot via Extended Event
**What:** `PositionOpenedEvent` gains a `score_snapshot` field (a frozen dataclass with composite_score, technical_score, fundamental_score, sentiment_score, regime, weights). This snapshot is stored alongside the position and later persisted with the closed trade.
**When to use:** Every position open.

### Anti-Patterns to Avoid
- **Pre-computing attribution on a schedule**: Locked decision is on-demand only. Do not add cron jobs.
- **Storing proposals in SQLite**: Use DuckDB for consistency with trade history analytics.
- **Auto-applying proposals**: SELF-02 mandates propose-then-approve. Never auto-modify weights.
- **Importing from self_improver in performance context**: Cross-context communication via events only per DDD rules.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sharpe/Sortino/Win Rate | Custom metric functions | `core/backtest/metrics.py` (compute_sharpe, compute_win_rate, compute_max_drawdown) | Already tested, handles edge cases (empty data, zero std) |
| Walk-forward validation | Custom backtest splitter | `core/backtest/walk_forward.py` (run_walk_forward) | 5-fold rolling IS/OOS with overfitting score |
| Spearman rank correlation | Manual rank + correlation | `scipy.stats.spearmanr` | Standard IC computation method, handles ties properly |
| DuckDB connection management | Custom connection pooling | `DBFactory.duckdb_conn()` | Singleton per factory, already used by 4+ stores |
| Event subscription wiring | Ad-hoc handler registration | `SyncEventBus.subscribe()` in bootstrap.py | Consistent with all existing cross-context subscriptions |

**Key insight:** The codebase already has Sharpe, max drawdown, win rate, walk-forward, and event bus infrastructure. The new work is: (1) trade persistence via events, (2) Brinson-Fachler decomposition logic, (3) IC/Kelly computation, (4) proposal CRUD.

## Common Pitfalls

### Pitfall 1: PositionClosedEvent Lacks Context
**What goes wrong:** Current `PositionClosedEvent` only has symbol, pnl, pnl_pct. Insufficient for trade history record.
**Why it happens:** Original event designed for simple logging, not analytics.
**How to avoid:** Extend `PositionClosedEvent` to carry entry_price, exit_price, entry_date, exit_date, quantity, strategy, sector, AND the score_snapshot from PositionOpenedEvent. The `Position.close()` method must be updated to include all these fields.
**Warning signs:** Missing fields in trade records showing as NULL in DuckDB.

### Pitfall 2: Score Snapshot Not Available at Close Time
**What goes wrong:** At close time, the score that existed at entry time is no longer available (scores update daily).
**Why it happens:** PositionOpenedEvent fires at entry but the snapshot must survive until close.
**How to avoid:** Store score_snapshot in the Position entity itself (or a separate lookup keyed by symbol). When PositionOpenedEvent fires, persist the snapshot. When PositionClosedEvent fires, attach the stored snapshot.
**Warning signs:** All closed trades have NULL score fields.

### Pitfall 3: IC Calculation on Insufficient Data
**What goes wrong:** Spearman correlation on < 5 data points produces meaningless results.
**Why it happens:** Early in system lifecycle, few closed trades exist.
**How to avoid:** Return null/None for IC when trade_count < 20 (minimum statistical significance). Display "--" in dashboard.
**Warning signs:** IC values of +1.0 or -1.0 (perfect correlation from tiny sample).

### Pitfall 4: DuckDB Table Creation Race Condition
**What goes wrong:** Multiple processes (CLI + API) try to CREATE TABLE IF NOT EXISTS simultaneously.
**Why it happens:** DuckDB file-level locking.
**How to avoid:** Follow existing pattern in `DuckDBSignalStore.__init__()`: CREATE TABLE IF NOT EXISTS in constructor. DuckDB handles this safely for single-process. For multi-process, ensure only one writer (API server) at a time.
**Warning signs:** "database is locked" errors.

### Pitfall 5: Sortino Ratio Not in Existing Metrics
**What goes wrong:** Dashboard KPI card expects Sortino, but `core/backtest/metrics.py` only computes Sharpe.
**Why it happens:** Original metrics module focused on backtest, not live performance.
**How to avoid:** Add `compute_sortino()` to the performance domain service (not to core/backtest -- keep that unchanged). Sortino = mean_return / downside_deviation where downside_deviation uses only negative returns.
**Warning signs:** Sortino always showing "--" or null.

### Pitfall 6: Kelly Efficiency Denominator
**What goes wrong:** Kelly optimal return = 0 when win_rate = 0 or average_win = 0, causing division by zero.
**Why it happens:** Early trades may all be losers.
**How to avoid:** Guard with: if kelly_optimal <= 0, return None (insufficient data). Kelly fraction = win_rate - (1 - win_rate) / (avg_win / avg_loss). Kelly efficiency = actual_geometric_return / theoretical_kelly_return.
**Warning signs:** Kelly efficiency of Infinity or NaN.

## Code Examples

### Brinson-Fachler 4-Level Decomposition
```python
# src/performance/domain/services.py
from dataclasses import dataclass

@dataclass(frozen=True)
class AttributionLevel:
    """Single level in Brinson-Fachler decomposition."""
    name: str
    allocation_effect: float  # Weight allocation contribution
    selection_effect: float   # Stock/signal selection contribution
    interaction_effect: float # Cross-term
    total_effect: float       # Sum of above

class BrinsonFachlerService:
    """4-level Brinson-Fachler attribution.

    Levels:
      1. Portfolio: total portfolio vs benchmark (SPY)
      2. Strategy: swing vs position strategy contribution
      3. Trade: individual trade quality (avg return vs strategy avg)
      4. Skill: IC-based signal quality per scoring axis
    """

    def compute(self, trades: list[ClosedTrade]) -> list[AttributionLevel]:
        # Level 1: Portfolio total return vs benchmark
        portfolio_return = self._portfolio_return(trades)
        # Level 2: Group by strategy, compute per-strategy attribution
        # Level 3: Per-trade excess return over strategy average
        # Level 4: Per-axis IC (fundamental/technical/sentiment)
        ...
```

### Information Coefficient (IC) Calculation
```python
# src/performance/domain/services.py
from scipy.stats import spearmanr

class ICCalculationService:
    """Compute Information Coefficient per scoring axis."""

    MIN_TRADES_FOR_IC = 20

    def compute_axis_ic(
        self, trades: list[ClosedTrade], axis: str
    ) -> float | None:
        """Spearman rank correlation between axis score at entry and realized return.

        Args:
            trades: Closed trades with score snapshots
            axis: "fundamental", "technical", or "sentiment"

        Returns:
            IC value or None if insufficient data.
        """
        if len(trades) < self.MIN_TRADES_FOR_IC:
            return None

        scores = [getattr(t, f"{axis}_score") for t in trades]
        returns = [t.pnl_pct for t in trades]

        if all(s == scores[0] for s in scores):
            return None  # No variance in scores

        ic, _ = spearmanr(scores, returns)
        return round(float(ic), 4)
```

### Kelly Efficiency
```python
# src/performance/domain/services.py

class KellyEfficiencyService:
    """Compute Kelly efficiency = actual geometric return / Kelly-optimal return."""

    def compute(self, trades: list[ClosedTrade]) -> float | None:
        if len(trades) < 20:
            return None

        returns = [t.pnl_pct for t in trades]
        winners = [r for r in returns if r > 0]
        losers = [r for r in returns if r <= 0]

        if not winners or not losers:
            return None

        win_rate = len(winners) / len(returns)
        avg_win = sum(winners) / len(winners)
        avg_loss = abs(sum(losers) / len(losers))

        if avg_loss == 0:
            return None

        # Kelly fraction
        kelly_f = win_rate - (1 - win_rate) / (avg_win / avg_loss)
        if kelly_f <= 0:
            return 0.0  # Negative expectancy

        # Kelly optimal geometric growth rate
        kelly_growth = win_rate * math.log(1 + kelly_f * avg_win) + \
                       (1 - win_rate) * math.log(1 - kelly_f * avg_loss)

        # Actual geometric growth rate (using 1/4 Kelly as per project rules)
        actual_f = kelly_f * 0.25  # Fractional Kelly 1/4
        actual_growth = win_rate * math.log(1 + actual_f * avg_win) + \
                        (1 - win_rate) * math.log(1 - actual_f * avg_loss)

        if kelly_growth <= 0:
            return None

        efficiency = (actual_growth / kelly_growth) * 100
        return round(efficiency, 1)
```

### DuckDB Trade History Repository
```python
# src/performance/infrastructure/duckdb_trade_repository.py
import duckdb
from src.performance.domain.repositories import ITradeHistoryRepository

class DuckDBTradeHistoryRepository(ITradeHistoryRepository):
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                entry_date DATE NOT NULL,
                exit_date DATE NOT NULL,
                entry_price DOUBLE NOT NULL,
                exit_price DOUBLE NOT NULL,
                quantity INTEGER NOT NULL,
                pnl DOUBLE NOT NULL,
                pnl_pct DOUBLE NOT NULL,
                strategy VARCHAR,
                sector VARCHAR,
                composite_score DOUBLE,
                technical_score DOUBLE,
                fundamental_score DOUBLE,
                sentiment_score DOUBLE,
                regime VARCHAR,
                weights_json VARCHAR,
                signal_direction VARCHAR
            )
        """)

    def save(self, trade: ClosedTrade) -> None:
        self._conn.execute(
            "INSERT INTO trades (...) VALUES (...)",
            [...]
        )

    def find_all(self) -> list[ClosedTrade]:
        rows = self._conn.execute("SELECT * FROM trades ORDER BY exit_date").fetchall()
        return [self._to_entity(row) for row in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
```

### Proposal Approval Endpoint Pattern
```python
# commercial/api/routers/performance.py
from fastapi import APIRouter, Depends, HTTPException
from commercial.api.dependencies import get_current_user
from commercial.api.schemas.common import DISCLAIMER

router = APIRouter(prefix="/performance", tags=["Performance"])

@router.get("/attribution")
def get_attribution(user: dict = Depends(get_current_user), handler=Depends(get_attribution_handler)):
    """Brinson-Fachler 4-level attribution with KPIs."""
    result = handler.handle(ComputeAttributionQuery())
    return {**result, "disclaimer": DISCLAIMER}

@router.put("/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str, user: dict = Depends(get_current_user), handler=Depends(get_proposal_handler)):
    """Approve a parameter adjustment proposal."""
    result = handler.handle(ApproveProposalCommand(proposal_id=proposal_id))
    # Apply weights to REGIME_SCORING_WEIGHTS in scoring domain
    return result

@router.put("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str, user: dict = Depends(get_current_user), handler=Depends(get_proposal_handler)):
    """Reject a parameter adjustment proposal."""
    result = handler.handle(RejectProposalCommand(proposal_id=proposal_id))
    return result
```

### Weight Proposal Application (Cross-Context via Event)
```python
# When a proposal is approved, publish WeightsApprovedEvent
# In bootstrap.py, subscribe the scoring regime adjuster to update weights:
#   bus.subscribe(WeightsApprovedEvent, regime_adjuster.on_weights_approved)
# This updates REGIME_SCORING_WEIGHTS in the scoring domain service.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `advisor.py` flat module | DDD bounded context for self-improver | Phase 29 | Testable, injectable, follows project DDD rules |
| No trade history persistence | DuckDB `trades` table with event-driven persistence | Phase 29 | Enables all PERF requirements |
| Performance page placeholder | Real data from `/v1/performance/attribution` | Phase 29 | Dashboard shows actual attribution |
| Walk-forward only in backtest | Walk-forward also validates self-improvement proposals | Phase 29 | SELF-03 compliance |

**Deprecated/outdated:**
- `personal/self_improver/advisor.py` direct import of `core.backtest.walk_forward.WalkForwardResult` -- must be wrapped via infrastructure adapter in DDD refactor

## Open Questions

1. **DuckDB Schema Migration Approach**
   - What we know: DuckDB supports `CREATE TABLE IF NOT EXISTS` (used by all existing stores)
   - What's unclear: Whether to use raw SQL in constructor (existing pattern) or a migration tool
   - Recommendation: **Use raw SQL in constructor** -- consistent with existing `DuckDBSignalStore`, `DuckDBBacktestStore`, and all other DuckDB stores in the project. No need for alembic since DuckDB tables are append-only analytics.

2. **PositionClosedEvent Extension Scope**
   - What we know: Current event has only symbol/pnl/pnl_pct. Needs entry_price, exit_price, entry_date, exit_date, quantity, strategy, sector, score_snapshot, signal_direction.
   - What's unclear: Whether to extend the existing event or create a new enriched event type.
   - Recommendation: **Extend the existing PositionClosedEvent** with all needed fields (backward-compatible via defaults). This matches the CONTEXT.md decision to extend PositionOpenedEvent with score_snapshot.

3. **Benchmark for Portfolio-Level Attribution**
   - What we know: Brinson-Fachler Level 1 needs a benchmark (SPY for US market).
   - What's unclear: How to fetch benchmark returns (DataClient? Cached?)
   - Recommendation: Use `DataClient` (already in bootstrap context) to fetch SPY returns. Cache benchmark returns in DuckDB if latency is a concern.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_performance.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PERF-01 | Trade P&L persisted to DuckDB with all fields | unit | `pytest tests/unit/test_performance_trade_repo.py -x` | Wave 0 |
| PERF-02 | Brinson-Fachler returns 4 levels with allocation/selection/interaction | unit | `pytest tests/unit/test_brinson_fachler.py -x` | Wave 0 |
| PERF-03 | IC computed per axis, compared to 0.03 threshold | unit | `pytest tests/unit/test_ic_calculation.py -x` | Wave 0 |
| PERF-04 | Kelly efficiency computed and compared to 70% threshold | unit | `pytest tests/unit/test_kelly_efficiency.py -x` | Wave 0 |
| PERF-05 | PositionOpenedEvent carries score_snapshot, Position stores it | unit | `pytest tests/unit/test_position_score_snapshot.py -x` | Wave 0 |
| SELF-01 | Proposals generated with weight adjustments per regime | unit | `pytest tests/unit/test_self_improver_proposal.py -x` | Wave 0 |
| SELF-02 | Approve/reject endpoints update proposal status | unit | `pytest tests/unit/test_proposal_approval.py -x` | Wave 0 |
| SELF-03 | Walk-forward validation runs before proposal is offered | unit | `pytest tests/unit/test_self_improver_proposal.py::test_walk_forward_required -x` | Wave 0 |
| SELF-04 | < 50 trades returns empty proposals | unit | `pytest tests/unit/test_self_improver_proposal.py::test_threshold_50 -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_performance*.py tests/unit/test_brinson*.py tests/unit/test_ic*.py tests/unit/test_kelly*.py tests/unit/test_self_improver*.py tests/unit/test_proposal*.py tests/unit/test_position_score_snapshot.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_performance_trade_repo.py` -- covers PERF-01
- [ ] `tests/unit/test_brinson_fachler.py` -- covers PERF-02
- [ ] `tests/unit/test_ic_calculation.py` -- covers PERF-03
- [ ] `tests/unit/test_kelly_efficiency.py` -- covers PERF-04
- [ ] `tests/unit/test_position_score_snapshot.py` -- covers PERF-05
- [ ] `tests/unit/test_self_improver_proposal.py` -- covers SELF-01, SELF-03, SELF-04
- [ ] `tests/unit/test_proposal_approval.py` -- covers SELF-02

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/portfolio/domain/events.py`, `src/portfolio/domain/entities.py` -- current event/entity structure
- Existing codebase: `core/backtest/metrics.py` -- Sharpe, max drawdown, win rate computations
- Existing codebase: `core/backtest/walk_forward.py` -- walk-forward validation engine
- Existing codebase: `personal/self_improver/advisor.py` -- current improvement logic
- Existing codebase: `src/signals/infrastructure/duckdb_signal_store.py` -- DuckDB usage patterns
- Existing codebase: `src/bootstrap.py` -- DI wiring, event subscriptions
- Existing codebase: `commercial/api/` -- FastAPI router patterns, auth, rate limiting
- Existing codebase: `dashboard/src/app/(dashboard)/performance/page.tsx` -- Phase 28 shell
- Existing codebase: `dashboard/src/hooks/use-performance.ts` -- existing hook with 404 fallback
- Existing codebase: `dashboard/src/types/api.ts` -- PerformanceData/PerformanceKPI types

### Secondary (MEDIUM confidence)
- Brinson-Fachler decomposition methodology: standard portfolio attribution theory (allocation + selection + interaction effects)
- Spearman IC calculation: standard quantitative finance practice for measuring signal predictive power

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and used in codebase
- Architecture: HIGH -- follows exact DDD patterns established in 6+ existing bounded contexts
- Pitfalls: HIGH -- identified from direct codebase analysis of existing event/entity limitations
- Domain logic (Brinson-Fachler, IC, Kelly): MEDIUM -- mathematical formulas are standard but implementation details need careful testing

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable domain, no external dependency changes expected)
