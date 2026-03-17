# Phase 28: Commercial API & Dashboard - Research

**Researched:** 2026-03-18
**Domain:** FastAPI commercial endpoints + Next.js dashboard enhancement
**Confidence:** HIGH

## Summary

Phase 28 extends an already-operational commercial API (FastAPI with JWT auth, rate limiting, 3 product routers) and an existing Next.js dashboard (4 pages, Bloomberg dark theme, shadcn/ui). The work is primarily data-plumbing: the scoring handler already returns technical sub-scores (5 indicators) and sentiment sub-scores (4 sources) from Phase 27 -- this phase surfaces them through the API response schemas and dashboard UI.

The API side requires: (1) extending `QuantScoreResponse` to include sentiment sub-scores alongside existing technical sub-scores, (2) extending `RegimeCurrentResponse` with per-regime HMM probabilities, (3) adding reasoning traces to `SignalResponse`, and (4) verifying all existing auth/rate-limit/disclaimer infrastructure works unchanged. The dashboard side requires: (1) expandable signal rows with F/T/S sub-score breakdown, (2) HMM probability bars in the Risk page regime section, (3) a new Performance Attribution page shell (empty state, no mock data), and (4) ensuring real data flows end-to-end.

**Primary recommendation:** This is a presentation-layer-only phase. No domain logic changes. Extend schemas, map handler data, add dashboard components. All infrastructure (auth, rate-limit, proxy) is already wired.

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
| API-01 | QuantScore endpoint returns composite score with sub-component breakdown | Extend `QuantScoreResponse` schema + router mapping; handler already returns `technical_sub_scores` and sentiment VO fields |
| API-02 | RegimeRadar endpoint returns current regime with probability and indicators | Extend `RegimeCurrentResponse` with `regime_probabilities` dict; compute from detection service scores |
| API-03 | SignalFusion endpoint returns consensus signal with reasoning trace | `SignalResponse` already returns methodology_votes; add `reasoning_traces` field mapping from handler data |
| API-04 | JWT authentication with API key management | ALREADY COMPLETE -- auth router, JWT decode, API key CRUD all wired and tested |
| API-05 | Rate limiting per tier (free/basic/pro) | ALREADY COMPLETE -- slowapi with tier extraction from JWT claims |
| API-06 | Legal disclaimer auto-included in all responses | ALREADY COMPLETE -- DISCLAIMER constant auto-set as default field in all response schemas |
| API-07 | OpenAPI/Swagger documentation auto-generated | FastAPI auto-generates at /docs; verify schema descriptions are updated after extensions |
| DASH-01 | Technical and sentiment sub-scores visible on Signals page | Expandable signal rows with F/T/S breakdown; new components consuming extended API data |
| DASH-02 | Performance attribution page added to dashboard | New `/performance` route with empty-state shell; KPI cards, Brinson table, equity curve, scorecard |
| DASH-03 | Real data displayed across all pages | End-to-end verification that dashboard hooks fetch real backend data through proxy rewrite |
| DASH-04 | Regime detection enhanced view with HMM probabilities | Horizontal progress bars per regime in Risk page; data from extended regime endpoint |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| FastAPI | existing | Commercial API framework | Already wired with routers, middleware |
| Pydantic v2 | existing | Response schemas | BaseModel for all responses |
| PyJWT | existing | JWT auth | Decode in dependencies.py |
| slowapi | existing | Rate limiting | Tier-based, per-user |
| Next.js | 16.1.6 | Dashboard framework | Rewrite proxy to FastAPI |
| React | 19.2.3 | UI library | |
| @tanstack/react-query | ^5.90.21 | Data fetching | All hooks use useQuery |
| @tanstack/react-table | ^8.21.3 | Data tables | Scoring table on Signals page |
| lightweight-charts | ^5.1.0 | Equity curve chart | TradingView charts, already used in overview |
| shadcn/ui | ^4.0.6 | Component library | Cards, badges, tables, progress bars |
| tailwindcss | ^4 | Styling | Bloomberg OKLCH dark theme |

### No New Dependencies Needed
All required functionality is covered by existing packages. The `progress.tsx` component from shadcn/ui is already installed and perfect for HMM probability bars.

## Architecture Patterns

### Current Architecture (do not change)
```
Dashboard (Next.js :3000)
  └─ /api/* → rewrite proxy → FastAPI (:8000)
       └─ /api/v1/quantscore/{ticker}  → ScoreSymbolHandler
       └─ /api/v1/regime/current       → DetectRegimeHandler
       └─ /api/v1/signals/{ticker}     → GenerateSignalHandler
       └─ /api/v1/auth/*               → JWT/API key management

Dashboard hooks (useSignals, useRisk, etc.)
  └─ fetch('/api/v1/dashboard/signals') → proxy → FastAPI
```

