"""
Main application file for the MCP-Forge-Python service.

This file orchestrates the initialization of the MCP server, configuration,
and FastAPI application using dedicated classes.
"""

import logging
import sys

import uvicorn

from mcp_app.app_config import AppConfig
from mcp_app.config import Configuration
from mcp_app.fastapi_app import FastAPIApp
from mcp_app.mcp_server import MCPServer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize components
app_config = AppConfig()
app_config.load_configuration()

mcp_server = MCPServer()

fastapi_app = FastAPIApp(app_config.config, mcp_server.mcp)

# Expose for backward compatibility (tests)
config = app_config.config
app = fastapi_app.app
mcp = mcp_server.mcp
handlers_manager = fastapi_app.handlers_manager


def safe_log_config(config_arg: Configuration) -> None:
    """Safe log config (backward compatibility)."""
    app_config.safe_log_config(config_arg)


def get_host_and_port() -> tuple[str, int]:
    """Get host and port from configuration or defaults."""
    config = app_config.config
    if config and config.server and config.server.transport and config.server.transport.http:
        http_config = config.server.transport.http
        return http_config.host, http_config.port
    return "0.0.0.0", 8080  # noqa: S104


def main() -> None:
    """Run the main application."""
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp_server.mcp.run(transport="stdio")
    else:
        # Default to HTTP
        host, port = get_host_and_port()
        uvicorn.run(fastapi_app.app, host=host, port=port)


def main_http() -> None:
    """Run the HTTP server."""
    host, port = get_host_and_port()
    uvicorn.run(fastapi_app.app, host=host, port=port)  # pragma: no cover


def main_stdio() -> None:
    """Run the stdio transport."""
    mcp_server.mcp.run(transport="stdio")  # pragma: no cover


# For stdio transport
if __name__ == "__main__":  # pragma: no cover
    main()
