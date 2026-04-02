"""
Sprint 9 QA — db/pool.py tests: _is_auth_error, _t(), load_schema_from_config,
query_df retry logic, execute retry logic.

All DB interactions are mocked — no real database connections.
"""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import psycopg2


# ---------------------------------------------------------------------------
# _is_auth_error
# ---------------------------------------------------------------------------

class TestIsAuthError:
    """Test _is_auth_error detects all known authentication error patterns."""

    @pytest.mark.parametrize("msg", [
        "invalid authorization specification",
        "FATAL: password authentication failed for user 'test'",
        "authentication failed for user postgres",
        "token expired",
        "token is expired or has been revoked",
        "ssl connection has been closed unexpectedly",
        "connection reset by peer",
        "server closed the connection unexpectedly",
        "FATAL: login attempt failed",
    ])
    def test_detects_auth_errors(self, msg):
        from db.pool import _is_auth_error
        assert _is_auth_error(Exception(msg)) is True

    @pytest.mark.parametrize("msg", [
        "relation 'my_table' does not exist",
        "syntax error at or near 'SELECT'",
        "division by zero",
        "column 'foo' does not exist",
        "deadlock detected",
        "unique constraint violation",
        "null value in column 'id'",
        "",
    ])
    def test_rejects_non_auth_errors(self, msg):
        from db.pool import _is_auth_error
        assert _is_auth_error(Exception(msg)) is False

    def test_case_insensitive(self):
        from db.pool import _is_auth_error
        assert _is_auth_error(Exception("TOKEN EXPIRED")) is True
        assert _is_auth_error(Exception("Password Authentication Failed")) is True

    def test_fatal_login_combo(self):
        """The function checks for 'fatal' AND 'login' together."""
        from db.pool import _is_auth_error
        assert _is_auth_error(Exception("FATAL: login role does not exist")) is True
        # Only 'fatal' without 'login' should not match (unless another pattern hits)
        assert _is_auth_error(Exception("FATAL: something else entirely")) is False
        # Only 'login' without 'fatal' should not match (unless another pattern hits)
        assert _is_auth_error(Exception("login prompt displayed")) is False


# ---------------------------------------------------------------------------
# _t() — table name builder
# ---------------------------------------------------------------------------

class TestTableNameBuilder:
    """Test _t() builds correct qualified table names."""

    def test_default_schema_and_prefix(self):
        from db.pool import _t, SCHEMA, PREFIX
        result = _t("loans")
        assert result == f"{SCHEMA}.{PREFIX}loans"

    def test_returns_string(self):
        from db.pool import _t
        assert isinstance(_t("test"), str)

    def test_with_various_table_names(self):
        from db.pool import _t, SCHEMA, PREFIX
        for name in ["model_ready_loans", "ecl_results", "audit_log", "x"]:
            assert _t(name) == f"{SCHEMA}.{PREFIX}{name}"


# ---------------------------------------------------------------------------
# load_schema_from_config
# ---------------------------------------------------------------------------

class TestLoadSchemaFromConfig:
    """Test load_schema_from_config loads and caches schema settings."""

    def test_loads_schema_from_admin_config(self):
        import db.pool as pool_mod
        original_schema = pool_mod.SCHEMA
        original_prefix = pool_mod.PREFIX
        original_loaded = pool_mod._config_loaded

        try:
            pool_mod._config_loaded = False
            mock_cfg = {
                "data_sources": {
                    "lakebase_schema": "test_schema",
                    "lakebase_prefix": "test_",
                }
            }
            mock_admin = MagicMock()
            mock_admin.get_config.return_value = mock_cfg
            with patch.dict("sys.modules", {"admin_config": mock_admin}):
                pool_mod.load_schema_from_config()
                assert pool_mod.SCHEMA == "test_schema"
                assert pool_mod.PREFIX == "test_"
                assert pool_mod._config_loaded is True
        finally:
            pool_mod.SCHEMA = original_schema
            pool_mod.PREFIX = original_prefix
            pool_mod._config_loaded = original_loaded

    def test_caches_after_first_load(self):
        import db.pool as pool_mod
        original_loaded = pool_mod._config_loaded
        original_schema = pool_mod.SCHEMA
        try:
            pool_mod._config_loaded = True
            # Should return early without importing admin_config
            pool_mod.load_schema_from_config()
            assert pool_mod._config_loaded is True
        finally:
            pool_mod._config_loaded = original_loaded
            pool_mod.SCHEMA = original_schema

    def test_fallback_on_import_error(self):
        import db.pool as pool_mod
        original_schema = pool_mod.SCHEMA
        original_prefix = pool_mod.PREFIX
        original_loaded = pool_mod._config_loaded

        try:
            pool_mod._config_loaded = False
            # Simulate admin_config import failure
            with patch.dict("sys.modules", {"admin_config": None}):
                pool_mod.load_schema_from_config()
                # Should not crash, keeps defaults
                assert pool_mod._config_loaded is False
        finally:
            pool_mod.SCHEMA = original_schema
            pool_mod.PREFIX = original_prefix
            pool_mod._config_loaded = original_loaded


