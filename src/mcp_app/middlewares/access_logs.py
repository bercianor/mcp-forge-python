"""
Access logs middleware.

Logs HTTP requests, excluding or redacting specified headers.
"""

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
    ) -> None:
        """Initialize the access logs middleware."""
        super().__init__(app)
        self.excluded_headers = set(excluded_headers or [])
        self.redacted_headers = set(redacted_headers or [])

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and log access information."""
        start_time = time.time()

        # Log request
        headers = {}
        for name, value in request.headers.items():
            if name.lower() in self.excluded_headers:
                continue
            if name.lower() in self.redacted_headers:
                headers[name] = "[REDACTED]"
            else:
                headers[name] = value

        logger.info("Request: %s %s - Headers: %s", request.method, request.url, headers)

        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info("Response: %s - Duration: %.3fs", response.status_code, duration)

        return response
