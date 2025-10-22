"""
MCP Tools for the MCP-Forge-Python application.

This module defines the MCP tools corresponding to the original Go application.
"""

from mcp.server import FastMCP


def hello_world(name: str) -> str:
    """
    Say hello to someone.

    Args:
        name: Name of the person to greet.

    Returns:
        Greeting message.

    """
    return f"Hello, {name}! 👋"


def whoami(jwt: str | None = None) -> str:
    """
    Expose information about the user.

    Args:
        jwt: Validated JWT from middleware.

    Returns:
        User information message.

    """
    if not jwt:
        return "JWT is empty. Information is not available"

    return f"Success! Data are in the following JWT. You have to decode it first. JWT: {jwt}"


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools."""
    mcp.tool()(hello_world)
    mcp.tool()(whoami)
