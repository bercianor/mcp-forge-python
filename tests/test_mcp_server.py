"""Tests for the MCPServer class."""

from mcp.server import FastMCP

from mcp_app.mcp_server import MCPServer


def test_mcp_server_init() -> None:
    """Test MCPServer initialization."""
    server = MCPServer()
    assert isinstance(server.mcp, FastMCP)
    assert server.mcp.name == "MCP-Forge-Python"
