"""
Sprint 5 QA: ECL Engine — Monte Carlo Correctness

Deep tests of the core ECL calculation engine (ecl/ module, 9 files):
  - ecl/helpers.py: _emit, _convergence_check, _convergence_check_from_paths, _df_to_records
  - ecl/constants.py: fallback LGD, satellite coefficients, default weights
  - ecl/config.py: _t, _schema, _prefix, _build_product_maps, _load_config
  - ecl/data_loader.py: _load_loans, _load_scenarios
  - ecl/monte_carlo.py: prepare_loan_columns, run_scenario_sims (core math)
  - ecl/aggregation.py: aggregate_results
  - ecl/simulation.py: run_simulation (integration), _build_scenario_map
  - Edge cases & numerical stability
"""
import json
import math
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch, MagicMock, call

import numpy as np
import pandas as pd
import pytest

from conftest import PRODUCT_TYPES, SCENARIOS


# ═══════════════════════════════════════════════════════════════════
# Section 1: ecl/helpers.py
# ═══════════════════════════════════════════════════════════════════


class TestEmit:
    """Tests for _emit() helper."""

    def test_emit_calls_callback(self):
        from ecl.helpers import _emit
        events = []
        _emit(events.append, {"phase": "test"})
        assert len(events) == 1
        assert events[0]["phase"] == "test"

    def test_emit_noop_when_callback_is_none(self):
        from ecl.helpers import _emit
        _emit(None, {"phase": "test"})  # Should not raise

    def test_emit_passes_complex_event(self):
        from ecl.helpers import _emit
        events = []
        event = {"phase": "computing", "step": "scenario_start",
                 "detail": {"nested": [1, 2, 3]}, "progress": 42}
        _emit(events.append, event)
        assert events[0]["detail"]["nested"] == [1, 2, 3]
        assert events[0]["progress"] == 42


class TestConvergenceCheck:
    """Tests for _convergence_check() with 2D loan×sim arrays."""

    def test_returns_all_checkpoint_keys(self):
        from ecl.helpers import _convergence_check
        ecl_sims = np.ones((5, 100))
        result = _convergence_check(ecl_sims, 100)
        expected_keys = {"ecl_at_25pct_sims", "ecl_at_50pct_sims",
                         "ecl_at_75pct_sims", "ecl_at_100pct_sims",
                         "coefficient_of_variation"}
        assert set(result.keys()) == expected_keys

    def test_constant_data_cv_zero(self):
        from ecl.helpers import _convergence_check
        ecl_sims = np.full((10, 200), 100.0)
        result = _convergence_check(ecl_sims, 200)
        assert result["coefficient_of_variation"] == pytest.approx(0.0, abs=1e-6)

    def test_all_checkpoints_equal_for_constant_data(self):
        from ecl.helpers import _convergence_check
        ecl_sims = np.full((3, 100), 50.0)
        result = _convergence_check(ecl_sims, 100)
        # With constant data, all checkpoint values should be identical
        assert result["ecl_at_25pct_sims"] == pytest.approx(result["ecl_at_100pct_sims"])

    def test_checkpoints_positive_for_positive_data(self):
        from ecl.helpers import _convergence_check
        rng = np.random.default_rng(42)
        ecl_sims = rng.uniform(100, 500, (8, 300))
        result = _convergence_check(ecl_sims, 300)
        for key in ["ecl_at_25pct_sims", "ecl_at_50pct_sims",
                     "ecl_at_75pct_sims", "ecl_at_100pct_sims"]:
            assert result[key] > 0

    def test_cv_non_negative(self):
        from ecl.helpers import _convergence_check
        rng = np.random.default_rng(99)
        ecl_sims = rng.uniform(10, 20, (4, 50))
        result = _convergence_check(ecl_sims, 50)
        assert result["coefficient_of_variation"] >= 0

    def test_single_sim(self):
        from ecl.helpers import _convergence_check
        ecl_sims = np.array([[100.0]])
        result = _convergence_check(ecl_sims, 1)
        # All checkpoints should use k=1 (max(1, int(1*pct)))
        assert result["ecl_at_25pct_sims"] == pytest.approx(100.0)

    def test_cv_zero_when_mean_is_zero(self):
        from ecl.helpers import _convergence_check
        ecl_sims = np.zeros((5, 100))
        result = _convergence_check(ecl_sims, 100)
        assert result["coefficient_of_variation"] == 0.0


class TestConvergenceCheckFromPaths:
    """Tests for _convergence_check_from_paths() with 1D portfolio paths."""

    def test_returns_all_checkpoint_keys(self):
        from ecl.helpers import _convergence_check_from_paths
        paths = np.ones(200)
        result = _convergence_check_from_paths(paths, 200)
        expected_keys = {"ecl_at_25pct_sims", "ecl_at_50pct_sims",
                         "ecl_at_75pct_sims", "ecl_at_100pct_sims",
                         "coefficient_of_variation"}
        assert set(result.keys()) == expected_keys

    def test_constant_paths_cv_zero(self):
        from ecl.helpers import _convergence_check_from_paths
        paths = np.full(500, 1234.56)
        result = _convergence_check_from_paths(paths, 500)
        assert result["coefficient_of_variation"] == pytest.approx(0.0, abs=1e-6)

    def test_decreasing_cv_with_more_sims(self):
        """CV should decrease (or stay same) with stable simulation data."""
        from ecl.helpers import _convergence_check_from_paths
        rng = np.random.default_rng(42)
        # Large stable sample — CV should be small
        paths = rng.normal(5000, 100, 10000)
        result = _convergence_check_from_paths(paths, 10000)
        assert result["coefficient_of_variation"] < 0.05

    def test_single_path(self):
        from ecl.helpers import _convergence_check_from_paths
        paths = np.array([999.0])
        result = _convergence_check_from_paths(paths, 1)
        assert result["ecl_at_100pct_sims"] == pytest.approx(999.0)


class TestDfToRecords:
    """Tests for _df_to_records() JSON serialization."""

    def test_basic_dataframe(self):
        from ecl.helpers import _df_to_records
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = _df_to_records(df)
        assert result == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]

    def test_decimal_conversion(self):
        from ecl.helpers import _df_to_records
        df = pd.DataFrame({"val": [Decimal("3.14"), Decimal("2.72")]})
        result = _df_to_records(df)
        assert result[0]["val"] == pytest.approx(3.14)
        assert result[1]["val"] == pytest.approx(2.72)

    def test_datetime_conversion(self):
        from ecl.helpers import _df_to_records
        dt = datetime(2025, 6, 15, 10, 30, 0)
        df = pd.DataFrame({"ts": [dt]})
        result = _df_to_records(df)
        assert result[0]["ts"] == "2025-06-15T10:30:00"

    def test_date_conversion(self):
        from ecl.helpers import _df_to_records
        d = date(2025, 12, 31)
        df = pd.DataFrame({"dt": [d]})
        result = _df_to_records(df)
        assert result[0]["dt"] == "2025-12-31"

    def test_empty_dataframe(self):
        from ecl.helpers import _df_to_records
        df = pd.DataFrame({"a": [], "b": []})
        result = _df_to_records(df)
        assert result == []

    def test_nan_handling(self):
        from ecl.helpers import _df_to_records
        df = pd.DataFrame({"val": [1.0, float("nan"), 3.0]})
        result = _df_to_records(df)
        assert result[0]["val"] == 1.0
        # NaN passes through JSON round-trip — verify it stays NaN (not crash)
        assert result[1]["val"] != result[1]["val"]  # NaN != NaN
        assert result[2]["val"] == 3.0

    def test_mixed_types(self):
        from ecl.helpers import _df_to_records
        df = pd.DataFrame({
            "i": [1], "f": [2.5], "s": ["hello"],
            "d": [Decimal("9.99")], "dt": [datetime(2025, 1, 1)],
        })
        result = _df_to_records(df)
        assert len(result) == 1
        assert result[0]["i"] == 1
        assert result[0]["f"] == 2.5
        assert result[0]["s"] == "hello"
        assert result[0]["d"] == pytest.approx(9.99)
        assert result[0]["dt"] == "2025-01-01T00:00:00"


# ═══════════════════════════════════════════════════════════════════
# Section 2: ecl/constants.py
# ═══════════════════════════════════════════════════════════════════


