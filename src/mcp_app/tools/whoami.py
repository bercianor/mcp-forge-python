"""Tool to expose user information."""

from typing import Any

from mcp_app.context import get_jwt_payload


def whoami() -> dict[str, Any] | str:
    """
    Expose information about the user from the JWT payload.

    Returns:
        The JWT payload as a dictionary, or an error message if not available.

    """
    payload = get_jwt_payload()
    if not payload:
        return "JWT is empty or invalid. Information is not available"

    return payload
