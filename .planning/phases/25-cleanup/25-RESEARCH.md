# Phase 25: Cleanup - Research

**Researched:** 2026-03-14
**Domain:** Legacy code removal (HTMX/Jinja2 templates, Plotly dependency)
**Confidence:** HIGH

## Summary

Phase 25 is a pure deletion/cleanup phase. The React dashboard (Phases 21-24) fully replaces the legacy HTMX/Jinja2 dashboard, making the old template routes, HTML files, Plotly chart builders, and associated tests dead code. The scope is well-defined: remove 3 source files, 13 template files, 2 test files, and update 3 files (app.py, queries.py, pyproject.toml).

The key risk is the Plotly usage inside `RiskQueryHandler.handle()` in the application layer (`queries.py`). This file imports `build_drawdown_gauge` and `build_sector_donut` from `charts.py` and embeds the results as `gauge_json` / `donut_json` in the return dict. The JSON API routes (`api_routes.py`) already strip these keys with `.pop()`, confirming they are unused by the React frontend. After removing Plotly calls from `queries.py`, those `.pop()` calls in `api_routes.py` become unnecessary but harmless (popping a non-existent key returns None). They should be cleaned up for clarity.

**Primary recommendation:** Delete legacy files in dependency order -- templates first, then routes.py and charts.py, then update queries.py and app.py, then remove tests and pyproject.toml entries. Verify with `pytest tests/` and `ruff check src/` after each step.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLNP-01 | HTMX/Jinja2 template code is removed | Full inventory of 13 template files, routes.py (342 lines), and app.py import identified. Test file test_dashboard_web.py (30 tests) exercises only HTMX routes and must be removed. |
| CLNP-02 | Plotly dependency is removed | charts.py (139 lines) is the sole Plotly importer. queries.py imports chart builders for gauge_json/donut_json. pyproject.toml line `"plotly>=6.0"` must be removed. test_dashboard_charts.py (5 tests) must be removed. |
</phase_requirements>

## Standard Stack

No new libraries. This phase only removes existing dependencies.

### Dependencies to REMOVE from pyproject.toml

| Library | Current Spec | Reason for Removal |
|---------|-------------|-------------------|
| `plotly>=6.0` | Line 27 | React frontend uses TradingView + CSS charts, not Plotly |
| `jinja2>=3.1` | Line 28 | Template rendering no longer needed (BUT see note below) |

**Jinja2 note:** `edgartools>=5.23.0` (line 23 in pyproject.toml) lists jinja2 as a runtime dependency. Removing jinja2 from explicit deps in pyproject.toml is correct (the project no longer directly uses it), but it will remain installed as a transitive dependency. This is expected and correct.

### Dependencies to KEEP (no change)

| Library | Why |
|---------|-----|
| `sse-starlette>=2.0` | Still used by `api_routes.py` SSE endpoint |
| `fastapi>=0.104` | JSON API routes remain |

## Architecture Patterns

### Files to DELETE (complete removal)

```
src/dashboard/presentation/routes.py          # 342 lines - all HTMX/Jinja2 routes + SSE HTML partial renderer
src/dashboard/presentation/charts.py          # 139 lines - Plotly chart builders (equity, gauge, donut)
src/dashboard/presentation/templates/         # 13 HTML files (entire directory)
  base.html
  overview.html
  signals.html
  risk.html
  pipeline.html
  partials/
    approval_section.html
    drawdown_gauge.html
    holdings_table.html
    kpi_cards.html
    pipeline_run_result.html
    pipeline_status.html
    regime_badge.html
    review_queue_section.html
tests/unit/test_dashboard_web.py              # 30 tests - all test HTMX routes
tests/unit/test_dashboard_charts.py           # 5 tests - all test Plotly chart builders
```

### Files to MODIFY

