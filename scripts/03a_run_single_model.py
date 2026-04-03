"""
IFRS 9 Satellite Model — Single Model Runner
==============================================
Runs ONE satellite model across all product × cohort combinations.
Designed to be called as a parallel task in a Databricks Job DAG.

Parameters:
  - model_name: which model to run (e.g. "random_forest", "ridge_regression")
  - catalog, schema: Unity Catalog location
"""

import numpy as np
import pandas as pd
import json
import os
import importlib.util
from datetime import datetime
from pyspark.sql import SparkSession

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
    MODEL_NAME = dbutils.widgets.get("model_name")  # type: ignore[name-defined]
except Exception:
    MODEL_NAME = "linear_regression"

try:
    _enabled_csv = dbutils.widgets.get("enabled_models")  # type: ignore[name-defined]
    ENABLED_MODELS = [m.strip() for m in _enabled_csv.split(",") if m.strip()]
except Exception:
    ENABLED_MODELS = []

if ENABLED_MODELS and MODEL_NAME not in ENABLED_MODELS:
    print(f"⏭️  {MODEL_NAME} is not in enabled_models ({ENABLED_MODELS}). Skipping.")
    try:
        dbutils.notebook.exit(f"SKIPPED: {MODEL_NAME} not enabled")  # type: ignore[name-defined]
    except Exception:
        import sys
        sys.exit(0)

FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

MODEL_FILES = {
    "linear_regression": "linear_regression.py",
    "logistic_regression": "logistic_regression.py",
    "polynomial_deg2": "polynomial_regression.py",
    "ridge_regression": "ridge_regression.py",
    "random_forest": "random_forest.py",
    "elastic_net": "elastic_net.py",
    "gradient_boosting": "gradient_boosting.py",
    "xgboost": "xgboost_model.py",
}

try:
    _WORKSPACE_PREFIX = dbutils.widgets.get("workspace_scripts_path")  # type: ignore[name-defined]
except Exception:
    _WORKSPACE_PREFIX = "/Workspace/Users/steven.tan@databricks.com/ifrs9-ecl-demo/scripts"
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = _WORKSPACE_PREFIX
MODELS_DIR = os.path.join(_script_dir, "models")

MACRO_FEATURES = ["unemployment_rate", "gdp_growth_rate", "inflation_rate"]
TARGET = "observed_default_rate"


def load_model_module(model_key):
    filename = MODEL_FILES.get(model_key)
    if not filename:
        raise ValueError(f"Unknown model: {model_key}")
    filepath = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    spec = importlib.util.spec_from_file_location(f"model_{model_key}", filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


print("=" * 70)
print(f"IFRS 9 ECL — Satellite Model Runner: {MODEL_NAME}")
print("=" * 70)

mod = load_model_module(MODEL_NAME)
print(f"  ✓ Loaded model module: {MODEL_NAME}")

qdr = spark.table(f"{FULL_SCHEMA}.quarterly_default_rates").toPandas()
print(f"Loaded {len(qdr):,} quarterly default rate observations")

comparison_rows = []
run_ts = datetime.now().isoformat()
products = sorted(qdr["product_type"].unique())

for product in products:
    product_data = qdr[qdr["product_type"] == product]
    product_cohorts = sorted(product_data["cohort_id"].unique())
    print(f"\n  Product: {product} ({len(product_cohorts)} cohorts)")

    for cohort in product_cohorts:
        subset = product_data[product_data["cohort_id"] == cohort]
        if len(subset) < 5:
            continue

        X = subset[MACRO_FEATURES].values
        y = subset[TARGET].values

        try:
            result = mod.fit(X, y)
        except Exception as e:
            print(f"    WARN: {MODEL_NAME} failed for {product}/{cohort}: {e}")
            continue

        comparison_rows.append({
            "product_type": product,
            "cohort_id": cohort,
            "model_type": result["model_type"],
            "r_squared": result["r_squared"],
            "rmse": result["rmse"],
            "aic": result.get("aic"),
            "bic": result.get("bic"),
            "cv_rmse": result.get("cv_rmse"),
            "coefficients_json": json.dumps(result["coefficients"]),
            "best_params_json": json.dumps(result.get("best_params", {})),
            "formula": result["formula"],
            "n_observations": len(subset),
            "run_timestamp": run_ts,
        })
        print(f"    {cohort}: R²={result['r_squared']:.4f}, RMSE={result['rmse']:.6f}")

if comparison_rows:
    comparison_pdf = pd.DataFrame(comparison_rows)
    output_table = f"{FULL_SCHEMA}.satellite_model_results_{MODEL_NAME}"
    spark.createDataFrame(comparison_pdf).write.mode("overwrite").option("overwriteSchema", "true") \
        .saveAsTable(output_table)
    print(f"\n✅ {MODEL_NAME}: {len(comparison_rows)} results saved to {output_table}")
else:
    print(f"\n⚠️ {MODEL_NAME}: No results produced")
