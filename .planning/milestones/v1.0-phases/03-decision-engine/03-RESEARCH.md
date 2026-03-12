# Phase 3: Decision Engine - Research

**Researched:** 2026-03-12
**Domain:** Signal generation, position sizing, risk management, walk-forward backtesting
**Confidence:** HIGH

## Summary

Phase 3 wires together the scoring (Phase 1) and valuation (Phase 2) outputs into actionable trading decisions. The implementation landscape is unusual: almost all the math already exists in two parallel codebases. The `core/signals/` directory has working implementations of all four methodology evaluators (CAN SLIM, Magic Formula, Dual Momentum, Trend Following), a consensus engine, and regime-based weighting. The `personal/sizer/` and `personal/risk/` modules contain working Kelly sizing, ATR position sizing, and 3-tier drawdown defense. The `core/backtest/` directory has a complete backtest engine, performance metrics calculator, and walk-forward validation framework. Meanwhile, the DDD `src/` layer already has scaffolded domain VOs, services, events, repos, and application handlers for both `signals/` and `portfolio/` bounded contexts -- but they are wired to fallback stubs rather than the real `core/` and `personal/` implementations.

The primary work in Phase 3 is therefore **integration, not invention**: (1) Create infrastructure adapters that bridge `core/signals/*` and `personal/sizer/kelly` into the DDD `src/signals/` and `src/portfolio/` bounded contexts, following the exact CoreScoringAdapter and CoreValuationAdapter patterns from Phases 1-2. (2) Implement the signal decision service that combines quality score + valuation gap into BUY/HOLD/SELL with reasoning traces. (3) Add the screener/ranker that queries DuckDB for Top N stocks. (4) Wire the backtest bounded context as a new DDD context (`src/backtest/`) wrapping `core/backtest/`. (5) Add take-profit levels derived from intrinsic value targets. (6) Connect regime detection to the existing `RegimeWeightAdjuster` Protocol left open in Phase 2.

**Primary recommendation:** Follow the adapter-only pattern: never rewrite math from `core/` or `personal/` -- only wrap it through DDD infrastructure adapters. The `src/signals/` and `src/portfolio/` bounded contexts already have the correct domain models. Focus on: (a) creating adapter classes, (b) enriching the signal generation handler with valuation-aware reasoning, (c) adding screener query capability, (d) creating `src/backtest/` bounded context, and (e) connecting profit targets to valuation outputs.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SIGN-01 | BUY/HOLD/SELL signal combining quality score + valuation gap, with reasoning trace | Existing `SignalFusionService.fuse()` handles methodology consensus. Need: (1) adapter wrapping `core/signals/*.evaluate()`, (2) valuation gap integration into decision logic, (3) reasoning trace builder citing composite score, MoS, methodology agreements. All VOs exist (`SignalDirection`, `MethodologyResult`, `SignalStrength`). |
| SIGN-02 | Screener/Ranker -- Top N by composite score, filtered by signal | Need screener query service that reads DuckDB scoring + valuation data, ranks by `CompositeScore.risk_adjusted`, filters by signal direction and MoS threshold. `DuckDBStore` patterns from Phase 1 available for reference. |
| RISK-01 | Fractional Kelly (1/4) position sizing | `PortfolioRiskService.compute_kelly_size()` already implements this correctly in domain. `personal/sizer/kelly.kelly_fraction()` also exists in core. Infrastructure adapter bridges the two. The `KellyFraction` VO enforces 0.25 fraction invariant. |
| RISK-02 | ATR-based stop-loss at 2.5-3.5x ATR(21) | `PortfolioRiskService.compute_atr_stop()` and `ATRStop` VO already implement this in domain. `personal/sizer/kelly.atr_position_size()` exists in core. Need adapter + ATR(21) data flow from price data. |
| RISK-03 | Take-profit levels from intrinsic value targets | New domain logic needed: take-profit = intrinsic value from ensemble valuation, partial exit levels at 50%/75%/100% of gap between entry and intrinsic. Connects to `MarginOfSafety.intrinsic_mid` from valuation context via domain events. |
| RISK-04 | Drawdown defense at 10%/15%/20% tiers | `Portfolio.drawdown_level` and `PortfolioRiskService.assess_drawdown_defense()` already implement all three tiers. `personal/risk/drawdown.assess_drawdown()` exists in core. Need adapter + integration into position opening flow. Already wired in `PortfolioManagerHandler.open_position()`. |
| RISK-05 | Max 8% per position, 25% per sector hard limits | `Portfolio.can_open_position()` enforces 8% single position limit. `PortfolioWeight`/`SectorWeight` VOs validate ranges. `personal/sizer/kelly.validate_position()` also validates. Need sector aggregation query from portfolio state. |
| BACK-01 | Walk-forward validation with Sharpe t-stat > 2, PBO < 10% targets | `core/backtest/walk_forward.run_walk_forward()` already implements rolling IS/OOS splits. `WalkForwardResult` has `overfitting_score`. Need: DDD adapter, profit factor metric addition, Sharpe t-stat calculation, PBO (Probability of Backtest Overfitting) computation. |
| BACK-02 | Performance report with Sharpe, max drawdown, win rate, profit factor | `core/backtest/metrics.PerformanceMetrics` already has Sharpe, max drawdown, win rate, CAGR, num trades, avg return. Need: profit factor addition (gross_profit / gross_loss), report formatting service. |
</phase_requirements>