#### 1. `src/dashboard/presentation/app.py` (lines 15, 83)
- **Remove:** `from src.dashboard.presentation.routes import router` (line 15)
- **Remove:** `app.include_router(router)` (line 83)
- **Keep:** `api_router` import and `app.include_router(api_router)` (lines 14, 84)

#### 2. `src/dashboard/application/queries.py` (line 9, lines 493-507)
- **Remove:** `from src.dashboard.presentation.charts import build_drawdown_gauge, build_sector_donut` (line 9)
- **Remove:** Plotly chart generation in `RiskQueryHandler.handle()`:
  - Lines 493-497: `gauge_json = build_drawdown_gauge(...)` and `donut_json = build_sector_donut(...)`
  - Lines 506-507: `"gauge_json": gauge_json,` and `"donut_json": donut_json,`
- **Important:** This also fixes a DDD violation -- `application/` was importing from `presentation/`

#### 3. `src/dashboard/presentation/api_routes.py` (lines 63-64, 84-86)
- **Remove (optional but recommended):** The `.pop("equity_curve_chart_json", None)` on line 64 and `.pop("gauge_json", None)` / `.pop("donut_json", None)` on lines 85-86. After queries.py no longer produces these keys, popping them is dead code. Remove for clarity.
- **Update docstring:** Remove references to "no HTML partials" and "Plotly chart data" since the HTMX alternative no longer exists.

#### 4. `pyproject.toml` (lines 27-28)
- **Remove:** `"plotly>=6.0",`
- **Remove:** `"jinja2>=3.1",`

### Dependency Order for Safe Removal

```
Step 1: Delete templates/ directory (no code imports these directly)
Step 2: Delete routes.py (depends on templates + charts)
Step 3: Delete charts.py (depends on plotly)
Step 4: Update app.py (remove routes import)
Step 5: Update queries.py (remove charts import)
Step 6: Update api_routes.py (remove dead .pop() calls, update docstrings)
Step 7: Delete test_dashboard_web.py and test_dashboard_charts.py
Step 8: Update pyproject.toml (remove plotly, jinja2)
Step 9: pip install -e . (to reflect dependency changes)
```

### Anti-Patterns to Avoid
- **Leaving orphan imports:** After removing charts.py, check `queries.py` still compiles
- **Breaking the CLI serve command:** The `cli/main.py` serve command calls `create_dashboard_app(ctx)` -- this must still work. It does not reference routes.py directly, only app.py
- **Removing sse-starlette:** The SSE endpoint in api_routes.py still needs this package

## Don't Hand-Roll

Not applicable -- this phase is pure deletion, no new code needed.

## Common Pitfalls

### Pitfall 1: DDD Layer Violation in queries.py
**What goes wrong:** `src/dashboard/application/queries.py` imports from `src/dashboard/presentation/charts.py` -- this is an application-layer importing from presentation-layer, violating the DDD rule.
**Why it happens:** The original HTMX dashboard embedded Plotly chart JSON in query results for template rendering.
**How to avoid:** When removing the import, simply stop generating chart JSON in the query handler. The React frontend builds its own charts.
**Warning signs:** If anyone adds chart-building back to queries.py, the DDD violation returns.

### Pitfall 2: Test Count Regression
**What goes wrong:** Removing 35 tests (30 web + 5 charts) may alarm CI or code coverage metrics.
**Why it happens:** These tests tested the deleted code path. They are not testing the JSON API path.
**How to avoid:** The 17 tests in `test_dashboard_json_api.py` and 6 in `test_dashboard_sse.py` remain and cover the active code paths. Document the test count change.
**Warning signs:** `pytest tests/` should collect 17 fewer tests (52 - 35 = 17 dashboard tests remaining).

### Pitfall 3: Jinja2 Transitive Dependency
**What goes wrong:** Removing `jinja2>=3.1` from pyproject.toml but then finding `import jinja2` fails somewhere.
**Why it happens:** jinja2 is also required by `edgartools`. It will remain installed even without the explicit dependency.
**How to avoid:** The only direct jinja2 usage is in `routes.py` (being deleted). After deletion, no project code imports jinja2. But it stays installed via edgartools.

