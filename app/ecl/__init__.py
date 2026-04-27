"""
ECL Engine sub-package.

Re-exports every public symbol so that ``from ecl import ...`` works
identically to the old monolithic ``ecl_engine`` module.
"""

from ecl.aggregation import aggregate_results
from ecl.config import (
    _build_product_maps,
    _load_config,
    _prefix,
    _schema,
    _t,
)
from ecl.constants import (
    _FALLBACK_BASE_LGD,
    _FALLBACK_SATELLITE,
    BASE_LGD,
    DEFAULT_LGD,
    DEFAULT_SAT,
    DEFAULT_SCENARIO_WEIGHTS,
    SATELLITE_COEFFICIENTS,
)
from ecl.data_loader import (
    _load_loans,
    _load_scenarios,
)
from ecl.defaults import get_defaults
from ecl.helpers import (
    _convergence_check,
    _convergence_check_from_paths,
    _df_to_records,
    _emit,
)
from ecl.simulation import run_simulation

__all__ = [
    # constants
    "_FALLBACK_BASE_LGD",
    "_FALLBACK_SATELLITE",
    "DEFAULT_SAT",
    "DEFAULT_LGD",
    "DEFAULT_SCENARIO_WEIGHTS",
    "BASE_LGD",
    "SATELLITE_COEFFICIENTS",
    # config
    "_schema",
    "_prefix",
    "_t",
    "_build_product_maps",
    "_load_config",
    # data loading
    "_load_loans",
    "_load_scenarios",
    # helpers
    "_emit",
    "_convergence_check",
    "_convergence_check_from_paths",
    "_df_to_records",
    # aggregation
    "aggregate_results",
    # core
    "run_simulation",
    "get_defaults",
]
