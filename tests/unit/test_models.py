"""
Unit tests for all IFRS 9 satellite model fit() functions.

Each model maps macro-economic variables (unemployment, GDP growth, inflation)
to observed default rates. Tests verify output schema, statistical validity,
and edge-case robustness.

Model list is derived from admin_config via conftest.MODEL_KEYS so that adding
or removing a satellite model in config automatically updates the test matrix.
"""
import numpy as np
import pytest

from conftest import MODEL_KEYS

# Check optuna availability — several models use Optuna for hyperparameter tuning
try:
    import optuna  # noqa: F401
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

requires_optuna = pytest.mark.skipif(
    not HAS_OPTUNA, reason="optuna not installed"
)

import linear_regression
import logistic_regression
import polynomial_regression
import ridge_regression
import random_forest
import elastic_net
import gradient_boosting
import xgboost_model


PARAMETRIC_MODELS = [
    (linear_regression, "linear_regression",
     ["intercept", "unemployment_rate", "gdp_growth_rate", "inflation_rate"]),
    (logistic_regression, "logistic_regression",
     ["intercept", "unemployment_rate", "gdp_growth_rate", "inflation_rate"]),
    (polynomial_regression, "polynomial_deg2",
     ["intercept", "unemployment_rate", "gdp_growth_rate", "inflation_rate",
      "unemployment_rate_sq", "gdp_growth_rate_sq", "inflation_rate_sq"]),
    pytest.param(ridge_regression, "ridge_regression",
     ["intercept", "unemployment_rate", "gdp_growth_rate", "inflation_rate"],
     marks=requires_optuna, id="ridge_regression"),
    pytest.param(elastic_net, "elastic_net",
     ["intercept", "unemployment_rate", "gdp_growth_rate", "inflation_rate"],
     marks=requires_optuna, id="elastic_net"),
]

ENSEMBLE_MODELS = [
    pytest.param(random_forest, "random_forest",
     ["unemployment_rate", "gdp_growth_rate", "inflation_rate"],
     marks=requires_optuna, id="random_forest"),
    pytest.param(gradient_boosting, "gradient_boosting",
     ["unemployment_rate", "gdp_growth_rate", "inflation_rate"],
     marks=requires_optuna, id="gradient_boosting"),
    pytest.param(xgboost_model, "xgboost",
     ["unemployment_rate", "gdp_growth_rate", "inflation_rate"],
     marks=requires_optuna, id="xgboost"),
]

ALL_MODELS = PARAMETRIC_MODELS + ENSEMBLE_MODELS


def _model_name(entry):
    """Extract model name from a tuple or pytest.param object."""
    if hasattr(entry, "values"):
        return entry.values[1]  # pytest.param stores args in .values
    return entry[1]


class TestModelCoverage:
    """Ensure the test matrix stays in sync with admin_config satellite models."""

    def test_all_config_models_are_tested(self):
        tested_keys = {_model_name(m) for m in ALL_MODELS}
        assert tested_keys == set(MODEL_KEYS), (
            f"Mismatch between admin_config satellite models and test matrix.\n"
            f"  Config: {sorted(MODEL_KEYS)}\n"
            f"  Tests:  {sorted(tested_keys)}"
        )


