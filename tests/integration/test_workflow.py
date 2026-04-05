"""
End-to-end workflow integration test with mocked DB.

Simulates the full IFRS 9 project lifecycle:
  Create project -> advance through steps -> sign off
Verifies step_status transitions and audit_log accumulation.
"""
import json
import copy
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone

import backend
from backend import STEPS


class InMemoryWorkflowStore:
    """Simulates the workflow table in memory for end-to-end testing.

    Intercepts backend.execute and backend.query_df calls to maintain
    a consistent in-memory project state without a real database.
    """

    def __init__(self):
        self.projects: dict[str, dict] = {}

    def create_project(self, project_id, name, ptype, desc, rdate, owner_id="usr-004"):
        step_status = {s: "pending" for s in STEPS}
        step_status["create_project"] = "completed"
        audit = [{
            "ts": datetime.now(timezone.utc).isoformat(),
            "user": "Current User",
            "action": "Project Created",
            "detail": f"{name} initialized",
            "step": "create_project",
        }]
        self.projects[project_id] = {
            "project_id": project_id,
            "project_name": name,
            "project_type": ptype,
            "description": desc,
            "reporting_date": rdate,
            "owner_id": owner_id,
            "current_step": 1,
            "step_status": step_status,
            "audit_log": audit,
            "overlays": [],
            "scenario_weights": {},
            "signed_off_by": None,
            "signed_off_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return copy.deepcopy(self.projects[project_id])

    def get_project(self, project_id):
        proj = self.projects.get(project_id)
        return copy.deepcopy(proj) if proj else None

    def advance_step(self, project_id, step_name, action, user, detail, status="completed"):
        proj = self.projects.get(project_id)
        if not proj:
            raise ValueError(f"Project {project_id} not found")

        proj["step_status"][step_name] = status
        step_idx = STEPS.index(step_name) if step_name in STEPS else proj["current_step"]
        if status == "completed":
            proj["current_step"] = max(proj["current_step"], step_idx + 1)

        proj["audit_log"].append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "action": action,
            "detail": detail,
            "step": step_name,
        })
        proj["updated_at"] = datetime.now(timezone.utc).isoformat()
        return copy.deepcopy(proj)

    def save_overlays(self, project_id, overlays):
        proj = self.projects.get(project_id)
        if proj:
            proj["overlays"] = overlays
            proj["updated_at"] = datetime.now(timezone.utc).isoformat()
        return copy.deepcopy(proj) if proj else None

    def save_scenario_weights(self, project_id, weights):
        proj = self.projects.get(project_id)
        if proj:
            proj["scenario_weights"] = weights
            proj["updated_at"] = datetime.now(timezone.utc).isoformat()
        return copy.deepcopy(proj) if proj else None

    def sign_off(self, project_id, user, attestation_data=None):
        proj = self.projects.get(project_id)
        if not proj:
            raise ValueError("Project not found")
        proj["step_status"]["sign_off"] = "completed"
        proj["current_step"] = len(STEPS)
        proj["signed_off_by"] = user
        proj["signed_off_at"] = datetime.now(timezone.utc).isoformat()
        proj["audit_log"].append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "action": "Final Sign-Off",
            "detail": "Project signed off and locked",
            "step": "sign_off",
        })
        return copy.deepcopy(proj)


@pytest.fixture
def workflow_store():
    return InMemoryWorkflowStore()


@pytest.fixture
def patched_backend(workflow_store, mock_db):
    """Patch backend workflow functions to use the in-memory store."""
    with patch("backend.create_project", side_effect=workflow_store.create_project), \
         patch("backend.get_project", side_effect=workflow_store.get_project), \
         patch("backend.advance_step", side_effect=workflow_store.advance_step), \
         patch("backend.save_overlays", side_effect=workflow_store.save_overlays), \
         patch("backend.save_scenario_weights", side_effect=workflow_store.save_scenario_weights), \
         patch("backend.sign_off_project", side_effect=workflow_store.sign_off):
        yield workflow_store


@pytest.fixture
def wf_client(patched_backend):
    """FastAPI TestClient wired to the in-memory workflow store."""
    from fastapi.testclient import TestClient
    import app as app_module
    return TestClient(app_module.app)


