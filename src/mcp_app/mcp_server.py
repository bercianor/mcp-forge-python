"""
MCP server management for the MCP-Forge-Python service.

This module handles MCP server initialization and tool registration.
"""

from mcp.server import FastMCP

from mcp_app.tools.router import register_tools


class MCPServer:
    """Handles MCP server initialization and tool registration."""

    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.mcp = FastMCP("MCP-Forge-Python")
        register_tools(self.mcp)
