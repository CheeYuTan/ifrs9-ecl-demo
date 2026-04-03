"""
Satellite Model: Random Forest (Optuna TPE Tuning)
====================================================
Ensemble of decision trees with Optuna TPE sampler for efficient
hyperparameter search over n_estimators, max_depth, min_samples_leaf.
Uses train/validation/test split (no cross-validation).
"""
import numpy as np

MACRO_FEATURES = ["unemployment_rate", "gdp_growth_rate", "inflation_rate"]
MODEL_TYPE = "random_forest"

N_TRIALS = 12


def fit(X, y):
    import optuna
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    pruner = optuna.pruners.MedianPruner(n_startup_trials=4, n_warmup_steps=0)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 30, 150),
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 5),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 6),
        }
        model = RandomForestRegressor(**params, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        val_pred = model.predict(X_val)
        mse = float(np.mean((y_val - val_pred) ** 2))
        trial.report(mse, 0)
        if trial.should_prune():
            raise optuna.TrialPruned()
        return mse

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42), pruner=pruner)
    study.optimize(objective, n_trials=N_TRIALS, n_jobs=1, show_progress_bar=False)

    best_params = study.best_params
    val_rmse = np.sqrt(study.best_value)

    best = RandomForestRegressor(**best_params, random_state=42, n_jobs=-1)
    best.fit(X_train, y_train)

    test_pred = best.predict(X_test)
    test_rmse = float(np.sqrt(np.mean((y_test - test_pred) ** 2)))

    y_pred = best.predict(X)
    rss = np.sum((y - y_pred) ** 2)
    rmse = np.sqrt(rss / len(y))
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - rss / ss_tot if ss_tot > 0 else 0
    importances = dict(zip(MACRO_FEATURES, best.feature_importances_.tolist()))

    params_str = ", ".join(f"{k}={v}" for k, v in best_params.items())
    return {
        "model_type": MODEL_TYPE,
        "coefficients": importances,
        "r_squared": round(r2, 6),
        "rmse": round(rmse, 6),
        "aic": None,
        "bic": None,
        "cv_rmse": round(val_rmse, 6),
        "test_rmse": round(test_rmse, 6),
        "formula": f"RF(Optuna TPE {N_TRIALS} trials+pruning, {params_str}) importances: {', '.join(f'{k}={v:.3f}' for k, v in importances.items())}",
        "best_params": best_params,
        "y_pred": y_pred,
    }