## Standard Stack

### Core (already installed -- no new dependencies needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | >=2.0 | Data manipulation, equity curves, signal series | Walk-forward backtest requires DataFrame operations. Already in use. |
| numpy | >=1.26 | Numerical computation for metrics | Sharpe ratio, statistical calculations. Already in use. |
| duckdb | >=1.0 | Screener queries across 900+ tickers | Columnar analytics for Top N ranking. Already in use. |
| pytest | >=7.4 | Test framework | Configured with asyncio_mode="auto". Already in use. |

### Supporting (already installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy | (in ml extras) | Sharpe t-stat calculation | `scipy.stats.t.ppf` for t-statistic, only if `n_splits` significance testing needed. |

### No New Dependencies Required
All Phase 3 work wraps existing `core/` and `personal/` implementations through DDD adapters. The signal evaluation, Kelly sizing, ATR stops, drawdown defense, backtest engine, walk-forward, and metrics are all already implemented and tested. The only new logic is: reasoning trace generation (string building), screener queries (DuckDB SQL), take-profit calculation (arithmetic), and profit factor (sum division).

## Architecture Patterns

### Existing Bounded Contexts to Extend
```
src/
  signals/            # EXTEND: add adapters for core/signals/* evaluators
    domain/           # EXISTING: VOs, services, events, repos -- mostly complete
    application/      # EXISTING: commands, handlers, queries -- needs valuation integration
    infrastructure/   # EXTEND: add CoreSignalAdapter wrapping core/signals/*
  portfolio/          # EXTEND: add adapters for personal/sizer/ and personal/risk/
    domain/           # EXISTING: aggregates, entities, VOs, services, repos -- complete
    application/      # EXISTING: handlers, commands -- needs take-profit + screener
    infrastructure/   # EXTEND: add CoreRiskAdapter wrapping personal/*
```

### New Bounded Context
```
src/
  backtest/           # NEW: walk-forward validation DDD context
    domain/
      value_objects.py  # BacktestConfig, PerformanceReport, WalkForwardConfig
      services.py       # BacktestValidationService (pure domain logic)
      events.py         # BacktestCompletedEvent
      repositories.py   # IBacktestResultRepository
      __init__.py
    application/
      commands.py       # RunBacktestCommand, RunWalkForwardCommand
      handlers.py       # BacktestHandler orchestrates adapter calls
      __init__.py
    infrastructure/
      core_backtest_adapter.py  # Wraps core/backtest/* (engine, walk_forward, metrics)
      duckdb_backtest_store.py  # Stores backtest results for comparison
      __init__.py
    DOMAIN.md
```

