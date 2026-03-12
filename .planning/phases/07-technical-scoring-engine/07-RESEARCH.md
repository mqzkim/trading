# Phase 7: Technical Scoring Engine - Research

**Researched:** 2026-03-12
**Domain:** Technical indicator scoring within DDD scoring bounded context (Python)
**Confidence:** HIGH

## Summary

Phase 7 integrates 5 technical indicators (RSI, MACD, MA, ADX, OBV) into the DDD scoring bounded context, producing per-indicator sub-scores with explanations and a composite technical score (0-100). The overall CompositeScore then blends fundamental (40%), technical (40%), and sentiment (20% placeholder) sub-scores.

The project already has all the required primitives. `core/data/indicators.py` computes RSI, MACD, MA, ADX, OBV from OHLCV DataFrames using pure pandas/numpy. `core/scoring/technical.py` already computes a composite technical score from those indicators. The DDD `scoring` bounded context has `TechnicalScore` (a ValueObject with a single `value: float`) and `CompositeScoringService` that already combines fundamental/technical/sentiment with strategy-specific weights. The gap is: (1) `TechnicalScore` has no sub-score breakdown, (2) there are no per-indicator explanations, (3) the CLI `score` command doesn't surface individual technical indicator scores, and (4) the requirement weights (40/40/20) differ from the existing `STRATEGY_WEIGHTS` for swing (35/40/25).

**Primary recommendation:** Extend `TechnicalScore` VO to include 5 sub-scores + explanations. Build a `TechnicalScoringService` domain service that converts raw indicator values to individual 0-100 scores with plain-text explanations. Update `CompositeScoringService` to use the new requirement weights. Wire into CLI `score` command to display breakdown.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TECH-01 | RSI/MACD/MA/ADX/OBV 5개 지표를 DDD 스코어링 컨텍스트에 통합 | Existing `core/data/indicators.py` computes all 5 raw indicators. Need new `TechnicalScoringService` in `src/scoring/domain/services.py` that takes raw values, normalizes to 0-100 per indicator. |
| TECH-02 | 기술적 복합 점수 (0-100) 산출 (가중 합산) | `core/scoring/technical.py` already does 40% trend + 40% momentum + 20% volume. Adapt into DDD domain service with configurable indicator weights. |
| TECH-03 | 기존 CompositeScore에 기술 점수 통합 (기본40%/기술40%/센티먼트20%) | `STRATEGY_WEIGHTS` currently defines swing as 35/40/25 and position as 50/30/20. Requirements specify default 40/40/20. Update `STRATEGY_WEIGHTS` or add new weight set per requirement. |
| TECH-04 | 서브 스코어 분해 출력 (5개 지표별 개별 점수 + 설명) | Extend `TechnicalScore` VO to hold 5 sub-scores. Each score gets a plain-text explanation string. Wire into CLI `score` command table output. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | >=2.0 | OHLCV DataFrame operations, indicator calculation | Already in project deps, pure-pandas indicator math |
| numpy | >=1.26 | Numerical operations for normalization | Already in project deps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none new) | - | All required libraries already in project | - |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure pandas indicators | ta-lib (C-based) | ta-lib requires system library install. Project already has hand-rolled indicators in `core/data/indicators.py` that work. No new dependency needed. |
| Custom normalization | scikit-learn MinMaxScaler | Over-engineering for 5 simple normalizations. `_norm()` helper already exists in `core/scoring/technical.py`. |

**Installation:** No new dependencies required. All indicator computation uses existing pandas/numpy.

## Architecture Patterns

### Existing Project Structure (scoring bounded context)
```
src/scoring/
    domain/
        __init__.py          # Public API (exports all VOs, services, repos)
        value_objects.py     # Symbol, FundamentalScore, TechnicalScore, SentimentScore, CompositeScore, SafetyGate
        services.py          # CompositeScoringService, SafetyFilterService, RegimeWeightAdjuster
        events.py            # ScoreUpdatedEvent
        repositories.py      # IScoreRepository (ABC)
    application/
        commands.py          # ScoreSymbolCommand, BatchScoreCommand
        queries.py           # GetLatestScoreQuery, GetTopScoredQuery
        handlers.py          # ScoreSymbolHandler (orchestrates scoring pipeline)
        __init__.py
    infrastructure/
        core_scoring_adapter.py  # Wraps core/scoring/ functions for DDD
        sqlite_repo.py           # SqliteScoreRepository
        in_memory_repo.py        # InMemoryScoreRepository (tests)
        __init__.py
```

