# Phase 20: CI/Test Debt Cleanup - Research

**Researched:** 2026-03-14
**Domain:** Python CI toolchain (mypy, pytest, ruff) -- fixing accumulated type errors, test failures, and lint warnings
**Confidence:** HIGH

## Summary

Phase 20 addresses two explicit success criteria and related CI debt accumulated across phases 11-19. The scope is narrow and fully diagnosable from the current codebase state.

**Bug 1 -- mypy failures:** Running `mypy src/` without `--explicit-package-bases` immediately fails with "Duplicate module named application" because `src/` and four subdirectories (`regime/`, `scoring/`, `signals/`, `shared/`) lack `__init__.py` files. With `--explicit-package-bases`, mypy finds 17 type errors across 10 files. The errors fall into three categories: (a) `object` typed parameters causing `attr-defined` errors (9 errors across order_monitor, safe_adapter, regime handler, trading_stream), (b) type narrowing issues (3 errors: union-attr, assignment), (c) the explicitly called-out `arg-type` error in bootstrap.py:228 where `RegimeType` enum is passed to a method expecting `str`, plus 1 `import-untyped` for requests, plus 1 `assignment` in core/scoring/technical.py.

**Bug 2 -- test_api_routes failures:** All 10 tests fail. The test file was written for the pre-Phase-11 commercial API (flat routes `/score/AAPL`, `/regime`, `/signal/AAPL` with version `1.0.0`). Phase 11 rewrote the API with JWT auth, versioned routes (`/api/v1/quantscore/{ticker}`, `/api/v1/regime/current`, `/api/v1/signals/{ticker}`), and version `1.1.0`. The test file is entirely stale -- it tests an API surface that no longer exists.

**Primary recommendation:** Fix the mypy config (add `explicit_package_bases = true` or add missing `__init__.py` files), resolve all 17 type errors, rewrite test_api_routes.py to match the current v1.1 API surface, and fix 4 ruff lint errors.

## Standard Stack

### Core (Already in Project)
| Tool | Version | Purpose | Config |
|------|---------|---------|--------|
| mypy | >=1.5 | Static type checking | `pyproject.toml [tool.mypy]` |
| pytest | >=7.4 | Test framework | `pyproject.toml [tool.pytest.ini_options]` |
| ruff | >=0.1 | Linter + formatter | `pyproject.toml [tool.ruff]` |

### Current mypy Config (pyproject.toml)
```toml
[tool.mypy]
python_version = "3.11"
strict = false
ignore_missing_imports = true
```

**Key observation:** `ignore_missing_imports = true` suppresses many errors. `strict = false` means no strict mode checks. But `explicit_package_bases` is NOT set, causing the "Duplicate module" blocker.

## Architecture Patterns

### Error Category Analysis

The 17 mypy errors break down into actionable fix categories:

#### Category A: Missing `__init__.py` / Package Resolution (BLOCKER)
**Files affected:** `src/__init__.py`, `src/regime/__init__.py`, `src/scoring/__init__.py`, `src/signals/__init__.py`, `src/shared/__init__.py`
**Error:** "Duplicate module named application" when running `mypy src/`
**Fix options:**
1. Add `explicit_package_bases = true` to `[tool.mypy]` in pyproject.toml -- quick fix, matches how code uses `from src.X import Y`
2. Add missing `__init__.py` files to all 5 directories -- proper fix, also helps other tools
**Recommendation:** Do BOTH. Add `__init__.py` files for correctness and `explicit_package_bases = true` for safety.

#### Category B: `object` Typed Parameters (9 errors)
**Files:** `order_monitor.py`, `safe_adapter.py`, `regime/handlers.py`, `trading_stream.py`
**Pattern:** Constructor params typed as `object` (e.g., `client: object`, `bus: object | None`) then methods like `.get_order_by_id()`, `.publish()`, `.notify()` called on them.
**Root cause:** These were typed loosely to avoid cross-context imports (DDD compliance) or because the actual types come from third-party libraries (alpaca-py).
**Fix:** Use `Protocol` classes or `Any` type instead of `object`. `Protocol` is DDD-compliant (defined in domain layer, implemented in infrastructure).

#### Category C: Type Narrowing (3 errors)
| File | Error | Fix |
|------|-------|-----|
| `signals/application/handlers.py:81` | `dict | None` assigned to `dict` | Add `if` guard or default `{}` |
| `pipeline/domain/services.py:403` | `None` item has no `.get_or_create_today` | Add `assert budget_repo is not None` or `if` check |
| `pipeline/domain/services.py:462` | `None` item has no `.save` | Same pattern |

#### Category D: Specific Type Mismatches (2 errors)
| File | Error | Fix |
|------|-------|-----|
| `bootstrap.py:228` | `RegimeType` passed to `str` param | Change param type to `RegimeType | str` or pass `event.new_regime.value` |
| `core/scoring/technical.py:42` | `float` assigned to `int` variable | Change variable type to `float` |

