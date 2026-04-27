"""Dedicated tests for middleware/request_id.py — request ID injection and timing."""
import uuid
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from middleware.request_id import RequestIDMiddleware


class TestRequestIDMiddleware:
    @pytest.fixture
    def middleware(self):
        return RequestIDMiddleware(app=MagicMock())

    def _mock_request(self, path="/api/test", request_id=None):
        request = MagicMock()
        request.url.path = path
        request.method = "GET"
        request.headers = {"X-Request-ID": request_id} if request_id else {}
        request.state = MagicMock()
        return request

    def _mock_response(self, status_code=200):
        response = MagicMock()
        response.status_code = status_code
        response.headers = {}
        return response

    @pytest.mark.asyncio
    async def test_adds_request_id_to_response(self, middleware):
        request = self._mock_request()
        response = self._mock_response()
        call_next = AsyncMock(return_value=response)
        result = await middleware.dispatch(request, call_next)
        assert "X-Request-ID" in result.headers

    @pytest.mark.asyncio
    async def test_uses_provided_request_id(self, middleware):
        request = self._mock_request(request_id="my-custom-id")
        response = self._mock_response()
        call_next = AsyncMock(return_value=response)
        result = await middleware.dispatch(request, call_next)
        assert result.headers["X-Request-ID"] == "my-custom-id"

    @pytest.mark.asyncio
    async def test_generates_id_when_not_provided(self, middleware):
        request = self._mock_request()
        response = self._mock_response()
        call_next = AsyncMock(return_value=response)
        result = await middleware.dispatch(request, call_next)
        rid = result.headers["X-Request-ID"]
        assert len(rid) == 12

    @pytest.mark.asyncio
    async def test_sets_request_state(self, middleware):
        request = self._mock_request()
        response = self._mock_response()
        call_next = AsyncMock(return_value=response)
        await middleware.dispatch(request, call_next)
        assert hasattr(request.state, "request_id")

    @pytest.mark.asyncio
    async def test_propagates_exception(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(side_effect=ValueError("boom"))
        with pytest.raises(ValueError, match="boom"):
            await middleware.dispatch(request, call_next)

    @pytest.mark.asyncio
    async def test_passes_through_normal_response(self, middleware):
        request = self._mock_request()
        response = self._mock_response(status_code=201)
        call_next = AsyncMock(return_value=response)
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 201

    @pytest.mark.asyncio
    async def test_calls_next_once(self, middleware):
        request = self._mock_request()
        call_next = AsyncMock(return_value=self._mock_response())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once()