class TestModelOutputSchema:
    """Verify every model returns the required keys with correct types."""

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_fit_returns_required_keys(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)

        assert "model_type" in result
        assert "coefficients" in result
        assert "r_squared" in result
        assert "rmse" in result
        assert "formula" in result
        assert "y_pred" in result

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_model_type_matches(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        assert result["model_type"] == expected_type

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_coefficients_has_expected_keys(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        coefficients = result["coefficients"]
        assert isinstance(coefficients, dict)
        for key in coeff_keys:
            assert key in coefficients, f"Missing coefficient key: {key}"

    @pytest.mark.parametrize("module,expected_type,coeff_keys", PARAMETRIC_MODELS,
                             ids=[_model_name(m) for m in PARAMETRIC_MODELS])
    def test_parametric_has_aic_bic(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        assert "aic" in result
        assert "bic" in result

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ENSEMBLE_MODELS,
                             ids=[_model_name(m) for m in ENSEMBLE_MODELS])
    def test_ensemble_has_cv_rmse(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        assert "cv_rmse" in result
        assert result["cv_rmse"] >= 0


class TestModelStatistics:
    """Verify statistical properties of model outputs."""

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_r_squared_in_valid_range(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        assert 0 <= result["r_squared"] <= 1.0, \
            f"R² = {result['r_squared']} out of [0, 1] range"

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_rmse_non_negative(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        assert result["rmse"] >= 0

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_y_pred_length_matches_input(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        y_pred = np.asarray(result["y_pred"])
        assert len(y_pred) == len(y)

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_y_pred_no_nans(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        y_pred = np.asarray(result["y_pred"])
        assert not np.any(np.isnan(y_pred)), "y_pred contains NaN values"

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_formula_is_nonempty_string(self, macro_data, module, expected_type, coeff_keys):
        X, y = macro_data
        result = module.fit(X, y)
        assert isinstance(result["formula"], str)
        assert len(result["formula"]) > 10


class TestModelEdgeCases:
    """Test models with edge-case inputs: minimal data, constant y, correlated features."""

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_minimum_data_5_rows(self, macro_data_minimal, module, expected_type, coeff_keys):
        X, y = macro_data_minimal
        result = module.fit(X, y)
        assert result["model_type"] == expected_type
        assert len(np.asarray(result["y_pred"])) == 5

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_constant_y_does_not_crash(self, macro_data_constant_y, module, expected_type, coeff_keys):
        """When y is constant, models should still return valid output (R²=0 is acceptable)."""
        X, y = macro_data_constant_y
        result = module.fit(X, y)
        assert result["rmse"] >= 0
        assert len(np.asarray(result["y_pred"])) == len(y)

    @pytest.mark.parametrize("module,expected_type,coeff_keys", ALL_MODELS,
                             ids=[_model_name(m) for m in ALL_MODELS])
    def test_highly_correlated_features(self, macro_data_correlated, module, expected_type, coeff_keys):
        X, y = macro_data_correlated
        result = module.fit(X, y)
        assert result["rmse"] >= 0
        assert isinstance(result["coefficients"], dict)


class TestLogisticSpecific:
    """Logistic regression-specific tests."""

    def test_predictions_bounded_0_1(self, macro_data):
        X, y = macro_data
        result = logistic_regression.fit(X, y)
        y_pred = np.asarray(result["y_pred"])
        assert np.all(y_pred >= 0), "Logistic predictions should be >= 0"
        assert np.all(y_pred <= 1), "Logistic predictions should be <= 1"

    def test_sigmoid_function(self):
        assert logistic_regression.sigmoid(0) == pytest.approx(0.5)
        assert logistic_regression.sigmoid(100) == pytest.approx(1.0, abs=1e-6)
        assert logistic_regression.sigmoid(-100) == pytest.approx(0.0, abs=1e-6)

    def test_logit_inverse_of_sigmoid(self):
        p = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        roundtrip = logistic_regression.sigmoid(logistic_regression.logit(p))
        np.testing.assert_allclose(roundtrip, p, atol=1e-6)


@requires_optuna
class TestRidgeSpecific:
    """Ridge regression-specific tests."""

    def test_custom_alpha(self, macro_data):
        X, y = macro_data
        result_low = ridge_regression.fit(X, y, alpha=0.01)
        result_high = ridge_regression.fit(X, y, alpha=100.0)
        coeff_low = np.array(list(result_low["coefficients"].values()))
        coeff_high = np.array(list(result_high["coefficients"].values()))
        assert np.linalg.norm(coeff_high[1:]) <= np.linalg.norm(coeff_low[1:]), \
            "Higher alpha should shrink non-intercept coefficients"