#### Category E: Missing Stubs (1 error)
| File | Error | Fix |
|------|-------|-----|
| `core/data/client.py:15` | `import-untyped` for requests | Already suppressed by `ignore_missing_imports = true` with `--explicit-package-bases`; or install `types-requests` |

**Note:** The `import-untyped` error for `requests` only appears with `--explicit-package-bases`. The `ignore_missing_imports = true` in pyproject.toml should suppress it once mypy reads the config properly.

#### Category F: `type: ignore` comment mismatch (2 errors)
| File | Error | Fix |
|------|-------|-----|
| `scoring/domain/services.py:85` | Error code "attr-defined" not covered by "type: ignore" comment | The `# type: ignore[union-attr]` should be `# type: ignore[attr-defined]` |
| `regime/application/handlers.py:53` | Same pattern | Same fix |

### Test Failure Analysis

**test_api_routes.py -- 10/10 failing:**

| Test | Failure | Root Cause |
|------|---------|------------|
| `test_health_endpoint` | `1.1.0 != 1.0.0` | Version bumped in Phase 11 |
| 9 other tests | `404 Not Found` | Routes moved: `/score/{sym}` -> `/api/v1/quantscore/{ticker}`, `/regime` -> `/api/v1/regime/current`, `/signal/{sym}` -> `/api/v1/signals/{ticker}` |

The test file is entirely stale. The project already has proper v1.1 API tests:
- `test_api_v1_quantscore.py`
- `test_api_v1_regime.py`
- `test_api_v1_signals.py`
- `test_api_v1_auth.py`
- `test_api_v1_apikeys.py`
- `test_api_v1_rate_limit.py`
- `test_api_v1_infra.py`

**Decision:** The stale `test_api_routes.py` should be rewritten to test the current API surface, OR deleted since the v1.1 test files already provide complete coverage.

### Ruff Lint Errors (4)

| File | Error | Fix |
|------|-------|-----|
| `src/backtest/domain/services.py:8` | F401: unused `math` import | Remove import |
| `src/portfolio/domain/value_objects.py:99` | E402: module-level import not at top | Add `# noqa: E402` (re-export intentional) |
| `src/regime/domain/entities.py:6` | F401: unused `Optional` import | Remove import |
| `src/regime/infrastructure/sqlite_repo.py:7` | F401: unused `timezone` import | Remove import |

3 are auto-fixable with `ruff check --fix`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Protocol types for DDD boundaries | Custom ABC classes | `typing.Protocol` | Runtime-transparent, no import dependency, mypy validates structurally |
| Test client auth | Manual token generation | `conftest_api.py` fixtures | Already exists with `get_auth_headers()`, `get_test_client()` patterns |

## Common Pitfalls

### Pitfall 1: Breaking Existing Tests While Fixing Type Errors
**What goes wrong:** Changing function signatures to fix mypy breaks callers
**Why it happens:** `object` -> `Protocol` changes may alter runtime behavior if isinstance checks exist
**How to avoid:** Run full test suite after each file change; prefer additive fixes (wider types, not narrower)
**Warning signs:** Test failures in unrelated test files

### Pitfall 2: Over-Scoping the Cleanup
**What goes wrong:** Fixing all possible type issues, refactoring for strict mode
**Why it happens:** CI debt tempts "while we're at it" scope creep
**How to avoid:** Phase 20 success criteria are explicit: (1) `mypy src/` zero errors, (2) `test_api_routes.py` all pass. Fix exactly what's needed.
**Warning signs:** Touching files not in the error list

### Pitfall 3: test_api_routes.py Rewrite Over-Engineering
**What goes wrong:** Building elaborate mock infrastructure for the rewritten tests
**Why it happens:** The old tests used complex sys.modules patching
**How to avoid:** The v1.1 API test files (`test_api_v1_*.py`) already demonstrate the correct testing pattern with `conftest_api.py` fixtures. Either: (a) delete test_api_routes.py (coverage already exists), or (b) rewrite to use the same patterns as existing v1.1 tests.

### Pitfall 4: mypy Config -- explicit_package_bases Gotcha
**What goes wrong:** Adding `explicit_package_bases = true` without understanding implications
**Why it happens:** This changes how mypy resolves imports
**How to avoid:** When enabled, mypy uses the current directory as the root, and `src.regime` is treated as a package path from the CWD. This matches the project's import convention (`from src.regime.domain import ...`). Safe to enable.

## Code Examples

### Fix Pattern: `object` -> `Protocol` for DDD-safe typing

```python
# In domain/repositories.py or a protocols.py file
from typing import Protocol

class BrokerClient(Protocol):
    """Structural type for broker API client."""
    def get_order_by_id(self, order_id: str) -> object: ...
    def cancel_order_by_id(self, order_id: str) -> None: ...

class EventBus(Protocol):
    """Structural type for event publishing."""
    def publish(self, event: object) -> None: ...

class Notifier(Protocol):
    """Structural type for notification service."""
    def notify(self, message: str) -> None: ...
```

