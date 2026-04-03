"""
IFRS 9 Data Processing Pipeline
================================
Performs data quality checks, GL reconciliation, SICR assessment,
and produces model-ready dataset for the ECL calculation engine.

Supports: Credit Card, Residential Mortgage, Commercial Loan,
Personal Loan, Auto Loan.
"""
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql import SparkSession
from datetime import datetime
import pandas as pd

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
PORTFOLIO_FILTER = "all"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

DEFAULT_SICR = {"pd_relative": 2.0, "pd_absolute": 0.008, "dpd_stage2": 30, "dpd_stage3": 90}

try:
    import json as _json
    _sicr_json = dbutils.widgets.get("sicr_thresholds")  # type: ignore[name-defined]
    SICR_THRESHOLDS = _json.loads(_sicr_json)
except Exception:
    SICR_THRESHOLDS = {}

_discovered_products = spark.table(f"{FULL_SCHEMA}.loan_tape").select("product_type").distinct().collect()
for _row in _discovered_products:
    _p = _row["product_type"]
    if _p not in SICR_THRESHOLDS:
        SICR_THRESHOLDS[_p] = dict(DEFAULT_SICR)

print("=" * 70)
print("IFRS 9 ECL — Data Processing Pipeline")
print(f"Products: {', '.join(SICR_THRESHOLDS.keys())}")
print("=" * 70)

loan_tape = spark.table(f"{FULL_SCHEMA}.loan_tape")
borrower_master = spark.table(f"{FULL_SCHEMA}.borrower_master")
payment_history = spark.table(f"{FULL_SCHEMA}.payment_history")
general_ledger = spark.table(f"{FULL_SCHEMA}.general_ledger")
collateral_register = spark.table(f"{FULL_SCHEMA}.collateral_register")

loan_tape_cols = set(loan_tape.columns)
borrower_cols = set(borrower_master.columns)

snapshot_stats = loan_tape.agg(
    F.count("*").alias("total_loans"),
    F.sum("gross_carrying_amount").alias("total_gca"),
    F.countDistinct("borrower_id").alias("unique_borrowers"),
).collect()[0]

snapshot_id = f"{PROJECT_ID}_{REPORTING_DATE}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
print(f"Snapshot: {snapshot_stats['total_loans']:,} loans, ${snapshot_stats['total_gca']:,.2f} GCA")

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

run_dq("C01", "completeness", "Missing GCA", "critical", F.col("gross_carrying_amount").isNull())
run_dq("C02", "completeness", "Missing EIR", "critical", F.col("effective_interest_rate").isNull())
run_dq("C03", "completeness", "Missing origination_date", "critical", F.col("origination_date").isNull())
run_dq("C04", "completeness", "Missing product_type", "critical", F.col("product_type").isNull())
run_dq("C05", "completeness", "Missing borrower_id", "critical", F.col("borrower_id").isNull())
run_dq("C06", "completeness", "Missing origination_pd", "critical", F.col("origination_pd").isNull())

run_dq("V01", "validity", "EIR out of range (0-30%)", "critical",
       (F.col("effective_interest_rate") < 0) | (F.col("effective_interest_rate") > 0.30))
run_dq("V02", "validity", "Negative GCA", "critical", F.col("gross_carrying_amount") <= 0)
run_dq("V03", "validity", "Negative DPD", "critical", F.col("days_past_due") < 0)
run_dq("V04", "validity", "Origination after reporting date", "critical",
       F.col("origination_date") > F.lit(REPORTING_DATE))
run_dq("V05", "validity", "Invalid stage (not 1/2/3)", "critical",
       ~F.col("current_stage").isin(1, 2, 3))

if "maturity_date" in loan_tape_cols:
    run_dq("V06", "validity", "Maturity before origination", "critical",
           F.col("maturity_date").isNotNull() & (F.col("maturity_date") < F.col("origination_date")))

run_dq("X01", "consistency", "DPD>30 but current_pd <= origination_pd", "high",
       (F.col("days_past_due") > 30) & (F.col("current_lifetime_pd") <= F.col("origination_pd")))
run_dq("X02", "consistency", "Stage 3 but DPD < 90", "high",
       (F.col("current_stage") == 3) & (F.col("days_past_due") < 90))
run_dq("X03", "consistency", "Stage 1 but DPD >= 30 (backstop violation)", "high",
       (F.col("current_stage") == 1) & (F.col("days_past_due") >= 30))

