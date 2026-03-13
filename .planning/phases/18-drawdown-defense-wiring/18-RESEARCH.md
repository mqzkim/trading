# Phase 18: Drawdown Defense Wiring - Research

**Researched:** 2026-03-14
**Domain:** Cross-phase integration wiring (event bus subscriptions, parameter bridging)
**Confidence:** HIGH

## Summary

Phase 18 closes the final 2 gaps from the v1.2 milestone audit. Both issues are pure wiring problems -- the implementation code exists and is fully tested at the unit level, but the cross-phase integration is missing. No new domain logic, libraries, or architectural patterns are needed.

**Gap 1 (APPR-05):** `ApprovalHandler.suspend_for_drawdown()` is fully implemented at `src/approval/application/handlers.py:125` and unit-tested, but `bootstrap.py` has no `bus.subscribe(DrawdownAlertEvent, ...)` call -- the method is dead code at runtime. The event publishes correctly to SSEBridge (verified by Phase 17) but never reaches the approval handler.

**Gap 2 (PIPE-06):** `PipelineOrchestrator._should_halt(drawdown_level)` works correctly when called with "warning" or "critical" (unit tests pass), but `RunPipelineHandler.handle()` at `src/pipeline/application/handlers.py:82-87` calls `orchestrator.run()` without the `drawdown_level` parameter -- it always defaults to "normal", so the pipeline never halts on drawdown. The `Portfolio.drawdown_level` property exists but is never queried by the pipeline.

**Primary recommendation:** Two targeted changes (bootstrap.py event subscription + RunPipelineHandler parameter bridge) plus 2-3 integration tests that publish events through the real SyncEventBus. Estimated scope: 3-4 files modified, under 50 lines of new code.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APPR-05 | Drawdown tier 2+ automatically suspends strategy approval and halts automated execution | Gap 1: Add `bus.subscribe(DrawdownAlertEvent, ...)` in bootstrap.py to wire the existing `suspend_for_drawdown()` method |
| PIPE-06 | Pipeline auto-halts execution when regime is Crisis or drawdown tier >= 2 | Gap 2: Query portfolio drawdown_level in RunPipelineHandler.handle() and pass to orchestrator.run() |
</phase_requirements>

## Standard Stack

### Core (already in project -- no new dependencies)

| Library | Version | Purpose | Already Used In |
|---------|---------|---------|-----------------|
| SyncEventBus | internal | Synchronous in-process event bus | bootstrap.py, all event subscriptions |
| pytest | 9.0.2 | Test framework | all test files |
| unittest.mock | stdlib | Mocking for unit tests | all test files |

### No New Dependencies

This phase requires zero new packages. All code changes use existing project infrastructure:
- `SyncEventBus.subscribe()` for event wiring
- `IPortfolioRepository.find_by_id()` for drawdown state query
- `Portfolio.drawdown_level` property (already computed correctly)
- `DrawdownAlertEvent` (already defined in `src/portfolio/domain/events.py`)

## Architecture Patterns

### Existing Event Subscription Pattern (follow exactly)

The RegimeChangedEvent -> approval suspension pattern in `bootstrap.py:227-230` is the template:

```python
# Existing pattern in bootstrap.py (RegimeChangedEvent -> approval)
from src.regime.domain.events import RegimeChangedEvent

def _on_regime_changed(event: RegimeChangedEvent) -> None:
    approval_handler.suspend_if_regime_invalid(event.new_regime)

bus.subscribe(RegimeChangedEvent, _on_regime_changed)
```

The DrawdownAlertEvent subscription MUST follow this identical pattern:

```python
# New: DrawdownAlertEvent -> approval suspension
from src.portfolio.domain.events import DrawdownAlertEvent

def _on_drawdown_alert(event: DrawdownAlertEvent) -> None:
    # Only suspend on tier 2+ (warning/critical)
    if event.level in ("warning", "critical"):
        approval_handler.suspend_for_drawdown()

bus.subscribe(DrawdownAlertEvent, _on_drawdown_alert)
```