# ---------------------------------------------------------------------------
# query_df retry logic
# ---------------------------------------------------------------------------

class TestQueryDfRetry:
    """Test query_df retries on OperationalError and returns DataFrame."""

    def _make_pool_mock(self, cursor_data=None, cols=None):
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        if cols:
            mock_cursor.description = [MagicMock(name=c) for c in cols]
        else:
            mock_cursor.description = [MagicMock(name="col1")]
        mock_cursor.fetchall.return_value = cursor_data or [(1,)]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.getconn.return_value = mock_conn
        return mock_pool, mock_conn, mock_cursor

    def test_returns_dataframe_on_success(self):
        import db.pool as pool_mod
        mock_pool, mock_conn, mock_cursor = self._make_pool_mock(
            cursor_data=[(1, "a"), (2, "b")],
            cols=["id", "name"],
        )
        orig_pool = pool_mod._pool
        try:
            pool_mod._pool = mock_pool
            df = pool_mod.query_df("SELECT id, name FROM test")
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
        finally:
            pool_mod._pool = orig_pool

    def test_retries_on_getconn_operational_error(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_pool.getconn.side_effect = psycopg2.OperationalError("connection reset")

        call_count = 0
        orig_pool = pool_mod._pool

        def mock_reinit():
            nonlocal call_count
            call_count += 1
            new_pool, _, _ = self._make_pool_mock()
            pool_mod._pool = new_pool

        try:
            pool_mod._pool = mock_pool
            with patch.object(pool_mod, "_reinit_pool", side_effect=mock_reinit):
                df = pool_mod.query_df("SELECT 1", _retry=True)
                assert call_count == 1
                assert isinstance(df, pd.DataFrame)
        finally:
            pool_mod._pool = orig_pool

    def test_raises_on_second_operational_error(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_pool.getconn.side_effect = psycopg2.OperationalError("dead")
        orig_pool = pool_mod._pool

        try:
            pool_mod._pool = mock_pool
            with pytest.raises(psycopg2.OperationalError):
                pool_mod.query_df("SELECT 1", _retry=False)
        finally:
            pool_mod._pool = orig_pool

    def test_retries_on_execute_operational_error(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.OperationalError("token expired")
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.getconn.return_value = mock_conn

        call_count = 0
        orig_pool = pool_mod._pool

        def mock_reinit():
            nonlocal call_count
            call_count += 1
            new_pool, _, _ = self._make_pool_mock()
            pool_mod._pool = new_pool

        try:
            pool_mod._pool = mock_pool
            with patch.object(pool_mod, "_reinit_pool", side_effect=mock_reinit):
                df = pool_mod.query_df("SELECT 1", _retry=True)
                assert call_count == 1
        finally:
            pool_mod._pool = orig_pool

    def test_non_operational_error_not_retried(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = ValueError("bad query")
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.getconn.return_value = mock_conn

        orig_pool = pool_mod._pool
        try:
            pool_mod._pool = mock_pool
            with patch.object(pool_mod, "_reinit_pool") as mock_reinit:
                with pytest.raises(ValueError, match="bad query"):
                    pool_mod.query_df("SELECT bad")
                mock_reinit.assert_not_called()
        finally:
            pool_mod._pool = orig_pool

    def test_init_pool_called_when_pool_is_none(self):
        import db.pool as pool_mod
        mock_pool, _, _ = self._make_pool_mock()
        orig_pool = pool_mod._pool

        try:
            pool_mod._pool = None
            with patch.object(pool_mod, "init_pool") as mock_init:
                def set_pool():
                    pool_mod._pool = mock_pool
                mock_init.side_effect = set_pool
                df = pool_mod.query_df("SELECT 1")
                mock_init.assert_called_once()
        finally:
            pool_mod._pool = orig_pool


# ---------------------------------------------------------------------------
# execute retry logic
# ---------------------------------------------------------------------------

class TestExecuteRetry:
    """Test execute retries on OperationalError."""

    def _make_pool_mock(self):
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.getconn.return_value = mock_conn
        return mock_pool, mock_conn, mock_cursor

    def test_execute_success(self):
        import db.pool as pool_mod
        mock_pool, mock_conn, mock_cursor = self._make_pool_mock()
        orig_pool = pool_mod._pool
        try:
            pool_mod._pool = mock_pool
            pool_mod.execute("INSERT INTO test VALUES (%s)", (1,))
            mock_conn.commit.assert_called_once()
        finally:
            pool_mod._pool = orig_pool

    def test_execute_retries_on_getconn_operational_error(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_pool.getconn.side_effect = psycopg2.OperationalError("dead")

        call_count = 0
        orig_pool = pool_mod._pool

        def mock_reinit():
            nonlocal call_count
            call_count += 1
            new_pool, _, _ = self._make_pool_mock()
            pool_mod._pool = new_pool

        try:
            pool_mod._pool = mock_pool
            with patch.object(pool_mod, "_reinit_pool", side_effect=mock_reinit):
                pool_mod.execute("INSERT INTO test VALUES (1)", _retry=True)
                assert call_count == 1
        finally:
            pool_mod._pool = orig_pool

    def test_execute_raises_on_retry_false(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_pool.getconn.side_effect = psycopg2.OperationalError("dead")
        orig_pool = pool_mod._pool

        try:
            pool_mod._pool = mock_pool
            with pytest.raises(psycopg2.OperationalError):
                pool_mod.execute("INSERT INTO test VALUES (1)", _retry=False)
        finally:
            pool_mod._pool = orig_pool

    def test_execute_retries_on_cursor_operational_error(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.OperationalError("connection reset")
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.getconn.return_value = mock_conn

        call_count = 0
        orig_pool = pool_mod._pool

        def mock_reinit():
            nonlocal call_count
            call_count += 1
            new_pool, _, _ = self._make_pool_mock()
            pool_mod._pool = new_pool

        try:
            pool_mod._pool = mock_pool
            with patch.object(pool_mod, "_reinit_pool", side_effect=mock_reinit):
                pool_mod.execute("UPDATE test SET x=1", _retry=True)
                assert call_count == 1
        finally:
            pool_mod._pool = orig_pool

    def test_execute_non_operational_error_not_retried(self):
        import db.pool as pool_mod
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = ValueError("bad")
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.getconn.return_value = mock_conn

        orig_pool = pool_mod._pool
        try:
            pool_mod._pool = mock_pool
            with patch.object(pool_mod, "_reinit_pool") as mock_reinit:
                with pytest.raises(ValueError, match="bad"):
                    pool_mod.execute("DELETE FROM test")
                mock_reinit.assert_not_called()
        finally:
            pool_mod._pool = orig_pool

    def test_execute_init_pool_when_none(self):
        import db.pool as pool_mod
        mock_pool, _, _ = self._make_pool_mock()
        orig_pool = pool_mod._pool

        try:
            pool_mod._pool = None
            with patch.object(pool_mod, "init_pool") as mock_init:
                def set_pool():
                    pool_mod._pool = mock_pool
                mock_init.side_effect = set_pool
                pool_mod.execute("INSERT INTO test VALUES (1)")
                mock_init.assert_called_once()
        finally:
            pool_mod._pool = orig_pool
