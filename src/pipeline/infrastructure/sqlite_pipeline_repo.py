"""Pipeline Infrastructure -- SQLite Pipeline Run Repository.

Persists PipelineRun entities with stage-level JSON.
Follows SqliteCooldownRepository pattern: WAL mode, json serialization.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from src.pipeline.domain.entities import PipelineRun
from src.pipeline.domain.repositories import IPipelineRunRepository
from src.pipeline.domain.value_objects import PipelineStatus, RunMode, StageResult


class SqlitePipelineRunRepository(IPipelineRunRepository):
    """SQLite-based persistence for pipeline run history.

    Stores stage results as JSON array. Uses WAL journal mode
    for concurrent safety between pipeline and CLI.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id              TEXT PRIMARY KEY,
            started_at          TEXT NOT NULL,
            finished_at         TEXT,
            status              TEXT NOT NULL,
            mode                TEXT NOT NULL,
            stages_json         TEXT NOT NULL DEFAULT '[]',
            symbols_total       INTEGER NOT NULL DEFAULT 0,
            symbols_succeeded   INTEGER NOT NULL DEFAULT 0,
            symbols_failed      INTEGER NOT NULL DEFAULT 0,
            halt_reason         TEXT,
            next_scheduled      TEXT,
            error_message       TEXT
        );
    """

    def __init__(self, db_path: str = "data/pipeline.db") -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        dir_part = os.path.dirname(self._db_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(self._CREATE_TABLE)

    def save(self, run: PipelineRun) -> None:
        """Persist or update a pipeline run (upsert by run_id)."""
        stages_json = json.dumps(
            [self._stage_to_dict(s) for s in run.stages], ensure_ascii=False
        )
        symbols_failed = sum(s.symbols_failed for s in run.stages)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO pipeline_runs
                    (run_id, started_at, finished_at, status, mode, stages_json,
                     symbols_total, symbols_succeeded, symbols_failed,
                     halt_reason, next_scheduled, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    finished_at = excluded.finished_at,
                    status = excluded.status,
                    stages_json = excluded.stages_json,
                    symbols_total = excluded.symbols_total,
                    symbols_succeeded = excluded.symbols_succeeded,
                    symbols_failed = excluded.symbols_failed,
                    halt_reason = excluded.halt_reason,
                    next_scheduled = excluded.next_scheduled,
                    error_message = excluded.error_message
                """,
                (
                    run.run_id,
                    run.started_at.isoformat(),
                    run.finished_at.isoformat() if run.finished_at else None,
                    run.status.value,
                    run.mode.value,
                    stages_json,
                    run.symbols_total,
                    run.symbols_succeeded,
                    symbols_failed,
                    run.halt_reason,
                    run.next_scheduled.isoformat() if run.next_scheduled else None,
                    run.error_message,
                ),
            )

    def get_recent(self, limit: int = 10) -> list[PipelineRun]:
        """Return the most recent N runs, ordered by started_at descending."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_run(row) for row in rows]

    def get_by_id(self, run_id: str) -> Optional[PipelineRun]:
        """Return a pipeline run by its ID, or None if not found."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM pipeline_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    @staticmethod
    def _stage_to_dict(stage: StageResult) -> dict:
        """Serialize a StageResult to a JSON-safe dict."""
        return {
            "stage_name": stage.stage_name,
            "started_at": stage.started_at.isoformat(),
            "finished_at": stage.finished_at.isoformat(),
            "status": stage.status,
            "symbols_processed": stage.symbols_processed,
            "symbols_succeeded": stage.symbols_succeeded,
            "symbols_failed": stage.symbols_failed,
            "error_message": stage.error_message,
            "succeeded_symbols": stage.succeeded_symbols,
        }

    @staticmethod
    def _dict_to_stage(d: dict) -> StageResult:
        """Deserialize a dict to a StageResult."""
        return StageResult(
            stage_name=d["stage_name"],
            started_at=datetime.fromisoformat(d["started_at"]).replace(
                tzinfo=timezone.utc
            ),
            finished_at=datetime.fromisoformat(d["finished_at"]).replace(
                tzinfo=timezone.utc
            ),
            status=d["status"],
            symbols_processed=d["symbols_processed"],
            symbols_succeeded=d["symbols_succeeded"],
            symbols_failed=d["symbols_failed"],
            error_message=d.get("error_message"),
            succeeded_symbols=d.get("succeeded_symbols", []),
        )

    @staticmethod
    def _row_to_run(row: sqlite3.Row) -> PipelineRun:
        """Convert SQLite row to PipelineRun entity."""
        stages_data = json.loads(row["stages_json"])
        stages = [
            SqlitePipelineRunRepository._dict_to_stage(d) for d in stages_data
        ]

        started_at = datetime.fromisoformat(row["started_at"]).replace(
            tzinfo=timezone.utc
        )
        finished_at = None
        if row["finished_at"]:
            finished_at = datetime.fromisoformat(row["finished_at"]).replace(
                tzinfo=timezone.utc
            )
        next_scheduled = None
        if row["next_scheduled"]:
            next_scheduled = datetime.fromisoformat(row["next_scheduled"]).replace(
                tzinfo=timezone.utc
            )

        return PipelineRun(
            run_id=row["run_id"],
            started_at=started_at,
            finished_at=finished_at,
            status=PipelineStatus(row["status"]),
            mode=RunMode(row["mode"]),
            stages=stages,
            halt_reason=row["halt_reason"],
            error_message=row["error_message"],
            next_scheduled=next_scheduled,
        )
