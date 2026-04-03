"""Tests for domain/markov.py — Markov transition matrices and lifetime PD."""
import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


@pytest.fixture
def _patch_db():
    with patch("domain.markov.query_df") as mock_q, \
         patch("domain.markov.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


class TestMatMult:
    def test_identity(self):
        from domain.markov import _mat_mult
        I = [[1, 0], [0, 1]]
        A = [[3, 4], [5, 6]]
        assert _mat_mult(I, A) == A

    def test_known_result(self):
        from domain.markov import _mat_mult
        A = [[1, 2], [3, 4]]
        B = [[5, 6], [7, 8]]
        result = _mat_mult(A, B)
        assert result == [[19, 22], [43, 50]]

    def test_zero_matrix(self):
        from domain.markov import _mat_mult
        Z = [[0, 0], [0, 0]]
        A = [[1, 2], [3, 4]]
        assert _mat_mult(Z, A) == Z

    def test_3x3(self):
        from domain.markov import _mat_mult
        A = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        B = [[2, 3, 4], [5, 6, 7], [8, 9, 10]]
        assert _mat_mult(A, B) == B


class TestMatPower:
    def test_power_zero_is_identity(self):
        from domain.markov import _mat_power
        A = [[0.9, 0.1], [0.2, 0.8]]
        result = _mat_power(A, 0)
        assert result == [[1.0, 0.0], [0.0, 1.0]]

    def test_power_one_is_same(self):
        from domain.markov import _mat_power
        A = [[0.9, 0.1], [0.2, 0.8]]
        result = _mat_power(A, 1)
        for i in range(2):
            for j in range(2):
                assert abs(result[i][j] - A[i][j]) < 1e-10

    def test_power_two_is_squared(self):
        from domain.markov import _mat_power, _mat_mult
        A = [[0.9, 0.1], [0.2, 0.8]]
        expected = _mat_mult(A, A)
        result = _mat_power(A, 2)
        for i in range(2):
            for j in range(2):
                assert abs(result[i][j] - expected[i][j]) < 1e-10

    def test_stochastic_stays_stochastic(self):
        from domain.markov import _mat_power
        P = [[0.7, 0.2, 0.1], [0.1, 0.6, 0.3], [0.0, 0.0, 1.0]]
        result = _mat_power(P, 10)
        for row in result:
            assert abs(sum(row) - 1.0) < 1e-8

    def test_absorbing_state_preserved(self):
        from domain.markov import _mat_power
        P = [[0.8, 0.1, 0.1, 0.0],
             [0.0, 0.7, 0.2, 0.1],
             [0.0, 0.0, 0.5, 0.5],
             [0.0, 0.0, 0.0, 1.0]]
        result = _mat_power(P, 20)
        assert abs(result[3][3] - 1.0) < 1e-10
        assert abs(result[3][0]) < 1e-10

    def test_large_exponent(self):
        from domain.markov import _mat_power
        P = [[0.9, 0.1], [0.3, 0.7]]
        result = _mat_power(P, 100)
        assert abs(result[0][0] - 0.75) < 0.01
        assert abs(result[0][1] - 0.25) < 0.01


class TestEstimateTransitionMatrix:
    def test_with_migration_data(self, _patch_db):
        from domain.markov import estimate_transition_matrix
        mig_data = pd.DataFrame({
            "original_stage": [1, 1, 2, 2, 3],
            "assessed_stage": [1, 2, 2, 3, 3],
            "loan_count": [900, 100, 700, 300, 500],
        })
        defaults_count = pd.DataFrame([{"default_count": 150}])
        stage_data = pd.DataFrame({
            "assessed_stage": [1, 2, 3],
            "cnt": [5000, 2000, 1000],
        })
        result_row = pd.DataFrame([{
            "matrix_id": "test-id",
            "model_name": "TM-All-All",
            "matrix_data": json.dumps({
                "states": ["Stage 1", "Stage 2", "Stage 3", "Default"],
                "matrix": [[0.9, 0.1, 0.0, 0.0], [0.0, 0.7, 0.3, 0.0],
                           [0.0, 0.0, 0.8, 0.2], [0.0, 0.0, 0.0, 1.0]],
            }),
            "n_observations": 2500,
        }])
        _patch_db["query_df"].side_effect = [mig_data, defaults_count, stage_data, result_row]
        result = estimate_transition_matrix()
        assert result is not None
        assert _patch_db["execute"].called

    def test_empty_migration_data(self, _patch_db):
        from domain.markov import estimate_transition_matrix
        empty = pd.DataFrame()
        defaults_empty = pd.DataFrame([{"default_count": 0}])
        stage_empty = pd.DataFrame()
        result_row = pd.DataFrame([{
            "matrix_id": "test-id",
            "model_name": "TM-All-All",
            "matrix_data": json.dumps({
                "states": ["Stage 1", "Stage 2", "Stage 3", "Default"],
                "matrix": [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]],
            }),
            "n_observations": 0,
        }])
        _patch_db["query_df"].side_effect = [empty, defaults_empty, stage_empty, result_row]
        result = estimate_transition_matrix()
        assert result is not None


