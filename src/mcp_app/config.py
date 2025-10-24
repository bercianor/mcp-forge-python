"""
Configuration module for the MCP-Forge-Python application.

This module defines the Pydantic models that correspond to the application's
configuration structure, originally defined in the Go version. It also provides
a loader function to read configuration from a YAML file, expanding environment
variables for dynamic configuration.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import timedelta  # noqa: TC003
from pathlib import Path

try:
    import tomllib  # pragma: no cover
except ImportError:  # pragma: no cover
    import tomli as tomllib  # pragma: no cover

from pydantic import BaseModel

# --- Pydantic Models for Configuration ---


class ServerTransportHTTPConfig(BaseModel):
    """HTTP transport configuration."""

    host: str


class ServerTransportConfig(BaseModel):
    """Server transport configuration."""

    type: str
    http: ServerTransportHTTPConfig | None = None


class ServerConfig(BaseModel):
    """Server configuration."""

    name: str
    version: str
    transport: ServerTransportConfig | None = None


class AccessLogsConfig(BaseModel):
    """Access logs middleware configuration."""

    excluded_headers: list[str] = []
    redacted_headers: list[str] = []


class JWTValidationAllowCondition(BaseModel):
    """Condition for allowing JWT validation."""

    expression: str


class JWTValidationLocalConfig(BaseModel):
    """Local JWT validation configuration."""

    jwks_uri: str
    cache_interval: timedelta
    allow_conditions: list[JWTValidationAllowCondition] = []


class JWTValidationConfig(BaseModel):
    """JWT validation configuration."""

    strategy: str
    forwarded_header: str | None = None
    local: JWTValidationLocalConfig | None = None


class JWTConfig(BaseModel):
    """JWT middleware configuration."""

    enabled: bool
    validation: JWTValidationConfig | None = None


class MiddlewareConfig(BaseModel):
    """Middleware configuration."""

    access_logs: AccessLogsConfig
    jwt: JWTConfig | None = None


class OAuthAuthorizationServer(BaseModel):
    """OAuth authorization server configuration."""

    enabled: bool
    issuer_uri: str


class OAuthProtectedResourceConfig(BaseModel):
    """OAuth protected resource configuration."""

    enabled: bool
    resource: str
    auth_servers: list[str]
    jwks_uri: str
    scopes_supported: list[str]
    bearer_methods_supported: list[str] = []
    resource_signing_alg_values_supported: list[str] = []
    resource_name: str | None = None
    resource_documentation: str | None = None
    resource_policy_uri: str | None = None
    resource_tos_uri: str | None = None
    tls_client_certificate_bound_access_tokens: bool = False
    authorization_details_types_supported: list[str] = []
    dpop_signing_alg_values_supported: list[str] = []
    dpop_bound_access_tokens_required: bool = False


class Configuration(BaseModel):
    """Top-level configuration model for the application."""

    server: ServerConfig | None = None
    middleware: MiddlewareConfig | None = None
    oauth_authorization_server: OAuthAuthorizationServer | None = None
    oauth_protected_resource: OAuthProtectedResourceConfig | None = None
    jwt_exposed_claims: str | list[str] = "all"
    oauth_whitelist_domains: list[str] = []


# --- Configuration Loading Function ---


def safe_expandvars(content: str, allowed_vars: set[str] | None = None) -> str:
    """
    Safely expand environment variables in content.

    Only expands variables that are in the allowed_vars set to prevent accidental
    exposure of sensitive environment variables.

    Args:
        content: The string content to expand variables in.
        allowed_vars: Set of allowed environment variable names. If None, allows all.

    Returns:
        The content with allowed variables expanded.

    """

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1) or match.group(2)
        if allowed_vars is not None and var_name not in allowed_vars:
            # Log warning but don't expand
            logger = logging.getLogger(__name__)
            logger.warning("Blocked expansion of disallowed env var: %s", var_name)
            return match.group(0)  # Return original ${VAR} or $VAR unchanged
        return os.environ.get(var_name, match.group(0))

    # Match ${VAR} or $VAR patterns
    pattern = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")
    return pattern.sub(replacer, content)


def load_config_from_file(filepath: str | Path) -> Configuration:
    """
    Read a TOML configuration file.

    Expand environment variables and parse it into a Configuration object.

        filepath: The path to the TOML configuration file.

    Returns:
        A validated Configuration object.


    """
    config_path = Path(filepath)
    if not config_path.is_file():
        msg = f"Configuration file not found at: {filepath}"
        raise FileNotFoundError(msg)

    raw_content = config_path.read_text(encoding="utf-8")
    # Only allow expansion of common, non-sensitive vars
    allowed_vars = {
        "HOME",
        "USER",
        "PATH",
        "PWD",
        "SHELL",
        "LANG",
        "LC_ALL",
        "TMPDIR",
        "TEMP",
        "TMP",
        "LOGNAME",
        "USERNAME",
    }
    expanded_content = safe_expandvars(raw_content, allowed_vars)
    config_data = tomllib.loads(expanded_content)

    return Configuration.model_validate(config_data)
