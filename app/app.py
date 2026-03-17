"""
IFRS 9 ECL — FastAPI Backend serving React frontend.
Powered by Databricks Lakebase.
"""
import os, logging, json, queue, threading
from contextlib import asynccontextmanager
from decimal import Decimal
from datetime import datetime, date
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import backend

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def df_to_records(df):
    return json.loads(json.dumps(df.to_dict("records"), cls=DecimalEncoder))


def _transform_simulation_result(raw: dict, config) -> dict:
    """Shared transformation from ecl_engine output to frontend-expected format."""
    stage_summary = raw.get("stage_summary", [])
    for row in stage_summary:
        gca_val = float(row.get("total_gca", 0) or 0)
        ecl_val = float(row.get("total_ecl", 0) or 0)
        row["assessed_stage"] = row.pop("stage", row.get("assessed_stage"))
        row["coverage_pct"] = round(ecl_val / gca_val * 100, 2) if gca_val else 0

    scenario_results = raw.get("scenario_results", [])
    for row in scenario_results:
        w = float(row.get("weight", 0))
        ecl_val = float(row.get("total_ecl", 0))
        row["weighted"] = round(ecl_val * w, 2)
        row.setdefault("weighted_contribution", round(ecl_val * w, 2))

    portfolio = raw.get("portfolio_summary", [])
    product_agg: dict[str, dict] = {}
    for row in portfolio:
        pt = row.get("product_type", "unknown")
        if pt not in product_agg:
            product_agg[pt] = {"product_type": pt, "loan_count": 0, "total_gca": 0.0, "total_ecl": 0.0}
        product_agg[pt]["loan_count"] += int(row.get("loan_count", 0))
        product_agg[pt]["total_gca"] += float(row.get("total_gca", 0))
        product_agg[pt]["total_ecl"] += float(row.get("total_ecl", 0))
    for v in product_agg.values():
        v["coverage_ratio"] = round(v["total_ecl"] / v["total_gca"] * 100, 2) if v["total_gca"] else 0

    return {
        "ecl_by_product": list(product_agg.values()),
        "scenario_summary": scenario_results,
        "loss_allowance_by_stage": stage_summary,
        "ecl_by_scenario_product": raw.get("product_scenario", []),
        "run_metadata": raw.get("run_metadata", {}),
        "n_simulations": config.n_simulations,
        "pd_lgd_correlation": config.pd_lgd_correlation,
    }


@asynccontextmanager
async def lifespan(app):
    log.info("Initializing Lakebase pool...")
    backend.init_pool()
    log.info("Lakebase ready.")
    yield


app = FastAPI(title="IFRS 9 ECL API", lifespan=lifespan)


@app.get("/api/health")
def health_check():
    try:
        df = backend.query_df("SELECT 1 as ok")
        return {"status": "healthy", "lakebase": "connected", "rows": len(df)}
    except Exception as e:
        return {"status": "degraded", "lakebase": "error", "error": str(e)}


# ── Workflow endpoints ───────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    project_id: str
    project_name: str
    project_type: str = "ifrs9"
    description: str = ""
    reporting_date: str = ""

class StepAction(BaseModel):
    action: str
    user: str
    detail: str = ""
    status: str = "completed"

class OverlayItem(BaseModel):
    id: str
    product: str
    type: str
    amount: float
    reason: str
    ifrs9: str = ""

class OverlaySave(BaseModel):
    overlays: list[OverlayItem]
    comment: str = ""

class ScenarioWeights(BaseModel):
    weights: dict[str, float]

class SignOff(BaseModel):
    name: str


def serialize_project(proj):
    if proj is None:
        return None
    return json.loads(json.dumps(proj, cls=DecimalEncoder))