### Pattern 1: Infrastructure Adapter (established in Phases 1-2)
**What:** Wrap existing `core/` and `personal/` pure math functions behind a class that the DDD application layer calls through dependency injection.
**When to use:** Every time Phase 3 needs computation already in `core/` or `personal/`.
**Example:**
```python
# src/signals/infrastructure/core_signal_adapter.py
from core.signals.canslim import evaluate as canslim_evaluate
from core.signals.magic_formula import evaluate as magic_evaluate
from core.signals.dual_momentum import evaluate as dual_evaluate
from core.signals.trend_following import evaluate as trend_evaluate
from core.signals.consensus import compute_consensus
from core.regime.classifier import classify as classify_regime
from core.regime.weights import get_weights, get_risk_adjustment

class CoreSignalAdapter:
    """Wraps core/signals/ evaluators for DDD signals context."""

    def evaluate_canslim(self, **kwargs) -> dict:
        return canslim_evaluate(**kwargs)

    def evaluate_magic_formula(self, **kwargs) -> dict:
        return magic_evaluate(**kwargs)

    def evaluate_dual_momentum(self, **kwargs) -> dict:
        return dual_evaluate(**kwargs)

    def evaluate_trend_following(self, **kwargs) -> dict:
        return trend_evaluate(**kwargs)

    def compute_consensus(self, results: list[dict], regime: str) -> dict:
        return compute_consensus(*results, regime=regime)

    def classify_regime(self, vix, sp500_vs_200ma, adx, yield_curve_bps) -> dict:
        return classify_regime(vix, sp500_vs_200ma, adx, yield_curve_bps)
```

### Pattern 2: Cross-Context Communication via Events
**What:** Signals context needs scoring and valuation data from other bounded contexts. Use domain events or query interfaces, never direct cross-context imports.
**When to use:** When signal generation needs CompositeScore or MarginOfSafety.
**How:** Signal handler receives scoring/valuation results as input parameters (passed in from orchestration layer or CLI), not by importing scoring/valuation modules directly.

### Pattern 3: Reasoning Trace Builder
**What:** Each signal decision must include a plain-text reasoning trace citing specific data points.
**When to use:** SIGN-01 requirement for explainability.
**Example:**
```python
def build_reasoning(
    symbol: str,
    direction: str,
    composite_score: float,
    margin_of_safety: float,
    methodology_results: dict,
    safety_passed: bool,
) -> str:
    """Build human-readable reasoning trace."""
    lines = [f"{symbol}: {direction}"]
    lines.append(f"  Composite Score: {composite_score:.1f}/100")
    lines.append(f"  Margin of Safety: {margin_of_safety:.1%}")
    lines.append(f"  Safety Gate: {'PASS' if safety_passed else 'FAIL'}")
    for method, data in methodology_results.items():
        lines.append(
            f"  {method}: {data['signal']} "
            f"(score {data['score']}/{data['score_max']})"
        )
    return "\n".join(lines)
```

### Anti-Patterns to Avoid
- **Rewriting core math:** Never reimplement Kelly, ATR, backtest engine, or signal evaluators in `src/` domain. Wrap through adapters only.
- **Cross-context imports:** Never `from src.scoring.domain import CompositeScore` inside `src/signals/`. Pass data as primitives (floats, dicts) through handler parameters.
- **Mutable domain objects for risk state:** The Portfolio aggregate tracks drawdown via `peak_value` mutation. This is the ONE allowed mutation pattern -- all other VOs remain frozen.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Kelly position sizing math | Custom Kelly formula | `personal/sizer/kelly.kelly_fraction()` | Already validated with tests; edge cases handled (zero inputs, max cap) |
| ATR position sizing | Custom ATR sizing | `personal/sizer/kelly.atr_position_size()` | ATR multiplier clamping, max position cap, risk-per-trade calc all done |
| Drawdown defense logic | Custom 3-tier system | `personal/risk/drawdown.assess_drawdown()` | Tier thresholds, cooldown state, boundary conditions all tested |
| Backtest engine | Custom trade simulation | `core/backtest/engine.run_backtest()` | Equity curve, trade log, BUY/SELL state machine all working |
| Walk-forward validation | Custom fold splitting | `core/backtest/walk_forward.run_walk_forward()` | IS/OOS splits, metric averaging, overfitting score computed |
| Performance metrics | Custom Sharpe/CAGR/MDD | `core/backtest/metrics.compute_metrics()` | Edge cases (zero std, empty trades, single-day) handled |
| Signal evaluators (4x) | Custom CAN SLIM, etc. | `core/signals/*.evaluate()` | All four methodologies with scoring criteria implemented |
| Regime classification | Custom regime rules | `core/regime/classifier.classify()` | 5-regime system with VIX/MA200/ADX/YieldCurve rules |
| Regime-based weights | Custom weight tables | `core/regime/weights.get_weights()` | Strategy weights per regime, risk adjustment factors |
| Position validation | Custom limit checks | `personal/sizer/kelly.validate_position()` | 8% position, 25% sector, violation reporting |