### Pattern 1: Schema Extension (API side)
**What:** Add new fields to existing Pydantic response models
**When to use:** All API-01, API-02, API-03 changes
**Key rule:** Add fields as `Optional` with defaults to maintain backward compatibility
```python
# Extend QuantScoreResponse
class QuantScoreResponse(BaseModel):
    # ... existing fields ...
    sentiment_confidence: Optional[str] = None  # NEW
    technical_sub_scores: Optional[list[SubScoreEntry]] = None  # NEW (replaces untyped sub_scores dict)
    sentiment_sub_scores: Optional[list[SubScoreEntry]] = None  # NEW
```

### Pattern 2: Expandable Table Row (Dashboard side)
**What:** Table row that expands to show sub-score detail panel
**When to use:** DASH-01 signals page
**Implementation:** Use @tanstack/react-table `getCanExpand()` + custom sub-row rendering. The existing `DataTable` component wraps react-table -- extend it or create a new `ExpandableDataTable` variant.

### Pattern 3: Empty-State Shell Page (Dashboard side)
**What:** Page with full layout structure but displaying "no data yet" when no data exists
**When to use:** DASH-02 performance attribution page
**Key rule:** Never use mock data. Show real components with empty states.

### Anti-Patterns to Avoid
- **Changing domain logic:** This phase is presentation-only. Do not modify scoring services, regime detection, or signal generation.
- **Breaking existing API contracts:** Add fields, never remove or rename. `sub_scores: Optional[dict]` can coexist with new typed fields during migration.
- **Creating Next.js API routes:** The dashboard uses rewrite proxy (next.config.ts), not API routes. Do not create `/app/api/` directories.
- **Mocking data on Performance page:** Empty state only. Phase 29 provides real data.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Progress bars | Custom div+css bars | shadcn `<Progress>` component | Already installed, themed, accessible |
| Expandable table rows | Manual toggle+state | @tanstack/react-table row expansion API | Built-in support, handles keyboard nav |
| Charts | Canvas/SVG from scratch | `lightweight-charts` (already imported) | TradingView quality, already used on overview |
| Loading states | Conditional rendering | `<Skeleton>` component | Already established pattern across all pages |

## Common Pitfalls

### Pitfall 1: Handler Result Key Mismatch
**What goes wrong:** The scoring handler returns `sentiment_score` as a float on the result dict (line 178 of handlers.py), but the SentimentScore VO has `news_score`, `insider_score`, etc. These sub-fields are NOT currently propagated to the handler result dict.
**Why it happens:** Phase 27 added sub-fields to the VO but the handler only extracts `sentiment.value` (not individual sub-scores).
**How to avoid:** In the handler result dict construction, add sentiment sub-scores explicitly:
```python
# Add to handler result dict (around line 183)
"sentiment_sub_scores": [
    {"name": "News", "value": sentiment.news_score, "raw_value": sentiment.news_score},
    {"name": "Insider", "value": sentiment.insider_score, "raw_value": sentiment.insider_score},
    # ... etc
]
```
**Warning signs:** API returns `sentiment_sub_scores: null` even when sentiment data exists.

### Pitfall 2: Regime Probabilities Not Available from Current Handler
**What goes wrong:** The CONTEXT.md asks for per-regime probability bars (Bull/Bear/Sideways/Crisis), but `DetectRegimeHandler.handle()` returns only the dominant regime + confidence. It does NOT return probabilities for all 4 regimes.
**Why it happens:** `RegimeDetectionService.detect()` returns `(RegimeType, confidence)` -- a single regime, not a probability distribution.
**How to avoid:** Compute approximate probabilities from the detection logic's scoring. The `_resolve_ambiguous` method has bull_score/bear_score -- expose these as normalized probabilities. For non-ambiguous cases, set dominant regime to the confidence value and distribute remaining probability.
**Warning signs:** Regime endpoint returns only 1 regime probability instead of 4.

### Pitfall 3: Dashboard Proxy Path Mismatch
**What goes wrong:** Dashboard hooks call `/api/v1/dashboard/signals` but the FastAPI has `/api/v1/quantscore/{ticker}` and `/api/v1/signals/{ticker}`. These are different endpoints.
**Why it happens:** The dashboard currently has a BFF-style aggregation layer that combines multiple FastAPI calls. The hook paths don't match FastAPI paths directly.
**How to avoid:** Check if there's a FastAPI dashboard aggregation router. If not, the dashboard hooks may be calling non-existent endpoints (returning 404 in production) or there's a separate BFF service.
**Warning signs:** Dashboard shows "Backend connection failed" on all pages.

### Pitfall 4: Next.js 16 Rewrite Caching
**What goes wrong:** Next.js caches rewritten responses, stale data shows in dashboard.
**How to avoid:** The existing hooks use `staleTime: 30_000` (30 seconds) which is appropriate. Don't increase this.

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
    sub_scores: Optional[dict] = None  # DEPRECATED - keep for backward compat
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
    regime_probabilities: Optional[dict[str, float]] = None  # NEW: {"Bull": 0.82, "Bear": 0.05, ...}
    disclaimer: str = DISCLAIMER
```

### Expandable Signal Row Component Pattern
```tsx
// Expandable row for signals table -- uses react-table expansion
// Row click toggles expanded state, renders sub-panel below
<TableRow onClick={() => row.toggleExpanded()}>
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

