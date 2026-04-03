"""
Unit tests for the Lakebase backend module.

All database interactions are mocked via psycopg2 connection pool patches.
Tests cover query execution, workflow state management, and error handling.

NOTE: Domain modules (domain.workflow, domain.model_runs, etc.) import
query_df/execute directly from db.pool, so we must patch db.pool functions
for those calls to be intercepted properly.
"""
import json
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone


class TestIsAuthError:
    """Test _is_auth_error recognizes various authentication failure messages."""

    @pytest.fixture(autouse=True)
    def _import_backend(self):
        import backend
        self.backend = backend

    @pytest.mark.parametrize("msg", [
        "FATAL: password authentication failed for user",
        "invalid authorization specification",
        "token expired",
        "token is expired",
        "ssl connection has been closed unexpectedly",
        "connection reset by peer",
        "server closed the connection unexpectedly",
        "FATAL: login failed",
    ])
    def test_recognizes_auth_errors(self, msg):
        exc = Exception(msg)
        assert self.backend._is_auth_error(exc) is True

    @pytest.mark.parametrize("msg", [
        "relation does not exist",
        "syntax error at or near SELECT",
        "division by zero",
        "column 'foo' does not exist",
    ])
    def test_rejects_non_auth_errors(self, msg):
        exc = Exception(msg)
        assert self.backend._is_auth_error(exc) is False


class TestQueryDf:
    """Test query_df returns DataFrame and handles errors."""

    def test_returns_dataframe(self):
        import backend
        import db.pool as pool_mod

        mock_cursor = MagicMock()
        mock_cursor.description = [
            MagicMock(name="col_a"),
            MagicMock(name="col_b"),
        ]
        mock_cursor.description[0].name = "col_a"
        mock_cursor.description[1].name = "col_b"
        mock_cursor.fetchall.return_value = [(1, "x"), (2, "y")]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch.object(pool_mod, "_pool", mock_pool):
            df = backend.query_df("SELECT col_a, col_b FROM test")

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["col_a", "col_b"]
        assert len(df) == 2

    def test_passes_params(self):
        import backend
        import db.pool as pool_mod

        mock_cursor = MagicMock()
        mock_cursor.description = [MagicMock()]
        mock_cursor.description[0].name = "id"
        mock_cursor.fetchall.return_value = [(1,)]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch.object(pool_mod, "_pool", mock_pool):
            backend.query_df("SELECT * FROM t WHERE id = %s", (42,))

        mock_cursor.execute.assert_called_once_with("SELECT * FROM t WHERE id = %s", (42,))


class TestExecute:
    """Test execute commits and handles errors."""

    def test_commits_on_success(self):
        import backend
        import db.pool as pool_mod

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        mock_pool = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch.object(pool_mod, "_pool", mock_pool):
            backend.execute("INSERT INTO t VALUES (%s)", ("val",))

        mock_conn.commit.assert_called_once()


class TestEnsureWorkflowTable:
    """Test ensure_workflow_table creates the table."""

    def test_calls_execute_with_create_table(self):
        import backend

        with patch("domain.workflow.execute") as mock_exec:
            backend.ensure_workflow_table()

        assert mock_exec.call_count >= 1
        sql = mock_exec.call_args_list[0][0][0]
        assert "CREATE TABLE IF NOT EXISTS" in sql
        assert "ecl_workflow" in sql


class TestGetProject:
    """Test get_project with mocked queries."""

    def test_returns_none_for_missing_project(self):
        import backend

        with patch("domain.workflow.query_df", return_value=pd.DataFrame()):
            result = backend.get_project("nonexistent")

        assert result is None

    def test_returns_parsed_project(self):
        import backend

        step_status = json.dumps({s: "pending" for s in backend.STEPS})
        audit_log = json.dumps([{"ts": "2025-01-01", "action": "Created"}])

        df = pd.DataFrame([{
            "project_id": "proj-1",
            "project_name": "Test",
            "project_type": "ifrs9",
            "description": "desc",
            "reporting_date": "2025-12-31",
            "current_step": 1,
            "step_status": step_status,
            "audit_log": audit_log,
            "overlays": "[]",
            "scenario_weights": "{}",
            "signed_off_by": None,
            "signed_off_at": None,
            "created_at": "2025-01-01",
            "updated_at": "2025-01-01",
        }])

        with patch("domain.workflow.query_df", return_value=df):
            result = backend.get_project("proj-1")

        assert result is not None
        assert result["project_id"] == "proj-1"
        assert isinstance(result["step_status"], dict)
        assert isinstance(result["audit_log"], list)


