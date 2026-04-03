"""Satellite model, model runs, cohort summary, and drill-down routes."""
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import backend
from routes._utils import df_to_records, DecimalEncoder, serialize_project

router = APIRouter(prefix="/api", tags=["satellite"])


class SaveRunRequest(BaseModel):
    run_id: str
    run_type: str = "satellite_model"
    models_used: list[str] = []
    products: list[str] = []
    total_cohorts: int = 0
    best_model_summary: dict = {}
    notes: str = ""


@router.get("/data/satellite-model-comparison")
def satellite_model_comparison(run_id: Optional[str] = None):
    try:
        return df_to_records(backend.get_satellite_model_comparison(run_id))
    except Exception as e:
        raise HTTPException(500, f"Failed to load satellite model comparison: {e}")

@router.get("/data/satellite-model-selected")
def satellite_model_selected(run_id: Optional[str] = None):
    try:
        return df_to_records(backend.get_satellite_model_selected(run_id))
    except Exception as e:
        raise HTTPException(500, f"Failed to load satellite model selected: {e}")

@router.get("/model-runs")
def list_model_runs(run_type: Optional[str] = None):
    try:
        df = backend.list_model_runs(run_type)
        records = df_to_records(df)
        for r in records:
            for col in ("models_used", "products", "best_model_summary"):
                if isinstance(r.get(col), str):
                    try:
                        r[col] = json.loads(r[col])
                    except Exception:
                        pass
        return records
    except Exception as e:
        raise HTTPException(500, f"Failed to load model runs: {e}")

@router.get("/model-runs/{run_id}")
def get_model_run(run_id: str):
    try:
        run = backend.get_model_run(run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        return serialize_project(run)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to load model run: {e}")

@router.post("/model-runs")
def save_model_run(body: SaveRunRequest):
    try:
        run = backend.save_model_run(
            body.run_id, body.run_type, body.models_used, body.products,
            body.total_cohorts, body.best_model_summary, body.notes,
        )
        return serialize_project(run)
    except Exception as e:
        raise HTTPException(500, f"Failed to save model run: {e}")

@router.get("/data/cohort-summary")
def cohort_summary():
    try:
        return df_to_records(backend.get_cohort_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load cohort summary: {e}")

@router.get("/data/cohort-summary/{product}")
def cohort_summary_by_product(product: str):
    try:
        return df_to_records(backend.get_cohort_summary_by_product(product))
    except Exception as e:
        raise HTTPException(500, f"Failed to load cohort summary: {e}")

@router.get("/data/drill-down-dimensions")
def drill_down_dimensions(product: str = "any"):
    try:
        return backend.get_drill_down_dimensions(product)
    except Exception as e:
        raise HTTPException(500, f"Failed to load dimensions: {e}")

@router.get("/data/ecl-by-cohort")
def ecl_by_cohort(product: str, dimension: str = "risk_band"):
    try:
        return df_to_records(backend.get_ecl_by_cohort(product, dimension))
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by cohort: {e}")

@router.get("/data/stage-by-cohort")
def stage_by_cohort(product: str):
    try:
        return df_to_records(backend.get_stage_by_cohort(product))
    except Exception as e:
        raise HTTPException(500, f"Failed to load stage by cohort: {e}")

@router.get("/data/portfolio-by-cohort")
def portfolio_by_cohort(product: str, dimension: str = "risk_band"):
    try:
        return df_to_records(backend.get_portfolio_by_dimension(product, dimension))
    except Exception as e:
        raise HTTPException(500, f"Failed to load portfolio by cohort: {e}")

@router.get("/data/ecl-by-product-drilldown")
def ecl_by_product_drilldown():
    try:
        return df_to_records(backend.get_ecl_by_product_drilldown())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by product drilldown: {e}")
