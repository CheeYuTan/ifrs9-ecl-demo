"""
IFRS 9 Data Processing Pipeline
================================
Performs data quality checks, GL reconciliation, SICR assessment,
and produces model-ready dataset for the ECL calculation engine.
"""
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql import SparkSession
from datetime import datetime
import pandas as pd

spark = SparkSession.builder.getOrCreate()

PROJECT_ID = "Q4-2025-IFRS9"
REPORTING_DATE = "2025-12-31"
PORTFOLIO_FILTER = "all"
CATALOG = "lakemeter_catalog"
SCHEMA = "expected_credit_loss"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

# Product-specific SICR thresholds — calibrated from back-testing
SICR_THRESHOLDS = {
    "credit_builder":      {"pd_relative": 2.5, "pd_absolute": 0.008, "alt_drop": 20, "ltv_max": 1.20},
    "emergency_microloan": {"pd_relative": 2.0, "pd_absolute": 0.010, "alt_drop": 18, "ltv_max": None},
    "career_transition":   {"pd_relative": 2.2, "pd_absolute": 0.008, "alt_drop": 22, "ltv_max": None},
    "bnpl_professional":   {"pd_relative": 2.0, "pd_absolute": 0.006, "alt_drop": 20, "ltv_max": None},
    "payroll_advance":     {"pd_relative": 1.8, "pd_absolute": 0.012, "alt_drop": 15, "ltv_max": None},
}
DEFAULT_SICR = {"pd_relative": 2.0, "pd_absolute": 0.008, "alt_drop": 20, "ltv_max": None}

print("=" * 70)
print("IFRS 9 ECL — Data Processing Pipeline")
print("=" * 70)

loan_tape = spark.table(f"{FULL_SCHEMA}.loan_tape")
borrower_master = spark.table(f"{FULL_SCHEMA}.borrower_master")
payment_history = spark.table(f"{FULL_SCHEMA}.payment_history")
general_ledger = spark.table(f"{FULL_SCHEMA}.general_ledger")
collateral_register = spark.table(f"{FULL_SCHEMA}.collateral_register")

snapshot_stats = loan_tape.agg(
    F.count("*").alias("total_loans"),
    F.sum("gross_carrying_amount").alias("total_gca"),
    F.countDistinct("borrower_id").alias("unique_borrowers"),
).collect()[0]

snapshot_id = f"{PROJECT_ID}_{REPORTING_DATE}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
print(f"Snapshot: {snapshot_stats['total_loans']:,} loans, ${snapshot_stats['total_gca']:,.2f} GCA")

# Exclude written-off loans from ECL calculation (they are already recognized as losses)
active_loans = loan_tape.filter(F.col("is_write_off") == False)
writeoff_count = loan_tape.filter(F.col("is_write_off") == True).count()
print(f"  Active loans: {active_loans.count():,} (excluded {writeoff_count:,} write-offs)")

# ── Data Quality Checks ──────────────────────────────────────────────────────
print("\n[DQ CHECKS]")
dq_results = []

def run_dq(check_id, cat, desc, sev, expr, threshold=0):
    result = active_loans.filter(expr).count()
    total = active_loans.count()
    pct = round(result / total * 100, 2) if total > 0 else 0
    passed = result <= threshold
    dq_results.append({"check_id": check_id, "category": cat, "description": desc,
                        "severity": sev, "failures": result, "total_records": total,
                        "failure_pct": pct, "threshold": threshold, "passed": passed,
                        "snapshot_id": snapshot_id, "reporting_date": REPORTING_DATE})
    print(f"  {'PASS' if passed else 'FAIL'} [{sev}] {desc}: {result}")