### Pattern 1: Extend TechnicalScore ValueObject with Sub-Scores
**What:** The current `TechnicalScore` VO holds only `value: float`. Extend it to carry individual indicator scores and explanation strings while maintaining backward compatibility.
**When to use:** When domain data needs richer structure without breaking existing consumers.
**Example:**
```python
# In src/scoring/domain/value_objects.py
@dataclass(frozen=True)
class TechnicalIndicatorScore(ValueObject):
    """Single technical indicator sub-score with explanation."""
    name: str           # e.g., "RSI", "MACD", "MA", "ADX", "OBV"
    value: float        # 0-100
    explanation: str    # e.g., "RSI at 65: moderately bullish momentum"
    raw_value: float | None = None  # raw indicator value for transparency

    def _validate(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"{self.name} score must be 0-100, got {self.value}")

@dataclass(frozen=True)
class TechnicalScore(ValueObject):
    """Technical analysis composite score (0-100) with sub-score breakdown."""
    value: float
    rsi_score: TechnicalIndicatorScore | None = None
    macd_score: TechnicalIndicatorScore | None = None
    ma_score: TechnicalIndicatorScore | None = None
    adx_score: TechnicalIndicatorScore | None = None
    obv_score: TechnicalIndicatorScore | None = None
    weights: dict[str, float] | None = None

    def _validate(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"TechnicalScore must be 0-100, got {self.value}")

    @property
    def sub_scores(self) -> list["TechnicalIndicatorScore"]:
        return [s for s in [self.rsi_score, self.macd_score, self.ma_score,
                            self.adx_score, self.obv_score] if s is not None]
```

### Pattern 2: TechnicalScoringService in Domain Layer
**What:** Pure domain service that converts raw indicator values to scored + explained sub-scores and computes composite. No framework dependencies.
**When to use:** Business logic that operates on multiple value objects without entity identity.
**Example:**
```python
# In src/scoring/domain/services.py

# Default weights for 5 technical indicators
TECHNICAL_INDICATOR_WEIGHTS: dict[str, float] = {
    "rsi": 0.20,
    "macd": 0.20,
    "ma": 0.25,
    "adx": 0.15,
    "obv": 0.20,
}

class TechnicalScoringService:
    """Scores 5 technical indicators and produces composite technical score."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = weights or TECHNICAL_INDICATOR_WEIGHTS

    def compute(
        self,
        rsi: float | None,
        macd_histogram: float | None,
        close: float,
        ma50: float | None,
        ma200: float | None,
        adx: float | None,
        obv_change_pct: float | None,
    ) -> TechnicalScore:
        """Compute technical composite from raw indicator values."""
        # Each _score_X method returns TechnicalIndicatorScore
        ...
```

### Pattern 3: Infrastructure Adapter Bridges Core Indicators to Domain
**What:** The `CoreScoringAdapter` pattern already used in the project. Add a method (or new adapter class) that takes OHLCV DataFrame, calls `core/data/indicators.compute_all()`, and returns domain-compatible raw values for the TechnicalScoringService.
**When to use:** Bridging existing proven math code into DDD domain service without rewriting.

### Anti-Patterns to Avoid
- **Rewriting indicator math:** `core/data/indicators.py` and `core/scoring/technical.py` contain proven, tested indicator calculations. Do not duplicate or rewrite this math. Adapter pattern only.
- **Putting pandas in domain layer:** The domain service must receive primitive values (float, None), not pandas Series. The infrastructure adapter extracts float values from pandas.
- **Breaking TechnicalScore backward compatibility:** Existing code creates `TechnicalScore(value=50)`. New fields must have defaults (`None`) so old callers keep working.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RSI calculation | Custom RSI formula | `core.data.indicators.rsi()` | Already tested with Wilder's smoothing, verified in test_data_indicators.py |
| MACD calculation | Custom MACD formula | `core.data.indicators.macd()` | EMA-based with configurable fast/slow/signal periods |
| ADX calculation | Custom ADX formula | `core.data.indicators.adx()` | Complex DI+/DI- calculation already implemented and tested |
| OBV calculation | Custom OBV formula | `core.data.indicators.obv()` | Cumulative signed volume already implemented |
| Moving Averages | Custom MA | `core.data.indicators.ma()` | Simple but already standardized with period parameter |
| Score normalization | Custom normalizer | `_norm(v, lo, hi)` pattern from `core/scoring/technical.py` | Maps any value range to 0-100, handles edge cases |