**Key detail:** The `DrawdownAlertEvent.level` field uses string values: "caution", "warning", "critical". Only "warning" (tier 2, 15-20%) and "critical" (tier 3, 20%+) should trigger approval suspension per the 3-tier drawdown defense protocol in CLAUDE.md.

### Parameter Bridge Pattern (RunPipelineHandler)

The handler already has access to the bootstrap context dict via `self._handlers`. The portfolio_repo and portfolio_handler are both in the context. The drawdown_level can be queried before calling `orchestrator.run()`:

```python
# In RunPipelineHandler.handle(), before orchestrator.run():
drawdown_level = "normal"  # safe default
portfolio_repo = self._handlers.get("portfolio_repo")
if portfolio_repo is not None:
    portfolio = portfolio_repo.find_by_id("default")
    if portfolio is not None:
        drawdown_level = portfolio.drawdown_level.value

run = self._orchestrator.run(
    handlers=self._handlers,
    symbols=symbols,
    dry_run=cmd.dry_run,
    mode=mode,
    drawdown_level=drawdown_level,  # NEW: pass actual drawdown state
)
```

**DDD consideration:** RunPipelineHandler is in the application layer, which CAN access other bounded contexts' repositories via the bootstrap context dict. This follows the existing pattern (it already accesses `approval_gate`, `approval_handler`, `budget_repo`, `regime_handler` from other contexts).

### File Change Map

| File | Change | Size |
|------|--------|------|
| `src/bootstrap.py` | Add `bus.subscribe(DrawdownAlertEvent, ...)` | ~6 lines |
| `src/pipeline/application/handlers.py` | Query drawdown_level before `orchestrator.run()` | ~8 lines |
| `tests/integration/test_drawdown_defense.py` | NEW: 2-3 integration tests | ~80-100 lines |
| `src/bootstrap.py` | Expose `portfolio_repo` in ctx (already there at line 314) | 0 lines (already done) |

### Recommended Test Structure

```
tests/
  integration/
    test_drawdown_defense.py      # NEW: cross-phase integration tests
```

Integration tests should:
1. Create real SyncEventBus + real SQLite repos (`:memory:`)
2. Wire subscriptions as bootstrap.py does
3. Publish DrawdownAlertEvent through the bus
4. Assert approval handler suspends
5. Assert pipeline halts with drawdown_level passed through

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Event routing | Custom pub/sub | Existing SyncEventBus | Already proven in 5+ cross-context subscriptions |
| Drawdown detection | New detection logic | Existing Portfolio.drawdown_level property | Already correct, already tested |
| Approval suspension | New suspension mechanism | Existing StrategyApproval.suspend("drawdown_tier2") | Exact mechanism already built and tested |
| Pipeline halt | New halt mechanism | Existing PipelineOrchestrator._should_halt() | Already handles "warning"/"critical" strings correctly |

**Key insight:** Every piece of logic needed for this phase already exists and is unit-tested. The only missing piece is the wiring -- connecting existing output to existing input.

## Common Pitfalls

### Pitfall 1: Subscribing to Wrong Event Level
**What goes wrong:** Subscribing DrawdownAlertEvent without filtering by level means "caution" (10%) would also suspend approval, which is too aggressive.
**Why it happens:** DrawdownAlertEvent fires for ALL drawdown levels (caution/warning/critical), not just tier 2+.
**How to avoid:** Filter `event.level in ("warning", "critical")` in the subscription handler before calling `suspend_for_drawdown()`.
**Warning signs:** Test with caution-level event passes when it should not trigger suspension.

### Pitfall 2: Portfolio Not Found Returns None
**What goes wrong:** `portfolio_repo.find_by_id("default")` returns None when no portfolio exists yet (new system, no positions opened).
**Why it happens:** Portfolio is created lazily on first `open_position` call.
**How to avoid:** Default to `drawdown_level = "normal"` when portfolio is None. This is safe because no positions = no drawdown.
**Warning signs:** KeyError or AttributeError in pipeline handler when run before any positions exist.