class TestFullWorkflowLifecycle:
    """End-to-end: create project -> advance all steps -> sign off."""

    def test_complete_lifecycle(self, wf_client, patched_backend):
        resp = wf_client.post("/api/projects", json={
            "project_id": "wf-e2e-001",
            "project_name": "E2E Workflow Test",
            "project_type": "ifrs9",
            "description": "Full lifecycle test",
            "reporting_date": "2025-12-31",
        })
        assert resp.status_code == 200
        project = resp.json()
        assert project["current_step"] == 1
        assert project["step_status"]["create_project"] == "completed"
        assert len(project["audit_log"]) == 1

        workflow_steps = [
            ("data_processing", "Data Processing Complete", "Data Engineer", "Loaded 84K loans"),
            ("data_control", "Data Quality Passed", "Data Analyst", "All DQ checks passed"),
            ("satellite_model", "Models Fitted", "Quant Analyst", "8 models fitted per cohort"),
            ("model_execution", "ECL Calculated", "Risk Engine", "Monte Carlo simulation complete"),
            ("stress_testing", "Stress Tests Done", "Risk Manager", "8 scenarios evaluated"),
            ("overlays", "Overlays Applied", "Credit Committee", "Management overlays submitted"),
        ]

        for step_name, action, user, detail in workflow_steps:
            resp = wf_client.post(f"/api/projects/wf-e2e-001/advance", json={
                "action": step_name,
                "user": user,
                "detail": detail,
            })
            assert resp.status_code == 200
            project = resp.json()
            assert project["step_status"][step_name] == "completed", \
                f"Step {step_name} should be completed"

        assert project["current_step"] == 7
        assert len(project["audit_log"]) == 7

        resp = wf_client.post("/api/projects/wf-e2e-001/sign-off", json={
            "name": "Chief Risk Officer",
        })
        assert resp.status_code == 200
        final = resp.json()
        assert final["signed_off_by"] == "Chief Risk Officer"
        assert final["step_status"]["sign_off"] == "completed"
        assert final["current_step"] == len(STEPS)
        assert len(final["audit_log"]) == 8

    def test_step_status_transitions(self, wf_client, patched_backend):
        """Verify each step transitions from pending to completed."""
        wf_client.post("/api/projects", json={
            "project_id": "wf-trans-001",
            "project_name": "Transition Test",
        })

        resp = wf_client.post("/api/projects/wf-trans-001/advance", json={
            "action": "data_processing",
            "user": "Engineer",
            "detail": "Done",
        })
        project = resp.json()
        assert project["step_status"]["data_processing"] == "completed"
        assert project["step_status"]["data_control"] == "pending"
        assert project["step_status"]["satellite_model"] == "pending"

    def test_audit_log_accumulates(self, wf_client, patched_backend):
        """Verify audit_log grows with each action."""
        wf_client.post("/api/projects", json={
            "project_id": "wf-audit-001",
            "project_name": "Audit Test",
        })

        for i, step in enumerate(["data_processing", "data_control", "satellite_model"]):
            resp = wf_client.post("/api/projects/wf-audit-001/advance", json={
                "action": step,
                "user": f"User {i}",
                "detail": f"Step {step} done",
            })
            project = resp.json()
            expected_entries = 1 + (i + 1)
            assert len(project["audit_log"]) == expected_entries

        last_entry = project["audit_log"][-1]
        assert last_entry["step"] == "satellite_model"
        assert last_entry["user"] == "User 2"

    def test_overlays_and_weights_persist(self, wf_client, patched_backend):
        """Verify overlays and scenario weights are saved correctly."""
        wf_client.post("/api/projects", json={
            "project_id": "wf-overlay-001",
            "project_name": "Overlay Test",
        })

        resp = wf_client.post("/api/projects/wf-overlay-001/scenario-weights", json={
            "weights": {"baseline": 0.40, "adverse": 0.35, "tail_risk": 0.25},
        })
        assert resp.status_code == 200
        project = resp.json()
        assert project["scenario_weights"]["baseline"] == 0.40

        resp = wf_client.post("/api/projects/wf-overlay-001/overlays", json={
            "overlays": [
                {
                    "id": "ovl-1",
                    "product": "emergency_microloan",
                    "type": "absolute",
                    "amount": 50000.0,
                    "reason": "Sector-specific risk adjustment",
                },
            ],
        })
        assert resp.status_code == 200
        project = resp.json()
        assert len(project["overlays"]) == 1
        assert project["overlays"][0]["product"] == "emergency_microloan"


class TestWorkflowErrorCases:
    """Error handling in the workflow lifecycle."""

    def test_advance_nonexistent_project(self, wf_client, patched_backend):
        resp = wf_client.post("/api/projects/does-not-exist/advance", json={
            "action": "data_processing",
            "user": "Nobody",
        })
        assert resp.status_code == 404

    def test_get_nonexistent_project(self, wf_client, patched_backend):
        with patch("backend.get_project", return_value=None):
            resp = wf_client.get("/api/projects/does-not-exist")
        assert resp.status_code == 404
