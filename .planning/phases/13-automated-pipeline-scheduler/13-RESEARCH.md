# Phase 13: Automated Pipeline Scheduler - Research

**Researched:** 2026-03-13
**Domain:** Task scheduling, market calendar awareness, pipeline orchestration, fault tolerance
**Confidence:** HIGH

## Summary

Phase 13 requires building a pipeline orchestrator that chains existing handlers (ingest, regime, score, signal, plan, execute) into a single automated daily run, triggered 30 minutes after NYSE market close (16:30 ET). The system must be aware of NYSE trading days (skipping weekends, holidays, early-close days), retry transient failures with exponential backoff, halt execution under dangerous market conditions, support dry-run mode, and persist both run history and schedule state across process restarts.

The two new external dependencies -- APScheduler 3.11.2 (SQLite job persistence via SQLAlchemy) and exchange_calendars 4.13.2 (NYSE calendar with holidays, early closes) -- are mature, well-maintained libraries. The orchestrator itself is a new bounded context (`pipeline/`) that coordinates existing handlers through their established command/handler interfaces, without introducing cross-context coupling. Slack webhook notifications use the already-included `httpx` library.

**Primary recommendation:** Create a `pipeline` bounded context with a `PipelineOrchestrator` that receives the bootstrap context dict and sequentially calls each stage. Use APScheduler `BackgroundScheduler` with `SQLAlchemyJobStore(url='sqlite:///data/scheduler.db')` for scheduling, and `exchange_calendars.get_calendar("XNYS")` for market day checks. Stage-level retry is handled within the orchestrator, not at the scheduler level.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Run timing: 16:30 ET (30 min after market close) daily via APScheduler
- APScheduler misfire_grace_time for process restart recovery
- exchange_calendars library for NYSE calendar (70+ exchanges, early close support)
- Skip weekends/holidays/early-close days with "skipped: holiday" log
- Crisis/drawdown tier>=2: run full analysis (ingest through plan) but halt before execute -- score data keeps accumulating
- ReconciliationService.check_and_halt() runs before every pipeline execution
- Existing positions maintained, only new entry blocked
- Notifier interface + Slack webhook default implementation
- SLACK_WEBHOOK_URL in .env
- Pipeline complete/halt/error notifications via Slack
- Stage-level summary logging: start/end time, success/fail symbol count, error message
- pipeline_runs SQLite table for run history (run_id, start/end, stage results, next schedule)
- Dry-run mode: full pipeline run, Rich table display of order plan, skip order submission
- CLI: `trade pipeline run [--dry-run]` and `trade pipeline status`
- 3 retries + exponential backoff (1s, 2s, 4s)
- Partial ingest failure: continue with successful symbols
- Per-symbol score/signal failure: skip symbol + log, continue rest
- No mid-pipeline resume needed (full re-run, pipeline takes minutes)

### Claude's Discretion
- APScheduler SQLite job store schema design
- pipeline_runs table schema details
- Stage inter-data passing mechanism (memory dict vs events)
- Slack webhook message format
- exchange_calendars integration approach
- Notifier interface design

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PIPE-01 | Daily automated pipeline runs ingest through execute after market close | APScheduler CronTrigger at 16:30 ET, PipelineOrchestrator sequential stage execution, bootstrap context reuse |
| PIPE-02 | Pipeline checks NYSE market calendar and skips weekends, holidays, early-close days | exchange_calendars `XNYS` calendar with `is_session()` and `early_closes` property |
| PIPE-03 | Each pipeline run logs stages completed, symbol counts, errors, and next scheduled run to SQLite | pipeline_runs SQLite table with stage-level JSON column for per-stage metrics |
| PIPE-04 | Dry-run mode executes full pipeline without submitting orders | Boolean flag on PipelineOrchestrator that bypasses SafeExecutionAdapter.submit_order, Rich table output |
| PIPE-05 | Individual pipeline stages retry with exponential backoff on transient failures | tenacity-style retry decorator or manual retry loop (1s, 2s, 4s) wrapping stage calls |
| PIPE-06 | Pipeline auto-halts execution when regime is Crisis or drawdown tier >= 2 | Check RegimeType.CRISIS from regime_handler result + drawdown_level from portfolio after analysis stages, before execute stage |
| PIPE-07 | APScheduler with SQLite job persistence manages schedule across process restarts | SQLAlchemyJobStore with `replace_existing=True` and explicit job ID, misfire_grace_time for late execution |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| APScheduler | 3.11.2 | Job scheduling with persistence | Industry standard for in-process Python scheduling; SQLAlchemy job store for SQLite persistence; CronTrigger for time-based scheduling |
| exchange_calendars | 4.13.2 | NYSE market calendar (holidays, early closes) | 50+ exchange calendars, actively maintained (latest release Mar 2025), covers 2026 holidays |
| httpx | >=0.25 (already installed) | Slack webhook HTTP POST | Already in project dependencies; async-capable for future use |
| SQLAlchemy | (APScheduler dependency) | Job store ORM backend | Auto-installed with APScheduler[sqlalchemy]; used only by APScheduler internals |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rich | >=13.0 (already installed) | Dry-run output tables, pipeline status display | CLI output formatting for `pipeline run --dry-run` and `pipeline status` |
| typer | >=0.9 (already installed) | CLI subcommands | Adding `pipeline run` and `pipeline status` commands |
| pydantic-settings | >=2.0 (already installed) | New settings fields | SLACK_WEBHOOK_URL, PIPELINE_SCHEDULE_TIME configuration |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| exchange_calendars | pandas_market_calendars | pandas_market_calendars wraps exchange_calendars; adds dependency bloat for no extra value needed here |
| APScheduler 3.x | APScheduler 4.x (alpha) | 4.x is still alpha (4.0.0a6); 3.x is stable and well-documented; no reason to use alpha |
| Manual retry logic | tenacity library | tenacity adds a dependency; 3-retry exponential backoff is trivial to implement manually (6 lines) |
| httpx for Slack | slack-sdk | slack-sdk adds a heavy dependency; raw webhook POST with httpx is ~10 lines |

