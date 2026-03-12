# Phase 8: Market Regime Detection - Research

**Researched:** 2026-03-12
**Domain:** Market regime detection wiring -- DDD handler, 3-day confirmation, EventBus publishing, scoring weight adjustment, CLI
**Confidence:** HIGH

## Summary

Phase 8 is a **wiring and integration** phase, not a greenfield build. The regime bounded context already has complete domain layer code (entities, value objects, events, services, repository interface + SQLite implementation), a working application handler, and a data pipeline that collects VIX/S&P500/yield curve data into DuckDB. The core regime classifier (legacy `core/regime/`) also works end-to-end with the CLI.

The primary gaps are: (1) the `DetectRegimeHandler` does not implement 3-day confirmation logic -- it creates each detection as a standalone entity with `confirmed_days=0`; (2) `RegimeChangedEvent` is never published to the `SyncEventBus`; (3) the scoring context has a `RegimeWeightAdjuster` Protocol and `NoOpRegimeAdjuster` placeholder but no real implementation that subscribes to regime events; (4) the CLI `regime` command uses the legacy `core/regime/classifier.py` path instead of the DDD handler; (5) there is no `--history` flag on the CLI regime command.

A secondary gap is that ADX data is NOT collected by the `RegimeDataClient` -- it only fetches VIX, S&P500, and yield curve. The DDD `RegimeDetectionService` requires ADX as input, but the data pipeline does not supply it. The solution is to compute ADX from S&P500 OHLCV data (already fetched) using the existing `core/data/indicators.adx()` function, or to pass a market-level ADX value.

**Primary recommendation:** Wire existing domain code end-to-end through the DDD handler, implement confirmation logic in the handler (not domain), subscribe scoring to RegimeChangedEvent in bootstrap, and rewire CLI through the DDD path -- following the exact same pattern used in Phase 7 for CLI score rewiring.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REGIME-01 | VIX/S&P500/ADX/yield curve data-based regime detection wiring | Handler needs data fetching + ADX computation; RegimeDataClient + compute_all provides all inputs |
| REGIME-02 | 3-day confirmation logic wiring (existing `MarketRegime.is_confirmed`) | Handler must track previous regime via `find_latest()`, increment `confirmed_days`, suppress premature flips |
| REGIME-03 | RegimeChangedEvent EventBus publishing | Handler must call `regime.pull_domain_events()` then `bus.publish()` -- entity already produces events on `transition_to()` |
| REGIME-04 | Regime-based scoring weight automatic adjustment (Bull/Bear/Sideways/Crisis) | Implement `RegimeWeightAdjuster` Protocol concretely, subscribe to `RegimeChangedEvent` in bootstrap, wire into `CompositeScoringService` |
| REGIME-05 | CLI current regime + 90-day history display | Rewire CLI `regime` command through DDD handler, add `--history N` flag using `IRegimeRepository.find_by_date_range()` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib dataclasses | 3.12 | Domain entities, value objects, commands | Already used throughout DDD layers |
| SQLite (via sqlite3) | stdlib | Regime persistence | Already wired via SqliteRegimeRepository |
| Typer | installed | CLI commands | Project CLI framework |
| Rich | installed | CLI output formatting | Project output framework |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | installed | Regime data fetching (VIX, S&P500, yields) | Already used by RegimeDataClient |
| pandas | installed | ADX computation from S&P500 OHLCV | Needed to compute ADX from market data |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Rule-based regime detection | HMM (hmmlearn) | Deferred to ADV-01 (v1.2+), rule-based is project requirement for v1.1 |
| SQLite regime store | DuckDB regime_data | DuckDB stores raw data; SQLite stores detected regime results -- both needed |

**Installation:**
No new packages needed. All dependencies are already installed.

## Architecture Patterns

### Current Code Map (What Exists)