# Completeness checks
run_dq("C01", "completeness", "Missing GCA", "critical", F.col("gross_carrying_amount").isNull())
run_dq("C02", "completeness", "Missing EIR", "critical", F.col("effective_interest_rate").isNull())
run_dq("C03", "completeness", "Missing origination_date", "critical", F.col("origination_date").isNull())
run_dq("C04", "completeness", "Missing product_type", "critical", F.col("product_type").isNull())
run_dq("C05", "completeness", "Missing borrower_id", "critical", F.col("borrower_id").isNull())
run_dq("C06", "completeness", "Missing origination_pd", "critical", F.col("origination_pd").isNull())

# Validity checks
run_dq("V01", "validity", "EIR out of range (0-36%)", "critical",
       (F.col("effective_interest_rate") < 0) | (F.col("effective_interest_rate") > 0.36))
run_dq("V02", "validity", "Negative GCA", "critical", F.col("gross_carrying_amount") <= 0)
run_dq("V03", "validity", "Negative DPD", "critical", F.col("days_past_due") < 0)
run_dq("V04", "validity", "Origination after reporting date", "critical",
       F.col("origination_date") > F.lit(REPORTING_DATE))
run_dq("V05", "validity", "Invalid stage (not 1/2/3)", "critical",
       ~F.col("current_stage").isin(1, 2, 3))
run_dq("V06", "validity", "Maturity before origination", "critical",
       F.col("maturity_date") < F.col("origination_date"))

# Cross-field consistency checks
run_dq("X01", "consistency", "DPD>0 but current_pd <= origination_pd", "high",
       (F.col("days_past_due") > 30) & (F.col("current_lifetime_pd") <= F.col("origination_pd")))
run_dq("X02", "consistency", "Stage 3 but DPD < 90", "high",
       (F.col("current_stage") == 3) & (F.col("days_past_due") < 90))
run_dq("X03", "consistency", "Stage 1 but DPD >= 30 (backstop violation)", "high",
       (F.col("current_stage") == 1) & (F.col("days_past_due") >= 30))
run_dq("X04", "consistency", "GCA exceeds original principal by >10%", "medium",
       F.col("gross_carrying_amount") > F.col("original_principal") * 1.10)
run_dq("X05", "consistency", "Remaining months exceeds contractual term", "medium",
       F.col("remaining_months") > F.col("contractual_term_months"))

# IFRS 9 specific checks
run_dq("I01", "ifrs9", "Missing origination PD for SICR assessment", "critical",
       F.col("origination_pd").isNull())
run_dq("I02", "ifrs9", "Missing EIR for ECL discounting", "critical",
       F.col("effective_interest_rate").isNull())
run_dq("I03", "ifrs9", "PD exceeds 80% (likely should be written off)", "high",
       F.col("current_lifetime_pd") > 0.80)

dq_pdf = pd.DataFrame(dq_results)
dq_score = round(dq_pdf["passed"].sum() / len(dq_pdf) * 100, 1)
print(f"\nDQ Score: {dq_score}% ({dq_pdf['passed'].sum()}/{len(dq_pdf)} checks passed)")

spark.createDataFrame(dq_pdf).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.dq_results")

# ── GL Reconciliation ─────────────────────────────────────────────────────────
print("\n[GL RECONCILIATION]")
loan_tape_by_product = active_loans.groupBy("product_type") \
    .agg(F.round(F.sum("gross_carrying_amount"), 2).alias("loan_tape_balance"))
lt_rows = {r["product_type"]: r["loan_tape_balance"] for r in loan_tape_by_product.collect()}

gl_rows = general_ledger.filter(F.col("account_type") == "asset") \
    .filter(F.col("account_name").startswith("Loans Receivable")).collect()