### Pitfall 4: Stale References in api_routes.py
**What goes wrong:** The `.pop("gauge_json", None)` and `.pop("donut_json", None)` calls in api_routes.py no longer do anything after queries.py stops producing these keys.
**Why it happens:** These were defensive strips for the React frontend. Without the Plotly code, the keys never appear.
**How to avoid:** Remove the dead `.pop()` calls and their associated comments. Keep the endpoint behavior identical (returning the same JSON shape minus keys that no longer exist anyway).

## Code Examples

### app.py After Cleanup
```python
# Source: codebase inspection of src/dashboard/presentation/app.py
"""Dashboard FastAPI app factory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.dashboard.infrastructure.sse_bridge import SSEBridge
from src.dashboard.presentation.api_routes import api_router

logger = logging.getLogger(__name__)

# ... lifespan unchanged ...

def create_dashboard_app(ctx: dict | None = None) -> FastAPI:
    # ... same as before, but WITHOUT:
    # from src.dashboard.presentation.routes import router
    # app.include_router(router)

    app.include_router(api_router)
    return app
```

### queries.py RiskQueryHandler.handle() After Cleanup
```python
# Source: codebase inspection of src/dashboard/application/queries.py
# Remove the import at top:
# from src.dashboard.presentation.charts import build_drawdown_gauge, build_sector_donut

def handle(self) -> dict:
    """Return risk metrics for the risk page."""
    # ... same position/sector/drawdown logic ...

    return {
        "drawdown_pct": drawdown_pct,
        "drawdown_level": drawdown_level,
        "sector_weights": sector_weights,
        "position_count": position_count,
        "max_positions": self.MAX_POSITIONS,
        "regime": regime,
        # gauge_json and donut_json REMOVED
    }
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/test_dashboard_json_api.py tests/unit/test_dashboard_sse.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLNP-01 | HTMX routes no longer exist on the app | smoke | `python3 -c "from src.dashboard.presentation.app import create_dashboard_app; app=create_dashboard_app.__wrapped__ if hasattr(create_dashboard_app,'__wrapped__') else create_dashboard_app; import inspect; src=inspect.getsource(app); assert 'routes' not in src.split('api_routes')[0]"` | N/A (inline check) |
| CLNP-01 | Templates directory does not exist | smoke | `python3 -c "from pathlib import Path; assert not Path('src/dashboard/presentation/templates').exists()"` | N/A |
| CLNP-02 | No Python code imports plotly | smoke | `ruff check src/ --select F401` + `grep -r "import plotly" src/` returns nothing | N/A |
| CLNP-02 | plotly not in pyproject.toml dependencies | smoke | `python3 -c "t=open('pyproject.toml').read(); assert 'plotly' not in t"` | N/A |
| CLNP-01+02 | Remaining JSON API tests pass | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | Exists |
| CLNP-01+02 | Remaining SSE tests pass | unit | `pytest tests/unit/test_dashboard_sse.py -x` | Exists |
| CLNP-01+02 | Full test suite passes | unit | `pytest tests/ -x` | Exists |
| CLNP-01+02 | Type check passes | static | `mypy src/` | N/A |
| CLNP-01+02 | Lint passes | static | `ruff check src/` | N/A |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_dashboard_json_api.py tests/unit/test_dashboard_sse.py -x`
- **Per wave merge:** `pytest tests/ -x && mypy src/ && ruff check src/`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
None -- existing test infrastructure covers all phase requirements. Tests being deleted (test_dashboard_web.py, test_dashboard_charts.py) test the code being removed. Remaining tests (test_dashboard_json_api.py, test_dashboard_sse.py) validate the surviving code paths.

## Complete Inventory

### Files to DELETE (18 files, ~830 lines of code + ~485 lines of tests)

