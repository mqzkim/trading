# Feature Research: v1.3 Bloomberg Dashboard

**Domain:** Bloomberg terminal-style trading dashboard (React + Next.js)
**Researched:** 2026-03-14
**Confidence:** HIGH (Bloomberg UX patterns well-documented, existing backend data verified, React ecosystem mature)

**Scope:** This document covers ONLY the Bloomberg-style dashboard features for v1.3. The existing HTMX dashboard (v1.2) provides working data endpoints and SSE event infrastructure. v1.3 replaces the presentation layer while reusing backend data queries.

**Existing backend data available (verified from `dashboard/application/queries.py`):**
- Portfolio: positions, market values, P&L, composite scores, stop/target prices
- Equity curve: cumulative P&L over time with regime period overlays
- Signals: composite scores, risk-adjusted scores, strategies, BUY/SELL directions, strength
- Risk: drawdown percentage + level (normal/warning/critical), sector weights, position count/limits, regime
- Pipeline: run history with stage results, next scheduled time, run/halt status
- Approval: strategy approval status, daily budget (spent/limit/remaining), review queue
- SSE events: PipelineCompleted, PipelineHalted, OrderFilled, DrawdownAlert, RegimeChanged

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any Bloomberg-style trading dashboard must have. Missing these and the product feels like a generic admin panel, not a professional trading interface.