### HMM Probability Bars Component Pattern
```tsx
// Risk page regime section -- horizontal progress bars
function RegimeProbabilities({ probabilities }: { probabilities: Record<string, number> }) {
  return (
    <div className="space-y-2">
      {Object.entries(probabilities).map(([regime, prob]) => (
        <div key={regime} className="flex items-center gap-3">
          <span className="w-20 text-sm">{regime}</span>
          <Progress value={prob * 100} className="flex-1" />
          <span className="w-12 text-right text-sm font-mono">{Math.round(prob * 100)}%</span>
        </div>
      ))}
    </div>
  );
}
```

## State of the Art

| Area | Current State | Phase 28 Change |
|------|---------------|-----------------|
| QuantScore response | Returns sub_scores as untyped dict (tech only) | Add typed technical_sub_scores + sentiment_sub_scores lists |
| Regime response | Returns dominant regime + confidence only | Add regime_probabilities dict for all 4 regimes |
| Signals response | Returns methodology_votes but no reasoning | Consider adding reasoning_traces if handler provides |
| Dashboard signals | Flat table, no sub-scores | Expandable rows with F/T/S breakdown |
| Dashboard risk/regime | Badge showing regime name only | + HMM probability bars per regime |
| Dashboard nav | 4 pages (Overview/Signals/Risk/Pipeline) | + Performance page (5th) |

## Open Questions

1. **Dashboard BFF Aggregation**
   - What we know: Hooks call `/api/v1/dashboard/signals` but FastAPI has `/api/v1/quantscore/{ticker}` and `/api/v1/signals/{ticker}` -- these are per-ticker endpoints, not bulk.
   - What's unclear: Is there a dashboard-specific FastAPI router that aggregates scoring data for all tracked symbols? Or do the hooks just not work currently?
   - Recommendation: Check if there's a `commercial/api/routes/` directory (separate from `routers/`) that handles dashboard aggregation. There IS a `routes/` directory -- investigate before planning.

2. **Regime Probability Computation**
   - What we know: Current `RegimeDetectionService.detect()` returns single (RegimeType, confidence). No HMM library is in use -- the "HMM" is a rule-based state machine.
   - What's unclear: The CONTEXT.md says "enhanced HMM probabilities" but there is no actual HMM (hmmlearn) in the regime detection code. The service uses rule-based detection.
   - Recommendation: Compute synthetic probabilities by scoring all 4 regime types based on indicator values and normalizing to sum=1. This is consistent with the existing architecture. Do NOT add hmmlearn dependency (that's ML-01 in future requirements).

3. **Signal Reasoning Traces (API-03)**
   - What we know: `SignalResponse` has methodology_votes. The handler returns methodology_scores and methodology_directions.
   - What's unclear: What constitutes a "reasoning trace"? The signal handler doesn't currently produce textual reasoning.
   - Recommendation: Use the existing methodology_votes as the reasoning trace -- each vote shows which methodology voted which direction with what score. This satisfies API-03 without domain changes.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (Python API tests), biome (dashboard lint) |
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
| API-05 | Rate limiting per tier | unit | `pytest tests/unit/test_api_v1_rate_limit.py -x` | Exists (in pycache) |
| API-06 | Disclaimer in all responses | unit | `pytest tests/unit/test_api_v1_quantscore.py -x -k disclaimer` | Covered by existing tests |
| API-07 | OpenAPI docs accessible | smoke | `curl -s http://localhost:8000/docs` | Manual -- Wave 0 add |
| DASH-01 | Signals page shows sub-scores | manual-only | Dashboard UI inspection | N/A -- TypeScript component |
| DASH-02 | Performance page exists | manual-only | Dashboard UI inspection | N/A -- new page |
| DASH-03 | Real data displayed | e2e | Start FastAPI + Next.js, verify data flow | Manual |
| DASH-04 | Regime probability bars | manual-only | Dashboard UI inspection | N/A -- TypeScript component |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_api_v1_quantscore.py tests/unit/test_api_v1_regime.py tests/unit/test_api_v1_signals.py -x`
- **Per wave merge:** `pytest tests/ -x && cd dashboard && npx biome check .`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Extend `tests/unit/test_api_v1_quantscore.py` -- add test for sentiment_sub_scores + sentiment_confidence
- [ ] Extend `tests/unit/test_api_v1_regime.py` -- add test for regime_probabilities dict
- [ ] Extend `tests/unit/test_api_v1_signals.py` -- add test for reasoning traces in response
- [ ] Add OpenAPI schema smoke test -- verify /openapi.json includes new fields

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis of `commercial/api/` (routers, schemas, middleware, dependencies)
- Direct codebase analysis of `dashboard/src/` (pages, hooks, components, types)
- Direct codebase analysis of `src/scoring/application/handlers.py` (handler result dict structure)
- Direct codebase analysis of `src/regime/` (detection service, handler, value objects)

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions from user discussion session
- REQUIREMENTS.md for requirement definitions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed and in use
- Architecture: HIGH - extending existing patterns, no new architectural decisions
- Pitfalls: HIGH - identified from direct code analysis, verified handler output structure

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable -- no external dependency changes expected)
