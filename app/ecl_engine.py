"""
In-App IFRS 9 ECL Simulation Engine
====================================
Lightweight Monte Carlo ECL calculator that reads loan data from Lakebase
and runs vectorized simulations with user-configurable parameters.

Methodology mirrors scripts/03_run_ecl_calculation.py:
  - 8 macro scenarios with product-specific PD/LGD multipliers
  - Correlated PD-LGD draws via Cholesky decomposition
  - PD term structure: flat hazard (Stage 1), increasing hazard (Stage 2/3)
  - Amortizing EAD with prepayment adjustment
  - Quarterly discounting at EIR
  - Stage 1 → 12-month horizon, Stage 2/3 → remaining life
"""
import time
import logging
import numpy as np
import pandas as pd
import backend

log = logging.getLogger(__name__)

SCHEMA = "expected_credit_loss"
PREFIX = "lb_"

BASE_LGD = {
    "credit_builder": 0.35,
    "emergency_microloan": 0.55,
    "career_transition": 0.45,
    "bnpl_professional": 0.50,
    "payroll_advance": 0.60,
}

SATELLITE_COEFFICIENTS = {
    "credit_builder": {
        "pd_lgd_corr": 0.25, "annual_prepay_rate": 0.08, "lgd_std": 0.10,
    },
    "emergency_microloan": {
        "pd_lgd_corr": 0.35, "annual_prepay_rate": 0.05, "lgd_std": 0.15,
    },
    "career_transition": {
        "pd_lgd_corr": 0.30, "annual_prepay_rate": 0.12, "lgd_std": 0.12,
    },
    "bnpl_professional": {
        "pd_lgd_corr": 0.28, "annual_prepay_rate": 0.03, "lgd_std": 0.13,
    },
    "payroll_advance": {
        "pd_lgd_corr": 0.40, "annual_prepay_rate": 0.02, "lgd_std": 0.16,
    },
}
DEFAULT_SAT = {"pd_lgd_corr": 0.30, "annual_prepay_rate": 0.05, "lgd_std": 0.15}

DEFAULT_SCENARIO_WEIGHTS = {
    "baseline": 0.30, "mild_recovery": 0.15, "strong_growth": 0.05,
    "mild_downturn": 0.15, "adverse": 0.15, "stagflation": 0.08,
    "severely_adverse": 0.07, "tail_risk": 0.05,
}


def _t(name: str) -> str:
    return f"{SCHEMA}.{PREFIX}{name}"


def _load_loans() -> pd.DataFrame:
    return backend.query_df(f"""
        SELECT loan_id, product_type, assessed_stage,
               gross_carrying_amount, effective_interest_rate,
               current_lifetime_pd, remaining_months
        FROM {_t('model_ready_loans')}
    """)


def _load_scenarios() -> pd.DataFrame:
    return backend.query_df(f"""
        SELECT scenario, weight, ecl_mean, ecl_p50, ecl_p75, ecl_p95, ecl_p99,
               avg_pd_multiplier, avg_lgd_multiplier, pd_vol, lgd_vol, n_simulations
        FROM {_t('mc_ecl_distribution')}
    """)


def _emit(cb, event):
    """Call progress_callback if provided."""
    if cb:
        cb(event)


def _convergence_check(ecl_sims: np.ndarray, n_sims: int) -> dict:
    """Compute ECL convergence at 25/50/75/100% of sims."""
    checkpoints = {}
    for pct in (0.25, 0.50, 0.75, 1.0):
        k = max(1, int(n_sims * pct))
        subset_mean = ecl_sims[:, :k].mean(axis=1).sum()
        checkpoints[f"ecl_at_{int(pct*100)}pct_sims"] = float(subset_mean)
    values = list(checkpoints.values())
    mean_val = np.mean(values)
    std_val = np.std(values)
    checkpoints["coefficient_of_variation"] = round(float(std_val / mean_val) if mean_val != 0 else 0.0, 6)
    return checkpoints


def _convergence_check_from_paths(portfolio_paths: np.ndarray, n_sims: int) -> dict:
    """Compute ECL convergence from portfolio-level path totals."""
    checkpoints = {}
    for pct in (0.25, 0.50, 0.75, 1.0):
        k = max(1, int(n_sims * pct))
        checkpoints[f"ecl_at_{int(pct*100)}pct_sims"] = float(portfolio_paths[:k].mean())
    values = list(checkpoints.values())
    mean_val = np.mean(values)
    std_val = np.std(values)
    checkpoints["coefficient_of_variation"] = round(float(std_val / mean_val) if mean_val != 0 else 0.0, 6)
    return checkpoints