if "credit_grade" in loan_tape_cols:
    run_dq("X04", "consistency", "Missing credit grade", "medium",
           F.col("credit_grade").isNull())

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

# ── SICR Assessment ───────────────────────────────────────────────────────────
print("\n[SICR ASSESSMENT]")

borrower_cols_to_drop = [c for c in borrower_master.columns if c in active_loans.columns and c != "borrower_id"]
borrower_for_join = borrower_master.drop(*borrower_cols_to_drop)
enriched = active_loans.join(borrower_for_join, "borrower_id", "left") \
    .join(collateral_register.select("loan_id", "current_collateral_value", "loan_to_value_ratio"), "loan_id", "left")

from pyspark.sql.types import StructType, StructField, StringType, DoubleType

sicr_threshold_data = []
for product, thresh in SICR_THRESHOLDS.items():
    sicr_threshold_data.append((
        product,
        float(thresh.get("pd_relative", 2.0)),
        float(thresh.get("pd_absolute", 0.008)),
    ))
sicr_schema = StructType([
    StructField("_product", StringType(), False),
    StructField("_pd_rel_thresh", DoubleType(), False),
    StructField("_pd_abs_thresh", DoubleType(), False),
])
sicr_thresh_df = spark.createDataFrame(sicr_threshold_data, schema=sicr_schema)

enriched = enriched.join(sicr_thresh_df, enriched["product_type"] == sicr_thresh_df["_product"], "left") \
    .fillna({"_pd_rel_thresh": 2.0, "_pd_abs_thresh": 0.008})

sicr = enriched.withColumn("sicr_pd_relative",
    F.when(F.col("origination_pd") > 0, F.col("current_lifetime_pd") / F.col("origination_pd")).otherwise(1.0)
).withColumn("sicr_pd_absolute", F.col("current_lifetime_pd") - F.col("origination_pd")
).withColumn("sicr_trigger_pd",
    (F.col("sicr_pd_relative") > F.col("_pd_rel_thresh")) & (F.col("sicr_pd_absolute") > F.col("_pd_abs_thresh"))
).withColumn("sicr_trigger_dpd", F.col("days_past_due") >= 30
).withColumn("sicr_trigger_restructured", F.col("is_restructured") == True
).withColumn("impairment_dpd90", F.col("days_past_due") >= 90
).withColumn("assessed_stage",
    F.when(F.col("impairment_dpd90"), 3)
     .when(F.col("sicr_trigger_pd") | F.col("sicr_trigger_dpd") | F.col("sicr_trigger_restructured"), 2)
     .otherwise(1)
).withColumn("sicr_trigger_reasons",
    F.concat_ws(", ",
        F.when(F.col("sicr_trigger_pd"), F.lit("PD_deterioration")),
        F.when(F.col("sicr_trigger_dpd"), F.lit("30+DPD_backstop")),
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

all_fields = set(f.name for f in sicr.schema.fields)

select_cols = [
    "loan_id", "borrower_id", "product_type",
    "origination_date", "maturity_date",
    "original_principal", "gross_carrying_amount", "effective_interest_rate",
    "contractual_term_months", "months_on_book", "remaining_months",
    "days_past_due", "delinquency_bucket", "origination_pd", "current_lifetime_pd",
    "assessed_stage", "prior_stage", "sicr_trigger_reasons", "is_restructured", "currency",
    "credit_grade", "risk_band", "vintage_year", "age_bucket", "employment_type", "region",
    "industry_sector", "ltv_ratio", "ltv_band",
    "credit_limit", "utilization_rate",
    "segment", "age", "annual_income", "credit_score", "education_level",
    "marital_status", "dependents", "employment_tenure_years", "existing_debt_ratio",
    "country",
    "current_collateral_value", "loan_to_value_ratio",
]

available_cols = [c for c in select_cols if c in all_fields]
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

# ── SICR Threshold Metadata ──────────────────────────────────────────────────
sicr_meta = []
for product, thresh in SICR_THRESHOLDS.items():
    sicr_meta.append({
        "product_type": product,
        "pd_relative_threshold": thresh.get("pd_relative", 2.0),
        "pd_absolute_threshold": thresh.get("pd_absolute", 0.008),
        "dpd_backstop_stage2": thresh.get("dpd_stage2", 30),
        "dpd_backstop_stage3": thresh.get("dpd_stage3", 90),
        "reporting_date": REPORTING_DATE,
    })
spark.createDataFrame(pd.DataFrame(sicr_meta)).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.sicr_thresholds")

print("\n✅ Data processing complete!")