```
src/regime/
  domain/
    entities.py          # MarketRegime aggregate (confirmed_days, transition_to)
    value_objects.py     # RegimeType, VIXLevel, TrendStrength, YieldCurve, SP500Position
    events.py            # RegimeChangedEvent (frozen dataclass)
    services.py          # RegimeDetectionService.detect() -> (RegimeType, float)
    repositories.py      # IRegimeRepository ABC (save, find_latest, find_by_date_range)
    __init__.py          # Public API
  application/
    commands.py          # DetectRegimeCommand, GetRegimeQuery
    handlers.py          # DetectRegimeHandler (creates entity, saves, returns Ok)
    __init__.py
  infrastructure/
    sqlite_repo.py       # SqliteRegimeRepository (full CRUD)
    __init__.py

src/data_ingest/infrastructure/
    regime_data_client.py    # RegimeDataClient (VIX, S&P500, yields -- NO ADX)
    duckdb_store.py          # DuckDB regime_data table (raw time series)

src/scoring/domain/
    services.py              # RegimeWeightAdjuster Protocol + NoOpRegimeAdjuster
    value_objects.py         # STRATEGY_WEIGHTS dict (swing/position)

core/regime/
    classifier.py            # Legacy classify() function (5 regimes, different names)
    weights.py               # REGIME_WEIGHTS (4 strategies), RISK_ADJUSTMENT

cli/main.py                  # regime command uses legacy core/regime/ path
src/bootstrap.py             # RegimeChangedEvent subscription commented out
```

### Gap Analysis (What Must Be Built)

```
REGIME-01: Handler data fetching
  GAP: DetectRegimeHandler receives raw floats but doesn't fetch them
  FIX: Either (a) add data-fetching fallback in handler (Phase 7 pattern),
       or (b) create a RegimeDataAdapter in infrastructure
  ADX GAP: RegimeDataClient has no ADX -- compute from S&P500 OHLCV

REGIME-02: 3-day confirmation
  GAP: Handler creates new entity each time, never checks previous regime
  FIX: Handler calls find_latest(), compares regime_type, increments
       confirmed_days or resets. Only publish event when is_confirmed.

REGIME-03: EventBus publishing
  GAP: Handler never calls pull_domain_events() or bus.publish()
  FIX: Inject bus into handler, after save() call
       regime.pull_domain_events() and bus.publish() each event

REGIME-04: Scoring weight adjustment
  GAP: NoOpRegimeAdjuster always returns default weights
  FIX: Implement concrete RegimeWeightAdjuster that maps 4 DDD regimes
       to weight adjustments, subscribe to RegimeChangedEvent in bootstrap

REGIME-05: CLI rewiring
  GAP: CLI regime command imports from core/regime/ not DDD handler
  FIX: Rewire through _get_ctx()["regime_handler"] (Phase 7 score pattern)
  ADD: --history N flag using find_by_date_range()
```

### Pattern 1: Handler Data-Fetching Fallback (from Phase 7)
**What:** Handler accepts injected data clients but falls back to direct import when none provided
**When to use:** When wiring data into DDD handlers without full infrastructure refactor
**Example:**
```python
# Source: src/scoring/application/handlers.py (Phase 7 pattern)
class DetectRegimeHandler:
    def __init__(self, regime_repo, bus=None, data_client=None):
        self._regime_repo = regime_repo
        self._bus = bus
        self._data_client = data_client
        self._detector = RegimeDetectionService()

    def _fetch_regime_data(self) -> dict:
        if self._data_client:
            return self._data_client.fetch()
        # Fallback: direct import (same pattern as ScoreSymbolHandler)
        from src.data_ingest.infrastructure.regime_data_client import RegimeDataClient
        client = RegimeDataClient()
        return client.fetch_regime_snapshot()
```

### Pattern 2: Confirmation State Machine in Handler
**What:** Handler tracks regime transition state by comparing with latest saved regime
**When to use:** 3-day confirmation requirement (REGIME-02)
**Example:**
```python
def handle(self, cmd: DetectRegimeCommand) -> Result:
    # Detect new regime
    regime_type, confidence = self._detector.detect(vix, sp500, trend, yc)

    # Load previous regime for confirmation tracking
    previous = self._regime_repo.find_latest()

    if previous and previous.regime_type == regime_type:
        # Same regime -- increment confirmed_days
        confirmed_days = previous.confirmed_days + 1
    else:
        # Different regime -- reset counter
        confirmed_days = 1

    regime = MarketRegime(
        _id=str(uuid.uuid4()),
        regime_type=regime_type,
        confidence=confidence,
        vix=vix, trend=trend, yield_curve=yc, sp500=sp500,
        confirmed_days=confirmed_days,
    )

    # Only publish event when confirmed AND regime actually changed
    if regime.is_confirmed and (not previous or previous.regime_type != regime_type):
        event = RegimeChangedEvent(
            previous_regime=previous.regime_type if previous else regime_type,
            new_regime=regime_type,
            confidence=confidence,
            vix_value=cmd.vix,
            adx_value=cmd.adx,
        )
        if self._bus:
            self._bus.publish(event)

    self._regime_repo.save(regime)
    return Ok({...})
```