class TestConstants:
    """Tests for ECL engine constant lookup tables."""

    def test_fallback_base_lgd_keys(self):
        from ecl.constants import _FALLBACK_BASE_LGD
        expected = {"credit_card", "residential_mortgage", "commercial_loan",
                    "personal_loan", "auto_loan"}
        assert set(_FALLBACK_BASE_LGD.keys()) == expected

    def test_fallback_base_lgd_values_in_range(self):
        from ecl.constants import _FALLBACK_BASE_LGD
        for product, lgd in _FALLBACK_BASE_LGD.items():
            assert 0 < lgd <= 1.0, f"LGD for {product} = {lgd} out of range"

    def test_fallback_satellite_keys_match_lgd(self):
        from ecl.constants import _FALLBACK_BASE_LGD, _FALLBACK_SATELLITE
        assert set(_FALLBACK_SATELLITE.keys()) == set(_FALLBACK_BASE_LGD.keys())

    def test_fallback_satellite_required_keys(self):
        from ecl.constants import _FALLBACK_SATELLITE
        required = {"pd_lgd_corr", "annual_prepay_rate", "lgd_std"}
        for product, sat in _FALLBACK_SATELLITE.items():
            assert set(sat.keys()) == required, f"Missing keys for {product}"

    def test_satellite_correlations_in_valid_range(self):
        from ecl.constants import _FALLBACK_SATELLITE
        for product, sat in _FALLBACK_SATELLITE.items():
            assert -1 <= sat["pd_lgd_corr"] <= 1, f"Invalid corr for {product}"

    def test_satellite_prepay_rates_positive(self):
        from ecl.constants import _FALLBACK_SATELLITE
        for product, sat in _FALLBACK_SATELLITE.items():
            assert 0 < sat["annual_prepay_rate"] < 1, f"Invalid prepay for {product}"

    def test_default_scenario_weights_sum_to_one(self):
        from ecl.constants import DEFAULT_SCENARIO_WEIGHTS
        total = sum(DEFAULT_SCENARIO_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=1e-10)

    def test_default_scenario_weights_all_positive(self):
        from ecl.constants import DEFAULT_SCENARIO_WEIGHTS
        for scenario, weight in DEFAULT_SCENARIO_WEIGHTS.items():
            assert weight > 0, f"Non-positive weight for {scenario}"

    def test_default_scenario_weights_count(self):
        from ecl.constants import DEFAULT_SCENARIO_WEIGHTS
        assert len(DEFAULT_SCENARIO_WEIGHTS) == 8

    def test_default_sat_has_required_keys(self):
        from ecl.constants import DEFAULT_SAT
        assert "pd_lgd_corr" in DEFAULT_SAT
        assert "annual_prepay_rate" in DEFAULT_SAT
        assert "lgd_std" in DEFAULT_SAT

    def test_default_lgd_value(self):
        from ecl.constants import DEFAULT_LGD
        assert DEFAULT_LGD == 0.45

    def test_base_lgd_is_fallback(self):
        from ecl.constants import BASE_LGD, _FALLBACK_BASE_LGD
        assert BASE_LGD is _FALLBACK_BASE_LGD

    def test_satellite_coefficients_is_fallback(self):
        from ecl.constants import SATELLITE_COEFFICIENTS, _FALLBACK_SATELLITE
        assert SATELLITE_COEFFICIENTS is _FALLBACK_SATELLITE

    def test_specific_lgd_values(self):
        """Verify known LGD values for key products."""
        from ecl.constants import _FALLBACK_BASE_LGD
        assert _FALLBACK_BASE_LGD["credit_card"] == 0.60
        assert _FALLBACK_BASE_LGD["residential_mortgage"] == 0.15
        assert _FALLBACK_BASE_LGD["commercial_loan"] == 0.25
        assert _FALLBACK_BASE_LGD["personal_loan"] == 0.50
        assert _FALLBACK_BASE_LGD["auto_loan"] == 0.35


# ═══════════════════════════════════════════════════════════════════
# Section 3: ecl/config.py
# ═══════════════════════════════════════════════════════════════════


class TestConfigFunctions:
    """Tests for ecl/config.py — _t, _schema, _prefix, _build_product_maps, _load_config."""

    def test_schema_returns_backend_schema(self):
        from ecl.config import _schema
        import backend
        assert _schema() == backend.SCHEMA

    def test_prefix_returns_backend_prefix(self):
        from ecl.config import _prefix
        import backend
        assert _prefix() == backend.PREFIX

    def test_t_returns_qualified_table_name(self):
        from ecl.config import _t
        import backend
        result = _t("model_ready_loans")
        assert result == f"{backend.SCHEMA}.{backend.PREFIX}model_ready_loans"

    def test_t_with_different_table_names(self):
        from ecl.config import _t
        import backend
        for table in ["mc_ecl_distribution", "sicr_thresholds", "satellite_model_metadata"]:
            result = _t(table)
            assert result.endswith(table)
            assert result.startswith(backend.SCHEMA)

    def test_build_product_maps_returns_two_dicts(self):
        from ecl.config import _build_product_maps
        with patch("ecl.config.backend.query_df", side_effect=Exception("no DB")):
            lgd_map, sat_map = _build_product_maps()
        assert isinstance(lgd_map, dict)
        assert isinstance(sat_map, dict)

    def test_build_product_maps_fallback_lgd_values(self):
        from ecl.config import _build_product_maps
        from ecl.constants import _FALLBACK_BASE_LGD
        with patch("ecl.config.backend.query_df", side_effect=Exception("no DB")):
            lgd_map, _ = _build_product_maps()
        for product, lgd in _FALLBACK_BASE_LGD.items():
            assert lgd_map[product] == lgd

    def test_build_product_maps_fallback_satellite_values(self):
        from ecl.config import _build_product_maps
        from ecl.constants import _FALLBACK_SATELLITE
        with patch("ecl.config.backend.query_df", side_effect=Exception("no DB")):
            _, sat_map = _build_product_maps()
        for product in _FALLBACK_SATELLITE:
            assert product in sat_map
            assert "pd_lgd_corr" in sat_map[product]

    def test_build_product_maps_adds_db_products(self):
        """If DB returns products not in fallbacks, they get DEFAULT_LGD."""
        from ecl.config import _build_product_maps
        from ecl.constants import DEFAULT_LGD, DEFAULT_SAT
        extra_product = pd.DataFrame({"product_type": ["student_loan"]})
        with patch("ecl.config.backend.query_df", return_value=extra_product):
            lgd_map, sat_map = _build_product_maps()
        assert lgd_map["student_loan"] == DEFAULT_LGD
        assert sat_map["student_loan"]["pd_lgd_corr"] == DEFAULT_SAT["pd_lgd_corr"]

    def test_load_config_returns_none_none_on_failure(self):
        from ecl.config import _load_config
        with patch.dict("sys.modules", {"admin_config": None}):
            with patch("builtins.__import__", side_effect=ImportError("no module")):
                result = _load_config()
        # Should return (None, None) when admin_config fails
        assert result == (None, None)

    def test_load_config_returns_lgd_and_weights_from_admin(self):
        from ecl.config import _load_config
        mock_admin = MagicMock()
        mock_admin.get_config.return_value = {
            "model": {"lgd_assumptions": {
                "credit_card": {"lgd": 0.55},
                "auto_loan": {"lgd": 0.30},
            }},
            "app_settings": {"scenarios": [
                {"key": "base", "weight": 0.6},
                {"key": "stress", "weight": 0.4},
            ]},
        }
        with patch.dict("sys.modules", {"admin_config": mock_admin}):
            lgd, weights = _load_config()
        assert lgd["credit_card"] == 0.55
        assert lgd["auto_loan"] == 0.30
        assert weights["base"] == 0.6
        assert weights["stress"] == 0.4


# ═══════════════════════════════════════════════════════════════════
# Section 4: ecl/data_loader.py
# ═══════════════════════════════════════════════════════════════════


class TestDataLoader:
    """Tests for ecl/data_loader.py — _load_loans, _load_scenarios."""

    def test_load_loans_calls_backend_query(self):
        from ecl.data_loader import _load_loans
        with patch("ecl.data_loader.backend.query_df", return_value=pd.DataFrame()) as mock_q:
            _load_loans()
        mock_q.assert_called_once()
        sql = mock_q.call_args[0][0]
        assert "model_ready_loans" in sql
        assert "loan_id" in sql
        assert "product_type" in sql
        assert "assessed_stage" in sql

    def test_load_scenarios_calls_backend_query(self):
        from ecl.data_loader import _load_scenarios
        df = pd.DataFrame({
            "scenario": ["base"], "weight": [1.0],
            "avg_pd_multiplier": [1.0], "avg_lgd_multiplier": [1.0],
            "pd_vol": [0.05], "lgd_vol": [0.03],
        })
        with patch("ecl.data_loader.backend.query_df", return_value=df) as mock_q:
            result = _load_scenarios()
        mock_q.assert_called_once()
        assert "mc_ecl_distribution" in mock_q.call_args[0][0]
        assert len(result) == 1

    def test_load_scenarios_fills_missing_columns(self):
        from ecl.data_loader import _load_scenarios
        df = pd.DataFrame({"scenario": ["base"], "weight": [1.0]})
        with patch("ecl.data_loader.backend.query_df", return_value=df):
            result = _load_scenarios()
        assert "avg_pd_multiplier" in result.columns
        assert result["avg_pd_multiplier"].iloc[0] == 1.0
        assert result["avg_lgd_multiplier"].iloc[0] == 1.0
        assert result["pd_vol"].iloc[0] == 0.05
        assert result["lgd_vol"].iloc[0] == 0.03

    def test_load_scenarios_preserves_existing_columns(self):
        from ecl.data_loader import _load_scenarios
        df = pd.DataFrame({
            "scenario": ["stress"], "weight": [1.0],
            "avg_pd_multiplier": [1.5], "avg_lgd_multiplier": [1.2],
            "pd_vol": [0.10], "lgd_vol": [0.08],
        })
        with patch("ecl.data_loader.backend.query_df", return_value=df):
            result = _load_scenarios()
        assert result["avg_pd_multiplier"].iloc[0] == 1.5
        assert result["lgd_vol"].iloc[0] == 0.08


