"""Tool to expose user information."""

from typing import Any

from mcp_app.context import get_jwt_payload


def whoami() -> dict[str, Any] | str:
    """
    Expose information about the user from the JWT payload.

    Requires tool:admin scope (or no JWT in stdio mode).

    Returns:
        The JWT payload as a dictionary, or an error message if not available.

    Raises:
        PermissionError: If user lacks required scope.

    """
    payload = get_jwt_payload()
    if not payload:
        return "No JWT available (running in stdio mode or invalid token)"

    scope = payload.get("scope", "")
    scopes = scope.split() if isinstance(scope, str) else scope or []
    if "tool:admin" not in scopes:
        msg = "Insufficient permissions: tool:admin scope required"
        raise PermissionError(msg)

    return payload