| Feature | Why Expected | Complexity | Backend Dependency | Notes |
|---------|--------------|------------|-------------------|-------|
| Dark theme with high-contrast data | Bloomberg = black background with bright data. Light themes signal "consumer app," not "trading terminal" | LOW | None (CSS only) | Use amber (#FB8B1E), cyan (#4AF6C3), blue (#0068FF), red (#FF433D) on black (#000000). Monospace fonts for all numerical data |
| Data-dense table views | Professionals need 20-50 rows visible at once without scrolling. The existing HTMX dashboard wastes too much whitespace | MEDIUM | Existing position/score/signal data | Compact row height (24-28px), minimal padding, no card wrappers around tables. AG Grid or TanStack Table |
| Color-coded P&L and price changes | Green = profit/up, Red = loss/down is universal in finance. Amber = neutral/unchanged | LOW | Existing P&L data | Apply to: position P&L, score changes, signal direction, drawdown levels. Include brightness variation for magnitude |
| Real-time data streaming | The existing SSE bridge already pushes events. The React frontend must consume and render them without full page reload | MEDIUM | Existing SSE endpoint at `/dashboard/events` | Use EventSource API or React hook. Update specific components on event type (OrderFilled -> holdings, DrawdownAlert -> gauge) |
| Navigation sidebar with page switching | Users expect instant page switching without full reloads. Bloomberg has four core panels; we have four pages | LOW | None | Tab-based or sidebar navigation. Active page highlighted. Consider keyboard shortcuts (1-4 for pages) |
| Holdings/positions table with live P&L | Core of any portfolio view. Must show: symbol, qty, entry, current, P&L ($), P&L (%), stop, target, score | MEDIUM | `OverviewQueryHandler.handle()` provides positions with all fields | Sort by any column. Color-code P&L. Flash/highlight on update via SSE |
| Equity curve chart | Time-series chart showing portfolio value over time. Already exists in HTMX with Plotly | MEDIUM | `_build_equity_curve()` returns dates + values | Replace Plotly with TradingView Lightweight Charts for consistent trading look. Overlay regime periods as colored bands |
| Drawdown gauge with tier indicators | Visual gauge showing current drawdown with 10%/15%/20% tier markers. Already exists in HTMX | LOW | `RiskQueryHandler` provides drawdown_pct and drawdown_level | Color transitions: green (0-10%), yellow (10-15%), red (15-20%), flashing red (>20%) |
| Sector exposure visualization | Donut or treemap showing portfolio allocation by sector with 25% limit line | LOW | `RiskQueryHandler` provides sector_weights | Existing Plotly donut works; convert to a more compact bar chart for data density |
| Pipeline run status and history | Show recent pipeline runs with stage-by-stage status. Already exists in HTMX | LOW | `PipelineQueryHandler` provides pipeline_runs with stages | Compact timeline view instead of table. Status dots per stage |
| Scoring heatmap table | Table of all scored symbols with color-coded composite/risk-adjusted scores | MEDIUM | `SignalsQueryHandler` provides scores with composite, risk_adjusted, strategy, signal | True heatmap coloring: gradient from red (0) through amber (50) to green (100). Sortable columns |
| Approval status panel | Show active strategy approval parameters, suspension state, daily budget usage | LOW | `PipelineQueryHandler` provides approval_status + daily_budget | Compact card with key/value pairs. Budget bar with spent/remaining |
| Review queue with approve/reject actions | List pending trade reviews with one-click approve/reject. Already exists in HTMX | LOW | Existing `/review/approve` and `/review/reject` POST endpoints | Inline action buttons. Flash confirmation on action |
| Responsive layout (desktop-first) | Must work on 1920x1080 minimum. Bloomberg runs on dedicated monitors; our dashboard runs in a browser | MEDIUM | None | Desktop-first design. Min-width 1280px. No mobile layout needed (trading is desktop-only) |

### Differentiators (Competitive Advantage)

Features that elevate the dashboard from "dark-themed admin panel" to "feels like a real terminal." Not required for launch but significantly increase perceived quality.

| Feature | Value Proposition | Complexity | Backend Dependency | Notes |
|---------|-------------------|------------|-------------------|-------|
| Command palette (Bloomberg-style) | Bloomberg's command bar is its most iconic feature. Type ticker or function name, autocomplete shows options. Replaces mouse navigation | HIGH | None (frontend routing + data lookup) | Trigger with `/` or `Cmd+K`. Commands: navigate pages, search symbols, trigger pipeline run, toggle approval. Autocomplete with fuzzy matching |
| Multi-panel workspace layout | Bloomberg Launchpad lets users arrange components freely. Draggable, resizable panels let users build their own layouts | HIGH | None (layout management is frontend-only) | Use react-grid-layout. Save layout to localStorage. Preset layouts: "Overview," "Analysis," "Risk Monitor," "Pipeline Control" |
| Linked security context | Clicking a symbol in any table sets the "active security" across all panels. Chart, score details, and signal data all update to show that symbol | HIGH | Need per-symbol detail endpoints or client-side filtering | Bloomberg calls this "security groups." Reduces clicks dramatically. Color-coded context indicator |
| Keyboard navigation | Bloomberg is keyboard-first. Arrow keys navigate tables, Enter opens detail, Esc closes, number keys switch pages | MEDIUM | None | Tab between panels, arrow keys within tables, Enter to drill down, Esc to go back. Show keyboard shortcut hints |
| TradingView candlestick charts | Professional-grade financial charts with OHLCV candles, volume bars, and technical indicator overlays | HIGH | Need OHLCV price data endpoint (not currently in dashboard queries) | TradingView Lightweight Charts library. Requires adding a price data API route that queries DuckDB OHLCV tables |
| Ticker tape header | Scrolling horizontal bar showing key symbols with last price and daily change. Bloomberg and CNBC use this pattern | MEDIUM | Need real-time or recent price data for watched symbols | Configurable symbol list. Color-coded changes. Click to set active security |
| Flash/pulse animation on data update | When a price or P&L value changes via SSE, briefly flash the cell background (green for increase, red for decrease) | MEDIUM | Existing SSE events | 300ms CSS transition. Professional terminals use this for visual attention. Must not be distracting -- subtle pulse, not blinking |
| System status bar | Bottom bar showing: connection status (SSE connected/disconnected), market status (open/closed/pre-market), execution mode (LIVE/PAPER), last data update timestamp | LOW | Existing execution_mode + SSE connection state | Bloomberg always shows system status. Builds trust that data is current |
| Alert/notification toast system | Pop-up notifications for critical events: order filled, drawdown tier change, regime change, pipeline completion | MEDIUM | Existing SSE events (OrderFilled, DrawdownAlert, RegimeChanged, PipelineCompleted) | Stack in bottom-right. Auto-dismiss after 5s. Color-coded by severity. Sound for critical (drawdown tier 2+) |
| Mini-sparklines in tables | Tiny inline charts (30px tall) showing 30-day price trend next to each symbol in holdings/scoring tables | MEDIUM | Need historical price data per symbol | High data density pattern. Bloomberg shows these inline. Can use TradingView Lightweight Charts micro mode |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem desirable but create problems for this specific project -- a personal trading system with daily granularity, not a high-frequency trading desk.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time tick-by-tick streaming | "Bloomberg does real-time" | This system operates on daily granularity for mid-term holding. Sub-second updates add complexity (WebSocket server, price feed subscription, client-side throttling) with zero value for 2-week+ hold periods. The system explicitly forbids day trading | Poll every 60 seconds during market hours. Use SSE for domain events (order fills, alerts) which are infrequent |
| Drag-and-drop trade execution | "Click to buy/sell from the dashboard" | The system's core value is deliberate, approval-gated execution. One-click trading bypasses the human-in-the-loop safety constraint. Bloomberg requires confirmation dialogs for orders too | Keep trade execution through the pipeline: generate trade plan -> review queue -> approve/reject. Dashboard is for monitoring and approval, not direct order entry |
| Multiple watchlists with custom categories | "Bloomberg has unlimited watchlists" | Adds significant state management (CRUD for lists, symbol assignment, persistence). The scoring universe is already defined by the pipeline. Adding user-managed lists creates a parallel, unscored tracking system | Single "watchlist" derived from: (1) current positions, (2) active signals, (3) pipeline universe. No user-managed lists -- the system decides what to watch based on scores |
| Chat/messaging system | "Bloomberg Terminal has IB (Instant Bloomberg)" | This is a personal system for one user. No one to chat with. Adding messaging is pure complexity | System log/activity feed showing recent events, decisions, and reasoning traces |
| Mobile-responsive design | "I want to check on my phone" | Bloomberg Terminal is desktop-only for a reason: data density requires screen real estate. Phone screens cannot display the information density needed. Adding responsive breakpoints doubles CSS complexity | Desktop-only (min-width 1280px). For mobile monitoring, use simple push notifications for critical alerts (drawdown, order fills) via a separate lightweight endpoint |
| Custom indicator builder | "Let me define my own technical indicators" | The system uses validated, research-backed indicators (F-Score, Z-Score, M-Score, G-Score). Custom indicators bypass the "verified methodologies only" constraint and add untested signals | Expose existing indicator weights as configurable parameters. The which-indicators decision is made at strategy level, not dashboard level |
| AI/LLM chat overlay | "Ask AI about my portfolio" | Adds LLM integration complexity, cost, and latency. The system already generates reasoning traces and explanations in the scoring/signal pipeline. An AI overlay is a separate product | Display existing reasoning traces prominently: score breakdowns, signal explanations, risk warnings. Make the system's existing intelligence visible, not hidden behind a chat |
| Paper/live mode toggle in dashboard | "Switch between paper and live from the UI" | Extremely dangerous. Accidental mode switches could execute real trades. The existing system requires explicit CLI configuration with confirmation | Show current mode prominently (red LIVE banner, green PAPER banner). Mode switching stays in CLI/config only. Dashboard is read-heavy, not config-heavy |

---

## Feature Dependencies

```
[Dark Theme + Design System]
    |
    +--requires--> [Data-Dense Tables]
    |                  |
    |                  +--requires--> [Color-Coded P&L]
    |                  +--requires--> [Scoring Heatmap]
    |                  +--enhances--> [Flash Animation on Update]
    |
    +--requires--> [Navigation Sidebar]
    |                  +--enhances--> [Keyboard Navigation (1-4 page switch)]
    |
    +--requires--> [Real-Time SSE Consumption]
                       |
                       +--enables--> [Flash Animation on Update]
                       +--enables--> [Alert Toast System]
                       +--enables--> [Pipeline Status Updates]

[Holdings Table]
    +--requires--> [Data-Dense Tables]
    +--requires--> [Color-Coded P&L]
    +--enhances--> [Mini-Sparklines]

[Equity Curve Chart]
    +--requires--> [TradingView Lightweight Charts]
    +--enhances--> [Regime Period Overlays]

[TradingView Candlestick Charts]
    +--requires--> [OHLCV Price Data Endpoint] (NEW backend work)
    +--requires--> [TradingView Lightweight Charts]
    +--enhances--> [Linked Security Context]

[Command Palette]
    +--requires--> [Navigation Sidebar] (needs page routing)
    +--enhances--> [Keyboard Navigation]
    +--enhances--> [Linked Security Context]

[Multi-Panel Layout]
    +--requires--> [react-grid-layout]
    +--requires--> all individual panels/widgets exist first
    +--enhances--> [Linked Security Context]

[Linked Security Context]
    +--requires--> [Holdings Table] + [Scoring Table] + at least one chart
    +--conflicts--> [building it too early before panels exist]

[Ticker Tape Header]
    +--requires--> price data for symbols (same as sparklines)
    +--enhances--> [Linked Security Context] (click symbol to select)
```

### Dependency Notes

- **Dark Theme must come first:** Every subsequent component inherits the design system. Building components on a light theme then switching creates rework.
- **Data-Dense Tables are foundational:** Holdings, scoring, pipeline history, review queue all need the same table component. Build one table primitive, reuse everywhere.
- **SSE consumption enables reactive features:** Flash animations, toasts, and live status updates all depend on the React SSE hook. Build this early.
- **TradingView Charts require OHLCV data endpoint:** The existing backend queries return derived data (scores, signals, P&L) but NOT raw OHLCV price history. A new API route querying DuckDB's OHLCV tables is needed for candlestick charts.
- **Command palette and multi-panel layout are late-stage:** These require all individual components to exist first. They orchestrate existing components, they don't create new data views.
- **Linked security context conflicts with building it too early:** You need at least 3 panels that can show per-symbol data before linking them adds value.

---

## MVP Definition

### Launch With (v1.3.0)

Minimum viable Bloomberg-style dashboard -- replaces HTMX with React while looking and feeling professional.

- [ ] **Design system + dark theme** -- Bloomberg color palette, monospace number fonts, compact spacing. This is the foundation everything else inherits
- [ ] **Holdings/positions table** -- Data-dense table with symbol, qty, entry, current, P&L ($ and %), stop, target, composite score. Color-coded P&L. Sortable columns
- [ ] **Equity curve with TradingView Lightweight Charts** -- Replace Plotly. Line chart with regime period colored bands overlay
- [ ] **Scoring heatmap table** -- All scored symbols with gradient-colored composite/risk-adjusted scores. Sortable. Signal direction indicator
- [ ] **Drawdown gauge + risk summary** -- Current drawdown with tier markers (10/15/20%). Sector exposure bars. Position count indicator
- [ ] **Pipeline status + run history** -- Compact timeline of recent runs. Stage-by-stage status dots. Next scheduled run
- [ ] **Approval + review queue** -- Current approval parameters. Budget bar. Pending reviews with approve/reject buttons
- [ ] **SSE event consumption** -- React hook consuming `/dashboard/events`. Updates holdings on OrderFilled, drawdown on DrawdownAlert, regime on RegimeChanged, pipeline on PipelineCompleted
- [ ] **Navigation + system status bar** -- Sidebar with 4 pages. Bottom bar with SSE connection status, execution mode badge, last update timestamp
- [ ] **LIVE/PAPER mode banner** -- Prominent red/green banner matching existing behavior

### Add After Validation (v1.3.x)

Features to add once the core dashboard is working and actively used for daily trading.

- [ ] **Keyboard navigation** -- Arrow keys in tables, 1-4 for page switching, Enter to drill down. Add after using the dashboard daily reveals friction points
- [ ] **Command palette** -- `/` or `Cmd+K` to open. Search symbols, navigate pages, trigger actions. Add after page structure is stable
- [ ] **Alert toast system** -- Pop-up notifications for SSE events. Add after daily use reveals which events actually need attention vs. are noise
- [ ] **Flash animation on data update** -- Cell pulse on value change. Add after SSE consumption is proven reliable
- [ ] **System activity feed** -- Chronological log of pipeline events, order fills, approval changes. Add after event volume is understood

### Future Consideration (v1.4+)

Features to defer until the dashboard has been used in production for at least 2 weeks.

- [ ] **TradingView candlestick charts** -- Requires new OHLCV data endpoint. Defer because the system operates on daily signals, not chart-based discretionary trading. Candlesticks are "nice to look at" but not decision-making tools in this system
- [ ] **Multi-panel workspace layout** -- Draggable/resizable panels with react-grid-layout. Defer because single-user doesn't need customization urgently; fixed layouts work fine
- [ ] **Linked security context** -- Click symbol to update all panels. Defer until multiple per-symbol views exist (chart + detail + signals)
- [ ] **Ticker tape header** -- Scrolling price ticker. Defer because it requires real-time price feed for symbols, which is out of scope for daily-granularity system
- [ ] **Mini-sparklines** -- Inline 30-day price charts. Defer because it requires per-symbol historical price API

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Phase |
|---------|------------|---------------------|----------|-------|
| Dark theme + design system | HIGH | LOW | P1 | v1.3.0 |
| Holdings/positions table | HIGH | MEDIUM | P1 | v1.3.0 |
| Equity curve (TradingView) | HIGH | MEDIUM | P1 | v1.3.0 |
| Scoring heatmap table | HIGH | MEDIUM | P1 | v1.3.0 |
| Drawdown gauge + risk summary | HIGH | LOW | P1 | v1.3.0 |
| Pipeline status + history | MEDIUM | LOW | P1 | v1.3.0 |
| Approval + review queue | MEDIUM | LOW | P1 | v1.3.0 |
| SSE event consumption | HIGH | MEDIUM | P1 | v1.3.0 |
| Navigation + status bar | MEDIUM | LOW | P1 | v1.3.0 |
| LIVE/PAPER mode banner | HIGH | LOW | P1 | v1.3.0 |
| Keyboard navigation | MEDIUM | MEDIUM | P2 | v1.3.x |
| Command palette | MEDIUM | HIGH | P2 | v1.3.x |
| Alert toast system | MEDIUM | MEDIUM | P2 | v1.3.x |
| Flash animation | LOW | MEDIUM | P2 | v1.3.x |
| Activity feed | LOW | MEDIUM | P2 | v1.3.x |
| Candlestick charts | MEDIUM | HIGH | P3 | v1.4+ |
| Multi-panel layout | LOW | HIGH | P3 | v1.4+ |
| Linked security context | MEDIUM | HIGH | P3 | v1.4+ |
| Ticker tape header | LOW | HIGH | P3 | v1.4+ |
| Mini-sparklines | LOW | MEDIUM | P3 | v1.4+ |

**Priority key:**
- P1: Must have for v1.3.0 launch -- these replace existing HTMX functionality with Bloomberg styling
- P2: Should have -- add once core dashboard is stable and daily usage reveals needs
- P3: Nice to have -- these require new backend work or are premature for single-user system

---

## Competitor Feature Analysis

| Feature | Bloomberg Terminal | TradingView | Existing HTMX Dashboard | Our v1.3 Approach |
|---------|-------------------|-------------|------------------------|-------------------|
| Theme | Black + amber/orange, ultra-dense | Dark + light toggle, modern | Light (Tailwind default), spacious | Black + amber/cyan/blue, dense like Bloomberg |
| Data tables | Monospace, 50+ rows visible, column resize | Not table-focused (chart-first) | Standard HTML tables, 10-15 rows | TanStack Table or AG Grid, 30+ rows, monospace numbers |
| Charts | Proprietary, integrated with data | Best-in-class candlestick + indicators | Plotly equity curve only | TradingView Lightweight Charts for equity + future candlestick |
| Real-time | Sub-second tick data | Sub-second tick data | SSE domain events (infrequent) | SSE domain events (keep existing pattern, sufficient for daily system) |
| Navigation | Command line + keyboard + 4 panels | Tab bar + sidebar | Sidebar with 4 pages | Sidebar with 4 pages + future command palette |
| Layout | Launchpad: fully customizable panels | Fixed layouts with chart focus | Fixed single-column | Fixed grid layout (v1.3) -> customizable panels (v1.4) |
| Keyboard | Keyboard-first with color-coded keys | Some keyboard shortcuts | None | Incremental: page switching first, then full keyboard nav |
| Alerts | Integrated alert + messaging system | Chart-based alerts, email/push | SSE partial updates | Toast notifications from SSE events |
| Watchlist | Multiple custom watchlists | Multiple watchlists with columns | No explicit watchlist | Derived from positions + signals (no user-managed lists) |
| Approval workflow | N/A (execution platform) | N/A (charting platform) | HTMX forms with partial swap | React forms with optimistic updates |
| Risk visualization | Comprehensive risk analytics | Basic portfolio metrics | Drawdown gauge + sector donut | Drawdown gauge + sector bars + position limits + regime badge |

---

## Bloomberg-Specific Design Patterns to Implement

### Pattern 1: Information Density Hierarchy

Bloomberg uses three density levels within a single screen:
1. **Header metrics** (largest) -- 3-5 KPI numbers in large font at top (portfolio value, P&L, drawdown)
2. **Primary data table** (medium) -- The main working table with 20-40 rows of detail
3. **Secondary panels** (compact) -- Supporting information in smaller panels around the main table

Apply this to each page: Overview = KPI cards + Holdings table + Equity chart. Signals = Score summary + Heatmap table + Signal cards.

### Pattern 2: Semantic Color System

Bloomberg's colors are not decorative -- every color carries meaning:
- **Amber (#FB8B1E)**: Default text color, neutral information, labels
- **White (#FFFFFF)**: High-emphasis data (current values, primary numbers)
- **Cyan (#4AF6C3)**: Positive/up indicators (profit, buy signals, increasing scores)
- **Red (#FF433D)**: Negative/down indicators (loss, sell signals, decreasing scores, warnings)
- **Blue (#0068FF)**: Interactive elements (links, buttons, selected states)
- **Gray (#666666)**: De-emphasized information (timestamps, secondary labels)

Never use color for decoration only. Every color must mean something.

### Pattern 3: Monospace Number Alignment

All numerical data uses a monospace font (JetBrains Mono, Fira Code, or SF Mono). This prevents visual "jumping" when numbers update and ensures columns align perfectly. Non-numerical text (labels, symbols) can use a proportional font.

### Pattern 4: Compact Component Boundaries

Bloomberg panels use 1px borders in dark gray (#333333) with no rounded corners, no shadows, and no padding between panels. Every pixel is data space. No card-style elevation. No whitespace "breathing room."

---

## Sources

- [Bloomberg UX: Designing the Terminal for Color Accessibility](https://www.bloomberg.com/ux/2021/10/14/designing-the-terminal-for-color-accessibility/) -- Color system, accessibility considerations
- [Bloomberg Color Palette](https://www.color-hex.com/color-palette/111776) -- Hex values: #000000, #FF433D, #0068FF, #4AF6C3, #FB8B1E
- [Bloomberg Terminal Essentials: IB, Worksheets & Launchpad](https://www.bloomberg.com/professional/insights/technology/bloomberg-terminal-essentials-ib-worksheets-launchpad/) -- Launchpad component system, security groups
- [How Bloomberg Terminal UX Designers Conceal Complexity](https://www.bloomberg.com/company/stories/how-bloomberg-terminal-ux-designers-conceal-complexity/) -- Progressive disclosure, UX patterns
- [Innovating a Modern Icon: How Bloomberg Keeps the Terminal Cutting-Edge](https://www.bloomberg.com/company/stories/innovating-a-modern-icon-how-bloomberg-keeps-the-terminal-cutting-edge/) -- Evolution from 4-panel to tabbed model
- [Bloomberg Keyboard Navigation Guide (SFU)](https://www.lib.sfu.ca/system/files/32883/bloomberg_keyboard.pdf) -- Color-coded keys, GO/Menu/Panel shortcuts
- [React Grid Layout](https://github.com/react-grid-layout/react-grid-layout) -- Draggable/resizable grid for future multi-panel
- [Berg VS Code Theme (Bloomberg-inspired)](https://github.com/jx22/berg) -- Dark background + bright blue/orange accent reference
- [TradingView Ticker Tape Widget](https://www.tradingview.com/widget-docs/widgets/tickers/ticker-tape/) -- Scrolling ticker design reference
- [Hacker News: Bloomberg as information-dense app](https://news.ycombinator.com/item?id=19153875) -- Community discussion on data density best practices
- Existing codebase: `src/dashboard/application/queries.py`, `src/dashboard/presentation/routes.py` -- Backend data availability verified

---
*Feature research for: v1.3 Bloomberg Dashboard*
*Researched: 2026-03-14*
