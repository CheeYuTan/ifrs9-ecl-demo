"""
Sprint 7 Iteration 4: Regression tests for BUG-S7-1 and BUG-S7-2.

BUG-S7-1: ensure_workflow_table() called ensure_backtesting_table() via
  globals().get("ensure_backtesting_table") but the function was NOT imported
  in workflow.py, so globals().get() returned None and the migration was silently
  skipped. Fix: replaced globals().get() with explicit lazy imports inside
  ensure_workflow_table().

BUG-S7-2: The globals().get() pattern was fragile. Now replaced with explicit
  lazy imports that will raise ImportError (caught) rather than silently
  returning None.
"""
import pytest
from unittest.mock import patch, MagicMock


ENSURE_FUNCTION_NAMES = [
    "ensure_attribution_table",
    "ensure_model_registry_table",
    "ensure_backtesting_table",
    "ensure_gl_tables",
    "ensure_markov_tables",
    "ensure_hazard_tables",
    "ensure_rbac_tables",
]

ENSURE_IMPORT_PATHS = {
    "ensure_attribution_table": "domain.attribution.ensure_attribution_table",
    "ensure_model_registry_table": "domain.model_registry.ensure_model_registry_table",
    "ensure_backtesting_table": "domain.backtesting.ensure_backtesting_table",
    "ensure_gl_tables": "reporting.gl_journals.ensure_gl_tables",
    "ensure_markov_tables": "domain.markov.ensure_markov_tables",
    "ensure_hazard_tables": "domain.hazard_tables.ensure_hazard_tables",
    "ensure_rbac_tables": "governance.rbac.ensure_rbac_tables",
}


class TestWorkflowEnsureInvocation:
    """Verify ensure_workflow_table() actually CALLS each ensure function via lazy imports."""

    @patch("domain.workflow.execute")
    def test_ensure_workflow_table_calls_ensure_backtesting_table(self, mock_exec):
        """BUG-S7-1: The full invocation path must work — backtesting migration runs."""
        mock_fn = MagicMock(return_value=None)
        with patch("domain.backtesting.ensure_backtesting_table", mock_fn):
            with patch("domain.audit_trail.ensure_audit_tables", return_value=None):
                from domain.workflow import ensure_workflow_table
                ensure_workflow_table()
        assert mock_fn.call_count >= 1, (
            "ensure_workflow_table() did not call ensure_backtesting_table()"
        )

    @patch("domain.workflow.execute")
    @pytest.mark.parametrize("fn_name", ENSURE_FUNCTION_NAMES)
    def test_ensure_workflow_table_calls_each_ensure_fn(self, mock_exec, fn_name):
        """BUG-S7-2: Every ensure function in the lazy-import block must be invoked."""
        import_path = ENSURE_IMPORT_PATHS[fn_name]
        mock_fn = MagicMock(return_value=None)
        with patch(import_path, mock_fn):
            with patch("domain.audit_trail.ensure_audit_tables", return_value=None):
                from domain.workflow import ensure_workflow_table
                ensure_workflow_table()
        mock_fn.assert_called_once(), (
            f"ensure_workflow_table() did not call {fn_name}"
        )

    @patch("domain.workflow.execute")
    def test_ensure_workflow_table_continues_on_single_failure(self, mock_exec):
        """If one ensure function fails, the rest should still be called."""
        mock_bt = MagicMock(return_value=None)
        with patch(
            "domain.attribution.ensure_attribution_table",
            side_effect=RuntimeError("test"),
        ):
            with patch("domain.backtesting.ensure_backtesting_table", mock_bt):
                with patch("domain.audit_trail.ensure_audit_tables",
                           return_value=None):
                    from domain.workflow import ensure_workflow_table
                    ensure_workflow_table()
        mock_bt.assert_called_once(), (
            "ensure_backtesting_table not called after ensure_attribution_table failed"
        )

    @patch("domain.workflow.execute")
    def test_ensure_workflow_table_calls_all_seven(self, mock_exec):
        """All 7 ensure functions must be called in a single invocation."""
        mocks = {}
        patchers = []
        for fn_name in ENSURE_FUNCTION_NAMES:
            mocks[fn_name] = MagicMock(return_value=None)
            patchers.append(
                patch(ENSURE_IMPORT_PATHS[fn_name], mocks[fn_name])
            )
        patchers.append(
            patch("domain.audit_trail.ensure_audit_tables", return_value=None)
        )
        for p in patchers:
            p.start()
        try:
            from domain.workflow import ensure_workflow_table
            ensure_workflow_table()
        finally:
            for p in patchers:
                p.stop()

        for fn_name in ENSURE_FUNCTION_NAMES:
            mocks[fn_name].assert_called_once(), (
                f"{fn_name} was not called by ensure_workflow_table()"
            )
