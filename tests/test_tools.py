"""Tests for tools module."""

from unittest.mock import MagicMock

import pytest

from mcp_app.context import jwt_context_config, jwt_payload, set_exposed_claims, set_jwt_context
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
    set_jwt_context("fake_token", {"scope": "tool:user"})
    result = hello_world("Test")
    assert result == "Hello, Test! 👋"


def test_hello_world_tool_no_jwt() -> None:
    """Test the hello_world tool function without JWT."""
    jwt_payload.set(None)  # Simulate no JWT
    result = hello_world("Test")
    assert result == "Hello, Test! 👋"


def test_hello_world_tool_insufficient_permissions() -> None:
    """Test hello_world tool with JWT but insufficient permissions."""
    set_jwt_context("fake_token", {"scope": "tool:admin"})  # No tool:user scope
    with pytest.raises(PermissionError, match="Insufficient permissions: tool:user scope required"):
        hello_world("Test")


def test_whoami_tool_no_jwt() -> None:
    """Test the whoami tool with no JWT."""
    jwt_payload.set(None)  # Simulate no JWT
    result = whoami()
    assert result == "No JWT available (running in stdio mode or invalid token)"


def test_whoami_tool_with_jwt() -> None:
    """Test the whoami tool with JWT."""
    test_payload = {"sub": "user123", "roles": ["admin"], "scope": "tool:admin"}
    jwt_payload.set(test_payload)  # Simulate decoded payload
    result = whoami()
    assert result == test_payload


def test_whoami_tool_insufficient_permissions() -> None:
    """Test whoami tool with JWT but insufficient permissions."""
    test_payload = {"sub": "user123", "roles": ["admin"], "scope": "tool:user"}
    jwt_payload.set(test_payload)  # No tool:admin scope
    with pytest.raises(
        PermissionError, match="Insufficient permissions: tool:admin scope required"
    ):
        whoami()


def test_whoami_tool_with_filtered_claims() -> None:
    """Test whoami tool with filtered JWT claims."""
    set_exposed_claims(["sub", "roles"])
    test_payload = {
        "sub": "user123",
        "roles": ["admin"],
        "email": "user@example.com",
        "scope": "tool:admin",
    }
    set_jwt_context("fake_token", test_payload)
    result = whoami()
    assert result == {"sub": "user123", "roles": ["admin"], "scope": "tool:admin"}
    assert "email" not in result


def test_whoami_tool_with_all_claims() -> None:
    """Test whoami tool with all JWT claims exposed."""
    set_exposed_claims("all")
    test_payload = {
        "sub": "user123",
        "roles": ["admin"],
        "email": "user@example.com",
        "scope": "tool:admin",
    }
    set_jwt_context("fake_token", test_payload)
    result = whoami()
    assert result == test_payload


def test_whoami_tool_with_invalid_claims_config() -> None:
    """Test whoami tool with invalid exposed claims configuration (fallback)."""
    # Directly modify config to test fallback
    jwt_context_config.exposed_claims = None  # type: ignore[assignment]
    test_payload = {
        "sub": "user123",
        "roles": ["admin"],
        "email": "user@example.com",
        "scope": "tool:admin",
    }
    set_jwt_context("fake_token", test_payload)
    result = whoami()
    assert result == test_payload