class TestCreateProject:
    """Test create_project."""

    def test_creates_and_returns_project(self):
        import backend

        step_status = {s: "pending" for s in backend.STEPS}
        step_status["create_project"] = "completed"
        project_dict = {
            "project_id": "new-proj",
            "project_name": "New Project",
            "project_type": "ifrs9",
            "description": "test",
            "reporting_date": "2025-12-31",
            "current_step": 1,
            "step_status": step_status,
            "audit_log": [{"ts": "2025-01-01", "action": "Project Created"}],
            "overlays": [],
            "scenario_weights": {},
            "signed_off_by": None,
            "signed_off_at": None,
        }

        with patch("domain.workflow.execute"), \
             patch("domain.workflow.get_project", return_value=project_dict):
            result = backend.create_project("new-proj", "New Project", "ifrs9", "test", "2025-12-31")

        assert result["project_id"] == "new-proj"
        assert result["step_status"]["create_project"] == "completed"


class TestAdvanceStep:
    """Test advance_step with mocked queries."""

    def test_advances_step_successfully(self):
        import backend
        from tests.conftest import _make_workflow_project

        proj = _make_workflow_project()
        updated_proj = {**proj, "current_step": 2,
                        "step_status": {**proj["step_status"], "data_processing": "completed"}}

        call_count = [0]
        def mock_get_project(pid):
            call_count[0] += 1
            if call_count[0] == 1:
                return proj
            return updated_proj

        with patch("domain.workflow.execute"), \
             patch("domain.workflow.get_project", side_effect=mock_get_project):
            result = backend.advance_step(
                "test-proj-001", "data_processing", "Data Processed",
                "Analyst", "Processing complete"
            )

        assert result["current_step"] == 2

    def test_raises_for_missing_project(self):
        import backend

        with patch("domain.workflow.get_project", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                backend.advance_step("missing", "data_processing", "act", "user", "detail")


class TestGetSatelliteModelComparison:
    """Test get_satellite_model_comparison with and without run_id."""

    def test_without_run_id(self):
        import backend

        df = pd.DataFrame({
            "product_type": ["credit_builder"],
            "cohort_id": ["cohort_1"],
            "model_type": ["linear_regression"],
            "r_squared": [0.85],
            "rmse": [0.02],
            "aic": [-100.0],
            "bic": [-95.0],
            "cv_rmse": [None],
            "coefficients_json": ['{"intercept": 0.01}'],
            "formula": ["PD = 0.01 + ..."],
            "n_observations": [200],
            "run_timestamp": ["2025-01-01"],
        })

        with patch("domain.model_runs.query_df", return_value=df) as mock_q:
            result = backend.get_satellite_model_comparison()

        assert len(result) == 1
        call_sql = mock_q.call_args[0][0]
        assert "WHERE run_timestamp" not in call_sql

    def test_with_run_id(self):
        import backend

        df = pd.DataFrame({
            "product_type": ["credit_builder"],
            "cohort_id": ["cohort_1"],
            "model_type": ["ridge_regression"],
            "r_squared": [0.82],
            "rmse": [0.025],
            "aic": [-90.0],
            "bic": [-85.0],
            "cv_rmse": [None],
            "coefficients_json": ['{"intercept": 0.02}'],
            "formula": ["PD = 0.02 + ..."],
            "n_observations": [200],
            "run_timestamp": ["2025-06-15"],
        })

        with patch("domain.model_runs.query_df", return_value=df) as mock_q:
            result = backend.get_satellite_model_comparison(run_id="2025-06-15")

        call_sql = mock_q.call_args[0][0]
        assert "WHERE run_timestamp" in call_sql
