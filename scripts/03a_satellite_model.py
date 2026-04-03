"""
IFRS 9 Satellite Model Selection — Orchestrator
=================================================
Runs configurable regression models per product × cohort on historical quarterly
default rates, evaluates fit metrics, and selects the best model for each combination.

All models include automatic hyperparameter tuning:
  1. Linear Regression (OLS)
  2. Logistic Regression (logit-space OLS)
  3. Polynomial Regression (degree 2)
  4. Ridge Regression — RidgeCV auto-selects α from [0.001..100]
  5. Random Forest — GridSearchCV over n_estimators, max_depth, min_samples_leaf
  6. Elastic Net — ElasticNetCV auto-selects α and L1 ratio
  7. Gradient Boosting — GridSearchCV over n_estimators, depth, lr, subsample
  8. XGBoost — GridSearchCV over n_estimators, depth, lr, subsample, colsample

Selection criteria: lowest AIC (parametric models) or cross-validated RMSE (tree-based).
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
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

# ── Model Configuration ──────────────────────────────────────────────────────
ALL_MODELS = [
    "linear_regression", "logistic_regression", "polynomial_deg2",
    "ridge_regression", "random_forest", "elastic_net",
    "gradient_boosting", "xgboost",
]

# Accept enabled_models as a job parameter (comma-separated) or default to all
try:
    _param = dbutils.widgets.get("enabled_models")  # type: ignore[name-defined]
    _requested = [m.strip() for m in _param.split(",") if m.strip()]
    ENABLED_MODELS = {m: (m in _requested) for m in ALL_MODELS}
except Exception:
    ENABLED_MODELS = {m: True for m in ALL_MODELS}

# ── Load model modules from scripts/models/ ─────────────────────────────────
# Databricks notebooks don't have __file__; use the workspace filesystem path
try:
    _WORKSPACE_PREFIX = dbutils.widgets.get("workspace_scripts_path")  # type: ignore[name-defined]
except Exception:
    _WORKSPACE_PREFIX = "/Workspace/Users/steven.tan@databricks.com/ifrs9-ecl-demo/scripts"
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = _WORKSPACE_PREFIX
MODELS_DIR = os.path.join(_script_dir, "models")

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


def load_model_module(model_key):
    """Dynamically load a model module from the models/ directory."""
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


MACRO_FEATURES = ["unemployment_rate", "gdp_growth_rate", "inflation_rate"]
TARGET = "observed_default_rate"

print("=" * 70)
print("IFRS 9 ECL — Satellite Model Selection (Orchestrator)")
print("=" * 70)

enabled = [k for k, v in ENABLED_MODELS.items() if v]
print(f"Enabled models ({len(enabled)}): {', '.join(enabled)}")

# Load model modules
model_modules = {}
for model_key in enabled:
    try:
        model_modules[model_key] = load_model_module(model_key)
        print(f"  ✓ Loaded {model_key}")
    except Exception as e:
        print(f"  ✗ Failed to load {model_key}: {e}")

qdr = spark.table(f"{FULL_SCHEMA}.quarterly_default_rates").toPandas()
print(f"\nLoaded {len(qdr):,} quarterly default rate observations")
print(f"  Products: {sorted(qdr['product_type'].unique())}")
print(f"  Cohorts: {qdr['cohort_id'].nunique()} unique (incl. __ALL__)")

comparison_rows = []
selected_rows = []
run_ts = datetime.now().isoformat()

products = sorted(qdr["product_type"].unique())

for product in products:
    product_data = qdr[qdr["product_type"] == product]
    product_cohorts = sorted(product_data["cohort_id"].unique())
    print(f"\n{'─' * 60}")
    print(f"Product: {product} ({len(product_cohorts)} cohorts)")

    for cohort in product_cohorts:
        subset = product_data[product_data["cohort_id"] == cohort]
        if len(subset) < 5:
            print(f"  Skipping {cohort}: only {len(subset)} observations")
            continue

        X = subset[MACRO_FEATURES].values
        y = subset[TARGET].values

        best_result = None
        best_score = float("inf")

        for model_key, mod in model_modules.items():
            try:
                result = mod.fit(X, y)
            except Exception as e:
                print(f"  WARN: {model_key} failed for {product}/{cohort}: {e}")
                continue

            score = result.get("aic") if result.get("aic") is not None else result.get("cv_rmse", float("inf"))

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

            if score < best_score:
                best_score = score
                best_result = result

        if best_result:
            selection_reason = (
                f"Lowest AIC ({best_result.get('aic', 'N/A')})"
                if best_result.get("aic") is not None
                else f"Lowest CV-RMSE ({best_result.get('cv_rmse', 'N/A')})"
            )
            selected_rows.append({
                "product_type": product,
                "cohort_id": cohort,
                "model_type": best_result["model_type"],
                "r_squared": best_result["r_squared"],
                "rmse": best_result["rmse"],
                "aic": best_result.get("aic"),
                "bic": best_result.get("bic"),
                "coefficients_json": json.dumps(best_result["coefficients"]),
                "best_params_json": json.dumps(best_result.get("best_params", {})),
                "formula": best_result["formula"],
                "selection_reason": selection_reason,
                "n_observations": len(subset),
                "run_timestamp": run_ts,
            })
            print(f"  {cohort}: BEST = {best_result['model_type']} (R²={best_result['r_squared']:.4f}, RMSE={best_result['rmse']:.6f})")

print(f"\n{'=' * 70}")
print("Saving satellite model results...")

comparison_pdf = pd.DataFrame(comparison_rows)
selected_pdf = pd.DataFrame(selected_rows)

print(f"  satellite_model_comparison: {len(comparison_pdf):,} rows ({len(model_modules)} models × {len(selected_pdf)} cohorts)")
print(f"  satellite_model_selected: {len(selected_pdf):,} rows")

spark.createDataFrame(comparison_pdf).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.satellite_model_comparison")

spark.createDataFrame(selected_pdf).write.mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{FULL_SCHEMA}.satellite_model_selected")

print("\nModel selection summary:")
print(selected_pdf.groupby("model_type").size().to_string())

print(f"\n✅ Satellite model selection complete! ({len(model_modules)} models evaluated)")