**Key insight:** Phase 3 is 90% integration work. The mathematical core is complete and tested. The DDD scaffolding (VOs, entities, events, repos) is also largely complete. The gap is the adapter layer connecting them, plus reasoning traces and screener queries.

## Common Pitfalls

### Pitfall 1: Rewriting Existing Math
**What goes wrong:** Implementer creates new Kelly/ATR/backtest code in `src/` domain services, introducing subtle differences from the tested `core/` and `personal/` versions.
**Why it happens:** DDD purism -- "domain shouldn't depend on infrastructure" -- but the math IS the domain.
**How to avoid:** Domain services call adapter methods. The adapter is in `infrastructure/`. `PortfolioRiskService` already follows this implicitly -- it does pure math. For signal evaluation and backtesting, the adapter pattern is explicit.
**Warning signs:** New mathematical functions in `src/*/domain/services.py` that duplicate `core/` functions.

### Pitfall 2: Cross-Context Data Coupling
**What goes wrong:** Signal handler imports `from src.scoring.domain import CompositeScore` or `from src.valuation.domain import MarginOfSafety` directly.
**Why it happens:** It's tempting when you need score+valuation data for signal decisions.
**How to avoid:** Signal handler receives primitive values (floats, strings) as command parameters. The orchestration layer (CLI or future API) gathers data from scoring and valuation contexts and passes it to the signal command.
**Warning signs:** Any `from src.scoring` or `from src.valuation` import inside `src/signals/` or `src/portfolio/`.

### Pitfall 3: Walk-Forward Data Leakage
**What goes wrong:** Walk-forward validation uses information from test period during training (look-ahead bias).
**Why it happens:** Signals generated for the full dataset before splitting into IS/OOS, or financial data not filtered by filing date.
**How to avoid:** The existing `run_walk_forward()` already handles this correctly by splitting OHLCV and signals independently per fold. Ensure signal generation for backtesting uses only data available up to each signal date (point-in-time correctness already enforced in Phase 1).
**Warning signs:** Signals series generated once for full period, then passed to walk-forward.

### Pitfall 4: Missing Profit Factor Metric
**What goes wrong:** Performance report missing profit factor (BACK-02 requirement).
**Why it happens:** `PerformanceMetrics` dataclass has 7 fields but not `profit_factor`.
**How to avoid:** Add `profit_factor` to the backtest adapter's output computation: `sum(positive_returns) / abs(sum(negative_returns))`. Do NOT modify `core/backtest/metrics.PerformanceMetrics` directly -- compute it in the adapter or backtest domain service.
**Warning signs:** Backtest report missing profit_factor field.

### Pitfall 5: Sector Weight Not Tracked at Portfolio Level
**What goes wrong:** `RISK-05` requires 25% max sector weight, but `Portfolio.can_open_position()` only checks single position weight -- it doesn't aggregate sector exposure.
**Why it happens:** The existing `can_open_position()` takes a `weight` parameter but doesn't compute sector totals from its positions dict.
**How to avoid:** Add a sector weight computation method to Portfolio aggregate that sums position weights by sector. The `Position` entity already has a `sector` field. The `PortfolioManagerHandler` can compute sector exposure before calling `can_open_position()`.
**Warning signs:** Portfolio allows 30% in one sector without blocking.

