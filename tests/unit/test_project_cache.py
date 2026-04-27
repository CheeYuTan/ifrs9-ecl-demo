"""Tests for workflow project caching."""
import time
import pandas as pd
from unittest.mock import patch

_M = "domain.workflow"


def _project_row(project_id="p1"):
    return pd.DataFrame([{
        "project_id": project_id, "project_name": "Test",
        "project_type": "standard", "current_step": 1,
        "step_status": '{"create_project": "completed"}',
        "overlays": "[]", "scenario_weights": "{}",
        "audit_log": "[]", "owner_id": "usr-001",
    }])


class TestProjectCache:
    def setup_method(self):
        from domain.workflow import invalidate_project_cache
        invalidate_project_cache()

    @patch(f"{_M}.query_df", return_value=_project_row())
    def test_cache_hit_avoids_db(self, mock_qdf):
        from domain.workflow import get_project
        r1 = get_project("p1")
        r2 = get_project("p1")
        assert r1 == r2
        assert mock_qdf.call_count == 1

    @patch(f"{_M}.query_df", return_value=_project_row())
    def test_invalidate_forces_reload(self, mock_qdf):
        from domain.workflow import get_project, invalidate_project_cache
        get_project("p1")
        invalidate_project_cache("p1")
        get_project("p1")
        assert mock_qdf.call_count == 2

    @patch(f"{_M}.query_df", return_value=pd.DataFrame())
    def test_not_found_cached(self, mock_qdf):
        from domain.workflow import get_project
        assert get_project("nope") is None
        assert get_project("nope") is None
        assert mock_qdf.call_count == 1

    @patch(f"{_M}.query_df", return_value=_project_row())
    def test_cache_invalidate_all(self, mock_qdf):
        from domain.workflow import get_project, invalidate_project_cache
        get_project("p1")
        invalidate_project_cache()
        get_project("p1")
        assert mock_qdf.call_count == 2
