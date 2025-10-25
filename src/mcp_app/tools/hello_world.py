"""Tool to say hello."""

from mcp_app.context import get_jwt_payload


def hello_world(name: str) -> str:
    """
    Say hello to someone. Requires tool:user scope (or no JWT in stdio mode).

    Args:
        name: Name of the person to greet.

    Returns:
        Greeting message.

    Raises:
        PermissionError: If user lacks required scope.

    """
    payload = get_jwt_payload()
    if payload:  # Only check scopes if JWT is present (HTTP mode)
        scope = payload.get("scope", "")
        scopes = scope.split() if isinstance(scope, str) else scope or []
        if "tool:user" not in scopes:
            msg = "Insufficient permissions: tool:user scope required"
            raise PermissionError(msg)
    # In stdio mode (no JWT), allow execution
    return f"Hello, {name}! 👋"
