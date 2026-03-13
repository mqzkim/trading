# Phase 14: Strategy and Budget Approval - Research

**Researched:** 2026-03-13
**Domain:** Trading strategy approval, budget enforcement, regime-gated execution
**Confidence:** HIGH

## Summary

Phase 14 introduces a gating layer between the automated pipeline (Phase 13) and trade execution. Currently, `PipelineOrchestrator._run_execute()` auto-approves all trade plans. This phase replaces that auto-approve with a strategy approval system: the user pre-defines what trades are allowed (score threshold, regime allow-list, max per-trade %, expiration date) and a daily budget cap. Trades matching the approval execute automatically; trades outside boundaries queue for manual review.

The implementation fits cleanly as a new bounded context (`src/approval/`) following the existing DDD patterns. The key integration points are: (1) `PipelineOrchestrator._run_execute()` must check approval before auto-approving, (2) `RegimeChangedEvent` subscription suspends active approvals, and (3) drawdown tier 2+ (already checked in pipeline halt logic) must also suspend approvals.

**Primary recommendation:** Create an `approval` bounded context with `StrategyApproval` entity + `DailyBudget` value object, SQLite persistence, and wire into the pipeline orchestrator's execute stage as a pre-check gate.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APPR-01 | User can create strategy approval with score threshold, regime allow-list, max per-trade %, and expiration date | New `StrategyApproval` entity with these fields, CLI commands to create/view/revoke, SQLite persistence |
| APPR-02 | User can set daily budget cap with real-time spent/remaining tracking per pipeline run | `DailyBudget` value object + `DailyBudgetTracker` service, SQLite table for daily spend tracking |
| APPR-03 | Trades exceeding budget or strategy parameters queue for manual review | `ApprovalGateService` checks each trade plan against approval + budget; non-matching plans get `PENDING_REVIEW` status |
| APPR-04 | Regime change event automatically suspends active strategy approval | `RegimeChangedEvent` subscriber in approval context suspends active approval, sets `suspended_reason` |
| APPR-05 | Drawdown tier 2+ automatically suspends strategy approval and halts execution | Drawdown check in approval gate (reuses existing cooldown repo tier info) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| dataclasses | stdlib | Entity/VO definitions | Project pattern -- all domain objects are dataclasses |
| sqlite3 | stdlib | Persistence | Project uses SQLite for all domain repos |
| datetime | stdlib | Expiration, timestamps | UTC-based expiry checking (project pattern) |
| enum | stdlib | Status enums | All status types use Python Enum |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typer | existing | CLI commands for approval CRUD | `trading approve create/status/revoke` |
| rich | existing | CLI output formatting | Tables for approval status display |
| pydantic-settings | existing | Settings for default budget | If default budget needs env var |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `approval/` BC | Extend `execution/` | Separate BC is cleaner -- approval is a distinct business concern, not execution |
| SQLite for budget tracking | In-memory only | SQLite survives restarts, enables dashboard queries in Phase 16 |

**Installation:**
No new packages needed. All dependencies already installed.

## Architecture Patterns

### Recommended Project Structure
```
src/
  approval/
    domain/
      entities.py          # StrategyApproval entity
      value_objects.py      # DailyBudget, ApprovalStatus, TradeReviewItem
      services.py           # ApprovalGateService (checks trade against approval)
      repositories.py       # IApprovalRepository, IBudgetRepository (ABC)
      events.py             # ApprovalSuspendedEvent, ApprovalCreatedEvent
      __init__.py
    application/
      commands.py           # CreateApprovalCommand, RevokeApprovalCommand, SetBudgetCommand
      handlers.py           # ApprovalHandler (CRUD), BudgetHandler
      __init__.py
    infrastructure/
      sqlite_approval_repo.py   # SQLite persistence for approvals
      sqlite_budget_repo.py     # SQLite persistence for daily budget tracking
      __init__.py
    DOMAIN.md
```

### Pattern 1: Approval Gate in Pipeline
**What:** Insert approval check between plan generation and order execution in `PipelineOrchestrator._run_execute()`
**When to use:** Every automated pipeline run
**Example:**
```python
# In PipelineOrchestrator._run_execute() -- replace auto-approve
for plan in trade_plans:
    gate_result = approval_gate.check(plan, current_regime, daily_spent)
    if gate_result.approved:
        trade_plan_handler.approve(ApproveTradePlanCommand(symbol=plan.symbol, approved=True))
        trade_plan_handler.execute(ExecuteOrderCommand(symbol=plan.symbol))
        daily_spent += plan.position_value
    else:
        # Queue for manual review -- save with PENDING status, do NOT auto-approve
        logger.info("Trade %s queued for review: %s", plan.symbol, gate_result.reason)
```

