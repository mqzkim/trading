# Phase 28: Commercial API & Dashboard - Research

**Researched:** 2026-03-18
**Domain:** FastAPI commercial endpoints + Next.js dashboard enhancement
**Confidence:** HIGH

## Summary

Phase 28 has TWO distinct work streams that share no runtime infrastructure:

1. **Commercial API** (`commercial/api/main.py` on :8000) -- public-facing, JWT-authenticated, per-ticker endpoints for paying customers. Extends response schemas to expose 3-axis sub-scores, regime probabilities, and signal reasoning.

2. **Dashboard Backend** (`src/dashboard/presentation/app.py` on :8000) -- internal-facing, no auth, bulk-query endpoints powering the React dashboard. The dashboard Next.js app (:3000) proxies `/api/*` to this FastAPI app via `next.config.ts` rewrites. This is a SEPARATE FastAPI app from the commercial API.

The scoring handler already returns technical sub-scores (5 indicators) and has SentimentScore VO with 4 sub-source fields from Phase 27. This phase surfaces them through both the commercial API schemas AND the dashboard query handlers.

**Critical architecture insight:** The dashboard hooks call `/api/v1/dashboard/signals` which routes to `SignalsQueryHandler` in `src/dashboard/application/queries.py` -- this is NOT the commercial API. The dashboard has its own bounded context (`src/dashboard/`) with query handlers that aggregate data from score_repo, signal_repo, regime_repo, etc. The dashboard backend (`src/dashboard/presentation/app.py`) and the commercial API (`commercial/api/main.py`) are two separate FastAPI applications.

**Primary recommendation:** Treat as two parallel work tracks: (A) extend commercial API schemas + routers, (B) extend dashboard query handlers + React components. Both are presentation-layer only -- no domain logic changes except minor handler result dict extensions to expose sentiment sub-scores.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- QuantScore endpoint returns: composite_score + fundamental_score + technical_score + sentiment_score + sentiment_confidence + technical_sub_scores (5 indicators) + sentiment_sub_scores (4 sources)
- Response structure: same as current QuantScoreResponse schema -- extend sub_scores to include both technical and sentiment breakdowns
- Each sub-score entry: {name, value (0-100 normalized), raw_value}
- Sentiment data unavailable: return `sentiment_score: null` + `sentiment_confidence: "NONE"` -- field always present, value nullable
- Do NOT omit sentiment key when data is missing -- consumers should not need to check key existence
- All responses include legal disclaimer auto-appended
- SignalFusion uses informational language: "Bullish"/"Bearish"/"Neutral" (not "BUY"/"SELL")
- No position sizing, stop-loss, or take-profit in commercial API responses
- Signal rows are expandable: click row -> score breakdown panel unfolds below the row
- Breakdown panel shows: F: XX | T: XX | S: XX (confidence label)
- Technical sub-row: RSI / MACD / MA / ADX / OBV (each normalized 0-100)
- Sentiment sub-row: News / Insider / Institutional / Analyst (each normalized 0-100)
- Bloomberg dark theme -- same visual language as existing pages
- When sentiment_confidence = NONE: sentiment sub-row grayed out + "Sentiment data unavailable" label
- Do NOT hide the row -- show it in disabled state so the user understands data freshness
- Performance Attribution page: 5th page in dashboard navigation
- Layout: Summary KPI cards (Sharpe / Sortino / Win Rate / Max Drawdown) at top
- Below: Brinson-Fachler 4-level decomposition table (Portfolio / Strategy / Trade / Skill columns)
- Below: Equity Curve chart (TradingView Lightweight Charts -- already installed)
- Below: Strategy scorecard (IC vs 0.03 threshold / Kelly efficiency vs 70% threshold)
- Empty state: "No performance data yet -- generates after first closed trades" -- DO NOT use mock data
- Phase 29 will seed real data; this phase builds the page shell that auto-populates when data arrives
- Regime dashboard: add HMM probability section to existing regime area on Risk page (no new page)
- Display: horizontal progress bars, one per regime (Bull / Bear / Sideways / Crisis)
- Current dominant regime highlighted with bold border
- Label format: `[progress-bar 82%] Bull`
- Data source: regime detection handler already wired; extend response to include per-regime probabilities

