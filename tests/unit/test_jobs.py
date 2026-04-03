"""
Unit tests for Databricks Jobs SDK integration.

All Databricks SDK calls are mocked to avoid hitting real endpoints.
Tests validate the jobs module's public API:
  - _ws_host(), _ws_id()
  - trigger_satellite_ecl_job(), trigger_full_pipeline(), trigger_demo_data_job()
  - get_run_status(), list_job_runs(), get_jobs_status()
  - Job definition builders
"""
import os
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

import jobs


class TestWsHost:
    """Test _ws_host with various configurations."""

    def test_returns_host_from_workspace_client(self):
        mock_client = MagicMock()
        mock_client.config.host = "https://my-workspace.databricks.com/"
        with patch("jobs._get_workspace_client", return_value=mock_client):
            result = jobs._ws_host()
        assert result == "https://my-workspace.databricks.com"

    def test_strips_trailing_slash(self):
        mock_client = MagicMock()
        mock_client.config.host = "https://example.databricks.com///"
        with patch("jobs._get_workspace_client", return_value=mock_client):
            result = jobs._ws_host()
        assert not result.endswith("/")

    def test_falls_back_to_env_var(self, monkeypatch):
        monkeypatch.setenv("DATABRICKS_HOST", "https://fallback.databricks.com")
        with patch("jobs._get_workspace_client", side_effect=Exception("no client")):
            # Also ensure admin_config import fails
            with patch.dict("sys.modules", {"admin_config": None}):
                result = jobs._ws_host()
        assert result == "https://fallback.databricks.com"


class TestWsId:
    """Test _ws_id retrieval."""

    def test_returns_from_env(self, monkeypatch):
        monkeypatch.setenv("DATABRICKS_WORKSPACE_ID", "12345")
        with patch.dict("sys.modules", {"admin_config": None}):
            result = jobs._ws_id()
        assert result == "12345"


class TestAllModels:
    """Test ALL_MODELS constant."""

    def test_all_models_contains_expected(self):
        assert "linear_regression" in jobs.ALL_MODELS
        assert "xgboost" in jobs.ALL_MODELS
        assert len(jobs.ALL_MODELS) == 8


class TestNotebookScripts:
    """Test NOTEBOOK_SCRIPTS mapping."""

    def test_contains_key_scripts(self):
        assert "03a_run_single_model" in jobs.NOTEBOOK_SCRIPTS
        assert "03a_aggregate_models" in jobs.NOTEBOOK_SCRIPTS
        assert "03b_run_ecl_calculation" in jobs.NOTEBOOK_SCRIPTS
        assert "04_sync_to_lakebase" in jobs.NOTEBOOK_SCRIPTS


class TestNbTask:
    """Test _nb_task helper for building task dicts."""

    def test_basic_task(self):
        task = jobs._nb_task("my_task", "/path/to/notebook")
        assert task["task_key"] == "my_task"
        assert task["notebook_task"]["notebook_path"] == "/path/to/notebook"
        assert task["notebook_task"]["source"] == "WORKSPACE"
        assert "depends_on" not in task

    def test_task_with_depends_on(self):
        task = jobs._nb_task("child", "/nb", depends_on=["parent1", "parent2"])
        assert len(task["depends_on"]) == 2
        assert task["depends_on"][0] == {"task_key": "parent1"}

    def test_task_with_base_params(self):
        task = jobs._nb_task("t", "/nb", base_params={"model_name": "xgboost"})
        assert task["notebook_task"]["base_parameters"] == {"model_name": "xgboost"}

    def test_task_with_run_if(self):
        task = jobs._nb_task("t", "/nb", depends_on=["dep"], run_if="ALL_DONE")
        assert task["run_if"] == "ALL_DONE"


