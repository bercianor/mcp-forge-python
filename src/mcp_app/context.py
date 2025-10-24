"""
Shared context for authentication data.

This module provides context variables to share JWT-related data between
middlewares and MCP tools in an async-safe way.
"""

from contextvars import ContextVar
from typing import Any

# Context variables for JWT data
jwt_token: ContextVar[str | None] = ContextVar("jwt_token", default=None)
jwt_payload: ContextVar[dict[str, Any] | None] = ContextVar("jwt_payload", default=None)


def set_jwt_context(token: str, payload: dict[str, Any]) -> None:
    """
    Set the JWT token and its decoded payload.

    Args:
        token: The validated JWT token string.
        payload: The decoded JWT payload.

    """
    jwt_token.set(token)
    jwt_payload.set(payload)


def get_jwt_payload() -> dict[str, Any] | None:
    """
    Get the decoded JWT payload.

    Returns:
        The JWT payload as a dictionary, or None if not set or decoding failed.

    """
    return jwt_payload.get()
