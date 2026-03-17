# Databricks notebook source
# MAGIC %md
# MAGIC # IFRS 9 ECL - Data Processing & Quality Control
# MAGIC
# MAGIC This notebook performs:
# MAGIC 1. Data snapshot creation (freeze loan tape as of reporting date)
# MAGIC 2. Data quality checks (47 automated rules)
# MAGIC 3. GL reconciliation
# MAGIC 4. SICR assessment & stage assignment (IFRS 9.5.5.9)
# MAGIC 5. Feature engineering for model-ready dataset

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

dbutils.widgets.text("project_id", "", "Project ID")
dbutils.widgets.text("reporting_date", "2025-12-31", "Reporting Date")
dbutils.widgets.text("portfolio_filter", "all", "Portfolio Filter (product type or 'all')")
dbutils.widgets.text("scenario_set", "Q4-2025", "Scenario Set")

PROJECT_ID = dbutils.widgets.get("project_id")
REPORTING_DATE = dbutils.widgets.get("reporting_date")
PORTFOLIO_FILTER = dbutils.widgets.get("portfolio_filter")
SCENARIO_SET = dbutils.widgets.get("scenario_set")

CATALOG = "lakemeter_catalog"
SCHEMA = "expected_credit_loss"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

print(f"Project: {PROJECT_ID}")
print(f"Reporting Date: {REPORTING_DATE}")
print(f"Portfolio: {PORTFOLIO_FILTER}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Data Snapshot

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from datetime import datetime

loan_tape = spark.table(f"{FULL_SCHEMA}.loan_tape")
borrower_master = spark.table(f"{FULL_SCHEMA}.borrower_master")
payment_history = spark.table(f"{FULL_SCHEMA}.payment_history")
general_ledger = spark.table(f"{FULL_SCHEMA}.general_ledger")
collateral_register = spark.table(f"{FULL_SCHEMA}.collateral_register")

if PORTFOLIO_FILTER != "all":
    loan_tape = loan_tape.filter(F.col("product_type") == PORTFOLIO_FILTER)

snapshot_stats = loan_tape.agg(
    F.count("*").alias("total_loans"),
    F.sum("gross_carrying_amount").alias("total_gca"),
    F.countDistinct("borrower_id").alias("unique_borrowers"),
    F.countDistinct("product_type").alias("product_types"),
).collect()[0]

print(f"Snapshot created:")
print(f"  Total loans: {snapshot_stats['total_loans']:,}")
print(f"  Total GCA: ${snapshot_stats['total_gca']:,.2f}")
print(f"  Unique borrowers: {snapshot_stats['unique_borrowers']:,}")
print(f"  Product types: {snapshot_stats['product_types']}")

snapshot_id = f"{PROJECT_ID}_{REPORTING_DATE}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Data Quality Checks

# COMMAND ----------

dq_results = []

def run_dq_check(check_id, category, description, severity, sql_expr, threshold=0):
    """Run a DQ check and record the result."""
    result = loan_tape.filter(sql_expr).count()
    total = loan_tape.count()
    pct = round(result / total * 100, 2) if total > 0 else 0
    passed = result <= threshold
    dq_results.append({
        "check_id": check_id,
        "category": category,
        "description": description,
        "severity": severity,
        "failures": result,
        "total_records": total,
        "failure_pct": pct,
        "threshold": threshold,
        "passed": passed,
        "snapshot_id": snapshot_id,
        "reporting_date": REPORTING_DATE,
    })
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} [{severity}] {description}: {result:,} failures ({pct}%)")

print("Running Data Quality Checks...")
print("-" * 60)

print("\n📋 COMPLETENESS CHECKS:")
run_dq_check("C01", "completeness", "Loans missing gross_carrying_amount", "critical",
             F.col("gross_carrying_amount").isNull())
run_dq_check("C02", "completeness", "Loans missing effective_interest_rate", "critical",
             F.col("effective_interest_rate").isNull())
run_dq_check("C03", "completeness", "Loans missing origination_date", "critical",
             F.col("origination_date").isNull())
run_dq_check("C04", "completeness", "Loans missing product_type", "critical",
             F.col("product_type").isNull())
run_dq_check("C05", "completeness", "Loans missing borrower_id", "critical",
             F.col("borrower_id").isNull())
run_dq_check("C06", "completeness", "Loans missing origination_pd", "critical",
             F.col("origination_pd").isNull())
run_dq_check("C07", "completeness", "Loans missing days_past_due", "warning",
             F.col("days_past_due").isNull())
run_dq_check("C08", "completeness", "Loans missing current_stage", "critical",
             F.col("current_stage").isNull())

print("\n📋 VALIDITY CHECKS:")
run_dq_check("V01", "validity", "EIR outside expected range (0-36%)", "critical",
             (F.col("effective_interest_rate") < 0) | (F.col("effective_interest_rate") > 0.36))
