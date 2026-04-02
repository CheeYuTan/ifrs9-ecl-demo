"""
Sprint 6 QA: Domain Logic — Workflow, Queries, Attribution, Validation

Deep tests of 8 domain modules (first half of domain/):
  - domain/workflow.py: Project state machine, step validation, audit events
  - domain/queries.py: 27 portfolio/ECL aggregation queries
  - domain/model_runs.py: Run history, satellite model queries (gap coverage)
  - domain/attribution.py: Waterfall decomposition (IFRS 7.35I)
  - domain/validation_rules.py: 23+ validation checks (gap coverage)
  - domain/data_mapper.py: Column mapping logic, auto-suggest, validate
  - domain/audit_trail.py: Immutable event logging, chain verification (gap coverage)
  - domain/config_audit.py: Config change tracking, diff (gap coverage)
"""
import json
import hashlib
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest.mock import patch, MagicMock, call, ANY

import numpy as np
import pandas as pd
import pytest

from conftest import PRODUCT_TYPES, SCENARIOS


# ═══════════════════════════════════════════════════════════════════
# Section 1: domain/workflow.py
# ═══════════════════════════════════════════════════════════════════


class TestWorkflowSTEPS:
    """Tests for the STEPS constant and workflow table setup."""

    def test_steps_has_8_entries(self):
        from domain.workflow import STEPS
        assert len(STEPS) == 8

    def test_steps_starts_with_create_project(self):
        from domain.workflow import STEPS
        assert STEPS[0] == "create_project"

    def test_steps_ends_with_sign_off(self):
        from domain.workflow import STEPS
        assert STEPS[-1] == "sign_off"

    def test_steps_contains_required_workflow_stages(self):
        from domain.workflow import STEPS
        required = {"create_project", "data_processing", "data_control",
                    "satellite_model", "model_execution", "stress_testing",
                    "overlays", "sign_off"}
        assert set(STEPS) == required

    def test_steps_order_is_sequential(self):
        from domain.workflow import STEPS
        # data_processing must come before model_execution
        assert STEPS.index("data_processing") < STEPS.index("model_execution")
        assert STEPS.index("model_execution") < STEPS.index("sign_off")


class TestGetProject:
    """Tests for get_project()."""

    @patch("domain.workflow.query_df")
    def test_returns_none_for_missing_project(self, mock_qdf):
        from domain.workflow import get_project
        mock_qdf.return_value = pd.DataFrame()
        assert get_project("nonexistent") is None

    @patch("domain.workflow.query_df")
    def test_returns_dict_for_existing_project(self, mock_qdf):
        from domain.workflow import get_project
        mock_qdf.return_value = pd.DataFrame([{
            "project_id": "p1", "project_name": "Test",
            "step_status": '{"create_project": "completed"}',
            "overlays": "[]", "scenario_weights": "{}",
            "audit_log": "[]", "current_step": 1,
        }])
        result = get_project("p1")
        assert result is not None
        assert result["project_id"] == "p1"

    @patch("domain.workflow.query_df")
    def test_parses_json_fields(self, mock_qdf):
        from domain.workflow import get_project
        mock_qdf.return_value = pd.DataFrame([{
            "project_id": "p1", "project_name": "Test",
            "step_status": '{"create_project": "completed", "data_processing": "pending"}',
            "overlays": '[{"amount": 100}]',
            "scenario_weights": '{"baseline": 0.5}',
            "audit_log": '[{"action": "created"}]',
            "current_step": 1,
        }])
        result = get_project("p1")
        assert isinstance(result["step_status"], dict)
        assert isinstance(result["overlays"], list)
        assert isinstance(result["scenario_weights"], dict)
        assert isinstance(result["audit_log"], list)

    @patch("domain.workflow.query_df")
    def test_handles_non_string_json_fields(self, mock_qdf):
        """When DB returns already-parsed dicts (e.g. JSONB), don't re-parse."""
        from domain.workflow import get_project
        mock_qdf.return_value = pd.DataFrame([{
            "project_id": "p1", "project_name": "Test",
            "step_status": {"create_project": "completed"},
            "overlays": [], "scenario_weights": {},
            "audit_log": [], "current_step": 1,
        }])
        result = get_project("p1")
        assert isinstance(result["step_status"], dict)


class TestListProjects:
    """Tests for list_projects()."""

    @patch("domain.workflow.query_df")
    def test_returns_dataframe(self, mock_qdf):
        from domain.workflow import list_projects
        mock_qdf.return_value = pd.DataFrame([
            {"project_id": "p1", "project_name": "A", "current_step": 1},
            {"project_id": "p2", "project_name": "B", "current_step": 3},
        ])
        result = list_projects()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @patch("domain.workflow.query_df")
    def test_returns_empty_dataframe_when_no_projects(self, mock_qdf):
        from domain.workflow import list_projects
        mock_qdf.return_value = pd.DataFrame()
        result = list_projects()
        assert result.empty


