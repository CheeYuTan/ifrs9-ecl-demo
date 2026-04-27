"""Extended tests for ecl/helpers.py — convergence checks and emit edge cases."""
import numpy as np
import pandas as pd
import pytest
from decimal import Decimal
from datetime import datetime, date

from ecl.helpers import _convergence_check, _convergence_check_from_paths, _df_to_records, _emit


class TestEmitExtended:
    def test_emit_with_complex_dict(self):
        events = []
        _emit(events.append, {"phase": "test", "nested": {"a": 1, "b": [2, 3]}})
        assert events[0]["nested"]["a"] == 1

    def test_emit_with_string_message(self):
        events = []
        _emit(events.append, "simple string message")
        assert events[0] == "simple string message"

    def test_emit_with_integer(self):
        events = []
        _emit(events.append, 42)
        assert events[0] == 42

    def test_emit_with_list(self):
        events = []
        _emit(events.append, [1, 2, 3])
        assert events[0] == [1, 2, 3]


class TestConvergenceCheckExtended:
    def test_returns_checkpoints(self):
        ecl_sims = np.random.default_rng(42).random((5, 100)) * 1000
        result = _convergence_check(ecl_sims, 100)
        assert "ecl_at_25pct_sims" in result
        assert "ecl_at_50pct_sims" in result
        assert "ecl_at_100pct_sims" in result

    def test_coefficient_of_variation(self):
        ecl_sims = np.random.default_rng(42).random((5, 100)) * 1000
        result = _convergence_check(ecl_sims, 100)
        assert "coefficient_of_variation" in result
        assert isinstance(result["coefficient_of_variation"], float)

    def test_single_sim(self):
        ecl_sims = np.random.default_rng(42).random((5, 1)) * 1000
        result = _convergence_check(ecl_sims, 1)
        assert result["coefficient_of_variation"] == 0.0

    def test_convergence_improves_with_more_sims(self):
        ecl_sims = np.random.default_rng(42).random((5, 1000)) * 1000
        result = _convergence_check(ecl_sims, 1000)
        assert result["coefficient_of_variation"] < 0.5


class TestConvergenceCheckFromPathsExtended:
    def test_uniform_paths(self):
        paths = np.ones(100) * 5000
        result = _convergence_check_from_paths(paths, 100)
        assert result["coefficient_of_variation"] < 0.01

    def test_high_variance_paths(self):
        rng = np.random.default_rng(42)
        paths = rng.normal(5000, 2000, 500)
        result = _convergence_check_from_paths(paths, 500)
        assert "ecl_at_100pct_sims" in result

    def test_single_path(self):
        result = _convergence_check_from_paths(np.array([5000.0]), 1)
        assert result["ecl_at_100pct_sims"] == 5000.0

    def test_returns_all_checkpoints(self):
        paths = np.random.default_rng(42).random(200) * 10000
        result = _convergence_check_from_paths(paths, 200)
        for pct in (25, 50, 75, 100):
            assert f"ecl_at_{pct}pct_sims" in result


class TestDfToRecordsExtended:
    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["a", "b"])
        result = _df_to_records(df)
        assert result == []

    def test_with_none_values(self):
        df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", None]})
        result = _df_to_records(df)
        assert len(result) == 3

    def test_with_mixed_types(self):
        df = pd.DataFrame({
            "int_col": [1, 2],
            "float_col": [1.5, 2.5],
            "str_col": ["a", "b"],
        })
        result = _df_to_records(df)
        assert len(result) == 2
        assert result[0]["int_col"] == 1
        assert result[0]["float_col"] == 1.5
        assert result[0]["str_col"] == "a"
