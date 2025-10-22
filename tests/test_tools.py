"""Tests for tools module."""

from unittest.mock import MagicMock

from mcp_app.tools.router import hello_world, register_tools, whoami

NUM_TOOLS = 2


def test_register_tools() -> None:
    """Test that register_tools registers the tools."""
    mcp = MagicMock()
    register_tools(mcp)
    # Check that tool decorator was called twice
    assert mcp.tool.call_count == NUM_TOOLS


def test_hello_world_tool() -> None:
    """Test the hello_world tool function."""
    result = hello_world("Test")
    assert result == "Hello, Test! 👋"


def test_whoami_tool_no_jwt() -> None:
    """Test the whoami tool with no JWT."""
    result = whoami(None)
    assert result == "JWT is empty. Information is not available"


def test_whoami_tool_with_jwt() -> None:
    """Test the whoami tool with JWT."""
    result = whoami("test.jwt.token")
    expected = (
        "Success! Data are in the following JWT. You have to decode it first. JWT: test.jwt.token"
    )
    assert result == expected