**Installation:**
```bash
pip install "APScheduler>=3.11,<4" "exchange-calendars>=4.13"
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  pipeline/                     # New bounded context
    domain/
      entities.py               # PipelineRun entity (run_id, stages, status)
      value_objects.py           # StageResult, PipelineStatus, RunMode enums
      events.py                 # PipelineCompletedEvent, PipelineHaltedEvent
      services.py               # PipelineOrchestrator (core orchestration logic)
      repositories.py           # IPipelineRunRepository (ABC)
      __init__.py
    application/
      commands.py               # RunPipelineCommand, GetPipelineStatusQuery
      handlers.py               # RunPipelineHandler, PipelineStatusHandler
      __init__.py
    infrastructure/
      sqlite_pipeline_repo.py   # SQLite pipeline_runs persistence
      scheduler_service.py      # APScheduler wrapper (BackgroundScheduler setup)
      market_calendar.py        # exchange_calendars wrapper (is_trading_day, next_trading_day)
      notifier.py               # Notifier interface + SlackNotifier implementation
      __init__.py
    DOMAIN.md
```

### Pattern 1: PipelineOrchestrator as Domain Service

**What:** Pure domain service that receives stage handlers and executes them sequentially, collecting StageResult value objects. No scheduler or infrastructure dependencies.
**When to use:** Always -- this is the core orchestration logic, testable without APScheduler or SQLite.
**Example:**
```python
# Source: project DDD pattern (domain services have no infra dependencies)
class PipelineOrchestrator:
    """Orchestrates ingest -> regime -> score -> signal -> plan -> execute.

    Pure domain service. Receives handler references, not infrastructure.
    """

    def run(
        self,
        handlers: dict,          # bootstrap context handlers
        symbols: list[str],
        dry_run: bool = False,
    ) -> PipelineRun:
        stages: list[StageResult] = []

        # Stage 1: Ingest (with per-symbol retry)
        ingest_result = self._run_stage("ingest", ...)
        stages.append(ingest_result)
        surviving_symbols = ingest_result.succeeded_symbols

        # Stage 2: Regime detection
        regime_result = self._run_stage("regime", ...)
        stages.append(regime_result)

        # ... stages 3-5 ...

        # Safety gate: check regime + drawdown before execute
        if self._should_halt(regime_result, drawdown_level):
            return PipelineRun(status=PipelineStatus.HALTED, stages=stages, ...)

        # Stage 6: Execute (skip if dry_run)
        if not dry_run:
            exec_result = self._run_stage("execute", ...)
            stages.append(exec_result)

        return PipelineRun(status=PipelineStatus.COMPLETED, stages=stages, ...)
```

### Pattern 2: Stage-Level Retry with Exponential Backoff