## Code Examples

### Screener Query (DuckDB)
```python
# Verified pattern from Phase 1 DuckDBStore
def query_top_n(
    conn,  # duckdb.DuckDBPyConnection
    top_n: int = 20,
    min_composite: float = 60.0,
    signal_filter: str | None = "BUY",
) -> list[dict]:
    """Rank universe by risk-adjusted composite score, filter by signal."""
    sql = """
        SELECT s.symbol, s.composite_score, s.risk_adjusted_score,
               v.intrinsic_value, v.margin_of_safety, v.has_margin,
               sig.direction, sig.strength
        FROM scores s
        LEFT JOIN valuations v ON s.symbol = v.symbol
        LEFT JOIN signals sig ON s.symbol = sig.symbol
        WHERE s.risk_adjusted_score >= ?
    """
    params: list = [min_composite]
    if signal_filter:
        sql += " AND sig.direction = ?"
        params.append(signal_filter)
    sql += " ORDER BY s.risk_adjusted_score DESC LIMIT ?"
    params.append(top_n)
    return conn.execute(sql, params).fetchdf().to_dict("records")
```

### Take-Profit Levels from Intrinsic Value
```python
# New domain logic for RISK-03
def compute_take_profit_levels(
    entry_price: float,
    intrinsic_value: float,
) -> dict:
    """Compute partial exit levels based on intrinsic value target.

    Levels: 50% of gap (partial), 75% of gap (partial), 100% = intrinsic.
    """
    if intrinsic_value <= entry_price:
        return {"levels": [], "reason": "No upside gap to intrinsic value"}
    gap = intrinsic_value - entry_price
    return {
        "levels": [
            {"pct": 0.50, "price": round(entry_price + gap * 0.50, 2),
             "action": "sell_25pct"},
            {"pct": 0.75, "price": round(entry_price + gap * 0.75, 2),
             "action": "sell_25pct"},
            {"pct": 1.00, "price": round(intrinsic_value, 2),
             "action": "sell_remaining"},
        ],
        "entry_price": entry_price,
        "intrinsic_target": intrinsic_value,
    }
```

### Profit Factor Computation
```python
# Addition for BACK-02 -- compute in adapter, not core
def compute_profit_factor(trade_returns: list[float]) -> float:
    """Profit factor = gross_profit / abs(gross_loss). >1 = profitable."""
    gross_profit = sum(r for r in trade_returns if r > 0)
    gross_loss = sum(r for r in trade_returns if r < 0)
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / abs(gross_loss)
```

### Regime Weight Adjuster Implementation (fulfills Phase 2 Protocol)
```python
# Fulfills the RegimeWeightAdjuster Protocol from scoring/domain/services.py
from core.regime.weights import REGIME_WEIGHTS
from src.scoring.domain import STRATEGY_WEIGHTS, DEFAULT_STRATEGY

class CoreRegimeAdjuster:
    """Concrete RegimeWeightAdjuster using core/regime/ weights."""

    def adjust_weights(
        self, strategy: str, regime_type: str | None = None
    ) -> dict[str, float]:
        if regime_type is None:
            return STRATEGY_WEIGHTS.get(
                strategy, STRATEGY_WEIGHTS[DEFAULT_STRATEGY]
            )
        # Map regime to strategy weights using core lookup
        # Note: core REGIME_WEIGHTS uses signal-level keys
        # while STRATEGY_WEIGHTS uses score-level keys
        # The mapping happens at the application layer
        return STRATEGY_WEIGHTS.get(
            strategy, STRATEGY_WEIGHTS[DEFAULT_STRATEGY]
        )
```

## State of the Art