class TestCreateProject:
    """Tests for create_project()."""

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_creates_project_with_correct_initial_state(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import create_project, STEPS
        mock_get.return_value = {"project_id": "p1", "current_step": 1,
                                 "step_status": {s: "pending" for s in STEPS}}
        result = create_project("p1", "Test", "ifrs9", "desc", "2025-12-31")
        assert result["project_id"] == "p1"
        mock_exec.assert_called_once()

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_initial_step_status_has_create_completed(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import create_project
        mock_get.return_value = {"project_id": "p1"}
        create_project("p1", "Test", "ifrs9", "desc", "2025-12-31")
        call_args = mock_exec.call_args
        # The step_status JSON is the 6th positional arg
        step_status_json = call_args[0][1][5]
        step_status = json.loads(step_status_json)
        assert step_status["create_project"] == "completed"
        assert step_status["data_processing"] == "pending"

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_audit_event_fired_on_create(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import create_project
        mock_get.return_value = {"project_id": "p1"}
        create_project("p1", "Test", "ifrs9", "desc", "2025-12-31")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[0][2] == "project_created"


class TestAdvanceStep:
    """Tests for advance_step()."""

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_raises_for_missing_project(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import advance_step
        mock_get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            advance_step("missing", "data_processing", "Completed", "user", "detail")

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_advances_current_step_on_completed(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import advance_step, STEPS
        proj = {
            "project_id": "p1", "current_step": 1,
            "step_status": {s: "pending" for s in STEPS},
            "audit_log": [],
        }
        proj["step_status"]["create_project"] = "completed"
        # First call returns the project, second call returns updated
        mock_get.side_effect = [proj, {**proj, "current_step": 2}]
        result = advance_step("p1", "data_processing", "Completed", "user", "detail", "completed")
        assert result["current_step"] == 2

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_does_not_advance_on_non_completed_status(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import advance_step, STEPS
        proj = {
            "project_id": "p1", "current_step": 1,
            "step_status": {s: "pending" for s in STEPS},
            "audit_log": [],
        }
        mock_get.side_effect = [proj, {**proj, "current_step": 1}]
        result = advance_step("p1", "data_processing", "Started", "user", "detail", "in_progress")
        assert result["current_step"] == 1

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_appends_audit_log_entry(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import advance_step, STEPS
        proj = {
            "project_id": "p1", "current_step": 1,
            "step_status": {s: "pending" for s in STEPS},
            "audit_log": [{"action": "created"}],
        }
        mock_get.side_effect = [proj, proj]
        advance_step("p1", "data_processing", "Completed", "analyst", "processed data")
        call_args = mock_exec.call_args
        # UPDATE params: (new_step, step_status_json, audit_log_json, project_id)
        audit_json = call_args[0][1][2]
        audit = json.loads(audit_json)
        assert len(audit) == 2
        assert audit[1]["action"] == "Completed"
        assert audit[1]["user"] == "analyst"

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_unknown_step_uses_current_index(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import advance_step, STEPS
        proj = {
            "project_id": "p1", "current_step": 3,
            "step_status": {s: "pending" for s in STEPS},
            "audit_log": [],
        }
        mock_get.side_effect = [proj, proj]
        # Unknown step name should use current_step as index
        advance_step("p1", "custom_step", "Custom action", "user", "detail")
        # Should not raise


class TestSaveOverlays:
    """Tests for save_overlays()."""

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_stores_overlays_json(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import save_overlays
        mock_get.return_value = {"project_id": "p1", "overlays": [{"amount": 100}]}
        overlays = [{"amount": 100, "reason": "COVID adjustment"}]
        save_overlays("p1", overlays, "analyst")
        call_args = mock_exec.call_args
        stored_json = call_args[0][1][0]
        assert json.loads(stored_json) == overlays

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_triggers_audit_event(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import save_overlays
        mock_get.return_value = {"project_id": "p1"}
        save_overlays("p1", [{"amount": 50}], "analyst")
        mock_audit.assert_called_once()
        assert "overlays_updated" in str(mock_audit.call_args)


class TestSaveScenarioWeights:
    """Tests for save_scenario_weights()."""

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_stores_weights_json(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import save_scenario_weights
        mock_get.return_value = {"project_id": "p1"}
        weights = {"baseline": 0.4, "adverse": 0.3, "optimistic": 0.3}
        save_scenario_weights("p1", weights, "analyst")
        call_args = mock_exec.call_args
        stored = json.loads(call_args[0][1][0])
        assert stored == weights


class TestResetProject:
    """Tests for reset_project()."""

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    def test_raises_for_missing_project(self, mock_get, mock_exec):
        from domain.workflow import reset_project
        mock_get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            reset_project("missing")

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    def test_raises_for_signed_off_project(self, mock_get, mock_exec):
        from domain.workflow import reset_project, STEPS
        mock_get.return_value = {
            "project_id": "p1", "signed_off_by": "auditor",
            "step_status": {s: "completed" for s in STEPS},
            "audit_log": [],
        }
        with pytest.raises(ValueError, match="signed-off"):
            reset_project("p1")

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    def test_resets_step_status_to_initial(self, mock_get, mock_exec):
        from domain.workflow import reset_project, STEPS
        proj = {
            "project_id": "p1", "signed_off_by": None,
            "step_status": {s: "completed" for s in STEPS},
            "audit_log": [{"action": "created"}],
        }
        mock_get.side_effect = [proj, {**proj, "current_step": 1}]
        reset_project("p1")
        call_args = mock_exec.call_args
        step_status = json.loads(call_args[0][1][0])
        assert step_status["create_project"] == "completed"
        assert step_status["data_processing"] == "pending"
        assert step_status["sign_off"] == "pending"


class TestSignOffProject:
    """Tests for sign_off_project()."""

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_raises_for_missing_project(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import sign_off_project
        mock_get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            sign_off_project("missing", "auditor")

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_sets_signed_off_by(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import sign_off_project, STEPS
        proj = {
            "project_id": "p1", "current_step": 7, "signed_off_by": None,
            "step_status": {s: "completed" for s in STEPS},
            "audit_log": [], "overlays": [], "scenario_weights": {},
        }
        proj["step_status"]["sign_off"] = "pending"
        mock_get.side_effect = [proj, {**proj, "signed_off_by": "auditor"}]
        result = sign_off_project("p1", "auditor")
        assert result["signed_off_by"] == "auditor"

    @patch("domain.workflow.execute")
    @patch("domain.workflow.get_project")
    @patch("domain.workflow._audit_event")
    def test_sign_off_with_attestation(self, mock_audit, mock_get, mock_exec):
        from domain.workflow import sign_off_project, STEPS
        proj = {
            "project_id": "p1", "current_step": 7, "signed_off_by": None,
            "step_status": {s: "completed" for s in STEPS},
            "audit_log": [], "overlays": [], "scenario_weights": {},
        }
        mock_get.side_effect = [proj, proj]
        attestation = {"prepared_by": "analyst", "reviewed_by": "manager"}
        sign_off_project("p1", "auditor", attestation_data=attestation)
        call_args = mock_exec.call_args_list[-1]
        # attestation_data should be JSON-serialized in the params
        params = call_args[0][1]
        assert json.loads(params[-3]) == attestation


class TestWorkflowAuditEvent:
    """Tests for _audit_event helper."""

    @patch("domain.workflow.log")
    def test_audit_event_does_not_block_on_failure(self, mock_log):
        from domain.workflow import _audit_event
        with patch("domain.audit_trail.append_audit_entry", side_effect=Exception("DB down")):
            # Should not raise
            _audit_event("p1", "workflow", "test", "user", {"key": "val"})
        mock_log.warning.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
# Section 2: domain/queries.py
# ═══════════════════════════════════════════════════════════════════


class TestPortfolioQueries:
    """Tests for portfolio-level query functions."""

    @patch("domain.queries.query_df")
    def test_get_portfolio_summary_returns_dataframe(self, mock_qdf):
        from domain.queries import get_portfolio_summary
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Personal Loans", "loan_count": 1000,
            "total_gca": 5000000.0, "avg_eir_pct": 12.5,
            "avg_dpd": 5.2, "avg_pd_pct": 3.1,
            "stage_1_count": 800, "stage_2_count": 150, "stage_3_count": 50,
        }])
        result = get_portfolio_summary()
        assert isinstance(result, pd.DataFrame)
        assert "product_type" in result.columns

    @patch("domain.queries.query_df")
    def test_get_stage_distribution_returns_dataframe(self, mock_qdf):
        from domain.queries import get_stage_distribution
        mock_qdf.return_value = pd.DataFrame([
            {"assessed_stage": 1, "loan_count": 8000, "total_gca": 40000000.0},
            {"assessed_stage": 2, "loan_count": 1500, "total_gca": 8000000.0},
            {"assessed_stage": 3, "loan_count": 500, "total_gca": 2000000.0},
        ])
        result = get_stage_distribution()
        assert len(result) == 3

    @patch("domain.queries.query_df")
    def test_get_borrower_segment_stats(self, mock_qdf):
        from domain.queries import get_borrower_segment_stats
        mock_qdf.return_value = pd.DataFrame([
            {"segment": "Prime", "borrower_count": 500, "avg_alt_score": 720.5},
        ])
        result = get_borrower_segment_stats()
        assert "segment" in result.columns

    @patch("domain.queries.query_df")
    def test_get_vintage_analysis(self, mock_qdf):
        from domain.queries import get_vintage_analysis
        mock_qdf.return_value = pd.DataFrame([
            {"vintage_cohort": "2023-Q1", "loan_count": 100, "total_gca": 500000.0},
        ])
        result = get_vintage_analysis()
        assert not result.empty

    @patch("domain.queries.query_df")
    def test_get_dpd_distribution_returns_buckets(self, mock_qdf):
        from domain.queries import get_dpd_distribution
        mock_qdf.return_value = pd.DataFrame([
            {"dpd_bucket": "Current", "loan_count": 7000, "total_gca": 35000000.0},
            {"dpd_bucket": "1-30 DPD", "loan_count": 1500, "total_gca": 8000000.0},
        ])
        result = get_dpd_distribution()
        assert "dpd_bucket" in result.columns


class TestECLQueries:
    """Tests for ECL-specific query functions."""

    @patch("domain.queries.query_df")
    def test_get_ecl_summary(self, mock_qdf):
        from domain.queries import get_ecl_summary
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Personal Loans", "assessed_stage": 1,
            "loan_count": 800, "total_gca": 4000000, "total_ecl": 50000,
            "coverage_ratio": 1.25,
        }])
        result = get_ecl_summary()
        assert "total_ecl" in result.columns

    @patch("domain.queries.query_df")
    def test_get_ecl_by_product(self, mock_qdf):
        from domain.queries import get_ecl_by_product
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Mortgages", "loan_count": 500,
            "total_gca": 10000000, "total_ecl": 150000, "coverage_ratio": 1.5,
        }])
        result = get_ecl_by_product()
        assert "coverage_ratio" in result.columns

    @patch("domain.queries.query_df")
    def test_get_scenario_summary(self, mock_qdf):
        from domain.queries import get_scenario_summary
        mock_qdf.return_value = pd.DataFrame([
            {"scenario": "baseline", "weight": 0.4, "total_ecl": 1000000,
             "total_ecl_p95": 1200000, "total_ecl_p99": 1500000, "weighted": 400000},
        ])
        result = get_scenario_summary()
        assert "weighted" in result.columns

    @patch("domain.queries.query_df")
    def test_get_mc_distribution(self, mock_qdf):
        from domain.queries import get_mc_distribution
        mock_qdf.return_value = pd.DataFrame([{
            "scenario": "baseline", "weight": 0.4, "ecl_mean": 1000000,
            "ecl_p50": 950000, "ecl_p75": 1100000, "ecl_p95": 1350000,
            "ecl_p99": 1550000, "n_simulations": 1000,
        }])
        result = get_mc_distribution()
        assert "ecl_mean" in result.columns

    @patch("domain.queries.query_df")
    def test_get_ecl_concentration(self, mock_qdf):
        from domain.queries import get_ecl_concentration
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Auto Loans", "assessed_stage": 1,
            "loan_count": 200, "total_ecl": 30000, "avg_ecl": 150, "max_ecl": 2000,
        }])
        result = get_ecl_concentration()
        assert "max_ecl" in result.columns

    @patch("domain.queries.query_df")
    def test_get_stage_migration(self, mock_qdf):
        from domain.queries import get_stage_migration
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Personal Loans", "original_stage": 1,
            "assessed_stage": 2, "loan_count": 50, "total_gca": 250000,
        }])
        result = get_stage_migration()
        assert "original_stage" in result.columns

    @patch("domain.queries.query_df")
    def test_get_credit_risk_exposure(self, mock_qdf):
        from domain.queries import get_credit_risk_exposure
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Personal Loans", "assessed_stage": 1,
            "credit_risk_grade": "A", "loan_count": 100, "total_gca": 500000,
        }])
        result = get_credit_risk_exposure()
        assert "credit_risk_grade" in result.columns

    @patch("domain.queries.query_df")
    def test_get_loss_allowance_by_stage(self, mock_qdf):
        from domain.queries import get_loss_allowance_by_stage
        mock_qdf.return_value = pd.DataFrame([
            {"assessed_stage": 1, "loan_count": 8000, "total_gca": 40000000,
             "total_ecl": 200000, "coverage_pct": 0.5},
        ])
        result = get_loss_allowance_by_stage()
        assert "coverage_pct" in result.columns


