"""
ECL Engine -- constant lookup tables and fallback defaults.
"""

_FALLBACK_BASE_LGD = {
    "credit_card": 0.60,
    "residential_mortgage": 0.15,
    "commercial_loan": 0.25,
    "personal_loan": 0.50,
    "auto_loan": 0.35,
}

_FALLBACK_SATELLITE = {
    "credit_card": {"pd_lgd_corr": 0.35, "annual_prepay_rate": 0.03, "lgd_std": 0.15},
    "residential_mortgage": {"pd_lgd_corr": 0.20, "annual_prepay_rate": 0.08, "lgd_std": 0.08},
    "commercial_loan": {"pd_lgd_corr": 0.30, "annual_prepay_rate": 0.05, "lgd_std": 0.12},
    "personal_loan": {"pd_lgd_corr": 0.32, "annual_prepay_rate": 0.10, "lgd_std": 0.14},
    "auto_loan": {"pd_lgd_corr": 0.25, "annual_prepay_rate": 0.06, "lgd_std": 0.10},
}

DEFAULT_SAT = {"pd_lgd_corr": 0.30, "annual_prepay_rate": 0.05, "lgd_std": 0.15}
DEFAULT_LGD = 0.45

BASE_LGD, SATELLITE_COEFFICIENTS = _FALLBACK_BASE_LGD, _FALLBACK_SATELLITE

DEFAULT_SCENARIO_WEIGHTS = {
    "baseline": 0.30,
    "mild_recovery": 0.15,
    "strong_growth": 0.05,
    "mild_downturn": 0.15,
    "adverse": 0.15,
    "stagflation": 0.08,
    "severely_adverse": 0.07,
    "tail_risk": 0.05,
}
