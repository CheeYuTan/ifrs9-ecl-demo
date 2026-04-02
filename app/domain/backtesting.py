"""
IFRS 9 Backtesting Engine — Real Metrics from Actual Data.

Implements PD and LGD backtesting per EBA/GL/2017/16 and BCBS Principle 5:
  - Discrimination metrics: AUC, Gini (Accuracy Ratio), KS statistic
  - Calibration tests: Binomial, Hosmer-Lemeshow, Jeffreys, Spiegelhalter
  - Population stability: PSI
  - LGD backtesting: Predicted vs realised LGD from historical defaults
  - Traffic light system for both discrimination and calibration

Sub-modules:
  backtesting_traffic  — traffic light / zone classification
  backtesting_stats    — statistical tests and discrimination metrics
"""
import json as _json
import uuid
import logging
import pandas as pd
import numpy as _np
from datetime import datetime as _dt, timezone as _tz

from db.pool import query_df, execute, _t, SCHEMA

# ── Sub-module imports (re-exported for backward compatibility) ───────────────
from domain.backtesting_traffic import (  # noqa: F401
    METRIC_THRESHOLDS,
    _traffic_light,
    _overall_traffic_light,
)
from domain.backtesting_stats import (  # noqa: F401
    _compute_auc_gini_ks,
    _compute_psi,
    _compute_brier,
    _binomial_test,
    _jeffreys_test,
    _hosmer_lemeshow_test,
    _spiegelhalter_test,
)

log = logging.getLogger(__name__)


