"""
ECL Engine -- result aggregation and metadata assembly.

Builds portfolio summaries, scenario results, product-scenario breakdowns,
stage summaries, convergence diagnostics, and run metadata from raw
simulation outputs.
"""
import time
import logging

import numpy as np
import pandas as pd

from ecl.helpers import _emit, _df_to_records

log = logging.getLogger(__name__)


def aggregate_results(
    *,
    loans_df: pd.DataFrame,
    loan_weighted_ecl: np.ndarray,
    scenario_ecl_totals: dict[str, np.ndarray],
    scenario_ecl_paths: dict[str, np.ndarray],
    product_sim_ecls: dict[str, np.ndarray],
    products: np.ndarray,
    scenarios: list[str],
    weights: dict[str, float],
    n_sims: int,
    n_loans: int,
    sim_params: dict,
    t0: float,
    load_time: float,
    progress_callback=None,
) -> dict:
    """Aggregate raw simulation arrays into the final result dict."""
    t_agg_start = time.time()
    _emit(progress_callback, {
        "phase": "aggregating", "step": "aggregating",
        "message": "Aggregating results across scenarios...",
        "progress": 92, "elapsed": round(time.time() - t0, 2),
    })

    loans_df["weighted_ecl"] = loan_weighted_ecl

    # Portfolio summary: by product_type and stage
    portfolio_summary = (
        loans_df.groupby(["product_type", "stage"])
        .agg(
            loan_count=("loan_id", "count"),
            total_gca=("gca", "sum"),
            total_ecl=("weighted_ecl", "sum"),
        )
        .reset_index()
    )
    portfolio_summary["coverage_ratio"] = (
        portfolio_summary["total_ecl"] / portfolio_summary["total_gca"].replace(0, np.nan) * 100
    ).round(4)
    portfolio_summary = portfolio_summary.rename(columns={"stage": "stage"})

    # Scenario results with distribution stats
    scenario_results = []
    for sc in scenarios:
        paths = scenario_ecl_paths[sc]
        ecl_mean = float(paths.mean())
        scenario_results.append({
            "scenario": sc,
            "weight": weights[sc],
            "total_ecl": round(ecl_mean, 2),
            "ecl_mean": round(ecl_mean, 2),
            "ecl_p50": round(float(np.percentile(paths, 50)), 2),
            "ecl_p75": round(float(np.percentile(paths, 75)), 2),
            "ecl_p95": round(float(np.percentile(paths, 95)), 2),
            "ecl_p99": round(float(np.percentile(paths, 99)), 2),
        })

    # Product x scenario breakdown
    product_scenario = []
    unique_products = loans_df["product_type"].unique()
    for sc in scenarios:
        sc_ecl = scenario_ecl_totals[sc]
        for prod in unique_products:
            mask = products == prod
            product_scenario.append({
                "product_type": prod,
                "scenario": sc,
                "total_ecl": round(float(sc_ecl[mask].sum()), 2),
            })

    # Stage summary
    stage_summary = (
        loans_df.groupby("stage")
        .agg(
            loan_count=("loan_id", "count"),
            total_gca=("gca", "sum"),
            total_ecl=("weighted_ecl", "sum"),
        )
        .reset_index()
    )

    duration = time.time() - t0

    # Convergence diagnostics per product
    convergence_by_product = {}
    for prod in unique_products:
        mask = products == prod
        sim_ecls = product_sim_ecls[prod]
        prod_mean = float(sim_ecls.mean()) if n_sims > 0 else 0.0
        prod_std = float(sim_ecls.std()) if n_sims > 1 else 0.0
        se = prod_std / (n_sims ** 0.5) if n_sims > 0 else 0.0
        ci_width = 1.96 * se
        prod_total = float(loan_weighted_ecl[mask].sum())
        convergence_by_product[prod] = {
            "mean_ecl": round(prod_total, 2),
            "std_ecl": round(prod_std, 2),
            "ci_95_width": round(ci_width, 2),
            "ci_95_pct": round(ci_width / prod_total * 100, 2) if prod_total > 0 else 0.0,
        }

    run_metadata = {
        **sim_params,
        "timestamp": pd.Timestamp.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "loan_count": n_loans,
        "scenario_count": len(scenarios),
        "convergence_by_product": convergence_by_product,
    }

    log.info(
        "Simulation complete: %d loans, %d scenarios, %d sims in %.1fs",
        n_loans, len(scenarios), n_sims, duration,
    )

    total_ecl = float(loan_weighted_ecl.sum())
    t_agg_done = time.time()
    agg_time = round(t_agg_done - t_agg_start, 2)
    compute_time = round(duration - load_time - agg_time, 2)
    _emit(progress_callback, {
        "phase": "done", "step": "complete",
        "message": f"Simulation complete: {n_loans:,} loans x {len(scenarios)} scenarios x {n_sims:,} sims in {duration:.1f}s",
        "progress": 100, "elapsed": round(duration, 2),
        "detail": {
            "total_ecl": round(total_ecl, 2),
            "duration": round(duration, 2),
            "load_time": load_time,
            "compute_time": compute_time,
            "aggregation_time": agg_time,
            "loans_per_second": round(n_loans * len(scenarios) / duration, 0) if duration > 0 else 0,
        },
    })

    return {
        "portfolio_summary": _df_to_records(portfolio_summary),
        "scenario_results": scenario_results,
        "product_scenario": product_scenario,
        "stage_summary": _df_to_records(stage_summary),
        "run_metadata": run_metadata,
    }
