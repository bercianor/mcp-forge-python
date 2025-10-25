"""Tests for the AppConfig class."""

from unittest.mock import MagicMock, patch

from mcp_app.app_config import AppConfig
from mcp_app.config import (
    AccessLogsConfig,
    Configuration,
    JWTConfig,
    MiddlewareConfig,
    ServerConfig,
)


def test_app_config_init() -> None:
    """Test AppConfig initialization."""
    config = AppConfig()
    assert config.config is None


@patch("mcp_app.app_config.load_config_from_file")
@patch("mcp_app.app_config.logger")
def test_load_configuration_success(mock_logger: MagicMock, mock_load: MagicMock) -> None:
    """Test successful configuration loading."""
    mock_config = Configuration(server=ServerConfig(name="Test", version="1.0"))
    mock_load.return_value = mock_config

    config = AppConfig()
    config.load_configuration()

    assert config.config == mock_config
    mock_logger.info.assert_called()


@patch("mcp_app.app_config.load_config_from_file")
@patch("mcp_app.app_config.logger")
def test_load_configuration_file_not_found(mock_logger: MagicMock, mock_load: MagicMock) -> None:
    """Test configuration loading when file not found."""
    mock_load.side_effect = FileNotFoundError

    config = AppConfig()
    config.load_configuration()

    assert config.config is None
    mock_logger.error.assert_called()


@patch("mcp_app.app_config.load_config_from_file")
@patch("mcp_app.app_config.logger")
def test_load_configuration_exception(mock_logger: MagicMock, mock_load: MagicMock) -> None:
    """Test configuration loading when exception occurs."""
    mock_load.side_effect = Exception("Test error")

    config = AppConfig()
    config.load_configuration()

    assert config.config is None
    mock_logger.exception.assert_called()


@patch("mcp_app.app_config.logger")
def test_safe_log_config_with_server_and_jwt(mock_logger: MagicMock) -> None:
    """Test safe_log_config with server and JWT config."""
    config = Configuration(
        server=ServerConfig(name="TestServer", version="1.0.0"),
        middleware=MiddlewareConfig(
            access_logs=AccessLogsConfig(),
            jwt=JWTConfig(enabled=True),
        ),
    )

    app_config = AppConfig()
    app_config.safe_log_config(config)

    calls = [call.args for call in mock_logger.info.call_args_list]
    assert ("Server Name: %s", "TestServer") in calls
    assert ("Server Version: %s", "1.0.0") in calls
    assert ("JWT Middleware: enabled=%s", True) in calls


@patch("mcp_app.app_config.logger")
def test_safe_log_config_none_config(mock_logger: MagicMock) -> None:
    """Test safe_log_config with None config."""
    app_config = AppConfig()
    app_config.safe_log_config(None)

    mock_logger.info.assert_not_called()
