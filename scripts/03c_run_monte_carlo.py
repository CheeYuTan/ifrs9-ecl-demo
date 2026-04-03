"""
IFRS 9 Monte Carlo Simulation — Databricks Job
================================================
Runs the vectorized Monte Carlo ECL simulation as a Databricks Job,
leveraging serverless compute for scalability.

Parameters (via notebook widgets):
  - catalog, schema: Unity Catalog location
  - n_simulations: Number of MC paths (default 1000)
  - pd_lgd_correlation: PD-LGD correlation (default 0.30)
  - aging_factor: Stage 2/3 aging factor (default 0.08)
  - random_seed: Reproducibility seed (optional)
  - scenario_weights: JSON dict of scenario weights (optional)
"""
from pyspark.sql import SparkSession
import numpy as np
import pandas as pd
import json
import time

spark = SparkSession.builder.getOrCreate()

# ── Widget parameters ─────────────────────────────────────────────────────────
try:
    CATALOG = dbutils.widgets.get("catalog")  # type: ignore[name-defined]
except Exception:
    CATALOG = "lakemeter_catalog"
try:
    SCHEMA = dbutils.widgets.get("schema")  # type: ignore[name-defined]
except Exception:
    SCHEMA = "expected_credit_loss"
try:
    N_SIMS = int(dbutils.widgets.get("n_simulations"))  # type: ignore[name-defined]
except Exception:
    N_SIMS = 1000
try:
    PD_LGD_CORR = float(dbutils.widgets.get("pd_lgd_correlation"))  # type: ignore[name-defined]
except Exception:
    PD_LGD_CORR = 0.30
try:
    AGING_FACTOR = float(dbutils.widgets.get("aging_factor"))  # type: ignore[name-defined]
except Exception:
    AGING_FACTOR = 0.08
try:
    PD_FLOOR = float(dbutils.widgets.get("pd_floor"))  # type: ignore[name-defined]
except Exception:
    PD_FLOOR = 0.001
try:
    PD_CAP = float(dbutils.widgets.get("pd_cap"))  # type: ignore[name-defined]
except Exception:
    PD_CAP = 0.95
try:
    LGD_FLOOR = float(dbutils.widgets.get("lgd_floor"))  # type: ignore[name-defined]
except Exception:
    LGD_FLOOR = 0.01
try:
    LGD_CAP = float(dbutils.widgets.get("lgd_cap"))  # type: ignore[name-defined]
except Exception:
    LGD_CAP = 0.95
try:
    RANDOM_SEED = int(dbutils.widgets.get("random_seed"))  # type: ignore[name-defined]
except Exception:
    RANDOM_SEED = 42
try:
    SCENARIO_WEIGHTS = json.loads(dbutils.widgets.get("scenario_weights"))  # type: ignore[name-defined]
except Exception:
    SCENARIO_WEIGHTS = None

FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

print("=" * 70)
print("  IFRS 9 Monte Carlo ECL Simulation (Databricks Job)")
print(f"  {N_SIMS:,} simulations, correlation={PD_LGD_CORR}, aging={AGING_FACTOR}")
print(f"  Seed: {RANDOM_SEED}")
print("=" * 70)

t0 = time.time()

# ── Load data ─────────────────────────────────────────────────────────────────
print("\n[1/4] LOADING DATA")

loans_df = spark.table(f"{FULL_SCHEMA}.model_ready_loans").toPandas()
scenarios_df = spark.table(f"{FULL_SCHEMA}.macro_scenarios").toPandas()
defaults_df = spark.table(f"{FULL_SCHEMA}.historical_defaults").toPandas()

loans_df = loans_df.dropna(subset=["assessed_stage", "remaining_months", "gross_carrying_amount"]).copy()
n_loans = len(loans_df)
print(f"  Loaded {n_loans:,} loans, {len(scenarios_df):,} scenario rows")

# ── Prepare loan arrays ──────────────────────────────────────────────────────
print("\n[2/4] PREPARING LOAN ARRAYS")

