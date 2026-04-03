"""Tests for reporting/gl_journals.py — GL journal generation and posting."""
import json
import pytest
import pandas as pd
from unittest.mock import patch, call


@pytest.fixture
def _patch_db():
    with patch("reporting.gl_journals.query_df") as mock_q, \
         patch("reporting.gl_journals.execute") as mock_e, \
         patch("reporting.gl_journals.get_project") as mock_proj:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e, "get_project": mock_proj}


class TestGlConstants:
    def test_seed_accounts_count(self):
        from reporting.gl_journals import _GL_SEED_ACCOUNTS
        assert len(_GL_SEED_ACCOUNTS) == 9

    def test_stage_provision_accounts(self):
        from reporting.gl_journals import _STAGE_PROVISION_ACCOUNT
        assert _STAGE_PROVISION_ACCOUNT[1] == "1210"
        assert _STAGE_PROVISION_ACCOUNT[2] == "1220"
        assert _STAGE_PROVISION_ACCOUNT[3] == "1230"

    def test_seed_accounts_have_required_fields(self):
        from reporting.gl_journals import _GL_SEED_ACCOUNTS
        for code, name, atype, parent in _GL_SEED_ACCOUNTS:
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert atype in ("asset", "contra-asset", "expense", "income")


class TestGetGlChart:
    def test_returns_records(self, _patch_db):
        from reporting.gl_journals import get_gl_chart
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"account_code": "1200", "account_name": "Loans", "account_type": "asset"},
        ])
        result = get_gl_chart()
        assert len(result) == 1
        assert result[0]["account_code"] == "1200"

    def test_returns_empty_list(self, _patch_db):
        from reporting.gl_journals import get_gl_chart
        assert get_gl_chart() == []


class TestGenerateEclJournals:
    def test_raises_for_missing_project(self, _patch_db):
        from reporting.gl_journals import generate_ecl_journals
        _patch_db["get_project"].return_value = None
        with pytest.raises(ValueError, match="not found"):
            generate_ecl_journals("bad-project")

    def test_creates_journal_with_ecl_data(self, _patch_db):
        from reporting.gl_journals import generate_ecl_journals
        _patch_db["get_project"].return_value = {
            "project_id": "p1",
            "reporting_date": "2025-12-31",
            "overlays": [],
        }
        ecl_df = pd.DataFrame([
            {"product_type": "mortgage", "assessed_stage": 1, "total_ecl": 50000},
            {"product_type": "mortgage", "assessed_stage": 2, "total_ecl": 30000},
        ])
        journal_row = pd.DataFrame([{
            "journal_id": "JE-p1-test",
            "project_id": "p1",
            "journal_date": "2025-12-31",
            "journal_type": "ecl_provision",
            "status": "draft",
            "created_by": "system",
            "posted_by": None,
            "posted_at": None,
            "description": "test",
            "reference": "test",
            "created_at": "2025-12-31",
        }])
        lines_df = pd.DataFrame([
            {"line_id": "l1", "account_code": "4100", "debit": 50000, "credit": 0,
             "account_name": "ECL Charge", "account_type": "expense",
             "product_type": "mortgage", "stage": "1", "description": "test"},
            {"line_id": "l2", "account_code": "1210", "debit": 0, "credit": 50000,
             "account_name": "Stage 1 Provision", "account_type": "contra-asset",
             "product_type": "mortgage", "stage": "1", "description": "test"},
        ])
        wo_df = pd.DataFrame()
        _patch_db["query_df"].side_effect = [ecl_df, wo_df, journal_row, lines_df]
        result = generate_ecl_journals("p1")
        assert result is not None
        assert _patch_db["execute"].called


class TestListJournals:
    def test_returns_empty_for_unknown_project(self, _patch_db):
        from reporting.gl_journals import list_journals
        assert list_journals("unknown") == []

    def test_returns_journals_with_balance_flag(self, _patch_db):
        from reporting.gl_journals import list_journals
        _patch_db["query_df"].return_value = pd.DataFrame([{
            "journal_id": "j1", "project_id": "p1", "total_debit": 1000.0,
            "total_credit": 1000.0, "line_count": 2, "journal_date": "2025-12-31",
            "journal_type": "ecl_provision", "status": "draft",
            "created_by": "system", "posted_by": None, "posted_at": None,
            "description": "test", "reference": "ref", "created_at": "2025-12-31",
        }])
        result = list_journals("p1")
        assert len(result) == 1
        assert result[0]["balanced"] is True