### Pattern 3: Cross-Context EventBus Subscription (from bootstrap.py)
**What:** Subscribe scoring handler to RegimeChangedEvent in bootstrap
**When to use:** REGIME-03 + REGIME-04
**Example:**
```python
# In bootstrap.py
from src.regime.domain.events import RegimeChangedEvent

bus.subscribe(RegimeChangedEvent, score_handler.on_regime_changed)
# or
bus.subscribe(RegimeChangedEvent, regime_weight_adjuster.on_regime_changed)
```

### Anti-Patterns to Avoid
- **DO NOT create a new RegimeType enum with different values:** The DDD layer uses `Bull/Bear/Sideways/Crisis` (4 types). The legacy `core/regime/` uses `Low-Vol Bull/High-Vol Bull/Low-Vol Range/High-Vol Bear/Transition` (5 types). Keep the DDD enum as canonical. Map legacy names in CLI display if needed.
- **DO NOT put confirmation logic in the domain service:** The domain service is pure detection (stateless). Confirmation requires reading previous state from repo -- that belongs in the handler (application layer).
- **DO NOT fetch ADX from per-ticker indicators:** ADX for regime detection should be market-level (computed from S&P500 OHLCV), not stock-specific.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ADX computation | Custom ADX calculation | `core.data.indicators.adx(df, 14)` | Already battle-tested, used in Phase 7 |
| Event publishing pattern | Custom event dispatch | `SyncEventBus.publish()` + `Entity.pull_domain_events()` | Established Phase 5 infrastructure |
| Regime persistence | New database schema | `SqliteRegimeRepository` (already has confirmed_days column) | Complete implementation exists |
| Yield curve data | Custom FRED API client | `RegimeDataClient.fetch_regime_snapshot()` | Phase 6 implementation complete |

**Key insight:** Nearly all building blocks exist. This phase is integration/wiring, not library development.

## Common Pitfalls

### Pitfall 1: ADX Data Source Gap
**What goes wrong:** RegimeDataClient returns VIX, S&P500, yield data but NOT ADX. The DDD DetectRegimeCommand requires ADX. Calling `handle()` without ADX fails.
**Why it happens:** Phase 6 data pipeline focused on macro indicators; ADX requires OHLCV computation.
**How to avoid:** Compute ADX from S&P500 OHLCV in the handler's data-fetching fallback. `RegimeDataClient` already fetches S&P500 history with `yf.Ticker("^GSPC").history()` -- extend the snapshot method to also compute ADX from that OHLCV, or compute it separately in the handler.
**Warning signs:** `DetectRegimeCommand` requires `adx: float` but no data source provides it.

### Pitfall 2: Regime Name Mismatch Between Legacy and DDD
**What goes wrong:** Legacy `core/regime/classifier.py` uses 5 regime names: `Low-Vol Bull, High-Vol Bull, Low-Vol Range, High-Vol Bear, Transition`. DDD uses 4: `Bull, Bear, Sideways, Crisis`. Other CLI commands (`signal`, `analyze`, `score`) still reference legacy regime names.
**Why it happens:** DDD regime was designed with simplified academic model; legacy was designed for practitioner nuance.
**How to avoid:** Keep DDD `RegimeType` as the canonical enum. The CLI regime command should display DDD types. Other CLI commands that still use legacy regime detection (signal, analyze) are out of scope for Phase 8 -- they will be migrated in Phase 9 (signals).
**Warning signs:** Tests comparing regime names across old and new code will fail if mixing conventions.

### Pitfall 3: Confirmation Counter Reset on Application Restart
**What goes wrong:** If `confirmed_days` is only tracked in memory, restarting the CLI resets the counter and the system may flip regimes prematurely.
**Why it happens:** `confirmed_days` must be persisted in SQLite.
**How to avoid:** The `SqliteRegimeRepository` already has a `confirmed_days` column. Always load `find_latest()` from DB, increment, and save back. The counter survives restarts.
**Warning signs:** Test with multiple `handle()` calls in sequence -- ensure confirmed_days increments across calls.

### Pitfall 4: Event Published Before Confirmation
**What goes wrong:** `MarketRegime.transition_to()` produces `RegimeChangedEvent` immediately on regime change, but the event should only fire after 3-day confirmation.
**Why it happens:** The entity's `transition_to()` method unconditionally adds the event.
**How to avoid:** Do NOT use `transition_to()` for the confirmation flow. Instead, construct the new `MarketRegime` directly in the handler and manually create + publish the event only when `is_confirmed` is true AND the regime is different from the previously confirmed regime.
**Warning signs:** Scoring weights changing on day 1 of a new regime before 3-day confirmation.