### Pitfall 3: DrawdownLevel Enum vs String Mismatch
**What goes wrong:** `Portfolio.drawdown_level` returns a `DrawdownLevel` enum, but `PipelineOrchestrator._should_halt()` expects a lowercase string.
**Why it happens:** Different conventions between portfolio domain (enum) and pipeline domain (string).
**How to avoid:** Use `.value` to convert: `portfolio.drawdown_level.value` returns "normal", "caution", "warning", "critical" as strings.
**Warning signs:** `_should_halt()` always returns False because `DrawdownLevel.WARNING` (enum) does not match `"warning"` (string).

### Pitfall 4: DDD Cross-Context Import
**What goes wrong:** Importing DrawdownAlertEvent directly in pipeline domain would violate DDD rules.
**Why it happens:** Temptation to import from another bounded context.
**How to avoid:** The subscription happens in `bootstrap.py` (composition root), which is the ONLY file allowed to import across contexts. The pipeline handler accesses portfolio_repo via the handlers dict (already in context).
**Warning signs:** Direct `from src.portfolio.domain.events import ...` in pipeline code files.

### Pitfall 5: Portfolio ID Assumption
**What goes wrong:** Hard-coding portfolio_id as "default" may not match the actual portfolio created by PortfolioManagerHandler.
**Why it happens:** PortfolioManagerHandler uses `cmd.portfolio_id` from OpenPositionCommand.
**How to avoid:** Check what portfolio_id is used in practice -- the default in `open_position` comes from the CLI command, typically "default". If needed, iterate all portfolios or use the first found.
**Warning signs:** `find_by_id("default")` always returns None in production.

## Code Examples

### Example 1: DrawdownAlertEvent Structure (verified from source)
```python
# Source: src/portfolio/domain/events.py:32
@dataclass(frozen=True)
class DrawdownAlertEvent(DomainEvent):
    portfolio_id: str = ""
    drawdown: float = 0.0
    level: str = ""  # "caution" | "warning" | "critical"
```

### Example 2: DrawdownLevel Enum Values (verified from source)
```python
# Source: src/portfolio/domain/value_objects.py:18
class DrawdownLevel(Enum):
    NORMAL = "normal"      # < 10%
    CAUTION = "caution"    # 10-15% -> new entry blocked
    WARNING = "warning"    # 15-20% -> 50% position reduction
    CRITICAL = "critical"  # > 20% -> full liquidation
```

### Example 3: Existing RegimeChangedEvent Subscription Pattern (template to follow)
```python
# Source: src/bootstrap.py:227-230
def _on_regime_changed(event: RegimeChangedEvent) -> None:
    approval_handler.suspend_if_regime_invalid(event.new_regime)

bus.subscribe(RegimeChangedEvent, _on_regime_changed)
```

### Example 4: Existing PipelineOrchestrator._should_halt() (already works correctly)
```python
# Source: src/pipeline/domain/services.py:532
_HALT_DRAWDOWN_LEVELS = {"warning", "critical"}

def _should_halt(self, regime_type: str, drawdown_level: str) -> bool:
    if regime_type == "Crisis":
        return True
    if drawdown_level.lower() in _HALT_DRAWDOWN_LEVELS:
        return True
    return False
```