| File | Lines | Content |
|------|-------|---------|
| `src/dashboard/presentation/routes.py` | 342 | All HTMX/Jinja2 page routes + SSE HTML renderer |
| `src/dashboard/presentation/charts.py` | 139 | Plotly chart builders (equity_curve, drawdown_gauge, sector_donut) |
| `src/dashboard/presentation/templates/base.html` | ~80 | Base layout with HTMX CDN, Plotly CDN, nav |
| `src/dashboard/presentation/templates/overview.html` | ~70 | Overview page template |
| `src/dashboard/presentation/templates/signals.html` | ~60 | Signals page template |
| `src/dashboard/presentation/templates/risk.html` | ~50 | Risk page template |
| `src/dashboard/presentation/templates/pipeline.html` | ~80 | Pipeline page template |
| `src/dashboard/presentation/templates/partials/approval_section.html` | ~30 | Approval CRUD partial |
| `src/dashboard/presentation/templates/partials/drawdown_gauge.html` | ~15 | Plotly gauge partial |
| `src/dashboard/presentation/templates/partials/holdings_table.html` | ~25 | Holdings table partial |
| `src/dashboard/presentation/templates/partials/kpi_cards.html` | ~20 | KPI cards partial |
| `src/dashboard/presentation/templates/partials/pipeline_run_result.html` | ~15 | Pipeline run result partial |
| `src/dashboard/presentation/templates/partials/pipeline_status.html` | ~20 | Pipeline status partial |
| `src/dashboard/presentation/templates/partials/regime_badge.html` | ~10 | Regime badge partial |
| `src/dashboard/presentation/templates/partials/review_queue_section.html` | ~25 | Review queue partial |
| `tests/unit/test_dashboard_web.py` | 485 | 30 tests for HTMX routes |
| `tests/unit/test_dashboard_charts.py` | 42 | 5 tests for Plotly charts |

### Files to MODIFY (4 files, ~15 lines changed)

| File | Changes |
|------|---------|
| `src/dashboard/presentation/app.py` | Remove 2 lines (routes import + include_router) |
| `src/dashboard/application/queries.py` | Remove 1 import line + ~8 lines of Plotly chart generation |
| `src/dashboard/presentation/api_routes.py` | Remove 3 `.pop()` lines + update docstring |
| `pyproject.toml` | Remove 2 dependency lines (plotly, jinja2) |

## Open Questions

1. **CLI serve URL path**
   - What we know: `cli/main.py` opens browser to `http://host:port/dashboard/` which is the HTMX route prefix
   - What's unclear: After removing the HTMX router, `/dashboard/` returns 404. The React dashboard runs on a separate Next.js dev server (port 3000).
   - Recommendation: Update the serve command to open `http://host:3000/` instead, or remove the browser-open for now since the React dashboard uses `npm run dev`. This is a minor follow-up, not a blocker for deletion.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `src/dashboard/presentation/routes.py` (342 lines, all HTMX routes)
- Codebase inspection: `src/dashboard/presentation/charts.py` (139 lines, sole Plotly user)
- Codebase inspection: `src/dashboard/presentation/app.py` (routes registration)
- Codebase inspection: `src/dashboard/application/queries.py` (Plotly imports in application layer)
- Codebase inspection: `src/dashboard/presentation/api_routes.py` (JSON API, `.pop()` strip logic)
- Codebase inspection: `pyproject.toml` (dependency declarations)
- `pip3 show jinja2`: Required-by: edgartools (transitive dependency confirmed)
- `pip3 show plotly`: Required-by: (nothing) -- safe to remove entirely
- `pip3 show fastapi`: Does NOT require jinja2 (it is optional for template support)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pure deletion, no new libraries, all files identified via grep/glob
- Architecture: HIGH - complete file inventory with line-by-line analysis of what to change
- Pitfalls: HIGH - DDD violation, transitive deps, and stale references all identified from codebase

**Research date:** 2026-03-14
**Valid until:** N/A (deletion research does not go stale)
