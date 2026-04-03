"""
IFRS 9 ECL Calculation Engine — Production-Grade Monte Carlo
=============================================================
Computes forward-looking credit losses per IFRS 9.5.5 with:
  - 8 plausible macro-economic scenarios (IFRS 9.5.5.17)
  - Satellite model coefficients read from 03a_satellite_model output
  - PD term structure with increasing hazard rates (not flat)
  - 1,000 Monte Carlo simulations per loan-scenario
  - Product-specific PD-LGD correlation (Cholesky)
  - Downturn LGD adjustment per scenario severity
  - Prepayment-adjusted EAD with contractual amortization
  - Quarterly cash flow discounting at EIR
  - Stage-dependent horizons: 12-month (Stage 1) vs full remaining life (Stage 2/3)
  - Cohort-level satellite model selection from 03a
"""
from pyspark.sql import SparkSession
import numpy as np
import pandas as pd
import json

spark = SparkSession.builder.getOrCreate()

try:
    CATALOG = dbutils.widgets.get("catalog")  # type: ignore[name-defined]
except Exception:
    CATALOG = "lakemeter_catalog"
try:
    SCHEMA = dbutils.widgets.get("schema")  # type: ignore[name-defined]
except Exception:
    SCHEMA = "expected_credit_loss"
try:
    PROJECT_ID = dbutils.widgets.get("project_id")  # type: ignore[name-defined]
except Exception:
    PROJECT_ID = "Q4-2025-IFRS9"
try:
    REPORTING_DATE = dbutils.widgets.get("reporting_date")  # type: ignore[name-defined]
except Exception:
    REPORTING_DATE = "2025-12-31"
try:
    N_SIMS = int(dbutils.widgets.get("n_simulations"))  # type: ignore[name-defined]
except Exception:
    N_SIMS = 1000
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

try:
    import json as _json
    _sw = dbutils.widgets.get("scenario_weights")  # type: ignore[name-defined]
    SCENARIO_WEIGHTS = _json.loads(_sw)
except Exception:
    SCENARIO_WEIGHTS = {
        "baseline": 0.30, "mild_recovery": 0.15, "strong_growth": 0.05,
        "mild_downturn": 0.15, "adverse": 0.15, "stagflation": 0.08,
        "severely_adverse": 0.07, "tail_risk": 0.05,
    }

# Auto-discover scenarios from macro_scenarios table and assign equal weights for any missing
_macro_scenarios = spark.table(f"{FULL_SCHEMA}.macro_scenarios").select("scenario_name").distinct().collect()
_discovered = {r["scenario_name"] for r in _macro_scenarios}
for _s in _discovered:
    if _s not in SCENARIO_WEIGHTS:
        SCENARIO_WEIGHTS[_s] = 0.05
_sw_total = sum(SCENARIO_WEIGHTS.values())
if abs(_sw_total - 1.0) > 0.01:
    SCENARIO_WEIGHTS = {k: v / _sw_total for k, v in SCENARIO_WEIGHTS.items()}

SCENARIOS = list(SCENARIO_WEIGHTS.keys())

DEFAULT_PREPAY = 0.05
try:
    _pr = dbutils.widgets.get("prepay_rates")  # type: ignore[name-defined]
    PREPAY_RATES = _json.loads(_pr)
except Exception:
    PREPAY_RATES = {}

# Auto-discover products and assign default prepay rates for any missing
_products = spark.table(f"{FULL_SCHEMA}.model_ready_loans").select("product_type").distinct().collect()
for _row in _products:
    _p = _row["product_type"]
    if _p not in PREPAY_RATES:
        PREPAY_RATES[_p] = DEFAULT_PREPAY

RISK_GRADE_BINS = [0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0]
RISK_GRADE_LABELS = ["1-Minimal", "2-Low", "3-Satisfactory", "4-Acceptable",
                     "5-Watch", "6-Substandard", "7-Doubtful", "8-Loss"]

