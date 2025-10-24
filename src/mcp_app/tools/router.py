"""
MCP Tools for the MCP-Forge-Python application.

This module defines the MCP tools corresponding to the original Go application.
"""

from mcp.server import FastMCP

from mcp_app.tools.hello_world import hello_world
from mcp_app.tools.whoami import whoami


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools."""
    mcp.tool()(hello_world)
    mcp.tool()(whoami)