### Pitfall 5: Missing Bus Injection in Bootstrap
**What goes wrong:** `DetectRegimeHandler` currently only takes `regime_repo` in `__init__`. Adding bus injection requires updating `bootstrap.py` wiring.
**Why it happens:** Handler was originally built without event publishing (deferred).
**How to avoid:** Add `bus` parameter to `DetectRegimeHandler.__init__()`, update `bootstrap.py` to pass the bus, update any tests that instantiate the handler directly.
**Warning signs:** Tests that mock the handler without providing a bus will break.

## Code Examples

### Example 1: Regime Weight Adjustment Mapping
```python
# Source: project domain rules (DOMAIN.md + strategy-recommendation.md)
# These are the DDD regime types (4) mapped to 3-axis scoring weights
REGIME_SCORING_WEIGHTS: dict[str, dict[str, float]] = {
    # Bull: standard weights (trust the trend)
    "Bull": {"fundamental": 0.35, "technical": 0.45, "sentiment": 0.20},
    # Bear: favor fundamentals (quality/safety), reduce technical
    "Bear": {"fundamental": 0.55, "technical": 0.25, "sentiment": 0.20},
    # Sideways: balanced, slight fundamental tilt
    "Sideways": {"fundamental": 0.45, "technical": 0.35, "sentiment": 0.20},
    # Crisis: maximum defensive (fundamentals dominate)
    "Crisis": {"fundamental": 0.60, "technical": 0.15, "sentiment": 0.25},
}
```

### Example 2: CLI Regime History Table
```python
# Pattern from cli/main.py (Phase 7 style)
@app.command()
def regime(
    history: int = typer.Option(0, "--history", help="Show N days of regime history"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    ctx = _get_ctx()
    handler = ctx["regime_handler"]

    if history > 0:
        # History mode: query date range from SQLite
        from datetime import datetime, timedelta, timezone
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=history)
        regimes = handler.query_history(start, end)
        # Display table with transitions, dates, durations
    else:
        # Current regime detection
        result = handler.handle(cmd)
```

### Example 3: Bootstrap EventBus Wiring
```python
# Source: src/bootstrap.py pattern
from src.regime.domain.events import RegimeChangedEvent

# Wire regime handler with bus
regime_handler = DetectRegimeHandler(regime_repo=regime_repo, bus=bus)

# Subscribe scoring context to regime events
def on_regime_changed(event: RegimeChangedEvent) -> None:
    # Update the regime adjuster's cached regime
    regime_adjuster.update_regime(event.new_regime.value)

bus.subscribe(RegimeChangedEvent, on_regime_changed)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy `core/regime/classifier.py` (5 regimes) | DDD `src/regime/domain/services.py` (4 regimes) | Phase 5 (DDD migration) | CLI still uses legacy; must rewire |
| CLI regime uses `core/data/market.py` | Should use `RegimeDataClient` | Phase 6 added RegimeDataClient | Data source consolidation |
| `NoOpRegimeAdjuster` placeholder | Concrete implementation needed | Phase 8 | Scoring weights will actually shift |
| RegimeChangedEvent commented in bootstrap | Must be activated | Phase 8 | Cross-context communication live |

**Deprecated/outdated:**
- `core/regime/classifier.py` 5-regime model: superseded by DDD 4-regime model in `src/regime/domain/services.py`
- `core/data/market.py` regime data functions: superseded by `RegimeDataClient` in Phase 6
- `NoOpRegimeAdjuster`: will be replaced by concrete implementation

## Open Questions

1. **Regime weight values for scoring (REGIME-04)**
   - What we know: The `STRATEGY_WEIGHTS` dict has `swing` and `position` strategies with `fundamental/technical/sentiment` weights. The legacy `REGIME_WEIGHTS` in `core/regime/weights.py` maps to 4 *signal strategy* weights (canslim/magic/momentum/trend) -- a different axis entirely.
   - What's unclear: The exact `fundamental/technical/sentiment` weight shift per regime. No existing code defines this mapping.
   - Recommendation: Use the pattern from the strategy recommendation doc: Bull = trust technical (45%), Bear = favor fundamentals (55%), Crisis = maximum defensive (60% fundamental). These are reasonable defaults that can be tuned later.

2. **ADX computation for market-level regime**
   - What we know: S&P500 OHLCV is already fetched by `RegimeDataClient`. `core/data/indicators.adx()` computes ADX from OHLCV DataFrame.
   - What's unclear: Whether to add ADX to `RegimeDataClient.fetch_regime_snapshot()` or compute it in the handler.
   - Recommendation: Extend `RegimeDataClient.fetch_regime_snapshot()` to also compute and return ADX from S&P500 OHLCV. This keeps data fetching in one place (infrastructure), handler stays focused on orchestration.

3. **How to handle "current regime" when DB is empty (first run)**
   - What we know: `find_latest()` returns `None` when no regime has been saved yet.
   - What's unclear: Should first detection count as confirmed (start fresh) or require 3 days?
   - Recommendation: First detection starts with `confirmed_days=1`. System returns the detected regime but marks it as "unconfirmed". After 3 consecutive days of the same regime, it becomes confirmed and fires the event.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ with pytest-asyncio |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd /home/mqz/workspace/trading && python -m pytest tests/unit/test_regime_classifier.py -x` |
