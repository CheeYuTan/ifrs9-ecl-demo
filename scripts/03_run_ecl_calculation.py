"""
IFRS 9 ECL Calculation Engine — Production-Grade Monte Carlo
=============================================================
Computes forward-looking credit losses per IFRS 9.5.5 with:
  - 8 plausible macro-economic scenarios (IFRS 9.5.5.17)
  - Product-specific satellite models for Stressed PD / Stressed LGD
  - PD term structure with increasing hazard rates (not flat)
  - 1,000 Monte Carlo simulations per loan-scenario
  - Product-specific PD-LGD correlation (Cholesky)
  - Downturn LGD adjustment per scenario severity
  - Prepayment-adjusted EAD with contractual amortization
  - Quarterly cash flow discounting at EIR
  - Stage-dependent horizons: 12-month (Stage 1) vs full remaining life (Stage 2/3)
  - Real stage migration matrix (prior_stage vs assessed_stage)
"""
from pyspark.sql import SparkSession
import numpy as np
import pandas as pd

spark = SparkSession.builder.getOrCreate()

PROJECT_ID = "Q4-2025-IFRS9"
REPORTING_DATE = "2025-12-31"
N_SIMS = 1000
CATALOG = "lakemeter_catalog"
SCHEMA = "expected_credit_loss"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

SCENARIO_WEIGHTS = {
    "baseline": 0.30, "mild_recovery": 0.15, "strong_growth": 0.05,
    "mild_downturn": 0.15, "adverse": 0.15, "stagflation": 0.08,
    "severely_adverse": 0.07, "tail_risk": 0.05,
}
SCENARIOS = list(SCENARIO_WEIGHTS.keys())

# Product-specific satellite model coefficients — will be calibrated below
# via OLS regression on quarterly_default_rates table.
# Fallback values used only if regression fails for a product.
FALLBACK_SAT = {
    "pd_unemp": 0.10, "pd_gdp": 0.06, "pd_infl": 0.03,
    "lgd_unemp": 0.035, "lgd_gdp": 0.025, "lgd_infl": 0.01,
    "pd_lgd_corr": 0.30, "annual_prepay_rate": 0.05,
    "r_squared_pd": 0.0, "r_squared_lgd": 0.0, "calibration_n": 0,
}
DEFAULT_SAT = FALLBACK_SAT.copy()

PREPAY_RATES = {
    "credit_builder": 0.08, "emergency_microloan": 0.05,
    "career_transition": 0.12, "bnpl_professional": 0.03, "payroll_advance": 0.02,
}

SATELLITE_COEFFICIENTS = {}  # populated by regression below

# Credit risk grading aligned to internal rating scale (not S&P)
RISK_GRADE_BINS = [0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0]
RISK_GRADE_LABELS = ["1-Minimal", "2-Low", "3-Satisfactory", "4-Acceptable",
                     "5-Watch", "6-Substandard", "7-Doubtful", "8-Loss"]

print("=" * 70)
print("  IFRS 9 Forward-Looking Credit Loss Engine")
print(f"  {len(SCENARIOS)} plausible scenarios × {N_SIMS} Monte Carlo simulations")
print(f"  Product-specific satellite models with PD term structure")
print("=" * 70)

model_ready = spark.table(f"{FULL_SCHEMA}.model_ready_loans")
macro_scenarios = spark.table(f"{FULL_SCHEMA}.macro_scenarios")
historical_defaults = spark.table(f"{FULL_SCHEMA}.historical_defaults")
quarterly_dr = spark.table(f"{FULL_SCHEMA}.quarterly_default_rates")

loans_pdf = model_ready.toPandas()
macro_pdf = macro_scenarios.toPandas()
defaults_pdf = historical_defaults.toPandas()
qdr_pdf = quarterly_dr.toPandas()

print(f"\nLoaded {len(loans_pdf):,} loans, {len(macro_pdf):,} macro rows, "
      f"{len(defaults_pdf):,} default records, {len(qdr_pdf):,} quarterly DR observations")

# ── LGD Calibration from Historical Defaults ─────────────────────────────────
print("\n[1/6] LGD CALIBRATION (with downturn adjustment)")
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

