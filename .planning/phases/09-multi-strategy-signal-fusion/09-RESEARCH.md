# Phase 9: Multi-Strategy Signal Fusion - Research

**Researched:** 2026-03-12
**Domain:** Multi-strategy signal fusion -- 4 strategy evaluators + consensus engine + regime-weighted fusion + CLI rewiring through DDD
**Confidence:** HIGH

## Summary

Phase 9 is primarily a **wiring, enhancement, and DDD-path rewiring** phase, not a greenfield build. All four strategy evaluators already exist and are functional in `core/signals/` (CAN SLIM, Magic Formula, Dual Momentum, Trend Following). The `core/signals/consensus.py` already implements 3/4 consensus logic with regime-weighted scoring. The DDD signals bounded context already has a `SignalFusionService` domain service, `MethodologyResult` value objects, `GenerateSignalHandler`, and `CoreSignalAdapter`. The CLI `signal` command exists but routes through the legacy `core/signals/consensus.py` path instead of the DDD handler.

The primary gaps are: (1) The DDD `GenerateSignalHandler` does not integrate regime-aware strategy weights -- the `SignalFusionService.fuse()` method uses uniform weighting for methodology results and does not adjust based on market regime; (2) The CLI `signal` command bypasses the DDD handler entirely, going through `core/signals/consensus.generate_signals()` and `core/regime/classifier.classify()` instead of `GenerateSignalHandler` and `DetectRegimeHandler`; (3) Strategy-specific reasoning chains lack regime context and per-strategy weight visibility; (4) The regime weight mapping for signal strategies (Bull -> momentum boost, Bear -> quality boost) exists only in `core/regime/weights.py` with 5-string regime names, but the DDD `RegimeType` enum has 4 values (BULL/BEAR/SIDEWAYS/CRISIS); (5) The CAN SLIM evaluator needs the `market_uptrend` parameter to come from the DDD regime system rather than being hardcoded.

**Primary recommendation:** Wire the DDD `GenerateSignalHandler` to receive current regime type (from `DetectRegimeHandler` or cached `ConcreteRegimeWeightAdjuster`) and apply regime-specific strategy weights in `SignalFusionService.fuse()`. Create a DDD-native `SIGNAL_STRATEGY_WEIGHTS` mapping using 4-enum `RegimeType` values (not the legacy 5-string names). Rewire the CLI `signal` command through the DDD handler path, following the exact Phase 7 pattern used for `score` command rewiring. Add regime-adjusted weights and per-strategy reasoning to the output.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SIGNAL-01 | CAN SLIM 7-criteria scoring | `core/signals/canslim.py` already implements all 7 criteria. `CoreSignalAdapter.evaluate_canslim()` wraps it. Needs `market_uptrend` from DDD regime instead of hardcoded value. |
| SIGNAL-02 | Magic Formula (Earnings Yield + ROC) ranking | `core/signals/magic_formula.py` already implements EY + ROC percentile ranking. `CoreSignalAdapter.evaluate_magic_formula()` wraps it. Functional as-is. |
| SIGNAL-03 | Dual Momentum (absolute + relative) signal | `core/signals/dual_momentum.py` already implements Antonacci dual momentum. `CoreSignalAdapter.evaluate_dual_momentum()` wraps it. Functional as-is. |
| SIGNAL-04 | Trend Following (20/55d high breakout + ADX) | `core/signals/trend_following.py` already implements MA cross + ADX + breakout. `CoreSignalAdapter.evaluate_trend_following()` wraps it. Minor: requirement says "20/55-day high" but current impl uses 20-day only. |
| SIGNAL-05 | 4-strategy consensus signal (3/4 agreement = strong) | `SignalFusionService.fuse()` already implements 3/4 consensus. `GenerateSignalHandler` orchestrates it. Needs to flow through DDD path end-to-end. |
| SIGNAL-06 | Regime-weighted strategy fusion (Bull->momentum, Bear->quality) | GAP: `SignalFusionService` does NOT apply regime weights to methodology results. `core/regime/weights.py` has per-strategy weights but uses incompatible 5-string regime names. Must create DDD-native regime-strategy weights and wire through handler. |
| SIGNAL-07 | Per-strategy reasoning chain output | `GenerateSignalHandler._build_reasoning_trace()` exists but lacks regime context, per-strategy weights, and regime-adjusted explanation. CLI `signal` command does not show reasoning. Must enhance both. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib dataclasses | 3.12 | Domain VOs, commands, events | Already used throughout DDD layers |
| SQLite (via sqlite3) | stdlib | Signal persistence | Already wired via SqliteSignalRepository |
| Typer | installed | CLI commands | Project CLI framework |
| Rich | installed | CLI output (Panel, Table) | Project output framework |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | installed | Market data for strategy evaluation | Already used by DataClient and CoreSignalAdapter |
| pandas | installed | Price history for indicator computation | Already used by core/data modules |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fixed 4 strategy weights | ML-optimized weights (Optuna) | Deferred: out of scope per requirements (ML optimization = overfitting risk) |
| Rule-based consensus (3/4) | Bayesian signal combination | Deferred: adds complexity without clear benefit for v1.1 |
| `core/regime/weights.py` 5-regime mapping | New DDD 4-regime mapping | Use new DDD mapping; 5-regime is legacy -- do not propagate |