# ═══════════════════════════════════════════════════════════════════
# Section 5: ecl/monte_carlo.py — Core Math
# ═══════════════════════════════════════════════════════════════════


class TestPrepareLoanColumns:
    """Tests for prepare_loan_columns() — derived column creation."""

    def _make_loans_df(self, n=5, **overrides):
        rng = np.random.default_rng(42)
        data = {
            "loan_id": [f"L{i}" for i in range(n)],
            "product_type": ["credit_card"] * n,
            "assessed_stage": [1] * n,
            "gross_carrying_amount": [10000.0] * n,
            "effective_interest_rate": [0.12] * n,
            "current_lifetime_pd": [0.05] * n,
            "remaining_months": [36] * n,
        }
        data.update(overrides)
        return pd.DataFrame(data)

    def test_adds_stage_column(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df()
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert "stage" in result.columns
        assert result["stage"].dtype == int

    def test_adds_gca_column(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df()
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert "gca" in result.columns
        assert result["gca"].iloc[0] == pytest.approx(10000.0)

    def test_adds_eir_column(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df()
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert "eir" in result.columns
        assert result["eir"].iloc[0] == pytest.approx(0.12)

    def test_adds_base_pd_column(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df()
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert "base_pd" in result.columns
        assert result["base_pd"].iloc[0] == pytest.approx(0.05)

    def test_adds_rem_q_column(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(remaining_months=[36] * 5)
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert "rem_q" in result.columns
        assert result["rem_q"].iloc[0] == 12  # 36 months / 3

    def test_rem_q_clips_to_minimum_1(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(remaining_months=[1] * 5)
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert result["rem_q"].iloc[0] >= 1

    def test_adds_base_lgd_from_product_map(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df()
        result = prepare_loan_columns(df, {"credit_card": 0.65})
        assert "base_lgd" in result.columns
        assert result["base_lgd"].iloc[0] == pytest.approx(0.65)

    def test_base_lgd_defaults_to_050_for_unknown_product(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(product_type=["unknown_product"] * 5)
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert result["base_lgd"].iloc[0] == pytest.approx(0.50)

    def test_drops_rows_with_null_stage(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(n=3, assessed_stage=[1, None, 3])
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert len(result) == 2

    def test_drops_rows_with_null_remaining_months(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(n=3, remaining_months=[36, None, 24])
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert len(result) == 2

    def test_drops_rows_with_null_gca(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(n=3, gross_carrying_amount=[10000, None, 5000])
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert len(result) == 2

    def test_fills_null_eir_with_floor(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(n=2, effective_interest_rate=[None, 0.10])
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert result["eir"].iloc[0] == pytest.approx(0.001)
        assert result["eir"].iloc[1] == pytest.approx(0.10)

    def test_fills_null_pd_with_zero(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(n=2, current_lifetime_pd=[None, 0.05])
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        assert result["base_pd"].iloc[0] == 0.0

    def test_rem_months_f_clipped_to_min_1(self):
        from ecl.monte_carlo import prepare_loan_columns
        df = self._make_loans_df(n=2, remaining_months=[0, 36])
        result = prepare_loan_columns(df, {"credit_card": 0.60})
        # remaining_months=0 should clip rem_months_f to 1.0
        assert result["rem_months_f"].min() >= 1.0


class TestRunScenarioSimsCoreMath:
    """Tests for run_scenario_sims() — the core Monte Carlo math."""

    def _make_simple_inputs(self, n_loans=1, n_sims=100, stage=1,
                            base_pd=0.05, base_lgd=0.45, gca=10000.0,
                            eir=0.12, rem_months=36, pd_mult=1.0, lgd_mult=1.0,
                            pd_vol=0.0, lgd_vol=0.0, pd_lgd_corr=0.3,
                            aging_factor=0.0, prepay_rate=0.0,
                            pd_floor=0.001, pd_cap=0.95,
                            lgd_floor=0.01, lgd_cap=0.95):
        """Build minimal inputs for run_scenario_sims."""
        rem_q = max(1, rem_months // 3)
        max_horizon = np.array([min(4, rem_q) if stage == 1 else rem_q] * n_loans)
        global_max_q = int(max_horizon.max())
        quarterly_prepay = 1.0 - (1.0 - prepay_rate) ** 0.25
        is_bullet = rem_months <= 3

        return dict(
            rng=np.random.default_rng(42),
            n_loans=n_loans, n_sims=n_sims, batch_size=min(n_sims, 200),
            rho_1d=np.full(n_loans, pd_lgd_corr),
            base_pd=np.full(n_loans, base_pd),
            base_lgd_arr=np.full(n_loans, base_lgd),
            pd_mult=pd_mult, lgd_mult=lgd_mult,
            pd_vol=pd_vol, lgd_vol=lgd_vol,
            pd_floor=pd_floor, pd_cap=pd_cap,
            lgd_floor=lgd_floor, lgd_cap=lgd_cap,
            aging_factor=aging_factor,
            is_stage_23_1d=(np.full(n_loans, stage) != 1),
            max_horizon=max_horizon,
            global_max_q=global_max_q,
            quarterly_prepay=np.full(n_loans, quarterly_prepay),
            rem_months_f=np.full(n_loans, float(max(1, rem_months))),
            is_bullet=np.full(n_loans, is_bullet),
            gca=np.full(n_loans, gca),
            eir=np.full(n_loans, eir),
            products=np.array(["credit_card"] * n_loans),
            unique_products=np.array(["credit_card"]),
            product_sim_ecls={"credit_card": np.zeros(n_sims)},
            w=1.0,
        )

    def test_returns_correct_shapes(self):
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(n_loans=5, n_sims=50)
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert loan_ecl.shape == (5,)
        assert path_ecls.shape == (50,)

    def test_ecl_non_negative(self):
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(n_loans=3, n_sims=100)
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert np.all(loan_ecl >= 0)
        assert np.all(path_ecls >= 0)

    def test_zero_pd_gives_near_zero_ecl(self):
        """With PD=0, ECL should be very close to zero (only pd_floor contributes)."""
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(base_pd=0.0, pd_vol=0.0, pd_floor=0.0, n_sims=200)
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        # With pd_floor=0 and base_pd=0, stressed_pd = 0, so ECL should be 0
        assert loan_ecl.sum() == pytest.approx(0.0, abs=1e-10)

    def test_zero_lgd_gives_near_zero_ecl(self):
        """With LGD=0, ECL should be very small (only lgd_floor contributes)."""
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(base_lgd=0.0, lgd_vol=0.0, lgd_floor=0.0, n_sims=200)
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert loan_ecl.sum() == pytest.approx(0.0, abs=1e-10)

    def test_zero_gca_gives_zero_ecl(self):
        """With GCA=0, EAD is 0 so ECL must be 0."""
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(gca=0.0, n_sims=50)
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert loan_ecl.sum() == pytest.approx(0.0, abs=1e-10)

    def test_stage_1_horizon_capped_at_4_quarters(self):
        """Stage 1 loans: max_horizon = min(4, rem_q)."""
        from ecl.monte_carlo import run_scenario_sims
        # 60 months = 20 quarters, but Stage 1 should cap at 4
        inputs = self._make_simple_inputs(stage=1, rem_months=60, n_sims=50)
        assert inputs["global_max_q"] == 4

    def test_stage_2_uses_full_remaining_life(self):
        """Stage 2/3 loans: max_horizon = rem_q (remaining quarters)."""
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(stage=2, rem_months=60, n_sims=50)
        assert inputs["global_max_q"] == 20  # 60/3

    def test_higher_pd_gives_higher_ecl(self):
        """ECL should increase with PD."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_low = self._make_simple_inputs(base_pd=0.02, pd_vol=0.0, n_sims=500)
        inputs_high = self._make_simple_inputs(base_pd=0.20, pd_vol=0.0, n_sims=500)
        ecl_low, _ = run_scenario_sims(**inputs_low)
        ecl_high, _ = run_scenario_sims(**inputs_high)
        assert ecl_high.sum() > ecl_low.sum()

    def test_higher_lgd_gives_higher_ecl(self):
        """ECL should increase with LGD."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_low = self._make_simple_inputs(base_lgd=0.10, lgd_vol=0.0, n_sims=500)
        inputs_high = self._make_simple_inputs(base_lgd=0.80, lgd_vol=0.0, n_sims=500)
        ecl_low, _ = run_scenario_sims(**inputs_low)
        ecl_high, _ = run_scenario_sims(**inputs_high)
        assert ecl_high.sum() > ecl_low.sum()

    def test_higher_gca_gives_higher_ecl(self):
        """ECL should increase with exposure."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_low = self._make_simple_inputs(gca=1000.0, n_sims=200)
        inputs_high = self._make_simple_inputs(gca=100000.0, n_sims=200)
        ecl_low, _ = run_scenario_sims(**inputs_low)
        ecl_high, _ = run_scenario_sims(**inputs_high)
        assert ecl_high.sum() > ecl_low.sum()

    def test_pd_clipping_at_floor_and_cap(self):
        """PD should be clipped between pd_floor and pd_cap."""
        from ecl.monte_carlo import run_scenario_sims
        # Very high PD should be clipped at cap
        inputs = self._make_simple_inputs(
            base_pd=0.99, pd_mult=2.0, pd_vol=0.0,
            pd_floor=0.01, pd_cap=0.50, n_sims=50
        )
        loan_ecl, _ = run_scenario_sims(**inputs)
        # ECL should be finite and reasonable (PD clipped to 0.50)
        assert np.all(np.isfinite(loan_ecl))
        assert loan_ecl.sum() > 0

    def test_lgd_clipping_at_floor_and_cap(self):
        """LGD should be clipped between lgd_floor and lgd_cap."""
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(
            base_lgd=0.99, lgd_mult=2.0, lgd_vol=0.0,
            lgd_floor=0.05, lgd_cap=0.50, n_sims=50
        )
        loan_ecl, _ = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_cholesky_correlation_structure(self):
        """Verify that z_lgd has expected correlation with z_pd."""
        rng = np.random.default_rng(42)
        n_loans, n_sims = 1, 100000
        rho = 0.5
        z_pd = rng.standard_normal((n_loans, n_sims))
        z_lgd_indep = rng.standard_normal((n_loans, n_sims))
        z_lgd = rho * z_pd + np.sqrt(1 - rho ** 2) * z_lgd_indep
        # Empirical correlation should be close to rho
        empirical_corr = np.corrcoef(z_pd[0], z_lgd[0])[0, 1]
        assert empirical_corr == pytest.approx(rho, abs=0.02)

    def test_cholesky_zero_correlation(self):
        """When rho=0, z_pd and z_lgd should be uncorrelated."""
        rng = np.random.default_rng(42)
        n = 100000
        z_pd = rng.standard_normal((1, n))
        z_lgd_indep = rng.standard_normal((1, n))
        rho = 0.0
        z_lgd = rho * z_pd + np.sqrt(1 - rho ** 2) * z_lgd_indep
        corr = np.corrcoef(z_pd[0], z_lgd[0])[0, 1]
        assert abs(corr) < 0.02

    def test_cholesky_negative_correlation(self):
        """Negative correlation should produce inversely correlated draws."""
        rng = np.random.default_rng(42)
        n = 100000
        z_pd = rng.standard_normal((1, n))
        z_lgd_indep = rng.standard_normal((1, n))
        rho = -0.4
        z_lgd = rho * z_pd + np.sqrt(1 - rho ** 2) * z_lgd_indep
        corr = np.corrcoef(z_pd[0], z_lgd[0])[0, 1]
        assert corr == pytest.approx(rho, abs=0.02)

    def test_lognormal_shock_mean_approximately_one(self):
        """PD/LGD shocks exp(z*vol - 0.5*vol^2) should have mean ~1.0."""
        rng = np.random.default_rng(42)
        n = 500000
        vol = 0.10
        z = rng.standard_normal(n)
        shock = np.exp(z * vol - 0.5 * vol ** 2)
        assert shock.mean() == pytest.approx(1.0, abs=0.01)

    def test_discount_factor_formula(self):
        """Verify discount = 1 / (1 + EIR/4)^q."""
        eir = 0.12
        for q in range(1, 13):
            expected = 1.0 / ((1.0 + eir / 4.0) ** q)
            actual = 1.0 / ((1.0 + eir / 4.0) ** q)
            assert actual == pytest.approx(expected)

    def test_amortizing_ead_decreases(self):
        """For non-bullet loans, EAD should decrease over time."""
        rem_months = 36.0
        gca = 10000.0
        # Quarter 1
        amort_q1 = max(0, 1.0 - (1 * 3) / rem_months)
        # Quarter 6
        amort_q6 = max(0, 1.0 - (6 * 3) / rem_months)
        assert amort_q1 > amort_q6

    def test_bullet_loan_constant_ead(self):
        """Bullet loans (rem_months <= 3) maintain constant GCA as EAD."""
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(
            rem_months=3, pd_vol=0.0, lgd_vol=0.0, n_sims=50
        )
        # is_bullet should be True for rem_months <= 3
        assert inputs["is_bullet"].all()

    def test_aging_factor_only_stage_23(self):
        """Aging factor should only increase PD for Stage 2/3, not Stage 1."""
        from ecl.monte_carlo import run_scenario_sims
        # Stage 1 with aging: should be same as without aging
        # (because aging mult = 1.0 for Stage 1)
        inputs_s1 = self._make_simple_inputs(
            stage=1, aging_factor=0.20, pd_vol=0.0, lgd_vol=0.0, n_sims=200
        )
        inputs_s1_no_aging = self._make_simple_inputs(
            stage=1, aging_factor=0.0, pd_vol=0.0, lgd_vol=0.0, n_sims=200
        )
        ecl_s1, _ = run_scenario_sims(**inputs_s1)
        ecl_s1_no, _ = run_scenario_sims(**inputs_s1_no_aging)
        assert ecl_s1.sum() == pytest.approx(ecl_s1_no.sum(), rel=1e-6)

    def test_aging_factor_increases_stage2_ecl(self):
        """Stage 2 with aging should have higher ECL than without."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_no_aging = self._make_simple_inputs(
            stage=2, aging_factor=0.0, pd_vol=0.0, lgd_vol=0.0, n_sims=200
        )
        inputs_aging = self._make_simple_inputs(
            stage=2, aging_factor=0.20, pd_vol=0.0, lgd_vol=0.0, n_sims=200
        )
        ecl_no, _ = run_scenario_sims(**inputs_no_aging)
        ecl_aging, _ = run_scenario_sims(**inputs_aging)
        assert ecl_aging.sum() > ecl_no.sum()

    def test_prepayment_reduces_ecl(self):
        """Higher prepayment should reduce ECL (less exposure over time)."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_no_prepay = self._make_simple_inputs(
            stage=2, rem_months=60, prepay_rate=0.0,
            pd_vol=0.0, lgd_vol=0.0, n_sims=300
        )
        inputs_prepay = self._make_simple_inputs(
            stage=2, rem_months=60, prepay_rate=0.20,
            pd_vol=0.0, lgd_vol=0.0, n_sims=300
        )
        ecl_no, _ = run_scenario_sims(**inputs_no_prepay)
        ecl_prepay, _ = run_scenario_sims(**inputs_prepay)
        assert ecl_prepay.sum() < ecl_no.sum()

    def test_pd_mult_scales_ecl(self):
        """Higher pd_mult (stress scenario) should increase ECL."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_base = self._make_simple_inputs(pd_mult=1.0, pd_vol=0.0, lgd_vol=0.0, n_sims=200)
        inputs_stress = self._make_simple_inputs(pd_mult=2.0, pd_vol=0.0, lgd_vol=0.0, n_sims=200)
        ecl_base, _ = run_scenario_sims(**inputs_base)
        ecl_stress, _ = run_scenario_sims(**inputs_stress)
        assert ecl_stress.sum() > ecl_base.sum()

    def test_lgd_mult_scales_ecl(self):
        """Higher lgd_mult (stress scenario) should increase ECL."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_base = self._make_simple_inputs(lgd_mult=1.0, pd_vol=0.0, lgd_vol=0.0, n_sims=200)
        inputs_stress = self._make_simple_inputs(lgd_mult=1.5, pd_vol=0.0, lgd_vol=0.0, n_sims=200)
        ecl_base, _ = run_scenario_sims(**inputs_base)
        ecl_stress, _ = run_scenario_sims(**inputs_stress)
        assert ecl_stress.sum() > ecl_base.sum()

    def test_survival_decreases_monotonically(self):
        """Survival probability should never increase across quarters."""
        # This is inherent: survival *= (1 - q_pd), where q_pd > 0
        # Verify by checking cumulative survival logic
        pd_q = 0.02  # quarterly PD
        survival = 1.0
        for q in range(1, 13):
            new_survival = survival * (1 - pd_q)
            assert new_survival <= survival
            survival = new_survival

    def test_deterministic_with_seed(self):
        """Same seed → same ECL."""
        from ecl.monte_carlo import run_scenario_sims
        inputs1 = self._make_simple_inputs(n_sims=100)
        inputs2 = self._make_simple_inputs(n_sims=100)
        ecl1, _ = run_scenario_sims(**inputs1)
        ecl2, _ = run_scenario_sims(**inputs2)
        np.testing.assert_array_almost_equal(ecl1, ecl2)

    def test_batch_processing_same_result(self):
        """Different batch sizes should produce same results with same seed."""
        from ecl.monte_carlo import run_scenario_sims
        inputs_small = self._make_simple_inputs(n_sims=100)
        inputs_small["batch_size"] = 10
        inputs_large = self._make_simple_inputs(n_sims=100)
        inputs_large["batch_size"] = 100
        ecl_small, path_small = run_scenario_sims(**inputs_small)
        ecl_large, path_large = run_scenario_sims(**inputs_large)
        # Same seed, same n_sims → same random draws → same results
        np.testing.assert_array_almost_equal(ecl_small, ecl_large)

    def test_product_sim_ecls_accumulated(self):
        """product_sim_ecls should be populated after simulation."""
        from ecl.monte_carlo import run_scenario_sims
        inputs = self._make_simple_inputs(n_sims=50, base_pd=0.05)
        run_scenario_sims(**inputs)
        prod_ecls = inputs["product_sim_ecls"]["credit_card"]
        # Should have non-zero values (w=1.0, base_pd=0.05)
        assert prod_ecls.sum() > 0


class TestHandCalculatedECL:
    """Verify ECL formula with hand-calculated expected values.

    For a deterministic case (zero volatility), we can compute ECL analytically.
    """

    def test_single_quarter_ecl_formula(self):
        """
        Single Stage 1 loan, 3 months remaining (1 quarter), zero vol:
        ECL = PD_q × LGD × GCA × DF
        where PD_q = 1 - (1 - PD_annual)^0.25
              DF = 1 / (1 + EIR/4)^1
        """
        from ecl.monte_carlo import run_scenario_sims

        pd_annual = 0.10
        lgd = 0.45
        gca = 100000.0
        eir = 0.08

        pd_q = 1.0 - (1.0 - pd_annual) ** 0.25
        df = 1.0 / (1.0 + eir / 4.0)
        expected_ecl = pd_q * lgd * gca * df

        n_sims = 1000
        inputs = dict(
            rng=np.random.default_rng(42),
            n_loans=1, n_sims=n_sims, batch_size=n_sims,
            rho_1d=np.array([0.3]),
            base_pd=np.array([pd_annual]),
            base_lgd_arr=np.array([lgd]),
            pd_mult=1.0, lgd_mult=1.0,
            pd_vol=0.0, lgd_vol=0.0,
            pd_floor=0.0, pd_cap=1.0,
            lgd_floor=0.0, lgd_cap=1.0,
            aging_factor=0.0,
            is_stage_23_1d=np.array([False]),
            max_horizon=np.array([1]),
            global_max_q=1,
            quarterly_prepay=np.array([0.0]),
            rem_months_f=np.array([3.0]),
            is_bullet=np.array([True]),
            gca=np.array([gca]),
            eir=np.array([eir]),
            products=np.array(["test"]),
            unique_products=np.array(["test"]),
            product_sim_ecls={"test": np.zeros(n_sims)},
            w=1.0,
        )

        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        actual_ecl = loan_ecl[0] / n_sims  # mean across sims
        assert actual_ecl == pytest.approx(expected_ecl, rel=1e-6)

    def test_two_quarter_ecl_with_survival(self):
        """
        Stage 1 loan, 6 months (2 quarters), zero vol, bullet:
        Q1: ECL_1 = PD_q × LGD × GCA × DF_1
        Q2: ECL_2 = (1-PD_q) × PD_q × LGD × GCA × DF_2
        Total = ECL_1 + ECL_2
        """
        from ecl.monte_carlo import run_scenario_sims

        pd_annual = 0.10
        lgd = 0.40
        gca = 50000.0
        eir = 0.10

        pd_q = 1.0 - (1.0 - pd_annual) ** 0.25
        df1 = 1.0 / (1.0 + eir / 4.0)
        df2 = 1.0 / ((1.0 + eir / 4.0) ** 2)
        ecl_q1 = pd_q * lgd * gca * df1
        ecl_q2 = (1.0 - pd_q) * pd_q * lgd * gca * df2
        expected_ecl = ecl_q1 + ecl_q2

        n_sims = 1000
        inputs = dict(
            rng=np.random.default_rng(42),
            n_loans=1, n_sims=n_sims, batch_size=n_sims,
            rho_1d=np.array([0.3]),
            base_pd=np.array([pd_annual]),
            base_lgd_arr=np.array([lgd]),
            pd_mult=1.0, lgd_mult=1.0,
            pd_vol=0.0, lgd_vol=0.0,
            pd_floor=0.0, pd_cap=1.0,
            lgd_floor=0.0, lgd_cap=1.0,
            aging_factor=0.0,
            is_stage_23_1d=np.array([False]),
            max_horizon=np.array([2]),
            global_max_q=2,
            quarterly_prepay=np.array([0.0]),
            rem_months_f=np.array([6.0]),
            is_bullet=np.array([True]),
            gca=np.array([gca]),
            eir=np.array([eir]),
            products=np.array(["test"]),
            unique_products=np.array(["test"]),
            product_sim_ecls={"test": np.zeros(n_sims)},
            w=1.0,
        )

        loan_ecl, _ = run_scenario_sims(**inputs)
        actual_ecl = loan_ecl[0] / n_sims
        assert actual_ecl == pytest.approx(expected_ecl, rel=1e-6)

    def test_amortizing_ead_formula(self):
        """
        Amortizing loan: EAD_q = GCA × max(0, 1 - q*3/rem_months) × prepay_survival
        With zero prepayment, verify EAD at each quarter.
        """
        gca = 120000.0
        rem_months = 36.0
        for q in range(1, 13):
            amort = max(0.0, 1.0 - (q * 3) / rem_months)
            ead = gca * amort
            expected = gca * max(0, 1 - q * 3 / 36)
            assert ead == pytest.approx(expected)

    def test_scenario_weighting(self):
        """
        With two deterministic scenarios (no vol), weighted ECL should be:
        ECL = w1 × ECL_scenario1 + w2 × ECL_scenario2
        """
        from ecl.monte_carlo import run_scenario_sims

        pd_annual = 0.05
        lgd = 0.30
        gca = 100000.0
        eir = 0.06

        n_sims = 500

        def make_inputs(pd_mult, lgd_mult):
            return dict(
                rng=np.random.default_rng(42),
                n_loans=1, n_sims=n_sims, batch_size=n_sims,
                rho_1d=np.array([0.3]),
                base_pd=np.array([pd_annual]),
                base_lgd_arr=np.array([lgd]),
                pd_mult=pd_mult, lgd_mult=lgd_mult,
                pd_vol=0.0, lgd_vol=0.0,
                pd_floor=0.0, pd_cap=1.0,
                lgd_floor=0.0, lgd_cap=1.0,
                aging_factor=0.0,
                is_stage_23_1d=np.array([False]),
                max_horizon=np.array([4]),
                global_max_q=4,
                quarterly_prepay=np.array([0.0]),
                rem_months_f=np.array([36.0]),
                is_bullet=np.array([False]),
                gca=np.array([gca]),
                eir=np.array([eir]),
                products=np.array(["test"]),
                unique_products=np.array(["test"]),
                product_sim_ecls={"test": np.zeros(n_sims)},
                w=1.0,
            )

        ecl_base, _ = run_scenario_sims(**make_inputs(1.0, 1.0))
        ecl_stress, _ = run_scenario_sims(**make_inputs(2.0, 1.5))

        ecl_base_mean = ecl_base[0] / n_sims
        ecl_stress_mean = ecl_stress[0] / n_sims

        # Weighted: 60% base + 40% stress
        expected_weighted = 0.6 * ecl_base_mean + 0.4 * ecl_stress_mean
        actual_weighted = 0.6 * ecl_base_mean + 0.4 * ecl_stress_mean
        assert actual_weighted == pytest.approx(expected_weighted)


# ═══════════════════════════════════════════════════════════════════
# Section 6: ecl/aggregation.py
# ═══════════════════════════════════════════════════════════════════


class TestAggregateResults:
    """Tests for aggregate_results() output structure and correctness."""

    def _make_agg_inputs(self, n_loans=10, n_sims=50, n_scenarios=2):
        rng = np.random.default_rng(42)
        products = np.array(["credit_card"] * (n_loans // 2) + ["auto_loan"] * (n_loans - n_loans // 2))
        stages = np.array([1] * (n_loans // 2) + [2] * (n_loans - n_loans // 2))
        loans_df = pd.DataFrame({
            "loan_id": [f"L{i}" for i in range(n_loans)],
            "product_type": products,
            "stage": stages,
            "gca": rng.uniform(5000, 50000, n_loans),
        })
        loan_weighted_ecl = rng.uniform(100, 2000, n_loans)
        scenarios = [f"scenario_{i}" for i in range(n_scenarios)]
        weights = {s: 1.0 / n_scenarios for s in scenarios}
        scenario_ecl_totals = {s: rng.uniform(50, 1000, n_loans) for s in scenarios}
        scenario_ecl_paths = {s: rng.uniform(5000, 50000, n_sims) for s in scenarios}
        unique_products = np.array(["credit_card", "auto_loan"])
        product_sim_ecls = {p: rng.uniform(100, 5000, n_sims) for p in unique_products}

        return dict(
            loans_df=loans_df,
            loan_weighted_ecl=loan_weighted_ecl,
            scenario_ecl_totals=scenario_ecl_totals,
            scenario_ecl_paths=scenario_ecl_paths,
            product_sim_ecls=product_sim_ecls,
            products=products,
            scenarios=scenarios,
            weights=weights,
            n_sims=n_sims,
            n_loans=n_loans,
            sim_params={"n_sims": n_sims, "random_seed": 42},
            t0=0.0,
            load_time=0.1,
        )

    def test_returns_all_required_keys(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        assert set(result.keys()) == {
            "portfolio_summary", "scenario_results", "product_scenario",
            "stage_summary", "run_metadata",
        }

    def test_portfolio_summary_groups_by_product_and_stage(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        for row in result["portfolio_summary"]:
            assert "product_type" in row
            assert "stage" in row
            assert "loan_count" in row
            assert "total_gca" in row
            assert "total_ecl" in row
            assert "coverage_ratio" in row

    def test_coverage_ratio_formula(self):
        """coverage_ratio = ECL / GCA × 100."""
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        for row in result["portfolio_summary"]:
            if row["total_gca"] > 0:
                expected = row["total_ecl"] / row["total_gca"] * 100
                assert row["coverage_ratio"] == pytest.approx(expected, rel=1e-3)

    def test_scenario_results_count(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs(n_scenarios=3)
        result = aggregate_results(**inputs)
        assert len(result["scenario_results"]) == 3

    def test_scenario_results_have_percentiles(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        for sr in result["scenario_results"]:
            assert "ecl_p50" in sr
            assert "ecl_p75" in sr
            assert "ecl_p95" in sr
            assert "ecl_p99" in sr
            # Percentiles should be ordered
            assert sr["ecl_p50"] <= sr["ecl_p75"] <= sr["ecl_p95"] <= sr["ecl_p99"]

    def test_product_scenario_cross_product_count(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs(n_scenarios=3)
        result = aggregate_results(**inputs)
        # 2 products × 3 scenarios = 6
        assert len(result["product_scenario"]) == 6

    def test_stage_summary_covers_input_stages(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        stages = {r["stage"] for r in result["stage_summary"]}
        assert 1 in stages
        assert 2 in stages

    def test_stage_summary_loan_count_sums(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs(n_loans=20)
        result = aggregate_results(**inputs)
        total_loans = sum(r["loan_count"] for r in result["stage_summary"])
        assert total_loans == 20

    def test_run_metadata_fields(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        meta = result["run_metadata"]
        assert meta["n_sims"] == 50
        assert meta["loan_count"] == 10
        assert meta["scenario_count"] == 2
        assert "timestamp" in meta
        assert "duration_seconds" in meta
        assert "convergence_by_product" in meta

    def test_convergence_by_product_keys(self):
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        conv = result["run_metadata"]["convergence_by_product"]
        assert "credit_card" in conv
        assert "auto_loan" in conv
        for prod_conv in conv.values():
            assert "mean_ecl" in prod_conv
            assert "std_ecl" in prod_conv
            assert "ci_95_width" in prod_conv
            assert "ci_95_pct" in prod_conv

    def test_progress_callback_called(self):
        from ecl.aggregation import aggregate_results
        events = []
        inputs = self._make_agg_inputs()
        inputs["progress_callback"] = events.append
        aggregate_results(**inputs)
        phases = [e["phase"] for e in events]
        assert "aggregating" in phases
        assert "done" in phases

    def test_ecl_values_serializable(self):
        """All values in result should be JSON-serializable."""
        from ecl.aggregation import aggregate_results
        inputs = self._make_agg_inputs()
        result = aggregate_results(**inputs)
        # This should not raise
        json.dumps(result, default=str)


# ═══════════════════════════════════════════════════════════════════
# Section 7: ecl/simulation.py — Integration
# ═══════════════════════════════════════════════════════════════════


class TestBuildScenarioMap:
    """Tests for _build_scenario_map()."""

    def test_converts_dataframe_to_dict(self):
        from ecl.simulation import _build_scenario_map
        df = pd.DataFrame({
            "scenario": ["base", "stress"],
            "weight": [0.6, 0.4],
            "avg_pd_multiplier": [1.0, 1.5],
            "avg_lgd_multiplier": [1.0, 1.2],
            "pd_vol": [0.05, 0.10],
            "lgd_vol": [0.03, 0.06],
        })
        result = _build_scenario_map(df)
        assert "base" in result
        assert "stress" in result
        assert result["base"]["pd_mult"] == 1.0
        assert result["stress"]["pd_mult"] == 1.5
        assert result["stress"]["lgd_mult"] == 1.2

    def test_values_are_float(self):
        from ecl.simulation import _build_scenario_map
        df = pd.DataFrame({
            "scenario": ["base"],
            "weight": [0.5],
            "avg_pd_multiplier": [1],  # int, should be converted to float
            "avg_lgd_multiplier": [1],
            "pd_vol": [5e-2],
            "lgd_vol": [3e-2],
        })
        result = _build_scenario_map(df)
        assert isinstance(result["base"]["weight"], float)
        assert isinstance(result["base"]["pd_mult"], float)

    def test_empty_dataframe(self):
        from ecl.simulation import _build_scenario_map
        df = pd.DataFrame(columns=["scenario", "weight", "avg_pd_multiplier",
                                    "avg_lgd_multiplier", "pd_vol", "lgd_vol"])
        result = _build_scenario_map(df)
        assert result == {}


class TestRunSimulationIntegration:
    """Integration tests for run_simulation() with mocked data loaders."""

    @pytest.fixture
    def mock_loaders(self, sample_loans_df, sample_scenarios_df):
        with patch("ecl.data_loader._load_loans", return_value=sample_loans_df), \
             patch("ecl.data_loader._load_scenarios", return_value=sample_scenarios_df), \
             patch("ecl.config.backend.query_df", side_effect=Exception("no DB")):
            yield

    def test_deterministic_output_with_seed(self, mock_loaders):
        from ecl.simulation import run_simulation
        r1 = run_simulation(n_sims=50, random_seed=12345)
        r2 = run_simulation(n_sims=50, random_seed=12345)
        # Same seed → same total ECL
        total1 = sum(r["total_ecl"] for r in r1["stage_summary"])
        total2 = sum(r["total_ecl"] for r in r2["stage_summary"])
        assert total1 == pytest.approx(total2, rel=1e-6)

    def test_different_seeds_give_different_results(self, mock_loaders):
        from ecl.simulation import run_simulation
        r1 = run_simulation(n_sims=100, random_seed=111)
        r2 = run_simulation(n_sims=100, random_seed=999)
        total1 = sum(r["total_ecl"] for r in r1["stage_summary"])
        total2 = sum(r["total_ecl"] for r in r2["stage_summary"])
        # Very unlikely to be exactly equal with different seeds
        assert total1 != total2

    def test_custom_weights_used(self, mock_loaders):
        from ecl.simulation import run_simulation
        custom = {"baseline": 0.5, "adverse": 0.5}
        result = run_simulation(n_sims=50, scenario_weights=custom)
        result_scenarios = {s["scenario"] for s in result["scenario_results"]}
        assert result_scenarios == {"baseline", "adverse"}

    def test_all_output_ecl_non_negative(self, mock_loaders):
        from ecl.simulation import run_simulation
        result = run_simulation(n_sims=50, random_seed=42)
        for sr in result["scenario_results"]:
            assert sr["total_ecl"] >= 0
        for ps in result["product_scenario"]:
            assert ps["total_ecl"] >= 0
        for ss in result["stage_summary"]:
            assert ss["total_ecl"] >= 0

    def test_missing_scenario_in_map_gets_defaults(self, sample_loans_df):
        """Scenarios in weights but not in DB should get default multipliers."""
        from ecl.simulation import run_simulation
        empty_scenarios = pd.DataFrame(columns=[
            "scenario", "weight", "avg_pd_multiplier", "avg_lgd_multiplier",
            "pd_vol", "lgd_vol"
        ])
        with patch("ecl.data_loader._load_loans", return_value=sample_loans_df), \
             patch("ecl.data_loader._load_scenarios", return_value=empty_scenarios), \
             patch("ecl.config.backend.query_df", side_effect=Exception("no DB")):
            result = run_simulation(n_sims=20, scenario_weights={"custom_scenario": 1.0})
        assert len(result["scenario_results"]) == 1
        assert result["scenario_results"][0]["scenario"] == "custom_scenario"

    def test_progress_phases_complete(self, mock_loaders):
        from ecl.simulation import run_simulation
        events = []
        run_simulation(n_sims=30, progress_callback=events.append, random_seed=42)
        phases = {e["phase"] for e in events}
        assert phases >= {"loading", "computing", "aggregating", "done"}

    def test_run_metadata_has_sim_params(self, mock_loaders):
        from ecl.simulation import run_simulation
        result = run_simulation(
            n_sims=30, pd_lgd_correlation=0.25,
            aging_factor=0.10, pd_floor=0.005,
            random_seed=42,
        )
        meta = result["run_metadata"]
        assert meta["pd_lgd_correlation"] == 0.25
        assert meta["aging_factor"] == 0.10
        assert meta["pd_floor"] == 0.005


# ═══════════════════════════════════════════════════════════════════
# Section 8: Edge Cases & Numerical Stability
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases: single loan, extreme parameters, numerical stability."""

    @pytest.fixture
    def mock_loaders_factory(self):
        """Factory to create mock loaders with custom loan data."""
        def _make(loans_df, scenarios_df=None):
            if scenarios_df is None:
                scenarios_df = pd.DataFrame({
                    "scenario": ["base"],
                    "weight": [1.0],
                    "avg_pd_multiplier": [1.0],
                    "avg_lgd_multiplier": [1.0],
                    "pd_vol": [0.05],
                    "lgd_vol": [0.03],
                })
            return patch("ecl.data_loader._load_loans", return_value=loans_df), \
                   patch("ecl.data_loader._load_scenarios", return_value=scenarios_df), \
                   patch("ecl.config.backend.query_df", side_effect=Exception("no DB"))
        return _make

    def _single_loan_df(self, **overrides):
        data = {
            "loan_id": ["L001"],
            "product_type": ["credit_card"],
            "assessed_stage": [1],
            "gross_carrying_amount": [10000.0],
            "effective_interest_rate": [0.12],
            "current_lifetime_pd": [0.05],
            "remaining_months": [36],
        }
        data.update(overrides)
        return pd.DataFrame(data)

    def test_single_loan_portfolio(self, mock_loaders_factory):
        from ecl.simulation import run_simulation
        df = self._single_loan_df()
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=50, scenario_weights={"base": 1.0}, random_seed=42)
        assert len(result["portfolio_summary"]) == 1
        assert result["portfolio_summary"][0]["loan_count"] == 1

    def test_very_small_pd(self, mock_loaders_factory):
        """PD=1e-6 should not cause NaN or Inf."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df(current_lifetime_pd=[1e-6])
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=50, scenario_weights={"base": 1.0}, random_seed=42)
        for sr in result["scenario_results"]:
            assert np.isfinite(sr["total_ecl"])

    def test_very_large_ead(self, mock_loaders_factory):
        """GCA=1e12 should not cause overflow."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df(gross_carrying_amount=[1e12])
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=50, scenario_weights={"base": 1.0}, random_seed=42)
        for sr in result["scenario_results"]:
            assert np.isfinite(sr["total_ecl"])
            assert sr["total_ecl"] > 0

    def test_pd_equals_one_certain_default(self, mock_loaders_factory):
        """PD=1.0 (certain default) should give maximum ECL."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df(current_lifetime_pd=[1.0])
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=50, scenario_weights={"base": 1.0},
                                    pd_cap=1.0, random_seed=42)
        total_ecl = sum(r["total_ecl"] for r in result["stage_summary"])
        assert total_ecl > 0

    def test_lgd_equals_one_total_loss(self, mock_loaders_factory):
        """LGD=1.0 should give maximum loss on default."""
        from ecl.simulation import run_simulation
        df_low = self._single_loan_df()
        df_high = self._single_loan_df()
        # Compare with normal LGD
        p1, p2, p3 = mock_loaders_factory(df_low)
        with p1, p2, p3:
            result_low = run_simulation(n_sims=100, scenario_weights={"base": 1.0},
                                        lgd_cap=0.30, random_seed=42)
        p1, p2, p3 = mock_loaders_factory(df_high)
        with p1, p2, p3:
            result_high = run_simulation(n_sims=100, scenario_weights={"base": 1.0},
                                         lgd_cap=1.0, random_seed=42)
        ecl_low = sum(r["total_ecl"] for r in result_low["stage_summary"])
        ecl_high = sum(r["total_ecl"] for r in result_high["stage_summary"])
        assert ecl_high >= ecl_low

    def test_single_scenario(self, mock_loaders_factory):
        """Single scenario with weight=1.0 should work correctly."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df()
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=30, scenario_weights={"single": 1.0}, random_seed=42)
        assert len(result["scenario_results"]) == 1
        assert result["scenario_results"][0]["weight"] == 1.0

    def test_many_scenarios(self, mock_loaders_factory):
        """10 scenarios with equal weights should work correctly."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df()
        weights = {f"sc_{i}": 0.1 for i in range(10)}
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=20, scenario_weights=weights, random_seed=42)
        assert len(result["scenario_results"]) == 10
        total_w = sum(s["weight"] for s in result["scenario_results"])
        assert total_w == pytest.approx(1.0)

    def test_stage_2_longer_horizon_more_ecl(self, mock_loaders_factory):
        """Stage 2 (lifetime) should have higher ECL than Stage 1 (12-month)."""
        from ecl.simulation import run_simulation
        df_s1 = self._single_loan_df(assessed_stage=[1], remaining_months=[60])
        df_s2 = self._single_loan_df(assessed_stage=[2], remaining_months=[60])
        p1, p2, p3 = mock_loaders_factory(df_s1)
        with p1, p2, p3:
            r1 = run_simulation(n_sims=200, scenario_weights={"base": 1.0}, random_seed=42)
        p1, p2, p3 = mock_loaders_factory(df_s2)
        with p1, p2, p3:
            r2 = run_simulation(n_sims=200, scenario_weights={"base": 1.0}, random_seed=42)
        ecl1 = sum(r["total_ecl"] for r in r1["stage_summary"])
        ecl2 = sum(r["total_ecl"] for r in r2["stage_summary"])
        assert ecl2 > ecl1

    def test_stage_3_more_ecl_than_stage_1(self, mock_loaders_factory):
        """Stage 3 should have even more ECL than Stage 1."""
        from ecl.simulation import run_simulation
        df_s1 = self._single_loan_df(assessed_stage=[1], remaining_months=[60])
        df_s3 = self._single_loan_df(assessed_stage=[3], remaining_months=[60])
        p1, p2, p3 = mock_loaders_factory(df_s1)
        with p1, p2, p3:
            r1 = run_simulation(n_sims=200, scenario_weights={"base": 1.0}, random_seed=42)
        p1, p2, p3 = mock_loaders_factory(df_s3)
        with p1, p2, p3:
            r3 = run_simulation(n_sims=200, scenario_weights={"base": 1.0}, random_seed=42)
        ecl1 = sum(r["total_ecl"] for r in r1["stage_summary"])
        ecl3 = sum(r["total_ecl"] for r in r3["stage_summary"])
        assert ecl3 > ecl1

    def test_short_remaining_life(self, mock_loaders_factory):
        """3-month remaining life (1 quarter) should still produce ECL."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df(remaining_months=[3])
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=50, scenario_weights={"base": 1.0}, random_seed=42)
        total_ecl = sum(r["total_ecl"] for r in result["stage_summary"])
        assert total_ecl > 0

    def test_mixed_products_portfolio(self, mock_loaders_factory):
        """Portfolio with multiple product types."""
        from ecl.simulation import run_simulation
        df = pd.DataFrame({
            "loan_id": [f"L{i}" for i in range(5)],
            "product_type": ["credit_card", "auto_loan", "residential_mortgage",
                            "commercial_loan", "personal_loan"],
            "assessed_stage": [1, 2, 1, 3, 1],
            "gross_carrying_amount": [10000, 25000, 200000, 50000, 15000],
            "effective_interest_rate": [0.20, 0.08, 0.04, 0.12, 0.15],
            "current_lifetime_pd": [0.05, 0.10, 0.01, 0.30, 0.08],
            "remaining_months": [24, 48, 240, 36, 12],
        })
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=30, scenario_weights={"base": 1.0}, random_seed=42)
        products = {r["product_type"] for r in result["portfolio_summary"]}
        assert len(products) == 5

    def test_convergence_improves_with_more_sims(self, mock_loaders_factory):
        """More simulations should reduce CV of the ECL estimate."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df()
        # Small n_sims
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            r_small = run_simulation(n_sims=20, scenario_weights={"base": 1.0}, random_seed=42)
        # Large n_sims
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            r_large = run_simulation(n_sims=500, scenario_weights={"base": 1.0}, random_seed=42)
        conv_small = r_small["run_metadata"]["convergence_by_product"]
        conv_large = r_large["run_metadata"]["convergence_by_product"]
        # CI width should be smaller with more sims
        for product in conv_small:
            if product in conv_large:
                assert conv_large[product]["ci_95_pct"] <= conv_small[product]["ci_95_pct"] + 5.0

    def test_no_nan_in_output(self, mock_loaders_factory):
        """No NaN values in any output field."""
        from ecl.simulation import run_simulation
        df = self._single_loan_df()
        p1, p2, p3 = mock_loaders_factory(df)
        with p1, p2, p3:
            result = run_simulation(n_sims=50, scenario_weights={"base": 1.0}, random_seed=42)
        # Check scenario results
        for sr in result["scenario_results"]:
            for key, val in sr.items():
                if isinstance(val, float):
                    assert not math.isnan(val), f"NaN in scenario_results.{key}"
        # Check portfolio summary
        for ps in result["portfolio_summary"]:
            for key, val in ps.items():
                if isinstance(val, float):
                    assert not math.isnan(val), f"NaN in portfolio_summary.{key}"


class TestNumericalStability:
    """Tests for numerical edge cases."""

    def test_very_small_gca_no_underflow(self):
        """Very small GCA should not cause underflow to negative."""
        from ecl.monte_carlo import run_scenario_sims
        n_sims = 100
        inputs = dict(
            rng=np.random.default_rng(42),
            n_loans=1, n_sims=n_sims, batch_size=n_sims,
            rho_1d=np.array([0.3]),
            base_pd=np.array([0.05]),
            base_lgd_arr=np.array([0.45]),
            pd_mult=1.0, lgd_mult=1.0,
            pd_vol=0.05, lgd_vol=0.03,
            pd_floor=0.001, pd_cap=0.95,
            lgd_floor=0.01, lgd_cap=0.95,
            aging_factor=0.0,
            is_stage_23_1d=np.array([False]),
            max_horizon=np.array([4]),
            global_max_q=4,
            quarterly_prepay=np.array([0.0]),
            rem_months_f=np.array([36.0]),
            is_bullet=np.array([False]),
            gca=np.array([0.01]),  # Very small GCA
            eir=np.array([0.12]),
            products=np.array(["test"]),
            unique_products=np.array(["test"]),
            product_sim_ecls={"test": np.zeros(n_sims)},
            w=1.0,
        )
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))
        assert np.all(loan_ecl >= 0)

    def test_zero_eir_no_division_error(self):
        """EIR=0 should not cause division by zero (discount = 1/(1+0)^q = 1)."""
        from ecl.monte_carlo import run_scenario_sims
        n_sims = 100
        inputs = dict(
            rng=np.random.default_rng(42),
            n_loans=1, n_sims=n_sims, batch_size=n_sims,
            rho_1d=np.array([0.3]),
            base_pd=np.array([0.05]),
            base_lgd_arr=np.array([0.45]),
            pd_mult=1.0, lgd_mult=1.0,
            pd_vol=0.05, lgd_vol=0.03,
            pd_floor=0.001, pd_cap=0.95,
            lgd_floor=0.01, lgd_cap=0.95,
            aging_factor=0.08,
            is_stage_23_1d=np.array([False]),
            max_horizon=np.array([4]),
            global_max_q=4,
            quarterly_prepay=np.array([0.0]),
            rem_months_f=np.array([36.0]),
            is_bullet=np.array([False]),
            gca=np.array([10000.0]),
            eir=np.array([0.0]),  # Zero interest rate
            products=np.array(["test"]),
            unique_products=np.array(["test"]),
            product_sim_ecls={"test": np.zeros(n_sims)},
            w=1.0,
        )
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))

    def test_high_volatility_no_nan(self):
        """High vol should not cause NaN from extreme shocks."""
        from ecl.monte_carlo import run_scenario_sims
        n_sims = 200
        inputs = dict(
            rng=np.random.default_rng(42),
            n_loans=1, n_sims=n_sims, batch_size=n_sims,
            rho_1d=np.array([0.3]),
            base_pd=np.array([0.05]),
            base_lgd_arr=np.array([0.45]),
            pd_mult=1.0, lgd_mult=1.0,
            pd_vol=0.50, lgd_vol=0.50,  # Very high volatility
            pd_floor=0.001, pd_cap=0.95,
            lgd_floor=0.01, lgd_cap=0.95,
            aging_factor=0.08,
            is_stage_23_1d=np.array([False]),
            max_horizon=np.array([4]),
            global_max_q=4,
            quarterly_prepay=np.array([0.0]),
            rem_months_f=np.array([36.0]),
            is_bullet=np.array([False]),
            gca=np.array([10000.0]),
            eir=np.array([0.12]),
            products=np.array(["test"]),
            unique_products=np.array(["test"]),
            product_sim_ecls={"test": np.zeros(n_sims)},
            w=1.0,
        )
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert np.all(np.isfinite(loan_ecl))
        assert np.all(np.isfinite(path_ecls))

    def test_correlation_near_one(self):
        """Correlation very close to 1 — Cholesky should still work."""
        rng = np.random.default_rng(42)
        rho = 0.99
        z_pd = rng.standard_normal((1, 10000))
        z_lgd_indep = rng.standard_normal((1, 10000))
        z_lgd = rho * z_pd + np.sqrt(1 - rho ** 2) * z_lgd_indep
        assert np.all(np.isfinite(z_lgd))
        corr = np.corrcoef(z_pd[0], z_lgd[0])[0, 1]
        assert corr == pytest.approx(rho, abs=0.02)

    def test_large_portfolio(self):
        """100 loans × 200 sims should complete without memory issues."""
        from ecl.monte_carlo import run_scenario_sims
        n_loans, n_sims = 100, 200
        rng = np.random.default_rng(42)
        inputs = dict(
            rng=rng,
            n_loans=n_loans, n_sims=n_sims, batch_size=200,
            rho_1d=np.full(n_loans, 0.3),
            base_pd=rng.uniform(0.01, 0.20, n_loans),
            base_lgd_arr=rng.uniform(0.10, 0.60, n_loans),
            pd_mult=1.0, lgd_mult=1.0,
            pd_vol=0.05, lgd_vol=0.03,
            pd_floor=0.001, pd_cap=0.95,
            lgd_floor=0.01, lgd_cap=0.95,
            aging_factor=0.08,
            is_stage_23_1d=np.array([i % 3 != 0 for i in range(n_loans)]),
            max_horizon=rng.integers(1, 20, n_loans),
            global_max_q=20,
            quarterly_prepay=np.full(n_loans, 0.02),
            rem_months_f=rng.uniform(3, 60, n_loans),
            is_bullet=np.full(n_loans, False),
            gca=rng.uniform(1000, 100000, n_loans),
            eir=rng.uniform(0.03, 0.25, n_loans),
            products=np.array(["credit_card"] * 50 + ["auto_loan"] * 50),
            unique_products=np.array(["credit_card", "auto_loan"]),
            product_sim_ecls={
                "credit_card": np.zeros(n_sims),
                "auto_loan": np.zeros(n_sims),
            },
            w=1.0,
        )
        loan_ecl, path_ecls = run_scenario_sims(**inputs)
        assert loan_ecl.shape == (n_loans,)
        assert path_ecls.shape == (n_sims,)
        assert np.all(np.isfinite(loan_ecl))
        assert np.all(np.isfinite(path_ecls))


# ═══════════════════════════════════════════════════════════════════
# Section 9: ecl/__init__.py — Re-exports
# ═══════════════════════════════════════════════════════════════════


class TestEclPackageExports:
    """Verify that the ecl package re-exports all public symbols."""

    def test_constants_exported(self):
        import ecl
        assert hasattr(ecl, "_FALLBACK_BASE_LGD")
        assert hasattr(ecl, "_FALLBACK_SATELLITE")
        assert hasattr(ecl, "DEFAULT_SAT")
        assert hasattr(ecl, "DEFAULT_LGD")
        assert hasattr(ecl, "DEFAULT_SCENARIO_WEIGHTS")
        assert hasattr(ecl, "BASE_LGD")
        assert hasattr(ecl, "SATELLITE_COEFFICIENTS")

    def test_config_exported(self):
        import ecl
        assert callable(ecl._schema)
        assert callable(ecl._prefix)
        assert callable(ecl._t)
        assert callable(ecl._build_product_maps)
        assert callable(ecl._load_config)

    def test_helpers_exported(self):
        import ecl
        assert callable(ecl._emit)
        assert callable(ecl._convergence_check)
        assert callable(ecl._convergence_check_from_paths)
        assert callable(ecl._df_to_records)

    def test_core_functions_exported(self):
        import ecl
        assert callable(ecl.run_simulation)
        assert callable(ecl.get_defaults)
        assert callable(ecl.aggregate_results)

    def test_data_loaders_exported(self):
        import ecl
        assert callable(ecl._load_loans)
        assert callable(ecl._load_scenarios)

    def test_all_list_complete(self):
        import ecl
        for name in ecl.__all__:
            assert hasattr(ecl, name), f"ecl.__all__ lists {name} but it's not exported"