class TestDrillDownQueries:
    """Tests for drill-down and detail query functions."""

    @patch("domain.queries.query_df")
    def test_get_ecl_by_stage_product(self, mock_qdf):
        from domain.queries import get_ecl_by_stage_product
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Personal Loans", "loan_count": 500,
            "total_gca": 2500000, "total_ecl": 50000, "coverage_pct": 2.0,
        }])
        result = get_ecl_by_stage_product(1)
        assert not result.empty
        # Verify stage parameter was passed
        call_args = mock_qdf.call_args
        assert call_args[0][1] == (1,)

    @patch("domain.queries.query_df")
    def test_get_ecl_by_scenario_product_detail(self, mock_qdf):
        from domain.queries import get_ecl_by_scenario_product_detail
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Mortgages", "loan_count": 300,
            "total_gca": 5000000, "total_ecl": 80000, "avg_ecl": 266.67,
        }])
        result = get_ecl_by_scenario_product_detail("baseline")
        assert not result.empty

    @patch("domain.queries.query_df")
    def test_get_top_exposures_default_limit(self, mock_qdf):
        from domain.queries import get_top_exposures
        mock_qdf.return_value = pd.DataFrame()
        get_top_exposures()
        call_args = mock_qdf.call_args
        assert call_args[0][1] == (20,)

    @patch("domain.queries.query_df")
    def test_get_top_exposures_custom_limit(self, mock_qdf):
        from domain.queries import get_top_exposures
        mock_qdf.return_value = pd.DataFrame()
        get_top_exposures(limit=5)
        call_args = mock_qdf.call_args
        assert call_args[0][1] == (5,)

    @patch("domain.queries.query_df")
    def test_get_loans_by_product_filters(self, mock_qdf):
        from domain.queries import get_loans_by_product
        mock_qdf.return_value = pd.DataFrame()
        get_loans_by_product("Auto Loans")
        call_args = mock_qdf.call_args
        assert call_args[0][1] == ("Auto Loans",)

    @patch("domain.queries.query_df")
    def test_get_loans_by_stage_filters(self, mock_qdf):
        from domain.queries import get_loans_by_stage
        mock_qdf.return_value = pd.DataFrame()
        get_loans_by_stage(3)
        call_args = mock_qdf.call_args
        assert call_args[0][1] == (3,)

    @patch("domain.queries.query_df")
    def test_get_scenario_ecl_by_product(self, mock_qdf):
        from domain.queries import get_scenario_ecl_by_product
        mock_qdf.return_value = pd.DataFrame()
        get_scenario_ecl_by_product("adverse")
        call_args = mock_qdf.call_args
        assert call_args[0][1] == ("adverse",)


class TestAnalyticsQueries:
    """Tests for analytics and stress testing query functions."""

    @patch("domain.queries.query_df")
    def test_get_sensitivity_data(self, mock_qdf):
        from domain.queries import get_sensitivity_data
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Personal Loans", "loan_count": 1000,
            "total_gca": 5000000, "avg_pd": 0.05, "implied_lgd": 0.4,
            "base_ecl": 100000,
        }])
        result = get_sensitivity_data()
        assert "implied_lgd" in result.columns

    @patch("domain.queries.query_df")
    def test_get_scenario_comparison(self, mock_qdf):
        from domain.queries import get_scenario_comparison
        mock_qdf.return_value = pd.DataFrame([
            {"scenario": "baseline", "product_type": "PL", "loan_count": 100, "total_ecl": 50000},
            {"scenario": "adverse", "product_type": "PL", "loan_count": 100, "total_ecl": 75000},
        ])
        result = get_scenario_comparison()
        assert len(result) == 2

    @patch("domain.queries.query_df")
    def test_get_stress_by_stage(self, mock_qdf):
        from domain.queries import get_stress_by_stage
        mock_qdf.return_value = pd.DataFrame([
            {"assessed_stage": 1, "loan_count": 8000, "total_gca": 40000000,
             "avg_pd": 0.02, "base_ecl": 200000},
        ])
        result = get_stress_by_stage()
        assert "base_ecl" in result.columns

    @patch("domain.queries.query_df")
    def test_get_vintage_performance(self, mock_qdf):
        from domain.queries import get_vintage_performance
        mock_qdf.return_value = pd.DataFrame([{
            "vintage_cohort": "2023-Q1", "loan_count": 100, "total_gca": 500000,
            "avg_pd_pct": 3.5, "delinquency_rate": 5.0, "dpd30_rate": 3.0,
            "dpd60_rate": 1.5, "dpd90_rate": 0.8,
            "stage1": 80, "stage2": 15, "stage3": 5,
        }])
        result = get_vintage_performance()
        assert "delinquency_rate" in result.columns

    @patch("domain.queries.query_df")
    def test_get_vintage_by_product(self, mock_qdf):
        from domain.queries import get_vintage_by_product
        mock_qdf.return_value = pd.DataFrame()
        result = get_vintage_by_product()
        assert isinstance(result, pd.DataFrame)

    @patch("domain.queries.query_df")
    def test_get_concentration_by_segment(self, mock_qdf):
        from domain.queries import get_concentration_by_segment
        mock_qdf.return_value = pd.DataFrame([{
            "segment": "Prime", "loan_count": 5000, "total_gca": 25000000,
            "total_ecl": 125000, "coverage_pct": 0.5, "max_single_ecl": 5000,
        }])
        result = get_concentration_by_segment()
        assert "max_single_ecl" in result.columns

    @patch("domain.queries.query_df")
    def test_get_concentration_by_product_stage(self, mock_qdf):
        from domain.queries import get_concentration_by_product_stage
        mock_qdf.return_value = pd.DataFrame()
        result = get_concentration_by_product_stage()
        assert isinstance(result, pd.DataFrame)

    @patch("domain.queries.query_df")
    def test_get_top_concentration_risk(self, mock_qdf):
        from domain.queries import get_top_concentration_risk
        mock_qdf.return_value = pd.DataFrame()
        result = get_top_concentration_risk()
        assert isinstance(result, pd.DataFrame)

    @patch("domain.queries.query_df")
    def test_get_ecl_by_scenario_product(self, mock_qdf):
        from domain.queries import get_ecl_by_scenario_product
        mock_qdf.return_value = pd.DataFrame()
        result = get_ecl_by_scenario_product()
        assert isinstance(result, pd.DataFrame)

    @patch("domain.queries.query_df")
    def test_get_stage_by_product(self, mock_qdf):
        from domain.queries import get_stage_by_product
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "PL", "assessed_stage": 1,
            "loan_count": 100, "total_gca": 500000,
        }])
        result = get_stage_by_product()
        assert "assessed_stage" in result.columns

    @patch("domain.queries.query_df")
    def test_get_pd_distribution(self, mock_qdf):
        from domain.queries import get_pd_distribution
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "PL", "avg_pd_pct": 3.5, "min_pd_pct": 0.1,
            "max_pd_pct": 45.0, "p25_pd_pct": 1.2, "p75_pd_pct": 8.5,
        }])
        result = get_pd_distribution()
        assert "p25_pd_pct" in result.columns

    @patch("domain.queries.query_df")
    def test_get_dq_results(self, mock_qdf):
        from domain.queries import get_dq_results
        mock_qdf.return_value = pd.DataFrame()
        result = get_dq_results()
        assert isinstance(result, pd.DataFrame)

    @patch("domain.queries.query_df")
    def test_get_dq_summary(self, mock_qdf):
        from domain.queries import get_dq_summary
        mock_qdf.return_value = pd.DataFrame()
        result = get_dq_summary()
        assert isinstance(result, pd.DataFrame)

    @patch("domain.queries.query_df")
    def test_get_gl_reconciliation(self, mock_qdf):
        from domain.queries import get_gl_reconciliation
        mock_qdf.return_value = pd.DataFrame()
        result = get_gl_reconciliation()
        assert isinstance(result, pd.DataFrame)