**Installation:**
No new packages needed. All dependencies already installed.

## Architecture Patterns

### Current DDD Structure (signals context)
```
src/signals/
  domain/
    __init__.py          # Public API (already exports all needed types)
    value_objects.py     # SignalDirection, MethodologyType, MethodologyResult, ConsensusThreshold, SignalStrength
    services.py          # SignalFusionService (needs regime weight enhancement)
    repositories.py      # ISignalRepository
    events.py            # SignalGeneratedEvent
  application/
    __init__.py
    commands.py          # GenerateSignalCommand (needs regime_type field)
    handlers.py          # GenerateSignalHandler (needs regime integration)
    queries.py           # GetActiveSignalQuery, GetSignalHistoryQuery
  infrastructure/
    __init__.py
    core_signal_adapter.py  # CoreSignalAdapter (wraps core/signals/ evaluators)
    sqlite_repo.py         # SqliteSignalRepository
    in_memory_repo.py      # InMemorySignalRepository (testing)
    duckdb_signal_store.py # DuckDBSignalStore (screener)
```

### Pattern 1: Regime-Weighted Signal Fusion (New)
**What:** Extend `SignalFusionService` to accept regime type and apply per-strategy weights.
**When to use:** Every signal generation call must be regime-aware.
**Example:**
```python
# In src/signals/domain/services.py

# DDD-native regime-strategy weights (4-enum, NOT legacy 5-string)
SIGNAL_STRATEGY_WEIGHTS: dict[str, dict[str, float]] = {
    "Bull":     {"CAN_SLIM": 0.20, "MAGIC_FORMULA": 0.20, "DUAL_MOMENTUM": 0.30, "TREND_FOLLOWING": 0.30},
    "Bear":     {"CAN_SLIM": 0.15, "MAGIC_FORMULA": 0.35, "DUAL_MOMENTUM": 0.25, "TREND_FOLLOWING": 0.25},
    "Sideways": {"CAN_SLIM": 0.25, "MAGIC_FORMULA": 0.35, "DUAL_MOMENTUM": 0.15, "TREND_FOLLOWING": 0.25},
    "Crisis":   {"CAN_SLIM": 0.10, "MAGIC_FORMULA": 0.40, "DUAL_MOMENTUM": 0.30, "TREND_FOLLOWING": 0.20},
}
DEFAULT_SIGNAL_WEIGHTS: dict[str, float] = {
    "CAN_SLIM": 0.25, "MAGIC_FORMULA": 0.25, "DUAL_MOMENTUM": 0.25, "TREND_FOLLOWING": 0.25,
}

class SignalFusionService:
    def fuse(
        self,
        results: list[MethodologyResult],
        composite_score: float,
        safety_passed: bool,
        threshold: ConsensusThreshold = DEFAULT_THRESHOLD,
        regime_type: str | None = None,  # NEW: "Bull"/"Bear"/"Sideways"/"Crisis"
    ) -> tuple[SignalDirection, SignalStrength]:
        # Apply regime-specific weights for strength computation
        weights = SIGNAL_STRATEGY_WEIGHTS.get(regime_type, DEFAULT_SIGNAL_WEIGHTS) if regime_type else DEFAULT_SIGNAL_WEIGHTS
        # ... existing consensus logic (buy_count >= 3, etc.) stays the same
        # ... _compute_strength uses regime weights instead of uniform averaging
```

