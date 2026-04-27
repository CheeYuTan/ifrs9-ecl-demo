"""Dedicated tests for dashboards/__init__.py — query listing and loading."""
import pytest

from dashboards import QUERY_FILES, list_queries, load_query, load_all_queries


class TestQueryFiles:
    def test_has_seven_files(self):
        assert len(QUERY_FILES) == 7

    def test_all_end_with_sql(self):
        for f in QUERY_FILES:
            assert f.endswith(".sql"), f"{f} doesn't end with .sql"

    def test_numbered_sequentially(self):
        for i, f in enumerate(QUERY_FILES, start=1):
            assert f.startswith(f"{i:02d}_"), f"{f} doesn't start with {i:02d}_"

    def test_first_is_user_activity(self):
        assert "user_activity" in QUERY_FILES[0]

    def test_last_is_system_health(self):
        assert "system_health" in QUERY_FILES[-1]


class TestListQueries:
    def test_returns_list(self):
        result = list_queries()
        assert isinstance(result, list)

    def test_matches_query_files(self):
        assert list_queries() == list(QUERY_FILES)

    def test_returns_copy(self):
        result = list_queries()
        result.append("extra.sql")
        assert len(list_queries()) == 7


class TestLoadQuery:
    def test_loads_existing_file(self):
        sql = load_query(QUERY_FILES[0])
        assert isinstance(sql, str)
        assert len(sql) > 0

    def test_substitutes_schema(self):
        sql = load_query(QUERY_FILES[0], schema="my_schema")
        assert "my_schema" in sql
        assert "{schema}" not in sql

    def test_default_schema(self):
        sql = load_query(QUERY_FILES[0])
        assert "expected_credit_loss" in sql

    def test_invalid_schema_raises(self):
        with pytest.raises(ValueError, match="Invalid schema"):
            load_query(QUERY_FILES[0], schema="DROP TABLE;--")

    def test_invalid_schema_with_space(self):
        with pytest.raises(ValueError, match="Invalid schema"):
            load_query(QUERY_FILES[0], schema="bad schema")

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_query("nonexistent.sql")

    def test_all_files_loadable(self):
        for f in QUERY_FILES:
            sql = load_query(f)
            assert len(sql) > 10, f"{f} appears empty"

    def test_schema_with_dots(self):
        sql = load_query(QUERY_FILES[0], schema="catalog.schema_name")
        assert "catalog.schema_name" in sql

    def test_schema_with_underscore(self):
        sql = load_query(QUERY_FILES[0], schema="my_ecl_schema")
        assert "my_ecl_schema" in sql


class TestLoadAllQueries:
    def test_returns_dict(self):
        result = load_all_queries()
        assert isinstance(result, dict)

    def test_has_all_seven_queries(self):
        result = load_all_queries()
        assert len(result) == 7

    def test_keys_match_query_files(self):
        result = load_all_queries()
        assert set(result.keys()) == set(QUERY_FILES)

    def test_all_values_are_strings(self):
        result = load_all_queries()
        for k, v in result.items():
            assert isinstance(v, str), f"{k} is not a string"

    def test_custom_schema(self):
        result = load_all_queries(schema="custom_schema")
        for k, sql in result.items():
            assert "custom_schema" in sql, f"{k} doesn't contain custom_schema"

    def test_no_empty_queries(self):
        result = load_all_queries()
        for k, sql in result.items():
            assert len(sql) > 10, f"{k} appears empty"