### Claude's Discretion
- Exact bar colors for regime probability display (Bloomberg palette preferred)
- Loading skeleton implementation for new dashboard sections
- Error state handling for API timeouts in dashboard BFF

### Deferred Ideas (OUT OF SCOPE)
- None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | QuantScore endpoint returns composite score with sub-component breakdown | Extend `QuantScoreResponse` schema + router mapping; handler already returns `technical_sub_scores`; add sentiment sub-scores to handler result dict |
| API-02 | RegimeRadar endpoint returns current regime with probability and indicators | Extend `RegimeCurrentResponse` with `regime_probabilities` dict; compute synthetic probabilities from indicator scores in router |
| API-03 | SignalFusion endpoint returns consensus signal with reasoning trace | `SignalResponse` already has methodology_votes; these ARE the reasoning trace -- each vote is a methodology + direction + score |
| API-04 | JWT authentication with API key management | ALREADY COMPLETE -- auth router, JWT decode, API key CRUD all wired and tested |
| API-05 | Rate limiting per tier (free/basic/pro) | ALREADY COMPLETE -- slowapi with tier extraction from JWT claims |
| API-06 | Legal disclaimer auto-included in all responses | ALREADY COMPLETE -- DISCLAIMER constant auto-set as default field in all response schemas |
| API-07 | OpenAPI/Swagger documentation auto-generated | FastAPI auto-generates at /docs; verify schema descriptions are updated after extensions |
| DASH-01 | Technical and sentiment sub-scores visible on Signals page | Extend `SignalsQueryHandler` to include sub-scores from score_repo details; create expandable row components |
| DASH-02 | Performance attribution page added to dashboard | New `/performance` route with empty-state shell; KPI cards, Brinson table, equity curve, scorecard |
| DASH-03 | Real data displayed across all pages | Ensure `SignalsQueryHandler` and `RiskQueryHandler` surface sub-score data that handlers now produce |
| DASH-04 | Regime detection enhanced view with HMM probabilities | Extend `RiskQueryHandler` to return regime probabilities; add probability bar components to Risk page |
</phase_requirements>

## Standard Stack

### Core (already installed -- NO new dependencies)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| FastAPI | existing | Commercial API + Dashboard backend | Two separate apps sharing same framework |
| Pydantic v2 | existing | Response schemas | BaseModel for all responses |
| PyJWT | existing | JWT auth | Commercial API only |
| slowapi | existing | Rate limiting | Commercial API only |
| Next.js | 16.1.6 | Dashboard frontend | Rewrite proxy to dashboard FastAPI app |
| React | 19.2.3 | UI library | |
| @tanstack/react-query | ^5.90.21 | Data fetching | All hooks use useQuery |
| @tanstack/react-table | ^8.21.3 | Data tables | Scoring table on Signals page |
| lightweight-charts | ^5.1.0 | Equity curve chart | TradingView charts, already used in overview |
| shadcn/ui | ^4.0.6 | Component library | Cards, badges, tables, progress bars |
| tailwindcss | ^4 | Styling | Bloomberg OKLCH dark theme |

### No New Dependencies Needed
All required functionality is covered by existing packages. The `progress.tsx` component from shadcn/ui is already installed and perfect for HMM probability bars.

## Architecture Patterns

### Critical: Two Separate FastAPI Applications