class TestBuildJobDefs:
    """Test job definition builder functions."""

    def test_satellite_ecl_job_has_model_tasks(self):
        job_def = jobs._build_satellite_ecl_job_def("/scripts")
        task_keys = [t["task_key"] for t in job_def["tasks"]]
        for m in jobs.ALL_MODELS:
            assert f"model_{m}" in task_keys
        assert "aggregate_models" in task_keys
        assert "ecl_calculation" in task_keys
        assert "sync_to_lakebase" in task_keys

    def test_satellite_ecl_job_has_environments(self):
        job_def = jobs._build_satellite_ecl_job_def("/scripts")
        assert "environments" in job_def
        assert len(job_def["environments"]) >= 1
        assert job_def["environments"][0]["environment_key"] == "ml_env"

    def test_full_pipeline_includes_data_processing(self):
        job_def = jobs._build_full_pipeline_job_def("/scripts")
        task_keys = [t["task_key"] for t in job_def["tasks"]]
        assert "data_processing" in task_keys
        assert "aggregate_models" in task_keys

    def test_demo_data_job_has_generate_and_process(self):
        job_def = jobs._build_demo_data_job_def("/scripts")
        task_keys = [t["task_key"] for t in job_def["tasks"]]
        assert "generate_data" in task_keys
        assert "data_processing" in task_keys
        assert len(job_def["tasks"]) == 2

    def test_full_pipeline_model_tasks_depend_on_data_processing(self):
        job_def = jobs._build_full_pipeline_job_def("/scripts")
        for task in job_def["tasks"]:
            if task["task_key"].startswith("model_"):
                deps = [d["task_key"] for d in task.get("depends_on", [])]
                assert "data_processing" in deps


class TestTriggerSatelliteEclJob:
    """Test trigger_satellite_ecl_job with mocked SDK."""

    def test_trigger_returns_run_id_and_url(self):
        mock_run = MagicMock()
        mock_run.run_id = 12345

        mock_client = MagicMock()
        mock_client.jobs.run_now.return_value = mock_run
        mock_client.config.host = "https://test.databricks.com/"
        mock_client.config.authenticate.return_value = {"Authorization": "Bearer tok"}

        with patch("jobs._get_workspace_client", return_value=mock_client), \
             patch("jobs._ensure_job", return_value=999), \
             patch("jobs._ws_host", return_value="https://test.databricks.com"), \
             patch("jobs._ws_id", return_value="abc123"), \
             patch("jobs._config_params", return_value={}):
            result = jobs.trigger_satellite_ecl_job()

        assert result["run_id"] == 12345
        assert result["job_id"] == 999
        assert "run_url" in result
        assert "12345" in result["run_url"] or str(12345) in str(result["run_url"])
        assert result["models"] == jobs.ALL_MODELS

    def test_trigger_with_custom_models(self):
        mock_run = MagicMock()
        mock_run.run_id = 99999

        mock_client = MagicMock()
        mock_client.jobs.run_now.return_value = mock_run

        with patch("jobs._get_workspace_client", return_value=mock_client), \
             patch("jobs._ensure_job", return_value=100), \
             patch("jobs._ws_host", return_value="https://test.databricks.com"), \
             patch("jobs._ws_id", return_value="abc"), \
             patch("jobs._config_params", return_value={}):
            custom = ["linear_regression", "ridge_regression"]
            result = jobs.trigger_satellite_ecl_job(enabled_models=custom)

        assert result["models"] == custom
        call_kwargs = mock_client.jobs.run_now.call_args
        nb_params = call_kwargs.kwargs.get("notebook_params", {})
        assert nb_params["enabled_models"] == "linear_regression,ridge_regression"

    def test_trigger_raises_on_sdk_error(self):
        mock_client = MagicMock()
        mock_client.jobs.run_now.side_effect = Exception("Job trigger failed")

        with patch("jobs._get_workspace_client", return_value=mock_client), \
             patch("jobs._ensure_job", return_value=100), \
             patch("jobs._config_params", return_value={}):
            with pytest.raises(RuntimeError, match="Failed to trigger job"):
                jobs.trigger_satellite_ecl_job()


class TestTriggerFullPipeline:
    """Test trigger_full_pipeline with mocked SDK."""

    def test_trigger_full_pipeline(self):
        mock_run = MagicMock()
        mock_run.run_id = 67890

        mock_client = MagicMock()
        mock_client.jobs.run_now.return_value = mock_run

        with patch("jobs._get_workspace_client", return_value=mock_client), \
             patch("jobs._ensure_job", return_value=200), \
             patch("jobs._ws_host", return_value="https://test.databricks.com"), \
             patch("jobs._ws_id", return_value="ws1"), \
             patch("jobs._config_params", return_value={}):
            result = jobs.trigger_full_pipeline()

        assert result["run_id"] == 67890
        assert result["job_id"] == 200
        assert "run_url" in result


