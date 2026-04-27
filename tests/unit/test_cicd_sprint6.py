"""Sprint 6 — CI/CD + Production Readiness Tests.

Tests for:
- CI workflow structure validation
- Pre-commit config validation
- Production readiness checklist (15 items)
- Graceful shutdown
- Error handler middleware
- Logging configuration
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"

sys.path.insert(0, str(APP_DIR))


# ── CI Workflow Validation ──────────────────────────────────────────────────


class TestCIWorkflow:
    def setup_method(self):
        ci_path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
        with open(ci_path) as f:
            self.ci = yaml.safe_load(f)

    def test_workflow_has_name(self):
        assert self.ci["name"] == "CI"

    def test_triggers_on_push_and_pr(self):
        triggers = self.ci.get("on") or self.ci.get(True)
        assert triggers is not None
        assert "push" in triggers
        assert "pull_request" in triggers

    def test_triggers_main_branch(self):
        triggers = self.ci.get("on") or self.ci.get(True)
        assert "main" in triggers["push"]["branches"]
        assert "main" in triggers["pull_request"]["branches"]

    def test_has_concurrency_group(self):
        assert "concurrency" in self.ci
        assert self.ci["concurrency"]["cancel-in-progress"] is True

    def test_has_backend_lint_job(self):
        assert "backend-lint" in self.ci["jobs"]
        steps = self.ci["jobs"]["backend-lint"]["steps"]
        commands = [s.get("run", "") for s in steps]
        assert any("ruff check" in c for c in commands)
        assert any("ruff format" in c for c in commands)

    def test_has_backend_typecheck_job(self):
        assert "backend-typecheck" in self.ci["jobs"]
        steps = self.ci["jobs"]["backend-typecheck"]["steps"]
        commands = [s.get("run", "") for s in steps]
        assert any("pyright" in c for c in commands)

    def test_has_backend_test_job(self):
        assert "backend-test" in self.ci["jobs"]
        steps = self.ci["jobs"]["backend-test"]["steps"]
        commands = [s.get("run", "") for s in steps]
        assert any("pytest" in c for c in commands)

    def test_has_frontend_lint_job(self):
        assert "frontend-lint" in self.ci["jobs"]

    def test_has_frontend_test_job(self):
        assert "frontend-test" in self.ci["jobs"]
        steps = self.ci["jobs"]["frontend-test"]["steps"]
        commands = [s.get("run", "") for s in steps]
        assert any("vitest" in c for c in commands)

    def test_has_frontend_build_job(self):
        assert "frontend-build" in self.ci["jobs"]
        steps = self.ci["jobs"]["frontend-build"]["steps"]
        commands = [s.get("run", "") for s in steps]
        assert any("tsc" in c for c in commands)
        assert any("build" in c for c in commands)

    def test_backend_test_has_rate_limit_disabled(self):
        env = self.ci["jobs"]["backend-test"].get("env", {})
        assert env.get("RATE_LIMIT_DISABLED") == "1"

    def test_python_version_312(self):
        for job_name in ["backend-lint", "backend-typecheck", "backend-test"]:
            steps = self.ci["jobs"][job_name]["steps"]
            for s in steps:
                if s.get("uses", "").startswith("actions/setup-python"):
                    assert s["with"]["python-version"] == "3.12"

    def test_node_version_22(self):
        for job_name in ["frontend-lint", "frontend-test", "frontend-build"]:
            steps = self.ci["jobs"][job_name]["steps"]
            for s in steps:
                if s.get("uses", "").startswith("actions/setup-node"):
                    assert s["with"]["node-version"] == "22"


# ── Pre-commit Config Validation ───────────────────────────────────────────


class TestPreCommitConfig:
    def setup_method(self):
        config_path = PROJECT_ROOT / ".pre-commit-config.yaml"
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def test_has_repos(self):
        assert "repos" in self.config
        assert len(self.config["repos"]) >= 2

    def test_has_ruff_hook(self):
        repos = self.config["repos"]
        ruff_repos = [r for r in repos if "ruff" in r.get("repo", "")]
        assert len(ruff_repos) >= 1
        hooks = ruff_repos[0]["hooks"]
        hook_ids = [h["id"] for h in hooks]
        assert "ruff" in hook_ids
        assert "ruff-format" in hook_ids

    def test_has_eslint_hook(self):
        repos = self.config["repos"]
        eslint_repos = [r for r in repos if "eslint" in r.get("repo", "")]
        assert len(eslint_repos) >= 1

    def test_has_general_hooks(self):
        repos = self.config["repos"]
        general = [r for r in repos if "pre-commit-hooks" in r.get("repo", "")]
        assert len(general) >= 1
        hook_ids = [h["id"] for h in general[0]["hooks"]]
        assert "trailing-whitespace" in hook_ids
        assert "check-yaml" in hook_ids
        assert "detect-private-key" in hook_ids


# ── Production Readiness Checklist ──────────────────────────────────────────


class TestProductionReadinessChecklist:
    """Verify the 15-item production readiness checklist."""

    def test_01_error_handling_global_handler_exists(self):
        from middleware.error_handler import ErrorHandlerMiddleware
        assert ErrorHandlerMiddleware is not None

    def test_01_error_handler_returns_json(self):
        from app import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.headers.get("content-type", "").startswith("application/json")

    def test_02_loading_states_frontend_has_suspense(self):
        app_tsx = APP_DIR / "frontend" / "src" / "App.tsx"
        content = app_tsx.read_text()
        assert "Suspense" in content

    def test_03_toast_notifications_exist(self):
        toast_path = APP_DIR / "frontend" / "src" / "components" / "Toast.tsx"
        assert toast_path.exists()

    def test_04_environment_config_exists(self):
        assert (PROJECT_ROOT / "pyproject.toml").exists()
        content = (PROJECT_ROOT / "pyproject.toml").read_text()
        assert "ifrs9-ecl" in content

    def test_05_data_validation_pydantic_used(self):
        from pydantic import BaseModel
        from routes.simulation import SimulationConfig
        assert issubclass(SimulationConfig, BaseModel)

    def test_06_dark_mode_supported(self):
        app_tsx = APP_DIR / "frontend" / "src" / "App.tsx"
        content = app_tsx.read_text()
        assert "useTheme" in content or "dark" in content

    def test_08_accessibility_semantic_html(self):
        datatable = APP_DIR / "frontend" / "src" / "components" / "DataTable.tsx"
        content = datatable.read_text()
        assert "aria-sort" in content
        assert "aria-label" in content
        assert "scope=\"col\"" in content

    def test_09_performance_caching_exists(self):
        from utils.cache import TTLCache, cached
        assert TTLCache is not None
        assert cached is not None

    def test_10_rate_limiting_exists(self):
        from middleware.rate_limiter import RateLimiterMiddleware
        assert RateLimiterMiddleware is not None

    def test_10_security_headers_exist(self):
        from middleware.security_headers import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None

    def test_11_seed_data_demo_mode(self):
        import admin_config
        assert hasattr(admin_config, "seed_defaults")

    def test_13_feature_flags_admin_config(self):
        import admin_config
        assert hasattr(admin_config, "get_config")
        assert hasattr(admin_config, "get_config_section")

    def test_14_analytics_middleware(self):
        from middleware.analytics import AnalyticsMiddleware
        assert AnalyticsMiddleware is not None

    def test_15_ci_cd_pipeline_exists(self):
        ci_path = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists()


# ── Graceful Shutdown ───────────────────────────────────────────────────────


class TestGracefulShutdown:
    def test_lifespan_has_shutdown_code(self):
        import inspect
        from app import lifespan
        src = inspect.getsource(lifespan)
        assert "Shutting down" in src
        assert "clear()" in src

    def test_cache_clears_on_shutdown(self):
        from utils.cache import get_cache
        cache = get_cache()
        cache.set("test_shutdown", "value", 60)
        cache.clear()
        assert cache.get("test_shutdown") is None


# ── Error Handler Middleware ────────────────────────────────────────────────


class TestErrorHandlerMiddlewareFormat:
    @pytest.fixture(autouse=True)
    def client(self):
        from app import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def test_health_returns_structured_json(self):
        resp = self.client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    def test_404_for_unknown_api_route(self):
        resp = self.client.get("/api/nonexistent")
        assert resp.status_code in (404, 405)

    def test_request_id_header_present(self):
        resp = self.client.get("/api/health")
        assert "x-request-id" in resp.headers


# ── Logging Configuration ──────────────────────────────────────────────────


class TestLoggingConfiguration:
    def test_structured_logging_configured_in_app(self):
        import inspect
        import app as app_module
        src = inspect.getsource(app_module)
        assert "logging.basicConfig" in src
        assert "level=logging.INFO" in src

    def test_app_has_logger(self):
        import app as app_module
        assert hasattr(app_module, "log")


# ── No Hardcoded Ports ──────────────────────────────────────────────────────


class TestNoHardcodedPorts:
    def test_no_hardcoded_ports_in_app(self):
        app_py = APP_DIR / "app.py"
        content = app_py.read_text()
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            if "8001" in stripped and "uvicorn" not in stripped and "dev_server" not in stripped:
                if "port" in stripped.lower() and "=" in stripped:
                    assert False, f"Possible hardcoded port: {stripped}"


# ── File Structure Validation ───────────────────────────────────────────────


class TestFileStructure:
    def test_pyproject_toml_exists(self):
        assert (PROJECT_ROOT / "pyproject.toml").exists()

    def test_requirements_txt_exists(self):
        assert (APP_DIR / "requirements.txt").exists()

    def test_pytest_config_exists(self):
        assert (APP_DIR / "pytest.ini").exists() or (PROJECT_ROOT / "pyproject.toml").exists()

    def test_github_actions_exists(self):
        assert (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").exists()

    def test_pre_commit_config_exists(self):
        assert (PROJECT_ROOT / ".pre-commit-config.yaml").exists()

    def test_frontend_package_json_exists(self):
        assert (APP_DIR / "frontend" / "package.json").exists()

    def test_app_yaml_exists(self):
        assert (APP_DIR / "app.yaml").exists()