```
COMMERCIAL API (commercial/api/main.py)
  Port: 8000 (standalone)
  Auth: JWT required
  Endpoints: /api/v1/quantscore/{ticker}, /api/v1/regime/current, /api/v1/signals/{ticker}
  Handlers: ScoreSymbolHandler, DetectRegimeHandler, GenerateSignalHandler
  Purpose: Per-ticker queries for paying API customers

DASHBOARD BACKEND (src/dashboard/presentation/app.py)
  Port: 8000 (dashboard mode)
  Auth: NONE
  Endpoints: /api/v1/dashboard/overview, /api/v1/dashboard/signals, /api/v1/dashboard/risk, /api/v1/dashboard/pipeline
  Handlers: OverviewQueryHandler, SignalsQueryHandler, RiskQueryHandler, PipelineQueryHandler
  Purpose: Bulk aggregation queries for internal dashboard

DASHBOARD FRONTEND (Next.js :3000)
  Proxy: /api/* → dashboard backend via next.config.ts rewrites
  Hooks: useOverview, useSignals, useRisk, usePipeline → fetch('/api/v1/dashboard/*')
```

These are NEVER the same running process. The planner must treat them as separate change sets.

### Pattern 1: Schema Extension (Commercial API)
**What:** Add new fields to existing Pydantic response models
**When to use:** API-01, API-02, API-03
**Key rule:** Add fields as `Optional` with defaults to maintain backward compatibility

### Pattern 2: Query Handler Extension (Dashboard Backend)
**What:** Extend existing query handlers to return additional data from repos
**When to use:** DASH-01, DASH-03, DASH-04
**Key point:** `SignalsQueryHandler` reads from `score_repo.find_all_latest()` which returns `CompositeScore` VOs. To get sub-scores, it needs to also read score details. The `score_repo.save()` receives a `details` dict with fundamental/technical/sentiment scores -- check if `find_all_latest()` also returns details or if a new method is needed.

### Pattern 3: Expandable Table Row (Dashboard Frontend)
**What:** Table row that expands to show sub-score detail panel
**When to use:** DASH-01 signals page
**Implementation:** Use @tanstack/react-table `getCanExpand()` + custom sub-row rendering. The existing `DataTable` component wraps react-table -- extend it with expansion support.

### Pattern 4: Empty-State Shell Page (Dashboard Frontend)
**What:** Page with full layout structure showing "no data yet" when empty
**When to use:** DASH-02 performance attribution page
**Key rule:** Never use mock data. Show real component structure with empty states.

### Anti-Patterns to Avoid
- **Confusing the two FastAPI apps:** Commercial API changes go in `commercial/api/`, dashboard backend changes go in `src/dashboard/`. Never mix.
- **Changing domain logic:** This phase is presentation-only. Do not modify scoring services, regime detection, or signal generation. Exception: handler result dict may need minor extension to expose sentiment sub-scores.
- **Breaking existing API contracts:** Add fields, never remove or rename. `sub_scores: Optional[dict]` can coexist with new typed fields.
- **Creating Next.js API routes:** Dashboard uses rewrite proxy, not API route handlers.
- **Mocking data on Performance page:** Empty state only. Phase 29 provides real data.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Progress bars | Custom div+css bars | shadcn `<Progress>` component | Already installed, themed, accessible |
| Expandable table rows | Manual toggle+state | @tanstack/react-table row expansion API | Built-in support, handles keyboard nav |
| Charts | Canvas/SVG from scratch | `lightweight-charts` (already imported) | TradingView quality, already used on overview |
| Loading states | Conditional rendering | `<Skeleton>` component | Already established pattern across all pages |

## Common Pitfalls

