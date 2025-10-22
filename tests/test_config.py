"""Tests for the configuration module."""

import tempfile
from datetime import timedelta
from pathlib import Path

import pytest

from mcp_app.config import Configuration, load_config_from_file


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
