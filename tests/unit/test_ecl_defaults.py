"""Tests for ecl/defaults.py — get_defaults() simulation parameter discovery."""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from ecl.defaults import get_defaults


class TestGetDefaults:
    def _mock_dependencies(self, scenarios_df=None, cfg_lgd=None, cfg_weights=None, dyn_lgd=None, dyn_sat=None):
        """Set up common mocks for get_defaults."""
        if scenarios_df is None:
            scenarios_df = pd.DataFrame({
                "scenario": ["base", "adverse"],
                "weight": [0.6, 0.3],
                "ecl_mean": [100_000.0, 200_000.0],
                "ecl_p50": [95_000.0, 180_000.0],
                "ecl_p75": [110_000.0, 220_000.0],
                "ecl_p95": [130_000.0, 280_000.0],
                "ecl_p99": [150_000.0, 320_000.0],
                "avg_pd_multiplier": [1.0, 1.5],
                "avg_lgd_multiplier": [1.0, 1.2],
                "pd_vol": [0.05, 0.10],
                "lgd_vol": [0.03, 0.06],
            })
        if dyn_lgd is None:
            dyn_lgd = {"Mortgage": 0.35, "Auto": 0.45}
        if dyn_sat is None:
            dyn_sat = {
                "Mortgage": {"pd_lgd_corr": 0.30, "annual_prepay_rate": 0.05},
                "Auto": {"pd_lgd_corr": 0.25, "annual_prepay_rate": 0.08},
            }
        return scenarios_df, cfg_lgd, cfg_weights, dyn_lgd, dyn_sat

    def test_basic_result_structure(self):
        scenarios_df, cfg_lgd, cfg_weights, dyn_lgd, dyn_sat = self._mock_dependencies()
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (None, None)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, dyn_sat)
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.side_effect = Exception("no table")
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            result = get_defaults()
            assert "scenarios" in result
            assert "default_weights" in result
            assert "products" in result
            assert "default_params" in result
            assert len(result["scenarios"]) == 2
            assert result["default_params"]["n_sims"] == 1000

    def test_uses_config_lgd_when_available(self):
        scenarios_df, _, _, dyn_lgd, dyn_sat = self._mock_dependencies()
        cfg_lgd = {"Corporate": 0.55}
        cfg_weights = {"base": 0.5, "adverse": 0.5}
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (cfg_lgd, cfg_weights)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, dyn_sat)
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.side_effect = Exception("no table")
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            result = get_defaults()
            assert len(result["products"]) == 1
            assert result["products"][0]["product_type"] == "Corporate"
            assert result["default_weights"] == cfg_weights

    def test_falls_back_to_dynamic_lgd(self):
        scenarios_df, _, _, dyn_lgd, dyn_sat = self._mock_dependencies()
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (None, None)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, dyn_sat)
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.side_effect = Exception("no table")
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            result = get_defaults()
            assert len(result["products"]) == 2
            types = {p["product_type"] for p in result["products"]}
            assert "Mortgage" in types
            assert "Auto" in types

    def test_scenario_fields(self):
        scenarios_df, _, _, dyn_lgd, dyn_sat = self._mock_dependencies()
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (None, None)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, dyn_sat)
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.side_effect = Exception("no table")
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            result = get_defaults()
            s = result["scenarios"][0]
            required_fields = {"scenario", "weight", "ecl_mean", "ecl_p50", "ecl_p75", "ecl_p95", "ecl_p99",
                               "avg_pd_multiplier", "avg_lgd_multiplier", "pd_vol", "lgd_vol"}
            assert required_fields.issubset(set(s.keys()))

    def test_includes_sicr_thresholds_when_available(self):
        scenarios_df, _, _, dyn_lgd, dyn_sat = self._mock_dependencies()
        sicr_df = pd.DataFrame({"threshold": [0.5]})
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (None, None)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, dyn_sat)
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.return_value = sicr_df
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            result = get_defaults()
            assert "sicr_thresholds" in result

    def test_omits_sicr_when_table_missing(self):
        scenarios_df, _, _, dyn_lgd, dyn_sat = self._mock_dependencies()
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (None, None)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, dyn_sat)
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.side_effect = Exception("table not found")
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            result = get_defaults()
            assert "sicr_thresholds" not in result

    def test_default_params_values(self):
        scenarios_df, _, _, dyn_lgd, dyn_sat = self._mock_dependencies()
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (None, None)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, dyn_sat)
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.side_effect = Exception("no table")
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            result = get_defaults()
            params = result["default_params"]
            assert params["pd_floor"] == 0.001
            assert params["pd_cap"] == 0.95
            assert params["lgd_floor"] == 0.01
            assert params["lgd_cap"] == 0.95
            assert params["aging_factor"] == 0.08

    def test_product_includes_sat_defaults(self):
        scenarios_df, _, _, dyn_lgd, _ = self._mock_dependencies()
        with patch("ecl.defaults._cfg") as mock_cfg, \
             patch("ecl.defaults._dl") as mock_dl, \
             patch("ecl.defaults.backend") as mock_be:
            mock_cfg._load_config.return_value = (None, None)
            mock_cfg._build_product_maps.return_value = (dyn_lgd, {})
            mock_dl._load_scenarios.return_value = scenarios_df
            mock_be.query_df.side_effect = Exception("no table")
            mock_cfg._t.side_effect = lambda t: f"schema.{t}"
            from ecl.constants import DEFAULT_SAT
            result = get_defaults()
            for p in result["products"]:
                assert p["pd_lgd_correlation"] == DEFAULT_SAT["pd_lgd_corr"]
