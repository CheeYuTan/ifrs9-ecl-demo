"""
Satellite Model: Elastic Net (Optuna TPE Tuning)
==================================================
L1 + L2 penalty with Optuna TPE sampler to efficiently search
for the best alpha and l1_ratio via train/validation/test split.
"""
import numpy as np

MACRO_FEATURES = ["unemployment_rate", "gdp_growth_rate", "inflation_rate"]
MODEL_TYPE = "elastic_net"

N_TRIALS = 30


def _aic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + 2 * k


def _bic(n, k, rss):
    if rss <= 0 or n <= k:
        return float("inf")
    return n * np.log(rss / n) + k * np.log(n)


def fit(X, y):
    import optuna
    from sklearn.linear_model import ElasticNet
    from sklearn.model_selection import train_test_split

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    def objective(trial):
        a = trial.suggest_float("alpha", 1e-4, 1.0, log=True)
        l1 = trial.suggest_float("l1_ratio", 0.05, 0.95)
        model = ElasticNet(alpha=a, l1_ratio=l1, max_iter=10000, random_state=42)
        model.fit(X_train, y_train)
        val_pred = model.predict(X_val)
        return float(np.mean((y_val - val_pred) ** 2))

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=N_TRIALS, n_jobs=1, show_progress_bar=False)

    best_alpha = study.best_params["alpha"]
    best_l1 = study.best_params["l1_ratio"]
    val_rmse = np.sqrt(study.best_value)

    en = ElasticNet(alpha=best_alpha, l1_ratio=best_l1, max_iter=10000, random_state=42)
    en.fit(X_train, y_train)

    test_pred = en.predict(X_test)
    test_rmse = float(np.sqrt(np.mean((y_test - test_pred) ** 2)))

    y_pred = en.predict(X)
    rss = np.sum((y - y_pred) ** 2)
    rmse = np.sqrt(rss / len(y))
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - rss / ss_tot if ss_tot > 0 else 0
    n = len(y)
    k = np.count_nonzero(en.coef_) + 1

    names = MACRO_FEATURES
    coeffs = {"intercept": float(en.intercept_)}
    coeffs.update(dict(zip(names, en.coef_.tolist())))

    return {
        "model_type": MODEL_TYPE,
        "coefficients": coeffs,
        "r_squared": round(r2, 6),
        "rmse": round(rmse, 6),
        "aic": round(_aic(n, k, rss), 4),
        "bic": round(_bic(n, k, rss), 4),
        "cv_rmse": round(val_rmse, 6),
        "test_rmse": round(test_rmse, 6),
        "formula": f"PD = {en.intercept_:.6f} + {en.coef_[0]:.6f}*unemp + {en.coef_[1]:.6f}*gdp + {en.coef_[2]:.6f}*infl  (ElasticNet Optuna α={best_alpha:.4f}, L1={best_l1:.3f})",
        "best_params": {"alpha": best_alpha, "l1_ratio": best_l1},
        "y_pred": y_pred,
    }