**Key insight:** All 5 technical indicators are already implemented, tested, and producing correct results in `core/data/indicators.py`. The task is not to build indicators but to (a) normalize their output to 0-100 scores with explanations, and (b) wire into the DDD domain layer.

## Common Pitfalls

### Pitfall 1: STRATEGY_WEIGHTS Mismatch
**What goes wrong:** The requirements specify fundamental 40% / technical 40% / sentiment 20% as the default. But the existing `STRATEGY_WEIGHTS` in `value_objects.py` defines swing as 35/40/25 and position as 50/30/20.
**Why it happens:** Requirements were written after the original code. Two weight definitions exist: `core/scoring/composite.py` (old) and `src/scoring/domain/value_objects.py` (DDD).
**How to avoid:** The requirement says "fundamental (40%), technical (40%), and sentiment (20% placeholder)". This MUST be the default. Either update `STRATEGY_WEIGHTS` or introduce a new default set. Document the change explicitly and update all tests that assert on specific composite values.
**Warning signs:** Tests passing with old weights but failing with new weights. Composite score values shifting.

### Pitfall 2: Breaking Backward Compatibility of TechnicalScore VO
**What goes wrong:** Existing code constructs `TechnicalScore(value=X)` in at least 3 places: `handlers.py` line 95, `test_scoring_composite_v2.py`, and potentially CLI code. Adding required fields breaks these callers.
**Why it happens:** Frozen dataclass fields added without defaults.
**How to avoid:** ALL new fields on TechnicalScore MUST have `None` defaults. The VO should work identically to before when only `value` is provided. Write a backward-compat test: `TechnicalScore(value=65.0)` must still work.
**Warning signs:** `TypeError: __init__() missing required positional argument` errors.

### Pitfall 3: Putting Pandas/Numpy in Domain Layer
**What goes wrong:** Domain services import pandas to process indicator Series directly, violating the "domain is pure" DDD rule.
**Why it happens:** Temptation to pass DataFrame to domain service for convenience.
**How to avoid:** Infrastructure adapter extracts float values from pandas Series, passes only primitives to domain service. Domain service signature uses `float | None` only.
**Warning signs:** `import pandas` appearing in any `src/scoring/domain/` file.

### Pitfall 4: CLI Score Command Data Flow
**What goes wrong:** The current CLI `score` command (`cli/main.py` lines 88-155) imports directly from `core.data.client`, `core.orchestrator`, and `core.scoring.composite` -- not through the DDD layers. Adding technical sub-scores requires either modifying this existing flow or migrating to DDD flow.
**Why it happens:** CLI score was built in v1.0 before DDD migration. It uses `_estimate_technical_score()` from `core/orchestrator.py` which returns a single float.
**How to avoid:** For this phase, update the CLI score command to call the DDD-layer scoring (through bootstrap context handler) instead of the old core imports. This aligns with the Phase 5 decision: "Core/ commands keep existing imports; full DDD migration deferred to Phase 6+". Phase 7 is the appropriate time to migrate the `score` command.
**Warning signs:** Technical sub-scores showing in one code path but not another.

### Pitfall 5: NaN/None Handling in Indicator Scores
**What goes wrong:** Raw indicator values can be NaN (insufficient data history) or None. Scoring service crashes on NaN arithmetic.
**Why it happens:** RSI requires 14+ data points, MA200 requires 200, ADX requires 28+. Short history tickers produce NaN.
**How to avoid:** Each indicator scoring function must handle NaN/None explicitly. Default to neutral score (50) when data is insufficient, and explanation must state "insufficient data". The `_safe_last()` pattern from `core/scoring/technical.py` already handles this.
**Warning signs:** `ValueError: cannot convert float NaN to integer`, scores of 0 or 100 for missing data.