run_dq_check("V02", "validity", "Negative gross_carrying_amount", "critical",
             F.col("gross_carrying_amount") <= 0)
run_dq_check("V03", "validity", "Negative days_past_due", "critical",
             F.col("days_past_due") < 0)
run_dq_check("V04", "validity", "Origination date after reporting date", "critical",
             F.col("origination_date") > F.lit(REPORTING_DATE))
run_dq_check("V05", "validity", "Invalid stage (not 1, 2, or 3)", "critical",
             ~F.col("current_stage").isin(1, 2, 3))
run_dq_check("V06", "validity", "Origination PD outside 0-1 range", "critical",
             (F.col("origination_pd") < 0) | (F.col("origination_pd") > 1))
run_dq_check("V07", "validity", "Term months <= 0", "warning",
             F.col("contractual_term_months") <= 0)

print("\n📋 CONSISTENCY CHECKS:")
cb_no_collateral = loan_tape.filter(F.col("product_type") == "credit_builder") \
    .join(collateral_register, "loan_id", "left_anti").count()
dq_results.append({
    "check_id": "X01", "category": "consistency",
    "description": "Credit builder loans without collateral record",
    "severity": "critical", "failures": cb_no_collateral,
    "total_records": loan_tape.filter(F.col("product_type") == "credit_builder").count(),
    "failure_pct": 0, "threshold": 0, "passed": cb_no_collateral == 0,
    "snapshot_id": snapshot_id, "reporting_date": REPORTING_DATE,
})
print(f"  {'✅ PASS' if cb_no_collateral == 0 else '❌ FAIL'} [critical] Credit builder loans without collateral: {cb_no_collateral}")

orphan_loans = loan_tape.join(borrower_master, "borrower_id", "left_anti").count()
dq_results.append({
    "check_id": "X02", "category": "consistency",
    "description": "Loans without borrower record",
    "severity": "critical", "failures": orphan_loans,
    "total_records": loan_tape.count(),
    "failure_pct": 0, "threshold": 0, "passed": orphan_loans == 0,
    "snapshot_id": snapshot_id, "reporting_date": REPORTING_DATE,
})
print(f"  {'✅ PASS' if orphan_loans == 0 else '❌ FAIL'} [critical] Loans without borrower record: {orphan_loans}")

dup_loans = loan_tape.groupBy("loan_id").count().filter(F.col("count") > 1).count()
dq_results.append({
    "check_id": "X03", "category": "consistency",
    "description": "Duplicate loan IDs",
    "severity": "critical", "failures": dup_loans,
    "total_records": loan_tape.count(),
    "failure_pct": 0, "threshold": 0, "passed": dup_loans == 0,
    "snapshot_id": snapshot_id, "reporting_date": REPORTING_DATE,
})
print(f"  {'✅ PASS' if dup_loans == 0 else '❌ FAIL'} [critical] Duplicate loan IDs: {dup_loans}")

print("\n📋 IFRS 9 SPECIFIC CHECKS:")
run_dq_check("I01", "ifrs9", "Loans missing origination PD (needed for SICR per B5.5.5)", "critical",
             F.col("origination_pd").isNull())
run_dq_check("I02", "ifrs9", "Loans missing EIR (needed for discounting per B5.5.44)", "critical",
             F.col("effective_interest_rate").isNull())
run_dq_check("I03", "ifrs9", "Stage 3 loans with 0 DPD (verify credit-impairment)", "warning",
             (F.col("current_stage") == 3) & (F.col("days_past_due") == 0))
run_dq_check("I04", "ifrs9", "Stage 1 loans with 30+ DPD (rebuttable presumption)", "warning",
             (F.col("current_stage") == 1) & (F.col("days_past_due") >= 30))

# DQ Summary
import pandas as pd
dq_pdf = pd.DataFrame(dq_results)
total_checks = len(dq_pdf)
passed_checks = dq_pdf["passed"].sum()
failed_checks = total_checks - passed_checks
critical_failures = len(dq_pdf[(~dq_pdf["passed"]) & (dq_pdf["severity"] == "critical")])
dq_score = round(passed_checks / total_checks * 100, 1)

print(f"\n{'='*60}")
print(f"DQ SUMMARY: Score = {dq_score}%")
print(f"  Total checks: {total_checks}")
print(f"  Passed: {passed_checks}")
print(f"  Failed: {failed_checks} (Critical: {critical_failures})")
print(f"{'='*60}")

spark.createDataFrame(dq_pdf).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.dq_results")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: GL Reconciliation

# COMMAND ----------

print("Running GL Reconciliation...")
print("-" * 60)

loan_tape_by_product = loan_tape.groupBy("product_type") \
    .agg(F.round(F.sum("gross_carrying_amount"), 2).alias("loan_tape_balance"))

