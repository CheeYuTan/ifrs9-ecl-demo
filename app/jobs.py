"""
Databricks Jobs integration for IFRS 9 ECL Application.
Auto-provisions and manages Databricks Jobs via the SDK.
When running as a Databricks App, uses the app's service principal for auth.
Jobs are created/updated automatically with correct notebook paths.
"""
import os
import logging
from functools import lru_cache

log = logging.getLogger(__name__)

ALL_MODELS = [
    "linear_regression", "logistic_regression", "polynomial_deg2",
    "ridge_regression", "random_forest", "elastic_net",
    "gradient_boosting", "xgboost",
]

NOTEBOOK_SCRIPTS = {
    "03a_run_single_model": "03a_run_single_model.py",
    "03a_aggregate_models": "03a_aggregate_models.py",
    "03b_run_ecl_calculation": "03b_run_ecl_calculation.py",
    "03c_run_monte_carlo": "03c_run_monte_carlo.py",
    "04_sync_to_lakebase": "04_sync_to_lakebase.py",
    "01_generate_data": "01_generate_data.py",
    "02_run_data_processing": "02_run_data_processing.py",
}


@lru_cache(maxsize=1)
def _get_workspace_client():
    from databricks.sdk import WorkspaceClient
    is_app = bool(os.environ.get("DATABRICKS_APP_NAME"))
    if is_app:
        return WorkspaceClient()
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "lakemeter")
    return WorkspaceClient(profile=profile)


def _detect_scripts_base() -> str:
    """Detect the workspace path where scripts are deployed.

    Strategy:
    1. Check admin config for explicit override
    2. Derive from the app's source code path (sibling 'scripts' folder)
    3. Fall back to convention: /Workspace/Users/{current_user}/ifrs9-ecl-demo/scripts
    """
    try:
        import admin_config
        cfg = admin_config.get_config()
        explicit = cfg.get("jobs", {}).get("scripts_base_path", "")
        if explicit:
            return explicit.rstrip("/")
    except Exception:
        pass

    try:
        app_src = os.environ.get("DATABRICKS_SOURCE_CODE_PATH", "")
        if app_src:
            parent = app_src.rsplit("/", 1)[0]
            return f"{parent}/scripts"
    except Exception:
        pass

    try:
        w = _get_workspace_client()
        app_name = os.environ.get("DATABRICKS_APP_NAME", "")
        if app_name:
            app_info = w.apps.get(app_name)
            active = app_info.active_deployment
            if active and active.source_code_path:
                parent = active.source_code_path.rsplit("/", 1)[0]
                return f"{parent}/scripts"
    except Exception as e:
        log.debug("Could not detect scripts path from app info: %s", e)

    try:
        w = _get_workspace_client()
        me = w.current_user.me()
        username = me.user_name
        return f"/Workspace/Users/{username}/ifrs9-ecl-demo/scripts"
    except Exception:
        pass

    return "/Workspace/Users/steven.tan@databricks.com/ifrs9-ecl-demo/scripts"


def _ws_host() -> str:
    try:
        w = _get_workspace_client()
        return (w.config.host or "").rstrip("/")
    except Exception:
        pass
    try:
        import admin_config
        cfg = admin_config.get_config()
        return cfg.get("jobs", {}).get("workspace_url", "")
    except Exception:
        return os.environ.get("DATABRICKS_HOST", "")


def _ws_id() -> str:
    try:
        import admin_config
        cfg = admin_config.get_config()
        return cfg.get("jobs", {}).get("workspace_id", "")
    except Exception:
        return os.environ.get("DATABRICKS_WORKSPACE_ID", "")


def _config_params() -> dict:
    """Build notebook_params from admin_config for catalog/schema/project forwarding."""
    params = {}
    try:
        import admin_config
        cfg = admin_config.get_config()
        ds = cfg.get("data_sources", {})
        app = cfg.get("app_settings", {})
        params["catalog"] = ds.get("catalog", "lakemeter_catalog")
        params["schema"] = ds.get("schema", "expected_credit_loss")
        params["lakebase_schema"] = ds.get("lakebase_schema", "expected_credit_loss")
        params["lakebase_prefix"] = ds.get("lakebase_prefix", "lb_")
        params["reporting_date"] = app.get("reporting_date", "2025-12-31")
        scripts_base = _detect_scripts_base()
        params["workspace_scripts_path"] = scripts_base
        dp = cfg.get("jobs", {}).get("default_job_params", {})
        params.update(dp)
    except Exception:
        pass
    return params