### Pitfall 6: OBV Score Scaling
**What goes wrong:** OBV is a cumulative volume number that varies wildly between stocks (AAPL OBV might be 500M, a small-cap might be 50K). Normalizing to 0-100 requires relative change, not absolute value.
**Why it happens:** Unlike RSI (0-100 bounded) or MACD (centered around 0), OBV has no natural scale.
**How to avoid:** Score OBV by its percentage change over a lookback window (e.g., 60 days), not its absolute value. The existing `core/scoring/technical.py` already does this correctly (lines 73-84): compares last OBV to 60-day-ago OBV.
**Warning signs:** All stocks getting identical OBV scores, or extreme scores.

## Code Examples

Verified patterns from the existing codebase:

### Existing Indicator Computation (core/data/indicators.py)
```python
# Source: /home/mqz/workspace/trading/core/data/indicators.py
def compute_all(df: pd.DataFrame) -> dict:
    """Compute all standard indicators from a cleaned OHLCV DataFrame."""
    close = df["close"]
    macd_df = macd(close)
    return {
        "ma50": ma(close, 50),
        "ma200": ma(close, 200),
        "rsi14": rsi(close, 14),
        "atr21": atr(df, 21),
        "adx14": adx(df, 14),
        "obv": obv(df),
        "macd": macd_df["macd"],
        "macd_signal": macd_df["signal"],
        "macd_histogram": macd_df["histogram"],
    }
```

### Existing Technical Scoring (core/scoring/technical.py)
```python
# Source: /home/mqz/workspace/trading/core/scoring/technical.py
# Composite (40% trend + 40% momentum + 20% volume)
technical_score = 0.40 * trend_score + 0.40 * momentum_score + 0.20 * volume_score
```

### Existing CompositeScore.compute() Pattern (domain VOs)
```python
# Source: src/scoring/domain/value_objects.py lines 126-149
@classmethod
def compute(
    cls,
    fundamental: FundamentalScore,
    technical: TechnicalScore,
    sentiment: SentimentScore,
    strategy: str = DEFAULT_STRATEGY,
    tail_risk_penalty: float = 0.0,
) -> "CompositeScore":
    w = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS[DEFAULT_STRATEGY])
    raw = (
        w["fundamental"] * fundamental.value
        + w["technical"] * technical.value
        + w["sentiment"] * sentiment.value
    )
```

### Existing Handler Data Flow Pattern (ScoreSymbolHandler)
```python
# Source: src/scoring/application/handlers.py lines 93-96
# This is how TechnicalScore is currently created -- single value
technical = TechnicalScore(value=technical_data.get("technical_score", 50))
```

### Existing CLI Score Output Pattern
```python
# Source: cli/main.py lines 141-155
table = Table(title=f"Composite Score: {symbol}", ...)
table.add_row("Fundamental", f"{result.get('fundamental_score', 0):.1f}")
table.add_row("Technical", f"{result.get('technical_score', 0):.1f}")
table.add_row("Sentiment", f"{result.get('sentiment_score', 50):.1f}")
```

