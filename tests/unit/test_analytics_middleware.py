"""Tests for middleware/analytics.py — API request analytics tracking."""
import pytest
from unittest.mock import patch, MagicMock, ANY
import time


# ---------------------------------------------------------------------------
# Path exclusion
# ---------------------------------------------------------------------------

class TestShouldRecord:
    def test_excludes_assets_path(self):
        from middleware.analytics import _should_record
        assert _should_record("/assets/main.js") is False
        assert _should_record("/assets/style.css") is False

    def test_excludes_docs_path(self):
        from middleware.analytics import _should_record
        assert _should_record("/docs/overview") is False
        assert _should_record("/docs/") is False

    def test_excludes_health_exact(self):
        from middleware.analytics import _should_record
        assert _should_record("/api/health") is False

    def test_records_api_projects(self):
        from middleware.analytics import _should_record
        assert _should_record("/api/projects") is True

    def test_records_api_admin(self):
        from middleware.analytics import _should_record
        assert _should_record("/api/admin/users") is True

    def test_records_root(self):
        from middleware.analytics import _should_record
        assert _should_record("/") is True

    def test_records_api_health_detailed(self):
        from middleware.analytics import _should_record
        assert _should_record("/api/health/detailed") is True


# ---------------------------------------------------------------------------
# User ID extraction
# ---------------------------------------------------------------------------

class TestExtractUserId:
    def _make_request(self, headers=None):
        req = MagicMock()
        req.headers = headers or {}
        return req

    def test_extracts_x_forwarded_user(self):
        from middleware.analytics import _extract_user_id
        req = self._make_request({"X-Forwarded-User": "alice@corp.com"})
        assert _extract_user_id(req) == "alice@corp.com"

    def test_falls_back_to_x_user_id(self):
        from middleware.analytics import _extract_user_id
        req = self._make_request({"X-User-Id": "bob"})
        assert _extract_user_id(req) == "bob"

    def test_x_forwarded_user_takes_priority(self):
        from middleware.analytics import _extract_user_id
        req = self._make_request({
            "X-Forwarded-User": "alice",
            "X-User-Id": "bob",
        })
        assert _extract_user_id(req) == "alice"

    def test_defaults_to_anonymous(self):
        from middleware.analytics import _extract_user_id
        req = self._make_request({})
        assert _extract_user_id(req) == "anonymous"


# ---------------------------------------------------------------------------
# Fire-and-forget recording
# ---------------------------------------------------------------------------

class TestFireAndForgetRecord:
    def test_calls_record_request(self):
        """Inline import inside _fire_and_forget_record — patch at usage site."""
        with patch("domain.usage_analytics.record_request") as mock_domain:
            from middleware.analytics import _fire_and_forget_record
            _fire_and_forget_record(
                "user1", "GET", "/api/projects", 200, 45.2, "req-1", "Mozilla"
            )
            mock_domain.assert_called_once_with(
                user_id="user1",
                method="GET",
                endpoint="/api/projects",
                status_code=200,
                duration_ms=45.2,
                request_id="req-1",
                user_agent="Mozilla",
            )

    def test_swallows_exceptions(self):
        from middleware.analytics import _fire_and_forget_record
        with patch("domain.usage_analytics.record_request", side_effect=RuntimeError("db down")):
            # Should not raise
            _fire_and_forget_record("u", "GET", "/", 200, 1.0, None, None)


# ---------------------------------------------------------------------------
# Middleware dispatch (integration-style with mock)
# ---------------------------------------------------------------------------