loans_df["stage"] = loans_df["assessed_stage"].fillna(1).astype(int)
loans_df["gca"] = loans_df["gross_carrying_amount"].astype(float)
loans_df["eir"] = loans_df["effective_interest_rate"].fillna(0.0).astype(float)
loans_df["base_pd"] = loans_df["current_lifetime_pd"].fillna(0.0).astype(float)
loans_df["rem_q"] = (loans_df["remaining_months"].fillna(1).astype(int) // 3).clip(lower=1)
loans_df["rem_months_f"] = loans_df["remaining_months"].fillna(1).astype(float).clip(lower=1)

# LGD from historical defaults
LGD_BY_PRODUCT = {}
for product in loans_df["product_type"].unique():
    prod_def = defaults_df[defaults_df["product_type"] == product]
    LGD_BY_PRODUCT[product] = float(prod_def["loss_given_default"].mean()) if len(prod_def) > 0 else 0.50
loans_df["base_lgd"] = loans_df["product_type"].map(LGD_BY_PRODUCT).fillna(0.50)

# Build scenario map
scenario_map = {}
for _, row in scenarios_df.groupby("scenario_name").mean(numeric_only=True).iterrows():
    scenario_map[row.name] = {
        "pd_mult": float(row.get("pd_multiplier", 1.0)) if "pd_multiplier" in row.index else 1.0,
        "lgd_mult": float(row.get("lgd_multiplier", 1.0)) if "lgd_multiplier" in row.index else 1.0,
        "pd_vol": 0.05,
        "lgd_vol": 0.03,
    }

# Compute scenario multipliers from macro data
baseline = scenarios_df[scenarios_df["scenario_name"] == "baseline"]
base_unemp = baseline["unemployment_rate"].mean() if len(baseline) > 0 else 5.0
base_gdp = baseline["gdp_growth_rate"].mean() if len(baseline) > 0 else 2.0

for sc_name in scenarios_df["scenario_name"].unique():
    sc_data = scenarios_df[scenarios_df["scenario_name"] == sc_name]
    sc_unemp = sc_data["unemployment_rate"].mean()
    sc_gdp = sc_data["gdp_growth_rate"].mean()
    pd_mult = 1.0 + (sc_unemp - base_unemp) * 0.08 + (base_gdp - sc_gdp) * 0.05
    pd_mult = max(pd_mult, 0.5)
    lgd_mult = 1.0 + (sc_unemp - base_unemp) * 0.03 + (base_gdp - sc_gdp) * 0.02
    lgd_mult = max(lgd_mult, 0.85)
    pd_vol = 0.05 + abs(pd_mult - 1.0) * 0.25
    lgd_vol = 0.03 + abs(lgd_mult - 1.0) * 0.18
    scenario_map[sc_name] = {"pd_mult": pd_mult, "lgd_mult": lgd_mult, "pd_vol": pd_vol, "lgd_vol": lgd_vol}

# Default scenario weights
DEFAULT_WEIGHTS = {
    "baseline": 0.30, "mild_recovery": 0.15, "strong_growth": 0.05,
    "mild_downturn": 0.15, "adverse": 0.15, "stagflation": 0.08,
    "severely_adverse": 0.07, "tail_risk": 0.05,
}
weights = SCENARIO_WEIGHTS if SCENARIO_WEIGHTS else DEFAULT_WEIGHTS
# Add discovered scenarios
for sc in scenario_map:
    if sc not in weights:
        weights[sc] = 0.05
# Normalize
w_total = sum(weights.values())
if abs(w_total - 1.0) > 0.01:
    weights = {k: v / w_total for k, v in weights.items()}

scenarios = list(weights.keys())
for sc in scenarios:
    if sc not in scenario_map:
        scenario_map[sc] = {"pd_mult": 1.0, "lgd_mult": 1.0, "pd_vol": 0.05, "lgd_vol": 0.03}

print(f"  {len(scenarios)} scenarios, weights sum={sum(weights.values()):.2f}")

# ── Vectorized Monte Carlo ───────────────────────────────────────────────────
print(f"\n[3/4] MONTE CARLO — {n_loans:,} loans × {len(scenarios)} scenarios × {N_SIMS:,} sims")

# Extract numpy arrays
stage = loans_df["stage"].values
gca = loans_df["gca"].values
eir = loans_df["eir"].values
base_pd = loans_df["base_pd"].values
rem_q = loans_df["rem_q"].values
rem_months_f = loans_df["rem_months_f"].values
base_lgd_arr = loans_df["base_lgd"].values
products = loans_df["product_type"].values
is_bullet = rem_months_f <= 3
max_horizon = np.where(stage == 1, np.minimum(4, rem_q), rem_q)
global_max_q = int(max_horizon.max())

# Default prepayment rate
quarterly_prepay = np.full(n_loans, 1.0 - (1.0 - 0.05) ** 0.25)
rho = np.full(n_loans, PD_LGD_CORR)

rng = np.random.default_rng(RANDOM_SEED)
BATCH_SIZE = min(N_SIMS, 200)

loan_weighted_ecl = np.zeros(n_loans)
scenario_results = []

for i, sc in enumerate(scenarios):
    sc_data = scenario_map[sc]
    w = weights[sc]
    t_sc = time.time()

    loan_ecl_accum = np.zeros(n_loans)
    portfolio_path_ecls = np.zeros(N_SIMS)
    sims_done = 0

    while sims_done < N_SIMS:
        batch = min(BATCH_SIZE, N_SIMS - sims_done)

        z_pd = rng.standard_normal((n_loans, batch))
        z_lgd_indep = rng.standard_normal((n_loans, batch))

        rho_2d = rho[:, np.newaxis]
        z_lgd = rho_2d * z_pd + np.sqrt(1 - rho_2d ** 2) * z_lgd_indep

        pd_shocks = np.exp(z_pd * sc_data["pd_vol"] - 0.5 * sc_data["pd_vol"] ** 2)
        lgd_shocks = np.exp(z_lgd * sc_data["lgd_vol"] - 0.5 * sc_data["lgd_vol"] ** 2)

        stressed_pd = np.clip(base_pd[:, np.newaxis] * sc_data["pd_mult"] * pd_shocks, PD_FLOOR, PD_CAP)
        stressed_lgd = np.clip(base_lgd_arr[:, np.newaxis] * sc_data["lgd_mult"] * lgd_shocks, LGD_FLOOR, LGD_CAP)

        ecl_batch = np.zeros((n_loans, batch))
        survival = np.ones((n_loans, batch))

        for q in range(1, global_max_q + 1):
            active = max_horizon >= q
            if not active.any():
                break

            quarterly_base_pd = 1.0 - (1.0 - stressed_pd) ** 0.25
            is_s23 = (stage != 1)[:, np.newaxis]
            aging = np.where(is_s23, 1.0 + AGING_FACTOR * (q - 1), 1.0)
            q_pd = np.clip(quarterly_base_pd * aging, 0, 0.99)

            default_this_q = survival * q_pd
            prepay_surv = (1.0 - quarterly_prepay[:, np.newaxis]) ** q
            amort = np.maximum(0.0, 1.0 - (q * 3) / rem_months_f[:, np.newaxis])
            ead_q = np.where(
                is_bullet[:, np.newaxis], gca[:, np.newaxis],
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

    loan_ecl_mean = loan_ecl_accum / N_SIMS
    loan_weighted_ecl += loan_ecl_mean * w
    sc_ecl_total = float(portfolio_path_ecls.mean())

    scenario_results.append({
        "scenario": sc, "weight": w,
        "total_ecl": round(sc_ecl_total, 2),
        "ecl_p50": round(float(np.percentile(portfolio_path_ecls, 50)), 2),
        "ecl_p75": round(float(np.percentile(portfolio_path_ecls, 75)), 2),
        "ecl_p95": round(float(np.percentile(portfolio_path_ecls, 95)), 2),
        "ecl_p99": round(float(np.percentile(portfolio_path_ecls, 99)), 2),
        "weighted_contribution": round(sc_ecl_total * w, 2),
    })

    elapsed_sc = time.time() - t_sc
    print(f"  Scenario {i+1}/{len(scenarios)}: {sc} (w={w:.0%}) ECL={sc_ecl_total:,.0f} [{elapsed_sc:.1f}s]")

# ── Save results ──────────────────────────────────────────────────────────────
print(f"\n[4/4] SAVING RESULTS")

# Per-loan weighted ECL
loans_df["weighted_ecl"] = loan_weighted_ecl
result_df = loans_df[["loan_id", "product_type", "assessed_stage", "gca", "weighted_ecl"]].copy()
result_df.rename(columns={"gca": "gross_carrying_amount"}, inplace=True)
result_df["coverage_ratio"] = (result_df["weighted_ecl"] / result_df["gross_carrying_amount"].clip(lower=1) * 100).round(4)
result_df["n_simulations"] = N_SIMS
result_df["random_seed"] = RANDOM_SEED

spark.createDataFrame(result_df).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.mc_loan_level_ecl")
print(f"  mc_loan_level_ecl: {len(result_df):,} rows")

# Scenario summary
scenario_df = pd.DataFrame(scenario_results)
spark.createDataFrame(scenario_df).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.mc_scenario_summary")
print(f"  mc_scenario_summary: {len(scenario_df):,} rows")

# Portfolio summary by product
product_summary = result_df.groupby("product_type").agg(
    loan_count=("loan_id", "count"),
    total_gca=("gross_carrying_amount", "sum"),
    total_ecl=("weighted_ecl", "sum"),
).reset_index()
product_summary["coverage_ratio"] = (product_summary["total_ecl"] / product_summary["total_gca"] * 100).round(2)

spark.createDataFrame(product_summary).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.mc_product_summary")
print(f"  mc_product_summary: {len(product_summary):,} rows")

duration = round(time.time() - t0, 1)
grand_ecl = result_df["weighted_ecl"].sum()
grand_gca = result_df["gross_carrying_amount"].sum()
grand_cov = round(grand_ecl / grand_gca * 100, 2)

print(f"\n{'='*70}")
print(f"  Monte Carlo Simulation Complete!")
print(f"  Total ECL: ${grand_ecl:,.0f} ({grand_cov:.2f}% coverage)")
print(f"  {len(scenarios)} scenarios × {N_SIMS:,} simulations")
print(f"  {n_loans:,} loans processed in {duration}s")
print(f"  Seed: {RANDOM_SEED}")
print(f"{'='*70}")