# ═══════════════════════════════════════════════════════════════════
# Section 3: domain/attribution.py — Gap Coverage
# ═══════════════════════════════════════════════════════════════════


class TestComputeAttribution:
    """Tests for the full compute_attribution flow.

    compute_attribution makes many sequential query_df calls via _safe_query.
    We use a side_effect function that returns the closing ECL for the first
    query (portfolio_ecl_summary) and empty DataFrames for all subsequent
    queries, which triggers the data_unavailable fallbacks gracefully.
    """

    @staticmethod
    def _ecl_df(s1=100000, s2=50000, s3=20000):
        return pd.DataFrame([
            {"assessed_stage": 1, "total_ecl": s1},
            {"assessed_stage": 2, "total_ecl": s2},
            {"assessed_stage": 3, "total_ecl": s3},
        ])

    @staticmethod
    def _make_side_effect(ecl_df, eir_df=None):
        """Return a side_effect function for query_df that provides:
        - ecl_df for the first call (closing ECL)
        - empty DF for prior attribution
        - empty DF for originations, derecognitions, migration, avg_ecl, write-offs
        - eir_df (or default) for the EIR query
        - empty DF for anything else
        """
        default_eir = pd.DataFrame([{"avg_eir": 0.10}])
        actual_eir = eir_df if eir_df is not None else default_eir
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            sql = args[0] if args else ""
            if "portfolio_ecl_summary" in sql and call_count[0] <= 2:
                return ecl_df
            if "avg_eir" in sql.lower() or "effective_interest_rate" in sql.lower():
                return actual_eir
            if "ecl_attribution" in sql and "OFFSET 1" in sql:
                return pd.DataFrame()  # no prior attribution
            return pd.DataFrame()
        return side_effect

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_returns_all_required_keys(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        required_keys = {"attribution_id", "project_id", "reporting_date",
                         "opening_ecl", "closing_ecl", "new_originations",
                         "derecognitions", "stage_transfers", "model_changes",
                         "macro_changes", "management_overlays", "write_offs",
                         "unwind_discount", "fx_changes", "residual",
                         "waterfall_data", "reconciliation"}
        assert required_keys.issubset(set(result.keys()))

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_closing_ecl_from_portfolio(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df(100000, 50000, 20000))
        result = compute_attribution("p1")
        assert result["closing_ecl"]["stage1"] == 100000
        assert result["closing_ecl"]["stage2"] == 50000
        assert result["closing_ecl"]["stage3"] == 20000
        assert result["closing_ecl"]["total"] == 170000

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_opening_ecl_estimated_when_no_prior(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        assert result["opening_ecl"]["total"] == result["closing_ecl"]["total"]

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_waterfall_data_is_list_of_12(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        assert isinstance(result["waterfall_data"], list)
        assert len(result["waterfall_data"]) == 12

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_waterfall_anchors(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        wf = result["waterfall_data"]
        assert wf[0]["name"] == "Opening ECL"
        assert wf[-1]["name"] == "Closing ECL"
        assert wf[0]["category"] == "anchor"
        assert wf[-1]["category"] == "anchor"

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_reconciliation_keys(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        recon = result["reconciliation"]
        assert "within_materiality" in recon
        assert "residual_pct" in recon
        assert "data_gaps" in recon

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_overlay_with_target_stage(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [{"amount": 5000, "stage": 2}],
            "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        assert result["management_overlays"]["stage2"] == 5000
        assert result["management_overlays"]["stage1"] == 0

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_overlay_proportional_no_stage(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [{"amount": 10000}],
            "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df(100000, 50000, 20000))
        result = compute_attribution("p1")
        total_overlay = result["management_overlays"]["total"]
        assert abs(total_overlay - 10000) < 1

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_fx_changes_zero(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        assert result["fx_changes"]["total"] == 0

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_unwind_discount_positive(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df(100000, 50000, 20000))
        result = compute_attribution("p1")
        # With EIR=0.10, quarterly=0.025, opening=170000: unwind ~ 4250
        assert result["unwind_discount"]["total"] > 0

    @patch("domain.attribution.execute")
    @patch("domain.attribution.query_df")
    @patch("domain.attribution.get_project")
    def test_data_gaps_tracked(self, mock_proj, mock_qdf, mock_exec):
        from domain.attribution import compute_attribution
        mock_proj.return_value = {
            "project_id": "p1", "reporting_date": "2025-12-31",
            "overlays": [], "scenario_weights": {},
        }
        # All queries return empty (except closing ECL)
        mock_qdf.side_effect = self._make_side_effect(self._ecl_df())
        result = compute_attribution("p1")
        # data_gaps should list components with missing data
        assert isinstance(result["reconciliation"]["data_gaps"], list)


class TestGetAttribution:
    """Tests for get_attribution and history."""

    @patch("domain.attribution.query_df")
    def test_get_attribution_returns_none_when_empty(self, mock_qdf):
        from domain.attribution import get_attribution
        mock_qdf.return_value = pd.DataFrame()
        assert get_attribution("p1") is None

    @patch("domain.attribution.query_df")
    def test_get_attribution_returns_parsed_dict(self, mock_qdf):
        from domain.attribution import get_attribution
        mock_qdf.return_value = pd.DataFrame([{
            "attribution_id": "p1_20251231", "project_id": "p1",
            "opening_ecl": '{"stage1": 100, "total": 100}',
            "closing_ecl": '{"stage1": 110, "total": 110}',
            "new_originations": '{}', "derecognitions": '{}',
            "stage_transfers": '{}', "model_changes": '{}',
            "macro_changes": '{}', "management_overlays": '{}',
            "write_offs": '{}', "unwind_discount": '{}',
            "fx_changes": '{}', "residual": '{}',
            "waterfall_data": '[]', "reconciliation": '{}',
        }])
        result = get_attribution("p1")
        assert isinstance(result["opening_ecl"], dict)

    @patch("domain.attribution.query_df")
    def test_get_attribution_handles_exception(self, mock_qdf):
        from domain.attribution import get_attribution
        mock_qdf.side_effect = Exception("DB error")
        assert get_attribution("p1") is None

    @patch("domain.attribution.query_df")
    def test_get_attribution_history_returns_list(self, mock_qdf):
        from domain.attribution import get_attribution_history
        mock_qdf.return_value = pd.DataFrame([
            {"attribution_id": "p1_1", "project_id": "p1",
             "opening_ecl": '{}', "closing_ecl": '{}',
             "new_originations": '{}', "derecognitions": '{}',
             "stage_transfers": '{}', "model_changes": '{}',
             "macro_changes": '{}', "management_overlays": '{}',
             "write_offs": '{}', "unwind_discount": '{}',
             "fx_changes": '{}', "residual": '{}',
             "waterfall_data": '[]', "reconciliation": '{}'},
        ])
        result = get_attribution_history("p1")
        assert isinstance(result, list)
        assert len(result) == 1

    @patch("domain.attribution.query_df")
    def test_get_attribution_history_empty(self, mock_qdf):
        from domain.attribution import get_attribution_history
        mock_qdf.return_value = pd.DataFrame()
        result = get_attribution_history("p1")
        assert result == []

    @patch("domain.attribution.query_df")
    def test_get_attribution_history_handles_exception(self, mock_qdf):
        from domain.attribution import get_attribution_history
        mock_qdf.side_effect = Exception("DB error")
        result = get_attribution_history("p1")
        assert result == []


# ═══════════════════════════════════════════════════════════════════
# Section 4: domain/validation_rules.py — Gap Coverage
# ═══════════════════════════════════════════════════════════════════


class TestStage3DPDCheck:
    """D7: Stage 3 DPD >= 90."""

    def test_d7_all_stage3_above_90_passes(self):
        from domain.validation_rules import check_stage3_dpd
        result = check_stage3_dpd([(3, 90), (3, 120), (1, 5), (2, 45)])
        assert result.passed

    def test_d7_stage3_below_90_fails(self):
        from domain.validation_rules import check_stage3_dpd
        result = check_stage3_dpd([(3, 60), (3, 90)])
        assert not result.passed
        assert result.detail["violations_count"] == 1

    def test_d7_empty_input_passes(self):
        from domain.validation_rules import check_stage3_dpd
        result = check_stage3_dpd([])
        assert result.passed

    def test_d7_no_stage3_passes(self):
        from domain.validation_rules import check_stage3_dpd
        result = check_stage3_dpd([(1, 0), (2, 30)])
        assert result.passed


class TestStage1DPDCheck:
    """D8: Stage 1 DPD < 30."""

    def test_d8_all_stage1_below_30_passes(self):
        from domain.validation_rules import check_stage1_dpd
        result = check_stage1_dpd([(1, 0), (1, 15), (2, 45), (3, 90)])
        assert result.passed

    def test_d8_stage1_at_30_fails(self):
        from domain.validation_rules import check_stage1_dpd
        result = check_stage1_dpd([(1, 30), (1, 0)])
        assert not result.passed
        assert result.detail["violations_count"] == 1

    def test_d8_empty_input_passes(self):
        from domain.validation_rules import check_stage1_dpd
        result = check_stage1_dpd([])
        assert result.passed


class TestOriginationDateCheck:
    """D9: origination_date < reporting_date."""

    def test_d9_all_before_reporting_passes(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(
            ["2024-01-01", "2024-06-15"], "2025-12-31"
        )
        assert result.passed

    def test_d9_origination_after_reporting_fails(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(
            ["2024-01-01", "2026-01-01"], "2025-12-31"
        )
        assert not result.passed

    def test_d9_origination_equal_to_reporting_fails(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(
            ["2025-12-31"], "2025-12-31"
        )
        assert not result.passed

    def test_d9_invalid_reporting_date_fails(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(["2024-01-01"], "not-a-date")
        assert not result.passed

    def test_d9_invalid_origination_date_fails(self):
        from domain.validation_rules import check_origination_before_reporting
        result = check_origination_before_reporting(["invalid"], "2025-12-31")
        assert not result.passed


class TestMaturityDateCheck:
    """D10: maturity_date > origination_date."""

    def test_d10_maturity_after_origination_passes(self):
        from domain.validation_rules import check_maturity_after_origination
        result = check_maturity_after_origination(
            [("2024-01-01", "2027-01-01"), ("2023-06-01", "2028-06-01")]
        )
        assert result.passed

    def test_d10_maturity_before_origination_fails(self):
        from domain.validation_rules import check_maturity_after_origination
        result = check_maturity_after_origination(
            [("2024-01-01", "2023-01-01")]
        )
        assert not result.passed

    def test_d10_maturity_equal_origination_fails(self):
        from domain.validation_rules import check_maturity_after_origination
        result = check_maturity_after_origination(
            [("2024-01-01", "2024-01-01")]
        )
        assert not result.passed

    def test_d10_invalid_dates_count_as_violations(self):
        from domain.validation_rules import check_maturity_after_origination
        result = check_maturity_after_origination(
            [("bad", "also-bad")]
        )
        assert not result.passed


class TestDomainAccuracyRules:
    """DA-1 through DA-6: IFRS 9 domain accuracy rules."""

    def test_da1_ead_non_negative_passes(self):
        from domain.validation_rules import check_ead_non_negative
        result = check_ead_non_negative([100, 200, 0, 50000])
        assert result.passed

    def test_da1_ead_negative_fails(self):
        from domain.validation_rules import check_ead_non_negative
        result = check_ead_non_negative([100, -50, 200])
        assert not result.passed
        assert result.detail["violations_count"] == 1

    def test_da1_ead_empty_passes(self):
        from domain.validation_rules import check_ead_non_negative
        result = check_ead_non_negative([])
        assert result.passed

    def test_da2_lgd_unit_interval_passes(self):
        from domain.validation_rules import check_lgd_unit_interval
        result = check_lgd_unit_interval([0, 0.3, 0.5, 1.0])
        assert result.passed

    def test_da2_lgd_above_one_fails(self):
        from domain.validation_rules import check_lgd_unit_interval
        result = check_lgd_unit_interval([0.5, 1.1])
        assert not result.passed

    def test_da2_lgd_negative_fails(self):
        from domain.validation_rules import check_lgd_unit_interval
        result = check_lgd_unit_interval([-0.1, 0.5])
        assert not result.passed

    def test_da3_stage3_pd_high_passes(self):
        from domain.validation_rules import check_stage3_pd_consistency
        result = check_stage3_pd_consistency([(3, 0.95), (3, 1.0), (1, 0.05)])
        assert result.passed

    def test_da3_stage3_pd_low_fails(self):
        from domain.validation_rules import check_stage3_pd_consistency
        result = check_stage3_pd_consistency([(3, 0.50), (3, 0.95)])
        assert not result.passed
        assert result.detail["violations_count"] == 1

    def test_da3_no_stage3_passes(self):
        from domain.validation_rules import check_stage3_pd_consistency
        result = check_stage3_pd_consistency([(1, 0.05), (2, 0.15)])
        assert result.passed

    def test_da3_custom_threshold(self):
        from domain.validation_rules import check_stage3_pd_consistency
        result = check_stage3_pd_consistency([(3, 0.80)], min_stage3_pd=0.75)
        assert result.passed

    def test_da4_discount_rate_valid(self):
        from domain.validation_rules import check_discount_rate_valid
        result = check_discount_rate_valid([0.05, 0.10, 0.0, -0.5])
        assert result.passed  # all > -1

    def test_da4_discount_rate_at_minus_one_fails(self):
        from domain.validation_rules import check_discount_rate_valid
        result = check_discount_rate_valid([0.05, -1.0])
        assert not result.passed

    def test_da4_discount_rate_below_minus_one_fails(self):
        from domain.validation_rules import check_discount_rate_valid
        result = check_discount_rate_valid([-2.0])
        assert not result.passed

    def test_da5_ecl_non_negative_passes(self):
        from domain.validation_rules import check_ecl_non_negative
        result = check_ecl_non_negative([0, 100, 5000, 0.01])
        assert result.passed

    def test_da5_ecl_negative_fails(self):
        from domain.validation_rules import check_ecl_non_negative
        result = check_ecl_non_negative([100, -5])
        assert not result.passed

    def test_da6_minimum_scenario_count_passes(self):
        from domain.validation_rules import check_minimum_scenario_count
        result = check_minimum_scenario_count(3)
        assert result.passed

    def test_da6_minimum_scenario_count_fails(self):
        from domain.validation_rules import check_minimum_scenario_count
        result = check_minimum_scenario_count(2)
        assert not result.passed

    def test_da6_custom_minimum(self):
        from domain.validation_rules import check_minimum_scenario_count
        result = check_minimum_scenario_count(5, minimum=5)
        assert result.passed


class TestAdditionalModelRules:
    """M-R3, M-R7: Additional model reasonableness rules."""

    def test_mr3_satellite_r_squared_passes(self):
        from domain.validation_rules import check_satellite_r_squared
        result = check_satellite_r_squared({"model_a": 0.55, "model_b": 0.72})
        assert result.passed

    def test_mr3_satellite_r_squared_fails(self):
        from domain.validation_rules import check_satellite_r_squared
        result = check_satellite_r_squared({"model_a": 0.15, "model_b": 0.72})
        assert not result.passed
        assert "model_a" in result.detail["failures"]

    def test_mr3_custom_threshold(self):
        from domain.validation_rules import check_satellite_r_squared
        result = check_satellite_r_squared({"m1": 0.25}, threshold=0.20)
        assert result.passed

    def test_mr7_pd_aging_factor_in_range(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(0.10)
        assert result.passed

    def test_mr7_pd_aging_factor_too_high(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(0.50)
        assert not result.passed

    def test_mr7_pd_aging_factor_negative_fails(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(-0.01)
        assert not result.passed

    def test_mr7_pd_aging_factor_at_zero_passes(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(0.0)
        assert result.passed

    def test_mr7_pd_aging_factor_at_max_passes(self):
        from domain.validation_rules import check_pd_aging_factor
        result = check_pd_aging_factor(0.30)
        assert result.passed


class TestGovernanceGapRules:
    """G-R4: Backtesting gate."""

    def test_gr4_no_backtest_fails(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(None)
        assert not result.passed

    def test_gr4_recent_backtest_passes(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(30)
        assert result.passed

    def test_gr4_expired_backtest_fails(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(100)
        assert not result.passed

    def test_gr4_at_limit_passes(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(90, max_days=90)
        assert result.passed

    def test_gr4_custom_max_days(self):
        from domain.validation_rules import check_backtesting_gate
        result = check_backtesting_gate(50, max_days=30)
        assert not result.passed


class TestBoundaryConditions:
    """Boundary tests for scenario weights and aggregate checks."""

    def test_d1_weights_at_lower_tolerance_passes(self):
        from domain.validation_rules import check_scenario_weights_sum
        # 0.9995 is within ±0.001 of 1.0
        result = check_scenario_weights_sum({"a": 0.4995, "b": 0.500})
        assert result.passed

    def test_d1_weights_at_upper_tolerance_passes(self):
        from domain.validation_rules import check_scenario_weights_sum
        # 1.0005 is within ±0.001 of 1.0
        result = check_scenario_weights_sum({"a": 0.5005, "b": 0.500})
        assert result.passed

    def test_d1_weights_beyond_tolerance_fails(self):
        from domain.validation_rules import check_scenario_weights_sum
        # 0.99 is 0.01 away from 1.0, well outside ±0.001
        result = check_scenario_weights_sum({"a": 0.49, "b": 0.50})
        assert not result.passed

    def test_pre_calculation_with_all_optional_params(self):
        from domain.validation_rules import run_all_pre_calculation_checks
        results = run_all_pre_calculation_checks(
            scenario_weights={"baseline": 0.5, "adverse": 0.3, "optimistic": 0.2},
            pd_values=[0.05, 0.10],
            lgd_values=[0.3, 0.5],
            eir_values=[0.05, 0.10],
            remaining_months=[12, 24],
            gca_values=[10000, 20000],
            stage_dpd_pairs=[(1, 5), (2, 45), (3, 100)],
            aging_factor=0.10,
            ead_values=[10000, 20000],
            stage_pd_pairs=[(1, 0.05), (3, 0.95)],
        )
        assert isinstance(results, list)
        assert len(results) > 10  # Should include all optional checks

    def test_has_critical_failures_with_mixed_results(self):
        from domain.validation_rules import has_critical_failures
        results = [
            {"severity": "HIGH", "passed": False},
            {"severity": "MEDIUM", "passed": True},
            {"severity": "CRITICAL", "passed": True},
        ]
        assert not has_critical_failures(results)

    def test_has_critical_failures_with_critical_failure(self):
        from domain.validation_rules import has_critical_failures
        results = [
            {"severity": "CRITICAL", "passed": False},
            {"severity": "HIGH", "passed": True},
        ]
        assert has_critical_failures(results)

    def test_mr5_zero_total_ecl(self):
        from domain.validation_rules import check_scenario_concentration
        result = check_scenario_concentration({"baseline": 0}, 0)
        assert result.passed

    def test_mr8_zero_base_ecl(self):
        from domain.validation_rules import check_overlay_cap
        result = check_overlay_cap(5000, 0)
        assert result.passed

    def test_mr5b_adverse_total_below_minimum(self):
        from domain.validation_rules import check_scenario_weight_constraints
        # All weight in baseline, zero in adverse
        result = check_scenario_weight_constraints({"baseline": 0.8, "optimistic": 0.2})
        assert not result.passed
        assert "Adverse scenarios total" in result.message


# ═══════════════════════════════════════════════════════════════════
# Section 5: domain/data_mapper.py
# ═══════════════════════════════════════════════════════════════════


class TestSafeIdentifier:
    """Tests for _safe_identifier."""

    def test_valid_identifier_passes(self):
        from domain.data_mapper import _safe_identifier
        assert _safe_identifier("my_table") == "my_table"

    def test_valid_identifier_with_dots(self):
        from domain.data_mapper import _safe_identifier
        assert _safe_identifier("catalog.schema.table") == "catalog.schema.table"

    def test_valid_identifier_with_dashes(self):
        from domain.data_mapper import _safe_identifier
        assert _safe_identifier("my-table") == "my-table"

    def test_invalid_identifier_raises(self):
        from domain.data_mapper import _safe_identifier
        with pytest.raises(ValueError, match="Invalid identifier"):
            _safe_identifier("table; DROP TABLE--")

    def test_empty_string_raises(self):
        from domain.data_mapper import _safe_identifier
        with pytest.raises(ValueError):
            _safe_identifier("")

    def test_starts_with_number_raises(self):
        from domain.data_mapper import _safe_identifier
        with pytest.raises(ValueError):
            _safe_identifier("1table")

    def test_sql_injection_rejected(self):
        from domain.data_mapper import _safe_identifier
        with pytest.raises(ValueError):
            _safe_identifier("table' OR 1=1 --")


class TestUCTypeMapping:
    """Tests for _uc_type_to_ecl_type."""

    def test_string_types(self):
        from domain.data_mapper import _uc_type_to_ecl_type
        assert _uc_type_to_ecl_type("STRING") == "TEXT"
        assert _uc_type_to_ecl_type("VARCHAR(255)") == "TEXT"
        assert _uc_type_to_ecl_type("CHAR(10)") == "TEXT"

    def test_integer_types(self):
        from domain.data_mapper import _uc_type_to_ecl_type
        assert _uc_type_to_ecl_type("INT") == "INT"
        assert _uc_type_to_ecl_type("LONG") == "INT"
        assert _uc_type_to_ecl_type("BIGINT") == "INT"
        assert _uc_type_to_ecl_type("TINYINT") == "INT"

    def test_numeric_types(self):
        from domain.data_mapper import _uc_type_to_ecl_type
        assert _uc_type_to_ecl_type("DOUBLE") == "NUMERIC"
        assert _uc_type_to_ecl_type("FLOAT") == "NUMERIC"
        assert _uc_type_to_ecl_type("DECIMAL(10,2)") == "NUMERIC"

    def test_date_types(self):
        from domain.data_mapper import _uc_type_to_ecl_type
        assert _uc_type_to_ecl_type("DATE") == "DATE"
        assert _uc_type_to_ecl_type("TIMESTAMP") == "DATE"

    def test_boolean_types(self):
        from domain.data_mapper import _uc_type_to_ecl_type
        assert _uc_type_to_ecl_type("BOOLEAN") == "BOOLEAN"
        assert _uc_type_to_ecl_type("BOOL") == "BOOLEAN"

    def test_unknown_type_defaults_to_text(self):
        from domain.data_mapper import _uc_type_to_ecl_type
        assert _uc_type_to_ecl_type("ARRAY<STRING>") == "TEXT"
        assert _uc_type_to_ecl_type("MAP<STRING,INT>") == "TEXT"


class TestValidateMapping:
    """Tests for validate_mapping."""

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_unknown_table_returns_invalid(self, mock_cfg, mock_cols):
        from domain.data_mapper import validate_mapping
        mock_cfg.get_config_section.return_value = {"tables": {}}
        result = validate_mapping("nonexistent", "cat.sch.tbl", {})
        assert not result["valid"]
        assert "Unknown ECL table" in result["errors"][0]

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_empty_source_columns_returns_invalid(self, mock_cfg, mock_cols):
        from domain.data_mapper import validate_mapping
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {"mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
                                     "optional_columns": []}}
        }
        mock_cols.return_value = []
        result = validate_mapping("loan_tape", "cat.sch.tbl", {"loan_id": "id"})
        assert not result["valid"]

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_mandatory_unmapped_produces_error(self, mock_cfg, mock_cols):
        from domain.data_mapper import validate_mapping
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [
                    {"name": "loan_id", "type": "TEXT"},
                    {"name": "amount", "type": "NUMERIC"},
                ],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "id", "type": "STRING"}]
        result = validate_mapping("loan_tape", "cat.sch.tbl", {"loan_id": "id"})
        assert not result["valid"]
        assert any("amount" in e for e in result["errors"])

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_all_mandatory_mapped_valid(self, mock_cfg, mock_cols):
        from domain.data_mapper import validate_mapping
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "id", "type": "STRING"}]
        result = validate_mapping("loan_tape", "cat.sch.tbl", {"loan_id": "id"})
        assert result["valid"]

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_type_mismatch_produces_error(self, mock_cfg, mock_cols):
        from domain.data_mapper import validate_mapping
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "loan_date", "type": "DATE"}],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "dt", "type": "BOOLEAN"}]
        result = validate_mapping("loan_tape", "cat.sch.tbl", {"loan_date": "dt"})
        assert not result["valid"]

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_numeric_int_compatibility(self, mock_cfg, mock_cols):
        from domain.data_mapper import validate_mapping
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "amount", "type": "NUMERIC"}],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "amt", "type": "INT"}]
        result = validate_mapping("loan_tape", "cat.sch.tbl", {"amount": "amt"})
        assert result["valid"]  # INT -> NUMERIC is safe widening

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_optional_unmapped_no_error(self, mock_cfg, mock_cols):
        from domain.data_mapper import validate_mapping
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
                "optional_columns": [{"name": "notes", "type": "TEXT"}],
            }}
        }
        mock_cols.return_value = [{"name": "id", "type": "STRING"}]
        result = validate_mapping("loan_tape", "cat.sch.tbl", {"loan_id": "id"})
        assert result["valid"]
        opt_col = [c for c in result["columns"] if c["ecl_column"] == "notes"][0]
        assert opt_col["status"] == "unmapped_optional"


class TestSuggestMappings:
    """Tests for suggest_mappings."""

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_exact_match(self, mock_cfg, mock_cols):
        from domain.data_mapper import suggest_mappings
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "loan_id", "type": "STRING"}]
        result = suggest_mappings("loan_tape", "cat.sch.tbl")
        assert "loan_id" in result["suggestions"]
        assert result["suggestions"]["loan_id"]["confidence"] == "exact"

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_case_insensitive_match(self, mock_cfg, mock_cols):
        from domain.data_mapper import suggest_mappings
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "LOAN_ID", "type": "STRING"}]
        result = suggest_mappings("loan_tape", "cat.sch.tbl")
        assert "loan_id" in result["suggestions"]
        assert result["suggestions"]["loan_id"]["confidence"] == "case_insensitive"

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_normalized_match(self, mock_cfg, mock_cols):
        from domain.data_mapper import suggest_mappings
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "loanid", "type": "STRING"}]
        result = suggest_mappings("loan_tape", "cat.sch.tbl")
        assert "loan_id" in result["suggestions"]
        assert result["suggestions"]["loan_id"]["confidence"] == "normalized"

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_no_match_returns_empty(self, mock_cfg, mock_cols):
        from domain.data_mapper import suggest_mappings
        mock_cfg.get_config_section.return_value = {
            "tables": {"loan_tape": {
                "mandatory_columns": [{"name": "loan_id", "type": "TEXT"}],
                "optional_columns": [],
            }}
        }
        mock_cols.return_value = [{"name": "xyz_abc", "type": "STRING"}]
        result = suggest_mappings("loan_tape", "cat.sch.tbl")
        assert result["matched"] == 0

    @patch("domain.data_mapper.get_uc_table_columns")
    @patch("domain.data_mapper.admin_config")
    def test_unknown_table_returns_empty(self, mock_cfg, mock_cols):
        from domain.data_mapper import suggest_mappings
        mock_cfg.get_config_section.return_value = {"tables": {}}
        result = suggest_mappings("nonexistent", "cat.sch.tbl")
        assert result["suggestions"] == {}