**What:** Each pipeline stage wraps its handler call in a retry loop (3 attempts, 1s/2s/4s delays). Per-symbol failures in ingest/score/signal stages do not abort the stage -- failed symbols are logged and skipped.
**When to use:** For transient failures (yfinance timeouts, network errors).
**Example:**
```python
import time
import logging

logger = logging.getLogger(__name__)

def _retry_stage(self, fn, max_retries=3, base_delay=1.0):
    """Retry with exponential backoff. Raises on final failure."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
            logger.warning(
                "Stage retry %d/%d after error: %s (waiting %.1fs)",
                attempt + 1, max_retries, e, delay,
            )
            time.sleep(delay)
```

### Pattern 3: Market Calendar Guard

**What:** Before running the pipeline, check if today is a NYSE trading day using exchange_calendars. Skip with log entry if not.
**When to use:** Every scheduled invocation.
**Example:**
```python
# Source: exchange_calendars official docs
import exchange_calendars as xcals
from datetime import date

class MarketCalendarService:
    """Wraps exchange_calendars for NYSE trading day checks."""

    def __init__(self) -> None:
        self._cal = xcals.get_calendar("XNYS")

    def is_trading_day(self, d: date | None = None) -> bool:
        """Check if the given date is a regular NYSE trading session."""
        d = d or date.today()
        return self._cal.is_session(str(d))

    def is_early_close(self, d: date | None = None) -> bool:
        """Check if the given date is an early close session."""
        d = d or date.today()
        ts = pd.Timestamp(d)
        return ts in self._cal.early_closes

    def next_trading_day(self, d: date | None = None) -> date:
        """Get the next trading session after the given date."""
        d = d or date.today()
        ts = self._cal.date_to_session(str(d), direction="next")
        return ts.date()
```

### Pattern 4: APScheduler Integration with FastAPI Lifespan

**What:** BackgroundScheduler with SQLAlchemyJobStore started during FastAPI lifespan startup, shut down on shutdown. Single job with explicit ID and replace_existing=True.
**When to use:** Production deployment where APScheduler runs inside FastAPI process.
**Example:**
```python
# Source: APScheduler 3.x official docs + FastAPI integration pattern
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

def create_scheduler(db_path: str = "data/scheduler.db") -> BackgroundScheduler:
    jobstores = {
        "default": SQLAlchemyJobStore(url=f"sqlite:///{db_path}")
    }
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        job_defaults={
            "coalesce": True,          # Merge missed executions into one
            "max_instances": 1,        # Never run pipeline concurrently
            "misfire_grace_time": 3600, # 1 hour grace for missed runs
        },
        timezone="US/Eastern",
    )
    return scheduler

# Adding the daily job:
scheduler.add_job(
    run_daily_pipeline,
    CronTrigger(hour=16, minute=30, day_of_week="mon-fri", timezone="US/Eastern"),
    id="daily_pipeline",
    replace_existing=True,  # CRITICAL: prevents duplicate jobs on restart
    name="Daily Trading Pipeline",
)
```

### Pattern 5: Notifier Interface with Slack Implementation

**What:** Abstract Notifier protocol with SlackNotifier implementation using httpx POST to webhook URL.
**When to use:** Pipeline completion, halt, and error notifications.
**Example:**
```python
from typing import Protocol
import httpx
import logging

logger = logging.getLogger(__name__)

class Notifier(Protocol):
    """Notification interface for pipeline events."""
    def notify(self, title: str, message: str, level: str = "info") -> None: ...

class SlackNotifier:
    """Sends notifications to Slack via incoming webhook."""

    def __init__(self, webhook_url: str | None) -> None:
        self._url = webhook_url

    def notify(self, title: str, message: str, level: str = "info") -> None:
        if not self._url:
            logger.info("Slack not configured, skipping notification: %s", title)
            return
        emoji = {"info": ":white_check_mark:", "warning": ":warning:", "error": ":x:"}.get(level, ":bell:")
        payload = {"text": f"{emoji} *{title}*\n{message}"}
        try:
            resp = httpx.post(self._url, json=payload, timeout=10.0)
            resp.raise_for_status()
        except Exception:
            logger.warning("Failed to send Slack notification: %s", title, exc_info=True)
```