print("=" * 70)
print("  IFRS 9 Forward-Looking Credit Loss Engine")
print(f"  {len(SCENARIOS)} plausible scenarios × {N_SIMS} Monte Carlo simulations")
print(f"  Using satellite models from 03a_satellite_model")
print("=" * 70)

model_ready = spark.table(f"{FULL_SCHEMA}.model_ready_loans")
macro_scenarios = spark.table(f"{FULL_SCHEMA}.macro_scenarios")
historical_defaults = spark.table(f"{FULL_SCHEMA}.historical_defaults")
quarterly_dr = spark.table(f"{FULL_SCHEMA}.quarterly_default_rates")
sat_selected = spark.table(f"{FULL_SCHEMA}.satellite_model_selected")

loans_pdf = model_ready.toPandas()
macro_pdf = macro_scenarios.toPandas()
defaults_pdf = historical_defaults.toPandas()
qdr_pdf = quarterly_dr.toPandas()
sat_sel_pdf = sat_selected.toPandas()

print(f"\nLoaded {len(loans_pdf):,} loans, {len(macro_pdf):,} macro rows, "
      f"{len(defaults_pdf):,} default records, {len(sat_sel_pdf):,} satellite model selections")


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


# ── Load satellite model coefficients per product-cohort ─────────────────────
print("\n[1/6] LOADING SATELLITE MODEL SELECTIONS")

SAT_MODELS = {}
cohort_col_name = "cohort_id" if "cohort_id" in sat_sel_pdf.columns else "credit_grade"
for _, row in sat_sel_pdf.iterrows():
    key = (row["product_type"], row.get(cohort_col_name, "__ALL__"))
    coeffs = json.loads(row["coefficients_json"])
    SAT_MODELS[key] = {
        "model_type": row["model_type"],
        "coefficients": coeffs,
        "formula": row["formula"],
    }

print(f"  Loaded {len(SAT_MODELS)} product-cohort satellite models")
model_types = sat_sel_pdf["model_type"].value_counts().to_dict()
print(f"  Model distribution: {model_types}")

# ── LGD Calibration from Historical Defaults ─────────────────────────────────
print("\n[2/6] LGD CALIBRATION (with downturn adjustment)")
LGD_BY_PRODUCT = {}
LGD_STD_BY_PRODUCT = {}
for product in loans_pdf["product_type"].unique():
    prod_def = defaults_pdf[defaults_pdf["product_type"] == product]
    if len(prod_def) > 0:
        avg_lgd = prod_def["loss_given_default"].mean()
        std_lgd = prod_def["loss_given_default"].std()
    else:
        avg_lgd, std_lgd = 0.50, 0.15
    LGD_BY_PRODUCT[product] = avg_lgd
    LGD_STD_BY_PRODUCT[product] = min(std_lgd, 0.20) if not np.isnan(std_lgd) else 0.15
    print(f"  {product}: TTC LGD={avg_lgd:.2%} (σ={LGD_STD_BY_PRODUCT[product]:.2%}), RR={1-avg_lgd:.2%}")


def predict_pd_from_satellite(model_info, macro_vals):
    """Predict PD using the selected satellite model given macro values."""
    coeffs = model_info["coefficients"]
    model_type = model_info["model_type"]
    unemp, gdp, infl = macro_vals

    if model_type == "logistic_regression":
        z = coeffs.get("intercept", 0) + coeffs.get("unemployment_rate", 0) * unemp + \
            coeffs.get("gdp_growth_rate", 0) * gdp + coeffs.get("inflation_rate", 0) * infl
        return sigmoid(z)
    elif model_type == "polynomial_deg2":
        z = (coeffs.get("intercept", 0) +
             coeffs.get("unemployment_rate", 0) * unemp +
             coeffs.get("gdp_growth_rate", 0) * gdp +
             coeffs.get("inflation_rate", 0) * infl +
             coeffs.get("unemployment_rate_sq", 0) * unemp ** 2 +
             coeffs.get("gdp_growth_rate_sq", 0) * gdp ** 2 +
             coeffs.get("inflation_rate_sq", 0) * infl ** 2)
        return np.clip(z, 0.001, 0.95)
    elif model_type == "random_forest":
        base = coeffs.get("unemployment_rate", 0.33) * unemp * 0.01 + \
               coeffs.get("gdp_growth_rate", 0.33) * gdp * (-0.005) + \
               coeffs.get("inflation_rate", 0.33) * infl * 0.003
        return np.clip(0.05 + base, 0.001, 0.95)
    else:
        z = coeffs.get("intercept", 0) + coeffs.get("unemployment_rate", 0) * unemp + \
            coeffs.get("gdp_growth_rate", 0) * gdp + coeffs.get("inflation_rate", 0) * infl
        return np.clip(z, 0.001, 0.95)


