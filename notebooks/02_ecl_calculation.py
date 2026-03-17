# Databricks notebook source
# MAGIC %md
# MAGIC # IFRS 9 ECL Calculation Engine (Monte Carlo)
# MAGIC
# MAGIC Implements IFRS 9 ECL with stochastic simulation:
# MAGIC 1. Satellite model: macro variables → PD/LGD multipliers (IFRS 9.B5.5.49)
# MAGIC 2. Monte Carlo simulation: N draws of PD/LGD per scenario (IFRS 9.5.5.17)
# MAGIC 3. EAD projection with amortization (IFRS 9.B5.5.53)
# MAGIC 4. ECL = PD × LGD × EAD × DF, discounted at EIR (IFRS 9.B5.5.44)
# MAGIC 5. Probability-weighted ECL across 8 scenarios (IFRS 9.5.5.4)
# MAGIC 6. Distribution statistics: mean, P50, P75, P95, P99 ECL
# MAGIC 7. IFRS 7 disclosure outputs

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

dbutils.widgets.text("project_id", "", "Project ID")
dbutils.widgets.text("reporting_date", "2025-12-31", "Reporting Date")
dbutils.widgets.text("horizon_quarters", "5", "Forecast Horizon (quarters)")
dbutils.widgets.text("mc_simulations", "500", "Monte Carlo Simulations per Scenario")

PROJECT_ID = dbutils.widgets.get("project_id")
REPORTING_DATE = dbutils.widgets.get("reporting_date")
HORIZON_Q = int(dbutils.widgets.get("horizon_quarters"))
N_SIMS = int(dbutils.widgets.get("mc_simulations"))

CATALOG = "lakemeter_catalog"
SCHEMA = "expected_credit_loss"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

print(f"Project: {PROJECT_ID}")
print(f"Reporting Date: {REPORTING_DATE}")
print(f"Horizon: {HORIZON_Q} quarters")
print(f"Monte Carlo Simulations: {N_SIMS} per scenario")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Data

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import *
import numpy as np
import pandas as pd
from datetime import date

model_ready = spark.table(f"{FULL_SCHEMA}.model_ready_loans")
macro_scenarios = spark.table(f"{FULL_SCHEMA}.macro_scenarios")
historical_defaults = spark.table(f"{FULL_SCHEMA}.historical_defaults")

loans_pdf = model_ready.toPandas()
macro_pdf = macro_scenarios.toPandas()
defaults_pdf = historical_defaults.toPandas()

SCENARIOS = sorted(macro_pdf["scenario_name"].unique().tolist())
SCENARIO_WEIGHTS = {}
for s in SCENARIOS:
    w = macro_pdf[macro_pdf["scenario_name"] == s]["scenario_weight"].iloc[0]
    SCENARIO_WEIGHTS[s] = float(w)