### Pattern 2: Event-Driven Suspension (RegimeChangedEvent)
**What:** Subscribe to `RegimeChangedEvent` from regime context; if new regime not in approval's allow-list, suspend the approval
**When to use:** Automatic, via SyncEventBus subscription in bootstrap
**Example:**
```python
# In bootstrap.py -- wire approval suspension
def _on_regime_changed(event: RegimeChangedEvent):
    approval_handler.suspend_if_regime_invalid(event.new_regime)

bus.subscribe(RegimeChangedEvent, _on_regime_changed)
```

### Pattern 3: Daily Budget Reset
**What:** Budget tracking resets daily (by UTC date). Each pipeline run records how much capital was committed.
**When to use:** Per pipeline run, checked before each trade execution
**Example:**
```python
# DailyBudget tracking
@dataclass
class DailyBudgetTracker:
    budget_cap: float          # user-set daily limit
    date: str                  # YYYY-MM-DD UTC
    spent: float = 0.0

    @property
    def remaining(self) -> float:
        return max(0.0, self.budget_cap - self.spent)

    def can_spend(self, amount: float) -> bool:
        return amount <= self.remaining
```

### Anti-Patterns to Avoid
- **Checking approval in SafeExecutionAdapter:** Approval is a business rule, not execution safety. Keep it in the pipeline orchestrator or a dedicated approval gate service, not in the broker adapter layer.
- **Storing approval state in memory only:** Must survive process restarts (APScheduler pattern from Phase 13). Use SQLite.
- **Hard-coding regime allow-list:** The user defines which regimes are allowed per approval. Don't assume "Bull only."

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date comparison for expiry | Custom timezone logic | `datetime.now(timezone.utc) > expires_at` | Project pattern from CooldownState -- expiry in Python, not SQL |
| Event subscription | Custom callback registry | `SyncEventBus.subscribe()` | Already exists and works |
| SQLite schema management | Migration framework | `CREATE TABLE IF NOT EXISTS` | Project pattern -- all repos use this approach |
| Daily date key | Complex calendar logic | `datetime.now(timezone.utc).strftime("%Y-%m-%d")` | Simple UTC date string as daily budget key |

**Key insight:** This phase requires no new libraries. Every pattern already exists in the codebase (CooldownState for expiry, SyncEventBus for events, SQLite repos for persistence).

## Common Pitfalls

### Pitfall 1: Race Condition Between Budget Check and Execution
**What goes wrong:** Multiple trades pass budget check simultaneously, then total exceeds budget.
**Why it happens:** Budget check and spend recording are not atomic.
**How to avoid:** Process trade plans sequentially in the execute stage (already the pattern in `_run_execute`). Update spent amount immediately after each successful execution, not after all trades.
**Warning signs:** Total daily spend exceeding budget cap.

### Pitfall 2: Stale Approval After Regime Change Mid-Pipeline
**What goes wrong:** Regime changes during a pipeline run (between regime stage and execute stage), but approval was checked before the change.
**Why it happens:** Regime detection happens at Stage 2, execution at Stage 6. If event fires at Stage 2 and suspends approval, execute stage should see it.
**How to avoid:** Check approval status at the point of execution (Stage 6), not at pipeline start. The `RegimeChangedEvent` handler suspends synchronously via `SyncEventBus`, so by the time execute runs, the approval is already suspended.
**Warning signs:** Trades executing in a regime not on the allow-list.

### Pitfall 3: Approval Expiration Not Checked Per-Trade
**What goes wrong:** An approval expires between the first and last trade in a pipeline run.
**Why it happens:** Only checking expiry at pipeline start, not per-trade.
**How to avoid:** Check `approval.is_expired()` inside the per-trade loop in the approval gate.
**Warning signs:** Trades executing after approval expiration timestamp.

### Pitfall 4: Conflicting Suspension Sources
**What goes wrong:** Both regime change and drawdown tier 2+ suspend the approval. When one clears, the other should still block.
**Why it happens:** Single `is_suspended` flag doesn't track why it was suspended.
**How to avoid:** Use a `suspended_reasons: set[str]` field (e.g., `{"regime_change", "drawdown_tier2"}`). Only reactivate when all reasons are cleared.
**Warning signs:** Approval reactivating while drawdown is still at tier 2.