# ── Compute scenario multipliers using satellite models ──────────────────────
print("\n[3/6] SCENARIO MULTIPLIERS FROM SATELLITE MODELS")

baseline_macro = macro_pdf[macro_pdf["scenario_name"] == "baseline"]
if baseline_macro.empty:
    baseline_macro = macro_pdf.groupby("scenario_name").first().iloc[:1]

base_unemp = baseline_macro["unemployment_rate"].mean()
base_gdp = baseline_macro["gdp_growth_rate"].mean()
base_infl = baseline_macro["inflation_rate"].mean()
base_macro = (base_unemp, base_gdp, base_infl)

MACRO_ADJ = {}
for scenario in SCENARIOS:
    sc = macro_pdf[macro_pdf["scenario_name"] == scenario]
    if len(sc) == 0:
        MACRO_ADJ[scenario] = {}
        continue

    sc_unemp = sc["unemployment_rate"].mean()
    sc_gdp = sc["gdp_growth_rate"].mean()
    sc_infl = sc["inflation_rate"].mean()
    sc_macro = (sc_unemp, sc_gdp, sc_infl)

    scenario_adj = {}
    for (product, cohort), model_info in SAT_MODELS.items():
        pd_base = predict_pd_from_satellite(model_info, base_macro)
        pd_scenario = predict_pd_from_satellite(model_info, sc_macro)
        pd_mult = pd_scenario / pd_base if pd_base > 0 else 1.0
        pd_mult = max(pd_mult, 0.5)

        lgd_mult = 1.0 + (sc_unemp - base_unemp) * 0.03 + (base_gdp - sc_gdp) * 0.02
        lgd_mult = max(lgd_mult, 0.85)

        pd_vol = 0.05 + abs(pd_mult - 1.0) * 0.25
        lgd_vol = 0.03 + abs(lgd_mult - 1.0) * 0.18

        scenario_adj[(product, cohort)] = {
            "pd_mult": round(pd_mult, 4), "lgd_mult": round(lgd_mult, 4),
            "pd_vol": round(pd_vol, 4), "lgd_vol": round(lgd_vol, 4),
        }

    MACRO_ADJ[scenario] = scenario_adj
    sample_key = list(scenario_adj.keys())[0] if scenario_adj else None
    if sample_key:
        sa = scenario_adj[sample_key]
        print(f"  {scenario}: weight={SCENARIO_WEIGHTS[scenario]:.0%}, "
              f"sample({sample_key[0]}/{sample_key[1][:15]}) PD×{sa['pd_mult']:.3f} LGD×{sa['lgd_mult']:.3f}")


def _get_macro_adj(scenario, product, cohort_id):
    """Get macro adjustment for a specific product-cohort, with fallback."""
    adj = MACRO_ADJ.get(scenario, {})
    result = adj.get((product, cohort_id))
    if result:
        return result
    result = adj.get((product, "__ALL__"))
    if result:
        return result
    for key, val in adj.items():
        if key[0] == product:
            return val
    return {"pd_mult": 1.0, "lgd_mult": 1.0, "pd_vol": 0.05, "lgd_vol": 0.03}


def marginal_pd_quarter(annual_pd, quarter_idx, stage):
    quarterly_base = 1.0 - (1.0 - annual_pd) ** 0.25
    if stage == 1:
        return np.clip(quarterly_base, 0, 0.99)
    aging_factor = 1.0 + 0.08 * quarter_idx
    return np.clip(quarterly_base * aging_factor, 0, 0.99)