@app.get("/api/projects")
def list_projects():
    return df_to_records(backend.list_projects())

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    p = backend.get_project(project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return serialize_project(p)

@app.post("/api/projects")
def create_project(body: ProjectCreate):
    p = backend.create_project(body.project_id, body.project_name, body.project_type, body.description, body.reporting_date)
    return serialize_project(p)

@app.post("/api/projects/{project_id}/advance")
def advance_step(project_id: str, body: StepAction):
    try:
        p = backend.advance_step(project_id, body.action, body.action, body.user, body.detail, body.status)
        return serialize_project(p)
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.post("/api/projects/{project_id}/overlays")
def save_overlays(project_id: str, body: OverlaySave):
    overlays = [o.model_dump() for o in body.overlays]
    p = backend.save_overlays(project_id, overlays)
    if body.comment:
        p = backend.advance_step(project_id, "overlays", "Overlays Submitted", "Credit Risk Analyst", body.comment)
    return serialize_project(p)

@app.post("/api/projects/{project_id}/scenario-weights")
def save_weights(project_id: str, body: ScenarioWeights):
    p = backend.save_scenario_weights(project_id, body.weights)
    return serialize_project(p)

@app.post("/api/projects/{project_id}/sign-off")
def sign_off(project_id: str, body: SignOff):
    p = backend.sign_off_project(project_id, body.name)
    return serialize_project(p)

@app.post("/api/projects/{project_id}/reset")
def reset_project(project_id: str):
    try:
        p = backend.reset_project(project_id)
        return serialize_project(p)
    except Exception as e:
        raise HTTPException(400, str(e))


# ── Data endpoints ───────────────────────────────────────────────────────────

@app.get("/api/data/portfolio-summary")
def portfolio_summary():
    try:
        return df_to_records(backend.get_portfolio_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load portfolio summary: {e}")

@app.get("/api/data/stage-distribution")
def stage_distribution():
    try:
        return df_to_records(backend.get_stage_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stage distribution: {e}")

@app.get("/api/data/borrower-segments")
def borrower_segments():
    try:
        return df_to_records(backend.get_borrower_segment_stats())
    except Exception as e:
        raise HTTPException(500, f"Failed to load borrower segments: {e}")

@app.get("/api/data/vintage-analysis")
def vintage_analysis():
    try:
        return df_to_records(backend.get_vintage_analysis())
    except Exception as e:
        raise HTTPException(500, f"Failed to load vintage analysis: {e}")

@app.get("/api/data/dpd-distribution")
def dpd_distribution():
    try:
        return df_to_records(backend.get_dpd_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load DPD distribution: {e}")

@app.get("/api/data/stage-by-product")
def stage_by_product():
    try:
        return df_to_records(backend.get_stage_by_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stage by product: {e}")

@app.get("/api/data/pd-distribution")
def pd_distribution():
    try:
        return df_to_records(backend.get_pd_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load PD distribution: {e}")

@app.get("/api/data/dq-results")
def dq_results():
    try:
        return df_to_records(backend.get_dq_results())
    except Exception as e:
        raise HTTPException(500, f"Failed to load DQ results: {e}")

@app.get("/api/data/dq-summary")
def dq_summary():
    try:
        return df_to_records(backend.get_dq_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load DQ summary: {e}")

@app.get("/api/data/gl-reconciliation")
def gl_reconciliation():
    try:
        return df_to_records(backend.get_gl_reconciliation())
    except Exception as e:
        raise HTTPException(500, f"Failed to load GL reconciliation: {e}")

@app.get("/api/data/ecl-summary")
def ecl_summary():
    try:
        return df_to_records(backend.get_ecl_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL summary: {e}")

@app.get("/api/data/ecl-by-product")
def ecl_by_product():
    try:
        return df_to_records(backend.get_ecl_by_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by product: {e}")

@app.get("/api/data/scenario-summary")
def scenario_summary():
    try:
        return df_to_records(backend.get_scenario_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load scenario summary: {e}")

@app.get("/api/data/mc-distribution")
def mc_distribution():
    try:
        return df_to_records(backend.get_mc_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load MC distribution: {e}")

@app.get("/api/data/ecl-by-scenario-product")
def ecl_by_scenario_product():
    try:
        return df_to_records(backend.get_ecl_by_scenario_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by scenario product: {e}")

@app.get("/api/data/ecl-concentration")
def ecl_concentration():
    try:
        return df_to_records(backend.get_ecl_concentration())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL concentration: {e}")

@app.get("/api/data/stage-migration")
def stage_migration():
    try:
        return df_to_records(backend.get_stage_migration())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stage migration: {e}")

@app.get("/api/data/credit-risk-exposure")
def credit_risk_exposure():
    try:
        return df_to_records(backend.get_credit_risk_exposure())
    except Exception as e:
        raise HTTPException(500, f"Failed to load credit risk exposure: {e}")

@app.get("/api/data/loss-allowance-by-stage")
def loss_allowance_by_stage():
    try:
        return df_to_records(backend.get_loss_allowance_by_stage())
    except Exception as e:
        raise HTTPException(500, f"Failed to load loss allowance by stage: {e}")

@app.get("/api/data/top-exposures")
def top_exposures(limit: int = 20):
    try:
        return df_to_records(backend.get_top_exposures(limit))
    except Exception as e:
        raise HTTPException(500, f"Failed to load top exposures: {e}")

@app.get("/api/data/loans-by-product/{product_type}")
def loans_by_product(product_type: str):
    try:
        return df_to_records(backend.get_loans_by_product(product_type))
    except Exception as e:
        raise HTTPException(500, f"Failed to load loans by product: {e}")

@app.get("/api/data/loans-by-stage/{stage}")
def loans_by_stage(stage: int):
    try:
        return df_to_records(backend.get_loans_by_stage(stage))
    except Exception as e:
        raise HTTPException(500, f"Failed to load loans by stage: {e}")

@app.get("/api/data/sensitivity")
def sensitivity_data():
    try:
        return df_to_records(backend.get_sensitivity_data())
    except Exception as e:
        raise HTTPException(500, f"Failed to load sensitivity data: {e}")

@app.get("/api/data/scenario-comparison")
def scenario_comparison():
    try:
        return df_to_records(backend.get_scenario_comparison())
    except Exception as e:
        raise HTTPException(500, f"Failed to load scenario comparison: {e}")

@app.get("/api/data/stress-by-stage")
def stress_by_stage():
    try:
        return df_to_records(backend.get_stress_by_stage())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stress by stage: {e}")

@app.get("/api/data/vintage-performance")
def vintage_performance():
    try:
        return df_to_records(backend.get_vintage_performance())
    except Exception as e:
        raise HTTPException(500, f"Failed to load vintage performance: {e}")

@app.get("/api/data/vintage-by-product")
def vintage_by_product():
    try:
        return df_to_records(backend.get_vintage_by_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load vintage by product: {e}")

@app.get("/api/data/concentration-by-segment")
def concentration_by_segment():
    try:
        return df_to_records(backend.get_concentration_by_segment())
    except Exception as e:
        raise HTTPException(500, f"Failed to load concentration by segment: {e}")

@app.get("/api/data/concentration-by-product-stage")
def concentration_by_product_stage():
    try:
        return df_to_records(backend.get_concentration_by_product_stage())
    except Exception as e:
        raise HTTPException(500, f"Failed to load concentration by product stage: {e}")

@app.get("/api/data/top-concentration-risk")
def top_concentration_risk():
    try:
        return df_to_records(backend.get_top_concentration_risk())
    except Exception as e:
        raise HTTPException(500, f"Failed to load top concentration risk: {e}")


# ── Simulation endpoints ──────────────────────────────────────────────────────

class SimulationConfig(BaseModel):
    n_simulations: int = 1000
    pd_lgd_correlation: float = 0.30
    aging_factor: float = 0.08
    pd_floor: float = 0.001
    pd_cap: float = 0.95
    lgd_floor: float = 0.01
    lgd_cap: float = 0.95
    scenario_weights: Optional[dict[str, float]] = None


@app.post("/api/simulate")
def run_simulation(config: SimulationConfig):
    """Run Monte Carlo ECL simulation with custom parameters."""
    try:
        import ecl_engine
        raw = ecl_engine.run_simulation(
            n_sims=config.n_simulations,
            pd_lgd_correlation=config.pd_lgd_correlation,
            aging_factor=config.aging_factor,
            pd_floor=config.pd_floor,
            pd_cap=config.pd_cap,
            lgd_floor=config.lgd_floor,
            lgd_cap=config.lgd_cap,
            scenario_weights=config.scenario_weights,
        )
        return _transform_simulation_result(raw, config)
    except Exception as e:
        log.exception("Simulation failed")
        raise HTTPException(500, f"Simulation failed: {e}")


@app.get("/api/simulation-defaults")
def simulation_defaults():
    """Get default simulation parameters and available scenarios.

    Returns a flat structure matching what the frontend SimulationPanel expects:
    n_simulations, pd_lgd_correlation, aging_factor, pd_floor, pd_cap,
    lgd_floor, lgd_cap, scenario_weights.
    """
    try:
        import ecl_engine
        raw = ecl_engine.get_defaults()
        params = raw.get("default_params", {})
        return {
            "n_simulations": params.get("n_sims", 1000),
            "pd_lgd_correlation": params.get("pd_lgd_correlation", 0.30),
            "aging_factor": params.get("aging_factor", 0.08),
            "pd_floor": params.get("pd_floor", 0.001),
            "pd_cap": params.get("pd_cap", 0.95),
            "lgd_floor": params.get("lgd_floor", 0.01),
            "lgd_cap": params.get("lgd_cap", 0.95),
            "scenario_weights": raw.get("default_weights", {}),
            "scenarios": raw.get("scenarios", []),
            "products": raw.get("products", []),
        }
    except Exception as e:
        log.exception("Failed to load simulation defaults")
        raise HTTPException(500, f"Failed to load defaults: {e}")


@app.post("/api/simulate-stream")
async def simulate_stream(config: SimulationConfig):
    """Run simulation with streaming progress via SSE."""
    progress_queue: queue.Queue = queue.Queue()
    result_holder: list = [None]
    error_holder: list = [None]

    def progress_cb(event):
        progress_queue.put(event)

    def run_in_thread():
        try:
            import ecl_engine
            raw = ecl_engine.run_simulation(
                n_sims=config.n_simulations,
                pd_lgd_correlation=config.pd_lgd_correlation,
                aging_factor=config.aging_factor,
                pd_floor=config.pd_floor,
                pd_cap=config.pd_cap,
                lgd_floor=config.lgd_floor,
                lgd_cap=config.lgd_cap,
                scenario_weights=config.scenario_weights,
                progress_callback=progress_cb,
            )
            result_holder[0] = _transform_simulation_result(raw, config)
        except Exception as e:
            error_holder[0] = str(e)
        finally:
            progress_queue.put(None)

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    async def event_generator():
        while True:
            try:
                event = progress_queue.get(timeout=0.5)
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                continue

            if event is None:
                if error_holder[0]:
                    yield f"data: {json.dumps({'type': 'error', 'message': error_holder[0]})}\n\n"
                elif result_holder[0]:
                    result_payload = {"type": "result", "data": result_holder[0]}
                    yield f"data: {json.dumps(result_payload, cls=DecimalEncoder)}\n\n"
                break
            else:
                yield f"data: {json.dumps({'type': 'progress', **event})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/simulate-validate")
def validate_simulation(config: SimulationConfig):
    """Validate simulation parameters before running."""
    warnings = []
    errors = []

    if config.pd_floor >= config.pd_cap:
        errors.append("PD Floor must be less than PD Cap")
    if config.lgd_floor >= config.lgd_cap:
        errors.append("LGD Floor must be less than LGD Cap")
    if config.n_simulations < 100:
        errors.append("Minimum 100 simulations required")
    if config.n_simulations > 5000:
        errors.append("Maximum 5000 simulations")

    if config.scenario_weights:
        total = sum(config.scenario_weights.values())
        if abs(total - 1.0) > 0.01:
            errors.append(f"Scenario weights must sum to 100% (currently {total*100:.1f}%)")

    if config.n_simulations > 2000:
        warnings.append(f"Running {config.n_simulations:,} simulations may take 3-5 minutes for ~84K loans")
    if config.n_simulations < 500:
        warnings.append("Fewer than 500 simulations may produce unstable ECL estimates")
    if config.pd_lgd_correlation > 0.7:
        warnings.append("Very high PD-LGD correlation (>70%) may produce extreme tail risk")
    if config.aging_factor > 0.15:
        warnings.append("High aging factor (>15%) significantly increases Stage 2/3 ECL")

    estimated_seconds = config.n_simulations * 0.02 + 5
    estimated_memory_mb = config.n_simulations * 84000 * 8 / 1e6 * 2

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "estimated_seconds": round(estimated_seconds, 0),
        "estimated_memory_mb": round(estimated_memory_mb, 0),
    }


# ── Serve React build ────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DATABRICKS_APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
