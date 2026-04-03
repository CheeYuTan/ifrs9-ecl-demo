"""
Satellite Model: Ridge Regression (Optuna TPE Tuning)
======================================================
β = (X'X + αI)⁻¹ X'y

Uses Optuna TPE sampler to efficiently search for the best alpha
regularization parameter via train/validation/test split.
"""
import numpy as np

MACRO_FEATURES = ["unemployment_rate", "gdp_growth_rate", "inflation_rate"]
MODEL_TYPE = "ridge_regression"

N_TRIALS = 30


def _aic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + 2 * k


def _bic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + k * np.log(n)


def fit(X, y, alpha=None):
    import optuna
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import train_test_split

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    def objective(trial):
        a = trial.suggest_float("alpha", 1e-4, 100.0, log=True)
        model = Ridge(alpha=a)
        model.fit(X_train, y_train)
        val_pred = model.predict(X_val)
        return float(np.mean((y_val - val_pred) ** 2))

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=N_TRIALS, n_jobs=1, show_progress_bar=False)

    best_alpha = study.best_params["alpha"]
    val_rmse = np.sqrt(study.best_value)

    ridge = Ridge(alpha=best_alpha)
    ridge.fit(X_train, y_train)

    test_pred = ridge.predict(X_test)
    test_rmse = float(np.sqrt(np.mean((y_test - test_pred) ** 2)))

    y_pred = ridge.predict(X)
    rss = np.sum((y - y_pred) ** 2)
    rmse = np.sqrt(rss / len(y))
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - rss / ss_tot if ss_tot > 0 else 0
    n = len(y)
    k = X.shape[1] + 1

    names = MACRO_FEATURES
    coeffs = {"intercept": float(ridge.intercept_)}
    coeffs.update(dict(zip(names, ridge.coef_.tolist())))

    return {
        "model_type": MODEL_TYPE,
        "coefficients": coeffs,
        "r_squared": round(r2, 6),
        "rmse": round(rmse, 6),
        "aic": round(_aic(n, k, rss), 4),
        "bic": round(_bic(n, k, rss), 4),
        "cv_rmse": round(val_rmse, 6),
        "test_rmse": round(test_rmse, 6),
        "formula": f"PD = {ridge.intercept_:.6f} + {ridge.coef_[0]:.6f}*unemp + {ridge.coef_[1]:.6f}*gdp + {ridge.coef_[2]:.6f}*infl  (Ridge Optuna α={best_alpha:.4f})",
        "best_params": {"alpha": best_alpha},
        "y_pred": y_pred,
    }
