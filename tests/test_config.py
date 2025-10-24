"""Tests for the configuration module."""

import os
import tempfile
from datetime import timedelta
from pathlib import Path

import pytest

from mcp_app.config import Configuration, load_config_from_file, safe_expandvars


def test_load_config_from_file_valid() -> None:
    """Test loading a valid configuration file."""
    config_data = """
[server]
name = "test-server"
version = "1.0.0"

[server.transport]
type = "http"

[server.transport.http]
host = "localhost"

[middleware]
[middleware.access_logs]
excluded_headers = ["Authorization"]
redacted_headers = ["password"]

[middleware.jwt]
enabled = true

[middleware.jwt.validation]
strategy = "local"
forwarded_header = "X-Forwarded-User"

[middleware.jwt.validation.local]
jwks_uri = "https://example.com/jwks"
cache_interval = "PT1H"

[[middleware.jwt.validation.local.allow_conditions]]
expression = "user.roles contains 'admin'"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_data)
        f.flush()
        config_path = Path(f.name)

    try:
        config = load_config_from_file(config_path)
        assert isinstance(config, Configuration)
        assert config.server is not None
        assert config.server.name == "test-server"
        assert config.server.version == "1.0.0"
        assert config.server.transport is not None
        assert config.server.transport.type == "http"
        assert config.server.transport.http is not None
        assert config.server.transport.http.host == "localhost"
        assert config.middleware is not None
        assert config.middleware.access_logs.excluded_headers == ["Authorization"]
        assert config.middleware.access_logs.redacted_headers == ["password"]
        assert config.middleware.jwt is not None
        assert config.middleware.jwt.enabled is True
        assert config.middleware.jwt.validation is not None
        assert config.middleware.jwt.validation.strategy == "local"
        assert config.middleware.jwt.validation.forwarded_header == "X-Forwarded-User"
        assert config.middleware.jwt.validation.local is not None
        assert config.middleware.jwt.validation.local.jwks_uri == "https://example.com/jwks"
        assert config.middleware.jwt.validation.local.cache_interval == timedelta(hours=1)
        assert len(config.middleware.jwt.validation.local.allow_conditions) == 1
        assert (
            config.middleware.jwt.validation.local.allow_conditions[0].expression
            == "user.roles contains 'admin'"
        )
    finally:
        config_path.unlink()


def test_load_config_from_file_file_not_found() -> None:
    """Test loading a configuration file that does not exist."""
    with pytest.raises(
        FileNotFoundError,
        match=r"Configuration file not found at: nonexistent.toml",
    ):
        load_config_from_file("nonexistent.toml")


def test_jwt_exposed_claims_default() -> None:
    """Test that jwt_exposed_claims defaults to 'all'."""
    config = Configuration()
    assert config.jwt_exposed_claims == "all"


def test_jwt_exposed_claims_custom_list() -> None:
    """Test setting jwt_exposed_claims to a custom list."""
    config = Configuration(jwt_exposed_claims=["user_id", "roles"])
    assert config.jwt_exposed_claims == ["user_id", "roles"]


def test_safe_expandvars_allowed() -> None:
    """Test safe_expandvars with allowed variables."""
    os.environ["TEST_VAR"] = "expanded_value"
    try:
        result = safe_expandvars("${TEST_VAR}", {"TEST_VAR"})
        assert result == "expanded_value"
    finally:
        del os.environ["TEST_VAR"]


def test_safe_expandvars_blocked() -> None:
    """Test safe_expandvars with blocked variables."""
    os.environ["BLOCKED_VAR"] = "blocked_content"
    try:
        result = safe_expandvars("${BLOCKED_VAR}", {"TEST_VAR"})
        assert result == "${BLOCKED_VAR}"  # Should not expand
    finally:
        del os.environ["BLOCKED_VAR"]


def test_safe_expandvars_no_restriction() -> None:
    """Test safe_expandvars without restrictions."""
    os.environ["ANY_VAR"] = "any_value"
    try:
        result = safe_expandvars("${ANY_VAR}")
        assert result == "any_value"
    finally:
        del os.environ["ANY_VAR"]
