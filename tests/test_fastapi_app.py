"""Tests for the FastAPIApp class."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from mcp_app.app_config import AppConfig
from mcp_app.config import ServerConfig
from mcp_app.fastapi_app import FastAPIApp
from mcp_app.mcp_server import MCPServer

HTTP_200_OK = 200


def test_fastapi_app_init() -> None:
    """Test FastAPIApp initialization."""
    config = MagicMock()
    mcp = MagicMock()
    app = FastAPIApp(config, mcp)
    assert app.config == config
    assert app.mcp == mcp
    assert app.app is not None


def test_read_root_with_config() -> None:
    """Test read_root endpoint with config."""
    mock_config = MagicMock()
    mock_config.server = ServerConfig(name="TestServer", version="1.0")
    test_app_config = AppConfig()
    test_app_config._config = mock_config
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/")
    assert response.status_code == HTTP_200_OK
    assert "Hello from TestServer" in response.json()["message"]


def test_read_root_without_config() -> None:
    """Test read_root endpoint without config."""
    test_app_config = AppConfig()
    test_app_config._config = None
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/")
    assert response.status_code == HTTP_200_OK
    assert "Hello from Unknown" in response.json()["message"]


def test_health_check() -> None:
    """Test health check endpoint."""
    test_app_config = AppConfig()
    test_app_config._config = None
    test_mcp_server = MCPServer()
    test_fastapi_app = FastAPIApp(test_app_config.config, test_mcp_server.mcp)
    client = TestClient(test_fastapi_app.app)
    response = client.get("/health")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"status": "ok"}