# ═══════════════════════════════════════════════════════════════════
# Section 6: domain/audit_trail.py — Gap Coverage
# ═══════════════════════════════════════════════════════════════════


class TestComputeHashDeep:
    """Additional hash computation tests."""

    def test_hash_is_deterministic_across_calls(self):
        from domain.audit_trail import _compute_hash
        h1 = _compute_hash("GENESIS", "workflow", "p1", "created", {}, "2025-01-01T00:00:00")
        h2 = _compute_hash("GENESIS", "workflow", "p1", "created", {}, "2025-01-01T00:00:00")
        assert h1 == h2

    def test_hash_changes_with_different_timestamp(self):
        from domain.audit_trail import _compute_hash
        h1 = _compute_hash("GENESIS", "workflow", "p1", "created", {}, "2025-01-01T00:00:00")
        h2 = _compute_hash("GENESIS", "workflow", "p1", "created", {}, "2025-01-01T00:00:01")
        assert h1 != h2

    def test_hash_uses_sort_keys_for_detail(self):
        from domain.audit_trail import _compute_hash
        # Order of keys in detail should not matter due to sort_keys=True
        h1 = _compute_hash("GENESIS", "wf", "p1", "act", {"a": 1, "b": 2}, "2025-01-01")
        h2 = _compute_hash("GENESIS", "wf", "p1", "act", {"b": 2, "a": 1}, "2025-01-01")
        assert h1 == h2

    def test_hash_length_is_64_chars(self):
        from domain.audit_trail import _compute_hash
        h = _compute_hash("GENESIS", "wf", "p1", "act", {}, "2025-01-01")
        assert len(h) == 64  # SHA-256 hex