# ══════════════════════════════════════════════════════════════════════════════
# ── Satellite Model Calibration via Logistic Regression ───────────────────────
# ══════════════════════════════════════════════════════════════════════════════
#
# Non-linear satellite model using logit transform:
#   PD model:  logit(default_rate) = β₀ + β₁·unemp + β₂·gdp + β₃·inflation
#   LGD model: logit(lgd)          = γ₀ + γ₁·unemp + γ₂·gdp + γ₃·inflation
#
# where logit(p) = ln(p / (1-p))  and  sigmoid(z) = 1 / (1 + exp(-z))
#
# Why logistic instead of linear?
#   1. Output is naturally bounded between 0 and 1 (can't predict negative PD)
#   2. Non-linear in the tails — extreme macro stress produces accelerating
#      losses, not just proportional increases
#   3. Standard in credit risk modeling, well-accepted by regulators
#
# The β coefficients operate in log-odds space. To compute scenario multipliers,
# we predict PD under each scenario and divide by the baseline prediction.
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2/6] SATELLITE MODEL — Logistic Regression Calibration")
print("  Regressing logit(default_rate) against macro variables per product...")
print("  Non-linear model: captures tail-risk acceleration under stress\n")

def logit(p):
    """Log-odds transform: logit(p) = ln(p/(1-p)). Clips to avoid inf."""
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))

def sigmoid(z):
    """Inverse logit: sigmoid(z) = 1/(1+exp(-z)). Maps log-odds back to probability."""
    return 1.0 / (1.0 + np.exp(-np.clip(z, -20, 20)))

def logistic_r2(y_true, y_pred_prob):
    """McFadden's pseudo-R² for logistic regression."""
    ll_model = np.sum(y_true * np.log(np.clip(y_pred_prob, 1e-10, 1)) +
                      (1 - y_true) * np.log(np.clip(1 - y_pred_prob, 1e-10, 1)))
    p_bar = y_true.mean()
    ll_null = len(y_true) * (p_bar * np.log(max(p_bar, 1e-10)) +
                              (1 - p_bar) * np.log(max(1 - p_bar, 1e-10)))
    return 1.0 - ll_model / ll_null if ll_null != 0 else 0.0

lgd_quarterly = (defaults_pdf.groupby(["product_type", "quarter"])["loss_given_default"]
                 .mean().reset_index()
                 .rename(columns={"loss_given_default": "observed_lgd"}))

products_in_data = sorted(qdr_pdf["product_type"].unique())

# Store logistic model objects for scenario prediction
PD_LOGISTIC_MODELS = {}
LGD_LOGISTIC_MODELS = {}