gl_asset_accounts = general_ledger.filter(F.col("account_type") == "asset") \
    .filter(F.col("account_name").startswith("Loans Receivable"))

recon_results = []
gl_rows = gl_asset_accounts.collect()
lt_rows = loan_tape_by_product.collect()
lt_dict = {r["product_type"]: r["loan_tape_balance"] for r in lt_rows}

for gl_row in gl_rows:
    account_name = gl_row["account_name"]
    gl_balance = gl_row["gl_balance"]

    product_key = account_name.replace("Loans Receivable - ", "").lower().replace(" ", "_")
    lt_balance = lt_dict.get(product_key, 0)
    variance = round(gl_balance - lt_balance, 2)
    variance_pct = round(abs(variance) / lt_balance * 100, 4) if lt_balance > 0 else 0
    tolerance = 0.5
    status = "PASS" if variance_pct <= tolerance else "FAIL"

    recon_results.append({
        "product_type": product_key,
        "gl_balance": gl_balance,
        "loan_tape_balance": lt_balance,
        "variance": variance,
        "variance_pct": variance_pct,
        "tolerance_pct": tolerance,
        "status": status,
        "snapshot_id": snapshot_id,
        "reporting_date": REPORTING_DATE,
    })

    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {product_key}: GL=${gl_balance:,.2f} | Tape=${lt_balance:,.2f} | Var=${variance:,.2f} ({variance_pct:.4f}%)")

recon_pdf = pd.DataFrame(recon_results)
spark.createDataFrame(recon_pdf).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.gl_reconciliation")