class TestVerifyAuditChainDeep:
    """Additional chain verification tests."""

    @patch("domain.audit_trail.get_audit_trail")
    def test_verify_tampered_hash_detected(self, mock_trail):
        from domain.audit_trail import verify_audit_chain, _compute_hash
        now = "2025-01-01T00:00:00"
        real_hash = _compute_hash("GENESIS", "workflow", "p1", "created", {}, now)
        mock_trail.return_value = [{
            "previous_hash": "GENESIS",
            "entry_hash": "TAMPERED_HASH",  # not the real hash
            "event_type": "workflow",
            "entity_id": "p1",
            "action": "created",
            "detail": {},
            "created_at": now,
        }]
        result = verify_audit_chain("p1")
        assert not result["valid"]
        assert result["broken_at_index"] == 0

    @patch("domain.audit_trail.get_audit_trail")
    def test_verify_tampered_previous_hash_detected(self, mock_trail):
        from domain.audit_trail import verify_audit_chain, _compute_hash
        now = "2025-01-01T00:00:00"
        entry1_hash = _compute_hash("GENESIS", "wf", "p1", "created", {}, now)
        # Entry 2 has wrong previous_hash
        now2 = "2025-01-01T00:00:01"
        entry2_hash = _compute_hash("WRONG_PREV", "wf", "p1", "updated", {}, now2)
        mock_trail.return_value = [
            {"previous_hash": "GENESIS", "entry_hash": entry1_hash,
             "event_type": "wf", "entity_id": "p1", "action": "created",
             "detail": {}, "created_at": now},
            {"previous_hash": "WRONG_PREV", "entry_hash": entry2_hash,
             "event_type": "wf", "entity_id": "p1", "action": "updated",
             "detail": {}, "created_at": now2},
        ]
        result = verify_audit_chain("p1")
        assert not result["valid"]
        assert result["broken_at_index"] == 1

    @patch("domain.audit_trail.get_audit_trail")
    def test_valid_multi_entry_chain(self, mock_trail):
        from domain.audit_trail import verify_audit_chain, _compute_hash
        now1 = "2025-01-01T00:00:00"
        h1 = _compute_hash("GENESIS", "wf", "p1", "created", {}, now1)
        now2 = "2025-01-01T00:01:00"
        h2 = _compute_hash(h1, "wf", "p1", "advanced", {"step": 2}, now2)
        now3 = "2025-01-01T00:02:00"
        h3 = _compute_hash(h2, "wf", "p1", "signed", {}, now3)
        mock_trail.return_value = [
            {"previous_hash": "GENESIS", "entry_hash": h1,
             "event_type": "wf", "entity_id": "p1", "action": "created",
             "detail": {}, "created_at": now1},
            {"previous_hash": h1, "entry_hash": h2,
             "event_type": "wf", "entity_id": "p1", "action": "advanced",
             "detail": {"step": 2}, "created_at": now2},
            {"previous_hash": h2, "entry_hash": h3,
             "event_type": "wf", "entity_id": "p1", "action": "signed",
             "detail": {}, "created_at": now3},
        ]
        result = verify_audit_chain("p1")
        assert result["valid"]
        assert result["entries"] == 3