class TestAnalyticsMiddlewareDispatch:
    @pytest.fixture
    def _mock_thread(self):
        with patch("middleware.analytics.threading.Thread") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            yield {"Thread": mock_cls, "instance": mock_instance}

    @pytest.mark.asyncio
    async def test_excluded_path_skips_recording(self, _mock_thread):
        from middleware.analytics import AnalyticsMiddleware
        mw = AnalyticsMiddleware(app=MagicMock())

        request = MagicMock()
        request.url.path = "/assets/main.js"
        response = MagicMock(status_code=200)

        async def call_next(req):
            return response

        result = await mw.dispatch(request, call_next)
        assert result is response
        _mock_thread["Thread"].assert_not_called()

    @pytest.mark.asyncio
    async def test_recorded_path_spawns_thread(self, _mock_thread):
        from middleware.analytics import AnalyticsMiddleware
        mw = AnalyticsMiddleware(app=MagicMock())

        request = MagicMock()
        request.url.path = "/api/projects"
        request.method = "GET"
        request.headers = {"User-Agent": "TestAgent"}
        request.state.request_id = "req-abc"
        response = MagicMock(status_code=200)

        async def call_next(req):
            return response

        result = await mw.dispatch(request, call_next)
        assert result is response
        _mock_thread["Thread"].assert_called_once()
        call_kwargs = _mock_thread["Thread"].call_args
        assert call_kwargs.kwargs["daemon"] is True
        _mock_thread["instance"].start.assert_called_once()

    @pytest.mark.asyncio
    async def test_captures_correct_args(self, _mock_thread):
        from middleware.analytics import AnalyticsMiddleware
        mw = AnalyticsMiddleware(app=MagicMock())

        request = MagicMock()
        request.url.path = "/api/data"
        request.method = "POST"
        request.headers = {
            "X-Forwarded-User": "alice@corp.com",
            "User-Agent": "TestBrowser",
        }
        request.state.request_id = "req-xyz"
        response = MagicMock(status_code=201)

        async def call_next(req):
            return response

        await mw.dispatch(request, call_next)
        args = _mock_thread["Thread"].call_args.kwargs["args"]
        assert args[0] == "alice@corp.com"  # user_id
        assert args[1] == "POST"            # method
        assert args[2] == "/api/data"       # endpoint
        assert args[3] == 201               # status_code
        assert isinstance(args[4], float)   # duration_ms
        assert args[4] >= 0                 # duration_ms non-negative
        assert args[5] == "req-xyz"         # request_id
        assert args[6] == "TestBrowser"     # user_agent

    @pytest.mark.asyncio
    async def test_duration_is_positive(self, _mock_thread):
        from middleware.analytics import AnalyticsMiddleware
        mw = AnalyticsMiddleware(app=MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {}
        request.state.request_id = None
        response = MagicMock(status_code=200)

        async def call_next(req):
            time.sleep(0.001)  # 1ms
            return response

        await mw.dispatch(request, call_next)
        args = _mock_thread["Thread"].call_args.kwargs["args"]
        assert args[4] > 0  # duration_ms

    @pytest.mark.asyncio
    async def test_missing_request_id_uses_none(self, _mock_thread):
        from middleware.analytics import AnalyticsMiddleware
        mw = AnalyticsMiddleware(app=MagicMock())

        request = MagicMock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {}
        # Simulate missing request_id attribute
        del request.state.request_id
        request.state = MagicMock(spec=[])
        response = MagicMock(status_code=200)

        async def call_next(req):
            return response

        await mw.dispatch(request, call_next)
        args = _mock_thread["Thread"].call_args.kwargs["args"]
        assert args[5] is None  # request_id


# ---------------------------------------------------------------------------
# Middleware ordering in app.py
# ---------------------------------------------------------------------------

class TestMiddlewareOrdering:
    @staticmethod
    def _find_app_py() -> "Path":
        from pathlib import Path
        for p in Path(__file__).absolute().parents:
            if (p / "app.py").is_file():
                return p / "app.py"
            if (p / "app" / "app.py").is_file():
                return p / "app" / "app.py"
        raise FileNotFoundError("Cannot locate app.py")

    def test_analytics_middleware_registered(self):
        """AnalyticsMiddleware is imported and used in app.py."""
        source = self._find_app_py().read_text()
        assert "AnalyticsMiddleware" in source
        assert "from middleware.analytics import AnalyticsMiddleware" in source

    def test_middleware_order(self):
        """AnalyticsMiddleware is added after ErrorHandler (outermost)
        and before RequestID (innermost) in add_middleware calls."""
        source = self._find_app_py().read_text()
        lines = source.split("\n")
        mw_lines = [
            (i, line.strip()) for i, line in enumerate(lines)
            if "app.add_middleware(" in line
        ]
        # Should have 3 middleware registrations
        assert len(mw_lines) >= 3
        names = [line for _, line in mw_lines]
        # ErrorHandler outermost (last add_middleware), RequestID innermost (first add_middleware)
        error_idx = next(i for i, (_, l) in enumerate(mw_lines) if "ErrorHandler" in l)
        analytics_idx = next(i for i, (_, l) in enumerate(mw_lines) if "Analytics" in l)
        request_idx = next(i for i, (_, l) in enumerate(mw_lines) if "RequestID" in l)
        # add_middleware order: ErrorHandler, Analytics, RequestID
        assert error_idx < analytics_idx < request_idx
