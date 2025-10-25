"""
MCP Tools for the MCP-Forge-Python application.

This module defines the MCP tools corresponding to the original Go application.
"""

from mcp.server.fastmcp import FastMCP

from mcp_app.mcp_components.tools.hello_world import hello_world
from mcp_app.mcp_components.tools.whoami import whoami

# List of tools to register
TOOLS = [
    {"func": hello_world, "stdio_only": False},
    {"func": whoami, "stdio_only": False},
]


def register_tools(mcp: FastMCP, mode: str = "http") -> None:
    """Register all MCP tools and resources."""
    # Register tools
    for tool in TOOLS:
        if not tool["stdio_only"] or mode == "stdio":
            mcp.tool()(tool["func"])
