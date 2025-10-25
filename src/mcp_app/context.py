"""
Shared context for authentication data.

This module provides context variables to share JWT-related data between
middlewares and MCP tools in an async-safe way.
"""

from contextvars import ContextVar
from typing import Any


class JWTContextConfig:
    """Configuration for JWT context exposure."""

    def __init__(self) -> None:
        """Initialize the JWT context configuration."""
        self.exposed_claims: str | list[str] = "all"


# Singleton instance
jwt_context_config = JWTContextConfig()

# Context variables for JWT data
jwt_token: ContextVar[str | None] = ContextVar("jwt_token", default=None)
jwt_payload: ContextVar[dict[str, Any] | None] = ContextVar("jwt_payload", default=None)


def set_exposed_claims(claims: str | list[str]) -> None:
    """
    Set the configuration for which JWT claims to expose.

    Args:
        claims: "all" to expose all claims, or a list of claim names to expose only those.

    """
    jwt_context_config.exposed_claims = claims


def filter_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Filter the JWT payload based on exposed_claims configuration.

    Always includes 'roles' and 'scope' claims for authorization.

    Args:
        payload: The full JWT payload.

    Returns:
        Filtered payload dictionary.

    """
    # Always include roles and scope for authorization
    always_include = {"roles", "scope"}
    if jwt_context_config.exposed_claims == "all":
        return payload
    if isinstance(jwt_context_config.exposed_claims, list):
        exposed = set(jwt_context_config.exposed_claims) | always_include
        return {k: v for k, v in payload.items() if k in exposed}
    # Fallback to all if misconfigured
    return payload


def set_jwt_context(token: str, payload: dict[str, Any]) -> None:
    """
    Set the JWT token and its decoded payload, filtering based on configuration.

    Args:
        token: The validated JWT token string.
        payload: The decoded JWT payload.

    """
    jwt_token.set(token)
    jwt_payload.set(filter_payload(payload))


def get_jwt_payload() -> dict[str, Any] | None:
    """
    Get the decoded JWT payload.

    Returns:
        The JWT payload as a dictionary, or None if not set or decoding failed.

    """
    return jwt_payload.get()