### Pitfall 1: Sentiment Sub-Scores Not in Handler Result Dict
**What goes wrong:** The scoring handler returns `sentiment_score` as a float (line 178 of handlers.py), but the SentimentScore VO has `news_score`, `insider_score`, `institutional_score`, `analyst_score`. These sub-fields are NOT currently propagated to the handler result dict.
**Why it happens:** Phase 27 added sub-fields to the SentimentScore VO but the handler only extracts `sentiment.value` to the result dict -- it doesn't include individual sub-scores.
**How to avoid:** Add `sentiment_sub_scores` list and `sentiment_confidence` to the handler result dict, similar to how `technical_sub_scores` is already added (lines 186-195):
```python
# Add alongside technical_sub_scores in handler result dict
result["sentiment_confidence"] = sentiment.confidence.value
if sentiment.news_score is not None or sentiment.insider_score is not None:
    result["sentiment_sub_scores"] = [
        {"name": "News", "value": sentiment.news_score, "raw_value": sentiment.news_score},
        {"name": "Insider", "value": sentiment.insider_score, "raw_value": sentiment.insider_score},
        {"name": "Institutional", "value": sentiment.institutional_score, "raw_value": sentiment.institutional_score},
        {"name": "Analyst", "value": sentiment.analyst_score, "raw_value": sentiment.analyst_score},
    ]
```
**Warning signs:** API returns `sentiment_sub_scores: null` even when sentiment data exists.

### Pitfall 2: Regime Probabilities Not Available from Handler
**What goes wrong:** CONTEXT.md asks for per-regime probability bars (Bull/Bear/Sideways/Crisis), but `DetectRegimeHandler.handle()` returns only the dominant regime + confidence, not a probability distribution for all 4 regimes.
**Why it happens:** `RegimeDetectionService.detect()` returns `(RegimeType, float)` -- single regime, not distribution.
**How to avoid:** Compute synthetic probabilities in the API router layer. For the dominant regime, use the confidence value. Distribute remaining (1 - confidence) across other regimes based on indicator proximity to thresholds. This is a presentation-layer calculation, not a domain change.
**Warning signs:** Regime endpoint returns only 1 regime probability instead of 4.

### Pitfall 3: Dashboard score_repo Returns CompositeScore Only
**What goes wrong:** `SignalsQueryHandler` calls `score_repo.find_all_latest()` which returns `dict[str, CompositeScore]`. The `CompositeScore` VO contains only `value`, `risk_adjusted`, `strategy`, `weights`. It does NOT contain sub-scores (fundamental, technical, sentiment).
**Why it happens:** The score_repo stores a CompositeScore VO, not the full scoring details. Sub-score details are saved via `score_repo.save(symbol, composite, details=details)` but `find_all_latest()` may not retrieve them.
**How to avoid:** Check if `IScoreRepository.find_all_latest()` returns details alongside CompositeScore. If not, add a method or extend it to also return the details dict that was saved.
**Warning signs:** Dashboard signals page shows composite scores but no F/T/S breakdown.

### Pitfall 4: Two Different Score Data Paths
**What goes wrong:** Commercial API uses `ScoreSymbolHandler.handle()` (computes live, per-ticker). Dashboard uses `score_repo.find_all_latest()` (reads stored, all-symbols). The stored data may lag behind or lack sub-scores.
**Why it happens:** The pipeline runs scoring and stores results; dashboard reads stored results. If storage doesn't include sub-scores, dashboard can't show them.
**How to avoid:** Verify that `score_repo.save()` stores sub-score details (technical_sub_scores, sentiment sub-scores) and that `find_all_latest()` retrieves them.

## Code Examples

### Extending QuantScoreResponse Schema
```python
# commercial/api/schemas/score.py
class SubScoreEntry(BaseModel):
    """Individual sub-score entry for technical/sentiment breakdown."""
    name: str
    value: Optional[float] = None  # 0-100 normalized, null if unavailable
    raw_value: Optional[float] = None

class QuantScoreResponse(BaseModel):
    symbol: str
    composite_score: float = Field(ge=0, le=100)
    risk_adjusted_score: float = Field(ge=0, le=100)
    safety_passed: bool
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    sentiment_confidence: Optional[str] = None  # "NONE"/"LOW"/"MEDIUM"/"HIGH"
    sub_scores: Optional[dict] = None  # Keep for backward compat
    technical_sub_scores: Optional[list[SubScoreEntry]] = None
    sentiment_sub_scores: Optional[list[SubScoreEntry]] = None
    disclaimer: str = DISCLAIMER
```

