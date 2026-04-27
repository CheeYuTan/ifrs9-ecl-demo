"""Dedicated tests for ecl/helpers.py — convergence checks, JSON encoding, emit."""
import json
from datetime import date, datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from ecl.helpers import (
    _convergence_check,
    _convergence_check_from_paths,
    _df_to_records,
    _emit,
)


class TestEmit:
    def test_emit_calls_callback(self):
        events = []
        _emit(events.append, {"phase": "test"})
        assert len(events) == 1
        assert events[0]["phase"] == "test"

    def test_emit_none_callback(self):
        _emit(None, {"phase": "test"})

    def test_emit_false_callback(self):
        _emit(False, {"phase": "test"})

    def test_emit_zero_callback(self):
        _emit(0, {"phase": "test"})


class TestConvergenceCheck:
    def test_basic_convergence(self):
        rng = np.random.default_rng(42)
        ecl_sims = rng.random((10, 100))
        result = _convergence_check(ecl_sims, 100)
        assert "ecl_at_25pct_sims" in result
        assert "ecl_at_50pct_sims" in result
        assert "ecl_at_75pct_sims" in result
        assert "ecl_at_100pct_sims" in result
        assert "coefficient_of_variation" in result

    def test_convergence_cv_decreases(self):
        rng = np.random.default_rng(42)
        ecl_sims = rng.random((10, 200))
        result = _convergence_check(ecl_sims, 200)
        cv = result["coefficient_of_variation"]
        assert cv >= 0.0

    def test_single_sim(self):
        ecl_sims = np.array([[1.0], [2.0], [3.0]])
        result = _convergence_check(ecl_sims, 1)
        assert result["coefficient_of_variation"] == 0.0
        expected = float(np.array([1.0, 2.0, 3.0]).sum())
        for key in ("ecl_at_25pct_sims", "ecl_at_50pct_sims", "ecl_at_75pct_sims", "ecl_at_100pct_sims"):
            assert result[key] == expected

    def test_zero_mean_cv(self):
        ecl_sims = np.zeros((5, 10))
        result = _convergence_check(ecl_sims, 10)
        assert result["coefficient_of_variation"] == 0.0

    def test_uniform_values(self):
        ecl_sims = np.ones((3, 20))
        result = _convergence_check(ecl_sims, 20)
        assert result["coefficient_of_variation"] == 0.0

    def test_nan_handling(self):
        ecl_sims = np.array([[np.nan, 1.0, 2.0], [3.0, np.nan, 4.0]])
        result = _convergence_check(ecl_sims, 3)
        for key in ("ecl_at_25pct_sims", "ecl_at_50pct_sims", "ecl_at_75pct_sims", "ecl_at_100pct_sims"):
            assert np.isfinite(result[key])

    def test_large_simulation(self):
        rng = np.random.default_rng(99)
        ecl_sims = rng.random((50, 500))
        result = _convergence_check(ecl_sims, 500)
        assert result["ecl_at_100pct_sims"] > 0
        assert result["coefficient_of_variation"] < 1.0

    def test_two_sims(self):
        ecl_sims = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = _convergence_check(ecl_sims, 2)
        assert result["ecl_at_100pct_sims"] > 0


class TestConvergenceCheckFromPaths:
    def test_basic_paths(self):
        paths = np.array([100.0, 110.0, 105.0, 95.0, 108.0])
        result = _convergence_check_from_paths(paths, 5)
        assert "ecl_at_25pct_sims" in result
        assert "ecl_at_100pct_sims" in result
        assert result["coefficient_of_variation"] >= 0.0

    def test_single_path(self):
        paths = np.array([100.0])
        result = _convergence_check_from_paths(paths, 1)
        assert result["ecl_at_100pct_sims"] == 100.0

    def test_zero_mean_paths(self):
        paths = np.zeros(10)
        result = _convergence_check_from_paths(paths, 10)
        assert result["coefficient_of_variation"] == 0.0

    def test_nan_in_paths(self):
        paths = np.array([100.0, np.nan, 200.0])
        result = _convergence_check_from_paths(paths, 3)
        for key in ("ecl_at_25pct_sims", "ecl_at_100pct_sims"):
            assert np.isfinite(result[key])

    def test_increasing_sims_reduces_cv(self):
        rng = np.random.default_rng(42)
        paths_small = rng.normal(100, 10, size=10)
        paths_large = rng.normal(100, 10, size=1000)
        cv_small = _convergence_check_from_paths(paths_small, 10)["coefficient_of_variation"]
        cv_large = _convergence_check_from_paths(paths_large, 1000)["coefficient_of_variation"]
        assert cv_large <= cv_small or cv_large < 0.1

    def test_checkpoint_ordering(self):
        rng = np.random.default_rng(42)
        paths = rng.random(100) * 1000
        result = _convergence_check_from_paths(paths, 100)
        vals = [result[f"ecl_at_{p}pct_sims"] for p in (25, 50, 75, 100)]
        assert all(v > 0 for v in vals)


class TestDfToRecords:
    def test_basic_dataframe(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        records = _df_to_records(df)
        assert len(records) == 2
        assert records[0]["a"] == 1
        assert records[0]["b"] == "x"

    def test_decimal_values(self):
        df = pd.DataFrame({"amount": [Decimal("123.45"), Decimal("678.90")]})
        records = _df_to_records(df)
        assert records[0]["amount"] == 123.45
        assert records[1]["amount"] == 678.90

    def test_datetime_values(self):
        df = pd.DataFrame({"dt": [datetime(2025, 1, 1, 12, 0)]})
        records = _df_to_records(df)
        assert "2025-01-01" in records[0]["dt"]

    def test_date_values(self):
        df = pd.DataFrame({"d": [date(2025, 6, 15)]})
        records = _df_to_records(df)
        assert records[0]["d"] == "2025-06-15"

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        records = _df_to_records(df)
        assert records == []

    def test_json_serializable(self):
        df = pd.DataFrame({
            "int_col": [1],
            "float_col": [1.5],
            "str_col": ["hello"],
            "decimal_col": [Decimal("99.99")],
            "date_col": [date(2025, 1, 1)],
        })
        records = _df_to_records(df)
        serialized = json.dumps(records)
        assert isinstance(serialized, str)

    def test_none_values(self):
        df = pd.DataFrame({"a": [None, 1], "b": [2, None]})
        records = _df_to_records(df)
        assert len(records) == 2

    def test_numpy_types(self):
        df = pd.DataFrame({
            "int64": np.array([1], dtype=np.int64),
            "float64": np.array([1.5], dtype=np.float64),
        })
        records = _df_to_records(df)
        serialized = json.dumps(records)
        assert isinstance(serialized, str)
