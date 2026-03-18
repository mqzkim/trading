# Phase 28: Commercial API & Dashboard - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Three commercial API products (QuantScore/RegimeRadar/SignalFusion) serve real 3-axis scoring data behind JWT authentication and rate limiting. Dashboard displays all new scoring (technical/sentiment sub-scores) and regime (HMM probabilities) data, and adds a Performance Attribution page shell ready for Phase 29 data.

Excluded from this phase: actual P&L tracking/trade history (Phase 29), new scoring logic changes (Phase 27), broker execution changes.

</domain>

<decisions>
## Implementation Decisions

### API Response Detail Level
- QuantScore endpoint returns: composite_score + fundamental_score + technical_score + sentiment_score + sentiment_confidence + technical_sub_scores (5 indicators) + sentiment_sub_scores (4 sources)
- Response structure: same as current QuantScoreResponse schema — extend sub_scores to include both technical and sentiment breakdowns
- Each sub-score entry: {name, value (0-100 normalized), raw_value}
- Sentiment data unavailable: return `sentiment_score: null` + `sentiment_confidence: "NONE"` — field always present, value nullable
- Do NOT omit sentiment key when data is missing — consumers should not need to check key existence

### API Legal Boundary (carry forward)
- All responses include legal disclaimer auto-appended
- SignalFusion uses informational language: "Bullish"/"Bearish"/"Neutral" (not "BUY"/"SELL")
- No position sizing, stop-loss, or take-profit in commercial API responses

### Signals Page Layout
- Signal rows are expandable: click row → score breakdown panel unfolds below the row
- Breakdown panel shows: F: XX | T: XX | S: XX (confidence label)
- Technical sub-row: RSI / MACD / MA / ADX / OBV (each normalized 0-100)
- Sentiment sub-row: News / Insider / Institutional / Analyst (each normalized 0-100)
- Bloomberg dark theme — same visual language as existing pages

### Sentiment Unavailable (Dashboard)
- When sentiment_confidence = NONE: sentiment sub-row grayed out + "Sentiment data unavailable" label
- Do NOT hide the row — show it in disabled state so the user understands data freshness

### Performance Attribution Page (new page)
- Add as 5th page in dashboard navigation
- Layout: Summary KPI cards (Sharpe / Sortino / Win Rate / Max Drawdown) at top
- Below: Brinson-Fachler 4-level decomposition table (Portfolio / Strategy / Trade / Skill columns)
- Below: Equity Curve chart (TradingView Lightweight Charts — already installed)
- Below: Strategy scorecard (IC vs 0.03 threshold / Kelly efficiency vs 70% threshold)
- Empty state: "No performance data yet — generates after first closed trades" — DO NOT use mock data
- Phase 29 will seed real data; this phase builds the page shell that auto-populates when data arrives

### Regime Dashboard Enhancement
- Location: Risk page — add HMM probability section to existing regime area (no new page)
- Display: horizontal progress bars, one per regime (Bull / Bear / Sideways / Crisis)
- Current dominant regime highlighted with bold border
- Label format: `[████████████████  82%] Bull`
- Data source: regime detection handler already wired; extend response to include per-regime probabilities

### Claude's Discretion
- Exact bar colors for regime probability display (Bloomberg palette preferred)
- Loading skeleton implementation for new dashboard sections
- Error state handling for API timeouts in dashboard BFF

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Commercial API
- `commercial/api/main.py` — FastAPI app setup, middleware, routers registered
- `commercial/api/routers/quantscore.py` — QuantScore router (extend sub_scores mapping)
- `commercial/api/routers/regime.py` — RegimeRadar router (extend with per-regime probabilities)
- `commercial/api/routers/signals.py` — SignalFusion router + legal boundary comments
- `commercial/api/schemas/score.py` — QuantScoreResponse schema (extend for 3-axis)
- `commercial/api/dependencies.py` — DI wiring for handlers

### Dashboard
- `dashboard/src/app/(dashboard)/` — 4 existing pages (overview, signals, risk, pipeline)
- `dashboard/src/app/(dashboard)/signals/` — Signals page to extend with expandable sub-scores
- `dashboard/src/app/(dashboard)/risk/` — Risk page to extend with HMM probability bars

### Scoring (Phase 27 output — read before planning)
- `src/scoring/` — 3-axis scoring domain; verify what data ScoreSymbolCommand now returns
- `src/regime/` — Regime detection domain; verify HMM probability output format

### Requirements
- `.planning/REQUIREMENTS.md` §API-01 through API-07, DASH-01 through DASH-04

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `QuantScoreResponse` schema: already has `fundamental_score`, `technical_score`, `sentiment_score` (Optional) — extend, don't replace
- `sub_scores: Optional[dict]` field exists — extend to support both technical and sentiment sub-score arrays
- `commercial/api/middleware/rate_limit.py` + `dependencies.py` — auth/rate-limiting fully wired, no changes needed
- TradingView Lightweight Charts: already installed in dashboard (used in overview equity curve)
- Bloomberg OKLCH dark theme + shadcn/ui: established design system — reuse existing components

### Established Patterns
- DDD handlers via `Depends()`: scoring, regime, signals all follow same dependency injection pattern
- BFF proxy architecture: dashboard → Next.js API routes → FastAPI backend
- SSE real-time updates: already wired for pipeline/portfolio; can extend for scoring updates
- Legal DISCLAIMER constant in `commercial/api/schemas/common.py` — auto-appended to all responses

### Integration Points
- Signals page: extend existing signal rows with expandable panel (no new route needed)
- Risk page: add HMM probability bars to existing regime section
- Performance page: new route `dashboard/src/app/(dashboard)/performance/page.tsx`
- Dashboard nav: add "Performance" link to layout navigation

</code_context>

<specifics>
## Specific Ideas

- Signals page expandable rows: similar to Bloomberg terminal "drill-down" — click row to expand inline, not modal
- Regime probability bars: horizontal bars with percentage, dominant regime highlighted — exact style from discussion preview
- Performance page empty state: "No performance data yet — generates after first closed trades" — minimalist, no mock data

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 28-commercial-api-dashboard*
*Context gathered: 2026-03-18*