def _get_job_ids() -> dict:
    """Get stored job IDs from admin config, or empty dict."""
    try:
        import admin_config
        cfg = admin_config.get_config()
        return cfg.get("jobs", {}).get("job_ids", {})
    except Exception:
        return {}


def _save_job_id(job_key: str, job_id: int):
    """Persist a job ID back to admin config."""
    try:
        import admin_config
        cfg = admin_config.get_config()
        jobs_cfg = cfg.get("jobs", {})
        job_ids = jobs_cfg.get("job_ids", {})
        job_ids[job_key] = job_id
        jobs_cfg["job_ids"] = job_ids
        admin_config.save_config_section("jobs", jobs_cfg)
        log.info("Saved job_id %s=%s to admin config", job_key, job_id)
    except Exception as e:
        log.warning("Could not save job_id to config: %s", e)


ML_ENVIRONMENT_DEPS = [
    "scikit-learn",
    "xgboost",
    "optuna",
    "psycopg2-binary",
    "faker",
]


def _env_dict():
    """Return the serverless environment spec as a plain dict (REST API compatible)."""
    return {
        "environment_key": "ml_env",
        "spec": {
            "client": "5",
            "dependencies": ML_ENVIRONMENT_DEPS,
        },
    }


def _nb_task(task_key, notebook_path, depends_on=None, base_params=None, run_if=None):
    """Build a task dict for the REST API."""
    t = {
        "task_key": task_key,
        "environment_key": "ml_env",
        "notebook_task": {
            "notebook_path": notebook_path,
            "source": "WORKSPACE",
        },
        "timeout_seconds": 0,
    }
    if depends_on:
        t["depends_on"] = [{"task_key": d} for d in depends_on]
    if base_params:
        t["notebook_task"]["base_parameters"] = base_params
    if run_if:
        t["run_if"] = run_if
    return t


def _build_satellite_ecl_job_def(scripts_base: str) -> dict:
    """Build the full job definition for the satellite model + ECL + sync pipeline."""
    model_tasks = [
        _nb_task(
            f"model_{m}",
            f"{scripts_base}/03a_run_single_model.py",
            base_params={"model_name": m},
        )
        for m in ALL_MODELS
    ]

    aggregate = _nb_task(
        "aggregate_models",
        f"{scripts_base}/03a_aggregate_models.py",
        depends_on=[f"model_{m}" for m in ALL_MODELS],
        run_if="ALL_DONE",
        base_params={"enabled_models": ",".join(ALL_MODELS)},
    )

    ecl = _nb_task(
        "ecl_calculation",
        f"{scripts_base}/03b_run_ecl_calculation.py",
        depends_on=["aggregate_models"],
        run_if="ALL_SUCCESS",
    )

    sync = _nb_task(
        "sync_to_lakebase",
        f"{scripts_base}/04_sync_to_lakebase.py",
        depends_on=["ecl_calculation"],
        run_if="ALL_SUCCESS",
    )

    return {
        "tasks": model_tasks + [aggregate, ecl, sync],
        "environments": [_env_dict()],
    }


def _build_full_pipeline_job_def(scripts_base: str) -> dict:
    """Build the full pipeline job definition (process -> satellite -> ECL -> sync).

    NOTE: This does NOT include generate_data. Customers map their own data
    via Admin > Data Sources. Use trigger_demo_data_job() to generate synthetic
    data for demo purposes only.
    """
    proc = _nb_task("data_processing", f"{scripts_base}/02_run_data_processing.py")

    model_tasks = [
        _nb_task(
            f"model_{m}",
            f"{scripts_base}/03a_run_single_model.py",
            depends_on=["data_processing"],
            base_params={"model_name": m},
        )
        for m in ALL_MODELS
    ]

    aggregate = _nb_task(
        "aggregate_models",
        f"{scripts_base}/03a_aggregate_models.py",
        depends_on=[f"model_{m}" for m in ALL_MODELS],
        run_if="ALL_DONE",
        base_params={"enabled_models": ",".join(ALL_MODELS)},
    )

    ecl = _nb_task(
        "ecl_calculation",
        f"{scripts_base}/03b_run_ecl_calculation.py",
        depends_on=["aggregate_models"],
        run_if="ALL_SUCCESS",
    )

    sync = _nb_task(
        "sync_to_lakebase",
        f"{scripts_base}/04_sync_to_lakebase.py",
        depends_on=["ecl_calculation"],
        run_if="ALL_SUCCESS",
    )

    return {
        "tasks": [proc] + model_tasks + [aggregate, ecl, sync],
        "environments": [_env_dict()],
    }