class TestExportAuditPackageDeep:
    """Additional export audit package tests."""

    @patch("domain.audit_trail.get_config_audit_log")
    @patch("domain.audit_trail.verify_audit_chain")
    @patch("domain.audit_trail.get_audit_trail")
    def test_export_includes_all_keys(self, mock_trail, mock_verify, mock_config_log):
        from domain.audit_trail import export_audit_package
        mock_trail.return_value = []
        mock_verify.return_value = {"valid": True, "entries": 0}
        mock_config_log.return_value = []
        result = export_audit_package("p1")
        assert "project_id" in result
        assert "export_timestamp" in result
        assert "chain_verification" in result
        assert "audit_entries" in result
        assert "config_changes" in result


# ═══════════════════════════════════════════════════════════════════
# Section 7: domain/config_audit.py — Gap Coverage
# ═══════════════════════════════════════════════════════════════════


class TestConfigDiff:
    """Tests for get_config_diff."""

    @patch("domain.config_audit.query_df")
    def test_diff_empty_when_no_changes(self, mock_qdf):
        from domain.config_audit import get_config_diff
        mock_qdf.return_value = pd.DataFrame()
        result = get_config_diff("2025-01-01", "2025-12-31")
        assert result == []

    @patch("domain.config_audit.query_df")
    def test_diff_returns_changes_in_range(self, mock_qdf):
        from domain.config_audit import get_config_diff
        mock_qdf.return_value = pd.DataFrame([{
            "section": "model_config", "config_key": "lgd",
            "old_value": '0.3', "new_value": '0.4',
            "changed_by": "admin", "changed_at": "2025-06-15T10:00:00",
        }])
        result = get_config_diff("2025-01-01", "2025-12-31")
        assert len(result) == 1
        assert result[0]["section"] == "model_config"

    @patch("domain.config_audit.query_df")
    def test_diff_with_section_filter(self, mock_qdf):
        from domain.config_audit import get_config_diff
        mock_qdf.return_value = pd.DataFrame()
        get_config_diff("2025-01-01", section="app_settings")
        call_args = mock_qdf.call_args
        assert "app_settings" in call_args[0][1]

    @patch("domain.config_audit.query_df")
    def test_diff_without_end_time(self, mock_qdf):
        from domain.config_audit import get_config_diff
        mock_qdf.return_value = pd.DataFrame()
        get_config_diff("2025-01-01")
        call_args = mock_qdf.call_args
        # Only start_time in params
        assert len(call_args[0][1]) == 1

    @patch("domain.config_audit.query_df")
    def test_diff_parses_json_values(self, mock_qdf):
        from domain.config_audit import get_config_diff
        mock_qdf.return_value = pd.DataFrame([{
            "section": "model_config", "config_key": "lgd",
            "old_value": '{"value": 0.3}', "new_value": '{"value": 0.4}',
            "changed_by": "admin", "changed_at": "2025-06-15T10:00:00",
        }])
        result = get_config_diff("2025-01-01")
        assert isinstance(result[0]["old_value"], dict)

    @patch("domain.config_audit.query_df")
    def test_diff_handles_non_json_values(self, mock_qdf):
        from domain.config_audit import get_config_diff
        mock_qdf.return_value = pd.DataFrame([{
            "section": "model_config", "config_key": "note",
            "old_value": "plain text",
            "new_value": "updated text",
            "changed_by": "admin", "changed_at": "2025-06-15T10:00:00",
        }])
        result = get_config_diff("2025-01-01")
        # Should not crash on non-JSON values
        assert result[0]["old_value"] == "plain text"

    @patch("domain.config_audit.query_df")
    def test_diff_converts_timestamp_to_iso(self, mock_qdf):
        from domain.config_audit import get_config_diff
        ts = datetime(2025, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_qdf.return_value = pd.DataFrame([{
            "section": "model_config", "config_key": "lgd",
            "old_value": '0.3', "new_value": '0.4',
            "changed_by": "admin", "changed_at": ts,
        }])
        result = get_config_diff("2025-01-01")
        assert isinstance(result[0]["changed_at"], str)


class TestLogConfigChange:
    """Tests for log_config_change."""

    @patch("domain.config_audit.execute")
    def test_inserts_change_record(self, mock_exec):
        from domain.config_audit import log_config_change
        log_config_change("model_config", "lgd_home_loan", 0.3, 0.4, "admin")
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0][1]
        assert args[0] == "model_config"
        assert args[1] == "lgd_home_loan"

    @patch("domain.config_audit.execute")
    def test_inserts_with_null_key(self, mock_exec):
        from domain.config_audit import log_config_change
        log_config_change("app_settings", None, {}, {"theme": "dark"})
        args = mock_exec.call_args[0][1]
        assert args[1] is None