class TestGetJournal:
    def test_returns_none_for_missing(self, _patch_db):
        from reporting.gl_journals import get_journal
        assert get_journal("nonexistent") is None

    def test_returns_journal_with_lines(self, _patch_db):
        from reporting.gl_journals import get_journal
        journal_df = pd.DataFrame([{
            "journal_id": "j1", "project_id": "p1", "status": "draft",
            "journal_date": "2025-12-31", "journal_type": "ecl_provision",
            "created_by": "system", "posted_by": None, "posted_at": None,
            "description": "test", "reference": "ref", "created_at": "2025-12-31",
        }])
        lines_df = pd.DataFrame([
            {"line_id": "l1", "account_code": "4100", "debit": 5000, "credit": 0,
             "account_name": "ECL Charge", "account_type": "expense",
             "product_type": "mortgage", "stage": "1", "description": "test"},
            {"line_id": "l2", "account_code": "1210", "debit": 0, "credit": 5000,
             "account_name": "Stage 1 Provision", "account_type": "contra-asset",
             "product_type": "mortgage", "stage": "1", "description": "test"},
        ])
        _patch_db["query_df"].side_effect = [journal_df, lines_df]
        result = get_journal("j1")
        assert result["journal_id"] == "j1"
        assert len(result["lines"]) == 2
        assert result["balanced"] is True
        assert result["total_debit"] == 5000
        assert result["total_credit"] == 5000


class TestPostJournal:
    def test_raises_for_missing_journal(self, _patch_db):
        from reporting.gl_journals import post_journal
        with pytest.raises(ValueError, match="not found"):
            post_journal("bad-id", "user1")

    def test_raises_for_non_draft(self, _patch_db):
        from reporting.gl_journals import post_journal
        journal_df = pd.DataFrame([{
            "journal_id": "j1", "project_id": "p1", "status": "posted",
            "journal_date": "2025-12-31", "journal_type": "ecl_provision",
            "created_by": "system", "posted_by": "user1", "posted_at": "2025-12-31",
            "description": "test", "reference": "ref", "created_at": "2025-12-31",
        }])
        lines_df = pd.DataFrame([
            {"line_id": "l1", "account_code": "4100", "debit": 1000, "credit": 0,
             "account_name": "ECL", "account_type": "expense",
             "product_type": "m", "stage": "1", "description": "t"},
            {"line_id": "l2", "account_code": "1210", "debit": 0, "credit": 1000,
             "account_name": "Prov", "account_type": "contra-asset",
             "product_type": "m", "stage": "1", "description": "t"},
        ])
        _patch_db["query_df"].side_effect = [journal_df, lines_df]
        with pytest.raises(ValueError, match="Only draft"):
            post_journal("j1", "user1")

    def test_raises_for_unbalanced(self, _patch_db):
        from reporting.gl_journals import post_journal
        journal_df = pd.DataFrame([{
            "journal_id": "j1", "project_id": "p1", "status": "draft",
            "journal_date": "2025-12-31", "journal_type": "ecl_provision",
            "created_by": "system", "posted_by": None, "posted_at": None,
            "description": "test", "reference": "ref", "created_at": "2025-12-31",
        }])
        lines_df = pd.DataFrame([
            {"line_id": "l1", "account_code": "4100", "debit": 1000, "credit": 0,
             "account_name": "ECL", "account_type": "expense",
             "product_type": "m", "stage": "1", "description": "t"},
        ])
        _patch_db["query_df"].side_effect = [journal_df, lines_df]
        with pytest.raises(ValueError, match="does not balance"):
            post_journal("j1", "user1")


class TestReverseJournal:
    def test_raises_for_non_posted(self, _patch_db):
        from reporting.gl_journals import reverse_journal
        journal_df = pd.DataFrame([{
            "journal_id": "j1", "project_id": "p1", "status": "draft",
            "journal_date": "2025-12-31", "journal_type": "ecl_provision",
            "created_by": "system", "posted_by": None, "posted_at": None,
            "description": "test", "reference": "ref", "created_at": "2025-12-31",
        }])
        lines_df = pd.DataFrame([
            {"line_id": "l1", "account_code": "4100", "debit": 1000, "credit": 0,
             "account_name": "ECL", "account_type": "expense",
             "product_type": "m", "stage": "1", "description": "t"},
            {"line_id": "l2", "account_code": "1210", "debit": 0, "credit": 1000,
             "account_name": "Prov", "account_type": "contra-asset",
             "product_type": "m", "stage": "1", "description": "t"},
        ])
        _patch_db["query_df"].side_effect = [journal_df, lines_df]
        with pytest.raises(ValueError, match="Only posted"):
            reverse_journal("j1", "user1")


class TestGetGlTrialBalance:
    def test_returns_empty_for_no_posted(self, _patch_db):
        from reporting.gl_journals import get_gl_trial_balance
        assert get_gl_trial_balance("p1") == []