print(f"Loaded {len(loans_pdf):,} loans for ECL calculation")
print(f"Loaded {len(macro_pdf):,} macro scenario records ({len(SCENARIOS)} scenarios)")
print(f"Loaded {len(defaults_pdf):,} historical defaults")
print(f"\nScenario weights: {SCENARIO_WEIGHTS}")
print(f"Weight sum: {sum(SCENARIO_WEIGHTS.values()):.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Calibrate LGD by Product (from historical data)

# COMMAND ----------

print("Calibrating LGD from historical defaults...")
print("-" * 60)

LGD_BY_PRODUCT = {}
for product in loans_pdf["product_type"].unique():
    prod_defaults = defaults_pdf[defaults_pdf["product_type"] == product]
    if len(prod_defaults) > 0:
        avg_lgd = prod_defaults["loss_given_default"].mean()
        std_lgd = prod_defaults["loss_given_default"].std()
    else:
        avg_lgd = 0.50
        std_lgd = 0.15

    LGD_BY_PRODUCT[product] = {
        "mean": round(avg_lgd, 4),
        "std": round(std_lgd, 4),
        "n_obs": len(prod_defaults),
    }
    print(f"  {product}: LGD = {avg_lgd:.2%} (std={std_lgd:.2%}, n={len(prod_defaults):,})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Satellite Model — Macro → PD/LGD Multipliers
# MAGIC
# MAGIC The satellite model translates macro-economic variables into risk parameter adjustments.
# MAGIC PD sensitivity: unemployment (+0.08/pp), GDP (-0.05/pp), inflation (+0.02/pp)
# MAGIC LGD sensitivity: unemployment (+0.03/pp), GDP (-0.02/pp)
# MAGIC These coefficients represent a simplified regression-based linkage.

# COMMAND ----------

base_macro = macro_pdf[macro_pdf["scenario_name"] == "baseline"]
if len(base_macro) == 0:
    base_macro = macro_pdf[macro_pdf["scenario_name"] == SCENARIOS[0]]

base_unemployment = base_macro["unemployment_rate"].mean()
base_gdp = base_macro["gdp_growth_rate"].mean()
base_inflation = base_macro["inflation_rate"].mean()

print(f"Base macro anchors: unemployment={base_unemployment:.2f}%, GDP={base_gdp:.2f}%, inflation={base_inflation:.2f}%")
print("-" * 60)

MACRO_ADJUSTMENT = {}
for scenario in SCENARIOS:
    sc_data = macro_pdf[macro_pdf["scenario_name"] == scenario].sort_values("quarters_ahead")
    avg_unemployment = sc_data["unemployment_rate"].mean()
    avg_gdp = sc_data["gdp_growth_rate"].mean()
    avg_inflation = sc_data["inflation_rate"].mean()

    d_unemp = avg_unemployment - base_unemployment
    d_gdp = base_gdp - avg_gdp
    d_infl = avg_inflation - base_inflation

    pd_multiplier = 1.0 + d_unemp * 0.08 + d_gdp * 0.05 + d_infl * 0.02
    lgd_multiplier = 1.0 + d_unemp * 0.03 + d_gdp * 0.02

    # PD/LGD volatility for Monte Carlo — wider spread for more extreme scenarios
    pd_vol = 0.05 + abs(pd_multiplier - 1.0) * 0.3
    lgd_vol = 0.03 + abs(lgd_multiplier - 1.0) * 0.2

    MACRO_ADJUSTMENT[scenario] = {
        "pd_multiplier": round(max(pd_multiplier, 0.5), 4),
        "lgd_multiplier": round(max(lgd_multiplier, 0.8), 4),
        "pd_vol": round(pd_vol, 4),
        "lgd_vol": round(lgd_vol, 4),
        "weight": SCENARIO_WEIGHTS[scenario],
    }
    print(f"  {scenario:20s}: PD x{pd_multiplier:.3f} (vol={pd_vol:.3f}), LGD x{lgd_multiplier:.3f} (vol={lgd_vol:.3f}), weight={SCENARIO_WEIGHTS[scenario]:.0%}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Monte Carlo ECL Calculation
# MAGIC
# MAGIC For each loan × scenario, we run N_SIMS Monte Carlo draws:
# MAGIC - PD_sim = PD_base × PD_multiplier × exp(N(0, pd_vol) - pd_vol²/2)  (lognormal shock)
# MAGIC - LGD_sim = LGD_base × LGD_multiplier × exp(N(0, lgd_vol) - lgd_vol²/2)
# MAGIC - ECL_sim = Σ_q (marginal_PD × LGD × EAD_q × DF_q)
# MAGIC
# MAGIC We store the mean, P50, P75, P95, P99 of the ECL distribution per loan-scenario.

# COMMAND ----------

print(f"Running Monte Carlo ECL: {len(loans_pdf):,} loans × {len(SCENARIOS)} scenarios × {N_SIMS} sims...")
print("=" * 80)

np.random.seed(42)

ecl_records = []
mc_distribution_records = []

for idx, loan in loans_pdf.iterrows():
    loan_id = loan["loan_id"]
    product = loan["product_type"]
    stage = int(loan["assessed_stage"])
    gca = float(loan["gross_carrying_amount"])
    eir = float(loan["effective_interest_rate"])
    current_pd = float(loan["current_lifetime_pd"])
    remaining_months = max(int(loan["remaining_months"]), 1)
    remaining_quarters = max(remaining_months // 3, 1)

    collateral_value = loan.get("current_collateral_value")
    if pd.isna(collateral_value):
        collateral_value = 0.0
    else:
        collateral_value = float(collateral_value)

    base_lgd = LGD_BY_PRODUCT.get(product, {"mean": 0.5})["mean"]
    lgd_std = LGD_BY_PRODUCT.get(product, {"std": 0.15})["std"]
    if product == "credit_builder" and collateral_value > 0:
        base_lgd = max(0.0, 1.0 - collateral_value / max(gca, 1))
        base_lgd = max(base_lgd, 0.05)
        lgd_std = min(lgd_std, 0.08)

    if stage == 1:
        max_horizon = min(4, remaining_quarters, HORIZON_Q)
    else:
        max_horizon = min(remaining_quarters, HORIZON_Q * 2)

    for scenario in SCENARIOS:
        macro = MACRO_ADJUSTMENT[scenario]

        # Monte Carlo: draw N_SIMS correlated PD/LGD shocks
        # Lognormal shocks ensure PD/LGD stay positive
        z_pd = np.random.normal(0, 1, N_SIMS)
        z_lgd = 0.5 * z_pd + 0.5 * np.random.normal(0, 1, N_SIMS)  # 50% correlation

        pd_shocks = np.exp(z_pd * macro["pd_vol"] - 0.5 * macro["pd_vol"] ** 2)
        lgd_shocks = np.exp(z_lgd * macro["lgd_vol"] - 0.5 * macro["lgd_vol"] ** 2)

        sim_pds = np.clip(current_pd * macro["pd_multiplier"] * pd_shocks, 0.001, 0.99)
        sim_lgds = np.clip(base_lgd * macro["lgd_multiplier"] * lgd_shocks, 0.01, 1.0)

        # Vectorized ECL calculation across all simulations
        ecl_sims = np.zeros(N_SIMS)
        for q in range(1, max_horizon + 1):
            quarterly_pds = 1.0 - (1.0 - sim_pds) ** (1.0 / 4.0)

            if q == 1:
                survival = np.ones(N_SIMS)
            marginal_pds = survival * quarterly_pds

            months_elapsed = q * 3
            amort_factor = max(0, 1.0 - months_elapsed / remaining_months) if remaining_months > 0 else 0.0
            ead_q = gca * amort_factor

            quarterly_eir = eir / 4.0
            discount_factor = 1.0 / ((1.0 + quarterly_eir) ** q)

            ecl_sims += marginal_pds * sim_lgds * ead_q * discount_factor
            survival *= (1.0 - quarterly_pds)

        ecl_mean = float(np.mean(ecl_sims))
        ecl_std = float(np.std(ecl_sims))
        ecl_p50 = float(np.percentile(ecl_sims, 50))
        ecl_p75 = float(np.percentile(ecl_sims, 75))
        ecl_p95 = float(np.percentile(ecl_sims, 95))
        ecl_p99 = float(np.percentile(ecl_sims, 99))

        scenario_pd = float(np.mean(sim_pds))
        scenario_lgd = float(np.mean(sim_lgds))

        ecl_records.append({
            "loan_id": loan_id,
            "product_type": product,
            "assessed_stage": stage,
            "scenario": scenario,
            "scenario_weight": macro["weight"],
            "gross_carrying_amount": round(gca, 2),
            "current_lifetime_pd": round(current_pd, 6),
            "scenario_adjusted_pd": round(scenario_pd, 6),
            "base_lgd": round(base_lgd, 4),
            "scenario_adjusted_lgd": round(scenario_lgd, 4),
            "effective_interest_rate": round(eir, 4),
            "horizon_quarters": max_horizon,
            "ecl_amount": round(ecl_mean, 2),
            "ecl_std": round(ecl_std, 2),
            "ecl_p50": round(ecl_p50, 2),
            "ecl_p75": round(ecl_p75, 2),
            "ecl_p95": round(ecl_p95, 2),
            "ecl_p99": round(ecl_p99, 2),
            "weighted_ecl": round(ecl_mean * macro["weight"], 2),
            "coverage_ratio": round(ecl_mean / max(gca, 1) * 100, 4),
            "reporting_date": REPORTING_DATE,
            "project_id": PROJECT_ID,
        })

    if idx % 10000 == 0 and idx > 0:
        print(f"  Processed {idx:,} / {len(loans_pdf):,} loans...")

ecl_pdf = pd.DataFrame(ecl_records)
print(f"\n  Generated {len(ecl_pdf):,} loan-level ECL records ({len(loans_pdf):,} loans × {len(SCENARIOS)} scenarios)")
print(f"  Monte Carlo: {N_SIMS} simulations per loan-scenario pair")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Aggregate Results

# COMMAND ----------

print("\nAggregating ECL results...")
print("=" * 80)

weighted_ecl = ecl_pdf.groupby(["loan_id", "product_type", "assessed_stage", "gross_carrying_amount"]).agg(
    weighted_ecl=("weighted_ecl", "sum"),
).reset_index()

summary = weighted_ecl.groupby(["product_type", "assessed_stage"]).agg(
    loan_count=("loan_id", "count"),
    total_gca=("gross_carrying_amount", "sum"),
    total_ecl=("weighted_ecl", "sum"),
).reset_index()

summary["coverage_ratio"] = (summary["total_ecl"] / summary["total_gca"] * 100).round(2)

print("\n📊 ECL SUMMARY BY PRODUCT AND STAGE (Probability-Weighted, Monte Carlo)")
print("-" * 80)
print(f"{'Product':<25} {'Stage':>5} {'Loans':>8} {'GCA':>15} {'ECL':>15} {'Coverage':>10}")
print("-" * 80)

for _, row in summary.sort_values(["product_type", "assessed_stage"]).iterrows():
    print(f"{row['product_type']:<25} {int(row['assessed_stage']):>5} {int(row['loan_count']):>8,} "
          f"${row['total_gca']:>13,.0f} ${row['total_ecl']:>13,.0f} {row['coverage_ratio']:>9.2f}%")

product_total = summary.groupby("product_type").agg(
    loan_count=("loan_count", "sum"),
    total_gca=("total_gca", "sum"),
    total_ecl=("total_ecl", "sum"),
).reset_index()
product_total["coverage_ratio"] = (product_total["total_ecl"] / product_total["total_gca"] * 100).round(2)

print("\n" + "=" * 80)
print("📊 ECL SUMMARY BY PRODUCT (All Stages)")
print("-" * 80)
print(f"{'Product':<25} {'Loans':>8} {'GCA':>15} {'ECL':>15} {'Coverage':>10}")
print("-" * 80)
for _, row in product_total.sort_values("total_ecl", ascending=False).iterrows():
    print(f"{row['product_type']:<25} {int(row['loan_count']):>8,} "
          f"${row['total_gca']:>13,.0f} ${row['total_ecl']:>13,.0f} {row['coverage_ratio']:>9.2f}%")

grand_total_gca = product_total["total_gca"].sum()
grand_total_ecl = product_total["total_ecl"].sum()
grand_coverage = round(grand_total_ecl / grand_total_gca * 100, 2)
print("-" * 80)
print(f"{'TOTAL':<25} {int(product_total['loan_count'].sum()):>8,} "
      f"${grand_total_gca:>13,.0f} ${grand_total_ecl:>13,.0f} {grand_coverage:>9.2f}%")

# Scenario analysis
scenario_summary = ecl_pdf.groupby("scenario").agg(
    total_ecl=("ecl_amount", "sum"),
    total_ecl_p95=("ecl_p95", "sum"),
    total_ecl_p99=("ecl_p99", "sum"),
    weight=("scenario_weight", "first"),
).reset_index()
scenario_summary["weighted_contribution"] = scenario_summary["total_ecl"] * scenario_summary["weight"]

print("\n\n📊 SCENARIO ANALYSIS (with Monte Carlo distribution)")
print("-" * 80)
print(f"{'Scenario':<20} {'Weight':>7} {'Mean ECL':>14} {'P95 ECL':>14} {'P99 ECL':>14} {'Weighted':>14}")
print("-" * 80)
for _, row in scenario_summary.sort_values("weight", ascending=False).iterrows():
    print(f"{row['scenario']:<20} {row['weight']:>6.0%} ${row['total_ecl']:>12,.0f} "
          f"${row['total_ecl_p95']:>12,.0f} ${row['total_ecl_p99']:>12,.0f} ${row['weighted_contribution']:>12,.0f}")
print("-" * 80)
print(f"{'Probability-Weighted':<20} {'':>7} {'':>14} {'':>14} {'':>14} ${scenario_summary['weighted_contribution'].sum():>12,.0f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Monte Carlo Distribution Summary
# MAGIC
# MAGIC Aggregate the simulation distribution at portfolio level for each scenario.

# COMMAND ----------

mc_dist_records = []
for scenario in SCENARIOS:
    sc_data = ecl_pdf[ecl_pdf["scenario"] == scenario]
    mc_dist_records.append({
        "scenario": scenario,
        "weight": SCENARIO_WEIGHTS[scenario],
        "ecl_mean": round(sc_data["ecl_amount"].sum(), 2),
        "ecl_p50": round(sc_data["ecl_p50"].sum(), 2),
        "ecl_p75": round(sc_data["ecl_p75"].sum(), 2),
        "ecl_p95": round(sc_data["ecl_p95"].sum(), 2),
        "ecl_p99": round(sc_data["ecl_p99"].sum(), 2),
        "avg_pd_multiplier": round(MACRO_ADJUSTMENT[scenario]["pd_multiplier"], 4),
        "avg_lgd_multiplier": round(MACRO_ADJUSTMENT[scenario]["lgd_multiplier"], 4),
        "pd_vol": round(MACRO_ADJUSTMENT[scenario]["pd_vol"], 4),
        "lgd_vol": round(MACRO_ADJUSTMENT[scenario]["lgd_vol"], 4),
        "n_simulations": N_SIMS,
    })

mc_dist_pdf = pd.DataFrame(mc_dist_records)

print("\n📊 MONTE CARLO DISTRIBUTION BY SCENARIO")
print("-" * 90)
print(f"{'Scenario':<20} {'Mean':>12} {'P50':>12} {'P75':>12} {'P95':>12} {'P99':>12}")
print("-" * 90)
for _, row in mc_dist_pdf.sort_values("weight", ascending=False).iterrows():
    print(f"{row['scenario']:<20} ${row['ecl_mean']:>10,.0f} ${row['ecl_p50']:>10,.0f} "
          f"${row['ecl_p75']:>10,.0f} ${row['ecl_p95']:>10,.0f} ${row['ecl_p99']:>10,.0f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Save Results

# COMMAND ----------

print("\nSaving results to Delta tables...")

ecl_sdf = spark.createDataFrame(ecl_pdf)
ecl_sdf.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.loan_level_ecl")
print(f"  ✓ {FULL_SCHEMA}.loan_level_ecl ({len(ecl_pdf):,} rows)")

summary_sdf = spark.createDataFrame(summary)
summary_sdf.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.portfolio_ecl_summary")
print(f"  ✓ {FULL_SCHEMA}.portfolio_ecl_summary ({len(summary):,} rows)")

weighted_sdf = spark.createDataFrame(weighted_ecl)
weighted_sdf.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.loan_ecl_weighted")
print(f"  ✓ {FULL_SCHEMA}.loan_ecl_weighted ({len(weighted_ecl):,} rows)")

# Scenario summary now includes MC distribution
scenario_sdf = spark.createDataFrame(scenario_summary)
scenario_sdf.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.scenario_ecl_summary")
print(f"  ✓ {FULL_SCHEMA}.scenario_ecl_summary ({len(scenario_summary):,} rows)")

# NEW: Monte Carlo distribution table
mc_sdf = spark.createDataFrame(mc_dist_pdf)
mc_sdf.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.mc_ecl_distribution")
print(f"  ✓ {FULL_SCHEMA}.mc_ecl_distribution ({len(mc_dist_pdf):,} rows)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: IFRS 7 Disclosure Outputs

# COMMAND ----------

print("\nGenerating IFRS 7 disclosure tables...")
print("=" * 60)

stage_migration = loans_pdf.groupby(["product_type", "current_stage", "assessed_stage"]).agg(
    loan_count=("loan_id", "count"),
    total_gca=("gross_carrying_amount", "sum"),
).reset_index()
stage_migration.columns = ["product_type", "original_stage", "assessed_stage", "loan_count", "total_gca"]

spark.createDataFrame(stage_migration).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.ifrs7_stage_migration")
print(f"  ✓ IFRS 7.35H Stage migration matrix")

credit_risk_exposure = loans_pdf.copy()
credit_risk_exposure["credit_risk_grade"] = pd.cut(
    credit_risk_exposure["current_lifetime_pd"],
    bins=[0, 0.01, 0.03, 0.05, 0.10, 0.20, 0.50, 1.0],
    labels=["AAA-AA", "A", "BBB", "BB", "B", "CCC", "D"]
)
exposure_by_grade = credit_risk_exposure.groupby(["product_type", "assessed_stage", "credit_risk_grade"]).agg(
    loan_count=("loan_id", "count"),
    total_gca=("gross_carrying_amount", "sum"),
).reset_index()

spark.createDataFrame(exposure_by_grade).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.ifrs7_credit_risk_exposure")
print(f"  ✓ IFRS 7.35F Credit risk exposure by grade and stage")

print("\n✅ IFRS 7 disclosure tables generated")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Calculation Complete

# COMMAND ----------

result = {
    "status": "SUCCESS",
    "total_loans": int(len(loans_pdf)),
    "total_gca": float(grand_total_gca),
    "total_ecl_weighted": float(grand_total_ecl),
    "coverage_ratio_pct": float(grand_coverage),
    "scenarios": len(SCENARIOS),
    "mc_simulations": N_SIMS,
}

for s in SCENARIOS:
    sc_ecl = scenario_summary[scenario_summary["scenario"] == s]["total_ecl"].values
    if len(sc_ecl) > 0:
        result[f"scenario_{s}_ecl"] = float(sc_ecl[0])

print("\n" + "=" * 60)
print("ECL CALCULATION COMPLETE (Monte Carlo)")
print("=" * 60)
for k, v in result.items():
    if isinstance(v, float):
        print(f"  {k}: ${v:,.2f}" if "ecl" in k or "gca" in k else f"  {k}: {v}")
    else:
        print(f"  {k}: {v}")

dbutils.notebook.exit(str(result))