def _build_monte_carlo_job_def(scripts_base: str) -> dict:
    """Build a Monte Carlo simulation job (simulation -> sync to lakebase)."""
    mc = _nb_task("monte_carlo_simulation", f"{scripts_base}/03c_run_monte_carlo.py")
    sync = _nb_task(
        "sync_to_lakebase",
        f"{scripts_base}/04_sync_to_lakebase.py",
        depends_on=["monte_carlo_simulation"],
        run_if="ALL_SUCCESS",
    )
    return {
        "tasks": [mc, sync],
        "environments": [_env_dict()],
    }


def _build_demo_data_job_def(scripts_base: str) -> dict:
    """Build a demo data generation job (generate synthetic data -> process)."""
    gen = _nb_task("generate_data", f"{scripts_base}/01_generate_data.py")
    proc = _nb_task(
        "data_processing",
        f"{scripts_base}/02_run_data_processing.py",
        depends_on=["generate_data"],
        run_if="ALL_SUCCESS",
    )
    return {
        "tasks": [gen, proc],
        "environments": [_env_dict()],
    }


def _rest_api(method: str, path: str, body: dict = None):
    """Call Databricks REST API directly (avoids SDK version issues with environments)."""
    w = _get_workspace_client()
    host = w.config.host.rstrip("/")
    headers = w.config.authenticate()
    headers["Content-Type"] = "application/json"
    import requests
    url = f"{host}{path}"
    if method == "GET":
        r = requests.get(url, headers=headers, timeout=30)
    elif method == "POST":
        r = requests.post(url, headers=headers, json=body or {}, timeout=30)
    else:
        r = requests.request(method, url, headers=headers, json=body or {}, timeout=30)
    r.raise_for_status()
    return r.json() if r.text else {}


def _ensure_job(job_key: str, job_name: str, build_fn) -> int:
    """Ensure a job exists with correct notebook paths and environment.
    Uses REST API directly to support environments field on all SDK versions.
    Returns the job_id.
    """
    scripts_base = _detect_scripts_base()
    log.info("Scripts base for %s: %s", job_key, scripts_base)
    job_def = build_fn(scripts_base)

    stored_ids = _get_job_ids()
    job_id = stored_ids.get(job_key)

    new_settings = {
        "name": job_name,
        "format": "MULTI_TASK",
        "max_concurrent_runs": 1,
        "queue": {"enabled": True},
        "tasks": job_def["tasks"],
        "environments": job_def.get("environments", []),
    }

    if job_id:
        try:
            existing = _rest_api("GET", f"/api/2.1/jobs/get?job_id={job_id}")
            existing_tasks = existing.get("settings", {}).get("tasks", [])
            needs_update = False

            desired_paths = {t["task_key"]: t.get("notebook_task", {}).get("notebook_path", "") for t in job_def["tasks"]}
            for task in existing_tasks:
                tk = task.get("task_key", "")
                nb = task.get("notebook_task", {}).get("notebook_path", "")
                desired = desired_paths.get(tk, "")
                if desired and nb != desired:
                    needs_update = True
                    break

            if not needs_update and len(existing_tasks) != len(job_def["tasks"]):
                needs_update = True

            if not needs_update:
                existing_envs = existing.get("settings", {}).get("environments", [])
                desired_envs = job_def.get("environments", [])
                if len(existing_envs) != len(desired_envs):
                    needs_update = True
                else:
                    for desired in desired_envs:
                        match = next((e for e in existing_envs if e.get("environment_key") == desired.get("environment_key")), None)
                        if not match or match.get("spec") != desired.get("spec"):
                            needs_update = True
                            break

            if needs_update:
                log.info("Updating job %s (%s) — paths, tasks, or environments changed", job_id, job_key)
                _rest_api("POST", "/api/2.1/jobs/reset", {
                    "job_id": int(job_id),
                    "new_settings": new_settings,
                })
                _grant_app_permissions(int(job_id))
            else:
                log.info("Job %s (%s) already up-to-date", job_id, job_key)
            return int(job_id)
        except Exception as e:
            log.warning("Stored job %s not accessible (%s), will create new", job_id, e)

    log.info("Creating new job: %s", job_name)
    result = _rest_api("POST", "/api/2.1/jobs/create", new_settings)
    new_id = result["job_id"]
    log.info("Created job %s: %s", job_key, new_id)
    _save_job_id(job_key, new_id)
    _grant_app_permissions(new_id)
    return new_id