### Pattern 2: CLI DDD Rewiring (Phase 7 Pattern)
**What:** Replace legacy `core/signals/consensus.generate_signals()` call with DDD `GenerateSignalHandler.handle()`.
**When to use:** CLI `signal` command.
**Example:**
```python
# In cli/main.py signal command -- follow Phase 7 score command pattern
@app.command()
def signal(symbol: str = typer.Argument(...)):
    ctx = _get_ctx()
    # 1. Get regime from DDD handler
    regime_result = ctx["regime_handler"].handle(DetectRegimeCommand())
    regime_type = regime_result.unwrap()["regime_type"]
    # 2. Get composite score from DDD handler
    score_result = ctx["score_handler"].handle(ScoreSymbolCommand(symbol=symbol))
    # 3. Generate signal through DDD handler
    cmd = GenerateSignalCommand(
        symbol=symbol,
        composite_score=score_result.unwrap()["composite_score"],
        safety_passed=score_result.unwrap()["safety_passed"],
        regime_type=regime_type,  # NEW
        symbol_data=symbol_data,
    )
    result = ctx["signal_handler"].handle(cmd)
```

### Pattern 3: Enhanced Reasoning Trace
**What:** Include regime context, per-strategy weights, and confidence in the reasoning output.
**When to use:** Every signal generation result.
**Example:**
```python
# Enhanced reasoning trace output format
"""
AAPL: BUY
  Regime: Bull (confidence 85%)
  Strategy Weights: CAN SLIM 20%, Magic Formula 20%, Dual Momentum 30%, Trend Following 30%
  Composite Score: 72.0/100
  Safety Gate: PASS
  ---
  CAN SLIM: BUY (score 85.7/100, weight 20%) -- 6/7 criteria met
  Magic Formula: BUY (score 80.0/100, weight 20%) -- Top 20% EY+ROC rank
  Dual Momentum: BUY (score 100.0/100, weight 30%) -- Both relative & absolute pass
  Trend Following: HOLD (score 33.3/100, weight 30%) -- 1/3 criteria met
  ---
  Consensus: 3/4 strategies agree BUY
  Weighted Score: 0.742
"""
```

