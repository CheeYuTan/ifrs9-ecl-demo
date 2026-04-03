"""Databricks jobs routes — /api/jobs/*"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import jobs

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class TriggerJobRequest(BaseModel):
    job_key: str = "satellite_ecl_sync"
    enabled_models: Optional[list[str]] = None
    # Monte Carlo parameters
    n_simulations: Optional[int] = None
    pd_lgd_correlation: Optional[float] = None
    aging_factor: Optional[float] = None
    pd_floor: Optional[float] = None
    pd_cap: Optional[float] = None
    lgd_floor: Optional[float] = None
    lgd_cap: Optional[float] = None
    random_seed: Optional[int] = None
    scenario_weights: Optional[dict[str, float]] = None


@router.post("/trigger")
def trigger_job(body: TriggerJobRequest):
    try:
        if body.job_key == "satellite_ecl_sync":
            result = jobs.trigger_satellite_ecl_job(body.enabled_models)
        elif body.job_key == "full_pipeline":
            result = jobs.trigger_full_pipeline()
        elif body.job_key == "demo_data":
            result = jobs.trigger_demo_data_job()
        elif body.job_key == "monte_carlo":
            mc_kwargs = {}
            if body.n_simulations is not None:
                mc_kwargs["n_simulations"] = body.n_simulations
            if body.pd_lgd_correlation is not None:
                mc_kwargs["pd_lgd_correlation"] = body.pd_lgd_correlation
            if body.aging_factor is not None:
                mc_kwargs["aging_factor"] = body.aging_factor
            if body.pd_floor is not None:
                mc_kwargs["pd_floor"] = body.pd_floor
            if body.pd_cap is not None:
                mc_kwargs["pd_cap"] = body.pd_cap
            if body.lgd_floor is not None:
                mc_kwargs["lgd_floor"] = body.lgd_floor
            if body.lgd_cap is not None:
                mc_kwargs["lgd_cap"] = body.lgd_cap
            if body.random_seed is not None:
                mc_kwargs["random_seed"] = body.random_seed
            if body.scenario_weights is not None:
                mc_kwargs["scenario_weights"] = body.scenario_weights
            result = jobs.trigger_monte_carlo_job(**mc_kwargs)
        else:
            raise HTTPException(400, f"Unknown job key: {body.job_key}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Failed to trigger job")
        raise HTTPException(500, f"Failed to trigger job: {e}")

@router.get("/run/{run_id}")
def get_job_run_status(run_id: int):
    try:
        return jobs.get_run_status(run_id)
    except Exception as e:
        log.exception("Failed to get run status")
        raise HTTPException(500, f"Failed to get run status: {e}")

@router.get("/runs/{job_key}")
def list_job_runs(job_key: str, limit: int = 10):
    try:
        return jobs.list_job_runs(job_key, limit)
    except Exception as e:
        log.exception("Failed to list job runs")
        raise HTTPException(500, f"Failed to list job runs: {e}")

@router.get("/config")
def get_jobs_config():
    status = jobs.get_jobs_status()
    return {
        "available_models": jobs.ALL_MODELS,
        "job_ids": jobs._get_job_ids(),
        "workspace_url": jobs._ws_host(),
        "workspace_id": jobs._ws_id(),
        **status,
    }

@router.post("/provision")
def provision_jobs():
    """Force-create or update all managed jobs with correct notebook paths."""
    try:
        sat_id = jobs._ensure_job(
            "satellite_ecl_sync",
            "IFRS9 ECL - Satellite Model + ECL + Sync",
            jobs._build_satellite_ecl_job_def,
        )
        pipe_id = jobs._ensure_job(
            "full_pipeline",
            "IFRS9 ECL - Full Pipeline",
            jobs._build_full_pipeline_job_def,
        )
        demo_id = jobs._ensure_job(
            "demo_data",
            "IFRS9 ECL - Generate Demo Data",
            jobs._build_demo_data_job_def,
        )
        mc_id = jobs._ensure_job(
            "monte_carlo",
            "IFRS9 ECL - Monte Carlo Simulation",
            jobs._build_monte_carlo_job_def,
        )
        return {
            "status": "ok",
            "satellite_ecl_sync": sat_id,
            "full_pipeline": pipe_id,
            "demo_data": demo_id,
            "monte_carlo": mc_id,
            "scripts_base": jobs._detect_scripts_base(),
        }
    except Exception as e:
        log.exception("Failed to provision jobs")
        raise HTTPException(500, f"Failed to provision jobs: {e}")
