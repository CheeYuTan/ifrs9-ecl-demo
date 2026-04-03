"""Data query routes — /api/data/*"""
from fastapi import APIRouter, HTTPException
import backend
from routes._utils import df_to_records

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/portfolio-summary")
def portfolio_summary():
    try:
        return df_to_records(backend.get_portfolio_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load portfolio summary: {e}")

@router.get("/stage-distribution")
def stage_distribution():
    try:
        return df_to_records(backend.get_stage_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stage distribution: {e}")

@router.get("/borrower-segments")
def borrower_segments():
    try:
        return df_to_records(backend.get_borrower_segment_stats())
    except Exception as e:
        raise HTTPException(500, f"Failed to load borrower segments: {e}")

@router.get("/vintage-analysis")
def vintage_analysis():
    try:
        return df_to_records(backend.get_vintage_analysis())
    except Exception as e:
        raise HTTPException(500, f"Failed to load vintage analysis: {e}")

@router.get("/dpd-distribution")
def dpd_distribution():
    try:
        return df_to_records(backend.get_dpd_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load DPD distribution: {e}")

@router.get("/stage-by-product")
def stage_by_product():
    try:
        return df_to_records(backend.get_stage_by_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stage by product: {e}")

@router.get("/pd-distribution")
def pd_distribution():
    try:
        return df_to_records(backend.get_pd_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load PD distribution: {e}")

@router.get("/dq-results")
def dq_results():
    try:
        return df_to_records(backend.get_dq_results())
    except Exception as e:
        raise HTTPException(500, f"Failed to load DQ results: {e}")

@router.get("/dq-summary")
def dq_summary():
    try:
        return df_to_records(backend.get_dq_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load DQ summary: {e}")

@router.get("/gl-reconciliation")
def gl_reconciliation():
    try:
        return df_to_records(backend.get_gl_reconciliation())
    except Exception as e:
        raise HTTPException(500, f"Failed to load GL reconciliation: {e}")

@router.get("/ecl-summary")
def ecl_summary():
    try:
        return df_to_records(backend.get_ecl_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL summary: {e}")

@router.get("/ecl-by-product")
def ecl_by_product():
    try:
        return df_to_records(backend.get_ecl_by_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by product: {e}")

@router.get("/scenario-summary")
def scenario_summary():
    try:
        return df_to_records(backend.get_scenario_summary())
    except Exception as e:
        raise HTTPException(500, f"Failed to load scenario summary: {e}")

@router.get("/mc-distribution")
def mc_distribution():
    try:
        return df_to_records(backend.get_mc_distribution())
    except Exception as e:
        raise HTTPException(500, f"Failed to load MC distribution: {e}")

@router.get("/ecl-by-scenario-product")
def ecl_by_scenario_product():
    try:
        return df_to_records(backend.get_ecl_by_scenario_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by scenario product: {e}")

@router.get("/ecl-concentration")
def ecl_concentration():
    try:
        return df_to_records(backend.get_ecl_concentration())
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL concentration: {e}")

@router.get("/stage-migration")
def stage_migration():
    try:
        return df_to_records(backend.get_stage_migration())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stage migration: {e}")

@router.get("/credit-risk-exposure")
def credit_risk_exposure():
    try:
        return df_to_records(backend.get_credit_risk_exposure())
    except Exception as e:
        raise HTTPException(500, f"Failed to load credit risk exposure: {e}")

@router.get("/loss-allowance-by-stage")
def loss_allowance_by_stage():
    try:
        return df_to_records(backend.get_loss_allowance_by_stage())
    except Exception as e:
        raise HTTPException(500, f"Failed to load loss allowance by stage: {e}")

@router.get("/ecl-by-stage-product/{stage}")
def ecl_by_stage_product(stage: int):
    try:
        return df_to_records(backend.get_ecl_by_stage_product(stage))
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by stage-product: {e}")

@router.get("/ecl-by-scenario-product-detail")
def ecl_by_scenario_product_detail(scenario: str):
    try:
        return df_to_records(backend.get_ecl_by_scenario_product_detail(scenario))
    except Exception as e:
        raise HTTPException(500, f"Failed to load ECL by scenario-product: {e}")

@router.get("/top-exposures")
def top_exposures(limit: int = 20):
    try:
        return df_to_records(backend.get_top_exposures(limit))
    except Exception as e:
        raise HTTPException(500, f"Failed to load top exposures: {e}")

@router.get("/loans-by-product/{product_type}")
def loans_by_product(product_type: str):
    try:
        return df_to_records(backend.get_loans_by_product(product_type))
    except Exception as e:
        raise HTTPException(500, f"Failed to load loans by product: {e}")

@router.get("/loans-by-stage/{stage}")
def loans_by_stage(stage: int):
    try:
        return df_to_records(backend.get_loans_by_stage(stage))
    except Exception as e:
        raise HTTPException(500, f"Failed to load loans by stage: {e}")

@router.get("/sensitivity")
def sensitivity_data():
    try:
        return df_to_records(backend.get_sensitivity_data())
    except Exception as e:
        raise HTTPException(500, f"Failed to load sensitivity data: {e}")

@router.get("/scenario-comparison")
def scenario_comparison():
    try:
        return df_to_records(backend.get_scenario_comparison())
    except Exception as e:
        raise HTTPException(500, f"Failed to load scenario comparison: {e}")

@router.get("/stress-by-stage")
def stress_by_stage():
    try:
        return df_to_records(backend.get_stress_by_stage())
    except Exception as e:
        raise HTTPException(500, f"Failed to load stress by stage: {e}")

@router.get("/vintage-performance")
def vintage_performance():
    try:
        return df_to_records(backend.get_vintage_performance())
    except Exception as e:
        raise HTTPException(500, f"Failed to load vintage performance: {e}")

@router.get("/vintage-by-product")
def vintage_by_product():
    try:
        return df_to_records(backend.get_vintage_by_product())
    except Exception as e:
        raise HTTPException(500, f"Failed to load vintage by product: {e}")

@router.get("/concentration-by-segment")
def concentration_by_segment():
    try:
        return df_to_records(backend.get_concentration_by_segment())
    except Exception as e:
        raise HTTPException(500, f"Failed to load concentration by segment: {e}")

@router.get("/concentration-by-product-stage")
def concentration_by_product_stage():
    try:
        return df_to_records(backend.get_concentration_by_product_stage())
    except Exception as e:
        raise HTTPException(500, f"Failed to load concentration by product stage: {e}")

@router.get("/top-concentration-risk")
def top_concentration_risk():
    try:
        return df_to_records(backend.get_top_concentration_risk())
    except Exception as e:
        raise HTTPException(500, f"Failed to load top concentration risk: {e}")