### Explanation String Pattern (for TECH-04)
```python
# Recommended pattern for indicator explanations
def _explain_rsi(rsi_value: float, score: float) -> str:
    if rsi_value > 70:
        return f"RSI at {rsi_value:.0f}: overbought territory, momentum may reverse"
    elif rsi_value > 60:
        return f"RSI at {rsi_value:.0f}: bullish momentum"
    elif rsi_value > 40:
        return f"RSI at {rsi_value:.0f}: neutral momentum"
    elif rsi_value > 30:
        return f"RSI at {rsi_value:.0f}: bearish momentum"
    else:
        return f"RSI at {rsi_value:.0f}: oversold territory, potential reversal"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single technical_score float | Sub-score breakdown per indicator | Phase 7 (this phase) | Users see which indicators drive the technical score |
| core/scoring/technical.py direct call | DDD TechnicalScoringService via adapter | Phase 7 (this phase) | Testable, injectable, DDD-compliant scoring |
| Rough _estimate_technical_score in orchestrator | Full indicator computation through data client | Phase 7 (this phase) | Accurate scores from live indicators, not rough estimates |

**Important weight change decision:**
- Current code: swing = fundamental 35% / technical 40% / sentiment 25%
- Requirement TECH-03: fundamental 40% / technical 40% / sentiment 20%
- The weights in `STRATEGY_WEIGHTS` must be updated to match the requirement. This is a deliberate design decision documented in REQUIREMENTS.md.

## Open Questions

1. **STRATEGY_WEIGHTS update scope**
   - What we know: Requirements say 40/40/20. Current swing weights are 35/40/25. Position weights are 50/30/20.
   - What's unclear: Should position weights also change? Requirements only mention "default" 40/40/20.
   - Recommendation: Update swing to 40/40/20 as required. Keep position at 50/30/20 (not mentioned in requirements). Document as TECH-03 applying to the default strategy.

2. **ScoreSymbolHandler migration depth**
   - What we know: Current handler uses `_get_technical()` which calls `core.scoring.technical.compute_technical_score()` -- returns a flat dict with trend/momentum/volume scores but not per-indicator breakdowns matching the 5 required indicators.
   - What's unclear: Should we replace the handler's data flow entirely or extend it?
   - Recommendation: Extend the infrastructure adapter with a new method that computes per-indicator scores. The handler creates `TechnicalScore` with full sub-score breakdown. Backward-compatible -- old path still works when sub-scores are not available.

3. **CLI score command: migrate to DDD or patch core path?**
   - What we know: CLI currently calls core/ directly. Phase 5 deferred DDD migration.
   - What's unclear: Is this phase the right time for full DDD migration of the score command?
   - Recommendation: Partially migrate. The CLI score command should use the DDD handler for technical scoring (to get sub-scores), but can still use the existing core path for fundamental/sentiment until those get their own DDD migrations.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.4 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/test_scoring_technical.py tests/unit/test_scoring_composite_v2.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TECH-01 | 5 indicators produce individual 0-100 scores via DDD service | unit | `pytest tests/unit/test_technical_scoring_service.py -x` | Wave 0 |
| TECH-02 | Technical composite (0-100) from weighted 5 indicators | unit | `pytest tests/unit/test_technical_scoring_service.py::test_composite_range -x` | Wave 0 |
| TECH-03 | CompositeScore uses 40/40/20 weights | unit | `pytest tests/unit/test_scoring_composite_v2.py -x` | Exists (needs update) |
| TECH-04 | Sub-scores with plain-text explanations in CLI output | unit + integration | `pytest tests/unit/test_cli_score_technical.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_technical_scoring_service.py tests/unit/test_scoring_composite_v2.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_technical_scoring_service.py` -- covers TECH-01, TECH-02 (TechnicalScoringService unit tests)
- [ ] `tests/unit/test_cli_score_technical.py` -- covers TECH-04 (CLI sub-score output)
- [ ] Update `tests/unit/test_scoring_composite_v2.py` -- covers TECH-03 (weight change to 40/40/20)

*(Existing test infrastructure covers framework and fixtures. Only new test files needed.)*

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/scoring/domain/value_objects.py` -- TechnicalScore VO, STRATEGY_WEIGHTS definition
- Codebase analysis: `src/scoring/domain/services.py` -- CompositeScoringService, RegimeWeightAdjuster
- Codebase analysis: `core/data/indicators.py` -- All 5 indicator implementations (RSI, MACD, MA, ADX, OBV)
- Codebase analysis: `core/scoring/technical.py` -- Existing technical scoring normalization logic
- Codebase analysis: `src/scoring/application/handlers.py` -- ScoreSymbolHandler data flow
- Codebase analysis: `cli/main.py` -- CLI score command current implementation
- Codebase analysis: `src/scoring/infrastructure/core_scoring_adapter.py` -- Adapter pattern for core/ bridge

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` -- TECH-01 through TECH-04 requirements definition
- `.planning/ROADMAP.md` -- Phase 7 success criteria
- `docs/quantitative-scoring-methodologies.md` -- Academic basis for scoring approach

### Tertiary (LOW confidence)
- None -- all findings are based on codebase analysis, no external searches needed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all tools already in project
- Architecture: HIGH -- extending existing patterns (VO extension, domain service, adapter bridge), well-established project conventions
- Pitfalls: HIGH -- identified through direct codebase analysis of existing code paths and data flow
- Indicator math: HIGH -- all 5 indicators already implemented and tested in `core/data/indicators.py`

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (stable -- no external dependency changes expected)