### Extending RegimeCurrentResponse with Probabilities
```python
# commercial/api/schemas/regime.py
class RegimeCurrentResponse(BaseModel):
    regime_type: str
    confidence: float = Field(ge=0, le=1)
    is_confirmed: bool
    confirmed_days: int
    vix: Optional[float] = None
    adx: Optional[float] = None
    yield_spread: Optional[float] = None
    detected_at: Optional[str] = None
    regime_probabilities: Optional[dict[str, float]] = None  # {"Bull": 0.82, "Bear": 0.05, ...}
    disclaimer: str = DISCLAIMER
```

### Synthetic Regime Probability Computation (Router Layer)
```python
# In commercial/api/routers/regime.py
def _compute_regime_probabilities(regime_type: str, confidence: float) -> dict[str, float]:
    """Compute approximate probability distribution from dominant regime + confidence."""
    regimes = ["Bull", "Bear", "Sideways", "Crisis"]
    remaining = 1.0 - confidence
    per_other = remaining / (len(regimes) - 1) if len(regimes) > 1 else 0.0
    probs = {r: per_other for r in regimes}
    probs[regime_type] = confidence
    return probs
```

### Dashboard RiskQueryHandler Extension
```python
# In src/dashboard/application/queries.py - RiskQueryHandler.handle()
# Add regime_probabilities to the returned dict
regime_probabilities = {}
if regime_obj is not None:
    regime_probabilities = _compute_regime_probabilities(
        regime_obj.regime_type.value, regime_obj.confidence
    )
return {
    # ... existing fields ...
    "regime_probabilities": regime_probabilities,
}
```

### Expandable Signal Row Component
```tsx
// Row click toggles expanded state
<TableRow onClick={() => row.toggleExpanded()} className="cursor-pointer">
  {/* existing columns */}
</TableRow>
{row.getIsExpanded() && (
  <TableRow>
    <TableCell colSpan={columns.length}>
      <ScoreBreakdownPanel scores={row.original} />
    </TableCell>
  </TableRow>
)}
```

### HMM Probability Bars Component
```tsx
function RegimeProbabilities({ probabilities, dominant }: {
  probabilities: Record<string, number>;
  dominant: string;
}) {
  return (
    <div className="space-y-2">
      {Object.entries(probabilities).map(([regime, prob]) => (
        <div key={regime} className={cn(
          "flex items-center gap-3 rounded-md p-1",
          regime === dominant && "ring-1 ring-primary font-bold"
        )}>
          <span className="w-20 text-sm">{regime}</span>
          <Progress value={prob * 100} className="flex-1" />
          <span className="w-12 text-right text-sm font-mono">
            {Math.round(prob * 100)}%
          </span>
        </div>
      ))}
    </div>
  );
}
```

## State of the Art

| Area | Current State | Phase 28 Change |
|------|---------------|-----------------|
| QuantScore response | `sub_scores` as untyped dict (tech only) | Add typed `technical_sub_scores` + `sentiment_sub_scores` + `sentiment_confidence` |
| Regime response | Dominant regime + confidence only | Add `regime_probabilities` dict for all 4 regimes |
| Signals response | `methodology_votes` (direction + score per method) | Methodology votes already serve as reasoning trace -- verify and document |
| Dashboard signals | Flat table with composite/risk_adjusted/strategy/signal | Expandable rows: click to see F/T/S + individual sub-scores |
| Dashboard risk/regime | RegimeBadge (name only) | + Probability bars per regime with dominant highlighted |
| Dashboard nav | 4 pages (Overview/Signals/Risk/Pipeline) | + Performance page (5th, empty-state shell) |
| Dashboard query handlers | Return composite scores only | Extend to return sub-score breakdowns |

## Open Questions

