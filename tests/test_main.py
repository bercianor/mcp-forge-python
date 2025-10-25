"""Tests for the main MCP application."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from mcp.server import FastMCP

import mcp_app.main
from mcp_app.config import (
    AccessLogsConfig,
    Configuration,
    JWTConfig,
    MiddlewareConfig,
    ServerConfig,
)
from mcp_app.main import (
    handlers_manager,
    main,
    safe_log_config,
)
from mcp_app.middlewares.access_logs import AccessLogsMiddleware
from mcp_app.tools.router import register_tools

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_307_TEMPORARY_REDIRECT = 307
PORT_DEFAULT = 8080


@pytest.fixture
def client() -> TestClient:
    """Test client for the FastAPI app."""
    # Create a test config without JWT middleware
    test_config = None

    # Create fresh app with test config

    test_app = FastAPI(
        title="MCP-Forge-Python",
        description="A Python port of the MCP Forge Go project.",
        redirect_slashes=False,
    )

    # Add CORS (default)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add access logs if config has it
    # pragma: no cover
    if test_config and test_config.middleware and test_config.middleware.access_logs:
        test_app.add_middleware(  # pragma: no cover
            AccessLogsMiddleware,
            excluded_headers=test_config.middleware.access_logs.excluded_headers,
            redacted_headers=test_config.middleware.access_logs.redacted_headers,
        )

    # Register tools
    test_mcp = FastMCP("MCP-Forge-Python")
    register_tools(test_mcp)

    # Add endpoints
    @test_app.get("/")
    async def read_root() -> dict[str, str]:
        from mcp_app.main import config  # noqa: PLC0415

        server_name = config.server.name if config and config.server else "Unknown"
        return {"message": f"Hello from {server_name}"}

    @test_app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.get("/.well-known/oauth-authorization-server")
    async def oauth_authorization_server() -> dict[str, Any]:
        if not handlers_manager:  # pragma: no cover
            return {"error": "Configuration not loaded"}
        return await handlers_manager.handle_oauth_authorization_server()

    @test_app.get("/.well-known/oauth-protected-resource")
    async def oauth_protected_resource() -> dict[str, Any]:
        if not handlers_manager:  # pragma: no cover
            return {"error": "Configuration not loaded"}
        return await handlers_manager.handle_oauth_protected_resources()

    return TestClient(test_app)


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200  # noqa: PLR2004
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200  # noqa: PLR2004
    data = response.json()
    assert "message" in data
    assert "Hello from" in data["message"]


def test_oauth_authorization_server_no_config(client: TestClient) -> None:
    """Test OAuth authorization server endpoint when config not loaded."""
    with patch("tests.test_main.handlers_manager", None):
        response = client.get("/.well-known/oauth-authorization-server")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"error": "Configuration not loaded"}


def test_oauth_protected_resource_no_config(client: TestClient) -> None:
    """Test OAuth protected resource endpoint when config not loaded."""
    with patch("tests.test_main.handlers_manager", None):
        response = client.get("/.well-known/oauth-protected-resource")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"error": "Configuration not loaded"}


@patch("sys.argv", ["main.py", "stdio"])
@patch("mcp_app.main.mcp")
def test_main_stdio(mock_mcp: MagicMock) -> None:
    """Test main function with stdio argument."""
    main()
    mock_mcp.run.assert_called_once_with(transport="stdio")


@patch("sys.argv", ["main.py"])
@patch("uvicorn.run")
def test_main_http(mock_uvicorn_run: MagicMock) -> None:
    """Test main function with default HTTP."""
    main()
    mock_uvicorn_run.assert_called_once()
    args, kwargs = mock_uvicorn_run.call_args
    assert isinstance(args[0], FastAPI)
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == PORT_DEFAULT


@patch("mcp_app.main.logger")
def test_safe_log_config(mock_logger: MagicMock) -> None:
    """Test safe_log_config function."""
    # Test with server and middleware config
    config = Configuration(
        server=ServerConfig(name="TestServer", version="1.0.0"),
        middleware=MiddlewareConfig(
            access_logs=AccessLogsConfig(),
            jwt=JWTConfig.model_validate({"enabled": True}),
        ),
    )
    safe_log_config(config)

    # Verify logging calls
    calls = [call.args for call in mock_logger.info.call_args_list]
    assert ("Server Name: %s", "TestServer") in calls
    assert ("Server Version: %s", "1.0.0") in calls
    assert ("JWT Middleware: enabled=%s", True) in calls


def test_oauth_authorization_server_with_config(client: TestClient) -> None:
    """Test OAuth authorization server endpoint when config loaded."""
    mock_manager = MagicMock()
    mock_manager.handle_oauth_authorization_server = AsyncMock(return_value={"test": "data"})
    with patch("tests.test_main.handlers_manager", mock_manager):
        response = client.get("/.well-known/oauth-authorization-server")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"test": "data"}
        mock_manager.handle_oauth_authorization_server.assert_called_once()


def test_oauth_protected_resource_with_config(client: TestClient) -> None:
    """Test OAuth protected resource endpoint when config loaded."""
    mock_manager = MagicMock()
    mock_manager.handle_oauth_protected_resources = AsyncMock(return_value={"test": "data"})
    with patch("tests.test_main.handlers_manager", mock_manager):
        response = client.get("/.well-known/oauth-protected-resource")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"test": "data"}
        mock_manager.handle_oauth_protected_resources.assert_called_once()


def test_login_no_config() -> None:
    """Test login endpoint when config is None."""
    original_config = mcp_app.main.config
    mcp_app.main.config = None
    try:
        client = TestClient(mcp_app.main.app)
        response = client.get("/login")
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json() == {"error": "Config incomplete"}
    finally:
        mcp_app.main.config = original_config


def test_login_incomplete_config() -> None:
    """Test login endpoint when config is incomplete."""
    original_config = mcp_app.main.config
    mock_config = MagicMock()
    mock_config.auth = None
    mock_config.middleware = None
    mcp_app.main.config = mock_config
    try:
        client = TestClient(mcp_app.main.app)
        response = client.get("/login")
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response.json() == {"error": "Config incomplete"}
    finally:
        mcp_app.main.config = original_config


def test_login_success() -> None:
    """Test login endpoint with valid config."""
    original_config = mcp_app.main.config

    # Mock valid config
    mock_auth = MagicMock()
    mock_auth.client_id = "test_client_id"
    mock_auth.redirect_uri = "http://localhost/callback"

    mock_local = MagicMock()
    mock_local.issuer = "https://test.auth0.com/"
    mock_local.audience = "test_audience"

    mock_validation = MagicMock()
    mock_validation.local = mock_local

    mock_jwt = MagicMock()
    mock_jwt.validation = mock_validation

    mock_middleware_config = MagicMock()
    mock_middleware_config.jwt = mock_jwt

    mock_config = MagicMock()
    mock_config.auth = mock_auth
    mock_config.middleware = mock_middleware_config

    mcp_app.main.config = mock_config
    try:
        client = TestClient(mcp_app.main.app)
        response = client.get("/login", follow_redirects=False)
        assert response.status_code == HTTP_307_TEMPORARY_REDIRECT  # Redirect
        location = response.headers.get("location", "")
        assert "https://test.auth0.com/authorize?" in location
        assert "client_id=test_client_id" in location
        assert "redirect_uri=http://localhost/callback" in location
        assert "audience=test_audience" in location
    finally:
        mcp_app.main.config = original_config


def test_callback_no_config() -> None:
    """Test callback endpoint when config is None."""
    original_config = mcp_app.main.config
    mcp_app.main.config = None
    try:
        client = TestClient(mcp_app.main.app)
        response = client.get("/callback?code=test_code")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"error": "Config incomplete"}
    finally:
        mcp_app.main.config = original_config


def test_callback_incomplete_config() -> None:
    """Test callback endpoint when config is incomplete."""
    original_config = mcp_app.main.config
    mock_config = MagicMock()
    mock_config.auth = None
    mock_config.middleware = None
    mcp_app.main.config = mock_config
    try:
        client = TestClient(mcp_app.main.app)
        response = client.get("/callback?code=test_code")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"error": "Config incomplete"}
    finally:
        mcp_app.main.config = original_config


@patch("httpx.AsyncClient")
def test_callback_success(mock_client_class: MagicMock) -> None:
    """Test callback endpoint with successful token exchange."""
    original_config = mcp_app.main.config

    # Mock valid config
    mock_auth = MagicMock()
    mock_auth.client_id = "test_client_id"
    mock_auth.client_secret = "test_secret"  # noqa: S105
    mock_auth.redirect_uri = "http://localhost/callback"

    mock_local = MagicMock()
    mock_local.issuer = "https://test.auth0.com/"

    mock_validation = MagicMock()
    mock_validation.local = mock_local

    mock_jwt_config = MagicMock()
    mock_jwt_config.validation = mock_validation

    mock_middleware_config = MagicMock()
    mock_middleware_config.jwt = mock_jwt_config

    mock_config = MagicMock()
    mock_config.auth = mock_auth
    mock_config.middleware = mock_middleware_config

    mcp_app.main.config = mock_config

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_token"}

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client_instance

    try:
        client = TestClient(mcp_app.main.app)
        response = client.get("/callback?code=test_code")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"access_token": "test_token"}
    finally:
        mcp_app.main.config = original_config


@patch("httpx.AsyncClient")
def test_callback_token_exchange_failure(mock_client_class: MagicMock) -> None:
    """Test callback endpoint when token exchange fails."""
    original_config = mcp_app.main.config

    # Mock valid config
    mock_auth = MagicMock()
    mock_auth.client_id = "test_client_id"
    mock_auth.client_secret = "test_secret"  # noqa: S105
    mock_auth.redirect_uri = "http://localhost/callback"

    mock_local = MagicMock()
    mock_local.issuer = "https://test.auth0.com/"

    mock_validation = MagicMock()
    mock_validation.local = mock_local

    mock_jwt_config = MagicMock()
    mock_jwt_config.validation = mock_validation

    mock_middleware_config = MagicMock()
    mock_middleware_config.jwt = mock_jwt_config

    mock_config = MagicMock()
    mock_config.auth = mock_auth
    mock_config.middleware = mock_middleware_config

    mcp_app.main.config = mock_config

    # Mock httpx response with failure
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid code"

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client_instance

    try:
        client = TestClient(mcp_app.main.app)
        response = client.get("/callback?code=test_code")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"error": "Failed to get token", "details": "Invalid code"}
    finally:
        mcp_app.main.config = original_config
