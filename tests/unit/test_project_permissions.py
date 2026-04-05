"""Tests for governance/project_permissions.py — per-project permission layer."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def _patch_db():
    """Patch DB calls in the project_permissions module."""
    with patch("governance.project_permissions.query_df") as mock_q, \
         patch("governance.project_permissions.execute") as mock_e:
        mock_q.return_value = pd.DataFrame()
        yield {"query_df": mock_q, "execute": mock_e}


def _make_user(user_id, role="analyst"):
    return {
        "user_id": user_id,
        "email": f"{user_id}@bank.com",
        "display_name": user_id.title(),
        "role": role,
        "permissions": [],
    }


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


# ---------------------------------------------------------------------------
# Role hierarchy
# ---------------------------------------------------------------------------

class TestRoleHierarchy:
    def test_viewer_lowest(self):
        from governance.project_permissions import role_level
        assert role_level("viewer") == 0

    def test_editor_above_viewer(self):
        from governance.project_permissions import role_level
        assert role_level("editor") > role_level("viewer")

    def test_manager_above_editor(self):
        from governance.project_permissions import role_level
        assert role_level("manager") > role_level("editor")

    def test_owner_highest(self):
        from governance.project_permissions import role_level
        assert role_level("owner") > role_level("manager")

    def test_unknown_role_returns_negative(self):
        from governance.project_permissions import role_level
        assert role_level("nonexistent") == -1

    def test_hierarchy_ordering(self):
        from governance.project_permissions import role_level
        assert role_level("viewer") < role_level("editor") < role_level("manager") < role_level("owner")


# ---------------------------------------------------------------------------
# ensure_project_members_table
# ---------------------------------------------------------------------------

class TestEnsureTable:
    def test_creates_table(self, _patch_db):
        with patch("governance.project_permissions.execute") as mock_e:
            from governance.project_permissions import ensure_project_members_table
            ensure_project_members_table()
            calls = mock_e.call_args_list
            assert len(calls) == 2  # CREATE TABLE + COMMENT
            ddl = calls[0].args[0]
            assert "CREATE TABLE IF NOT EXISTS" in ddl
            assert "project_members" in ddl

    def test_table_comment(self, _patch_db):
        with patch("governance.project_permissions.execute") as mock_e:
            from governance.project_permissions import ensure_project_members_table
            ensure_project_members_table()
            comment = mock_e.call_args_list[1].args[0]
            assert "COMMENT ON TABLE" in comment
            assert "ifrs9ecl:" in comment

    def test_schema_columns(self, _patch_db):
        with patch("governance.project_permissions.execute") as mock_e:
            from governance.project_permissions import ensure_project_members_table
            ensure_project_members_table()
            ddl = mock_e.call_args_list[0].args[0]
            for col in ("project_id", "user_id", "role", "granted_by", "granted_at"):
                assert col in ddl, f"Column {col} missing from DDL"

    def test_role_check_constraint(self, _patch_db):
        with patch("governance.project_permissions.execute") as mock_e:
            from governance.project_permissions import ensure_project_members_table
            ensure_project_members_table()
            ddl = mock_e.call_args_list[0].args[0]
            assert "viewer" in ddl
            assert "editor" in ddl
            assert "manager" in ddl

    def test_unique_constraint(self, _patch_db):
        with patch("governance.project_permissions.execute") as mock_e:
            from governance.project_permissions import ensure_project_members_table
            ensure_project_members_table()
            ddl = mock_e.call_args_list[0].args[0]
            assert "UNIQUE" in ddl


# ---------------------------------------------------------------------------
# get_effective_role
# ---------------------------------------------------------------------------

class TestGetEffectiveRole:
    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project")
    @patch("governance.rbac.get_user")
    def test_admin_override(self, mock_user, mock_proj, mock_member):
        mock_user.return_value = _make_user("usr-004", "admin")
        from governance.project_permissions import get_effective_role
        result = get_effective_role("usr-004", "proj-1")
        assert result == "owner"

    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project")
    @patch("governance.rbac.get_user")
    def test_owner_by_project_field(self, mock_user, mock_proj, mock_member):
        mock_user.return_value = _make_user("usr-owner", "analyst")
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        from governance.project_permissions import get_effective_role
        result = get_effective_role("usr-owner", "proj-1")
        assert result == "owner"

    @patch("governance.project_permissions.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.rbac.get_user")
    def test_member_role(self, mock_user, mock_proj, mock_member):
        mock_user.return_value = _make_user("usr-001", "analyst")
        mock_proj.return_value = _make_project(owner_id="usr-other")
        mock_member.return_value = {"role": "editor"}
        from governance.project_permissions import get_effective_role
        result = get_effective_role("usr-001", "proj-1")
        assert result == "editor"

    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project")
    @patch("governance.rbac.get_user")
    def test_no_access(self, mock_user, mock_proj, mock_member):
        mock_user.return_value = _make_user("usr-001", "analyst")
        mock_proj.return_value = _make_project(owner_id="usr-other")
        from governance.project_permissions import get_effective_role
        result = get_effective_role("usr-001", "proj-1")
        assert result is None

    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project", return_value=None)
    @patch("governance.rbac.get_user")
    def test_nonexistent_project(self, mock_user, mock_proj, mock_member):
        mock_user.return_value = _make_user("usr-001", "analyst")
        from governance.project_permissions import get_effective_role
        result = get_effective_role("usr-001", "no-such-proj")
        assert result is None

    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project")
    @patch("governance.rbac.get_user", return_value=None)
    def test_nonexistent_user(self, mock_user, mock_proj, mock_member):
        mock_proj.return_value = _make_project(owner_id="usr-other")
        from governance.project_permissions import get_effective_role
        result = get_effective_role("no-such-user", "proj-1")
        assert result is None

    @patch("governance.project_permissions.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.rbac.get_user")
    def test_admin_beats_member_role(self, mock_user, mock_proj, mock_member):
        """Admin gets owner even if they have a lower member role."""
        mock_user.return_value = _make_user("usr-004", "admin")
        mock_member.return_value = {"role": "viewer"}  # Should be ignored
        from governance.project_permissions import get_effective_role
        result = get_effective_role("usr-004", "proj-1")
        assert result == "owner"


# ---------------------------------------------------------------------------
# check_project_access
# ---------------------------------------------------------------------------

class TestCheckProjectAccess:
    @patch("governance.project_permissions.get_effective_role", return_value="owner")
    def test_owner_can_do_anything(self, mock_role):
        from governance.project_permissions import check_project_access
        result = check_project_access("usr-1", "proj-1", "owner")
        assert result["allowed"] is True
        assert result["effective_role"] == "owner"

    @patch("governance.project_permissions.get_effective_role", return_value="viewer")
    def test_viewer_cannot_edit(self, mock_role):
        from governance.project_permissions import check_project_access
        result = check_project_access("usr-1", "proj-1", "editor")
        assert result["allowed"] is False
        assert "insufficient" in result["reason"].lower()

    @patch("governance.project_permissions.get_effective_role", return_value="editor")
    def test_editor_can_view(self, mock_role):
        from governance.project_permissions import check_project_access
        result = check_project_access("usr-1", "proj-1", "viewer")
        assert result["allowed"] is True

    @patch("governance.project_permissions.get_effective_role", return_value="manager")
    def test_manager_can_edit(self, mock_role):
        from governance.project_permissions import check_project_access
        result = check_project_access("usr-1", "proj-1", "editor")
        assert result["allowed"] is True

    @patch("governance.project_permissions.get_effective_role", return_value=None)
    def test_no_access_denied(self, mock_role):
        from governance.project_permissions import check_project_access
        result = check_project_access("usr-1", "proj-1", "viewer")
        assert result["allowed"] is False
        assert result["effective_role"] is None

    def test_invalid_required_role(self):
        from governance.project_permissions import check_project_access
        result = check_project_access("usr-1", "proj-1", "superadmin")
        assert result["allowed"] is False
        assert "invalid" in result["reason"].lower()


# ---------------------------------------------------------------------------
# Permission matrix: RBAC role x project role x access check
# ---------------------------------------------------------------------------

class TestPermissionMatrix:
    """Comprehensive permission matrix: RBAC roles x project membership x access."""

    @pytest.mark.parametrize("rbac_role,expected", [
        ("analyst", "owner"),
        ("reviewer", "owner"),
        ("approver", "owner"),
        ("admin", "owner"),
    ])
    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project")
    @patch("governance.rbac.get_user")
    def test_all_rbac_roles_as_owner(self, mock_user, mock_proj, mock_member,
                                      rbac_role, expected):
        """Project owner gets 'owner' effective role regardless of RBAC role."""
        mock_user.return_value = _make_user("usr-1", rbac_role)
        mock_proj.return_value = _make_project(owner_id="usr-1")
        from governance.project_permissions import get_effective_role
        assert get_effective_role("usr-1", "proj-1") == expected

    @pytest.mark.parametrize("member_role,required,allowed", [
        ("viewer", "viewer", True),
        ("viewer", "editor", False),
        ("viewer", "manager", False),
        ("viewer", "owner", False),
        ("editor", "viewer", True),
        ("editor", "editor", True),
        ("editor", "manager", False),
        ("editor", "owner", False),
        ("manager", "viewer", True),
        ("manager", "editor", True),
        ("manager", "manager", True),
        ("manager", "owner", False),
    ])
    @patch("governance.project_permissions.get_effective_role")
    def test_member_role_access(self, mock_eff, member_role, required, allowed):
        mock_eff.return_value = member_role
        from governance.project_permissions import check_project_access
        result = check_project_access("usr-1", "proj-1", required)
        assert result["allowed"] is allowed


# ---------------------------------------------------------------------------
# CRUD: add / remove / list / get member
# ---------------------------------------------------------------------------

class TestAddMember:
    @patch("governance.project_permissions._audit_permission_change")
    @patch("governance.project_permissions.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.project_permissions.execute")
    @patch("governance.project_permissions.query_df")
    def test_add_member_success(self, mock_q, mock_e, mock_proj, mock_get, mock_audit):
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        mock_get.side_effect = [None, {"project_id": "proj-1", "user_id": "usr-1", "role": "editor"}]
        from governance.project_permissions import add_project_member
        result = add_project_member("proj-1", "usr-1", "editor", "admin")
        assert result["role"] == "editor"
        mock_audit.assert_called_once()

    @patch("domain.workflow.get_project")
    @patch("governance.project_permissions.get_project_member", return_value={"role": "viewer"})
    def test_duplicate_member_raises(self, mock_get, mock_proj):
        mock_proj.return_value = _make_project()
        from governance.project_permissions import add_project_member
        with pytest.raises(ValueError, match="already a member"):
            add_project_member("proj-1", "usr-1", "editor", "admin")

    def test_invalid_role_raises(self):
        from governance.project_permissions import add_project_member
        with pytest.raises(ValueError, match="Invalid role"):
            add_project_member("proj-1", "usr-1", "owner", "admin")

    def test_empty_project_id_raises(self):
        from governance.project_permissions import add_project_member
        with pytest.raises(ValueError, match="required"):
            add_project_member("", "usr-1", "editor", "admin")

    def test_empty_user_id_raises(self):
        from governance.project_permissions import add_project_member
        with pytest.raises(ValueError, match="required"):
            add_project_member("proj-1", "", "editor", "admin")

    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project", return_value=None)
    def test_nonexistent_project_raises(self, mock_proj, mock_get):
        from governance.project_permissions import add_project_member
        with pytest.raises(ValueError, match="not found"):
            add_project_member("no-proj", "usr-1", "editor", "admin")

    @patch("governance.project_permissions.get_project_member", return_value=None)
    @patch("domain.workflow.get_project")
    def test_cannot_add_owner_as_member(self, mock_proj, mock_get):
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        from governance.project_permissions import add_project_member
        with pytest.raises(ValueError, match="owner"):
            add_project_member("proj-1", "usr-owner", "editor", "admin")


class TestRemoveMember:
    @patch("governance.project_permissions._audit_permission_change")
    @patch("governance.project_permissions.get_project_member")
    @patch("governance.project_permissions.execute")
    def test_remove_existing(self, mock_e, mock_get, mock_audit):
        mock_get.return_value = {"role": "editor"}
        from governance.project_permissions import remove_project_member
        assert remove_project_member("proj-1", "usr-1", "admin") is True
        mock_e.assert_called_once()
        mock_audit.assert_called_once()

    @patch("governance.project_permissions.get_project_member", return_value=None)
    def test_remove_nonexistent(self, mock_get):
        from governance.project_permissions import remove_project_member
        assert remove_project_member("proj-1", "usr-1", "admin") is False

    def test_empty_ids_raises(self):
        from governance.project_permissions import remove_project_member
        with pytest.raises(ValueError, match="required"):
            remove_project_member("", "usr-1", "admin")


class TestListMembers:
    def test_list_empty(self, _patch_db):
        from governance.project_permissions import list_project_members
        result = list_project_members("proj-1")
        assert result == []

    def test_list_with_members(self, _patch_db):
        _patch_db["query_df"].return_value = pd.DataFrame([
            {"project_id": "proj-1", "user_id": "usr-1", "role": "viewer",
             "granted_by": "admin", "granted_at": "2024-01-01"},
            {"project_id": "proj-1", "user_id": "usr-2", "role": "editor",
             "granted_by": "admin", "granted_at": "2024-01-02"},
        ])
        from governance.project_permissions import list_project_members
        result = list_project_members("proj-1")
        assert len(result) == 2


class TestGetMember:
    def test_get_existing(self, _patch_db):
        _patch_db["query_df"].return_value = _member_df("proj-1", "usr-1", "editor")
        from governance.project_permissions import get_project_member
        result = get_project_member("proj-1", "usr-1")
        assert result["role"] == "editor"

    def test_get_nonexistent(self, _patch_db):
        from governance.project_permissions import get_project_member
        result = get_project_member("proj-1", "usr-1")
        assert result is None


# ---------------------------------------------------------------------------
# Transfer ownership
# ---------------------------------------------------------------------------

class TestTransferOwnership:
    @patch("governance.project_permissions._audit_permission_change")
    @patch("governance.project_permissions.execute")
    @patch("domain.workflow.get_project")
    def test_transfer_success(self, mock_proj, mock_e, mock_audit):
        mock_proj.side_effect = [
            _make_project(owner_id="usr-old"),
            _make_project(owner_id="usr-new"),
        ]
        from governance.project_permissions import transfer_ownership
        result = transfer_ownership("proj-1", "usr-new", "usr-old")
        assert result["owner_id"] == "usr-new"
        mock_audit.assert_called_once()
        detail = mock_audit.call_args[0][3]
        assert detail["old_owner_id"] == "usr-old"
        assert detail["new_owner_id"] == "usr-new"

    @patch("domain.workflow.get_project", return_value=None)
    def test_nonexistent_project_raises(self, mock_proj):
        from governance.project_permissions import transfer_ownership
        with pytest.raises(ValueError, match="not found"):
            transfer_ownership("no-proj", "usr-new", "usr-old")

    def test_empty_ids_raises(self):
        from governance.project_permissions import transfer_ownership
        with pytest.raises(ValueError, match="required"):
            transfer_ownership("", "usr-new", "performed-by")
        with pytest.raises(ValueError, match="required"):
            transfer_ownership("proj-1", "", "performed-by")


# ---------------------------------------------------------------------------
# Audit trail integration
# ---------------------------------------------------------------------------

class TestAuditIntegration:
    @patch("domain.audit_trail.append_audit_entry")
    @patch("governance.project_permissions.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.project_permissions.execute")
    @patch("governance.project_permissions.query_df")
    def test_add_member_audits(self, mock_q, mock_e, mock_proj, mock_get, mock_audit):
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        mock_get.side_effect = [None, {"project_id": "proj-1", "user_id": "usr-1", "role": "editor"}]
        from governance.project_permissions import add_project_member
        add_project_member("proj-1", "usr-1", "editor", "admin-user")
        mock_audit.assert_called_once()
        args = mock_audit.call_args
        assert args[0][0] == "proj-1"  # project_id
        assert args[0][4] == "member_added"  # action
        assert args[0][5] == "admin-user"  # performed_by

    @patch("domain.audit_trail.append_audit_entry")
    @patch("governance.project_permissions.get_project_member")
    @patch("governance.project_permissions.execute")
    def test_remove_member_audits(self, mock_e, mock_get, mock_audit):
        mock_get.return_value = {"role": "viewer"}
        from governance.project_permissions import remove_project_member
        remove_project_member("proj-1", "usr-1", "admin-user")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[0][4] == "member_removed"

    @patch("domain.audit_trail.append_audit_entry")
    @patch("governance.project_permissions.execute")
    @patch("domain.workflow.get_project")
    def test_transfer_ownership_audits(self, mock_proj, mock_e, mock_audit):
        mock_proj.side_effect = [
            _make_project(owner_id="usr-old"),
            _make_project(owner_id="usr-new"),
        ]
        from governance.project_permissions import transfer_ownership
        transfer_ownership("proj-1", "usr-new", "usr-old")
        mock_audit.assert_called_once()
        assert mock_audit.call_args[0][4] == "ownership_transferred"

    @patch("domain.audit_trail.append_audit_entry", side_effect=Exception("DB down"))
    @patch("governance.project_permissions.get_project_member")
    @patch("domain.workflow.get_project")
    @patch("governance.project_permissions.execute")
    @patch("governance.project_permissions.query_df")
    def test_audit_failure_does_not_break_add(self, mock_q, mock_e, mock_proj,
                                               mock_get, mock_audit):
        """Audit trail failure is best-effort — should not break the operation."""
        mock_proj.return_value = _make_project(owner_id="usr-owner")
        mock_get.side_effect = [None, {"project_id": "proj-1", "user_id": "usr-1", "role": "editor"}]
        from governance.project_permissions import add_project_member
        result = add_project_member("proj-1", "usr-1", "editor", "admin")
        assert result is not None  # Operation succeeded despite audit failure


# ---------------------------------------------------------------------------
# Backend re-exports
# ---------------------------------------------------------------------------

class TestBackendReExports:
    def test_module_accessible(self):
        import backend
        assert hasattr(backend, "check_project_access")
        assert hasattr(backend, "get_effective_role")
        assert hasattr(backend, "add_project_member")
        assert hasattr(backend, "remove_project_member")
        assert hasattr(backend, "transfer_ownership")
        assert hasattr(backend, "list_project_members")
        assert hasattr(backend, "get_project_member")
        assert hasattr(backend, "ensure_project_members_table")
        assert hasattr(backend, "ROLE_HIERARCHY")
        assert hasattr(backend, "role_level")
        assert hasattr(backend, "PROJECT_MEMBERS_TABLE")
        assert hasattr(backend, "VALID_PROJECT_ROLES")


# ---------------------------------------------------------------------------
# Workflow owner_id integration
# ---------------------------------------------------------------------------

class TestWorkflowOwnerId:
    def test_create_project_signature_has_owner_id(self):
        """create_project() accepts owner_id parameter."""
        import inspect
        from domain.workflow import create_project
        sig = inspect.signature(create_project)
        assert "owner_id" in sig.parameters

    def test_create_project_owner_default(self):
        """Default owner_id is 'usr-004' (admin)."""
        import inspect
        from domain.workflow import create_project
        param = inspect.signature(create_project).parameters["owner_id"]
        assert param.default == "usr-004"

    def test_workflow_table_has_owner_id(self):
        """ensure_workflow_table DDL includes owner_id column."""
        import inspect
        from domain.workflow import ensure_workflow_table
        source = inspect.getsource(ensure_workflow_table)
        assert "owner_id" in source
