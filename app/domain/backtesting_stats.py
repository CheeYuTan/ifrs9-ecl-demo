"""
Statistical test functions for IFRS 9 backtesting.

Implements EBA/GL/2017/16 calibration tests and discrimination metrics:
  - Discrimination: AUC, Gini (Accuracy Ratio), KS statistic
  - Calibration: Binomial (§71), Jeffreys (§72), Hosmer-Lemeshow (§74), Spiegelhalter
  - Stability: Population Stability Index (PSI)
  - Scoring: Brier score
"""
import numpy as _np
import pandas as pd
from scipy import stats as _stats


def _compute_auc_gini_ks(predicted: list[float], actual: list[int]) -> dict:
    """AUC-ROC, Gini coefficient (Accuracy Ratio), and KS statistic."""
    n = len(predicted)
    if n == 0:
        return {"auc": 0.5, "gini": 0.0, "ks": 0.0}

    pairs = sorted(zip(predicted, actual), key=lambda x: -x[0])
    n_pos = sum(actual)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return {"auc": 0.5, "gini": 0.0, "ks": 0.0}

    tp = 0
    fp = 0
    auc = 0.0
    max_ks = 0.0
    prev_fpr = 0.0
    prev_tpr = 0.0

    for _, a in pairs:
        if a == 1:
            tp += 1
        else:
            fp += 1
        tpr = tp / n_pos
        fpr = fp / n_neg
        auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2
        ks_val = abs(tpr - fpr)
        if ks_val > max_ks:
            max_ks = ks_val
        prev_fpr = fpr
        prev_tpr = tpr

    gini = 2 * auc - 1
    return {"auc": round(auc, 4), "gini": round(gini, 4), "ks": round(max_ks, 4)}


def _compute_psi(expected: list[float], actual_vals: list[float], n_bins: int = 10) -> float:
    """Population Stability Index between two distributions."""
    if not expected or not actual_vals:
        return 0.0
    bins = _np.linspace(0, 1, n_bins + 1)
    exp_hist, _ = _np.histogram(expected, bins=bins)
    act_hist, _ = _np.histogram(actual_vals, bins=bins)
    exp_pct = (exp_hist + 1) / (sum(exp_hist) + n_bins)
    act_pct = (act_hist + 1) / (sum(act_hist) + n_bins)
    psi = float(_np.sum((act_pct - exp_pct) * _np.log(act_pct / exp_pct)))
    return round(psi, 4)


def _compute_brier(predicted: list[float], actual: list[int]) -> float:
    """Brier score: mean squared error for probability predictions."""
    if not predicted:
        return 0.0
    return round(sum((p - a) ** 2 for p, a in zip(predicted, actual)) / len(predicted), 4)


def _binomial_test(predicted_pd: float, n_obligors: int, n_defaults: int,
                   confidence: float = 0.95) -> dict:
    """
    Per-grade binomial test: is the observed default count within the
    confidence interval of the predicted PD × number of obligors?
    EBA/GL/2017/16 §71.
    """
    if n_obligors == 0:
        return {"pass": True, "p_value": 1.0, "detail": "No obligors"}

    btest = _stats.binomtest(n_defaults, n_obligors, predicted_pd, alternative='greater')
    p_value = btest.pvalue
    ci_upper = _stats.binom.ppf(confidence, n_obligors, predicted_pd)

    return {
        "predicted_pd": round(predicted_pd, 6),
        "n_obligors": n_obligors,
        "n_defaults": n_defaults,
        "observed_dr": round(n_defaults / n_obligors, 6) if n_obligors > 0 else 0,
        "expected_defaults": round(predicted_pd * n_obligors, 2),
        "ci_upper_95": int(ci_upper),
        "p_value": round(float(p_value), 6),
        "pass": n_defaults <= ci_upper,
    }