def _grant_app_permissions(job_id: int):
    """Grant CAN_MANAGE_RUN to the app's service principal."""
    try:
        w = _get_workspace_client()
        sp_id = os.environ.get("DATABRICKS_SERVICE_PRINCIPAL_ID", "")
        if not sp_id:
            me = w.current_user.me()
            sp_id = me.user_name if me else ""
        if not sp_id:
            return

        from databricks.sdk.service.iam import AccessControlRequest, PermissionLevel
        w.permissions.update(
            request_object_type="jobs",
            request_object_id=str(job_id),
            access_control_list=[
                AccessControlRequest(
                    service_principal_name=sp_id,
                    permission_level=PermissionLevel.CAN_MANAGE_RUN,
                ),
            ],
        )
        log.info("Granted CAN_MANAGE_RUN on job %s to %s", job_id, sp_id)
    except Exception as e:
        log.warning("Could not grant permissions on job %s: %s (non-fatal)", job_id, e)


def trigger_satellite_ecl_job(enabled_models: list[str] | None = None) -> dict:
    """Trigger the satellite model + ECL + sync job.

    Auto-creates the job if it doesn't exist yet.
    The job has 8 parallel model tasks + aggregator + ECL + sync.
    """
    job_id = _ensure_job(
        "satellite_ecl_sync",
        "IFRS9 ECL - Satellite Model + ECL + Sync",
        _build_satellite_ecl_job_def,
    )
    models = enabled_models or ALL_MODELS

    nb_params = _config_params()
    nb_params["enabled_models"] = ",".join(models)

    w = _get_workspace_client()
    try:
        run = w.jobs.run_now(job_id=job_id, notebook_params=nb_params)
        run_id = run.run_id
        log.info("Triggered satellite_ecl_sync job %s, run_id=%s, models=%s", job_id, run_id, models)
    except Exception as e:
        log.error("Failed to trigger job %s: %s", job_id, e)
        raise RuntimeError(f"Failed to trigger job: {e}")

    return {
        "run_id": run_id,
        "job_id": job_id,
        "models": models,
        "parallel": True,
        "run_url": f"{_ws_host()}/?o={_ws_id()}#job/{job_id}/run/{run_id}",
    }


def trigger_full_pipeline() -> dict:
    """Trigger the full ECL pipeline (data processing -> models -> ECL -> sync).

    Does NOT generate synthetic data. Customers map their own data via Admin config.
    """
    job_id = _ensure_job(
        "full_pipeline",
        "IFRS9 ECL - Full Pipeline",
        _build_full_pipeline_job_def,
    )
    nb_params = _config_params()

    w = _get_workspace_client()
    try:
        run = w.jobs.run_now(job_id=job_id, notebook_params=nb_params)
        run_id = run.run_id
    except Exception as e:
        log.error("Failed to trigger full pipeline job %s: %s", job_id, e)
        raise RuntimeError(f"Failed to trigger job: {e}")

    log.info("Triggered full_pipeline job %s, run_id=%s", job_id, run_id)
    return {
        "run_id": run_id,
        "job_id": job_id,
        "run_url": f"{_ws_host()}/?o={_ws_id()}#job/{job_id}/run/{run_id}",
    }


def trigger_demo_data_job() -> dict:
    """Generate synthetic demo data and process it. For demo/testing purposes only."""
    job_id = _ensure_job(
        "demo_data",
        "IFRS9 ECL - Generate Demo Data",
        _build_demo_data_job_def,
    )
    nb_params = _config_params()

    w = _get_workspace_client()
    try:
        run = w.jobs.run_now(job_id=job_id, notebook_params=nb_params)
        run_id = run.run_id
    except Exception as e:
        log.error("Failed to trigger demo data job %s: %s", job_id, e)
        raise RuntimeError(f"Failed to trigger job: {e}")

    log.info("Triggered demo_data job %s, run_id=%s", job_id, run_id)
    return {
        "run_id": run_id,
        "job_id": job_id,
        "run_url": f"{_ws_host()}/?o={_ws_id()}#job/{job_id}/run/{run_id}",
    }