class TestGetTransitionMatrix:
    def test_found(self, _patch_db):
        from domain.markov import get_transition_matrix
        row = pd.DataFrame([{
            "matrix_id": "m1",
            "model_name": "TM-All",
            "matrix_data": json.dumps({"states": ["S1"], "matrix": [[1.0]]}),
        }])
        _patch_db["query_df"].return_value = row
        result = get_transition_matrix("m1")
        assert result["matrix_id"] == "m1"
        assert isinstance(result["matrix_data"], dict)

    def test_not_found(self, _patch_db):
        from domain.markov import get_transition_matrix
        result = get_transition_matrix("nonexistent")
        assert result is None


class TestListTransitionMatrices:
    def test_empty(self, _patch_db):
        from domain.markov import list_transition_matrices
        assert list_transition_matrices() == []

    def test_with_filter(self, _patch_db):
        from domain.markov import list_transition_matrices
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"matrix_id": "m1", "model_name": "TM-mortgage", "product_type": "mortgage"}
        ])
        result = list_transition_matrices("mortgage")
        assert len(result) == 1
        assert result[0]["product_type"] == "mortgage"


class TestForecastStageDistribution:
    def test_basic_forecast(self, _patch_db):
        from domain.markov import forecast_stage_distribution
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["S1", "S2", "S3", "Default"],
                "matrix": [[0.9, 0.08, 0.02, 0.0],
                           [0.05, 0.8, 0.1, 0.05],
                           [0.0, 0.05, 0.7, 0.25],
                           [0.0, 0.0, 0.0, 1.0]],
            }),
        }])
        _patch_db["query_df"].return_value = mat_row
        result = forecast_stage_distribution("m1", [0.7, 0.2, 0.1, 0.0], 6)
        assert result["horizon_months"] == 6
        points = result["forecast_data"]["points"]
        assert len(points) == 7
        assert points[0]["month"] == 0

    def test_normalizes_input(self, _patch_db):
        from domain.markov import forecast_stage_distribution
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["S1", "S2"],
                "matrix": [[0.9, 0.1], [0.2, 0.8]],
            }),
        }])
        _patch_db["query_df"].return_value = mat_row
        result = forecast_stage_distribution("m1", [2.0, 8.0], 3)
        init = result["forecast_data"]["initial_distribution"]
        assert abs(sum(init) - 1.0) < 1e-10

    def test_missing_matrix_raises(self, _patch_db):
        from domain.markov import forecast_stage_distribution
        with pytest.raises(ValueError, match="not found"):
            forecast_stage_distribution("bad-id", [1.0], 6)


class TestComputeLifetimePd:
    def test_basic(self, _patch_db):
        from domain.markov import compute_lifetime_pd
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["Stage 1", "Stage 2", "Stage 3", "Default"],
                "matrix": [[0.9, 0.05, 0.03, 0.02],
                           [0.02, 0.8, 0.1, 0.08],
                           [0.0, 0.02, 0.7, 0.28],
                           [0.0, 0.0, 0.0, 1.0]],
            }),
        }])
        _patch_db["query_df"].return_value = mat_row
        result = compute_lifetime_pd("m1", max_months=12)
        assert "Stage 1" in result["pd_curves"]
        curve = result["pd_curves"]["Stage 1"]
        assert len(curve) == 13
        assert curve[0]["cumulative_pd"] == 0.0
        assert curve[-1]["cumulative_pd"] > 0

    def test_cumulative_pd_increases(self, _patch_db):
        from domain.markov import compute_lifetime_pd
        mat_row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({
                "states": ["Stage 1", "Stage 2", "Default"],
                "matrix": [[0.9, 0.05, 0.05],
                           [0.0, 0.8, 0.2],
                           [0.0, 0.0, 1.0]],
            }),
        }])
        _patch_db["query_df"].return_value = mat_row
        result = compute_lifetime_pd("m1", max_months=24)
        curve = result["pd_curves"]["Stage 1"]
        for i in range(1, len(curve)):
            assert curve[i]["cumulative_pd"] >= curve[i - 1]["cumulative_pd"]


class TestCompareMatrices:
    def test_empty_list(self, _patch_db):
        from domain.markov import compare_matrices
        assert compare_matrices([]) == []

    def test_returns_found_matrices(self, _patch_db):
        from domain.markov import compare_matrices
        row = pd.DataFrame([{
            "matrix_id": "m1",
            "matrix_data": json.dumps({"states": ["S1"], "matrix": [[1.0]]}),
        }])
        _patch_db["query_df"].return_value = row
        result = compare_matrices(["m1"])
        assert len(result) == 1