def _json_default(obj):
    """Handle numpy types when serializing to JSON."""
    if isinstance(obj, (_np.integer,)):
        return int(obj)
    if isinstance(obj, (_np.floating,)):
        return float(obj)
    if isinstance(obj, (_np.bool_,)):
        return bool(obj)
    if isinstance(obj, _np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


MIN_SAMPLE_SIZE = 30
MIN_DEFAULTS_FOR_LGD = 20
MIN_DEFAULTS_PER_GRADE = 5


def ensure_backtesting_table():
    try:
        test_df = query_df(f"SELECT model_type FROM {SCHEMA}.backtest_results LIMIT 1")
    except Exception:
        try:
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.backtest_cohort_results CASCADE")
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.backtest_metrics CASCADE")
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.backtest_results CASCADE")
            log.info("Dropped legacy backtest tables for schema migration")
        except Exception:
            pass
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.backtest_results (
            backtest_id TEXT PRIMARY KEY,
            model_id TEXT,
            model_type TEXT NOT NULL DEFAULT 'PD',
            backtest_date TIMESTAMP DEFAULT NOW(),
            observation_window TEXT,
            outcome_window TEXT,
            overall_traffic_light TEXT DEFAULT 'Green',
            pass_count INT DEFAULT 0,
            amber_count INT DEFAULT 0,
            fail_count INT DEFAULT 0,
            total_loans INT DEFAULT 0,
            config JSONB,
            created_by TEXT DEFAULT 'system'
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.backtest_metrics (
            metric_id TEXT PRIMARY KEY,
            backtest_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value FLOAT,
            threshold_green FLOAT,
            threshold_amber FLOAT,
            pass_fail TEXT DEFAULT 'Green',
            detail JSONB
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.backtest_cohort_results (
            cohort_id TEXT PRIMARY KEY,
            backtest_id TEXT NOT NULL,
            cohort_name TEXT NOT NULL,
            predicted_rate FLOAT,
            actual_rate FLOAT,
            count INT DEFAULT 0,
            abs_diff FLOAT
        )
    """)
    log.info("Ensured backtesting tables exist")


BACKTEST_TABLE = f"{SCHEMA}.backtest_results"
BACKTEST_METRICS_TABLE = f"{SCHEMA}.backtest_metrics"
BACKTEST_COHORT_TABLE = f"{SCHEMA}.backtest_cohort_results"


# ── LGD Backtesting (EBA/GL/2017/16 §150-160) ──────────────────────────────

def _compute_lgd_backtest(loans_df: pd.DataFrame) -> dict:
    """
    Compute real LGD backtesting metrics from historical defaults.
    Compares predicted LGD assumptions against realised recovery outcomes.
    Returns 'insufficient_data' status if not enough defaults available.
    """
    defaults_tbl = _t('historical_defaults')
    try:
        defaults_df = query_df(f"""
            SELECT loan_id, product_type,
                   gross_carrying_amount_at_default as gca_at_default,
                   total_recovery_amount,
                   CASE WHEN gross_carrying_amount_at_default > 0
                        THEN 1.0 - (total_recovery_amount / gross_carrying_amount_at_default)
                        ELSE 1.0
                   END as realised_lgd
            FROM {defaults_tbl}
            WHERE total_recovery_amount IS NOT NULL
        """)
    except Exception:
        defaults_df = pd.DataFrame()

    if defaults_df.empty or len(defaults_df) < MIN_DEFAULTS_FOR_LGD:
        return {
            "status": "insufficient_data",
            "message": f"LGD backtesting requires at least {MIN_DEFAULTS_FOR_LGD} resolved defaults with recovery data. "
                       f"Found: {len(defaults_df) if not defaults_df.empty else 0}.",
            "minimum_required": MIN_DEFAULTS_FOR_LGD,
            "available": len(defaults_df) if not defaults_df.empty else 0,
            "metrics": {},
        }

    defaults_df["realised_lgd"] = defaults_df["realised_lgd"].astype(float).clip(0, 1)

    from db.pool import SCHEMA as _schema
    try:
        product_lgd_df = query_df(f"""
            SELECT DISTINCT product_type,
                   COALESCE(
                       (SELECT value::float FROM {_schema}.app_config
                        WHERE key = 'model' LIMIT 1),
                       0.45
                   ) as predicted_lgd
            FROM {defaults_tbl}
        """)
    except Exception:
        product_lgd_df = pd.DataFrame()

    predicted_lgd_map = {}
    _FALLBACK_LGD = {
        "credit_card": 0.60, "residential_mortgage": 0.15,
        "commercial_loan": 0.25, "personal_loan": 0.50, "auto_loan": 0.35,
    }
    for product in defaults_df["product_type"].unique():
        predicted_lgd_map[product] = _FALLBACK_LGD.get(product, 0.45)

    try:
        import admin_config
        cfg = admin_config.get_config()
        lgd_cfg = cfg.get("model", {}).get("lgd_assumptions", {})
        for product, vals in lgd_cfg.items():
            predicted_lgd_map[product] = vals.get("lgd", predicted_lgd_map.get(product, 0.45))
    except Exception:
        pass

    overall_predicted = []
    overall_realised = []
    product_results = []

    for product, group in defaults_df.groupby("product_type"):
        pred_lgd = predicted_lgd_map.get(product, 0.45)
        realised = group["realised_lgd"].values
        mean_realised = float(realised.mean())
        std_realised = float(realised.std()) if len(realised) > 1 else 0.0

        overall_predicted.extend([pred_lgd] * len(group))
        overall_realised.extend(realised.tolist())

        product_results.append({
            "product_type": product,
            "n_defaults": len(group),
            "predicted_lgd": round(pred_lgd, 4),
            "mean_realised_lgd": round(mean_realised, 4),
            "std_realised_lgd": round(std_realised, 4),
            "median_realised_lgd": round(float(_np.median(realised)), 4),
            "p25_realised_lgd": round(float(_np.percentile(realised, 25)), 4),
            "p75_realised_lgd": round(float(_np.percentile(realised, 75)), 4),
            "bias": round(pred_lgd - mean_realised, 4),
            "abs_bias": round(abs(pred_lgd - mean_realised), 4),
        })

    pred_arr = _np.array(overall_predicted)
    real_arr = _np.array(overall_realised)
    mae = float(_np.mean(_np.abs(pred_arr - real_arr)))
    rmse = float(_np.sqrt(_np.mean((pred_arr - real_arr) ** 2)))
    mean_bias = float(_np.mean(pred_arr - real_arr))

    conservative = mean_bias > 0

    return {
        "status": "complete",
        "n_defaults": len(defaults_df),
        "metrics": {
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "Mean_Bias": round(mean_bias, 4),
            "Conservative": conservative,
        },
        "product_results": product_results,
    }


# ── Main Backtest Runner ─────────────────────────────────────────────────────

def run_backtest(model_type: str, config: dict | None = None) -> dict:
    """Execute backtesting: compare predicted PD/LGD vs actual outcomes using portfolio data."""
    config = config or {}
    backtest_id = f"BT-{model_type}-{_dt.now(_tz.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6]}"
    observation_window = config.get("observation_window", "12M")
    outcome_window = config.get("outcome_window", "12M")

    loans_tbl = _t('model_ready_loans')

    loan_df = query_df(f"""
        SELECT loan_id, product_type, assessed_stage, current_lifetime_pd,
               days_past_due, segment, vintage_cohort as cohort_id, gross_carrying_amount,
               CASE WHEN days_past_due >= 90 OR assessed_stage = 3 THEN 1 ELSE 0 END as defaulted
        FROM {loans_tbl}
    """)

    if loan_df.empty:
        raise ValueError("No portfolio data available for backtesting")

    total_loans = len(loan_df)
    predicted = loan_df["current_lifetime_pd"].astype(float).tolist()
    actual = loan_df["defaulted"].astype(int).tolist()

    metrics_data = {}
    metrics_detail = {}

    if model_type.upper() == "PD":
        disc = _compute_auc_gini_ks(predicted, actual)
        metrics_data["AUC"] = disc["auc"]
        metrics_data["Gini"] = disc["gini"]
        metrics_data["KS"] = disc["ks"]
        metrics_data["PSI"] = _compute_psi(predicted, [float(a) for a in actual])
        metrics_data["Brier"] = _compute_brier(predicted, actual)

        hl_result = _hosmer_lemeshow_test(predicted, actual)
        metrics_data["Hosmer_Lemeshow_pvalue"] = hl_result["p_value"]
        metrics_detail["Hosmer_Lemeshow_pvalue"] = hl_result

        sp_result = _spiegelhalter_test(predicted, actual)
        metrics_detail["Spiegelhalter"] = sp_result

        binomial_results = []
        grades = loan_df.groupby("product_type")
        passes = 0
        total_grades = 0
        for grade_name, grade_group in grades:
            n_g = len(grade_group)
            if n_g < MIN_DEFAULTS_PER_GRADE:
                continue
            avg_pd = float(grade_group["current_lifetime_pd"].astype(float).mean())
            n_def = int(grade_group["defaulted"].astype(int).sum())
            total_grades += 1

            binom_res = _binomial_test(avg_pd, n_g, n_def)
            binom_res["grade"] = str(grade_name)
            binomial_results.append(binom_res)
            if binom_res["pass"]:
                passes += 1

            jeff_res = _jeffreys_test(avg_pd, n_g, n_def)
            jeff_res["grade"] = str(grade_name)
            binomial_results.append({**jeff_res, "test_type": "jeffreys"})

        if total_grades > 0:
            metrics_data["Binomial_pass_rate"] = round(passes / total_grades, 4)
        metrics_detail["Binomial_tests"] = binomial_results

    else:
        lgd_result = _compute_lgd_backtest(loan_df)
        if lgd_result["status"] == "insufficient_data":
            metrics_data["LGD_Status"] = 0.0
            metrics_detail["LGD_Backtest"] = lgd_result
        else:
            for k, v in lgd_result["metrics"].items():
                if isinstance(v, (int, float)):
                    metrics_data[k] = v
            metrics_detail["LGD_Backtest"] = lgd_result

    metric_lights = []
    for name, value in metrics_data.items():
        light = _traffic_light(name, value)
        metric_lights.append(light)
        t = METRIC_THRESHOLDS.get(name, {})
        detail_json = _json.dumps(metrics_detail.get(name), default=_json_default) if name in metrics_detail else None
        execute(f"""
            INSERT INTO {BACKTEST_METRICS_TABLE}
                (metric_id, backtest_id, metric_name, metric_value,
                 threshold_green, threshold_amber, pass_fail, detail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), backtest_id, name, value,
              t.get("green", 0), t.get("amber", 0), light, detail_json))

    overall = _overall_traffic_light(metric_lights)
    pass_count = metric_lights.count("Green")
    amber_count = metric_lights.count("Amber")
    fail_count = metric_lights.count("Red")

    cohort_col = "product_type"
    try:
        if "cohort_id" in loan_df.columns and loan_df["cohort_id"].nunique() > 1:
            cohort_col = "cohort_id"
    except Exception:
        pass

    cohort_groups = loan_df.groupby(cohort_col)
    for cohort_name, group in cohort_groups:
        pred_rate = float(group["current_lifetime_pd"].astype(float).mean())
        act_rate = float(group["defaulted"].astype(int).mean())
        count = len(group)
        abs_diff = round(abs(pred_rate - act_rate), 6)
        execute(f"""
            INSERT INTO {BACKTEST_COHORT_TABLE}
                (cohort_id, backtest_id, cohort_name, predicted_rate, actual_rate, count, abs_diff)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), backtest_id, str(cohort_name),
              round(pred_rate, 6), round(act_rate, 6), count, abs_diff))

    execute(f"""
        INSERT INTO {BACKTEST_TABLE}
            (backtest_id, model_type, backtest_date, observation_window, outcome_window,
             overall_traffic_light, pass_count, amber_count, fail_count, total_loans, config, created_by)
        VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (backtest_id, model_type.upper(), observation_window, outcome_window,
          overall, pass_count, amber_count, fail_count, total_loans,
          _json.dumps(config), config.get("created_by", "system")))

    return get_backtest(backtest_id)


def list_backtests(model_type: str | None = None) -> list[dict]:
    if model_type:
        df = query_df(f"""
            SELECT backtest_id, model_type, backtest_date, observation_window, outcome_window,
                   overall_traffic_light, pass_count, amber_count, fail_count, total_loans, created_by
            FROM {BACKTEST_TABLE}
            WHERE model_type = %s
            ORDER BY backtest_date DESC
            LIMIT 50
        """, (model_type.upper(),))
    else:
        df = query_df(f"""
            SELECT backtest_id, model_type, backtest_date, observation_window, outcome_window,
                   overall_traffic_light, pass_count, amber_count, fail_count, total_loans, created_by
            FROM {BACKTEST_TABLE}
            ORDER BY backtest_date DESC
            LIMIT 50
        """)
    if df.empty:
        return []
    return df.to_dict("records")


def get_backtest(backtest_id: str) -> dict | None:
    df = query_df(f"SELECT * FROM {BACKTEST_TABLE} WHERE backtest_id = %s", (backtest_id,))
    if df.empty:
        return None
    result = df.iloc[0].to_dict()
    for col in ("config",):
        v = result.get(col)
        if isinstance(v, str):
            try:
                result[col] = _json.loads(v)
            except Exception:
                pass

    metrics_df = query_df(f"""
        SELECT metric_id, metric_name, metric_value, threshold_green, threshold_amber, pass_fail, detail
        FROM {BACKTEST_METRICS_TABLE}
        WHERE backtest_id = %s
        ORDER BY metric_name
    """, (backtest_id,))
    metrics_list = []
    if not metrics_df.empty:
        for _, row in metrics_df.iterrows():
            m = row.to_dict()
            if isinstance(m.get("detail"), str):
                try:
                    m["detail"] = _json.loads(m["detail"])
                except Exception:
                    pass
            metrics_list.append(m)
    result["metrics"] = metrics_list

    cohort_df = query_df(f"""
        SELECT cohort_id, cohort_name, predicted_rate, actual_rate, count, abs_diff
        FROM {BACKTEST_COHORT_TABLE}
        WHERE backtest_id = %s
        ORDER BY count DESC
    """, (backtest_id,))
    result["cohort_results"] = cohort_df.to_dict("records") if not cohort_df.empty else []

    return result


def get_backtest_trend(model_type: str) -> list[dict]:
    """Historical trend of key metrics over time for a model type."""
    df = query_df(f"""
        SELECT r.backtest_id, r.backtest_date, r.overall_traffic_light,
               m.metric_name, m.metric_value, m.pass_fail
        FROM {BACKTEST_TABLE} r
        JOIN {BACKTEST_METRICS_TABLE} m ON r.backtest_id = m.backtest_id
        WHERE r.model_type = %s
        ORDER BY r.backtest_date ASC, m.metric_name
    """, (model_type.upper(),))

    if df.empty:
        return []

    trend_map: dict[str, dict] = {}
    for _, row in df.iterrows():
        bid = row["backtest_id"]
        if bid not in trend_map:
            trend_map[bid] = {
                "backtest_id": bid,
                "backtest_date": row["backtest_date"],
                "overall_traffic_light": row["overall_traffic_light"],
            }
        trend_map[bid][row["metric_name"]] = float(row["metric_value"]) if row["metric_value"] is not None else None
        trend_map[bid][f"{row['metric_name']}_light"] = row["pass_fail"]

    return list(trend_map.values())
