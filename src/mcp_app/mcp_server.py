"""
MCP server management for the MCP-Forge-Python service.

This module handles MCP server initialization and tool registration.
"""

from mcp.server import FastMCP

from mcp_app.mcp_components.router import register_tools


class MCPServer:
    """Handles MCP server initialization and tool registration."""

    def __init__(self, mode: str = "http") -> None:
        """Initialize the MCP server."""
        self.mcp = FastMCP("MCP-Forge-Python")
        register_tools(self.mcp, mode)
