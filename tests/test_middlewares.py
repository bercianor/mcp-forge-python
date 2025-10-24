"""Tests for middlewares."""

import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_app.middlewares.access_logs import AccessLogsMiddleware

# Constants for tests
DEFAULT_MAX_BODY_SIZE = 1024
HTTP_OK_STATUS = 200


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
    # Should include custom + defaults
    expected_redacted = {"pass", "authorization", "x-api-key", "x-auth-token", "cookie"}
    assert middleware.redacted_headers == expected_redacted


def test_access_logs_middleware_init_defaults() -> None:
    """Test AccessLogsMiddleware initialization with defaults."""
    app = MagicMock()
    middleware = AccessLogsMiddleware(app)
    assert middleware.excluded_headers == set()
    # Should include default redacted headers
    expected_redacted = {"authorization", "x-api-key", "x-auth-token", "cookie"}
    assert middleware.redacted_headers == expected_redacted
    assert middleware.max_body_size == DEFAULT_MAX_BODY_SIZE


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
    request.headers = {
        "exclude": "value",
        "redact": "secret",
        "keep": "value",
        "content-length": "9",
    }
    request.body = AsyncMock(return_value=b"test body")

    response = MagicMock()
    response.status_code = 200

    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert result == response
    call_next.assert_called_once_with(request)

    # Check JSON logs
    log_messages = [record.message for record in caplog.records]
    request_log = None
    response_log = None
    for msg in log_messages:
        data = json.loads(msg)
        if data.get("event") == "request":
            request_log = data
        elif data.get("event") == "response":
            response_log = data

    assert request_log is not None
    assert request_log["method"] == "GET"
    assert request_log["url"] == "http://example.com"
    assert request_log["headers"] == {
        "redact": "[REDACTED]",
        "keep": "value",
        "content-length": "9",
    }
    assert request_log["body"] == "test body"

    assert response_log is not None
    assert response_log["status_code"] == HTTP_OK_STATUS
    assert "duration" in response_log


@pytest.mark.asyncio
async def test_access_logs_middleware_invalid_body(caplog: pytest.LogCaptureFixture) -> None:
    """Test AccessLogsMiddleware with invalid body content."""
    app = MagicMock()
    middleware = AccessLogsMiddleware(app)

    request = MagicMock()
    request.method = "POST"
    request.url = "http://example.com"
    request.headers = {"content-length": "invalid"}  # Invalid content-length
    request.body = AsyncMock(return_value=b"test body")

    response = MagicMock()
    response.status_code = 200

    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert result == response
    call_next.assert_called_once_with(request)

    # Check JSON logs
    log_messages = [record.message for record in caplog.records]
    request_log = None
    for msg in log_messages:
        data = json.loads(msg)
        if data.get("event") == "request":
            request_log = data
            break

    assert request_log is not None
    assert request_log["body"] == "[BINARY OR INVALID BODY]"
