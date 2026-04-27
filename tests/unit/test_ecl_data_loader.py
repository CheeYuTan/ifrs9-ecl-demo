"""Tests for ecl/data_loader.py — loan and scenario data loading."""

import pandas as pd
import pytest
from unittest.mock import patch

from ecl.data_loader import _load_loans, _load_scenarios


class TestLoadLoans:
    def test_returns_dataframe(self):
        expected = pd.DataFrame({
            "loan_id": ["LN-001", "LN-002"],
            "product_type": ["Mortgage", "Auto"],
            "assessed_stage": [1, 2],
            "gross_carrying_amount": [100_000.0, 25_000.0],
            "effective_interest_rate": [0.05, 0.08],
            "current_lifetime_pd": [0.01, 0.05],
            "remaining_months": [120, 36],
        })
        with patch("ecl.data_loader.backend") as mock_be:
            mock_be.query_df.return_value = expected
            result = _load_loans()
            assert len(result) == 2
            assert list(result.columns) == list(expected.columns)

    def test_empty_result(self):
        with patch("ecl.data_loader.backend") as mock_be:
            mock_be.query_df.return_value = pd.DataFrame()
            result = _load_loans()
            assert result.empty

    def test_uses_correct_table(self):
        with patch("ecl.data_loader.backend") as mock_be, \
             patch("ecl.data_loader._t", return_value="schema.ecl_model_ready_loans"):
            mock_be.query_df.return_value = pd.DataFrame()
            _load_loans()
            call_args = mock_be.query_df.call_args[0][0]
            assert "schema.ecl_model_ready_loans" in call_args


class TestLoadScenarios:
    def test_returns_dataframe_with_all_columns(self):
        df = pd.DataFrame({
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
        with patch("ecl.data_loader.backend") as mock_be:
            mock_be.query_df.return_value = df
            result = _load_scenarios()
            assert len(result) == 2
            assert "avg_pd_multiplier" in result.columns

    def test_adds_missing_columns_with_defaults(self):
        df = pd.DataFrame({
            "scenario": ["base"],
            "weight": [1.0],
            "ecl_mean": [100_000.0],
            "ecl_p50": [95_000.0],
            "ecl_p75": [110_000.0],
            "ecl_p95": [130_000.0],
            "ecl_p99": [150_000.0],
        })
        with patch("ecl.data_loader.backend") as mock_be:
            mock_be.query_df.return_value = df
            result = _load_scenarios()
            assert result.iloc[0]["avg_pd_multiplier"] == 1.0
            assert result.iloc[0]["avg_lgd_multiplier"] == 1.0
            assert result.iloc[0]["pd_vol"] == 0.05
            assert result.iloc[0]["lgd_vol"] == 0.03

    def test_preserves_existing_columns(self):
        df = pd.DataFrame({
            "scenario": ["base"],
            "weight": [1.0],
            "ecl_mean": [100_000.0],
            "ecl_p50": [95_000.0],
            "ecl_p75": [110_000.0],
            "ecl_p95": [130_000.0],
            "ecl_p99": [150_000.0],
            "avg_pd_multiplier": [2.0],
            "avg_lgd_multiplier": [1.5],
            "pd_vol": [0.10],
            "lgd_vol": [0.08],
        })
        with patch("ecl.data_loader.backend") as mock_be:
            mock_be.query_df.return_value = df
            result = _load_scenarios()
            assert result.iloc[0]["avg_pd_multiplier"] == 2.0
            assert result.iloc[0]["lgd_vol"] == 0.08

    def test_empty_result(self):
        df = pd.DataFrame(columns=["scenario", "weight", "ecl_mean", "ecl_p50", "ecl_p75", "ecl_p95", "ecl_p99"])
        with patch("ecl.data_loader.backend") as mock_be:
            mock_be.query_df.return_value = df
            result = _load_scenarios()
            assert "avg_pd_multiplier" in result.columns
            assert len(result) == 0