for product in products_in_data:
    prod_dr = qdr_pdf[qdr_pdf["product_type"] == product].copy()
    n_obs = len(prod_dr)

    if n_obs < 8:
        print(f"  {product}: Only {n_obs} quarters — using fallback coefficients")
        SATELLITE_COEFFICIENTS[product] = {**FALLBACK_SAT, "calibration_n": n_obs,
                                            "annual_prepay_rate": PREPAY_RATES.get(product, 0.05)}
        continue

    # ── PD Logistic Regression ────────────────────────────────────────────
    # Transform: logit(observed_default_rate) = β₀ + β₁·unemp + β₂·gdp + β₃·infl
    X = prod_dr[["unemployment_rate", "gdp_growth_rate", "inflation_rate"]].values
    X_with_const = np.column_stack([np.ones(n_obs), X])
    y_pd_raw = prod_dr["observed_default_rate"].values
    y_pd_logit = logit(y_pd_raw)

    # OLS on the logit-transformed target: β = (XᵀX)⁻¹ Xᵀ·logit(y)
    beta_pd = np.linalg.solve(X_with_const.T @ X_with_const, X_with_const.T @ y_pd_logit)

    # Predictions back in probability space via sigmoid
    y_pred_logit = X_with_const @ beta_pd
    y_pred_prob = sigmoid(y_pred_logit)
    r2_pd = logistic_r2(y_pd_raw, y_pred_prob)

    # Also compute standard R² on the logit space for interpretability
    ss_res = np.sum((y_pd_logit - y_pred_logit) ** 2)
    ss_tot = np.sum((y_pd_logit - y_pd_logit.mean()) ** 2)
    r2_logit_space = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    PD_LOGISTIC_MODELS[product] = beta_pd
    mean_dr = y_pd_raw.mean()

    # Marginal effects at the mean (for interpretability / multiplier conversion)
    # For logistic: ∂p/∂x = β × p × (1-p), evaluated at mean
    p_at_mean = sigmoid(beta_pd[0] + beta_pd[1]*X[:,0].mean() + beta_pd[2]*X[:,1].mean() + beta_pd[3]*X[:,2].mean())
    scale = p_at_mean * (1 - p_at_mean)
    pd_unemp_marginal = beta_pd[1] * scale / mean_dr if mean_dr > 0 else 0.10
    pd_gdp_marginal = -beta_pd[2] * scale / mean_dr if mean_dr > 0 else 0.06
    pd_infl_marginal = beta_pd[3] * scale / mean_dr if mean_dr > 0 else 0.03

    print(f"  ┌─ {product} — PD Logistic Regression ({n_obs} quarters)")
    print(f"  │  logit(DR) = {beta_pd[0]:.4f} + {beta_pd[1]:+.4f}·unemp + {beta_pd[2]:+.4f}·gdp + {beta_pd[3]:+.4f}·infl")
    print(f"  │  R²(logit-space) = {r2_logit_space:.4f}  |  Pseudo-R² = {r2_pd:.4f}  |  Mean DR = {mean_dr:.4%}")
    print(f"  │  Marginal effects at mean: unemp={pd_unemp_marginal:.4f}, gdp={pd_gdp_marginal:.4f}, infl={pd_infl_marginal:.4f}")
    print(f"  │  Non-linearity: at DR=5% → +1pp unemp adds {beta_pd[1]*0.05*0.95:.4%}")
    print(f"  │                 at DR=15% → +1pp unemp adds {beta_pd[1]*0.15*0.85:.4%}  (accelerating)")

    # ── LGD Logistic Regression ───────────────────────────────────────────
    prod_lgd = lgd_quarterly[lgd_quarterly["product_type"] == product].copy()
    prod_lgd = prod_lgd.merge(
        qdr_pdf[qdr_pdf["product_type"] == product][["quarter", "unemployment_rate", "gdp_growth_rate", "inflation_rate"]],
        on="quarter", how="inner"
    )
    n_lgd = len(prod_lgd)

    if n_lgd >= 8:
        X_lgd = prod_lgd[["unemployment_rate", "gdp_growth_rate", "inflation_rate"]].values
        X_lgd_c = np.column_stack([np.ones(n_lgd), X_lgd])
        y_lgd_raw = prod_lgd["observed_lgd"].values
        y_lgd_logit = logit(y_lgd_raw)

        beta_lgd = np.linalg.solve(X_lgd_c.T @ X_lgd_c, X_lgd_c.T @ y_lgd_logit)
        y_lgd_pred_logit = X_lgd_c @ beta_lgd
        y_lgd_pred_prob = sigmoid(y_lgd_pred_logit)

        ss_res_lgd = np.sum((y_lgd_logit - y_lgd_pred_logit) ** 2)
        ss_tot_lgd = np.sum((y_lgd_logit - y_lgd_logit.mean()) ** 2)
        r2_lgd = 1.0 - ss_res_lgd / ss_tot_lgd if ss_tot_lgd > 0 else 0.0

        LGD_LOGISTIC_MODELS[product] = beta_lgd
        mean_lgd = y_lgd_raw.mean()

        lgd_at_mean = sigmoid(beta_lgd[0] + beta_lgd[1]*X_lgd[:,0].mean() + beta_lgd[2]*X_lgd[:,1].mean() + beta_lgd[3]*X_lgd[:,2].mean())
        lgd_scale = lgd_at_mean * (1 - lgd_at_mean)
        lgd_unemp_marginal = beta_lgd[1] * lgd_scale / mean_lgd if mean_lgd > 0 else 0.035
        lgd_gdp_marginal = -beta_lgd[2] * lgd_scale / mean_lgd if mean_lgd > 0 else 0.025
        lgd_infl_marginal = beta_lgd[3] * lgd_scale / mean_lgd if mean_lgd > 0 else 0.01

        print(f"  │")
        print(f"  │  logit(LGD) = {beta_lgd[0]:.4f} + {beta_lgd[1]:+.4f}·unemp + {beta_lgd[2]:+.4f}·gdp + {beta_lgd[3]:+.4f}·infl")
        print(f"  │  R²(logit-space) = {r2_lgd:.4f}  |  Mean LGD = {mean_lgd:.4%}")
    else:
        r2_lgd = 0.0
        lgd_unemp_marginal, lgd_gdp_marginal, lgd_infl_marginal = 0.035, 0.025, 0.01
        LGD_LOGISTIC_MODELS[product] = None
        print(f"  │  LGD: insufficient data ({n_lgd} quarters), using fallback")

    # ── PD-LGD Correlation (from logit-space residuals) ───────────────────
    if n_lgd >= 8 and n_obs >= 8 and LGD_LOGISTIC_MODELS.get(product) is not None:
        merged = prod_dr.merge(prod_lgd[["quarter", "observed_lgd"]], on="quarter", how="inner")
        if len(merged) >= 8:
            m_X = merged[["unemployment_rate", "gdp_growth_rate", "inflation_rate"]].values
            m_X_c = np.column_stack([np.ones(len(merged)), m_X])
            pd_resid = logit(merged["observed_default_rate"].values) - (m_X_c @ beta_pd)
            lgd_resid = logit(merged["observed_lgd"].values) - (m_X_c @ beta_lgd)
            corr_matrix = np.corrcoef(pd_resid, lgd_resid)
            pd_lgd_corr = max(0.10, min(0.60, corr_matrix[0, 1]))
        else:
            pd_lgd_corr = 0.30
    else:
        pd_lgd_corr = 0.30

    print(f"  │  PD-LGD correlation (logit-space residuals): {pd_lgd_corr:.4f}")
    print(f"  └─────────────────────────────────────────────")

    SATELLITE_COEFFICIENTS[product] = {
        "pd_unemp": round(abs(pd_unemp_marginal), 6),
        "pd_gdp": round(abs(pd_gdp_marginal), 6),
        "pd_infl": round(abs(pd_infl_marginal), 6),
        "lgd_unemp": round(abs(lgd_unemp_marginal), 6),
        "lgd_gdp": round(abs(lgd_gdp_marginal), 6),
        "lgd_infl": round(abs(lgd_infl_marginal), 6),
        "pd_lgd_corr": round(pd_lgd_corr, 4),
        "annual_prepay_rate": PREPAY_RATES.get(product, 0.05),
        "r_squared_pd": round(r2_logit_space, 4),
        "r_squared_lgd": round(r2_lgd, 4),
        "calibration_n": n_obs,
        "pd_logistic_beta": [round(float(b), 8) for b in beta_pd],
        "lgd_logistic_beta": [round(float(b), 8) for b in beta_lgd] if LGD_LOGISTIC_MODELS.get(product) is not None else None,
    }