class TestTriggerDemoDataJob:
    """Test trigger_demo_data_job with mocked SDK."""

    def test_trigger_demo_data(self):
        mock_run = MagicMock()
        mock_run.run_id = 55555

        mock_client = MagicMock()
        mock_client.jobs.run_now.return_value = mock_run

        with patch("jobs._get_workspace_client", return_value=mock_client), \
             patch("jobs._ensure_job", return_value=300), \
             patch("jobs._ws_host", return_value="https://test.databricks.com"), \
             patch("jobs._ws_id", return_value="ws1"), \
             patch("jobs._config_params", return_value={}):
            result = jobs.trigger_demo_data_job()

        assert result["run_id"] == 55555
        assert result["job_id"] == 300
        assert "run_url" in result


class TestGetRunStatus:
    """Test get_run_status response parsing with mocked SDK."""

    def test_parses_response_correctly(self):
        mock_state = MagicMock()
        mock_state.life_cycle_state.value = "TERMINATED"
        mock_state.result_state.value = "SUCCESS"
        mock_state.state_message = "All tasks completed"

        mock_task_state = MagicMock()
        mock_task_state.life_cycle_state.value = "TERMINATED"
        mock_task_state.result_state.value = "SUCCESS"

        mock_task = MagicMock()
        mock_task.task_key = "satellite_models"
        mock_task.state = mock_task_state
        mock_task.run_page_url = "https://example.com/task/1"
        mock_task.execution_duration = 120000

        mock_result = MagicMock()
        mock_result.run_id = 12345
        mock_result.job_id = 999
        mock_result.state = mock_state
        mock_result.run_page_url = "https://example.com/run/12345"
        mock_result.start_time = 1700000000000
        mock_result.end_time = 1700000300000
        mock_result.run_duration = 300000
        mock_result.tasks = [mock_task]

        mock_client = MagicMock()
        mock_client.jobs.get_run.return_value = mock_result

        with patch("jobs._get_workspace_client", return_value=mock_client):
            result = jobs.get_run_status(12345)

        assert result["run_id"] == 12345
        assert result["lifecycle_state"] == "TERMINATED"
        assert result["result_state"] == "SUCCESS"
        assert result["state_message"] == "All tasks completed"
        assert result["run_duration_ms"] == 300000
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["task_key"] == "satellite_models"
        assert result["tasks"][0]["execution_duration_ms"] == 120000

    def test_raises_on_sdk_error(self):
        mock_client = MagicMock()
        mock_client.jobs.get_run.side_effect = Exception("Run not found")

        with patch("jobs._get_workspace_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Failed to get run status"):
                jobs.get_run_status(99999)


class TestListJobRuns:
    """Test list_job_runs with mocked SDK."""

    def test_unknown_job_key_returns_empty(self):
        with patch("jobs._get_job_ids", return_value={}):
            result = jobs.list_job_runs("nonexistent_job")
        assert result == []

    def test_returns_formatted_runs(self):
        mock_state = MagicMock()
        mock_state.life_cycle_state.value = "TERMINATED"
        mock_state.result_state.value = "SUCCESS"
        mock_state.state_message = ""

        mock_run = MagicMock()
        mock_run.run_id = 111
        mock_run.job_id = 500
        mock_run.state = mock_state
        mock_run.run_page_url = "https://example.com/run/111"
        mock_run.start_time = 1700000000000
        mock_run.end_time = 1700000060000
        mock_run.run_duration = 60000

        mock_client = MagicMock()
        mock_client.jobs.list_runs.return_value = iter([mock_run])

        with patch("jobs._get_workspace_client", return_value=mock_client), \
             patch("jobs._get_job_ids", return_value={"satellite_ecl_sync": 500}):
            result = jobs.list_job_runs("satellite_ecl_sync", limit=5)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["run_id"] == 111
        assert result[0]["lifecycle_state"] == "TERMINATED"

    def test_sdk_error_returns_empty(self):
        mock_client = MagicMock()
        mock_client.jobs.list_runs.side_effect = Exception("API error")

        with patch("jobs._get_workspace_client", return_value=mock_client), \
             patch("jobs._get_job_ids", return_value={"my_job": 100}):
            result = jobs.list_job_runs("my_job")
        assert result == []


class TestEnvDict:
    """Test _env_dict helper."""

    def test_returns_environment_spec(self):
        env = jobs._env_dict()
        assert env["environment_key"] == "ml_env"
        assert "spec" in env
        assert "dependencies" in env["spec"]
        assert "scikit-learn" in env["spec"]["dependencies"]
        assert "xgboost" in env["spec"]["dependencies"]
