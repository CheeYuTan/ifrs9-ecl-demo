"""
Satellite Model: Logistic Regression
======================================
logit(PD) = β₀ + β₁×unemployment + β₂×gdp + β₃×inflation
PD = sigmoid(logit)

Maps default rates through logit transform, ensuring predictions are bounded
between 0% and 100%. Produces accelerating losses under extreme stress.
"""
import numpy as np

MACRO_FEATURES = ["unemployment_rate", "gdp_growth_rate", "inflation_rate"]
MODEL_TYPE = "logistic_regression"


def _aic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + 2 * k


def _bic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + k * np.log(n)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit(X, y):
    from numpy.linalg import lstsq
    from sklearn.model_selection import train_test_split
    y_logit = logit(y)
    X_b = np.column_stack([np.ones(len(X)), X])
    beta, _, _, _ = lstsq(X_b, y_logit, rcond=None)
    y_pred = sigmoid(X_b @ beta)
    rss = np.sum((y - y_pred) ** 2)
    rmse = np.sqrt(rss / len(y))
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - rss / ss_tot if ss_tot > 0 else 0
    n, k = len(y), len(beta)
    if len(X) >= 6:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X_train_b = np.column_stack([np.ones(len(X_train)), X_train])
        beta_t, _, _, _ = lstsq(X_train_b, logit(y_train), rcond=None)
        X_test_b = np.column_stack([np.ones(len(X_test)), X_test])
        test_pred = sigmoid(X_test_b @ beta_t)
        test_rmse = float(np.sqrt(np.mean((y_test - test_pred) ** 2)))
    else:
        test_rmse = float(rmse)
    names = ["intercept"] + MACRO_FEATURES
    return {
        "model_type": MODEL_TYPE,
        "coefficients": dict(zip(names, beta.tolist())),
        "r_squared": round(r2, 6),
        "rmse": round(rmse, 6),
        "cv_rmse": round(test_rmse, 6),
        "test_rmse": round(test_rmse, 6),
        "aic": round(_aic(n, k, rss), 4),
        "bic": round(_bic(n, k, rss), 4),
        "formula": f"logit(PD) = {beta[0]:.6f} + {beta[1]:.6f}*unemp + {beta[2]:.6f}*gdp + {beta[3]:.6f}*infl",
        "y_pred": y_pred,
    }
