"""
In-App IFRS 9 ECL Simulation Engine
====================================
Lightweight Monte Carlo ECL calculator that reads loan data from Lakebase
and runs vectorized simulations with user-configurable parameters.

Methodology mirrors scripts/03_run_ecl_calculation.py:
  - 8 macro scenarios with product-specific PD/LGD multipliers
  - Correlated PD-LGD draws via Cholesky decomposition
  - PD term structure: flat hazard (Stage 1), increasing hazard (Stage 2/3)
  - Amortizing EAD with prepayment adjustment
  - Quarterly discounting at EIR
  - Stage 1 -> 12-month horizon, Stage 2/3 -> remaining life

This module is now a thin re-export shim.  All implementation lives in
the ``ecl`` sub-package (ecl/constants.py, ecl/config.py, ecl/data_loader.py,
ecl/helpers.py, ecl/simulation.py, ecl/defaults.py).
"""

import logging as _logging
import sys as _sys

# Explicit imports that the old monolithic module exposed at module level.
# These are needed so that ``patch("ecl_engine.backend.query_df")`` works.
import backend  # noqa: F401
import numpy as np  # noqa: F401
import pandas as pd  # noqa: F401

log = _logging.getLogger(__name__)

# Re-export everything from the ecl sub-package so that existing callers
# (``import ecl_engine`` / ``from ecl_engine import run_simulation``) keep working.
from ecl import *  # noqa: F401,F403
from ecl import __all__ as _all  # noqa: F401

# Patching support: tests that ``patch("ecl_engine._load_loans")`` need the
# patch to propagate to the actual call-site in ecl.simulation, which calls
# through ``ecl.data_loader._load_loans``.  We override __setattr__ so that
# patching this module also patches the underlying sub-module attribute.

_PATCH_MAP = {
    "_load_loans": "ecl.data_loader",
    "_load_scenarios": "ecl.data_loader",
    "_load_config": "ecl.config",
    "_build_product_maps": "ecl.config",
}


class _PatchableModule(_sys.modules[__name__].__class__):
    """Module subclass that propagates mock.patch to sub-modules."""

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in _PATCH_MAP:
            submod = _sys.modules.get(_PATCH_MAP[name])
            if submod is not None:
                setattr(submod, name, value)


_sys.modules[__name__].__class__ = _PatchableModule