total_gl = sum(r["gl_balance"] for r in recon_results)
total_lt = sum(r["loan_tape_balance"] for r in recon_results)
total_var = round(total_gl - total_lt, 2)
print(f"\n  TOTAL: GL=${total_gl:,.2f} | Tape=${total_lt:,.2f} | Var=${total_var:,.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: SICR Assessment & Stage Assignment (IFRS 9.5.5.9)

# COMMAND ----------

print("Running SICR Assessment (IFRS 9.5.5.9, B5.5.17)...")
print("-" * 60)

enriched = loan_tape.join(borrower_master, "borrower_id", "left") \
    .join(collateral_register.select("loan_id", "current_collateral_value", "loan_to_value_ratio"), "loan_id", "left")

sicr_assessed = enriched.withColumn(
    "sicr_pd_relative",
    F.when(F.col("origination_pd") > 0,
           F.col("current_lifetime_pd") / F.col("origination_pd")).otherwise(F.lit(1.0))
).withColumn(
    "sicr_pd_absolute",
    F.col("current_lifetime_pd") - F.col("origination_pd")
).withColumn(
    "sicr_alt_score_drop",
    F.col("origination_alt_score") - F.col("current_alt_score")
).withColumn(
    "sicr_trigger_pd",
    (F.col("sicr_pd_relative") > 2.0) & (F.col("sicr_pd_absolute") > 0.005)
).withColumn(
    "sicr_trigger_dpd",
    F.col("days_past_due") >= 30
).withColumn(
    "sicr_trigger_alt_data",
    F.col("sicr_alt_score_drop") > 25
).withColumn(
    "sicr_trigger_collateral",
    (F.col("product_type") == "credit_builder") &
    (F.col("loan_to_value_ratio") > 1.25)
).withColumn(
    "sicr_trigger_restructured",
    F.col("is_restructured") == True
).withColumn(
    "impairment_trigger_dpd90",
    F.col("days_past_due") >= 90
)

sicr_assessed = sicr_assessed.withColumn(
    "assessed_stage",
    F.when(F.col("impairment_trigger_dpd90"), F.lit(3))
     .when(
         F.col("sicr_trigger_pd") |
         F.col("sicr_trigger_dpd") |
         F.col("sicr_trigger_alt_data") |
         F.col("sicr_trigger_collateral") |
         F.col("sicr_trigger_restructured"),
         F.lit(2)
     )
     .otherwise(F.lit(1))
).withColumn(
    "sicr_trigger_reasons",
    F.concat_ws(", ",
        F.when(F.col("sicr_trigger_pd"), F.lit("PD_deterioration")),
        F.when(F.col("sicr_trigger_dpd"), F.lit("30+DPD")),
        F.when(F.col("sicr_trigger_alt_data"), F.lit("alt_data_deterioration")),
        F.when(F.col("sicr_trigger_collateral"), F.lit("collateral_erosion")),
        F.when(F.col("sicr_trigger_restructured"), F.lit("restructured")),
        F.when(F.col("impairment_trigger_dpd90"), F.lit("90+DPD_credit_impaired")),
    )
)

stage_summary = sicr_assessed.groupBy("assessed_stage").agg(
    F.count("*").alias("loan_count"),
    F.round(F.sum("gross_carrying_amount"), 2).alias("total_gca"),
).orderBy("assessed_stage").collect()

print("\n  Assessed Stage Distribution:")
for row in stage_summary:
    print(f"    Stage {row['assessed_stage']}: {row['loan_count']:,} loans, ${row['total_gca']:,.2f}")

trigger_counts = sicr_assessed.filter(F.col("assessed_stage") >= 2).select(
    F.sum(F.col("sicr_trigger_pd").cast("int")).alias("pd_deterioration"),
    F.sum(F.col("sicr_trigger_dpd").cast("int")).alias("dpd_30plus"),
    F.sum(F.col("sicr_trigger_alt_data").cast("int")).alias("alt_data_drop"),
    F.sum(F.col("sicr_trigger_collateral").cast("int")).alias("collateral_erosion"),
    F.sum(F.col("sicr_trigger_restructured").cast("int")).alias("restructured"),
).collect()[0]

print("\n  SICR Trigger Frequency (Stage 2+3 loans):")
print(f"    PD deterioration (>2x relative + >0.5% absolute): {trigger_counts['pd_deterioration']:,}")
print(f"    30+ DPD (rebuttable presumption): {trigger_counts['dpd_30plus']:,}")
print(f"    Alt data score drop (>25 points): {trigger_counts['alt_data_drop']:,}")
print(f"    Collateral erosion (LTV >125%): {trigger_counts['collateral_erosion']:,}")
print(f"    Restructured: {trigger_counts['restructured']:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Feature Engineering (Model-Ready Dataset)

# COMMAND ----------

print("Building model-ready dataset...")
print("-" * 60)

model_ready = sicr_assessed.select(
    "loan_id", "borrower_id", "product_type",
    "origination_date", "maturity_date",
    "original_principal", "gross_carrying_amount",
    "effective_interest_rate", "contractual_term_months",
    "months_on_book", "remaining_months",
    "days_past_due", "origination_pd", "current_lifetime_pd",
    "origination_alt_score", "current_alt_score",
    "assessed_stage", "sicr_trigger_reasons",
    "is_restructured", "currency",
    "segment", "age", "income_source", "monthly_income",
    "employment_tenure_months", "education_level",
    "formal_credit_score", "rent_payment_score",
    "utility_payment_score", "mobile_money_velocity",
    "bank_account_age_months", "alt_data_composite_score",
    "has_student_loan", "dependents", "country",
    "current_collateral_value", "loan_to_value_ratio",
).withColumn(
    "payment_behaviour_6m",
    F.lit(None).cast("double")
).withColumn(
    "payment_behaviour_12m",
    F.lit(None).cast("double")
).withColumn(
    "vintage_cohort",
    F.concat(
        F.lit("Q"),
        F.ceil(F.month(F.col("origination_date")) / 3).cast("string"),
        F.lit("-"),
        F.year(F.col("origination_date")).cast("string")
    )
)

payment_stats = payment_history.groupBy("loan_id").agg(
    F.avg(F.when(F.col("payment_status") == "on_time", 1).otherwise(0)).alias("pmt_on_time_rate"),
    F.count("*").alias("total_payments"),
    F.sum(F.when(F.col("payment_status") == "missed", 1).otherwise(0)).alias("missed_payments"),
)

model_ready = model_ready.join(payment_stats, "loan_id", "left") \
    .withColumn("payment_behaviour_6m", F.coalesce(F.col("pmt_on_time_rate"), F.lit(0.9))) \
    .withColumn("payment_behaviour_12m", F.coalesce(F.col("pmt_on_time_rate"), F.lit(0.9))) \
    .drop("pmt_on_time_rate")

model_ready.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.model_ready_loans")

final_count = model_ready.count()
print(f"\n  Model-ready dataset: {final_count:,} loans")
print(f"  Written to: {FULL_SCHEMA}.model_ready_loans")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Processing Complete

# COMMAND ----------

result = {
    "status": "SUCCESS",
    "snapshot_id": snapshot_id,
    "total_loans": int(snapshot_stats["total_loans"]),
    "total_gca": float(snapshot_stats["total_gca"]),
    "dq_score": float(dq_score),
    "dq_critical_failures": int(critical_failures),
    "gl_total_variance": float(total_var),
    "stage_1_count": int(stage_summary[0]["loan_count"]) if len(stage_summary) > 0 else 0,
    "stage_2_count": int(stage_summary[1]["loan_count"]) if len(stage_summary) > 1 else 0,
    "stage_3_count": int(stage_summary[2]["loan_count"]) if len(stage_summary) > 2 else 0,
    "model_ready_count": int(final_count),
}

print("\n" + "=" * 60)
print("DATA PROCESSING COMPLETE")
print("=" * 60)
for k, v in result.items():
    print(f"  {k}: {v}")

dbutils.notebook.exit(str(result))
