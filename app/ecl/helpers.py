"""
ECL Engine -- utility / helper functions.
"""
import json
from decimal import Decimal
from datetime import datetime, date

import numpy as np
import pandas as pd


def _emit(cb, event):
    """Call progress_callback if provided."""
    if cb:
        cb(event)


def _convergence_check(ecl_sims: np.ndarray, n_sims: int) -> dict:
    """Compute ECL convergence at 25/50/75/100% of sims."""
    checkpoints = {}
    for pct in (0.25, 0.50, 0.75, 1.0):
        k = max(1, int(n_sims * pct))
        subset_mean = ecl_sims[:, :k].mean(axis=1).sum()
        checkpoints[f"ecl_at_{int(pct*100)}pct_sims"] = float(subset_mean)
    values = list(checkpoints.values())
    mean_val = np.mean(values)
    std_val = np.std(values)
    checkpoints["coefficient_of_variation"] = round(float(std_val / mean_val) if mean_val != 0 else 0.0, 6)
    return checkpoints


def _convergence_check_from_paths(portfolio_paths: np.ndarray, n_sims: int) -> dict:
    """Compute ECL convergence from portfolio-level path totals."""
    checkpoints = {}
    for pct in (0.25, 0.50, 0.75, 1.0):
        k = max(1, int(n_sims * pct))
        checkpoints[f"ecl_at_{int(pct*100)}pct_sims"] = float(portfolio_paths[:k].mean())
    values = list(checkpoints.values())
    mean_val = np.mean(values)
    std_val = np.std(values)
    checkpoints["coefficient_of_variation"] = round(float(std_val / mean_val) if mean_val != 0 else 0.0, 6)
    return checkpoints


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts with JSON-safe types."""

    class _Enc(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Decimal):
                return float(o)
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            return super().default(o)

    return json.loads(json.dumps(df.to_dict("records"), cls=_Enc))