### Pitfall 5: DDD Layer Violation in Approval Check
**What goes wrong:** Importing from `approval/` context directly in `pipeline/domain/services.py`.
**Why it happens:** `PipelineOrchestrator` needs approval info but is a domain service.
**How to avoid:** Pass approval gate as a parameter through `handlers` dict (same pattern as other cross-context dependencies). The orchestrator calls it but doesn't import from it.
**Warning signs:** `from src.approval import ...` appearing in `pipeline/domain/`.

## Code Examples

### StrategyApproval Entity
```python
# src/approval/domain/entities.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from src.shared.domain import Entity

@dataclass(eq=False)
class StrategyApproval(Entity[str]):
    _id: str
    score_threshold: float           # minimum composite score to auto-execute
    allowed_regimes: list[str]       # e.g., ["Bull", "Sideways"]
    max_per_trade_pct: float         # max % of capital per trade (e.g., 8.0)
    expires_at: datetime             # mandatory expiration
    daily_budget_cap: float          # daily capital limit
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    suspended_reasons: set[str] = field(default_factory=set)

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_suspended(self) -> bool:
        return len(self.suspended_reasons) > 0

    @property
    def is_effective(self) -> bool:
        """Approval is active, not expired, and not suspended."""
        return self.is_active and not self.is_expired and not self.is_suspended

    def suspend(self, reason: str) -> None:
        self.suspended_reasons.add(reason)

    def unsuspend(self, reason: str) -> None:
        self.suspended_reasons.discard(reason)

    def revoke(self) -> None:
        self.is_active = False
```

### ApprovalGateService
```python
# src/approval/domain/services.py
from dataclasses import dataclass

@dataclass(frozen=True)
class GateResult:
    approved: bool
    reason: str = ""

class ApprovalGateService:
    """Check a trade plan against active strategy approval + budget."""

    def check(
        self,
        plan_symbol: str,
        plan_score: float,
        plan_position_pct: float,  # position_value / capital * 100
        current_regime: str,
        daily_remaining: float,
        plan_position_value: float,
        approval,  # StrategyApproval or None
    ) -> GateResult:
        if approval is None:
            return GateResult(approved=False, reason="No active approval")
        if not approval.is_effective:
            return GateResult(approved=False, reason="Approval not effective")
        if plan_score < approval.score_threshold:
            return GateResult(approved=False, reason=f"Score {plan_score} below threshold {approval.score_threshold}")
        if current_regime not in approval.allowed_regimes:
            return GateResult(approved=False, reason=f"Regime {current_regime} not allowed")
        if plan_position_pct > approval.max_per_trade_pct:
            return GateResult(approved=False, reason=f"Position {plan_position_pct}% exceeds max {approval.max_per_trade_pct}%")
        if plan_position_value > daily_remaining:
            return GateResult(approved=False, reason=f"Position ${plan_position_value} exceeds remaining budget ${daily_remaining}")
        return GateResult(approved=True)
```

