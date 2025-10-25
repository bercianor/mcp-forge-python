"""Tests for the main MCP application."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mcp_app.app_config import AppConfig
from mcp_app.config import (
    AccessLogsConfig,
    Configuration,
    JWTConfig,
    MiddlewareConfig,
    ServerConfig,
)
from mcp_app.fastapi_app import FastAPIApp
from mcp_app.main import (
    get_host_and_port,
    main,
    main_http,
    main_stdio,
    safe_log_config,
)
from mcp_app.mcp_server import MCPServer

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_307_TEMPORARY_REDIRECT = 307
PORT_DEFAULT = 8080


@pytest.fixture
def client() -> TestClient:
    """Test client for the FastAPI app."""
    # Create test components with None config
    test_app_config = AppConfig()
    test_app_config._config = None  # Set to None for testing
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)

    return TestClient(test_fastapi_app.app)


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
    response = client.get("/.well-known/oauth-authorization-server")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"error": "Configuration not loaded"}


def test_oauth_protected_resource_no_config(client: TestClient) -> None:
    """Test OAuth protected resource endpoint when config not loaded."""
    response = client.get("/.well-known/oauth-protected-resource")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"error": "Configuration not loaded"}


@patch("sys.argv", ["main.py", "stdio"])
@patch("mcp_app.main.mcp_server.mcp")
def test_main_stdio(mock_mcp: MagicMock) -> None:
    """Test main function with stdio argument."""
    main()
    mock_mcp.run.assert_called_once_with(transport="stdio")


@patch("mcp_app.main.mcp_server.mcp")
def test_main_stdio_function(mock_mcp: MagicMock) -> None:
    """Test main_stdio function."""
    main_stdio()
    mock_mcp.run.assert_called_once_with(transport="stdio")


@patch("sys.argv", ["main.py"])
@patch("uvicorn.run")
def test_main_http(mock_uvicorn_run: MagicMock) -> None:
    """Test main function with default HTTP."""
    main()
    mock_uvicorn_run.assert_called_once()
    args, kwargs = mock_uvicorn_run.call_args
    assert isinstance(args[0], FastAPI)
    assert kwargs["host"] == "0.0.0.0"  # noqa: S104  # From config.toml
    assert kwargs["port"] == PORT_DEFAULT


@patch("uvicorn.run")
def test_main_http_function(mock_uvicorn_run: MagicMock) -> None:
    """Test main_http function."""
    main_http()
    mock_uvicorn_run.assert_called_once()
    args, kwargs = mock_uvicorn_run.call_args
    assert isinstance(args[0], FastAPI)
    assert kwargs["host"] == "0.0.0.0"  # noqa: S104  # From config.toml
    assert kwargs["port"] == PORT_DEFAULT


@patch("mcp_app.main.app_config._config", None)
def test_get_host_and_port_no_config() -> None:
    """Test get_host_and_port with no config."""
    host, port = get_host_and_port()
    assert host == "0.0.0.0"  # noqa: S104
    assert port == PORT_DEFAULT


@patch("mcp_app.app_config.logger")
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


def test_oauth_authorization_server_with_config() -> None:
    """Test OAuth authorization server endpoint when config loaded."""
    mock_manager = MagicMock()
    mock_manager.handle_oauth_authorization_server = AsyncMock(return_value={"test": "data"})
    test_app_config = AppConfig()
    test_app_config._config = MagicMock()  # Mock config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    test_fastapi_app.handlers_manager = mock_manager  # Set mock manager
    client = TestClient(test_fastapi_app.app)
    response = client.get("/.well-known/oauth-authorization-server")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"test": "data"}
    mock_manager.handle_oauth_authorization_server.assert_called_once()


def test_oauth_protected_resource_with_config() -> None:
    """Test OAuth protected resource endpoint when config loaded."""
    mock_manager = MagicMock()
    mock_manager.handle_oauth_protected_resources = AsyncMock(return_value={"test": "data"})
    test_app_config = AppConfig()
    test_app_config._config = MagicMock()  # Mock config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    test_fastapi_app.handlers_manager = mock_manager  # Set mock manager
    client = TestClient(test_fastapi_app.app)
    response = client.get("/.well-known/oauth-protected-resource")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"test": "data"}
    mock_manager.handle_oauth_protected_resources.assert_called_once()


def test_login_no_config() -> None:
    """Test login endpoint when config is None."""
    test_app_config = AppConfig()
    test_app_config._config = None
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/login")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "Config incomplete"}


def test_login_incomplete_config() -> None:
    """Test login endpoint when config is incomplete."""
    mock_config = MagicMock()
    mock_config.auth = None
    mock_config.middleware = None
    test_app_config = AppConfig()
    test_app_config._config = mock_config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/login")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "Config incomplete"}


def test_login_success() -> None:
    """Test login endpoint with valid config."""
    # Mock valid config
    mock_auth = MagicMock()
    mock_auth.client_id = "test_client_id"

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

    test_app_config = AppConfig()
    test_app_config._config = mock_config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == HTTP_307_TEMPORARY_REDIRECT  # Redirect
    location = response.headers.get("location", "")
    assert "https://test.auth0.com/authorize?" in location
    assert "client_id=test_client_id" in location
    assert "redirect_uri=http://testserver/callback" in location
    assert "audience=test_audience" in location


def test_callback_no_config() -> None:
    """Test callback endpoint when config is None."""
    test_app_config = AppConfig()
    test_app_config._config = None
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/callback?code=test_code")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"error": "Config incomplete"}


def test_callback_incomplete_config() -> None:
    """Test callback endpoint when config is incomplete."""
    mock_config = MagicMock()
    mock_config.auth = None
    mock_config.middleware = None
    test_app_config = AppConfig()
    test_app_config._config = mock_config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/callback?code=test_code")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"error": "Config incomplete"}


@patch("httpx.AsyncClient")
def test_callback_success(mock_client_class: MagicMock) -> None:
    """Test callback endpoint with successful token exchange."""
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

    test_app_config = AppConfig()
    test_app_config._config = mock_config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_token"}

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client_instance

    client = TestClient(test_fastapi_app.app)
    response = client.get("/callback?code=test_code")
    assert response.status_code == HTTP_200_OK
    assert "test_token" in response.text
    assert response.headers["content-type"] == "text/html; charset=utf-8"


@patch("httpx.AsyncClient")
def test_callback_token_exchange_failure(mock_client_class: MagicMock) -> None:
    """Test callback endpoint when token exchange fails."""
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

    test_app_config = AppConfig()
    test_app_config._config = mock_config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)

    # Mock httpx response with failure
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid code"

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value.__aenter__.return_value = mock_client_instance

    client = TestClient(test_fastapi_app.app)
    response = client.get("/callback?code=test_code")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"error": "Failed to get token", "details": "Invalid code"}


def test_callback_oauth_error() -> None:
    """Test callback endpoint when OAuth returns error."""
    test_app_config = AppConfig()
    test_app_config._config = None  # No config needed for error handling
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get(
        "/callback?error=access_denied&error_description=Scope%20claim%20cannot%20be%20set"
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"error": "access_denied", "description": "Scope claim cannot be set"}


def test_callback_missing_code() -> None:
    """Test callback endpoint when code is missing."""
    test_app_config = AppConfig()
    test_app_config._config = None  # No config needed for error handling
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/callback")  # No params
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"error": "Missing authorization code"}
