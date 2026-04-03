"""
Satellite Model: Polynomial Regression (degree 2)
===================================================
PD = β₀ + β₁×x₁ + β₂×x₂ + β₃×x₃ + β₄×x₁² + β₅×x₂² + β₆×x₃²

Captures non-linear relationships between macro variables and default rates
using quadratic terms. More flexible than linear but risks overfitting.
"""
import numpy as np

MACRO_FEATURES = ["unemployment_rate", "gdp_growth_rate", "inflation_rate"]
MODEL_TYPE = "polynomial_deg2"


def _aic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + 2 * k


def _bic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + k * np.log(n)


def fit(X, y):
    from numpy.linalg import lstsq
    from sklearn.model_selection import train_test_split
    X_poly = np.column_stack([np.ones(len(X)), X, X ** 2])
    beta, _, _, _ = lstsq(X_poly, y, rcond=None)
    y_pred = X_poly @ beta
    rss = np.sum((y - y_pred) ** 2)
    rmse = np.sqrt(rss / len(y))
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - rss / ss_tot if ss_tot > 0 else 0
    n, k = len(y), len(beta)
    if len(X) >= 6:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X_train_poly = np.column_stack([np.ones(len(X_train)), X_train, X_train ** 2])
        beta_t, _, _, _ = lstsq(X_train_poly, y_train, rcond=None)
        X_test_poly = np.column_stack([np.ones(len(X_test)), X_test, X_test ** 2])
        test_pred = X_test_poly @ beta_t
        test_rmse = float(np.sqrt(np.mean((y_test - test_pred) ** 2)))
    else:
        test_rmse = float(rmse)
    names = ["intercept"] + MACRO_FEATURES + [f"{f}_sq" for f in MACRO_FEATURES]
    return {
        "model_type": MODEL_TYPE,
        "coefficients": dict(zip(names, beta.tolist())),
        "r_squared": round(r2, 6),
        "rmse": round(rmse, 6),
        "cv_rmse": round(test_rmse, 6),
        "test_rmse": round(test_rmse, 6),
        "aic": round(_aic(n, k, rss), 4),
        "bic": round(_bic(n, k, rss), 4),
        "formula": (f"PD = {beta[0]:.6f} + {beta[1]:.6f}*unemp + {beta[2]:.6f}*gdp + {beta[3]:.6f}*infl"
                    f" + {beta[4]:.6f}*unemp² + {beta[5]:.6f}*gdp² + {beta[6]:.6f}*infl²"),
        "y_pred": y_pred,
    }