def trigger_monte_carlo_job(
    n_simulations: int = 1000,
    pd_lgd_correlation: float = 0.30,
    aging_factor: float = 0.08,
    pd_floor: float = 0.001,
    pd_cap: float = 0.95,
    lgd_floor: float = 0.01,
    lgd_cap: float = 0.95,
    random_seed: int | None = None,
    scenario_weights: dict[str, float] | None = None,
) -> dict:
    """Trigger Monte Carlo simulation as a Databricks Job.

    Runs the vectorized simulation on serverless compute for better
    scalability and resource isolation.
    """
    import json as _json
    job_id = _ensure_job(
        "monte_carlo",
        "IFRS9 ECL - Monte Carlo Simulation",
        _build_monte_carlo_job_def,
    )

    nb_params = _config_params()
    nb_params["n_simulations"] = str(n_simulations)
    nb_params["pd_lgd_correlation"] = str(pd_lgd_correlation)
    nb_params["aging_factor"] = str(aging_factor)
    nb_params["pd_floor"] = str(pd_floor)
    nb_params["pd_cap"] = str(pd_cap)
    nb_params["lgd_floor"] = str(lgd_floor)
    nb_params["lgd_cap"] = str(lgd_cap)
    if random_seed is not None:
        nb_params["random_seed"] = str(random_seed)
    if scenario_weights:
        nb_params["scenario_weights"] = _json.dumps(scenario_weights)

    w = _get_workspace_client()
    try:
        run = w.jobs.run_now(job_id=job_id, notebook_params=nb_params)
        run_id = run.run_id
        log.info("Triggered monte_carlo job %s, run_id=%s, n_sims=%s", job_id, run_id, n_simulations)
    except Exception as e:
        log.error("Failed to trigger monte carlo job %s: %s", job_id, e)
        raise RuntimeError(f"Failed to trigger job: {e}")

    return {
        "run_id": run_id,
        "job_id": job_id,
        "n_simulations": n_simulations,
        "run_url": f"{_ws_host()}/?o={_ws_id()}#job/{job_id}/run/{run_id}",
    }


def get_run_status(run_id: int) -> dict:
    """Get the status of a specific job run."""
    w = _get_workspace_client()
    try:
        result = w.jobs.get_run(run_id=run_id)
        state = result.state
        tasks = []
        for t in (result.tasks or []):
            ts = t.state
            tasks.append({
                "task_key": t.task_key,
                "lifecycle_state": ts.life_cycle_state.value if ts and ts.life_cycle_state else None,
                "result_state": ts.result_state.value if ts and ts.result_state else None,
                "run_url": t.run_page_url,
                "execution_duration_ms": t.execution_duration or 0,
            })
        return {
            "run_id": result.run_id,
            "job_id": result.job_id,
            "lifecycle_state": state.life_cycle_state.value if state and state.life_cycle_state else None,
            "result_state": state.result_state.value if state and state.result_state else None,
            "state_message": state.state_message if state else "",
            "run_url": result.run_page_url,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "run_duration_ms": result.run_duration or 0,
            "tasks": tasks,
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get run status: {e}")


def list_job_runs(job_key: str, limit: int = 10) -> list[dict]:
    """List recent runs for a given job key."""
    job_ids = _get_job_ids()
    job_id = job_ids.get(job_key)
    if not job_id:
        return []
    w = _get_workspace_client()
    try:
        runs_iter = w.jobs.list_runs(job_id=int(job_id), limit=limit)
        runs = []
        for r in runs_iter:
            state = r.state
            runs.append({
                "run_id": r.run_id,
                "job_id": r.job_id,
                "lifecycle_state": state.life_cycle_state.value if state and state.life_cycle_state else None,
                "result_state": state.result_state.value if state and state.result_state else None,
                "state_message": state.state_message if state else "",
                "run_url": r.run_page_url,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "run_duration_ms": r.run_duration or 0,
            })
            if len(runs) >= limit:
                break
        return runs
    except Exception as e:
        log.warning("Failed to list runs for %s: %s", job_key, e)
        return []


def get_jobs_status() -> dict:
    """Return status of all managed jobs — useful for admin UI."""
    scripts_base = _detect_scripts_base()
    job_ids = _get_job_ids()
    result = {
        "scripts_base": scripts_base,
        "jobs": {},
    }
    w = _get_workspace_client()
    for key in ["satellite_ecl_sync", "full_pipeline", "demo_data", "monte_carlo"]:
        jid = job_ids.get(key)
        if jid:
            try:
                job = w.jobs.get(job_id=int(jid))
                task_count = len(job.settings.tasks) if job.settings and job.settings.tasks else 0
                paths_ok = all(
                    scripts_base in (t.notebook_task.notebook_path or "")
                    for t in (job.settings.tasks or [])
                    if t.notebook_task
                )
                result["jobs"][key] = {
                    "job_id": int(jid),
                    "name": job.settings.name if job.settings else "",
                    "task_count": task_count,
                    "paths_ok": paths_ok,
                    "status": "ok" if paths_ok else "needs_update",
                }
            except Exception as e:
                result["jobs"][key] = {"job_id": int(jid), "status": "error", "error": str(e)}
        else:
            result["jobs"][key] = {"job_id": None, "status": "not_created"}
    return result
