"""
Configuration management for the MCP-Forge-Python service.

This module handles loading and managing application configuration.
"""

import logging

from mcp_app.config import Configuration, load_config_from_file

logger = logging.getLogger(__name__)


class AppConfig:
    """Handles application configuration loading and management."""

    def __init__(self) -> None:
        """Initialize AppConfig with no loaded configuration."""
        self._config: Configuration | None = None

    @property
    def config(self) -> Configuration | None:
        """Get the loaded configuration."""
        return self._config

    def load_configuration(self) -> None:
        """Load configuration from file."""
        config_paths = ["/data/config.toml", "config.toml"]  # Check mounted config first

        for config_path in config_paths:
            try:
                self._config = load_config_from_file(config_path)
                logger.info("Configuration loaded successfully from %s.", config_path)
                self.safe_log_config(self._config)
                break
            except FileNotFoundError:  # pragma: no cover
                continue  # pragma: no cover
            except Exception:  # pragma: no cover
                logger.exception("Failed to load config from %s", config_path)  # pragma: no cover
                self._config = None  # pragma: no cover
                break  # pragma: no cover
        else:  # pragma: no cover
            logger.error(
                "No configuration file found in any of: %s", config_paths
            )  # pragma: no cover
            self._config = None  # pragma: no cover

    def safe_log_config(self, config: Configuration | None) -> None:
        """Log configuration fields safely, avoiding sensitive data."""
        if config and config.server:
            logger.info("Server Name: %s", config.server.name)
            logger.info("Server Version: %s", config.server.version)
        # Avoid logging URIs, secrets, or sensitive fields
        # Only log basic info like enabled features
        if config and config.middleware and config.middleware.jwt:
            logger.info("JWT Middleware: enabled=%s", config.middleware.jwt.enabled)
