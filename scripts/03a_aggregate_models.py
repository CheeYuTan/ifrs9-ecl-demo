"""
IFRS 9 Satellite Model — Aggregator
=====================================
Reads per-model result tables written by parallel model runners,
merges them into satellite_model_comparison, and selects the best
model per product × cohort into satellite_model_selected.

Runs AFTER all parallel model tasks complete.
"""

import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType,
)

spark = SparkSession.builder.getOrCreate()

ALL_MODELS = [
    "linear_regression", "logistic_regression", "polynomial_deg2",
    "ridge_regression", "random_forest", "elastic_net",
    "gradient_boosting", "xgboost",
]

try:
    CATALOG = dbutils.widgets.get("catalog")  # type: ignore[name-defined]
except Exception:
    CATALOG = "lakemeter_catalog"
try:
    SCHEMA = dbutils.widgets.get("schema")  # type: ignore[name-defined]
except Exception:
    SCHEMA = "expected_credit_loss"

# Which models to aggregate — defaults to all 8 if not specified
try:
    _enabled_raw = dbutils.widgets.get("enabled_models")  # type: ignore[name-defined]
    ENABLED_MODELS = [m.strip() for m in _enabled_raw.split(",") if m.strip()] if _enabled_raw else ALL_MODELS
except Exception:
    ENABLED_MODELS = ALL_MODELS

FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

EXPECTED_COLS = [
    "product_type", "cohort_id", "model_type", "r_squared", "rmse",
    "aic", "bic", "cv_rmse", "coefficients_json", "best_params_json",
    "formula", "n_observations", "run_timestamp",
]

OUTPUT_SCHEMA = StructType([
    StructField("product_type", StringType()),
    StructField("cohort_id", StringType()),
    StructField("model_type", StringType()),
    StructField("r_squared", DoubleType()),
    StructField("rmse", DoubleType()),
    StructField("aic", DoubleType()),
    StructField("bic", DoubleType()),
    StructField("cv_rmse", DoubleType()),
    StructField("coefficients_json", StringType()),
    StructField("best_params_json", StringType()),
    StructField("formula", StringType()),
    StructField("n_observations", LongType()),
    StructField("run_timestamp", StringType()),
])

print("=" * 70)
print("IFRS 9 ECL — Satellite Model Aggregator")
print("=" * 70)

all_pdfs: list[pd.DataFrame] = []
for model_name in ENABLED_MODELS:
    table = f"{FULL_SCHEMA}.satellite_model_results_{model_name}"
    try:
        df = spark.table(table)
        count = df.count()
        if count > 0:
            pdf = df.toPandas()
            for col in EXPECTED_COLS:
                if col not in pdf.columns:
                    pdf[col] = None
            all_pdfs.append(pdf[EXPECTED_COLS])
            print(f"  ✓ {model_name}: {count:,} results")
        else:
            print(f"  ⚠ {model_name}: empty table")
    except Exception as e:
        print(f"  ✗ {model_name}: table not found ({e})")

if not all_pdfs:
    print("\n❌ No model results found! Ensure model tasks ran successfully.")
    raise RuntimeError("No model results to aggregate")

combined_pdf = pd.concat(all_pdfs, ignore_index=True)

for col in ["r_squared", "rmse", "aic", "bic", "cv_rmse"]:
    combined_pdf[col] = pd.to_numeric(combined_pdf[col], errors="coerce")
combined_pdf["n_observations"] = pd.to_numeric(combined_pdf["n_observations"], errors="coerce")
for col in ["product_type", "cohort_id", "model_type", "coefficients_json",
            "best_params_json", "formula", "run_timestamp"]:
    combined_pdf[col] = combined_pdf[col].astype(str).replace("None", None)

combined_pdf["n_observations"] = combined_pdf["n_observations"].apply(
    lambda x: int(x) if pd.notna(x) else None
)

total = len(combined_pdf)
print(f"\nCombined: {total:,} total results from {len(all_pdfs)} models")

combined_sdf = spark.createDataFrame(combined_pdf, schema=OUTPUT_SCHEMA)
combined_sdf.write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.satellite_model_comparison")
print(f"  ✓ Saved to {FULL_SCHEMA}.satellite_model_comparison")

selected_rows = []
for (product, cohort), group in combined_pdf.groupby(["product_type", "cohort_id"]):
    best_row = None
    best_score = float("inf")

    for _, row in group.iterrows():
        aic = row.get("aic")
        cv_rmse = row.get("cv_rmse")
        score = aic if pd.notna(aic) else (cv_rmse if pd.notna(cv_rmse) else float("inf"))
        if score < best_score:
            best_score = score
            best_row = row

    if best_row is not None:
        reason = (
            f"Lowest AIC ({best_row.get('aic', 'N/A')})"
            if pd.notna(best_row.get("aic"))
            else f"Lowest CV-RMSE ({best_row.get('cv_rmse', 'N/A')})"
        )
        selected_rows.append({
            "product_type": product,
            "cohort_id": cohort,
            "model_type": best_row["model_type"],
            "r_squared": best_row["r_squared"],
            "rmse": best_row["rmse"],
            "aic": best_row.get("aic"),
            "bic": best_row.get("bic"),
            "coefficients_json": best_row.get("coefficients_json"),
            "best_params_json": best_row.get("best_params_json"),
            "formula": best_row.get("formula"),
            "selection_reason": reason,
            "n_observations": best_row.get("n_observations"),
            "run_timestamp": best_row.get("run_timestamp"),
        })

selected_pdf = pd.DataFrame(selected_rows)
spark.createDataFrame(selected_pdf).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.satellite_model_selected")

print(f"\n  ✓ Saved {len(selected_pdf):,} best-model selections to {FULL_SCHEMA}.satellite_model_selected")
print("\nModel selection summary:")
print(selected_pdf.groupby("model_type").size().to_string())

for model_name in ENABLED_MODELS:
    table = f"{FULL_SCHEMA}.satellite_model_results_{model_name}"
    try:
        spark.sql(f"DROP TABLE IF EXISTS {table}")
        print(f"  Cleaned up {table}")
    except Exception as e:
        print(f"  ⚠ Could not clean up {table} (may need MANAGE permission): {e}")

print(f"\n✅ Aggregation complete!")