### Anti-Patterns to Avoid
- **Direct handler import across contexts:** PipelineOrchestrator must receive handlers via bootstrap dict, never import from scoring/signals/etc directly.
- **Retry at scheduler level:** APScheduler's built-in retry is for missed schedules, not transient stage failures. Stage retry belongs in the orchestrator.
- **Blocking the scheduler thread:** Pipeline execution should not block APScheduler's scheduler thread. Use a thread pool executor (APScheduler default) or run pipeline in a separate thread.
- **Global exchange_calendars instance:** Calendar creation is expensive (~100ms). Create once and cache in MarketCalendarService, not on every call.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Market calendar / holidays | Custom holiday list | exchange_calendars XNYS | 70+ exchanges, maintained yearly, includes early closes, half-days |
| Job scheduling with persistence | Custom cron + SQLite | APScheduler 3.x + SQLAlchemyJobStore | Misfire handling, timezone support, job serialization, process restart recovery |
| Exponential backoff timing | Complex retry framework | Simple loop with `time.sleep(base * 2**attempt)` | 3-retry backoff is 6 lines; no need for tenacity dependency |
| Slack webhook POST | Slack SDK integration | httpx.post(url, json=payload) | Already have httpx; webhook is a single POST call |

**Key insight:** The orchestrator itself IS the custom code. Everything it coordinates -- handlers, calendar, scheduler, notifications -- uses existing libraries or project infrastructure.

## Common Pitfalls

### Pitfall 1: APScheduler Duplicate Jobs on Restart
**What goes wrong:** Without `replace_existing=True` and explicit `id`, every process restart adds a duplicate job to the SQLite store. After 10 restarts, the pipeline runs 10 times per trigger.
**Why it happens:** APScheduler's `add_job()` creates a new job entry by default.
**How to avoid:** Always use `id="daily_pipeline", replace_existing=True` when adding the scheduled job.
**Warning signs:** Multiple pipeline runs at the same trigger time in logs.

