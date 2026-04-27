"""Dedicated tests for dashboards/provision_dashboard.py — dashboard spec building."""
import pytest

from dashboards.provision_dashboard import (
    DASHBOARD_NAME,
    PAGE_TITLES,
    _build_dashboard_spec,
)
from dashboards import QUERY_FILES


class TestPageTitles:
    def test_all_query_files_have_titles(self):
        for f in QUERY_FILES:
            assert f in PAGE_TITLES, f"{f} missing from PAGE_TITLES"

    def test_no_extra_titles(self):
        for f in PAGE_TITLES:
            assert f in QUERY_FILES, f"{f} in PAGE_TITLES but not QUERY_FILES"

    def test_all_titles_nonempty(self):
        for f, title in PAGE_TITLES.items():
            assert len(title) > 0, f"{f} has empty title"

    def test_first_page_is_user_activity(self):
        assert PAGE_TITLES["01_user_activity.sql"] == "User Activity"

    def test_last_page_is_system_health(self):
        assert PAGE_TITLES["07_system_health.sql"] == "System Health"


class TestDashboardName:
    def test_contains_ifrs9(self):
        assert "IFRS 9" in DASHBOARD_NAME

    def test_contains_ecl(self):
        assert "ECL" in DASHBOARD_NAME


class TestBuildDashboardSpec:
    def test_returns_dict(self):
        spec = _build_dashboard_spec()
        assert isinstance(spec, dict)

    def test_has_display_name(self):
        spec = _build_dashboard_spec()
        assert spec["displayName"] == DASHBOARD_NAME

    def test_has_datasets(self):
        spec = _build_dashboard_spec()
        assert "datasets" in spec
        assert len(spec["datasets"]) == 7

    def test_has_pages(self):
        spec = _build_dashboard_spec()
        assert "pages" in spec
        assert len(spec["pages"]) == 7

    def test_dataset_names_match_files(self):
        spec = _build_dashboard_spec()
        expected_names = [f.replace(".sql", "") for f in QUERY_FILES]
        actual_names = [d["name"] for d in spec["datasets"]]
        assert actual_names == expected_names

    def test_datasets_have_queries(self):
        spec = _build_dashboard_spec()
        for ds in spec["datasets"]:
            assert "query" in ds
            assert len(ds["query"]) > 10

    def test_custom_schema_in_queries(self):
        spec = _build_dashboard_spec(schema="test_schema")
        for ds in spec["datasets"]:
            assert "test_schema" in ds["query"]

    def test_page_names_match_titles(self):
        spec = _build_dashboard_spec()
        for page, filename in zip(spec["pages"], QUERY_FILES):
            assert page["name"] == PAGE_TITLES[filename]

    def test_page_display_names(self):
        spec = _build_dashboard_spec()
        for page in spec["pages"]:
            assert "displayName" in page
            assert page["displayName"] == page["name"]

    def test_datasets_ordered_correctly(self):
        spec = _build_dashboard_spec()
        for i, ds in enumerate(spec["datasets"]):
            assert ds["name"].startswith(f"{i+1:02d}_")
