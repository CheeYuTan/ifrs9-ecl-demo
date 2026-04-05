"""Tests for governance/project_members.py — CRUD operations for project membership."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_project(project_id="proj-1", owner_id="usr-owner"):
    return {
        "project_id": project_id,
        "project_name": "Test Project",
        "owner_id": owner_id,
        "current_step": 1,
        "step_status": {},
        "audit_log": [],
        "overlays": [],
        "scenario_weights": {},
    }


def _member_df(project_id, user_id, role):
    return pd.DataFrame([{
        "project_id": project_id,
        "user_id": user_id,
        "role": role,
        "granted_by": "admin",
        "granted_at": datetime.now(timezone.utc),
    }])


@pytest.fixture
def _patch_db():
    """Patch DB calls in the project_members module."""
    with patch("governance.project_members.query_df") as mock_q, \
         patch("governance.project_members.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


# ---------------------------------------------------------------------------
# CRUD: add / remove / list / get member
# ---------------------------------------------------------------------------

class TestAddMember:
    @patch("governance.project_members._audit_permission_change")
    @patch("governance.project_members.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.project_members.execute")
    @patch("governance.project_members.query_df")
    def test_add_member_success(self, mock_q, mock_e, mock_proj, mock_get, mock_audit):
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        mock_get.side_effect = [None, {"project_id": "proj-1", "user_id": "usr-1", "role": "editor"}]
        from governance.project_members import add_project_member
        result = add_project_member("proj-1", "usr-1", "editor", "admin")
        assert result["role"] == "editor"
        mock_audit.assert_called_once()

    @patch("domain.workflow.get_project")
    @patch("governance.project_members.get_project_member", return_value={"role": "viewer"})
    def test_duplicate_member_raises(self, mock_get, mock_proj):
        mock_proj.return_value = _make_project()
        from governance.project_members import add_project_member
        with pytest.raises(ValueError, match="already a member"):
            add_project_member("proj-1", "usr-1", "editor", "admin")

    def test_invalid_role_raises(self):
        from governance.project_members import add_project_member
        with pytest.raises(ValueError, match="Invalid role"):
            add_project_member("proj-1", "usr-1", "owner", "admin")

    def test_empty_project_id_raises(self):
        from governance.project_members import add_project_member
        with pytest.raises(ValueError, match="required"):
            add_project_member("", "usr-1", "editor", "admin")

    def test_empty_user_id_raises(self):
        from governance.project_members import add_project_member
        with pytest.raises(ValueError, match="required"):
            add_project_member("proj-1", "", "editor", "admin")

    @patch("governance.project_members.get_project_member", return_value=None)
    @patch("domain.workflow.get_project", return_value=None)
    def test_nonexistent_project_raises(self, mock_proj, mock_get):
        from governance.project_members import add_project_member
        with pytest.raises(ValueError, match="not found"):
            add_project_member("no-proj", "usr-1", "editor", "admin")

    @patch("governance.project_members.get_project_member", return_value=None)
    @patch("domain.workflow.get_project")
    def test_cannot_add_owner_as_member(self, mock_proj, mock_get):
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        from governance.project_members import add_project_member
        with pytest.raises(ValueError, match="owner"):
            add_project_member("proj-1", "usr-owner", "editor", "admin")


class TestRemoveMember:
    @patch("governance.project_members._audit_permission_change")
    @patch("governance.project_members.get_project_member")
    @patch("governance.project_members.execute")
    def test_remove_existing(self, mock_e, mock_get, mock_audit):
        mock_get.return_value = {"role": "editor"}
        from governance.project_members import remove_project_member
        assert remove_project_member("proj-1", "usr-1", "admin") is True
        mock_e.assert_called_once()
        mock_audit.assert_called_once()

    @patch("governance.project_members.get_project_member", return_value=None)
    def test_remove_nonexistent(self, mock_get):
        from governance.project_members import remove_project_member
        assert remove_project_member("proj-1", "usr-1", "admin") is False

    def test_empty_ids_raises(self):
        from governance.project_members import remove_project_member
        with pytest.raises(ValueError, match="required"):
            remove_project_member("", "usr-1", "admin")


class TestListMembers:
    def test_list_empty(self, _patch_db):
        from governance.project_members import list_project_members
        result = list_project_members("proj-1")
        assert result == []

    def test_list_with_members(self, _patch_db):
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"project_id": "proj-1", "user_id": "usr-1", "role": "viewer",
             "granted_by": "admin", "granted_at": "2024-01-01"},
            {"project_id": "proj-1", "user_id": "usr-2", "role": "editor",
             "granted_by": "admin", "granted_at": "2024-01-02"},
        ])
        from governance.project_members import list_project_members
        result = list_project_members("proj-1")
        assert len(result) == 2


class TestGetMember:
    def test_get_existing(self, _patch_db):
        _patch_db["query_df"].return_value = _member_df("proj-1", "usr-1", "editor")
        from governance.project_members import get_project_member
        result = get_project_member("proj-1", "usr-1")
        assert result["role"] == "editor"

    def test_get_nonexistent(self, _patch_db):
        from governance.project_members import get_project_member
        result = get_project_member("proj-1", "usr-1")
        assert result is None


# ---------------------------------------------------------------------------
# Transfer ownership
# ---------------------------------------------------------------------------

class TestTransferOwnership:
    @patch("governance.project_members._audit_permission_change")
    @patch("governance.project_members.execute")
    @patch("domain.workflow.get_project")
    def test_transfer_success(self, mock_proj, mock_e, mock_audit):
        mock_proj.side_effect = [
            _make_project(owner_id="usr-old"),
            _make_project(owner_id="usr-new"),
        ]
        from governance.project_members import transfer_ownership
        result = transfer_ownership("proj-1", "usr-new", "usr-old")
        assert result["owner_id"] == "usr-new"
        mock_audit.assert_called_once()
        detail = mock_audit.call_args[0][3]
        assert detail["old_owner_id"] == "usr-old"
        assert detail["new_owner_id"] == "usr-new"

    @patch("domain.workflow.get_project", return_value=None)
    def test_nonexistent_project_raises(self, mock_proj):
        from governance.project_members import transfer_ownership
        with pytest.raises(ValueError, match="not found"):
            transfer_ownership("no-proj", "usr-new", "usr-old")

    def test_empty_ids_raises(self):
        from governance.project_members import transfer_ownership
        with pytest.raises(ValueError, match="required"):
            transfer_ownership("", "usr-new", "performed-by")
        with pytest.raises(ValueError, match="required"):
            transfer_ownership("proj-1", "", "performed-by")


# ---------------------------------------------------------------------------
# Audit trail integration
# ---------------------------------------------------------------------------

class TestAuditIntegration:
    @patch("domain.audit_trail.append_audit_entry")
    @patch("governance.project_members.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.project_members.execute")
    @patch("governance.project_members.query_df")
    def test_add_member_audits(self, mock_q, mock_e, mock_proj, mock_get, mock_audit):
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        mock_get.side_effect = [None, {"project_id": "proj-1", "user_id": "usr-1", "role": "editor"}]
        from governance.project_members import add_project_member
        add_project_member("proj-1", "usr-1", "editor", "admin-user")
        mock_audit.assert_called_once()
        args = mock_audit.call_args
        assert args[0][0] == "proj-1"  # project_id
        assert args[0][4] == "member_added"  # action
        assert args[0][5] == "admin-user"  # performed_by

    @patch("domain.audit_trail.append_audit_entry")
    @patch("governance.project_members.get_project_member")
    @patch("governance.project_members.execute")
    def test_remove_member_audits(self, mock_e, mock_get, mock_audit):
        mock_get.return_value = {"role": "viewer"}
        from governance.project_members import remove_project_member
        remove_project_member("proj-1", "usr-1", "admin-user")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[0][4] == "member_removed"

    @patch("domain.audit_trail.append_audit_entry")
    @patch("governance.project_members.execute")
    @patch("domain.workflow.get_project")
    def test_transfer_ownership_audits(self, mock_proj, mock_e, mock_audit):
        mock_proj.side_effect = [
            _make_project(owner_id="usr-old"),
            _make_project(owner_id="usr-new"),
        ]
        from governance.project_members import transfer_ownership
        transfer_ownership("proj-1", "usr-new", "usr-old")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[0][4] == "ownership_transferred"

    @patch("domain.audit_trail.append_audit_entry", side_effect=Exception("DB down"))
    @patch("governance.project_members.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.project_members.execute")
    @patch("governance.project_members.query_df")
    def test_audit_failure_does_not_break_add(self, mock_q, mock_e, mock_proj,
                                               mock_get, mock_audit):
        """Audit trail failure is best-effort — should not break the operation."""
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        mock_get.side_effect = [None, {"project_id": "proj-1", "user_id": "usr-1", "role": "editor"}]
        from governance.project_members import add_project_member
        result = add_project_member("proj-1", "usr-1", "editor", "admin")
        assert result is not None  # Operation succeeded despite audit failure