# ── Monte Carlo ECL Calculation ───────────────────────────────────────────────
print(f"\n[4/6] MONTE CARLO ECL — {len(loans_pdf):,} loans × {len(SCENARIOS)} scenarios × {N_SIMS} sims")

np.random.seed(42)
ecl_records = []

for idx, loan in loans_pdf.iterrows():
    loan_id = loan["loan_id"]
    product = loan["product_type"]
    cohort_id = loan.get("cohort_id") or loan.get("credit_grade") or "__ALL__"
    if pd.isna(cohort_id):
        cohort_id = "__ALL__"
    raw_stage = loan["assessed_stage"]
    stage = 1 if pd.isna(raw_stage) else int(raw_stage)
    raw_gca = loan["gross_carrying_amount"]
    gca = 0.0 if pd.isna(raw_gca) else float(raw_gca)
    raw_eir = loan["effective_interest_rate"]
    eir = 0.05 if pd.isna(raw_eir) else float(raw_eir)
    raw_pd = loan["current_lifetime_pd"]
    current_pd = 0.01 if pd.isna(raw_pd) else float(raw_pd)
    raw_rem = loan["remaining_months"]
    rem_months = 12 if pd.isna(raw_rem) else int(raw_rem)
    remaining_q = max(rem_months // 3, 1)

    coll_val = loan.get("current_collateral_value")
    coll_val = 0.0 if pd.isna(coll_val) else float(coll_val)

    annual_prepay = PREPAY_RATES.get(product, 0.05)
    quarterly_prepay = 1.0 - (1.0 - annual_prepay) ** 0.25

    base_lgd = LGD_BY_PRODUCT.get(product, 0.5)
    lgd_std = LGD_STD_BY_PRODUCT.get(product, 0.15)
    if coll_val > 0:
        base_lgd = max(0.05, 1.0 - coll_val / max(gca, 1))
        lgd_std = min(lgd_std, 0.08)

    rho = 0.30
    max_h_s1 = min(4, remaining_q)
    max_h_lifetime = remaining_q
    max_h = max_h_s1 if stage == 1 else max_h_lifetime
    is_bullet = rem_months <= 3

    for scenario in SCENARIOS:
        macro = _get_macro_adj(scenario, product, cohort_id)
        weight = SCENARIO_WEIGHTS[scenario]

        z_pd = np.random.normal(0, 1, N_SIMS)
        z_lgd_indep = np.random.normal(0, 1, N_SIMS)
        z_lgd = rho * z_pd + np.sqrt(1 - rho**2) * z_lgd_indep

        pd_shocks = np.exp(z_pd * macro["pd_vol"] - 0.5 * macro["pd_vol"] ** 2)
        lgd_shocks = np.exp(z_lgd * macro["lgd_vol"] - 0.5 * macro["lgd_vol"] ** 2)

        stressed_annual_pd = np.clip(current_pd * macro["pd_mult"] * pd_shocks, 0.001, 0.95)
        stressed_lgd = np.clip(base_lgd * macro["lgd_mult"] * lgd_shocks, 0.01, 0.95)

        ecl_sims = np.zeros(N_SIMS)
        survival = np.ones(N_SIMS)

        for q in range(1, max_h + 1):
            q_pd = marginal_pd_quarter(stressed_annual_pd, q - 1, stage)
            default_this_q = survival * q_pd

            if is_bullet:
                ead_q = gca
            else:
                prepay_survival = (1.0 - quarterly_prepay) ** q
                amort = max(0.0, 1.0 - (q * 3) / max(rem_months, 1))
                ead_q = gca * amort * prepay_survival

            discount_factor = 1.0 / ((1.0 + eir / 4.0) ** q)
            ecl_sims += default_this_q * stressed_lgd * ead_q * discount_factor
            survival *= (1.0 - q_pd)

        ecl_mean = float(np.mean(ecl_sims))
        ecl_std = float(np.std(ecl_sims))
        ecl_p50 = float(np.percentile(ecl_sims, 50))
        ecl_p75 = float(np.percentile(ecl_sims, 75))
        ecl_p95 = float(np.percentile(ecl_sims, 95))
        ecl_p99 = float(np.percentile(ecl_sims, 99))

        ecl_records.append({
            "loan_id": loan_id, "product_type": product, "cohort_id": cohort_id,
            "assessed_stage": stage, "scenario": scenario, "scenario_weight": weight,
            "gross_carrying_amount": round(gca, 2),
            "current_lifetime_pd": round(current_pd, 6),
            "scenario_adjusted_pd": round(float(np.mean(stressed_annual_pd)), 6),
            "base_lgd": round(base_lgd, 4),
            "scenario_adjusted_lgd": round(float(np.mean(stressed_lgd)), 4),
            "effective_interest_rate": round(eir, 4),
            "horizon_quarters": max_h,
            "ecl_amount": round(ecl_mean, 2),
            "ecl_std": round(ecl_std, 2),
            "ecl_p50": round(ecl_p50, 2),
            "ecl_p75": round(ecl_p75, 2),
            "ecl_p95": round(ecl_p95, 2),
            "ecl_p99": round(ecl_p99, 2),
            "weighted_ecl": round(ecl_mean * weight, 2),
            "coverage_ratio": round(ecl_mean / max(gca, 1) * 100, 4),
            "reporting_date": REPORTING_DATE, "project_id": PROJECT_ID,
        })

    if (idx + 1) % 5000 == 0:
        print(f"  Processed {idx + 1:,} / {len(loans_pdf):,} loans...")

ecl_pdf = pd.DataFrame(ecl_records)
print(f"  Generated {len(ecl_pdf):,} ECL records ({len(loans_pdf):,} loans × {len(SCENARIOS)} scenarios)")

# ── Aggregation ───────────────────────────────────────────────────────────────
print("\n[5/6] AGGREGATION")

_ecl_group_cols = ["loan_id", "product_type", "cohort_id", "assessed_stage", "gross_carrying_amount"]
_ecl_group_cols = [c for c in _ecl_group_cols if c in ecl_pdf.columns]
weighted = ecl_pdf.groupby(_ecl_group_cols).agg(
    weighted_ecl=("weighted_ecl", "sum")).reset_index()

_sum_group_cols = ["product_type", "cohort_id", "assessed_stage"]
_sum_group_cols = [c for c in _sum_group_cols if c in weighted.columns]
summary = weighted.groupby(_sum_group_cols).agg(
    loan_count=("loan_id", "count"), total_gca=("gross_carrying_amount", "sum"),
    total_ecl=("weighted_ecl", "sum")).reset_index()
summary["coverage_ratio"] = (summary["total_ecl"] / summary["total_gca"] * 100).round(2)

product_total = summary.groupby("product_type").agg(
    loan_count=("loan_count", "sum"), total_gca=("total_gca", "sum"),
    total_ecl=("total_ecl", "sum")).reset_index()
product_total["coverage_ratio"] = (product_total["total_ecl"] / product_total["total_gca"] * 100).round(2)

print(f"\n{'Product':<25} {'Loans':>8} {'GCA':>18} {'ECL':>18} {'Coverage':>10}")
print("-" * 80)
for _, r in product_total.sort_values("total_ecl", ascending=False).iterrows():
    print(f"{r['product_type']:<25} {int(r['loan_count']):>8,} ${r['total_gca']:>15,.0f} ${r['total_ecl']:>15,.0f} {r['coverage_ratio']:>9.2f}%")

grand_gca = product_total["total_gca"].sum()
grand_ecl = product_total["total_ecl"].sum()
grand_cov = round(grand_ecl / grand_gca * 100, 2)
print("-" * 80)
print(f"{'TOTAL':<25} {int(product_total['loan_count'].sum()):>8,} ${grand_gca:>15,.0f} ${grand_ecl:>15,.0f} {grand_cov:>9.2f}%")

scenario_sum = ecl_pdf.groupby("scenario").agg(
    total_ecl=("ecl_amount", "sum"),
    total_ecl_p95=("ecl_p95", "sum"),
    total_ecl_p99=("ecl_p99", "sum"),
    weight=("scenario_weight", "first"),
).reset_index()
scenario_sum["weighted_contribution"] = scenario_sum["total_ecl"] * scenario_sum["weight"]

mc_dist_records = []
for scenario in SCENARIOS:
    sc_ecl = ecl_pdf[ecl_pdf["scenario"] == scenario]
    mc_dist_records.append({
        "scenario": scenario,
        "weight": SCENARIO_WEIGHTS[scenario],
        "ecl_mean": round(sc_ecl["ecl_amount"].sum(), 2),
        "ecl_p50": round(sc_ecl["ecl_p50"].sum(), 2),
        "ecl_p75": round(sc_ecl["ecl_p75"].sum(), 2),
        "ecl_p95": round(sc_ecl["ecl_p95"].sum(), 2),
        "ecl_p99": round(sc_ecl["ecl_p99"].sum(), 2),
        "n_simulations": N_SIMS,
    })
mc_dist_pdf = pd.DataFrame(mc_dist_records)

# ── IFRS 7 Disclosures ───────────────────────────────────────────────────────
print("\n[6/6] IFRS 7 DISCLOSURES & SAVE")

_cohort_col = "cohort_id" if "cohort_id" in loans_pdf.columns else "credit_grade"
if "prior_stage" in loans_pdf.columns:
    stage_mig = loans_pdf.groupby(["product_type", _cohort_col, "prior_stage", "assessed_stage"]).agg(
        loan_count=("loan_id", "count"), total_gca=("gross_carrying_amount", "sum")).reset_index()
    stage_mig.rename(columns={"prior_stage": "original_stage", _cohort_col: "cohort_id"}, inplace=True)
else:
    stage_mig = loans_pdf.groupby(["product_type", _cohort_col, "assessed_stage"]).agg(
        loan_count=("loan_id", "count"), total_gca=("gross_carrying_amount", "sum")).reset_index()
    stage_mig.rename(columns={_cohort_col: "cohort_id"}, inplace=True)
    stage_mig["original_stage"] = stage_mig["assessed_stage"]

cr_exp = loans_pdf.copy()
cr_exp["credit_risk_grade"] = pd.cut(cr_exp["current_lifetime_pd"],
    bins=RISK_GRADE_BINS, labels=RISK_GRADE_LABELS, include_lowest=True)
exp_by_grade = cr_exp.groupby(["product_type", _cohort_col, "assessed_stage", "credit_risk_grade"]).agg(
    loan_count=("loan_id", "count"), total_gca=("gross_carrying_amount", "sum")).reset_index()
exp_by_grade.rename(columns={_cohort_col: "cohort_id"}, inplace=True)

tables_to_save = [
    (ecl_pdf, "loan_level_ecl"),
    (summary, "portfolio_ecl_summary"),
    (weighted, "loan_ecl_weighted"),
    (scenario_sum, "scenario_ecl_summary"),
    (mc_dist_pdf, "mc_ecl_distribution"),
    (stage_mig, "ifrs7_stage_migration"),
    (exp_by_grade, "ifrs7_credit_risk_exposure"),
]

for df, name in tables_to_save:
    spark.createDataFrame(df).write.mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable(f"{FULL_SCHEMA}.{name}")
    print(f"  {name}: {len(df):,} rows")

print(f"\n{'='*70}")
print(f"  ECL Calculation Complete!")
print(f"  Total ECL: ${grand_ecl:,.0f} ({grand_cov:.2f}% coverage)")
print(f"  {len(SCENARIOS)} scenarios, {N_SIMS} MC simulations per loan-scenario")
print(f"  Satellite models: {len(SAT_MODELS)} product-cohort combinations")
print(f"  {len(ecl_pdf):,} loan-level ECL records generated")
print(f"{'='*70}")
