"""Tests for tools module."""

from unittest.mock import MagicMock

from mcp_app.context import jwt_payload, set_exposed_claims, set_jwt_context
from mcp_app.tools.hello_world import hello_world
from mcp_app.tools.router import register_tools
from mcp_app.tools.whoami import whoami

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
    jwt_payload.set(None)  # Simulate no JWT
    result = whoami()
    assert result == "JWT is empty or invalid. Information is not available"


def test_whoami_tool_with_jwt() -> None:
    """Test the whoami tool with JWT."""
    test_payload = {"sub": "user123", "roles": ["admin"]}
    jwt_payload.set(test_payload)  # Simulate decoded payload
    result = whoami()
    assert result == test_payload


def test_whoami_tool_with_filtered_claims() -> None:
    """Test whoami tool with filtered JWT claims."""
    set_exposed_claims(["sub", "roles"])
    test_payload = {"sub": "user123", "roles": ["admin"], "email": "user@example.com"}
    set_jwt_context("fake_token", test_payload)
    result = whoami()
    assert result == {"sub": "user123", "roles": ["admin"]}
    assert "email" not in result