1. **Score Repository Details Retrieval**
   - What we know: `score_repo.save(symbol, composite, details=details)` stores sub-score details. `find_all_latest()` returns `dict[str, CompositeScore]`.
   - What's unclear: Does `find_all_latest()` also return the details dict, or only the CompositeScore VO? The dashboard needs sub-scores.
   - Recommendation: Check `IScoreRepository` implementation. If details are not retrievable, extend the repo interface.

2. **Regime Probability Computation Method**
   - What we know: No actual HMM (hmmlearn) in codebase. Rule-based detection with single (RegimeType, confidence) output.
   - Resolution: Compute synthetic probabilities by assigning confidence to dominant regime and distributing remainder. This is presentation-layer, consistent with architecture.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (Python API/dashboard tests), biome (dashboard lint) |
| Config file | pyproject.toml (pytest section) |
| Quick run command | `pytest tests/unit/test_api_v1_quantscore.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | QuantScore returns 3-axis sub-scores | unit | `pytest tests/unit/test_api_v1_quantscore.py -x` | Exists -- extend |
| API-02 | Regime returns per-regime probabilities | unit | `pytest tests/unit/test_api_v1_regime.py -x` | Exists -- extend |
| API-03 | Signals returns reasoning traces | unit | `pytest tests/unit/test_api_v1_signals.py -x` | Exists -- extend |
| API-04 | JWT auth rejects invalid tokens | unit | `pytest tests/unit/test_api_v1_quantscore.py::TestQuantScoreEndpoint::test_no_jwt_returns_401_or_403 -x` | Exists |
| API-05 | Rate limiting per tier | unit | (covered by existing tests) | Exists |
| API-06 | Disclaimer in all responses | unit | (covered by existing tests) | Exists |
| API-07 | OpenAPI docs auto-generated | smoke | `pytest tests/unit/test_api_v1_quantscore.py -x` (schema validation) | Covered |
| DASH-01 | Signals page shows sub-scores | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | Exists (pycache) -- extend |
| DASH-02 | Performance page exists | manual-only | Dashboard UI inspection | N/A |
| DASH-03 | Real data displayed | e2e | Manual: start servers, verify data | Manual |
| DASH-04 | Regime probability bars | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | Extend for regime_probabilities |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_api_v1_quantscore.py tests/unit/test_api_v1_regime.py tests/unit/test_api_v1_signals.py -x`
- **Per wave merge:** `pytest tests/ -x && cd dashboard && npx biome check .`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Extend `tests/unit/test_api_v1_quantscore.py` -- add test for `sentiment_sub_scores`, `sentiment_confidence`, `technical_sub_scores` (typed list)
- [ ] Extend `tests/unit/test_api_v1_regime.py` -- add test for `regime_probabilities` dict (4 regimes, sums to ~1.0)
- [ ] Extend `tests/unit/test_api_v1_signals.py` -- add test verifying methodology_votes serves as reasoning trace
- [ ] Extend dashboard query handler tests for sub-score data in signals response

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `commercial/api/` (routers, schemas, middleware, dependencies)
- Direct codebase analysis: `src/dashboard/presentation/` (app.py, api_routes.py)
- Direct codebase analysis: `src/dashboard/application/queries.py` (SignalsQueryHandler, RiskQueryHandler)
- Direct codebase analysis: `src/scoring/application/handlers.py` (handler result dict structure)
- Direct codebase analysis: `src/regime/` (detection service, handler, value objects)
- Direct codebase analysis: `dashboard/src/` (pages, hooks, components, types)
- Direct codebase analysis: `dashboard/next.config.ts` (rewrite proxy configuration)

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions from user discussion session
- REQUIREMENTS.md for requirement definitions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed and in use, no new deps
- Architecture: HIGH - two-app architecture confirmed by codebase, extending existing patterns
- Pitfalls: HIGH - identified from direct code analysis (sentiment sub-scores missing from handler dict, score_repo details retrieval unknown)

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable -- no external dependency changes expected)
