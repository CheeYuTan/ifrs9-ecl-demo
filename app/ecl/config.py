"""
ECL Engine -- configuration loading (admin config + DB product maps).
"""
import logging
import backend
from ecl.constants import (
    _FALLBACK_BASE_LGD,
    _FALLBACK_SATELLITE,
    DEFAULT_SAT,
    DEFAULT_LGD,
)

log = logging.getLogger(__name__)


def _schema():
    return backend.SCHEMA


def _prefix():
    return backend.PREFIX


def _t(name: str) -> str:
    return f"{_schema()}.{_prefix()}{name}"


def _build_product_maps():
    """Build BASE_LGD and SATELLITE_COEFFICIENTS from admin config + DB products."""
    base_lgd = dict(_FALLBACK_BASE_LGD)
    sat_coeffs = {k: dict(v) for k, v in _FALLBACK_SATELLITE.items()}

    try:
        import admin_config
        cfg = admin_config.get_config()
        lgd_cfg = cfg.get("model", {}).get("lgd_assumptions", {})
        if lgd_cfg:
            for product, vals in lgd_cfg.items():
                base_lgd[product] = vals.get("lgd", DEFAULT_LGD)
    except Exception as exc:
        log.warning("Failed to load LGD config from admin_config, using fallbacks: %s", exc)

    try:
        products_df = backend.query_df(
            f"SELECT DISTINCT product_type FROM {_schema()}.{_prefix()}model_ready_loans"
        )
        for _, row in products_df.iterrows():
            p = row["product_type"]
            if p not in base_lgd:
                base_lgd[p] = DEFAULT_LGD
            if p not in sat_coeffs:
                sat_coeffs[p] = dict(DEFAULT_SAT)
    except Exception as exc:
        log.warning("Failed to load product types from DB, using fallbacks: %s", exc)

    return base_lgd, sat_coeffs


def _load_config():
    """Load product/scenario config from admin config, falling back to hardcoded defaults."""
    try:
        import admin_config
        cfg = admin_config.get_config()

        lgd_cfg = cfg.get("model", {}).get("lgd_assumptions", {})
        base_lgd = {k: v["lgd"] for k, v in lgd_cfg.items()} if lgd_cfg else None

        scenarios = cfg.get("app_settings", {}).get("scenarios", [])
        weights = {s["key"]: s["weight"] for s in scenarios} if scenarios else None

        return base_lgd, weights
    except Exception:
        return None, None