### SQLite Approval Repository Schema
```python
# src/approval/infrastructure/sqlite_approval_repo.py
_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS strategy_approvals (
        approval_id         TEXT PRIMARY KEY,
        score_threshold     REAL NOT NULL,
        allowed_regimes     TEXT NOT NULL,  -- JSON array
        max_per_trade_pct   REAL NOT NULL,
        expires_at          TEXT NOT NULL,
        daily_budget_cap    REAL NOT NULL,
        created_at          TEXT NOT NULL,
        is_active           INTEGER NOT NULL DEFAULT 1,
        suspended_reasons   TEXT NOT NULL DEFAULT '[]'  -- JSON array
    );
"""

_CREATE_BUDGET_TABLE = """
    CREATE TABLE IF NOT EXISTS daily_budget (
        date_key            TEXT PRIMARY KEY,  -- YYYY-MM-DD
        budget_cap          REAL NOT NULL,
        spent               REAL NOT NULL DEFAULT 0.0,
        trade_count         INTEGER NOT NULL DEFAULT 0,
        updated_at          TEXT NOT NULL
    );
"""

_CREATE_REVIEW_QUEUE_TABLE = """
    CREATE TABLE IF NOT EXISTS trade_review_queue (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol              TEXT NOT NULL,
        plan_json           TEXT NOT NULL,
        rejection_reason    TEXT NOT NULL,
        pipeline_run_id     TEXT,
        created_at          TEXT NOT NULL,
        reviewed            INTEGER NOT NULL DEFAULT 0
    );
"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Auto-approve all plans in `_run_execute` | Approval gate checks before execution | Phase 14 (now) | Trades must match pre-defined strategy to auto-execute |
| No daily budget tracking | Daily budget cap with spent/remaining | Phase 14 (now) | Capital commitment limited per day |
| Pipeline halts on Crisis regime | Approval also suspends on regime change | Phase 14 (now) | Double protection: pipeline halt + approval suspension |

**Current state (pre-Phase 14):**
- `PipelineOrchestrator._run_execute()` auto-approves every trade plan (13-03 decision: "Auto-approve trade plans in _run_execute -- manual approval deferred to Phase 14")
- Pipeline halts on Crisis regime or drawdown tier 2+ (PIPE-06), but no per-trade gating
- No concept of strategy parameters or budget limits

## Open Questions

1. **Review queue UX for Phase 14 vs Phase 16**
   - What we know: Trades queued for review need to be actionable before the dashboard (Phase 16)
   - What's unclear: How detailed should the CLI review flow be?
   - Recommendation: CLI commands `trading review list` and `trading review approve/reject <symbol>` are sufficient for Phase 14. Dashboard view is Phase 16 (DASH-06).

2. **Multiple active approvals**
   - What we know: The simplest model is one active approval at a time
   - What's unclear: Should users be able to have multiple approvals (e.g., different score thresholds for different regimes)?
   - Recommendation: Single active approval for Phase 14. Creating a new one deactivates the previous. Keeps the gate logic simple.

3. **Budget tracking granularity**
   - What we know: APPR-02 says "real-time spent/remaining tracking per pipeline run"
   - What's unclear: Does "real-time" mean within a single run, or visible between runs during the day?
   - Recommendation: Track per-trade within a run (sequential execution makes this straightforward). Persist to SQLite so CLI can query current day's status anytime.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pytest.ini` (or `pyproject.toml` section) |
| Quick run command | `pytest tests/unit/test_approval.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| APPR-01 | Create approval with all parameters, validation | unit | `pytest tests/unit/test_approval_domain.py -x` | No -- Wave 0 |
| APPR-02 | Daily budget cap tracking, spent/remaining | unit | `pytest tests/unit/test_budget_tracking.py -x` | No -- Wave 0 |
| APPR-03 | Gate rejects trades outside params, queues for review | unit | `pytest tests/unit/test_approval_gate.py -x` | No -- Wave 0 |
| APPR-04 | Regime change suspends approval | unit | `pytest tests/unit/test_approval_suspension.py -x` | No -- Wave 0 |
| APPR-05 | Drawdown tier 2+ suspends approval | unit | `pytest tests/unit/test_approval_suspension.py -x` | No -- Wave 0 |
| Integration | Pipeline with approval gate end-to-end | integration | `pytest tests/integration/test_pipeline_approval.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_approval*.py tests/unit/test_budget*.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_approval_domain.py` -- covers APPR-01 (entity creation, validation, expiry)
- [ ] `tests/unit/test_approval_gate.py` -- covers APPR-03 (gate check logic)
- [ ] `tests/unit/test_budget_tracking.py` -- covers APPR-02 (daily budget)
- [ ] `tests/unit/test_approval_suspension.py` -- covers APPR-04, APPR-05 (suspension logic)
- [ ] `tests/integration/test_pipeline_approval.py` -- covers approval gate in pipeline flow

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/pipeline/domain/services.py` -- current auto-approve pattern in `_run_execute()`
- Codebase analysis: `src/execution/domain/value_objects.py` -- CooldownState expiry pattern
- Codebase analysis: `src/regime/domain/events.py` -- RegimeChangedEvent for subscription
- Codebase analysis: `src/shared/infrastructure/sync_event_bus.py` -- event bus pattern
- Codebase analysis: `src/bootstrap.py` -- composition root wiring pattern
- Codebase analysis: `src/execution/infrastructure/sqlite_cooldown_repo.py` -- SQLite repo pattern
- Codebase analysis: `src/pipeline/infrastructure/sqlite_pipeline_repo.py` -- SQLite repo pattern

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` -- decision "[13-03]: Auto-approve trade plans in _run_execute (manual approval deferred to Phase 14)"
- `.planning/REQUIREMENTS.md` -- APPR-01 through APPR-05 requirements

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries needed, all patterns exist in codebase
- Architecture: HIGH -- follows existing DDD bounded context pattern exactly
- Pitfalls: HIGH -- identified from concrete code analysis of pipeline flow
- Integration points: HIGH -- clear from reading `_run_execute()` and bootstrap wiring

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable domain, internal patterns)
