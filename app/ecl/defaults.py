"""
ECL Engine -- get_defaults() for simulation parameter discovery.
"""

import backend

import ecl.config as _cfg
import ecl.data_loader as _dl
from ecl.constants import DEFAULT_SAT, DEFAULT_SCENARIO_WEIGHTS
from ecl.helpers import _df_to_records


def get_defaults() -> dict:
    """Return default simulation parameters, available scenarios, and product info."""
    cfg_lgd, cfg_weights = _cfg._load_config()
    dyn_lgd, dyn_sat = _cfg._build_product_maps()
    base_lgd = cfg_lgd if cfg_lgd else dyn_lgd
    default_weights = cfg_weights if cfg_weights else DEFAULT_SCENARIO_WEIGHTS

    scenarios_df = _dl._load_scenarios()

    scenario_info = []
    for _, row in scenarios_df.iterrows():
        scenario_info.append(
            {
                "scenario": row["scenario"],
                "weight": float(row["weight"]),
                "ecl_mean": float(row["ecl_mean"]),
                "ecl_p50": float(row["ecl_p50"]),
                "ecl_p75": float(row["ecl_p75"]),
                "ecl_p95": float(row["ecl_p95"]),
                "ecl_p99": float(row["ecl_p99"]),
                "avg_pd_multiplier": float(row["avg_pd_multiplier"]),
                "avg_lgd_multiplier": float(row["avg_lgd_multiplier"]),
                "pd_vol": float(row["pd_vol"]),
                "lgd_vol": float(row["lgd_vol"]),
            }
        )

    product_info = []
    for product, lgd in base_lgd.items():
        sat = dyn_sat.get(product, DEFAULT_SAT)
        product_info.append(
            {
                "product_type": product,
                "base_lgd": lgd,
                "pd_lgd_correlation": sat["pd_lgd_corr"],
                "annual_prepay_rate": sat["annual_prepay_rate"],
            }
        )

    default_params = {
        "n_sims": 1000,
        "pd_lgd_correlation": 0.30,
        "aging_factor": 0.08,
        "pd_floor": 0.001,
        "pd_cap": 0.95,
        "lgd_floor": 0.01,
        "lgd_cap": 0.95,
    }

    result = {
        "scenarios": scenario_info,
        "default_weights": default_weights,
        "products": product_info,
        "default_params": default_params,
    }

    # Optionally include SICR thresholds if the table exists
    try:
        sicr_df = backend.query_df(f"SELECT * FROM {_cfg._t('sicr_thresholds')} LIMIT 50")
        if not sicr_df.empty:
            result["sicr_thresholds"] = _df_to_records(sicr_df)
    except Exception:
        pass

    # Optionally include satellite model metadata if the table exists
    try:
        sat_df = backend.query_df(f"SELECT * FROM {_cfg._t('satellite_model_metadata')} LIMIT 50")
        if not sat_df.empty:
            result["satellite_model_metadata"] = _df_to_records(sat_df)
    except Exception:
        pass

    return result