def _jeffreys_test(predicted_pd: float, n_obligors: int, n_defaults: int,
                   confidence: float = 0.95) -> dict:
    """
    Bayesian alternative to binomial test using Jeffreys prior Beta(0.5, 0.5).
    More appropriate for low-default portfolios.
    EBA/GL/2017/16 §72.
    """
    if n_obligors == 0:
        return {"pass": True, "p_value": 1.0, "detail": "No obligors"}

    alpha_post = 0.5 + n_defaults
    beta_post = 0.5 + n_obligors - n_defaults
    posterior_mean = alpha_post / (alpha_post + beta_post)
    ci_lower = _stats.beta.ppf((1 - confidence) / 2, alpha_post, beta_post)
    ci_upper = _stats.beta.ppf(1 - (1 - confidence) / 2, alpha_post, beta_post)

    return {
        "predicted_pd": round(predicted_pd, 6),
        "n_obligors": n_obligors,
        "n_defaults": n_defaults,
        "posterior_mean": round(float(posterior_mean), 6),
        "ci_lower_95": round(float(ci_lower), 6),
        "ci_upper_95": round(float(ci_upper), 6),
        "pass": ci_lower <= predicted_pd <= ci_upper,
    }


def _hosmer_lemeshow_test(predicted: list[float], actual: list[int],
                          n_groups: int = 10) -> dict:
    """
    Hosmer-Lemeshow goodness-of-fit test across PD deciles.
    Tests whether observed default rates match predicted rates across the
    full PD spectrum. EBA/GL/2017/16 §74.
    """
    n = len(predicted)
    if n < n_groups * 5:
        return {
            "chi_squared": 0.0, "p_value": 1.0, "df": n_groups - 2,
            "pass": True, "detail": f"Insufficient data (n={n}, need {n_groups * 5})",
            "groups": [],
        }

    arr = _np.array(list(zip(predicted, actual)), dtype=[('pred', float), ('act', int)])
    arr.sort(order='pred')
    groups = _np.array_split(arr, n_groups)

    chi_sq = 0.0
    group_details = []
    for i, g in enumerate(groups):
        n_g = len(g)
        if n_g == 0:
            continue
        obs_defaults = int(g['act'].sum())
        exp_defaults = float(g['pred'].sum())
        exp_non_defaults = n_g - exp_defaults

        if exp_defaults > 0:
            chi_sq += (obs_defaults - exp_defaults) ** 2 / exp_defaults
        if exp_non_defaults > 0:
            obs_non_defaults = n_g - obs_defaults
            chi_sq += (obs_non_defaults - exp_non_defaults) ** 2 / exp_non_defaults

        group_details.append({
            "group": i + 1,
            "n": n_g,
            "avg_predicted_pd": round(float(g['pred'].mean()), 6),
            "observed_dr": round(obs_defaults / n_g, 6),
            "expected_defaults": round(exp_defaults, 2),
            "observed_defaults": obs_defaults,
        })

    df = max(1, n_groups - 2)
    p_value = 1.0 - _stats.chi2.cdf(chi_sq, df)

    return {
        "chi_squared": round(float(chi_sq), 4),
        "p_value": round(float(p_value), 6),
        "df": df,
        "pass": p_value > 0.05,
        "traffic_light": "Green" if p_value > 0.05 else ("Amber" if p_value > 0.01 else "Red"),
        "groups": group_details,
    }


def _spiegelhalter_test(predicted: list[float], actual: list[int]) -> dict:
    """
    Spiegelhalter test for overall calibration of predicted probabilities.
    Tests H0: the model is well-calibrated.
    """
    n = len(predicted)
    if n == 0:
        return {"z_statistic": 0.0, "p_value": 1.0, "pass": True}

    p = _np.array(predicted)
    y = _np.array(actual, dtype=float)

    numerator = float(_np.sum((y - p) * (1 - 2 * p)))
    denominator = float(_np.sqrt(_np.sum(((1 - 2 * p) ** 2) * p * (1 - p))))

    if denominator == 0:
        return {"z_statistic": 0.0, "p_value": 1.0, "pass": True}

    z = numerator / denominator
    p_value = 2 * (1 - _stats.norm.cdf(abs(z)))

    return {
        "z_statistic": round(float(z), 4),
        "p_value": round(float(p_value), 6),
        "pass": p_value > 0.05,
        "traffic_light": "Green" if p_value > 0.05 else ("Amber" if p_value > 0.01 else "Red"),
    }
