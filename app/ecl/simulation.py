"""
ECL Engine -- Monte Carlo simulation orchestrator.

Loads data, prepares arrays, dispatches per-scenario simulation batches
(ecl.monte_carlo), and delegates result aggregation (ecl.aggregation).
"""

import logging
import time

import numpy as np

import ecl.config as _cfg
import ecl.data_loader as _dl
from ecl.aggregation import aggregate_results
from ecl.constants import DEFAULT_SAT, DEFAULT_SCENARIO_WEIGHTS
from ecl.helpers import _convergence_check_from_paths, _emit
from ecl.monte_carlo import prepare_loan_columns, run_scenario_sims

log = logging.getLogger(__name__)


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
    random_seed: int | None = None,
) -> dict:
    """
    Run Monte Carlo ECL simulation across all loans and scenarios.

    Processes loans in batches per (product, stage, scenario) for full
    numpy vectorization -- no per-loan Python loops.
    """
    t0 = time.time()
    if n_sims < 1:
        raise ValueError(f"n_sims must be >= 1, got {n_sims}")

    cfg_lgd, cfg_weights = _cfg._load_config()
    dyn_lgd, dyn_sat = _cfg._build_product_maps()
    base_lgd = cfg_lgd if cfg_lgd else dyn_lgd

    _emit(
        progress_callback,
        {
            "phase": "loading",
            "step": "loans",
            "message": "Loading loan data from Lakebase...",
            "progress": 0,
            "elapsed": 0.0,
        },
    )

    loans_df = _dl._load_loans()
    if len(loans_df) == 0:
        raise ValueError("No loans found in model_ready_loans")

    _emit(
        progress_callback,
        {
            "phase": "loading",
            "step": "loans_done",
            "message": f"Loaded {len(loans_df):,} loans ({loans_df['product_type'].nunique()} products, {loans_df['assessed_stage'].nunique()} stages)",
            "progress": 5,
            "elapsed": round(time.time() - t0, 2),
            "detail": {
                "loan_count": len(loans_df),
                "products": sorted(loans_df["product_type"].unique().tolist()),
                "stages": sorted(int(s) for s in loans_df["assessed_stage"].unique()),
                "total_gca": round(float(loans_df["gross_carrying_amount"].astype(float).sum()), 2),
                "memory_mb": round(loans_df.memory_usage(deep=True).sum() / 1e6, 1),
            },
        },
    )

    scenarios_df = _dl._load_scenarios()
    scenario_map = _build_scenario_map(scenarios_df)

    weights = scenario_weights if scenario_weights else (cfg_weights if cfg_weights else DEFAULT_SCENARIO_WEIGHTS)
    if not weights:
        raise ValueError("No scenario weights provided — at least one scenario is required")
    scenarios = list(weights.keys())
    for sc in scenarios:
        if sc not in scenario_map:
            log.warning("Scenario '%s' missing from DB — using default multipliers", sc)
            scenario_map[sc] = {"weight": weights[sc], "pd_mult": 1.0, "lgd_mult": 1.0, "pd_vol": 0.05, "lgd_vol": 0.03}
    if not scenario_map:
        raise ValueError("scenario_map is empty after loading scenarios and applying defaults")

    t_load_done = time.time()
    load_time = round(t_load_done - t0, 2)

    _emit(
        progress_callback,
        {
            "phase": "loading",
            "step": "scenarios_done",
            "message": f"Loaded {len(scenarios)} macro scenarios",
            "progress": 10,
            "elapsed": load_time,
            "detail": {"scenarios": scenarios},
        },
    )

    loans_df = prepare_loan_columns(loans_df, base_lgd)
    n_loans = len(loans_df)

    if random_seed is None:
        random_seed = int(np.random.default_rng().integers(0, 2**31))
    rng = np.random.default_rng(random_seed)

    # Extract numpy arrays for the simulation loop
    products = loans_df["product_type"].values
    stage = loans_df["stage"].values
    gca, eir = loans_df["gca"].values, loans_df["eir"].values
    base_pd, rem_q = loans_df["base_pd"].values, loans_df["rem_q"].values
    rem_months_f = loans_df["rem_months_f"].values
    base_lgd_arr = loans_df["base_lgd"].values

    product_corr = np.array([dyn_sat.get(p, DEFAULT_SAT)["pd_lgd_corr"] for p in products])
    product_prepay = np.array([dyn_sat.get(p, DEFAULT_SAT)["annual_prepay_rate"] for p in products])
    if pd_lgd_correlation != 0.30:
        product_corr[:] = pd_lgd_correlation

    quarterly_prepay = 1.0 - (1.0 - product_prepay) ** 0.25
    max_horizon = np.where(stage == 1, np.minimum(4, rem_q), rem_q)
    global_max_q = int(max_horizon.max())
    is_bullet = rem_months_f <= 3

    loan_weighted_ecl = np.zeros(n_loans)
    scenario_ecl_totals = {sc: np.zeros(n_loans) for sc in scenarios}
    scenario_ecl_paths: dict[str, np.ndarray] = {}
    _unique_products = loans_df["product_type"].unique()
    product_sim_ecls = {p: np.zeros(n_sims) for p in _unique_products}
    running_weighted_ecl = 0.0
    BATCH_SIZE = min(n_sims, 200)

    for i, sc in enumerate(scenarios):
        sc_data = scenario_map[sc]
        w = weights[sc]

        _emit(
            progress_callback,
            {
                "phase": "computing",
                "step": "scenario_start",
                "scenario": sc,
                "scenario_index": i,
                "scenario_count": len(scenarios),
                "weight": w,
                "message": f"Scenario {i + 1}/{len(scenarios)}: {sc} (weight: {w * 100:.0f}%)",
                "progress": 10 + (i / len(scenarios)) * 80,
                "elapsed": round(time.time() - t0, 2),
            },
        )

        loan_ecl_accum, portfolio_path_ecls = run_scenario_sims(
            rng=rng,
            n_loans=n_loans,
            n_sims=n_sims,
            batch_size=BATCH_SIZE,
            rho_1d=product_corr,
            base_pd=base_pd,
            base_lgd_arr=base_lgd_arr,
            pd_mult=sc_data["pd_mult"],
            lgd_mult=sc_data["lgd_mult"],
            pd_vol=sc_data["pd_vol"],
            lgd_vol=sc_data["lgd_vol"],
            pd_floor=pd_floor,
            pd_cap=pd_cap,
            lgd_floor=lgd_floor,
            lgd_cap=lgd_cap,
            aging_factor=aging_factor,
            is_stage_23_1d=(stage != 1),
            max_horizon=max_horizon,
            global_max_q=global_max_q,
            quarterly_prepay=quarterly_prepay,
            rem_months_f=rem_months_f,
            is_bullet=is_bullet,
            gca=gca,
            eir=eir,
            products=products,
            unique_products=_unique_products,
            product_sim_ecls=product_sim_ecls,
            w=w,
        )

        loan_ecl_mean = loan_ecl_accum / n_sims
        scenario_ecl_totals[sc] = loan_ecl_mean
        loan_weighted_ecl += loan_ecl_mean * w
        sc_ecl_total = float(portfolio_path_ecls.mean())
        running_weighted_ecl += sc_ecl_total * w
        scenario_ecl_paths[sc] = portfolio_path_ecls

        _emit(
            progress_callback,
            {
                "phase": "computing",
                "step": "scenario_done",
                "scenario": sc,
                "scenario_index": i,
                "scenario_ecl": float(sc_ecl_total),
                "cumulative_weighted_ecl": float(running_weighted_ecl),
                "message": f"Scenario {sc}: ECL = {sc_ecl_total:,.0f}",
                "progress": 10 + ((i + 1) / len(scenarios)) * 80,
                "elapsed": round(time.time() - t0, 2),
                "detail": {
                    "scenario_ecl": round(float(sc_ecl_total), 2),
                    "mean_pd_mult": sc_data["pd_mult"],
                    "mean_lgd_mult": sc_data["lgd_mult"],
                    "quarters_processed": global_max_q,
                    "convergence": _convergence_check_from_paths(portfolio_path_ecls, n_sims),
                },
            },
        )

    return aggregate_results(
        loans_df=loans_df,
        loan_weighted_ecl=loan_weighted_ecl,
        scenario_ecl_totals=scenario_ecl_totals,
        scenario_ecl_paths=scenario_ecl_paths,
        product_sim_ecls=product_sim_ecls,
        products=products,
        scenarios=scenarios,
        weights=weights,
        n_sims=n_sims,
        n_loans=n_loans,
        sim_params={
            "n_sims": n_sims,
            "random_seed": random_seed,
            "pd_lgd_correlation": pd_lgd_correlation,
            "aging_factor": aging_factor,
            "pd_floor": pd_floor,
            "pd_cap": pd_cap,
            "lgd_floor": lgd_floor,
            "lgd_cap": lgd_cap,
        },
        t0=t0,
        load_time=load_time,
        progress_callback=progress_callback,
    )


def _build_scenario_map(scenarios_df):
    """Convert scenario DataFrame to lookup dict."""
    scenario_map = {}
    for _, row in scenarios_df.iterrows():
        scenario_map[row["scenario"]] = {
            "weight": float(row["weight"]),
            "pd_mult": float(row["avg_pd_multiplier"]),
            "lgd_mult": float(row["avg_lgd_multiplier"]),
            "pd_vol": float(row["pd_vol"]),
            "lgd_vol": float(row["lgd_vol"]),
        }
    return scenario_map
