"""Dedicated tests for ecl/simulation.py — _build_scenario_map."""
import pandas as pd
import pytest

from ecl.simulation import _build_scenario_map


class TestBuildScenarioMap:
    def _make_df(self, scenarios=None):
        if scenarios is None:
            scenarios = [
                {"scenario": "base", "weight": 0.5, "avg_pd_multiplier": 1.0,
                 "avg_lgd_multiplier": 1.0, "pd_vol": 0.05, "lgd_vol": 0.03},
                {"scenario": "upside", "weight": 0.25, "avg_pd_multiplier": 0.8,
                 "avg_lgd_multiplier": 0.9, "pd_vol": 0.04, "lgd_vol": 0.02},
                {"scenario": "downside", "weight": 0.25, "avg_pd_multiplier": 1.5,
                 "avg_lgd_multiplier": 1.3, "pd_vol": 0.08, "lgd_vol": 0.05},
            ]
        return pd.DataFrame(scenarios)

    def test_returns_dict(self):
        result = _build_scenario_map(self._make_df())
        assert isinstance(result, dict)

    def test_has_all_scenarios(self):
        result = _build_scenario_map(self._make_df())
        assert set(result.keys()) == {"base", "upside", "downside"}

    def test_base_scenario_values(self):
        result = _build_scenario_map(self._make_df())
        base = result["base"]
        assert base["weight"] == 0.5
        assert base["pd_mult"] == 1.0
        assert base["lgd_mult"] == 1.0
        assert base["pd_vol"] == 0.05
        assert base["lgd_vol"] == 0.03

    def test_downside_stress_multipliers(self):
        result = _build_scenario_map(self._make_df())
        ds = result["downside"]
        assert ds["pd_mult"] > 1.0
        assert ds["lgd_mult"] > 1.0

    def test_upside_relief_multipliers(self):
        result = _build_scenario_map(self._make_df())
        up = result["upside"]
        assert up["pd_mult"] < 1.0
        assert up["lgd_mult"] < 1.0

    def test_values_are_float(self):
        result = _build_scenario_map(self._make_df())
        for sc_name, sc_data in result.items():
            for key in ("weight", "pd_mult", "lgd_mult", "pd_vol", "lgd_vol"):
                assert isinstance(sc_data[key], float), f"{sc_name}.{key} is not float"

    def test_empty_df(self):
        df = pd.DataFrame(columns=["scenario", "weight", "avg_pd_multiplier",
                                    "avg_lgd_multiplier", "pd_vol", "lgd_vol"])
        result = _build_scenario_map(df)
        assert result == {}

    def test_single_scenario(self):
        df = self._make_df([
            {"scenario": "only", "weight": 1.0, "avg_pd_multiplier": 1.0,
             "avg_lgd_multiplier": 1.0, "pd_vol": 0.05, "lgd_vol": 0.03},
        ])
        result = _build_scenario_map(df)
        assert len(result) == 1
        assert "only" in result

    def test_eight_scenarios(self):
        scenarios = [
            {"scenario": f"sc_{i}", "weight": 1.0 / 8, "avg_pd_multiplier": 1.0 + i * 0.1,
             "avg_lgd_multiplier": 1.0 + i * 0.05, "pd_vol": 0.05, "lgd_vol": 0.03}
            for i in range(8)
        ]
        result = _build_scenario_map(pd.DataFrame(scenarios))
        assert len(result) == 8

    def test_preserves_extreme_values(self):
        df = self._make_df([
            {"scenario": "extreme", "weight": 0.01, "avg_pd_multiplier": 5.0,
             "avg_lgd_multiplier": 3.0, "pd_vol": 0.50, "lgd_vol": 0.40},
        ])
        result = _build_scenario_map(df)
        assert result["extreme"]["pd_mult"] == 5.0
        assert result["extreme"]["lgd_mult"] == 3.0

    def test_zero_weight_scenario(self):
        df = self._make_df([
            {"scenario": "zero_w", "weight": 0.0, "avg_pd_multiplier": 1.0,
             "avg_lgd_multiplier": 1.0, "pd_vol": 0.05, "lgd_vol": 0.03},
        ])
        result = _build_scenario_map(df)
        assert result["zero_w"]["weight"] == 0.0

    def test_output_keys(self):
        result = _build_scenario_map(self._make_df())
        for sc_data in result.values():
            assert set(sc_data.keys()) == {"weight", "pd_mult", "lgd_mult", "pd_vol", "lgd_vol"}
