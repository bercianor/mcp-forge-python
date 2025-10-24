"""
Main application file for the MCP-Forge-Python service.

This file initializes the MCP server using FastMCP, loads the configuration,
and sets up OAuth endpoints and middlewares.
"""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from mcp.server import FastMCP

from mcp_app.config import Configuration, load_config_from_file
from mcp_app.context import set_exposed_claims
from mcp_app.handlers.handlers import HandlersManager
from mcp_app.middlewares.access_logs import AccessLogsMiddleware
from mcp_app.middlewares.jwt_validation import JWTValidationMiddleware
from mcp_app.tools.router import register_tools

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global variable to hold the application's configuration
config: Configuration | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001  # pragma: no cover
    """Application lifespan context manager."""
    global config  # noqa: PLW0603
    config_paths = ["/data/config.toml", "config.toml"]  # Check mounted config first

    for config_path in config_paths:
        try:
            config = load_config_from_file(config_path)
            logger.info("Configuration loaded successfully from %s.", config_path)
            logger.info("Server Name: %s", config.server.name if config.server else "N/A")
            # Set JWT exposed claims configuration
            set_exposed_claims(config.jwt_exposed_claims)
            break
        except FileNotFoundError:
            continue
        except Exception:
            logger.exception("FATAL: Failed to load configuration from %s", config_path)
            config = None
            break
    else:
        logger.error("FATAL: No configuration file found in any of: %s", config_paths)
        config = None

    yield

    logger.info("Application shutting down.")


# Initialize FastMCP server (will be updated in lifespan if config available)
mcp = FastMCP("MCP-Forge-Python")

# Register tools
register_tools(mcp)

# Create FastAPI app for additional endpoints
app = FastAPI(
    title="MCP-Forge-Python",
    description="A Python port of the MCP Forge Go project.",
    lifespan=lifespan,
)

# Add middlewares
if config and config.middleware:  # pragma: no cover
    if config.middleware.access_logs:
        app.add_middleware(
            AccessLogsMiddleware,
            excluded_headers=config.middleware.access_logs.excluded_headers,
            redacted_headers=config.middleware.access_logs.redacted_headers,
        )

    if config.middleware.jwt and config.middleware.jwt.enabled:
        jwt_config = config.middleware.jwt
        validation = jwt_config.validation
        local_config = validation.local if validation else None

        app.add_middleware(
            JWTValidationMiddleware,
            strategy=validation.strategy if validation else "external",
            forwarded_header=validation.forwarded_header if validation else "X-Validated-Jwt",
            jwks_uri=local_config.jwks_uri if local_config else None,
            cache_interval=local_config.cache_interval.total_seconds() if local_config else 300,
            allow_conditions=[
                c.expression for c in (local_config.allow_conditions if local_config else [])
            ],
        )

# Initialize handlers
handlers_manager = HandlersManager(config) if config else None


# OAuth endpoints
@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server() -> dict[str, Any]:
    """Handle OAuth authorization server metadata endpoint."""
    if not handlers_manager:
        return {"error": "Configuration not loaded"}
    return await handlers_manager.handle_oauth_authorization_server()  # pragma: no cover


@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource() -> dict[str, Any]:
    """Handle OAuth protected resource metadata endpoint."""
    if not handlers_manager:
        return {"error": "Configuration not loaded"}
    return await handlers_manager.handle_oauth_protected_resources()  # pragma: no cover


# Mount MCP servers
app.mount("/mcp", mcp.sse_app())  # SSE transport
# WebSocket not available in this version


@app.get("/")
async def read_root() -> dict[str, str]:
    """Root endpoint returning server information."""
    server_name = config.server.name if config and config.server else "Unknown"
    return {"message": f"Hello from {server_name}"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


def main() -> None:
    """Run the main application."""
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run(transport="stdio")
    else:
        # Default to HTTP
        uvicorn.run(app, host="127.0.0.1", port=8080)


def main_http() -> None:
    """Run the HTTP server."""
    uvicorn.run(app, host="127.0.0.1", port=8080)


def main_stdio() -> None:
    """Run the stdio transport."""
    mcp.run(transport="stdio")


# For stdio transport
if __name__ == "__main__":  # pragma: no cover
    main()