recon_results = []
for gl_row in gl_rows:
    product_key = gl_row["account_name"].replace("Loans Receivable - ", "").lower().replace(" ", "_")
    lt_bal = lt_rows.get(product_key, 0)
    var = round(gl_row["gl_balance"] - lt_bal, 2)
    var_pct = round(abs(var) / lt_bal * 100, 4) if lt_bal > 0 else 0
    tolerance = 0.50 if lt_bal > 10_000_000 else 1.00
    status = "PASS" if var_pct <= tolerance else "FAIL"
    recon_results.append({
        "product_type": product_key, "gl_balance": gl_row["gl_balance"],
        "loan_tape_balance": lt_bal, "variance": var, "variance_pct": var_pct,
        "tolerance_pct": tolerance, "status": status,
        "snapshot_id": snapshot_id, "reporting_date": REPORTING_DATE,
    })
    print(f"  {status} {product_key}: var=${var:,.2f} ({var_pct:.4f}%, tol={tolerance}%)")

spark.createDataFrame(pd.DataFrame(recon_results)).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.gl_reconciliation")

# ── SICR Assessment (Product-Specific Thresholds) ────────────────────────────
print("\n[SICR ASSESSMENT — Product-Specific Thresholds]")
enriched = active_loans.join(borrower_master, "borrower_id", "left") \
    .join(collateral_register.select("loan_id", "current_collateral_value", "loan_to_value_ratio"), "loan_id", "left")

# Build product-specific threshold columns
sicr_threshold_data = []
for product, thresh in SICR_THRESHOLDS.items():
    sicr_threshold_data.append((product, thresh["pd_relative"], thresh["pd_absolute"],
                                thresh["alt_drop"], thresh.get("ltv_max")))
sicr_thresh_df = spark.createDataFrame(sicr_threshold_data,
    ["_product", "_pd_rel_thresh", "_pd_abs_thresh", "_alt_drop_thresh", "_ltv_thresh"])

enriched = enriched.join(sicr_thresh_df, enriched["product_type"] == sicr_thresh_df["_product"], "left") \
    .fillna({"_pd_rel_thresh": 2.0, "_pd_abs_thresh": 0.008, "_alt_drop_thresh": 20})

sicr = enriched.withColumn("sicr_pd_relative",
    F.when(F.col("origination_pd") > 0, F.col("current_lifetime_pd") / F.col("origination_pd")).otherwise(1.0)
).withColumn("sicr_pd_absolute", F.col("current_lifetime_pd") - F.col("origination_pd")
).withColumn("sicr_alt_drop", F.col("origination_alt_score") - F.col("current_alt_score")
).withColumn("sicr_trigger_pd",
    (F.col("sicr_pd_relative") > F.col("_pd_rel_thresh")) & (F.col("sicr_pd_absolute") > F.col("_pd_abs_thresh"))
).withColumn("sicr_trigger_dpd", F.col("days_past_due") >= 30
).withColumn("sicr_trigger_alt", F.col("sicr_alt_drop") > F.col("_alt_drop_thresh")
).withColumn("sicr_trigger_collateral",
    F.col("_ltv_thresh").isNotNull() & (F.col("loan_to_value_ratio") > F.col("_ltv_thresh"))
).withColumn("sicr_trigger_restructured", F.col("is_restructured") == True
).withColumn("impairment_dpd90", F.col("days_past_due") >= 90
).withColumn("assessed_stage",
    F.when(F.col("impairment_dpd90"), 3)
     .when(F.col("sicr_trigger_pd") | F.col("sicr_trigger_dpd") | F.col("sicr_trigger_alt") |
           F.col("sicr_trigger_collateral") | F.col("sicr_trigger_restructured"), 2)
     .otherwise(1)
).withColumn("sicr_trigger_reasons",
    F.concat_ws(", ",
        F.when(F.col("sicr_trigger_pd"), F.lit("PD_deterioration")),
        F.when(F.col("sicr_trigger_dpd"), F.lit("30+DPD_backstop")),
        F.when(F.col("sicr_trigger_alt"), F.lit("alt_data_deterioration")),
        F.when(F.col("sicr_trigger_collateral"), F.lit("collateral_erosion")),
        F.when(F.col("sicr_trigger_restructured"), F.lit("forbearance_restructured")),
        F.when(F.col("impairment_dpd90"), F.lit("90+DPD_credit_impaired")),
    )
)