### Pitfall 2: misfire_grace_time Not Serialized to SQLite
**What goes wrong:** There is a known issue (GitHub #147) where `misfire_grace_time` set per-job may not survive serialization to SQLite. On restart, it defaults to 1 second.
**Why it happens:** APScheduler 3.x serialization limitation with SQLite job store.
**How to avoid:** Set `misfire_grace_time` at the scheduler level in `job_defaults`, not per-job. This is set in the scheduler constructor and applies to all jobs.
**Warning signs:** Jobs not executing after process restart despite being within grace period.

### Pitfall 3: exchange_calendars Calendar Creation Performance
**What goes wrong:** `xcals.get_calendar("XNYS")` takes ~100ms and creates a large object. Calling it on every schedule check wastes resources.
**Why it happens:** Calendar objects precompute sessions for their entire date range.
**How to avoid:** Create the calendar once in MarketCalendarService.__init__() and reuse. The calendar covers future dates automatically.
**Warning signs:** Slow pipeline startup, high memory churn.

### Pitfall 4: Pipeline Running During Market Hours
**What goes wrong:** If the pipeline runs before market close (due to clock drift, timezone misconfiguration), ingest data may be incomplete.
**Why it happens:** Timezone misconfiguration -- APScheduler CronTrigger defaults to UTC if not explicitly set.
**How to avoid:** Always set `timezone="US/Eastern"` on CronTrigger. The 30-minute post-close buffer (16:30 ET) also helps.
**Warning signs:** Partial OHLCV data, different close prices than expected.

### Pitfall 5: Async/Sync Mismatch
**What goes wrong:** DataPipeline.ingest_universe() is async, but bootstrap handlers (score_handler, signal_handler) are sync. Mixing them in the orchestrator causes issues.
**Why it happens:** Data ingest uses asyncio (yfinance concurrency); DDD handlers are synchronous.
**How to avoid:** Use `asyncio.run()` for the ingest stage only. All other stages call sync handlers directly. The orchestrator itself should be synchronous (runs in APScheduler's thread pool).
**Warning signs:** "Event loop is already running" errors, blocked execution.

### Pitfall 6: Drawdown Tier Mapping to Numeric Values
**What goes wrong:** The CONTEXT.md says "drawdown tier >= 2" but the codebase uses DrawdownLevel enum (NORMAL/CAUTION/WARNING/CRITICAL), not numeric tiers.
**Why it happens:** Strategy documentation uses tier numbers (1=CAUTION@10%, 2=WARNING@15%, 3=CRITICAL@20%); code uses enum names.
**How to avoid:** Map "tier >= 2" to `DrawdownLevel.WARNING` or `DrawdownLevel.CRITICAL`. Check `drawdown_level` property from Portfolio aggregate.
**Warning signs:** Pipeline not halting when it should, or halting too aggressively.

## Code Examples

### Pipeline Run Entry (SQLite Table Schema)
```python
# Claude's discretion: pipeline_runs table schema
"""
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,           -- UUID
    started_at TEXT NOT NULL,          -- ISO 8601
    finished_at TEXT,                  -- ISO 8601 (NULL if running)
    status TEXT NOT NULL,              -- 'running', 'completed', 'halted', 'failed'
    mode TEXT NOT NULL DEFAULT 'auto', -- 'auto', 'manual', 'dry_run'
    stages_json TEXT,                  -- JSON array of stage results
    symbols_total INTEGER DEFAULT 0,
    symbols_succeeded INTEGER DEFAULT 0,
    symbols_failed INTEGER DEFAULT 0,
    halt_reason TEXT,                  -- NULL unless halted
    next_scheduled TEXT,               -- ISO 8601 of next run
    error_message TEXT                 -- NULL unless failed
);
"""
```

### Stage Result Value Object
```python
@dataclass(frozen=True)
class StageResult:
    """Result of a single pipeline stage."""
    stage_name: str              # "ingest", "regime", "score", "signal", "plan", "execute"
    started_at: datetime
    finished_at: datetime
    status: str                  # "success", "partial", "failed", "skipped"
    symbols_processed: int = 0
    symbols_succeeded: int = 0
    symbols_failed: int = 0
    error_message: str | None = None
    succeeded_symbols: list[str] = field(default_factory=list)
```

### Halt Check Logic
```python
# Maps "drawdown tier >= 2" from strategy docs to code enum values
from src.regime.domain.value_objects import RegimeType
from src.portfolio.domain.value_objects import DrawdownLevel

def _should_halt(self, regime_type: RegimeType, drawdown_level: DrawdownLevel) -> bool:
    """Check if pipeline should halt before execution stage.

    Halt when:
    - Regime is Crisis (RegimeType.CRISIS)
    - Drawdown tier >= 2 (DrawdownLevel.WARNING or CRITICAL)
    """
    if regime_type == RegimeType.CRISIS:
        return True
    if drawdown_level in (DrawdownLevel.WARNING, DrawdownLevel.CRITICAL):
        return True
    return False
```

### CLI Integration Pattern
```python
# Follows existing cli/main.py pattern with @app.command()
@app.command(name="pipeline")
def pipeline_cmd(
    action: str = typer.Argument("run", help="run|status"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Execute without submitting orders"),
):
    """Run or check status of the automated pipeline."""
    # Note: Typer subcommand groups can also be used, but the existing
    # CLI uses flat @app.command() -- follow established pattern.
    if action == "run":
        # Manual pipeline trigger
        ...
    elif action == "status":
        # Show recent runs + next schedule
        ...
```

### Data Passing Between Stages
```python
# Claude's discretion: use simple dict for stage data passing
# Simpler than events, no overhead, pipeline is sequential
stage_data = {}
stage_data["ingest"] = {"succeeded_symbols": ["AAPL", "MSFT", ...]}
stage_data["regime"] = {"regime_type": RegimeType.BULL, "confidence": 0.85}
stage_data["scores"] = {"AAPL": 72.5, "MSFT": 68.3, ...}
stage_data["signals"] = {"AAPL": {"direction": "BUY", ...}, ...}
stage_data["plans"] = [TradePlan(...), ...]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| APScheduler 4.x async-native | APScheduler 3.x stable | 4.x still alpha (4.0.0a6 Apr 2025) | Use 3.x; 4.x API completely different, not production-ready |
| pandas_market_calendars | exchange_calendars (upstream) | exchange_calendars is the maintained upstream | pandas_market_calendars wraps it; use exchange_calendars directly |
| Custom holiday lists | exchange_calendars prebuilt | Always current for 2026 | No manual holiday maintenance needed |

**Deprecated/outdated:**
- `trading_calendars` (Quantopian): Abandoned, replaced by `exchange_calendars`
- APScheduler `@app.on_event("startup")`: FastAPI deprecated `on_event` in favor of lifespan context manager
- `scheduler.add_job()` without `replace_existing`: Causes duplicate jobs on restart

## Open Questions

1. **Typer CLI structure: flat command vs subcommand group**
   - What we know: Existing CLI uses flat `@app.command()` pattern. CONTEXT.md specifies `trade pipeline run` and `trade pipeline status`.
   - What's unclear: Whether to use Typer's `app.add_typer()` for a `pipeline` subcommand group or keep flat with `pipeline-run`/`pipeline-status`.
   - Recommendation: Use Typer subcommand group (`pipeline_app = typer.Typer()` + `app.add_typer(pipeline_app, name="pipeline")`) to match the `trade pipeline run/status` syntax from CONTEXT.md.

2. **Async ingest in sync orchestrator**
   - What we know: DataPipeline.ingest_universe() is async; all DDD handlers are sync.
   - What's unclear: Whether to wrap ingest with `asyncio.run()` inside the sync orchestrator, or make the orchestrator async.
   - Recommendation: Keep orchestrator sync (runs in APScheduler thread), use `asyncio.run()` for ingest stage only. This matches how the existing CLI handles async ingest.

3. **Calendar caching scope**
   - What we know: exchange_calendars objects are expensive to create. MarketCalendarService should cache the calendar.
   - What's unclear: Whether to create calendar at module level or per-service-instance.
   - Recommendation: Create in MarketCalendarService.__init__() and inject the service via bootstrap. Calendar range covers all future dates.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ with pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_pipeline_orchestrator.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | Pipeline runs ingest through execute sequentially | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_full_pipeline_run -x` | Wave 0 |
| PIPE-02 | Pipeline skips non-trading days (weekends, holidays, early-close) | unit | `pytest tests/unit/test_market_calendar.py -x` | Wave 0 |
| PIPE-03 | Run logs stages, symbol counts, errors to SQLite | unit | `pytest tests/unit/test_pipeline_repo.py -x` | Wave 0 |
| PIPE-04 | Dry-run mode runs full pipeline without order submission | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_dry_run_skips_execution -x` | Wave 0 |
| PIPE-05 | Stages retry 3x with exponential backoff on transient failures | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_retry_exponential_backoff -x` | Wave 0 |
| PIPE-06 | Pipeline halts when regime is Crisis or drawdown tier >= 2 | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_halt_on_crisis -x` | Wave 0 |
| PIPE-07 | APScheduler persists schedule across process restarts | unit | `pytest tests/unit/test_scheduler_service.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_pipeline_orchestrator.py tests/unit/test_market_calendar.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_pipeline_orchestrator.py` -- covers PIPE-01, PIPE-04, PIPE-05, PIPE-06
- [ ] `tests/unit/test_market_calendar.py` -- covers PIPE-02
- [ ] `tests/unit/test_pipeline_repo.py` -- covers PIPE-03
- [ ] `tests/unit/test_scheduler_service.py` -- covers PIPE-07
- [ ] Framework install: `pip install "APScheduler>=3.11,<4" "exchange-calendars>=4.13"` -- if not detected

## Sources

### Primary (HIGH confidence)
- [APScheduler 3.x User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) -- BackgroundScheduler setup, SQLAlchemyJobStore, CronTrigger, misfire_grace_time, replace_existing
- [APScheduler 3.x CronTrigger docs](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html) -- CronTrigger parameters, timezone, day_of_week
- [APScheduler 3.x SQLAlchemy JobStore](https://apscheduler.readthedocs.io/en/3.x/modules/jobstores/sqlalchemy.html) -- SQLAlchemyJobStore(url=) configuration
- [exchange_calendars GitHub](https://github.com/gerrymanoim/exchange_calendars) -- is_session(), early_closes property, get_calendar("XNYS"), date_to_session()
- [exchange_calendars releases](https://github.com/gerrymanoim/exchange_calendars/releases) -- v4.13.2 (latest stable, Mar 2025)
- [APScheduler PyPI](https://pypi.org/project/APScheduler/) -- v3.11.2 (latest stable, Dec 2025)

### Secondary (MEDIUM confidence)
- [APScheduler + FastAPI integration](https://bytegoblin.io/blog/implementing-background-job-scheduling-in-fastapi-with-apscheduler.mdx) -- Lifespan integration pattern, SQLite job store with FastAPI
- [APScheduler misfire_grace_time issue #147](https://github.com/agronholm/apscheduler/issues/147) -- misfire_grace_time not serialized per-job in SQLite; use job_defaults instead
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks) -- Webhook POST format and setup

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- APScheduler 3.x and exchange_calendars are well-documented, stable libraries with official docs verified
- Architecture: HIGH -- Follows project's established DDD patterns; PipelineOrchestrator mirrors existing handler/service patterns
- Pitfalls: HIGH -- APScheduler duplicate jobs and misfire_grace_time issues verified via GitHub issues; async/sync mismatch verified by reading codebase
- Market calendar: HIGH -- exchange_calendars API verified via official GitHub README and PyPI

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable libraries, 30-day validity)
