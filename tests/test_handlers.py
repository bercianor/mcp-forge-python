"""Tests for the handlers module."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest
from fastapi import HTTPException

from mcp_app.config import Configuration, OAuthAuthorizationServer, OAuthProtectedResourceConfig
from mcp_app.handlers.handlers import HandlersManager

HTTP_403_FORBIDDEN = 403

HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_SERVER_ERROR = 500


def test_handlers_manager_init() -> None:
    """Test HandlersManager initialization."""
    config = Configuration()
    manager = HandlersManager(config)
    assert manager.config == config


@pytest.mark.asyncio
async def test_handle_oauth_authorization_server_disabled() -> None:
    """Test handle_oauth_authorization_server when disabled."""
    config = Configuration(
        oauth_authorization_server=OAuthAuthorizationServer(enabled=False, issuer_uri="")
    )
    manager = HandlersManager(config)
    with pytest.raises(HTTPException) as exc_info:
        await manager.handle_oauth_authorization_server()
    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert "OAuth authorization server not enabled" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.handlers.handlers.httpx.AsyncClient")
async def test_handle_oauth_authorization_server_success(mock_client_class: MagicMock) -> None:
    """Test handle_oauth_authorization_server successful response."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"test": "data"}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__aenter__.return_value = mock_client

    config = Configuration(
        oauth_authorization_server=OAuthAuthorizationServer(
            enabled=True, issuer_uri="https://example.com"
        )
    )
    manager = HandlersManager(config)

    result = await manager.handle_oauth_authorization_server()
    assert result == {"test": "data"}
    mock_client.get.assert_called_once_with("https://example.com/.well-known/openid-configuration")


@pytest.mark.asyncio
@patch("mcp_app.handlers.handlers.httpx.AsyncClient")
async def test_handle_oauth_authorization_server_http_error(mock_client_class: MagicMock) -> None:
    """Test handle_oauth_authorization_server with HTTP error."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError("Network error")
    mock_client_class.return_value.__aenter__.return_value = mock_client

    config = Configuration(
        oauth_authorization_server=OAuthAuthorizationServer(
            enabled=True, issuer_uri="https://example.com"
        )
    )
    manager = HandlersManager(config)

    with pytest.raises(HTTPException) as exc_info:
        await manager.handle_oauth_authorization_server()
    assert exc_info.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error fetching OpenID config" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_handle_oauth_protected_resources_disabled() -> None:
    """Test handle_oauth_protected_resources when disabled."""
    config = Configuration(
        oauth_protected_resource=OAuthProtectedResourceConfig(
            enabled=False, resource="", auth_servers=[], jwks_uri="", scopes_supported=[]
        )
    )
    manager = HandlersManager(config)
    with pytest.raises(HTTPException) as exc_info:
        await manager.handle_oauth_protected_resources()
    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert "OAuth protected resource not enabled" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_handle_oauth_protected_resources_success() -> None:
    """Test handle_oauth_protected_resources successful response."""
    pr_config = OAuthProtectedResourceConfig(
        enabled=True,
        resource="https://api.example.com",
        auth_servers=["https://auth.example.com"],
        jwks_uri="https://auth.example.com/jwks",
        scopes_supported=["read", "write"],
        bearer_methods_supported=["Bearer"],
        resource_signing_alg_values_supported=["RS256"],
        resource_name="Example API",
        resource_documentation="https://docs.example.com",
        resource_policy_uri="https://policy.example.com",
        resource_tos_uri="https://tos.example.com",
        tls_client_certificate_bound_access_tokens=True,
        authorization_details_types_supported=["type1"],
        dpop_signing_alg_values_supported=["ES256"],
        dpop_bound_access_tokens_required=True,
    )
    config = Configuration(oauth_protected_resource=pr_config)
    manager = HandlersManager(config)

    result = await manager.handle_oauth_protected_resources()
    expected = {
        "resource": "https://api.example.com",
        "authorization_servers": ["https://auth.example.com"],
        "jwks_uri": "https://auth.example.com/jwks",
        "scopes_supported": ["read", "write"],
        "bearer_methods_supported": ["Bearer"],
        "resource_signing_alg_values_supported": ["RS256"],
        "resource_name": "Example API",
        "resource_documentation": "https://docs.example.com",
        "resource_policy_uri": "https://policy.example.com",
        "resource_tos_uri": "https://tos.example.com",
        "tls_client_certificate_bound_access_tokens": True,
        "authorization_details_types_supported": ["type1"],
        "dpop_signing_alg_values_supported": ["ES256"],
        "dpop_bound_access_tokens_required": True,
    }
    assert result == expected


def test_is_uri_allowed_no_whitelist() -> None:
    """Test _is_uri_allowed with no whitelist."""
    config = Configuration(oauth_whitelist_domains=[])
    manager = HandlersManager(config)
    assert manager._is_uri_allowed("https://example.com") is True


def test_is_uri_allowed_allowed_domain() -> None:
    """Test _is_uri_allowed with allowed domain."""
    config = Configuration(oauth_whitelist_domains=["example.com"])
    manager = HandlersManager(config)
    assert manager._is_uri_allowed("https://sub.example.com") is True


def test_is_uri_allowed_blocked_domain() -> None:
    """Test _is_uri_allowed with blocked domain."""
    config = Configuration(oauth_whitelist_domains=["example.com"])
    manager = HandlersManager(config)
    assert manager._is_uri_allowed("https://bad.com") is False


@pytest.mark.asyncio
async def test_handle_oauth_authorization_server_uri_blocked() -> None:
    """Test handle_oauth_authorization_server with blocked URI."""
    config = Configuration(
        oauth_authorization_server=OAuthAuthorizationServer(
            enabled=True, issuer_uri="https://bad.com"
        ),
        oauth_whitelist_domains=["example.com"],
    )
    manager = HandlersManager(config)
    with pytest.raises(HTTPException) as exc_info:
        await manager.handle_oauth_authorization_server()
    assert exc_info.value.status_code == HTTP_403_FORBIDDEN
    assert "Issuer URI not in allowed domains" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.handlers.handlers.httpx.AsyncClient")
async def test_handle_oauth_authorization_server_sanitized(mock_client_class: MagicMock) -> None:
    """Test handle_oauth_authorization_server sanitizes response."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "issuer": "https://example.com",
        "private_key_jwt": "secret",  # Should be removed
        "authorization_endpoint": "https://example.com/auth",
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__aenter__.return_value = mock_client

    config = Configuration(
        oauth_authorization_server=OAuthAuthorizationServer(
            enabled=True, issuer_uri="https://example.com"
        )
    )
    manager = HandlersManager(config)

    result = await manager.handle_oauth_authorization_server()
    expected = {
        "issuer": "https://example.com",
        "authorization_endpoint": "https://example.com/auth",
    }
    assert result == expected


@pytest.mark.asyncio
async def test_handle_oauth_protected_resources_uri_blocked() -> None:
    """Test handle_oauth_protected_resources with blocked URI."""
    pr_config = OAuthProtectedResourceConfig(
        enabled=True,
        resource="https://api.example.com",
        auth_servers=["https://bad.com"],
        jwks_uri="https://auth.example.com/jwks",
        scopes_supported=["read"],
    )
    config = Configuration(
        oauth_protected_resource=pr_config, oauth_whitelist_domains=["example.com"]
    )
    manager = HandlersManager(config)
    with pytest.raises(HTTPException) as exc_info:
        await manager.handle_oauth_protected_resources()
    assert exc_info.value.status_code == HTTP_403_FORBIDDEN
    assert "Auth server URI not allowed" in str(exc_info.value.detail)