stage_dist = sicr.groupBy("assessed_stage").agg(
    F.count("*").alias("cnt"), F.round(F.sum("gross_carrying_amount"), 2).alias("gca")
).orderBy("assessed_stage").collect()
for r in stage_dist:
    print(f"  Stage {r['assessed_stage']}: {r['cnt']:,} loans, ${r['gca']:,.2f}")

# ── Payment Behavior Statistics ───────────────────────────────────────────────
print("\n[PAYMENT BEHAVIOR ANALYSIS]")
payment_stats = payment_history.groupBy("loan_id").agg(
    F.avg(F.when(F.col("payment_status") == "on_time", 1).otherwise(0)).alias("pmt_on_time_rate"),
    F.count("*").alias("total_payments"),
    F.sum(F.when(F.col("payment_status") == "missed", 1).otherwise(0)).alias("missed_payments"),
    F.sum(F.when(F.col("payment_status") == "partial", 1).otherwise(0)).alias("partial_payments"),
    F.max(F.when(F.col("payment_status") == "on_time", F.col("payment_date"))).alias("last_on_time_date"),
)

# ── Model-Ready Dataset ──────────────────────────────────────────────────────
print("\n[MODEL-READY DATASET]")

# Include prior_stage if available in the loan tape
select_cols = [
    "loan_id", "borrower_id", "product_type", "origination_date", "maturity_date",
    "original_principal", "gross_carrying_amount", "effective_interest_rate",
    "contractual_term_months", "months_on_book", "remaining_months",
    "days_past_due", "origination_pd", "current_lifetime_pd",
    "origination_alt_score", "current_alt_score", "assessed_stage",
    "sicr_trigger_reasons", "is_restructured", "currency",
    "segment", "age", "income_source", "monthly_income",
    "employment_tenure_months", "education_level", "formal_credit_score",
    "rent_payment_score", "utility_payment_score", "mobile_money_velocity",
    "bank_account_age_months", "alt_data_composite_score",
    "has_student_loan", "dependents", "country",
    "current_collateral_value", "loan_to_value_ratio",
]

if "prior_stage" in [f.name for f in sicr.schema.fields]:
    select_cols.append("prior_stage")
if "consecutive_on_time_payments" in [f.name for f in sicr.schema.fields]:
    select_cols.append("consecutive_on_time_payments")

available_cols = [c for c in select_cols if c in [f.name for f in sicr.schema.fields]]
model_ready = sicr.select(*available_cols)

model_ready = model_ready.withColumn("vintage_cohort",
    F.concat(F.lit("Q"), F.ceil(F.month(F.col("origination_date")) / 3).cast("string"),
             F.lit("-"), F.year(F.col("origination_date")).cast("string"))
)

model_ready = model_ready.join(payment_stats, "loan_id", "left")

model_ready.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.model_ready_loans")

cnt = model_ready.count()
print(f"  Written {cnt:,} rows to {FULL_SCHEMA}.model_ready_loans")

# ── SICR Threshold Metadata (for audit/governance) ───────────────────────────
sicr_meta = []
for product, thresh in SICR_THRESHOLDS.items():
    sicr_meta.append({
        "product_type": product,
        "pd_relative_threshold": thresh["pd_relative"],
        "pd_absolute_threshold": thresh["pd_absolute"],
        "alt_score_drop_threshold": thresh["alt_drop"],
        "ltv_threshold": thresh.get("ltv_max"),
        "dpd_backstop_stage2": 30,
        "dpd_backstop_stage3": 90,
        "cure_period_months": 3,
        "calibration_date": "2025-09-30",
        "reporting_date": REPORTING_DATE,
    })
spark.createDataFrame(pd.DataFrame(sicr_meta)).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.sicr_thresholds")

print("\nData processing complete!")
