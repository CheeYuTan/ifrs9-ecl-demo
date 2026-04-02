"""
QA Sprint 4 — GL Journals, Reports, RBAC Endpoints.

Tests routes/gl_journals.py (7 endpoints), routes/reports.py (6 endpoints),
and routes/rbac.py (8 endpoints) with mocked backend.
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(mock_db):
    import app as app_module
    return TestClient(app_module.app)


def _journal_dict(**overrides):
    base = {
        "journal_id": "JRN-001",
        "project_id": "proj-001",
        "journal_date": "2025-12-31",
        "journal_type": "ecl_provision",
        "status": "draft",
        "created_by": "system",
        "posted_by": None,
        "posted_at": None,
        "description": "ECL provision journal",
        "lines": [
            {"account_code": "4100", "account_name": "ECL Expense",
             "debit": Decimal("50000.00"), "credit": Decimal("0.00")},
            {"account_code": "2100", "account_name": "ECL Provision",
             "debit": Decimal("0.00"), "credit": Decimal("50000.00")},
        ],
        "total_debits": Decimal("50000.00"),
        "total_credits": Decimal("50000.00"),
    }
    base.update(overrides)
    return base


def _report_dict(**overrides):
    base = {
        "report_id": "RPT-001",
        "project_id": "proj-001",
        "report_type": "ifrs7_disclosure",
        "report_date": "2025-12-31",
        "status": "draft",
        "generated_by": "system",
        "report_data": json.dumps({
            "report_type": "ifrs7_disclosure",
            "project_id": "proj-001",
            "report_date": "2025-12-31",
            "generated_at": "2025-12-31T00:00:00",
            "sections": {
                "35H": {
                    "title": "Loss Allowance Reconciliation",
                    "data": [
                        {"stage": "Stage 1", "opening": 10000, "closing": 12000},
                        {"stage": "Stage 2", "opening": 5000, "closing": 6000},
                    ],
                },
            },
        }),
        "created_at": "2025-12-31T00:00:00",
    }
    base.update(overrides)
    return base


def _user_dict(user_id="usr-001", role="analyst"):
    perms = {
        "analyst": ["create_models", "run_backtests", "view_portfolio", "view_reports",
                     "generate_journals", "create_overlays"],
        "approver": ["create_models", "run_backtests", "view_portfolio", "view_reports",
                      "generate_journals", "create_overlays", "submit_for_approval",
                      "review_models", "review_overlays", "approve_requests",
                      "reject_requests", "sign_off_projects", "post_journals"],
        "admin": ["create_models", "run_backtests", "view_portfolio", "view_reports",
                   "generate_journals", "create_overlays", "submit_for_approval",
                   "review_models", "review_overlays", "approve_requests",
                   "reject_requests", "sign_off_projects", "post_journals",
                   "manage_users", "manage_config", "manage_roles"],
    }
    return {
        "user_id": user_id,
        "email": f"{user_id}@bank.com",
        "display_name": "Test User",
        "role": role,
        "department": "Risk",
        "is_active": True,
        "permissions": perms.get(role, perms["analyst"]),
    }


def _approval_dict(**overrides):
    base = {
        "request_id": "apr-001",
        "request_type": "model_approval",
        "entity_id": "MDL-001",
        "entity_type": "model",
        "status": "pending",
        "requested_by": "usr-001",
        "assigned_to": "usr-003",
        "approved_by": None,
        "approved_at": None,
        "rejection_reason": "",
        "comments": "Please review",
        "priority": "normal",
        "due_date": None,
        "created_at": "2025-12-31T00:00:00",
        "requested_by_name": "Ana Reyes",
        "assigned_to_name": "Sarah Chen",
        "approved_by_name": None,
    }
    base.update(overrides)
    return base


# ===================================================================
# GL JOURNAL ROUTES — /api/gl/*
# ===================================================================

class TestGlGenerateJournals:
    """POST /api/gl/generate/{project_id}"""

    def test_generate_returns_journal(self, client):
        with patch("backend.generate_ecl_journals", return_value=_journal_dict()):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "analyst"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["journal_id"] == "JRN-001"
        assert data["journal_type"] == "ecl_provision"

    def test_generate_double_entry_balanced(self, client):
        journal = _journal_dict()
        with patch("backend.generate_ecl_journals", return_value=journal):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "analyst"})
        data = resp.json()
        total_dr = sum(float(l.get("debit", 0)) for l in data["lines"])
        total_cr = sum(float(l.get("credit", 0)) for l in data["lines"])
        assert abs(total_dr - total_cr) < 0.01, "Double-entry: debits must equal credits"

    def test_generate_value_error_returns_400(self, client):
        with patch("backend.generate_ecl_journals", side_effect=ValueError("No ECL data")):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "x"})
        assert resp.status_code == 400
        assert "No ECL data" in resp.json()["detail"]

    def test_generate_exception_returns_500(self, client):
        with patch("backend.generate_ecl_journals", side_effect=RuntimeError("DB down")):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "x"})
        assert resp.status_code == 500

    def test_generate_default_user(self, client):
        with patch("backend.generate_ecl_journals", return_value=_journal_dict()) as mock:
            resp = client.post("/api/gl/generate/proj-001", json={})
        assert resp.status_code == 200
        mock.assert_called_once_with("proj-001", "system")


class TestGlListJournals:
    """GET /api/gl/journals/{project_id}"""

    def test_list_returns_journals(self, client):
        with patch("backend.list_journals", return_value=[_journal_dict()]):
            resp = client.get("/api/gl/journals/proj-001")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1

    def test_list_empty(self, client):
        with patch("backend.list_journals", return_value=[]):
            resp = client.get("/api/gl/journals/proj-001")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_exception_returns_500(self, client):
        with patch("backend.list_journals", side_effect=RuntimeError("fail")):
            resp = client.get("/api/gl/journals/proj-001")
        assert resp.status_code == 500


class TestGlGetJournal:
    """GET /api/gl/journal/{journal_id}"""

    def test_get_returns_journal(self, client):
        with patch("backend.get_journal", return_value=_journal_dict()):
            resp = client.get("/api/gl/journal/JRN-001")
        assert resp.status_code == 200
        assert resp.json()["journal_id"] == "JRN-001"

    def test_get_not_found_returns_404(self, client):
        with patch("backend.get_journal", return_value=None):
            resp = client.get("/api/gl/journal/MISSING")
        assert resp.status_code == 404

    def test_get_exception_returns_500(self, client):
        with patch("backend.get_journal", side_effect=RuntimeError("fail")):
            resp = client.get("/api/gl/journal/JRN-001")
        assert resp.status_code == 500


class TestGlPostJournal:
    """POST /api/gl/journal/{journal_id}/post"""

    def test_post_journal(self, client):
        posted = _journal_dict(status="posted", posted_by="usr-003")
        with patch("backend.post_journal", return_value=posted):
            resp = client.post("/api/gl/journal/JRN-001/post", json={"user": "usr-003"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "posted"

    def test_post_already_posted_returns_400(self, client):
        with patch("backend.post_journal", side_effect=ValueError("Already posted")):
            resp = client.post("/api/gl/journal/JRN-001/post", json={"user": "usr-003"})
        assert resp.status_code == 400

    def test_post_exception_returns_500(self, client):
        with patch("backend.post_journal", side_effect=RuntimeError("fail")):
            resp = client.post("/api/gl/journal/JRN-001/post", json={"user": "x"})
        assert resp.status_code == 500


class TestGlReverseJournal:
    """POST /api/gl/journal/{journal_id}/reverse"""

    def test_reverse_journal(self, client):
        reversed_j = _journal_dict(status="reversed", journal_type="reversal")
        with patch("backend.reverse_journal", return_value=reversed_j):
            resp = client.post("/api/gl/journal/JRN-001/reverse",
                               json={"user": "usr-003", "reason": "Error"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "reversed"

    def test_reverse_value_error_returns_400(self, client):
        with patch("backend.reverse_journal", side_effect=ValueError("Not posted")):
            resp = client.post("/api/gl/journal/JRN-001/reverse",
                               json={"user": "x", "reason": "test"})
        assert resp.status_code == 400

    def test_reverse_default_reason(self, client):
        with patch("backend.reverse_journal", return_value=_journal_dict()) as mock:
            resp = client.post("/api/gl/journal/JRN-001/reverse", json={"user": "x"})
        assert resp.status_code == 200
        mock.assert_called_once_with("JRN-001", "x", "")


class TestGlTrialBalance:
    """GET /api/gl/trial-balance/{project_id}"""

    def test_trial_balance(self, client):
        tb = {
            "accounts": [
                {"account_code": "4100", "debit": 50000, "credit": 0},
                {"account_code": "2100", "debit": 0, "credit": 50000},
            ],
            "total_debits": 50000,
            "total_credits": 50000,
        }
        with patch("backend.get_gl_trial_balance", return_value=tb):
            resp = client.get("/api/gl/trial-balance/proj-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_debits"] == data["total_credits"]

    def test_trial_balance_exception(self, client):
        with patch("backend.get_gl_trial_balance", side_effect=RuntimeError("fail")):
            resp = client.get("/api/gl/trial-balance/proj-001")
        assert resp.status_code == 500


class TestGlChartOfAccounts:
    """GET /api/gl/chart-of-accounts"""

    def test_chart_of_accounts(self, client):
        chart = [
            {"account_code": "4100", "account_name": "ECL Expense", "account_type": "expense"},
            {"account_code": "2100", "account_name": "Provision", "account_type": "liability"},
        ]
        with patch("backend.get_gl_chart", return_value=chart):
            resp = client.get("/api/gl/chart-of-accounts")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_chart_exception(self, client):
        with patch("backend.get_gl_chart", side_effect=RuntimeError("fail")):
            resp = client.get("/api/gl/chart-of-accounts")
        assert resp.status_code == 500


# ===================================================================
# REPORT ROUTES — /api/reports/*
# ===================================================================

REPORT_TYPES = [
    "ifrs7_disclosure", "ecl_movement", "stage_migration",
    "sensitivity_analysis", "concentration_risk",
]

REPORT_GENERATORS = {
    "ifrs7_disclosure": "backend.generate_ifrs7_disclosure",
    "ecl_movement": "backend.generate_ecl_movement_report",
    "stage_migration": "backend.generate_stage_migration_report",
    "sensitivity_analysis": "backend.generate_sensitivity_report",
    "concentration_risk": "backend.generate_concentration_report",
}


class TestGenerateReport:
    """POST /api/reports/generate/{project_id}"""

    @pytest.mark.parametrize("report_type", REPORT_TYPES)
    def test_generate_each_type(self, client, report_type):
        result = _report_dict(report_type=report_type)
        with patch(REPORT_GENERATORS[report_type], return_value=result):
            resp = client.post("/api/reports/generate/proj-001",
                               json={"report_type": report_type, "user": "analyst"})
        assert resp.status_code == 200
        assert resp.json()["report_type"] == report_type

    def test_unknown_type_returns_400(self, client):
        resp = client.post("/api/reports/generate/proj-001",
                           json={"report_type": "nonexistent"})
        assert resp.status_code == 400
        assert "Unknown report type" in resp.json()["detail"]

    def test_value_error_returns_400(self, client):
        with patch("backend.generate_ifrs7_disclosure", side_effect=ValueError("No data")):
            resp = client.post("/api/reports/generate/proj-001",
                               json={"report_type": "ifrs7_disclosure"})
        assert resp.status_code == 400

    def test_exception_returns_500(self, client):
        with patch("backend.generate_ifrs7_disclosure", side_effect=RuntimeError("fail")):
            resp = client.post("/api/reports/generate/proj-001",
                               json={"report_type": "ifrs7_disclosure"})
        assert resp.status_code == 500

    def test_default_user_is_system(self, client):
        with patch("backend.generate_ifrs7_disclosure", return_value=_report_dict()) as mock:
            resp = client.post("/api/reports/generate/proj-001",
                               json={"report_type": "ifrs7_disclosure"})
        assert resp.status_code == 200
        mock.assert_called_once_with("proj-001", "system")


class TestListReports:
    """GET /api/reports"""

    def test_list_all(self, client):
        reports = [_report_dict(), _report_dict(report_id="RPT-002")]
        with patch("backend.list_reports", return_value=reports):
            resp = client.get("/api/reports")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_by_project(self, client):
        with patch("backend.list_reports", return_value=[_report_dict()]) as mock:
            resp = client.get("/api/reports?project_id=proj-001")
        assert resp.status_code == 200
        mock.assert_called_once_with("proj-001", None)

    def test_list_by_type(self, client):
        with patch("backend.list_reports", return_value=[]) as mock:
            resp = client.get("/api/reports?report_type=ecl_movement")
        assert resp.status_code == 200
        mock.assert_called_once_with(None, "ecl_movement")

    def test_list_exception(self, client):
        with patch("backend.list_reports", side_effect=RuntimeError("fail")):
            resp = client.get("/api/reports")
        assert resp.status_code == 500


class TestGetReport:
    """GET /api/reports/{report_id}"""

    def test_get_report(self, client):
        with patch("backend.get_report", return_value=_report_dict()):
            resp = client.get("/api/reports/RPT-001")
        assert resp.status_code == 200
        assert resp.json()["report_id"] == "RPT-001"

    def test_get_not_found(self, client):
        with patch("backend.get_report", return_value=None):
            resp = client.get("/api/reports/MISSING")
        assert resp.status_code == 404

    def test_get_exception(self, client):
        with patch("backend.get_report", side_effect=RuntimeError("fail")):
            resp = client.get("/api/reports/RPT-001")
        assert resp.status_code == 500


class TestExportReportCsv:
    """GET /api/reports/{report_id}/export"""

    def test_export_csv(self, client):
        rows = [
            {"section": "35H", "stage": "Stage 1", "opening": 10000},
            {"section": "35H", "stage": "Stage 2", "opening": 5000},
        ]
        with patch("backend.export_report_csv", return_value=rows):
            resp = client.get("/api/reports/RPT-001/export")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "Stage 1" in resp.text

    def test_export_empty_returns_404(self, client):
        with patch("backend.export_report_csv", return_value=[]):
            resp = client.get("/api/reports/RPT-001/export")
        assert resp.status_code == 404

    def test_export_none_returns_404(self, client):
        with patch("backend.export_report_csv", return_value=None):
            resp = client.get("/api/reports/RPT-001/export")
        assert resp.status_code == 404

    def test_export_exception(self, client):
        with patch("backend.export_report_csv", side_effect=RuntimeError("fail")):
            resp = client.get("/api/reports/RPT-001/export")
        assert resp.status_code == 500


class TestFinalizeReport:
    """POST /api/reports/{report_id}/finalize"""

    def test_finalize(self, client):
        final = _report_dict(status="final")
        with patch("backend.finalize_report", return_value=final):
            resp = client.post("/api/reports/RPT-001/finalize")
        assert resp.status_code == 200
        assert resp.json()["status"] == "final"

    def test_finalize_not_found(self, client):
        with patch("backend.finalize_report", return_value=None):
            resp = client.post("/api/reports/MISSING/finalize")
        assert resp.status_code == 404

    def test_finalize_exception(self, client):
        with patch("backend.finalize_report", side_effect=RuntimeError("fail")):
            resp = client.post("/api/reports/RPT-001/finalize")
        assert resp.status_code == 500


class TestExportReportPdf:
    """GET /api/reports/{report_id}/export/pdf"""

    def test_export_pdf(self, client):
        report = _report_dict()
        report["report_data"] = json.loads(report["report_data"])
        with patch("backend.get_report", return_value=report), \
             patch("reporting.pdf_export.generate_report_pdf", return_value=b"%PDF-1.4 test"):
            resp = client.get("/api/reports/RPT-001/export/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")

    def test_export_pdf_not_found(self, client):
        with patch("backend.get_report", return_value=None):
            resp = client.get("/api/reports/MISSING/export/pdf")
        assert resp.status_code == 404

    def test_export_pdf_report_data_as_string(self, client):
        report = _report_dict()  # report_data is already JSON string
        with patch("backend.get_report", return_value=report), \
             patch("reporting.pdf_export.generate_report_pdf", return_value=b"%PDF-test"):
            resp = client.get("/api/reports/RPT-001/export/pdf")
        assert resp.status_code == 200

    def test_export_pdf_generation_failure(self, client):
        report = _report_dict()
        report["report_data"] = json.loads(report["report_data"])
        with patch("backend.get_report", return_value=report), \
             patch("reporting.pdf_export.generate_report_pdf", side_effect=RuntimeError("PDF fail")):
            resp = client.get("/api/reports/RPT-001/export/pdf")
        assert resp.status_code == 500


# ===================================================================
# RBAC ROUTES — /api/rbac/*
# ===================================================================

class TestRbacListUsers:
    """GET /api/rbac/users"""

    def test_list_all_users(self, client):
        users = [_user_dict(), _user_dict(user_id="usr-002", role="approver")]
        with patch("backend.list_users", return_value=users):
            resp = client.get("/api/rbac/users")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_by_role(self, client):
        with patch("backend.list_users", return_value=[_user_dict()]) as mock:
            resp = client.get("/api/rbac/users?role=analyst")
        assert resp.status_code == 200
        mock.assert_called_once_with("analyst")

    def test_list_exception(self, client):
        with patch("backend.list_users", side_effect=RuntimeError("fail")):
            resp = client.get("/api/rbac/users")
        assert resp.status_code == 500


class TestRbacGetUser:
    """GET /api/rbac/users/{user_id}"""

    def test_get_user(self, client):
        with patch("backend.get_user", return_value=_user_dict()):
            resp = client.get("/api/rbac/users/usr-001")
        assert resp.status_code == 200
        assert resp.json()["role"] == "analyst"

    def test_get_not_found(self, client):
        with patch("backend.get_user", return_value=None):
            resp = client.get("/api/rbac/users/MISSING")
        assert resp.status_code == 404

    def test_get_exception(self, client):
        with patch("backend.get_user", side_effect=RuntimeError("fail")):
            resp = client.get("/api/rbac/users/usr-001")
        assert resp.status_code == 500


class TestRbacListApprovals:
    """GET /api/rbac/approvals"""

    def test_list_all(self, client):
        with patch("backend.list_approval_requests", return_value=[_approval_dict()]):
            resp = client.get("/api/rbac/approvals")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_by_status(self, client):
        with patch("backend.list_approval_requests", return_value=[]) as mock:
            resp = client.get("/api/rbac/approvals?status=pending")
        mock.assert_called_once_with("pending", None, None)

    def test_list_by_assigned_to(self, client):
        with patch("backend.list_approval_requests", return_value=[]) as mock:
            resp = client.get("/api/rbac/approvals?assigned_to=usr-003")
        mock.assert_called_once_with(None, "usr-003", None)

    def test_list_by_type(self, client):
        with patch("backend.list_approval_requests", return_value=[]) as mock:
            resp = client.get("/api/rbac/approvals?type=model_approval")
        mock.assert_called_once_with(None, None, "model_approval")

    def test_list_exception(self, client):
        with patch("backend.list_approval_requests", side_effect=RuntimeError("fail")):
            resp = client.get("/api/rbac/approvals")
        assert resp.status_code == 500


class TestRbacCreateApproval:
    """POST /api/rbac/approvals"""

    def test_create_approval(self, client):
        with patch("backend.create_approval_request", return_value=_approval_dict()):
            resp = client.post("/api/rbac/approvals", json={
                "request_type": "model_approval",
                "entity_id": "MDL-001",
                "entity_type": "model",
                "requested_by": "usr-001",
                "assigned_to": "usr-003",
            })
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_create_with_priority(self, client):
        with patch("backend.create_approval_request", return_value=_approval_dict(priority="high")) as mock:
            resp = client.post("/api/rbac/approvals", json={
                "request_type": "model_approval",
                "entity_id": "MDL-001",
                "requested_by": "usr-001",
                "priority": "high",
            })
        assert resp.status_code == 200

    def test_create_exception(self, client):
        with patch("backend.create_approval_request", side_effect=RuntimeError("fail")):
            resp = client.post("/api/rbac/approvals", json={
                "request_type": "model_approval",
                "entity_id": "MDL-001",
                "requested_by": "usr-001",
            })
        assert resp.status_code == 500


class TestRbacApprove:
    """POST /api/rbac/approvals/{request_id}/approve"""

    def test_approve(self, client):
        approved = _approval_dict(status="approved", approved_by="usr-003")
        with patch("backend.approve_request", return_value=approved):
            resp = client.post("/api/rbac/approvals/apr-001/approve",
                               json={"user_id": "usr-003", "comment": "Looks good"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_approve_no_permission_returns_400(self, client):
        with patch("backend.approve_request",
                   side_effect=ValueError("Role 'analyst' does not have permission 'approve_requests'")):
            resp = client.post("/api/rbac/approvals/apr-001/approve",
                               json={"user_id": "usr-001"})
        assert resp.status_code == 400
        assert "permission" in resp.json()["detail"].lower()

    def test_approve_already_processed_returns_400(self, client):
        with patch("backend.approve_request",
                   side_effect=ValueError("Request is already approved")):
            resp = client.post("/api/rbac/approvals/apr-001/approve",
                               json={"user_id": "usr-003"})
        assert resp.status_code == 400

    def test_approve_exception(self, client):
        with patch("backend.approve_request", side_effect=RuntimeError("fail")):
            resp = client.post("/api/rbac/approvals/apr-001/approve",
                               json={"user_id": "usr-003"})
        assert resp.status_code == 500


class TestRbacReject:
    """POST /api/rbac/approvals/{request_id}/reject"""

    def test_reject(self, client):
        rejected = _approval_dict(status="rejected", approved_by="usr-003")
        with patch("backend.reject_request", return_value=rejected):
            resp = client.post("/api/rbac/approvals/apr-001/reject",
                               json={"user_id": "usr-003", "comment": "Needs revision"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_reject_no_permission_returns_400(self, client):
        with patch("backend.reject_request",
                   side_effect=ValueError("Role 'analyst' does not have permission")):
            resp = client.post("/api/rbac/approvals/apr-001/reject",
                               json={"user_id": "usr-001"})
        assert resp.status_code == 400

    def test_reject_exception(self, client):
        with patch("backend.reject_request", side_effect=RuntimeError("fail")):
            resp = client.post("/api/rbac/approvals/apr-001/reject",
                               json={"user_id": "usr-003"})
        assert resp.status_code == 500


class TestRbacApprovalHistory:
    """GET /api/rbac/approvals/history/{entity_id}"""

    def test_history(self, client):
        history = [_approval_dict(), _approval_dict(status="approved")]
        with patch("backend.get_approval_history", return_value=history):
            resp = client.get("/api/rbac/approvals/history/MDL-001")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_history_empty(self, client):
        with patch("backend.get_approval_history", return_value=[]):
            resp = client.get("/api/rbac/approvals/history/MDL-999")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_exception(self, client):
        with patch("backend.get_approval_history", side_effect=RuntimeError("fail")):
            resp = client.get("/api/rbac/approvals/history/MDL-001")
        assert resp.status_code == 500


class TestRbacPermissions:
    """GET /api/rbac/permissions/{user_id}"""

    def test_analyst_permissions(self, client):
        user = _user_dict(role="analyst")
        with patch("backend.get_user", return_value=user):
            resp = client.get("/api/rbac/permissions/usr-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "analyst"
        assert "approve_requests" not in data["permissions"]

    def test_approver_permissions(self, client):
        user = _user_dict(user_id="usr-003", role="approver")
        with patch("backend.get_user", return_value=user):
            resp = client.get("/api/rbac/permissions/usr-003")
        data = resp.json()
        assert "approve_requests" in data["permissions"]
        assert "sign_off_projects" in data["permissions"]

    def test_permissions_user_not_found(self, client):
        with patch("backend.get_user", return_value=None):
            resp = client.get("/api/rbac/permissions/MISSING")
        assert resp.status_code == 404

    def test_permissions_exception(self, client):
        with patch("backend.get_user", side_effect=RuntimeError("fail")):
            resp = client.get("/api/rbac/permissions/usr-001")
        assert resp.status_code == 500


# ===================================================================
# GL JOURNAL DOMAIN-LEVEL — Double-entry integrity
# ===================================================================

class TestGlDoubleEntryIntegrity:
    """Verify GL journal double-entry invariant with various amounts."""

    @pytest.mark.parametrize("amount", [0.01, 100.50, 999999.99, 1000000.00])
    def test_debits_equal_credits(self, client, amount):
        journal = _journal_dict(
            lines=[
                {"account_code": "4100", "debit": amount, "credit": 0},
                {"account_code": "2100", "debit": 0, "credit": amount},
            ],
            total_debits=amount,
            total_credits=amount,
        )
        with patch("backend.generate_ecl_journals", return_value=journal):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "x"})
        data = resp.json()
        dr = sum(float(l.get("debit", 0)) for l in data["lines"])
        cr = sum(float(l.get("credit", 0)) for l in data["lines"])
        assert abs(dr - cr) < 0.01

    def test_multi_line_balanced(self, client):
        journal = _journal_dict(
            lines=[
                {"account_code": "4100", "debit": 30000, "credit": 0},
                {"account_code": "4200", "debit": 20000, "credit": 0},
                {"account_code": "2100", "debit": 0, "credit": 30000},
                {"account_code": "2200", "debit": 0, "credit": 20000},
            ],
            total_debits=50000,
            total_credits=50000,
        )
        with patch("backend.generate_ecl_journals", return_value=journal):
            resp = client.post("/api/gl/generate/proj-001", json={"user": "x"})
        data = resp.json()
        dr = sum(float(l.get("debit", 0)) for l in data["lines"])
        cr = sum(float(l.get("credit", 0)) for l in data["lines"])
        assert abs(dr - cr) < 0.01


# ===================================================================
# RBAC — Maker-Checker segregation of duties
# ===================================================================

class TestRbacMakerCheckerSegregation:
    """Validate maker-checker separation through RBAC permissions."""

    def test_analyst_cannot_approve(self, client):
        """Analyst (maker) should not have approve_requests permission."""
        user = _user_dict(role="analyst")
        with patch("backend.get_user", return_value=user):
            resp = client.get("/api/rbac/permissions/usr-001")
        perms = resp.json()["permissions"]
        assert "approve_requests" not in perms
        assert "reject_requests" not in perms

    def test_approver_can_approve(self, client):
        """Approver (checker) should have approve + reject permissions."""
        user = _user_dict(user_id="usr-003", role="approver")
        with patch("backend.get_user", return_value=user):
            resp = client.get("/api/rbac/permissions/usr-003")
        perms = resp.json()["permissions"]
        assert "approve_requests" in perms
        assert "reject_requests" in perms

    def test_admin_has_all_permissions(self, client):
        user = _user_dict(user_id="usr-004", role="admin")
        with patch("backend.get_user", return_value=user):
            resp = client.get("/api/rbac/permissions/usr-004")
        perms = resp.json()["permissions"]
        assert "manage_users" in perms
        assert "manage_config" in perms
        assert "approve_requests" in perms