print(f"\n  Calibrated {len(SATELLITE_COEFFICIENTS)} product satellite models via logistic regression")

# ── Apply Logistic Satellite Model to Forward-Looking Scenarios ───────────────
# Instead of linear multipliers, we predict PD/LGD directly under each scenario
# using the logistic model, then compute: multiplier = predicted_scenario / predicted_baseline
# This produces non-linear multipliers that accelerate under extreme stress.
print("\n  Applying logistic model to forward-looking scenarios...")
print("  (multipliers are non-linear — severe scenarios produce disproportionately higher stress)")

baseline_macro = macro_pdf[macro_pdf["scenario_name"] == "baseline"]
if baseline_macro.empty:
    print("  WARNING: No 'baseline' scenario found, using first scenario as reference")
    baseline_macro = macro_pdf.groupby("scenario_name").first().iloc[:1]

base_unemp = baseline_macro["unemployment_rate"].mean()
base_gdp = baseline_macro["gdp_growth_rate"].mean()
base_infl = baseline_macro["inflation_rate"].mean()

MACRO_ADJ = {}
for scenario in SCENARIOS:
    sc = macro_pdf[macro_pdf["scenario_name"] == scenario]
    if len(sc) == 0:
        MACRO_ADJ[scenario] = {p: {"pd_mult": 1.0, "lgd_mult": 1.0, "pd_vol": 0.05, "lgd_vol": 0.03}
                               for p in SATELLITE_COEFFICIENTS}
        print(f"  {scenario}: NO DATA — using defaults")
        continue

    sc_unemp = sc["unemployment_rate"].mean()
    sc_gdp = sc["gdp_growth_rate"].mean()
    sc_infl = sc["inflation_rate"].mean()

    scenario_adj = {}
    for product, coeff in SATELLITE_COEFFICIENTS.items():
        beta_pd_model = PD_LOGISTIC_MODELS.get(product)
        beta_lgd_model = LGD_LOGISTIC_MODELS.get(product)

        if beta_pd_model is not None:
            # Predict PD under baseline and scenario using logistic model
            pd_baseline = sigmoid(beta_pd_model[0] + beta_pd_model[1]*base_unemp + beta_pd_model[2]*base_gdp + beta_pd_model[3]*base_infl)
            pd_scenario = sigmoid(beta_pd_model[0] + beta_pd_model[1]*sc_unemp + beta_pd_model[2]*sc_gdp + beta_pd_model[3]*sc_infl)
            pd_mult = pd_scenario / pd_baseline if pd_baseline > 0 else 1.0
        else:
            d_unemp = sc_unemp - base_unemp
            d_gdp = base_gdp - sc_gdp
            d_infl = sc_infl - base_infl
            pd_mult = 1.0 + d_unemp * coeff["pd_unemp"] + d_gdp * coeff["pd_gdp"] + d_infl * coeff["pd_infl"]

        if beta_lgd_model is not None:
            lgd_baseline = sigmoid(beta_lgd_model[0] + beta_lgd_model[1]*base_unemp + beta_lgd_model[2]*base_gdp + beta_lgd_model[3]*base_infl)
            lgd_scenario = sigmoid(beta_lgd_model[0] + beta_lgd_model[1]*sc_unemp + beta_lgd_model[2]*sc_gdp + beta_lgd_model[3]*sc_infl)
            lgd_mult = lgd_scenario / lgd_baseline if lgd_baseline > 0 else 1.0
        else:
            d_unemp = sc_unemp - base_unemp
            d_gdp = base_gdp - sc_gdp
            d_infl = sc_infl - base_infl
            lgd_mult = 1.0 + d_unemp * coeff["lgd_unemp"] + d_gdp * coeff["lgd_gdp"] + d_infl * coeff["lgd_infl"]

        pd_mult = max(pd_mult, 0.5)
        lgd_mult = max(lgd_mult, 0.85)

        pd_vol = 0.05 + abs(pd_mult - 1.0) * 0.25
        lgd_vol = 0.03 + abs(lgd_mult - 1.0) * 0.18

        scenario_adj[product] = {
            "pd_mult": round(pd_mult, 4), "lgd_mult": round(lgd_mult, 4),
            "pd_vol": round(pd_vol, 4), "lgd_vol": round(lgd_vol, 4),
        }

    MACRO_ADJ[scenario] = scenario_adj
    sample_p = list(SATELLITE_COEFFICIENTS.keys())[0]
    sa = scenario_adj[sample_p]
    print(f"  {scenario}: weight={SCENARIO_WEIGHTS[scenario]:.0%}, "
          f"sample({sample_p}) PD×{sa['pd_mult']:.3f} LGD×{sa['lgd_mult']:.3f}")

