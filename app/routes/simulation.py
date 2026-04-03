"""Simulation routes — /api/simulate*"""
import json, queue, threading, logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["simulation"])


def _get_simulation_cap() -> int:
    """Get max simulation count from admin config, default 50000."""
    try:
        import admin_config
        cfg = admin_config.get_config()
        model = cfg.get("model", cfg.get("model_config", {}))
        params = model.get("default_parameters", model.get("default_params", {}))
        return int(params.get("max_simulations", 50000))
    except Exception:
        return 50000


def _persist_simulation_run(result: dict, config: "SimulationConfig"):
    """Persist simulation run metadata including seed to model_runs DB."""
    try:
        from domain.model_runs import save_model_run
        metadata = result.get("run_metadata", {})
        run_id = f"sim_{metadata.get('timestamp', 'unknown')}"
        products = [p["product_type"] for p in result.get("ecl_by_product", [])]
        summary = {
            "random_seed": metadata.get("random_seed"),
            "n_simulations": config.n_simulations,
            "total_ecl": sum(float(p.get("total_ecl", 0)) for p in result.get("ecl_by_product", [])),
            "total_gca": sum(float(p.get("total_gca", 0)) for p in result.get("ecl_by_product", [])),
            "duration_seconds": metadata.get("duration_seconds"),
            "convergence_by_product": metadata.get("convergence_by_product", {}),
            "ecl_by_product": {p["product_type"]: float(p.get("total_ecl", 0)) for p in result.get("ecl_by_product", [])},
        }
        save_model_run(
            run_id=run_id,
            run_type="monte_carlo_simulation",
            models_used=["monte_carlo"],
            products=products,
            total_cohorts=metadata.get("loan_count", 0),
            best_model_summary=summary,
            notes=f"seed={metadata.get('random_seed')}, n_sims={config.n_simulations}",
        )
        log.info("Persisted simulation run %s (seed=%s)", run_id, metadata.get("random_seed"))
    except Exception as e:
        log.warning("Failed to persist simulation run: %s", e)


class SimulationConfig(BaseModel):
    n_simulations: int = 1000
    pd_lgd_correlation: float = 0.30
    aging_factor: float = 0.08
    pd_floor: float = 0.001
    pd_cap: float = 0.95
    lgd_floor: float = 0.01
    lgd_cap: float = 0.95
    scenario_weights: Optional[dict[str, float]] = None
    random_seed: Optional[int] = None
    use_databricks_job: bool = False


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


def _run_pre_checks(config: SimulationConfig) -> list[dict]:
    """Run IFRS 9 pre-calculation validation checks against live portfolio data."""
    try:
        from domain.validation_rules import run_all_pre_calculation_checks, has_critical_failures
        import backend
        loans_df = backend.query_df(f"""
            SELECT current_lifetime_pd, effective_interest_rate,
                   remaining_months, gross_carrying_amount,
                   assessed_stage, days_past_due
            FROM {backend._t('model_ready_loans')}
            LIMIT 10000
        """)
        if loans_df.empty:
            return []
        weights = config.scenario_weights or {}
        stage_dpd = list(zip(
            loans_df["assessed_stage"].fillna(1).astype(int).tolist(),
            loans_df["days_past_due"].fillna(0).astype(int).tolist(),
        )) if "days_past_due" in loans_df.columns else None
        return run_all_pre_calculation_checks(
            scenario_weights=weights,
            pd_values=loans_df["current_lifetime_pd"].dropna().tolist(),
            lgd_values=[],
            eir_values=loans_df["effective_interest_rate"].dropna().tolist(),
            remaining_months=loans_df["remaining_months"].dropna().tolist(),
            gca_values=loans_df["gross_carrying_amount"].dropna().tolist(),
            stage_dpd_pairs=stage_dpd,
            aging_factor=config.aging_factor,
        )
    except Exception as exc:
        log.warning("Pre-calculation validation skipped: %s", exc)
        return []


@router.post("/simulate")
def run_simulation(config: SimulationConfig):
    """Run Monte Carlo ECL simulation with custom parameters."""
    from domain.validation_rules import has_critical_failures
    pre_checks = _run_pre_checks(config)
    if has_critical_failures(pre_checks):
        raise HTTPException(400, detail={
            "message": "Pre-calculation validation failed with critical errors",
            "validation_results": pre_checks,
        })
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
            random_seed=config.random_seed,
        )
        result = _transform_simulation_result(raw, config)
        result["validation_results"] = pre_checks
        _persist_simulation_run(result, config)
        return result
    except Exception as e:
        log.exception("Simulation failed")
        raise HTTPException(500, f"Simulation failed: {e}")


