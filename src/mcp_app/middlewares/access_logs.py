"""
Access logs middleware.

Logs HTTP requests, excluding or redacting specified headers.
"""

import json
import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class AccessLogsMiddleware(BaseHTTPMiddleware):
    """Middleware for logging access logs."""

    def __init__(
        self,
        app: ASGIApp,
        excluded_headers: list[str] | None = None,
        redacted_headers: list[str] | None = None,
        max_body_size: int = 1024,  # Max body size to log in bytes
    ) -> None:
        """Initialize the access logs middleware."""
        super().__init__(app)
        self.excluded_headers = set(excluded_headers or [])
        # Default redacted headers for security
        default_redacted = {"authorization", "x-api-key", "x-auth-token", "cookie"}
        self.redacted_headers = set(redacted_headers or []) | default_redacted
        self.max_body_size = max_body_size

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and log access information."""
        start_time = time.time()

        # Read request body if small enough
        body = None
        if request.headers.get("content-length"):
            try:
                content_length = int(request.headers["content-length"])
                if content_length <= self.max_body_size:
                    body_bytes = await request.body()
                    body = body_bytes.decode("utf-8", errors="replace")
            except (ValueError, UnicodeDecodeError):
                body = "[BINARY OR INVALID BODY]"

        # Log request
        headers = {}
        for name, value in request.headers.items():
            if name.lower() in self.excluded_headers:
                continue
            if name.lower() in self.redacted_headers:
                headers[name] = "[REDACTED]"
            else:
                headers[name] = value

        # Structured logging for request
        request_log = {
            "event": "request",
            "method": request.method,
            "url": str(request.url),
            "headers": headers,
            "body": body,
            "timestamp": start_time,
        }
        logger.info(json.dumps(request_log))

        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        response_log = {
            "event": "response",
            "status_code": response.status_code,
            "duration": round(duration, 3),
            "timestamp": time.time(),
        }
        logger.info(json.dumps(response_log))

        return response