# ── PD Term Structure Helper ─────────────────────────────────────────────────
def marginal_pd_quarter(annual_pd, quarter_idx, stage):
    """
    Compute marginal PD for a single quarter.
    Accepts scalar or array annual_pd (for vectorized Monte Carlo).
    Stage 2/3: increasing hazard rate (credit deterioration).
    Stage 1: flat hazard (constant default intensity).
    """
    quarterly_base = 1.0 - (1.0 - annual_pd) ** 0.25
    if stage == 1:
        return np.clip(quarterly_base, 0, 0.99)
    aging_factor = 1.0 + 0.08 * quarter_idx
    return np.clip(quarterly_base * aging_factor, 0, 0.99)

# ── Monte Carlo ECL Calculation ───────────────────────────────────────────────
print(f"\n[3/6] MONTE CARLO ECL — {len(loans_pdf):,} loans × {len(SCENARIOS)} scenarios × {N_SIMS} sims")

np.random.seed(42)
ecl_records = []
mc_scenario_stats = {s: [] for s in SCENARIOS}

for idx, loan in loans_pdf.iterrows():
    loan_id = loan["loan_id"]
    product = loan["product_type"]
    stage = int(loan["assessed_stage"])
    gca = float(loan["gross_carrying_amount"])
    eir = float(loan["effective_interest_rate"])
    current_pd = float(loan["current_lifetime_pd"])
    rem_months = int(loan["remaining_months"])
    remaining_q = max(rem_months // 3, 1)

    coll_val = loan.get("current_collateral_value")
    coll_val = 0.0 if pd.isna(coll_val) else float(coll_val)

    sat = SATELLITE_COEFFICIENTS.get(product, DEFAULT_SAT)
    rho = sat["pd_lgd_corr"]
    annual_prepay = sat["annual_prepay_rate"]
    quarterly_prepay = 1.0 - (1.0 - annual_prepay) ** 0.25

    base_lgd = LGD_BY_PRODUCT.get(product, 0.5)
    lgd_std = LGD_STD_BY_PRODUCT.get(product, 0.15)
    if product == "credit_builder" and coll_val > 0:
        base_lgd = max(0.05, 1.0 - coll_val / max(gca, 1))
        lgd_std = min(lgd_std, 0.08)

    max_h_s1 = min(4, remaining_q)
    max_h_lifetime = remaining_q
    max_h = max_h_s1 if stage == 1 else max_h_lifetime

    is_bullet = rem_months <= 3

    for scenario in SCENARIOS:
        macro = MACRO_ADJ[scenario].get(product, MACRO_ADJ[scenario].get(list(MACRO_ADJ[scenario].keys())[0]))
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

        mc_scenario_stats[scenario].append(ecl_mean)

        ecl_records.append({
            "loan_id": loan_id, "product_type": product, "assessed_stage": stage,
            "scenario": scenario, "scenario_weight": weight,
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
print("\n[4/6] AGGREGATION")

weighted = ecl_pdf.groupby(["loan_id", "product_type", "assessed_stage", "gross_carrying_amount"]).agg(
    weighted_ecl=("weighted_ecl", "sum")).reset_index()

summary = weighted.groupby(["product_type", "assessed_stage"]).agg(
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

print(f"\n{'Scenario':<20} {'Weight':>7} {'ECL Mean':>18} {'ECL P95':>18} {'Weighted':>18}")
print("-" * 85)
for _, r in scenario_sum.sort_values("weight", ascending=False).iterrows():
    print(f"{r['scenario']:<20} {r['weight']:>6.0%} ${r['total_ecl']:>15,.0f} ${r['total_ecl_p95']:>15,.0f} ${r['weighted_contribution']:>15,.0f}")
print(f"{'Probability-Weighted':<20} {'':>7} {'':>18} {'':>18} ${scenario_sum['weighted_contribution'].sum():>15,.0f}")

mc_dist_records = []
for scenario in SCENARIOS:
    macro_sample = MACRO_ADJ[scenario]
    sc_ecl = ecl_pdf[ecl_pdf["scenario"] == scenario]
    avg_pd_m = np.mean([v["pd_mult"] for v in macro_sample.values()])
    avg_lgd_m = np.mean([v["lgd_mult"] for v in macro_sample.values()])
    avg_pd_v = np.mean([v["pd_vol"] for v in macro_sample.values()])
    avg_lgd_v = np.mean([v["lgd_vol"] for v in macro_sample.values()])
    mc_dist_records.append({
        "scenario": scenario,
        "weight": SCENARIO_WEIGHTS[scenario],
        "ecl_mean": round(sc_ecl["ecl_amount"].sum(), 2),
        "ecl_p50": round(sc_ecl["ecl_p50"].sum(), 2),
        "ecl_p75": round(sc_ecl["ecl_p75"].sum(), 2),
        "ecl_p95": round(sc_ecl["ecl_p95"].sum(), 2),
        "ecl_p99": round(sc_ecl["ecl_p99"].sum(), 2),
        "avg_pd_multiplier": round(avg_pd_m, 4),
        "avg_lgd_multiplier": round(avg_lgd_m, 4),
        "pd_vol": round(avg_pd_v, 4),
        "lgd_vol": round(avg_lgd_v, 4),
        "n_simulations": N_SIMS,
    })
mc_dist_pdf = pd.DataFrame(mc_dist_records)

# ── Satellite Model Metadata (for governance/audit) ──────────────────────────
# Records the regression-derived coefficients, R², sample sizes, and raw betas
# so auditors and model validators can reproduce the calibration.
sat_meta_records = []
for product, coeff in SATELLITE_COEFFICIENTS.items():
    sat_meta_records.append({
        "product_type": product,
        "calibration_method": "LOGISTIC_REGRESSION",
        "pd_marginal_unemp": coeff["pd_unemp"],
        "pd_marginal_gdp": coeff["pd_gdp"],
        "pd_marginal_infl": coeff["pd_infl"],
        "lgd_marginal_unemp": coeff["lgd_unemp"],
        "lgd_marginal_gdp": coeff["lgd_gdp"],
        "lgd_marginal_infl": coeff["lgd_infl"],
        "pd_lgd_correlation": coeff["pd_lgd_corr"],
        "annual_prepayment_rate": coeff["annual_prepay_rate"],
        "r_squared_pd_logit_space": coeff["r_squared_pd"],
        "r_squared_lgd_logit_space": coeff["r_squared_lgd"],
        "calibration_sample_quarters": coeff["calibration_n"],
        "pd_logistic_betas": str(coeff.get("pd_logistic_beta", [])),
        "lgd_logistic_betas": str(coeff.get("lgd_logistic_beta", [])),
        "calibration_date": REPORTING_DATE,
        "next_recalibration_date": "2026-06-30",
        "model_version": "v4.0-logistic",
        "reporting_date": REPORTING_DATE,
    })
sat_meta_pdf = pd.DataFrame(sat_meta_records)

# ── IFRS 7 Disclosures ───────────────────────────────────────────────────────
print("\n[5/6] IFRS 7 DISCLOSURES")

# Stage migration: use prior_stage from data processing (if available) vs assessed_stage
if "prior_stage" in loans_pdf.columns:
    stage_mig = loans_pdf.groupby(["product_type", "prior_stage", "assessed_stage"]).agg(
        loan_count=("loan_id", "count"), total_gca=("gross_carrying_amount", "sum")).reset_index()
    stage_mig.rename(columns={"prior_stage": "original_stage"}, inplace=True)
else:
    stage_mig = loans_pdf.groupby(["product_type", "assessed_stage"]).agg(
        loan_count=("loan_id", "count"), total_gca=("gross_carrying_amount", "sum")).reset_index()
    stage_mig["original_stage"] = stage_mig["assessed_stage"]

cr_exp = loans_pdf.copy()
cr_exp["credit_risk_grade"] = pd.cut(cr_exp["current_lifetime_pd"],
    bins=RISK_GRADE_BINS, labels=RISK_GRADE_LABELS, include_lowest=True)
exp_by_grade = cr_exp.groupby(["product_type", "assessed_stage", "credit_risk_grade"]).agg(
    loan_count=("loan_id", "count"), total_gca=("gross_carrying_amount", "sum")).reset_index()

# ── Save to UC Delta ──────────────────────────────────────────────────────────
print("\n[6/6] SAVING RESULTS TO UNITY CATALOG")

tables_to_save = [
    (ecl_pdf, "loan_level_ecl"),
    (summary, "portfolio_ecl_summary"),
    (weighted, "loan_ecl_weighted"),
    (scenario_sum, "scenario_ecl_summary"),
    (mc_dist_pdf, "mc_ecl_distribution"),
    (sat_meta_pdf, "satellite_model_metadata"),
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
print(f"  Product-specific satellite models (R²: {min(c['r_squared_pd'] for c in SATELLITE_COEFFICIENTS.values()):.0%}-{max(c['r_squared_pd'] for c in SATELLITE_COEFFICIENTS.values()):.0%})")
print(f"  {len(ecl_pdf):,} loan-level ECL records generated")
print(f"{'='*70}")