### Example 5: Integration Test Pattern (verified from existing tests)
```python
# Pattern from tests/unit/test_approval_integration.py
# Use real SQLite repos with :memory: and real SyncEventBus
from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.portfolio.domain.events import DrawdownAlertEvent

def test_drawdown_event_suspends_approval():
    bus = SyncEventBus()
    approval_repo = SqliteApprovalRepository(db_path=":memory:")
    # ... create handler, subscribe, publish event, assert suspension
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct method calls | Event bus subscriptions | Phase 14+ | Decoupled cross-context communication |
| Manual drawdown checking | DrawdownAlertEvent fired from Portfolio aggregate | Phase 12 | Automatic drawdown detection on position changes |

**Nothing deprecated or changed** -- all existing patterns are current and stable.

## Open Questions

1. **Portfolio ID Convention**
   - What we know: `PortfolioManagerHandler` uses `cmd.portfolio_id` from `OpenPositionCommand`, which defaults to a string set by the caller (CLI or pipeline)
   - What's unclear: Whether "default" is consistently used across all callers
   - Recommendation: Check the CLI and pipeline callers for the portfolio_id value used. If uncertain, query all portfolios or use a defensive approach (iterate).

2. **Caution Level Handling**
   - What we know: DrawdownAlertEvent fires for ALL non-normal levels including "caution" (10%)
   - What's unclear: Should "caution" also affect pipeline behavior in any way?
   - Recommendation: Per APPR-05 requirement text ("Drawdown tier 2+"), only "warning" and "critical" trigger suspension. "Caution" is tier 1 -- new entry blocked by Portfolio.can_open_position() but pipeline continues and approval stays active.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `python3 -m pytest tests/integration/test_drawdown_defense.py -x -v` |
| Full suite command | `python3 -m pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| APPR-05 | DrawdownAlertEvent fires -> approval handler suspends via bus subscription | integration | `python3 -m pytest tests/integration/test_drawdown_defense.py::test_drawdown_event_suspends_approval -x` | Wave 0 |
| APPR-05 | Caution-level event does NOT suspend (only tier 2+) | integration | `python3 -m pytest tests/integration/test_drawdown_defense.py::test_caution_level_does_not_suspend -x` | Wave 0 |
| PIPE-06 | Pipeline halts when drawdown_level >= warning | integration | `python3 -m pytest tests/integration/test_drawdown_defense.py::test_pipeline_halts_on_drawdown_warning -x` | Wave 0 |
| PIPE-06 | Pipeline passes drawdown_level through handler to orchestrator | unit | `python3 -m pytest tests/unit/test_pipeline_orchestrator.py::test_halt_on_warning_drawdown -x` | Exists (passes when called directly) |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/integration/test_drawdown_defense.py tests/unit/test_pipeline_orchestrator.py tests/unit/test_approval_integration.py -x -v`
- **Per wave merge:** `python3 -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/integration/test_drawdown_defense.py` -- covers APPR-05, PIPE-06 cross-phase integration
- [ ] No new fixtures or framework config needed -- existing pytest infrastructure sufficient

## Sources

### Primary (HIGH confidence)
- `src/bootstrap.py` -- verified no DrawdownAlertEvent subscription exists (line-by-line review)
- `src/pipeline/application/handlers.py:82-87` -- verified `drawdown_level` parameter not passed to `orchestrator.run()`
- `src/pipeline/domain/services.py:532-543` -- verified `_should_halt()` works correctly when given proper drawdown_level
- `src/approval/application/handlers.py:125-134` -- verified `suspend_for_drawdown()` fully implemented
- `src/portfolio/domain/aggregates.py:67-75` -- verified `drawdown_level` property returns correct DrawdownLevel enum
- `src/portfolio/domain/events.py:32-37` -- verified DrawdownAlertEvent structure with `level` field
- `.planning/v1.2-MILESTONE-AUDIT.md` -- audit evidence for both gaps

### Secondary (MEDIUM confidence)
- `src/shared/infrastructure/sync_event_bus.py` -- verified SyncEventBus.subscribe/publish API
- `tests/unit/test_approval_integration.py` -- verified testing patterns for approval handler
- `tests/unit/test_pipeline_orchestrator.py` -- verified testing patterns for pipeline halt

### Tertiary (LOW confidence)
- Portfolio ID convention ("default") -- inferred from code patterns but not verified in all callers

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing code
- Architecture: HIGH -- follows exact existing patterns (RegimeChangedEvent subscription template)
- Pitfalls: HIGH -- all pitfalls verified from source code analysis

**Research date:** 2026-03-14
**Valid until:** Indefinite -- this is a wiring fix, not affected by library version changes