def run_simulation(
    n_sims: int = 1000,
    pd_lgd_correlation: float = 0.30,
    aging_factor: float = 0.08,
    pd_floor: float = 0.001,
    pd_cap: float = 0.95,
    lgd_floor: float = 0.01,
    lgd_cap: float = 0.95,
    scenario_weights: dict[str, float] | None = None,
    progress_callback=None,
) -> dict:
    """
    Run Monte Carlo ECL simulation across all loans and scenarios.

    Processes loans in batches per (product, stage, scenario) for full
    numpy vectorization — no per-loan Python loops.

    Args:
        progress_callback: Optional callable(dict) invoked at each major step
            with progress info (phase, step, message, progress %, elapsed, detail).
    """
    t0 = time.time()

    _emit(progress_callback, {
        "phase": "loading", "step": "loans",
        "message": "Loading loan data from Lakebase...",
        "progress": 0, "elapsed": 0.0,
    })

    loans_df = _load_loans()

    n_loans = len(loans_df)
    if n_loans == 0:
        raise ValueError("No loans found in model_ready_loans")

    n_products = loans_df["product_type"].nunique()
    n_stages = loans_df["assessed_stage"].nunique()
    total_gca = float(loans_df["gross_carrying_amount"].astype(float).sum())
    mem_mb = round(loans_df.memory_usage(deep=True).sum() / 1e6, 1)

    _emit(progress_callback, {
        "phase": "loading", "step": "loans_done",
        "message": f"Loaded {n_loans:,} loans ({n_products} products, {n_stages} stages)",
        "progress": 5, "elapsed": round(time.time() - t0, 2),
        "detail": {
            "loan_count": n_loans,
            "products": sorted(loans_df["product_type"].unique().tolist()),
            "stages": sorted(int(s) for s in loans_df["assessed_stage"].unique()),
            "total_gca": round(total_gca, 2),
            "memory_mb": mem_mb,
        },
    })

    scenarios_df = _load_scenarios()

    scenario_map = {}
    for _, row in scenarios_df.iterrows():
        scenario_map[row["scenario"]] = {
            "weight": float(row["weight"]),
            "pd_mult": float(row["avg_pd_multiplier"]),
            "lgd_mult": float(row["avg_lgd_multiplier"]),
            "pd_vol": float(row["pd_vol"]),
            "lgd_vol": float(row["lgd_vol"]),
        }

    weights = scenario_weights if scenario_weights else DEFAULT_SCENARIO_WEIGHTS
    scenarios = list(weights.keys())

    for sc in scenarios:
        if sc not in scenario_map:
            scenario_map[sc] = {
                "weight": weights[sc], "pd_mult": 1.0, "lgd_mult": 1.0,
                "pd_vol": 0.05, "lgd_vol": 0.03,
            }

    t_load_done = time.time()
    load_time = round(t_load_done - t0, 2)

    _emit(progress_callback, {
        "phase": "loading", "step": "scenarios_done",
        "message": f"Loaded {len(scenarios)} macro scenarios",
        "progress": 10, "elapsed": round(t_load_done - t0, 2),
        "detail": {"scenarios": scenarios},
    })

    loans_df["stage"] = loans_df["assessed_stage"].astype(int)
    loans_df["gca"] = loans_df["gross_carrying_amount"].astype(float)
    loans_df["eir"] = loans_df["effective_interest_rate"].astype(float)
    loans_df["base_pd"] = loans_df["current_lifetime_pd"].astype(float)
    loans_df["rem_q"] = (loans_df["remaining_months"].astype(int) // 3).clip(lower=1)
    loans_df["rem_months_f"] = loans_df["remaining_months"].astype(float).clip(lower=1)
    loans_df["base_lgd"] = loans_df["product_type"].map(BASE_LGD).fillna(0.50)

    rng = np.random.default_rng()

    loan_weighted_ecl = np.zeros(n_loans)
    scenario_ecl_totals = {sc: np.zeros(n_loans) for sc in scenarios}

    gca = loans_df["gca"].values
    eir = loans_df["eir"].values
    base_pd = loans_df["base_pd"].values
    stage = loans_df["stage"].values
    rem_q = loans_df["rem_q"].values
    rem_months_f = loans_df["rem_months_f"].values
    base_lgd_arr = loans_df["base_lgd"].values
    products = loans_df["product_type"].values

    product_corr = np.array([
        SATELLITE_COEFFICIENTS.get(p, DEFAULT_SAT)["pd_lgd_corr"]
        for p in products
    ])
    product_prepay = np.array([
        SATELLITE_COEFFICIENTS.get(p, DEFAULT_SAT)["annual_prepay_rate"]
        for p in products
    ])

    if pd_lgd_correlation != 0.30:
        product_corr[:] = pd_lgd_correlation

    quarterly_prepay = 1.0 - (1.0 - product_prepay) ** 0.25

    max_horizon_s1 = np.minimum(4, rem_q)
    max_horizon_lt = rem_q
    max_horizon = np.where(stage == 1, max_horizon_s1, max_horizon_lt)
    global_max_q = int(max_horizon.max())

    is_bullet = rem_months_f <= 3

    running_weighted_ecl = 0.0
    scenario_ecl_paths: dict[str, np.ndarray] = {}

    BATCH_SIZE = min(n_sims, 200)

    is_stage_23_1d = stage != 1
    rho_1d = product_corr

    for i, sc in enumerate(scenarios):
        sc_data = scenario_map[sc]
        w = weights[sc]
        pd_mult = sc_data["pd_mult"]
        lgd_mult = sc_data["lgd_mult"]
        pd_vol = sc_data["pd_vol"]
        lgd_vol = sc_data["lgd_vol"]

        _emit(progress_callback, {
            "phase": "computing", "step": "scenario_start",
            "scenario": sc, "scenario_index": i,
            "scenario_count": len(scenarios), "weight": w,
            "message": f"Scenario {i+1}/{len(scenarios)}: {sc} (weight: {w*100:.0f}%)",
            "progress": 10 + (i / len(scenarios)) * 80,
            "elapsed": round(time.time() - t0, 2),
        })

        loan_ecl_accum = np.zeros(n_loans)
        portfolio_path_ecls = np.zeros(n_sims)
        sims_done = 0

        while sims_done < n_sims:
            batch = min(BATCH_SIZE, n_sims - sims_done)

            z_pd = rng.standard_normal((n_loans, batch))
            z_lgd_indep = rng.standard_normal((n_loans, batch))

            rho = rho_1d[:, np.newaxis]
            z_lgd = rho * z_pd + np.sqrt(1 - rho ** 2) * z_lgd_indep

            pd_shocks = np.exp(z_pd * pd_vol - 0.5 * pd_vol ** 2)
            lgd_shocks = np.exp(z_lgd * lgd_vol - 0.5 * lgd_vol ** 2)

            stressed_pd = np.clip(
                base_pd[:, np.newaxis] * pd_mult * pd_shocks,
                pd_floor, pd_cap,
            )
            stressed_lgd = np.clip(
                base_lgd_arr[:, np.newaxis] * lgd_mult * lgd_shocks,
                lgd_floor, lgd_cap,
            )

            ecl_batch = np.zeros((n_loans, batch))
            survival = np.ones((n_loans, batch))

            for q in range(1, global_max_q + 1):
                active = max_horizon >= q
                if not active.any():
                    break

                quarterly_base_pd = 1.0 - (1.0 - stressed_pd) ** 0.25
                is_s23 = is_stage_23_1d[:, np.newaxis]
                aging = np.where(is_s23, 1.0 + aging_factor * (q - 1), 1.0)
                q_pd = np.clip(quarterly_base_pd * aging, 0, 0.99)

                default_this_q = survival * q_pd
                prepay_surv = (1.0 - quarterly_prepay[:, np.newaxis]) ** q
                amort = np.maximum(0.0, 1.0 - (q * 3) / rem_months_f[:, np.newaxis])
                ead_q = np.where(
                    is_bullet[:, np.newaxis],
                    gca[:, np.newaxis],
                    gca[:, np.newaxis] * amort * prepay_surv,
                )
                discount = 1.0 / ((1.0 + eir[:, np.newaxis] / 4.0) ** q)

                contribution = default_this_q * stressed_lgd * ead_q * discount
                contribution[~active] = 0.0
                ecl_batch += contribution
                survival *= (1.0 - q_pd)

            loan_ecl_accum += ecl_batch.sum(axis=1)
            portfolio_path_ecls[sims_done:sims_done + batch] = ecl_batch.sum(axis=0)
            sims_done += batch

        loan_ecl_mean = loan_ecl_accum / n_sims
        scenario_ecl_totals[sc] = loan_ecl_mean
        loan_weighted_ecl += loan_ecl_mean * w

        sc_ecl_total = float(portfolio_path_ecls.mean())
        running_weighted_ecl += sc_ecl_total * w

        scenario_ecl_paths[sc] = portfolio_path_ecls
        convergence = _convergence_check_from_paths(portfolio_path_ecls, n_sims)

        _emit(progress_callback, {
            "phase": "computing", "step": "scenario_done",
            "scenario": sc, "scenario_index": i,
            "scenario_ecl": float(sc_ecl_total),
            "cumulative_weighted_ecl": float(running_weighted_ecl),
            "message": f"Scenario {sc}: ECL = {sc_ecl_total:,.0f}",
            "progress": 10 + ((i + 1) / len(scenarios)) * 80,
            "elapsed": round(time.time() - t0, 2),
            "detail": {
                "scenario_ecl": round(float(sc_ecl_total), 2),
                "mean_pd_mult": pd_mult,
                "mean_lgd_mult": lgd_mult,
                "quarters_processed": global_max_q,
                "convergence": convergence,
            },
        })

    t_agg_start = time.time()
    _emit(progress_callback, {
        "phase": "aggregating", "step": "aggregating",
        "message": "Aggregating results across scenarios...",
        "progress": 92, "elapsed": round(time.time() - t0, 2),
    })

    loans_df["weighted_ecl"] = loan_weighted_ecl

    # --- Build result dicts ---

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

    run_metadata = {
        "n_sims": n_sims,
        "pd_lgd_correlation": pd_lgd_correlation,
        "aging_factor": aging_factor,
        "pd_floor": pd_floor,
        "pd_cap": pd_cap,
        "lgd_floor": lgd_floor,
        "lgd_cap": lgd_cap,
        "timestamp": pd.Timestamp.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "loan_count": n_loans,
        "scenario_count": len(scenarios),
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
        "message": f"Simulation complete: {n_loans:,} loans × {len(scenarios)} scenarios × {n_sims:,} sims in {duration:.1f}s",
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


def get_defaults() -> dict:
    """Return default simulation parameters, available scenarios, and product info."""
    scenarios_df = _load_scenarios()

    scenario_info = []
    for _, row in scenarios_df.iterrows():
        scenario_info.append({
            "scenario": row["scenario"],
            "weight": float(row["weight"]),
            "ecl_mean": float(row["ecl_mean"]),
            "ecl_p50": float(row["ecl_p50"]),
            "ecl_p75": float(row["ecl_p75"]),
            "ecl_p95": float(row["ecl_p95"]),
            "ecl_p99": float(row["ecl_p99"]),
            "avg_pd_multiplier": float(row["avg_pd_multiplier"]),
            "avg_lgd_multiplier": float(row["avg_lgd_multiplier"]),
            "pd_vol": float(row["pd_vol"]),
            "lgd_vol": float(row["lgd_vol"]),
        })

    product_info = []
    for product, lgd in BASE_LGD.items():
        sat = SATELLITE_COEFFICIENTS.get(product, DEFAULT_SAT)
        product_info.append({
            "product_type": product,
            "base_lgd": lgd,
            "pd_lgd_correlation": sat["pd_lgd_corr"],
            "annual_prepay_rate": sat["annual_prepay_rate"],
        })

    default_params = {
        "n_sims": 1000,
        "pd_lgd_correlation": 0.30,
        "aging_factor": 0.08,
        "pd_floor": 0.001,
        "pd_cap": 0.95,
        "lgd_floor": 0.01,
        "lgd_cap": 0.95,
    }

    result = {
        "scenarios": scenario_info,
        "default_weights": DEFAULT_SCENARIO_WEIGHTS,
        "products": product_info,
        "default_params": default_params,
    }

    # Optionally include SICR thresholds if the table exists
    try:
        sicr_df = backend.query_df(f"SELECT * FROM {_t('sicr_thresholds')} LIMIT 50")
        if not sicr_df.empty:
            result["sicr_thresholds"] = _df_to_records(sicr_df)
    except Exception:
        pass

    # Optionally include satellite model metadata if the table exists
    try:
        sat_df = backend.query_df(f"SELECT * FROM {_t('satellite_model_metadata')} LIMIT 50")
        if not sat_df.empty:
            result["satellite_model_metadata"] = _df_to_records(sat_df)
    except Exception:
        pass

    return result


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts with JSON-safe types."""
    import json
    from decimal import Decimal
    from datetime import datetime, date

    class _Enc(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Decimal):
                return float(o)
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            return super().default(o)

    return json.loads(json.dumps(df.to_dict("records"), cls=_Enc))