| What | Current State | Impact on Phase 3 |
|------|---------------|-------------------|
| Signal evaluators (4x) | Complete in `core/signals/` | Adapter-only wrapping needed |
| Signal fusion | Complete in `src/signals/domain/services.py` | Already has consensus logic -- needs valuation gap integration |
| Kelly/ATR sizing | Complete in both `personal/sizer/` and `src/portfolio/domain/` | Both implementations exist -- adapter bridges them |
| Drawdown defense | Complete in both `personal/risk/` and `src/portfolio/domain/` | Both implementations exist -- adapter bridges them |
| Backtest engine | Complete in `core/backtest/` | Adapter + DDD bounded context needed |
| Walk-forward | Complete in `core/backtest/walk_forward.py` | Adapter wrapping needed |
| Performance metrics | 7/8 fields (missing profit_factor) | Add profit_factor in adapter |
| Regime classifier | Complete in `core/regime/` | Adapter wrapping + fulfills Phase 2 Protocol |
| DDD domain models | Signals + Portfolio VOs/services mostly complete | Extend with take-profit VO, screener query |
| Screener | Not implemented | New: DuckDB query service |
| Reasoning traces | Not implemented | New: string builder in application layer |
| Take-profit levels | Not implemented | New: pure math from intrinsic value |

**What already exists and should NOT be rebuilt:**
- `SignalFusionService.fuse()` -- 4-methodology consensus
- `PortfolioRiskService.compute_kelly_size()` -- fractional Kelly
- `PortfolioRiskService.compute_atr_stop()` -- ATR stops
- `PortfolioRiskService.assess_drawdown_defense()` -- 3-tier defense
- `Portfolio.can_open_position()` -- drawdown + position limit gate
- `PortfolioManagerHandler.open_position()` -- full position opening flow
- All `core/signals/*.evaluate()` functions
- All `core/backtest/` functions
- `personal/sizer/kelly.*` and `personal/risk/drawdown.*`

## Open Questions

1. **Regime data source for live signal generation**
   - What we know: `core/regime/classifier.classify()` needs VIX, SP500 vs 200MA, ADX, yield curve. These come from external market data.
   - What's unclear: Whether the data pipeline from Phase 1 provides these macro indicators, or if a new data fetch is needed.
   - Recommendation: The signal generation handler should accept regime indicators as command parameters. The CLI/orchestration layer fetches them before calling the handler. This avoids coupling the signals context to market data infrastructure.

2. **Signal persistence schema for DuckDB**
   - What we know: `ISignalRepository` interface exists with `save(symbol, direction, strength, metadata)`. SQLite implementation exists in `sqlite_repo.py`.
   - What's unclear: Whether signals should also be stored in DuckDB for screener queries (joining with scores and valuations).
   - Recommendation: Add a DuckDB signals table alongside the existing SQLite repo. Screener queries need joins across scores + valuations + signals -- DuckDB is the right store for this analytical workload.

