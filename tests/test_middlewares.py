"""Tests for middlewares."""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_app.middlewares.access_logs import AccessLogsMiddleware


@pytest.fixture
def caplog(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Fixture to capture log messages."""
    caplog.set_level(logging.INFO)
    return caplog


def test_access_logs_middleware_init() -> None:
    """Test AccessLogsMiddleware initialization."""
    app = MagicMock()
    middleware = AccessLogsMiddleware(app, excluded_headers=["auth"], redacted_headers=["pass"])
    assert middleware.excluded_headers == {"auth"}
    assert middleware.redacted_headers == {"pass"}


def test_access_logs_middleware_init_defaults() -> None:
    """Test AccessLogsMiddleware initialization with defaults."""
    app = MagicMock()
    middleware = AccessLogsMiddleware(app)
    assert middleware.excluded_headers == set()
    assert middleware.redacted_headers == set()


@pytest.mark.asyncio
async def test_dispatch_logs_request_and_response(caplog: pytest.LogCaptureFixture) -> None:
    """Test dispatch logs request and response."""
    app = MagicMock()
    middleware = AccessLogsMiddleware(
        app, excluded_headers=["exclude"], redacted_headers=["redact"]
    )

    request = MagicMock()
    request.method = "GET"
    request.url = "http://example.com"
    request.headers = {"exclude": "value", "redact": "secret", "keep": "value"}

    response = MagicMock()
    response.status_code = 200

    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert result == response
    call_next.assert_called_once_with(request)

    # Check logs
    log_messages = [record.message for record in caplog.records]
    assert any("Request: GET http://example.com" in msg for msg in log_messages)
    assert any("Headers: {'redact': '[REDACTED]', 'keep': 'value'}" in msg for msg in log_messages)
    assert any("Response: 200" in msg for msg in log_messages)
    assert any("Duration:" in msg for msg in log_messages)