| Full suite command | `cd /home/mqz/workspace/trading && python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REGIME-01 | Handler fetches data and creates regime entity | unit | `pytest tests/unit/test_regime_handler_wiring.py -x` | No -- Wave 0 |
| REGIME-02 | 3-day confirmation increments/resets, premature flip suppressed | unit | `pytest tests/unit/test_regime_confirmation.py -x` | No -- Wave 0 |
| REGIME-03 | RegimeChangedEvent published to bus on confirmed transition | unit | `pytest tests/unit/test_regime_event_publish.py -x` | No -- Wave 0 |
| REGIME-04 | Scoring weights shift when regime changes | unit | `pytest tests/unit/test_regime_weight_adjustment.py -x` | No -- Wave 0 |
| REGIME-05 | CLI regime shows current + history | unit | `pytest tests/unit/test_cli_regime_ddd.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/unit/test_regime_handler_wiring.py tests/unit/test_regime_confirmation.py tests/unit/test_regime_event_publish.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_regime_handler_wiring.py` -- covers REGIME-01 (handler data fetch + detect)
- [ ] `tests/unit/test_regime_confirmation.py` -- covers REGIME-02 (3-day confirmation state machine)
- [ ] `tests/unit/test_regime_event_publish.py` -- covers REGIME-03 (EventBus publish on confirmed transition)
- [ ] `tests/unit/test_regime_weight_adjustment.py` -- covers REGIME-04 (concrete RegimeWeightAdjuster)
- [ ] `tests/unit/test_cli_regime_ddd.py` -- covers REGIME-05 (CLI rewiring + history flag)

## Sources

### Primary (HIGH confidence)
- `src/regime/domain/` -- All domain layer code (entities, VOs, events, services, repo interface) read directly
- `src/regime/application/handlers.py` -- Current handler implementation gaps verified
- `src/regime/infrastructure/sqlite_repo.py` -- Confirmed confirmed_days column exists
- `src/bootstrap.py` -- Confirmed RegimeChangedEvent subscription is commented out (line 114)
- `src/scoring/domain/services.py` -- Confirmed RegimeWeightAdjuster Protocol and NoOpRegimeAdjuster
- `src/data_ingest/infrastructure/regime_data_client.py` -- Confirmed no ADX in output
- `cli/main.py` -- Confirmed legacy core/regime/ imports in regime command
- `core/regime/classifier.py` -- Confirmed 5-regime naming convention difference
- `core/regime/weights.py` -- Confirmed signal strategy weights (different axis from scoring weights)

### Secondary (MEDIUM confidence)
- `core/regime/DOMAIN.md` -- Domain rules (Bull/Bear/Sideways/Crisis criteria, 3-day confirmation)
- `.claude/skills/regime-detect/regime-rules.md` -- Skill rules reference (5-day confirmation mentioned -- contradicts DOMAIN.md 3-day rule; DOMAIN.md is authoritative)

### Tertiary (LOW confidence)
- Regime weight adjustment values (fundamental/technical/sentiment per regime) -- No existing code defines these. Proposed values are reasonable estimates based on project strategy docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, no new deps
- Architecture: HIGH -- all domain code exists, gap analysis based on direct code reading
- Pitfalls: HIGH -- each pitfall verified by reading specific code that exhibits the gap
- Regime weight values: MEDIUM -- proposed from project docs but not yet validated empirically

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable domain, no external dependency changes expected)