3. **Backtest signal generation strategy**
   - What we know: Walk-forward needs a `signals_series` per fold. Each fold should generate signals using only data available within that fold's IS period.
   - What's unclear: How to generate per-fold signals in a computationally efficient way for 900+ ticker universe.
   - Recommendation: For Phase 3, backtest validation runs on individual stocks (not full universe). The backtest handler takes OHLCV + pre-generated signals for a single ticker. Universe-wide backtesting is a Phase 4/future optimization.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 7.4 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/test_FILE.py -x -v` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIGN-01 | Signal engine produces BUY/HOLD/SELL with reasoning trace | unit | `pytest tests/unit/test_signal_engine.py -x` | No -- Wave 0 |
| SIGN-02 | Screener ranks Top N by composite score + signal filter | unit | `pytest tests/unit/test_screener.py -x` | No -- Wave 0 |
| RISK-01 | Fractional Kelly (1/4) position sizing via adapter | unit | `pytest tests/unit/test_portfolio_sizing.py -x` | No -- Wave 0 |
| RISK-02 | ATR(21) stop-loss at 2.5-3.5x | unit | `pytest tests/unit/test_portfolio_sizing.py -x` | No -- Wave 0 |
| RISK-03 | Take-profit levels from intrinsic value | unit | `pytest tests/unit/test_take_profit.py -x` | No -- Wave 0 |
| RISK-04 | Drawdown defense 10%/15%/20% via Portfolio aggregate | unit | `pytest tests/unit/test_portfolio_risk.py -x` | No -- Wave 0 |
| RISK-05 | Max 8% position + 25% sector hard limits | unit | `pytest tests/unit/test_portfolio_risk.py -x` | No -- Wave 0 |
| BACK-01 | Walk-forward validation produces IS/OOS metrics | unit | `pytest tests/unit/test_backtest_validation.py -x` | No -- Wave 0 |
| BACK-02 | Performance report with Sharpe, MDD, win rate, profit factor | unit | `pytest tests/unit/test_backtest_validation.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_TARGET.py -x -v` (specific test file)
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `tests/unit/test_signal_engine.py` -- covers SIGN-01 (signal + reasoning trace)
- [ ] `tests/unit/test_screener.py` -- covers SIGN-02 (Top N ranking + filtering)
- [ ] `tests/unit/test_portfolio_sizing.py` -- covers RISK-01, RISK-02 (Kelly + ATR via DDD adapter)
- [ ] `tests/unit/test_take_profit.py` -- covers RISK-03 (intrinsic value targets)
- [ ] `tests/unit/test_portfolio_risk.py` -- covers RISK-04, RISK-05 (drawdown defense + limits via DDD)
- [ ] `tests/unit/test_backtest_validation.py` -- covers BACK-01, BACK-02 (walk-forward + report via DDD adapter)

Note: Existing tests (`test_sizer_kelly.py`, `test_risk_drawdown.py`, `test_walk_forward.py`, `test_backtest_engine.py`, `test_signal_consensus.py`) cover the `core/` and `personal/` implementations and should remain green. New tests cover the DDD adapter layer and new domain logic (reasoning, screener, take-profit, profit factor).

## Sources

### Primary (HIGH confidence)
- Existing codebase: `core/signals/` (all 4 evaluators + consensus) -- read and verified
- Existing codebase: `core/backtest/` (engine + walk_forward + metrics) -- read and verified
- Existing codebase: `personal/sizer/kelly.py` + `personal/risk/drawdown.py` -- read and verified
- Existing codebase: `src/signals/domain/` (VOs, services, events, repos, handlers) -- read and verified
- Existing codebase: `src/portfolio/domain/` (aggregates, entities, VOs, services, repos, handlers) -- read and verified
- Existing codebase: `src/scoring/domain/services.py` -- `RegimeWeightAdjuster` Protocol confirmed ready for Phase 3 implementation
- Existing codebase: `core/regime/` (classifier + weights) -- read and verified
- Project REQUIREMENTS.md -- all 9 requirement IDs confirmed
- Project STATE.md -- Phase 2 complete, accumulated decisions reviewed

### Secondary (MEDIUM confidence)
- Phase 1 and Phase 2 RESEARCH.md patterns -- adapter pattern, DDD structure, testing approach
- Existing tests (`test_sizer_kelly.py`, `test_risk_drawdown.py`, etc.) -- verified working implementations

### Tertiary (LOW confidence)
- Sharpe t-stat calculation method -- standard formula `t = sharpe * sqrt(n)` but should verify scipy.stats usage if significance testing needed
- PBO (Probability of Backtest Overfitting) computation -- CSCV method is complex; may defer to overfitting_score (IS Sharpe - OOS Sharpe) as simpler proxy per existing `core/backtest/walk_forward.py`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all libraries already installed and in use
- Architecture: HIGH -- DDD adapter pattern proven in 2 prior phases, all bounded contexts scaffolded
- Pitfalls: HIGH -- comprehensive review of existing codebase revealed sector weight gap and profit factor gap
- Signal logic: HIGH -- all 4 methodology evaluators read and verified, consensus engine verified
- Risk management: HIGH -- Kelly, ATR, drawdown all implemented in both core and DDD layers
- Backtesting: HIGH -- engine, walk-forward, metrics all implemented and tested
- Screener: MEDIUM -- DuckDB query pattern is established but screener-specific schema needs design
- Reasoning traces: MEDIUM -- straightforward string building but format not yet defined

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable domain -- no external API changes expected)
