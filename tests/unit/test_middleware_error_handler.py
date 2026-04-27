"""Dedicated tests for middleware/error_handler.py — global error response formatting."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from middleware.error_handler import ErrorHandlerMiddleware


class TestErrorHandlerMiddleware:
    @pytest.fixture
    def middleware(self):
        return ErrorHandlerMiddleware(app=MagicMock())

    def _mock_request(self, path="/api/test"):
        request = MagicMock()
        request.url.path = path
        request.state.request_id = "req-123"
        return request

    @pytest.mark.asyncio
    async def test_passes_through_successful_response(self, middleware):
        request = self._mock_request()
        expected = MagicMock(status_code=200)
        call_next = AsyncMock(return_value=expected)
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_catches_exception_returns_500(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=ValueError("test error"))
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_error_response_is_json(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=RuntimeError("boom"))
        response = await middleware.dispatch(request, call_next)
        body = json.loads(response.body.decode())
        assert "error" in body
        assert body["error"] == "internal_server_error"

    @pytest.mark.asyncio
    async def test_error_response_includes_message(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=ValueError("detailed error msg"))
        response = await middleware.dispatch(request, call_next)
        body = json.loads(response.body.decode())
        assert body["message"] == "detailed error msg"

    @pytest.mark.asyncio
    async def test_error_response_includes_request_id(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=Exception("err"))
        response = await middleware.dispatch(request, call_next)
        body = json.loads(response.body.decode())
        assert body["request_id"] == "req-123"

    @pytest.mark.asyncio
    async def test_error_response_includes_path(self, middleware):
        request = self._mock_request(path="/api/simulation")
        call_next = AsyncMock(side_effect=Exception("err"))
        response = await middleware.dispatch(request, call_next)
        body = json.loads(response.body.decode())
        assert body["path"] == "/api/simulation"

    @pytest.mark.asyncio
    async def test_handles_missing_request_id(self, middleware):
        request = MagicMock()
        request.url.path = "/api/test"
        request.state = MagicMock(spec=[])  # no request_id attribute
        call_next = AsyncMock(side_effect=Exception("err"))
        response = await middleware.dispatch(request, call_next)
        body = json.loads(response.body.decode())
        assert body["request_id"] == "unknown"

    @pytest.mark.asyncio
    async def test_does_not_expose_traceback(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=Exception("secret info"))
        response = await middleware.dispatch(request, call_next)
        body = json.loads(response.body.decode())
        assert "Traceback" not in body.get("message", "")
        assert "File" not in body.get("message", "")

    @pytest.mark.asyncio
    async def test_handles_type_error(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=TypeError("unsupported operand"))
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_handles_key_error(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=KeyError("missing_key"))
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_calls_next_exactly_once(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