Then in the class constructor:
```python
# Before
def __init__(self, client: object, bus: object | None = None) -> None:

# After
def __init__(self, client: BrokerClient, bus: EventBus | None = None) -> None:
```

### Fix Pattern: bootstrap.py arg-type

```python
# Before (line 228) -- RegimeType passed to str param
approval_handler.suspend_if_regime_invalid(event.new_regime)

# Fix option A: Pass .value
approval_handler.suspend_if_regime_invalid(event.new_regime.value)

# Fix option B: Widen method signature (already handles enum internally)
def suspend_if_regime_invalid(self, new_regime: str | RegimeType) -> None:
```

Option A is cleanest -- the method docstring already says "Accepts regime as string."

### Fix Pattern: Type narrowing for optional dict access

```python
# Before
budget_repo = handlers.get("budget_repo")
budget = budget_repo.get_or_create_today(...)  # Error: None has no .get_or_create_today

# After
budget_repo = handlers.get("budget_repo")
if budget_repo is None:
    raise RuntimeError("budget_repo not configured")
budget = budget_repo.get_or_create_today(...)
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `pyproject.toml [tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_api_routes.py -x` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC-01 | mypy zero errors | CI check | `mypy src/ --explicit-package-bases` (then just `mypy src/` after config fix) | N/A (tool check) |
| SC-02 | test_api_routes passes | unit | `pytest tests/unit/test_api_routes.py -x` | Exists but stale |

### Sampling Rate
- **Per task commit:** `mypy src/ && pytest tests/unit/test_api_routes.py -x && ruff check src/`
- **Per wave merge:** `pytest tests/ -q && mypy src/`
- **Phase gate:** Full suite green before verify

### Wave 0 Gaps
- [ ] `pyproject.toml [tool.mypy]` -- add `explicit_package_bases = true`
- [ ] `src/__init__.py` -- create empty file
- [ ] `src/regime/__init__.py` -- create empty file
- [ ] `src/scoring/__init__.py` -- create empty file
- [ ] `src/signals/__init__.py` -- create empty file
- [ ] `src/shared/__init__.py` -- create empty file

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `object` type for loose coupling | `Protocol` (PEP 544) | Python 3.8+ | Structural subtyping without import dependency |
| Flat commercial API routes | Versioned `/api/v1/` with JWT auth | Phase 11 (v1.1) | test_api_routes.py became entirely stale |

## Open Questions

1. **Delete or rewrite test_api_routes.py?**
   - What we know: v1.1 API tests (`test_api_v1_*.py`) already exist with complete coverage of the current API surface. `test_api_routes.py` tests a non-existent API.
   - What's unclear: Whether to update `test_api_routes.py` to test current routes (duplicating coverage) or delete it.
   - Recommendation: **Rewrite** to test `/health` endpoint (version check) and basic route registration (routes return non-404). Keep it minimal -- the comprehensive tests are in `test_api_v1_*.py`. This satisfies the success criterion "pytest tests/unit/test_api_routes.py passes all tests" while avoiding duplicate coverage.

2. **Protocol files -- where to place?**
   - What we know: DDD rules say interfaces go in domain layer. Protocol classes define structural types.
   - Recommendation: Add protocols to existing domain layer files (e.g., `src/execution/domain/repositories.py` already has `IBrokerAdapter`). Or use `typing.Any` for the quick-fix approach -- less pure but faster and lower risk.

## Sources

### Primary (HIGH confidence)
- Direct analysis of codebase: `mypy src/ --explicit-package-bases` output (17 errors, 10 files)
- Direct analysis of codebase: `pytest tests/unit/test_api_routes.py` output (10 failures, 10 tests)
- Direct analysis of codebase: `ruff check src/` output (4 errors)
- File inspection: `commercial/api/main.py` (version 1.1.0, route structure)
- File inspection: `tests/unit/test_api_routes.py` (stale tests for pre-v1.1 API)
- File inspection: `src/bootstrap.py:228` (RegimeType vs str arg-type)
- File inspection: Missing `__init__.py` in `src/`, `src/regime/`, `src/scoring/`, `src/signals/`, `src/shared/`
- `.planning/v1.2-MILESTONE-AUDIT.md` -- documents both bugs as pre-existing tech debt

### Secondary (MEDIUM confidence)
- mypy documentation on `explicit_package_bases` -- standard fix for namespace package resolution

## Metadata

**Confidence breakdown:**
- Error diagnosis: HIGH -- all errors reproducible and root-caused from direct tool output
- Fix approach: HIGH -- standard Python typing patterns, well-understood
- Scope: HIGH -- success criteria are binary (zero errors, all tests pass)

**Research date:** 2026-03-14
**Valid until:** Stable (these are bug fixes, not moving-target technology)