@router.get("/simulation-defaults")
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


@router.post("/simulate-stream")
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
                random_seed=config.random_seed,
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


@router.post("/simulate-job")
def simulate_via_job(config: SimulationConfig):
    """Run Monte Carlo simulation as a Databricks Job for scalable compute."""
    try:
        import jobs
        result = jobs.trigger_monte_carlo_job(
            n_simulations=config.n_simulations,
            pd_lgd_correlation=config.pd_lgd_correlation,
            aging_factor=config.aging_factor,
            pd_floor=config.pd_floor,
            pd_cap=config.pd_cap,
            lgd_floor=config.lgd_floor,
            lgd_cap=config.lgd_cap,
            random_seed=config.random_seed,
            scenario_weights=config.scenario_weights,
        )
        return result
    except Exception as e:
        log.exception("Failed to trigger Monte Carlo job")
        raise HTTPException(500, f"Failed to trigger simulation job: {e}")


@router.post("/simulate-validate")
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
    max_sims = _get_simulation_cap()
    if config.n_simulations > max_sims:
        errors.append(f"Maximum {max_sims:,} simulations")

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


@router.get("/simulation/compare")
def compare_simulation_runs(run_a: str, run_b: str):
    """Compare two simulation runs by product, stage, and scenario deltas."""
    try:
        from domain.model_runs import get_model_run
        a = get_model_run(run_a)
        b = get_model_run(run_b)
        if not a or not b:
            missing = [r for r, v in [(run_a, a), (run_b, b)] if not v]
            raise HTTPException(404, f"Run(s) not found: {', '.join(missing)}")

        summary_a = a.get("best_model_summary", {}) or {}
        summary_b = b.get("best_model_summary", {}) or {}

        deltas = []
        all_keys = set(list(summary_a.keys()) + list(summary_b.keys()))
        for key in sorted(all_keys):
            val_a = summary_a.get(key)
            val_b = summary_b.get(key)
            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                abs_delta = round(val_b - val_a, 4)
                pct_delta = round((val_b - val_a) / val_a * 100, 2) if val_a != 0 else None
                deltas.append({"metric": key, "run_a": val_a, "run_b": val_b,
                               "absolute_delta": abs_delta, "relative_delta_pct": pct_delta})

        # Per-product ECL breakdown comparison
        product_deltas = _build_product_deltas(summary_a, summary_b)

        return {
            "run_a": {"run_id": run_a, "timestamp": str(a.get("run_timestamp")),
                      "type": a.get("run_type"), "products": a.get("products"),
                      "seed": summary_a.get("random_seed")},
            "run_b": {"run_id": run_b, "timestamp": str(b.get("run_timestamp")),
                      "type": b.get("run_type"), "products": b.get("products"),
                      "seed": summary_b.get("random_seed")},
            "deltas": deltas,
            "product_deltas": product_deltas,
            "summary": {
                "metrics_compared": len(deltas),
                "metrics_improved": sum(1 for d in deltas if d["absolute_delta"] and d["absolute_delta"] < 0),
                "metrics_degraded": sum(1 for d in deltas if d["absolute_delta"] and d["absolute_delta"] > 0),
                "products_compared": len(product_deltas),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Comparison failed: {e}")


def _build_product_deltas(summary_a: dict, summary_b: dict) -> list[dict]:
    """Build per-product ECL deltas from ecl_by_product stored in run summaries."""
    ecl_a = summary_a.get("ecl_by_product", {}) or {}
    ecl_b = summary_b.get("ecl_by_product", {}) or {}
    all_products = sorted(set(list(ecl_a.keys()) + list(ecl_b.keys())))
    result = []
    for prod in all_products:
        va = float(ecl_a.get(prod, 0))
        vb = float(ecl_b.get(prod, 0))
        abs_delta = round(vb - va, 2)
        pct_delta = round((vb - va) / va * 100, 2) if va != 0 else None
        result.append({
            "product_type": prod,
            "run_a_ecl": va,
            "run_b_ecl": vb,
            "absolute_delta": abs_delta,
            "relative_delta_pct": pct_delta,
        })
    return result