class TestGetConfigAuditLog:
    """Tests for get_config_audit_log."""

    @patch("domain.config_audit.query_df")
    def test_returns_empty_list_for_no_data(self, mock_qdf):
        from domain.config_audit import get_config_audit_log
        mock_qdf.return_value = pd.DataFrame()
        result = get_config_audit_log()
        assert result == []

    @patch("domain.config_audit.query_df")
    def test_returns_records_with_parsed_json(self, mock_qdf):
        from domain.config_audit import get_config_audit_log
        mock_qdf.return_value = pd.DataFrame([{
            "id": 1, "section": "model_config", "config_key": "lgd",
            "old_value": '0.3', "new_value": '0.4',
            "changed_by": "admin", "changed_at": "2025-06-15T10:00:00",
        }])
        result = get_config_audit_log()
        assert len(result) == 1

    @patch("domain.config_audit.query_df")
    def test_section_filter_applied(self, mock_qdf):
        from domain.config_audit import get_config_audit_log
        mock_qdf.return_value = pd.DataFrame()
        get_config_audit_log(section="model_config")
        call_args = mock_qdf.call_args
        assert "model_config" in call_args[0][1]


# ═══════════════════════════════════════════════════════════════════
# Section 8: domain/model_runs.py — Gap Coverage
# ═══════════════════════════════════════════════════════════════════


class TestModelRunsGapCoverage:
    """Additional tests for model_runs functions not covered by existing suite."""

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_get_cohort_summary(self, mock_exec, mock_qdf):
        from domain.model_runs import get_cohort_summary
        mock_qdf.return_value = pd.DataFrame([{
            "product_type": "Personal Loans", "cohort_id": 2023,
            "loan_count": 500, "total_gca": 2500000, "avg_pd": 0.05,
            "avg_dpd": 10.0, "stage1": 400, "stage2": 80, "stage3": 20,
        }])
        result = get_cohort_summary()
        assert "cohort_id" in result.columns
        assert not result.empty

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_get_cohort_summary_by_product(self, mock_exec, mock_qdf):
        from domain.model_runs import get_cohort_summary_by_product
        mock_qdf.return_value = pd.DataFrame([{
            "cohort_id": 2023, "loan_count": 200,
            "total_gca": 1000000, "avg_pd": 0.04,
        }])
        result = get_cohort_summary_by_product("Personal Loans")
        assert not result.empty
        # Verify product filter parameter passed
        call_args = mock_qdf.call_args
        assert call_args[0][1] == ("Personal Loans",)

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_get_stage_by_cohort(self, mock_exec, mock_qdf):
        from domain.model_runs import get_stage_by_cohort
        mock_qdf.return_value = pd.DataFrame([{
            "cohort_id": 2023, "assessed_stage": 1,
            "loan_count": 300, "total_gca": 1500000,
        }])
        result = get_stage_by_cohort("Auto Loans")
        call_args = mock_qdf.call_args
        assert call_args[0][1] == ("Auto Loans",)

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_get_ecl_by_cohort_with_auto_dimension(self, mock_exec, mock_qdf):
        from domain.model_runs import get_ecl_by_cohort
        # First call: column detection
        cols_df = pd.DataFrame({"column_name": ["credit_grade", "assessed_stage", "vintage_year"]})
        # Second call: actual ECL data
        ecl_df = pd.DataFrame([{
            "cohort_id": "A", "loan_count": 100, "total_gca": 500000,
            "total_ecl": 10000, "coverage_ratio": 2.0,
        }])
        mock_qdf.side_effect = [cols_df, ecl_df]
        result = get_ecl_by_cohort("Personal Loans", "auto")
        assert isinstance(result, pd.DataFrame)

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_get_portfolio_by_cohort_delegates(self, mock_exec, mock_qdf):
        from domain.model_runs import get_portfolio_by_cohort
        cols_df = pd.DataFrame({"column_name": ["assessed_stage"]})
        data_df = pd.DataFrame([{"cohort_id": "Stage 1", "loan_count": 100}])
        mock_qdf.side_effect = [cols_df, data_df]
        result = get_portfolio_by_cohort("Personal Loans")
        assert isinstance(result, pd.DataFrame)

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_save_model_run_upsert(self, mock_exec, mock_qdf):
        from domain.model_runs import save_model_run
        mock_qdf.return_value = pd.DataFrame([{
            "run_id": "run-1", "run_type": "satellite_model",
            "models_used": '["ols", "ridge"]', "products": '["PL"]',
            "total_cohorts": 5, "best_model_summary": '{}',
            "status": "completed", "notes": "test",
            "created_by": "system", "run_timestamp": "2025-01-01",
        }])
        result = save_model_run("run-1", "satellite_model", ["ols", "ridge"],
                                ["PL"], 5, {}, "test")
        assert result is not None
        # Verify INSERT ON CONFLICT in one of the execute calls
        all_sqls = [c[0][0] for c in mock_exec.call_args_list]
        assert any("ON CONFLICT" in sql for sql in all_sqls)

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_get_satellite_model_selected_no_filter(self, mock_exec, mock_qdf):
        from domain.model_runs import get_satellite_model_selected
        mock_qdf.return_value = pd.DataFrame()
        get_satellite_model_selected()
        sql = mock_qdf.call_args[0][0]
        assert "WHERE" not in sql.split("FROM")[1]  # No WHERE clause

    @patch("domain.model_runs.query_df")
    @patch("domain.model_runs.execute")
    def test_get_satellite_model_selected_with_filter(self, mock_exec, mock_qdf):
        from domain.model_runs import get_satellite_model_selected
        mock_qdf.return_value = pd.DataFrame()
        get_satellite_model_selected(run_id="2025-01-01")
        call_args = mock_qdf.call_args
        assert call_args[0][1] == ("2025-01-01",)
