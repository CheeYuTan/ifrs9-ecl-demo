"""Period-End Close pipeline routes — /api/pipeline/*"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from domain.period_close import (
    start_pipeline, execute_step, complete_pipeline,
    get_pipeline_run, get_pipeline_health, PIPELINE_STEPS,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class StartPipelineRequest(BaseModel):
    triggered_by: str = "system"


class ExecuteStepRequest(BaseModel):
    step_key: str


@router.post("/start/{project_id}")
def start_pipeline_route(project_id: str, body: StartPipelineRequest):
    """Start a new period-end close pipeline run."""
    try:
        result = start_pipeline(project_id, body.triggered_by)
        return result
    except Exception as e:
        log.exception("Failed to start pipeline")
        raise HTTPException(500, f"Failed to start pipeline: {e}")


@router.get("/steps")
def list_pipeline_steps():
    """Return the ordered list of pipeline steps."""
    return PIPELINE_STEPS


@router.get("/run/{run_id}")
def get_run(run_id: str):
    """Get pipeline run status and step details."""
    run = get_pipeline_run(run_id)
    if not run:
        raise HTTPException(404, "Pipeline run not found")
    return run


@router.post("/run/{run_id}/execute-step")
def execute_step_route(run_id: str, body: ExecuteStepRequest):
    """Execute a single pipeline step."""
    valid_keys = {s["key"] for s in PIPELINE_STEPS}
    if body.step_key not in valid_keys:
        raise HTTPException(400, f"Invalid step key: {body.step_key}")
    run = get_pipeline_run(run_id)
    if not run:
        raise HTTPException(404, "Pipeline run not found")
    try:
        result = execute_step(run_id, body.step_key)
        return result
    except Exception as e:
        log.exception("Failed to execute step %s", body.step_key)
        raise HTTPException(500, f"Step execution failed: {e}")


@router.post("/run/{run_id}/complete")
def complete_pipeline_route(run_id: str):
    """Mark the pipeline run as completed."""
    run = get_pipeline_run(run_id)
    if not run:
        raise HTTPException(404, "Pipeline run not found")
    steps = run.get("steps", [])
    failed = [s["key"] for s in steps if s.get("status") == "failed"]
    status = "failed" if failed else "completed"
    error_msg = f"Steps failed: {', '.join(failed)}" if failed else None
    try:
        complete_pipeline(run_id, status=status, error_message=error_msg)
        updated = get_pipeline_run(run_id)
        return updated or {"run_id": run_id, "status": status}
    except Exception as e:
        log.exception("Failed to complete pipeline")
        raise HTTPException(500, f"Failed to complete pipeline: {e}")


@router.get("/health/{project_id}")
def pipeline_health(project_id: str):
    """Get pipeline health summary for a project."""
    return get_pipeline_health(project_id)


@router.post("/run-all/{project_id}")
def run_full_pipeline(project_id: str, body: StartPipelineRequest):
    """Run all pipeline steps sequentially. Stops on first failure."""
    try:
        run_data = start_pipeline(project_id, body.triggered_by)
        run_id = run_data["run_id"]
        results = []
        for step in PIPELINE_STEPS:
            result = execute_step(run_id, step["key"])
            results.append(result)
            if result.get("status") == "failed":
                complete_pipeline(
                    run_id, status="failed",
                    error_message=f"Failed at step: {step['key']}",
                )
                final = get_pipeline_run(run_id)
                return {**(final or {}), "step_results": results}
        complete_pipeline(run_id, status="completed")
        final = get_pipeline_run(run_id)
        return {**(final or {}), "step_results": results}
    except Exception as e:
        log.exception("Full pipeline run failed")
        raise HTTPException(500, f"Full pipeline run failed: {e}")
