"""Pipeline control router -- trigger, status, daemon.

POST /api/v1/pipeline/run -- trigger pipeline execution (background).
GET /api/v1/pipeline/status -- recent pipeline runs.
POST /api/v1/pipeline/daemon/start -- start scheduler daemon.
"""
from __future__ import annotations

import logging
import threading
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from commercial.api.dependencies import (
    get_pipeline_status_handler,
    get_run_pipeline_handler,
    get_scheduler_service,
    verify_dashboard_secret,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


class RunPipelineRequest(BaseModel):
    """Request body for pipeline run."""

    symbols: Optional[list[str]] = None
    dry_run: bool = False


@router.post("/run")
def run_pipeline(
    body: RunPipelineRequest,
    handler=Depends(get_run_pipeline_handler),
    _: None = Depends(verify_dashboard_secret),
):
    """Trigger pipeline execution in background, return immediately."""
    from src.pipeline.application.commands import RunPipelineCommand
    from src.pipeline.domain.value_objects import RunMode

    import uuid

    run_id = str(uuid.uuid4())

    cmd = RunPipelineCommand(
        dry_run=body.dry_run,
        mode=RunMode.MANUAL,
    )

    def _run():
        try:
            handler.handle(cmd)
        except Exception:
            logger.exception("Background pipeline run failed")

    thread = threading.Thread(target=_run, daemon=True, name=f"pipeline-{run_id}")
    thread.start()

    return {"status": "started", "run_id": run_id, "message": "Pipeline started in background"}


@router.get("/status")
def get_status(
    limit: int = 10,
    handler=Depends(get_pipeline_status_handler),
    _: None = Depends(verify_dashboard_secret),
):
    """Return recent pipeline runs."""
    from src.pipeline.application.commands import GetPipelineStatusQuery

    runs = handler.handle(GetPipelineStatusQuery(limit=limit))
    return {
        "pipeline_runs": [
            {
                "run_id": r.run_id,
                "status": r.status.value,
                "mode": r.mode.value,
                "started_at": r.started_at.isoformat(),
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "symbols_total": r.symbols_total,
                "symbols_succeeded": r.symbols_succeeded,
                "error_message": r.error_message,
                "halt_reason": r.halt_reason,
            }
            for r in runs
        ],
    }


@router.post("/daemon/start")
def start_daemon(
    scheduler=Depends(get_scheduler_service),
    _: None = Depends(verify_dashboard_secret),
):
    """Start the pipeline scheduler daemon in background."""
    try:
        scheduler.start()
        return {"status": "started", "message": "Scheduler daemon started"}
    except Exception as e:
        logger.error("Failed to start scheduler: %s", e)
        return {"status": "error", "message": str(e)}