### Anti-Patterns to Avoid
- **Using legacy 5-string regime names for new code:** The DDD `RegimeType` enum (BULL/BEAR/SIDEWAYS/CRISIS) is the canonical taxonomy. Never use "Low-Vol Bull", "High-Vol Bull" etc. in the DDD signal fusion path. See Pitfall 3 in PITFALLS.md.
- **Modifying core/signals/ evaluators:** These are working implementations. The DDD adapter wraps them. Do not rewrite the math -- enhance the DDD orchestration layer.
- **Adding cross-context domain imports:** Do NOT import `RegimeType` VO in the signals domain. Pass regime as a primitive string through the command/handler boundary (same pattern as `composite_score: float`).
- **Breaking existing test coverage:** 8+ test files cover signals. All must pass before and after changes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Strategy evaluation math | Custom CAN SLIM/Magic Formula/Dual Momentum/Trend Following logic | `CoreSignalAdapter` wrapping `core/signals/*.evaluate()` | Already tested, validated, working |
| Signal consensus logic | Custom voting algorithm | `SignalFusionService.fuse()` (extend, don't replace) | Business rules already encoded, 3/4 threshold is domain invariant |
| Regime detection | New regime classifier in signals context | `DetectRegimeHandler` (already complete from Phase 8) | Regime detection is a separate bounded context |
| Score computation | Custom composite scoring | `ScoreSymbolHandler` (already complete from Phase 7) | Cross-context data flows as primitives via commands |
| CLI rendering | Custom formatting | Rich Table, Panel, color coding | Already established patterns in score/regime commands |

**Key insight:** Almost all the math exists. This phase is about orchestration wiring (getting the right data to the right handler in the right order) and presentation (showing regime-adjusted reasoning in CLI output).

## Common Pitfalls

### Pitfall 1: Regime Name Taxonomy Mismatch
**What goes wrong:** Using `core/regime/weights.py` 5-string names ("Low-Vol Bull") in the DDD signal fusion path causes weight lookups to fall through to defaults.
**Why it happens:** The legacy `core/signals/consensus.py` calls `get_weights(regime)` with 5-string names. Copying this pattern into DDD code where `RegimeType` produces 4-string values ("Bull") silently breaks weighting.
**How to avoid:** Create new `SIGNAL_STRATEGY_WEIGHTS` dict in `src/signals/domain/services.py` keyed by the 4 DDD `RegimeType.value` strings ("Bull", "Bear", "Sideways", "Crisis"). Do not import from `core/regime/weights.py`.
**Warning signs:** All strategies getting equal 0.25 weight regardless of regime.

### Pitfall 2: GenerateSignalCommand Missing Regime Data
**What goes wrong:** `GenerateSignalCommand` currently has no `regime_type` field. Without it, the handler cannot pass regime info to `SignalFusionService.fuse()`.
**Why it happens:** The command was designed before regime integration existed.
**How to avoid:** Add `regime_type: str | None = None` to `GenerateSignalCommand`. This follows the existing pattern of `composite_score: float | None = None` -- optional with fallback.
**Warning signs:** Regime-weighted fusion tests failing because handler has no way to receive regime type.

### Pitfall 3: CLI Signal Command Dual-Path Confusion
**What goes wrong:** The CLI `signal` command at `cli/main.py:261` imports `core/signals/consensus.generate_signals()` and `core/regime/classifier.classify()`. After rewiring to DDD, both paths coexist and produce different results.
**Why it happens:** Phase 7 faced exactly this issue with the `score` command and resolved it by removing the legacy import.
**How to avoid:** Follow Phase 7 pattern: replace the entire CLI signal function body with DDD handler calls. Remove all `from core.signals.*` and `from core.regime.*` imports from the CLI signal command.
**Warning signs:** `import` statements for both `core.signals.consensus` and `src.signals.application.handlers` in the same file.

### Pitfall 4: CAN SLIM market_uptrend Hardcoded
**What goes wrong:** `CoreSignalAdapter.evaluate_all()` passes `market_uptrend=symbol_data.get("market_uptrend", True)` with a `True` default. In Bear regime, this should be `False`, but the caller may forget to set it.
**Why it happens:** The CAN SLIM evaluator requires market regime context ("M" criterion = market in uptrend), but the adapter doesn't know the current regime.
**How to avoid:** In the CLI/handler, derive `market_uptrend` from the current regime type: `True` if regime is Bull, `False` if Bear/Crisis, `True` if Sideways (debatable -- default to True as conservative choice).
**Warning signs:** CAN SLIM always giving market_uptrend = True even in Bear markets.

### Pitfall 5: Score Normalization Inconsistency
**What goes wrong:** Each evaluator returns scores on different scales (CAN SLIM: 0-7, Magic Formula: 0-100, Dual Momentum: 0-2, Trend Following: 0-3). The `_raw_to_methodology_results()` normalizes to 0-100, but `_evaluate_via_clients()` does not normalize consistently.
**Why it happens:** Two code paths (`_evaluate_via_adapter` vs `_evaluate_via_clients`) handle normalization differently.
**How to avoid:** Ensure the adapter path (which does normalize) is the only path used. The client path is legacy fallback.
**Warning signs:** Trend Following score of 2 out of 3 (67%) being compared as "67" against Magic Formula "80" without normalization context.

## Code Examples

### Example 1: Existing SignalFusionService.fuse() (current implementation)
```python
# Source: src/signals/domain/services.py (lines 28-80)
# Current: no regime awareness, uniform strength computation
def fuse(self, results, composite_score, safety_passed, threshold=DEFAULT_THRESHOLD):
    buy_count = sum(1 for r in results if r.direction == SignalDirection.BUY)
    sell_count = sum(1 for r in results if r.direction == SignalDirection.SELL)
    # ... consensus logic uses buy_count/sell_count only
    # ... _compute_strength averages matching methodology scores uniformly
```

### Example 2: Existing CoreSignalAdapter.evaluate_all() (input mapping)
```python
# Source: src/signals/infrastructure/core_signal_adapter.py (lines 36-75)
# Shows exactly which symbol_data keys each evaluator needs
def evaluate_all(self, symbol_data: dict) -> list[dict]:
    canslim = self.evaluate_canslim(
        eps_growth_qoq=symbol_data.get("eps_growth_qoq"),
        eps_cagr_3y=symbol_data.get("eps_cagr_3y"),
        near_52w_high=symbol_data.get("near_52w_high", False),
        volume_ratio=symbol_data.get("volume_ratio", 1.0),
        relative_strength=symbol_data.get("relative_strength", 50),
        institutional_increase=symbol_data.get("institutional_increase", False),
        market_uptrend=symbol_data.get("market_uptrend", True),  # <-- needs regime input
    )
    # ... 3 more evaluators ...
```

### Example 3: CLI Score Command Rewiring Pattern (from Phase 7 -- reference)
```python
# Source: cli/main.py score command (already rewired in Phase 7)
# This pattern should be replicated for the signal command
@app.command()
def score(symbol: str = typer.Argument(...)):
    ctx = _get_ctx()
    cmd = ScoreSymbolCommand(symbol=symbol, strategy=strategy)
    result = ctx["score_handler"].handle(cmd)
    if result.is_err():
        console.print(f"[bold red]Error: {result.unwrap_err()}[/bold red]")
        raise typer.Exit(code=1)
    data = result.unwrap()
    # ... Rich Table rendering ...
```

### Example 4: Regime Weight Mapping (legacy vs DDD)
```python
# LEGACY (core/regime/weights.py) -- DO NOT USE in DDD path
REGIME_WEIGHTS = {
    "Low-Vol Bull":  {"canslim": 0.30, "magic": 0.20, "momentum": 0.25, "trend": 0.25},
    "High-Vol Bull": {"canslim": 0.20, "magic": 0.25, "momentum": 0.25, "trend": 0.30},
    # ... 5 regimes ...
}

# NEW DDD (to be created in src/signals/domain/services.py)
# Uses MethodologyType.value keys and RegimeType.value keys
SIGNAL_STRATEGY_WEIGHTS = {
    "Bull":     {"CAN_SLIM": 0.20, "MAGIC_FORMULA": 0.20, "DUAL_MOMENTUM": 0.30, "TREND_FOLLOWING": 0.30},
    "Bear":     {"CAN_SLIM": 0.15, "MAGIC_FORMULA": 0.35, "DUAL_MOMENTUM": 0.25, "TREND_FOLLOWING": 0.25},
    "Sideways": {"CAN_SLIM": 0.25, "MAGIC_FORMULA": 0.35, "DUAL_MOMENTUM": 0.15, "TREND_FOLLOWING": 0.25},
    "Crisis":   {"CAN_SLIM": 0.10, "MAGIC_FORMULA": 0.40, "DUAL_MOMENTUM": 0.30, "TREND_FOLLOWING": 0.20},
}
```

### Example 5: Expected CLI Signal Output (enhanced)
```python
# Rich Panel output showing full reasoning chain
# Panel title: "Signal Consensus: AAPL"
# Panel subtitle: "Regime: Bull (85% confidence)"
# Body shows direction + agreement + weighted score

# Table columns: Strategy | Signal | Score | Weight | Reasoning
# Row: CAN SLIM | BUY | 85.7 | 20% | 6/7 criteria met (C,A,N,S,L,M)
# Row: Magic Formula | BUY | 80.0 | 20% | Top 20% EY+ROC combined rank
# Row: Dual Momentum | BUY | 100.0 | 30% | Both relative and absolute pass
# Row: Trend Following | HOLD | 33.3 | 30% | 1/3 criteria (MA cross only)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CLI `signal` uses `core/signals/consensus.generate_signals()` | Should use DDD `GenerateSignalHandler` | Phase 9 (this phase) | Consistent DDD path, regime integration |
| `core/regime/weights.py` 5-string regime names | DDD `RegimeType` 4-enum values | Phase 8 (established) | Must use DDD taxonomy in signal weights |
| Uniform strategy weighting in `SignalFusionService` | Regime-weighted strategy fusion | Phase 9 (this phase) | Bull boosts momentum, Bear boosts quality |
| No reasoning chain in CLI signal output | Full reasoning with regime context | Phase 9 (this phase) | Transparency and explainability |

**Deprecated/outdated:**
- `core/signals/consensus.generate_signals()`: Legacy pipeline. Still works but should not be the primary CLI path after this phase.
- `core/regime/classifier.classify()` 5-regime output: Superseded by `DetectRegimeHandler` 4-regime output in Phase 8.
- `core/regime/weights.REGIME_WEIGHTS`: 5-string keyed. Use new DDD-native `SIGNAL_STRATEGY_WEIGHTS` keyed by 4-enum values.

## Open Questions

1. **Trend Following 55-day high parameter**
   - What we know: SIGNAL-04 requirement says "20/55-day high breakout" but `core/signals/trend_following.py` only checks `at_20d_high` (20-day). No 55-day breakout criterion exists.
   - What's unclear: Should 55-day high be added to the evaluator, or is the requirement documentation outdated?
   - Recommendation: Implement as-is with 20-day high (matches existing implementation). Adding 55-day high is a minor enhancement that can be done but needs additional `at_55d_high` data from the data pipeline. Since the requirement text mentions both, consider adding it as a bonus criterion that scores 4 max instead of 3.

2. **Strategy weight rationale (Bull vs Bear)**
   - What we know: Requirements say "Bull -> momentum strategies higher weight, Bear -> quality/value higher weight." CAN SLIM and Magic Formula are quality/value; Dual Momentum and Trend Following are momentum.
   - What's unclear: Exact weight percentages are not specified in requirements.
   - Recommendation: Use the proposed weights in Code Example 4. Bull: momentum (DM+TF) gets 60%, quality (CS+MF) gets 40%. Bear: quality gets 50%, momentum gets 50% but shifted toward DM (defensive). These are reasonable starting points.

3. **EventBus subscription for signal regeneration**
   - What we know: `bootstrap.py` has commented-out subscription `bus.subscribe(ScoreUpdatedEvent, signal_handler.on_score_updated)`.
   - What's unclear: Should Phase 9 activate this cross-context event wiring?
   - Recommendation: Do NOT activate reactive event wiring in Phase 9. Keep signals as an explicit command flow (CLI calls handler). Reactive wiring is a separate concern for the commercial API phase. Phase 9 focus should be on the explicit CLI pipeline.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed) |
| Config file | `pyproject.toml` or implicit pytest discovery |
| Quick run command | `pytest tests/unit/test_signal_engine.py tests/unit/test_signal_consensus.py tests/unit/test_signal_canslim.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIGNAL-01 | CAN SLIM 7-criteria produces BUY/HOLD/SELL | unit | `pytest tests/unit/test_signal_canslim.py -x` | Yes |
| SIGNAL-02 | Magic Formula ranking produces BUY/HOLD/SELL | unit | `pytest tests/unit/test_signal_engine.py::TestCoreSignalAdapter -x` | Yes (partial) |
| SIGNAL-03 | Dual Momentum absolute+relative produces BUY/HOLD/SELL | unit | `pytest tests/unit/test_signal_engine.py::TestCoreSignalAdapter -x` | Yes (partial) |
| SIGNAL-04 | Trend Following MA+ADX+breakout produces BUY/HOLD/SELL | unit | `pytest tests/unit/test_signal_engine.py::TestCoreSignalAdapter -x` | Yes (partial) |
| SIGNAL-05 | 4-strategy consensus 3/4 agreement = strong signal | unit | `pytest tests/unit/test_signal_consensus.py -x` | Yes (core/) |
| SIGNAL-06 | Regime-weighted strategy fusion (Bull->momentum, Bear->quality) | unit | `pytest tests/unit/test_signal_regime_weights.py -x` | No -- Wave 0 |
| SIGNAL-07 | Per-strategy reasoning chain with regime context | unit | `pytest tests/unit/test_signal_reasoning.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_signal_engine.py tests/unit/test_signal_consensus.py tests/unit/test_signal_canslim.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_signal_regime_weights.py` -- covers SIGNAL-06 (regime-weighted fusion)
- [ ] `tests/unit/test_signal_reasoning.py` -- covers SIGNAL-07 (enhanced reasoning trace with regime context)
- [ ] Update `tests/unit/test_signal_engine.py` -- add tests for regime-aware `GenerateSignalHandler` flow (SIGNAL-05 DDD path)
- [ ] Update `tests/unit/test_signal_consensus.py` -- add tests for DDD `SignalFusionService` with regime weights (SIGNAL-05 + SIGNAL-06)

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis of `src/signals/` domain layer (all files read and analyzed)
- Direct codebase analysis of `core/signals/` evaluators (canslim.py, magic_formula.py, dual_momentum.py, trend_following.py, consensus.py)
- Direct codebase analysis of `src/regime/` domain layer (services.py, entities.py, value_objects.py, events.py)
- Direct codebase analysis of `src/scoring/` domain services (CompositeScoringService, RegimeWeightAdjuster pattern)
- Direct codebase analysis of `cli/main.py` signal command (lines 260-332)
- Direct codebase analysis of `src/bootstrap.py` (handler wiring, event subscriptions)
- `.planning/research/PITFALLS.md` (Pitfall 3: regime name incompatibility, Pitfall 8: 4-methodology hardcoding, Pitfall 13: weight constant duplication)

### Secondary (MEDIUM confidence)
- Phase 8 RESEARCH.md pattern for regime integration approach
- Phase 7/8 STATE.md decisions for CLI rewiring pattern and regime weight adjuster pattern

### Tertiary (LOW confidence)
- Exact strategy weight percentages for regime-adjusted fusion (proposed values based on domain logic -- Bull favors momentum, Bear favors quality -- but not empirically validated)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and used
- Architecture: HIGH -- DDD structure fully established, patterns from Phase 7/8 directly applicable
- Pitfalls: HIGH -- all identified from direct codebase analysis and documented PITFALLS.md
- Regime weight values: MEDIUM -- rationale is sound but exact percentages are design choices, not verified against backtest

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable -- no external dependency changes expected)
