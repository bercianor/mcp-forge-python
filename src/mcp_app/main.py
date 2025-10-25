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

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
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

# HTTP status constants
HTTP_OK = 200


def load_configuration() -> None:
    """Load configuration from file."""
    global config  # noqa: PLW0603
    config_paths = ["/data/config.toml", "config.toml"]  # Check mounted config first

    for config_path in config_paths:
        try:
            config = load_config_from_file(config_path)
            logger.info("Configuration loaded successfully from %s.", config_path)
            safe_log_config(config)
            break
        except FileNotFoundError:  # pragma: no cover
            continue  # pragma: no cover
        except Exception:  # pragma: no cover
            logger.exception("Failed to load config from %s", config_path)  # pragma: no cover
            config = None  # pragma: no cover
            break  # pragma: no cover
    else:  # pragma: no cover
        logger.error("No configuration file found in any of: %s", config_paths)  # pragma: no cover
        config = None  # pragma: no cover


def safe_log_config(config: Configuration) -> None:
    """Log configuration fields safely, avoiding sensitive data."""
    if config.server:
        logger.info("Server Name: %s", config.server.name)
        logger.info("Server Version: %s", config.server.version)
    # Avoid logging URIs, secrets, or sensitive fields
    # Only log basic info like enabled features
    if config.middleware and config.middleware.jwt:
        logger.info("JWT Middleware: enabled=%s", config.middleware.jwt.enabled)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001  # pragma: no cover
    """Application lifespan context manager."""
    # Set JWT exposed claims configuration if config is loaded
    if config:
        set_exposed_claims(config.jwt_exposed_claims)

    yield

    logger.info("Application shutting down.")


# Initialize FastMCP server (will be updated in lifespan if config available)
mcp = FastMCP("MCP-Forge-Python")

# Register tools
register_tools(mcp)

# Load configuration
load_configuration()

# Create FastAPI app for additional endpoints
app = FastAPI(
    title="MCP-Forge-Python",
    description="A Python port of the MCP Forge Go project.",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Add CORS middleware
cors_config = (
    config.middleware.cors if config and config.middleware and config.middleware.cors else None
)
if cors_config:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config.allow_origins,
        allow_credentials=cors_config.allow_credentials,
        allow_methods=cors_config.allow_methods,
        allow_headers=cors_config.allow_headers,
    )
else:
    # Default CORS configuration
    app.add_middleware(  # pragma: no cover
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
            issuer=local_config.issuer if local_config else None,
            audience=local_config.audience if local_config else None,
        )

# Initialize handlers
handlers_manager = HandlersManager(config) if config else None


# OAuth endpoints
@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server() -> dict[str, Any]:
    """Handle OAuth authorization server metadata endpoint."""
    if not handlers_manager:  # pragma: no cover
        return {"error": "Configuration not loaded"}  # pragma: no cover
    return await handlers_manager.handle_oauth_authorization_server()  # pragma: no cover


@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource() -> dict[str, Any]:
    """Handle OAuth protected resource metadata endpoint."""
    if not handlers_manager:  # pragma: no cover
        return {"error": "Configuration not loaded"}  # pragma: no cover
    return await handlers_manager.handle_oauth_protected_resources()  # pragma: no cover


@app.get("/")
async def read_root() -> dict[str, str]:
    """Root endpoint returning server information."""
    server_name = config.server.name if config and config.server else "Unknown"  # pragma: no cover
    return {"message": f"Hello from {server_name}"}  # pragma: no cover


@app.get("/login")
async def login() -> Response:
    """Redirect to Auth0 login."""
    if (
        not config
        or not config.auth
        or not config.middleware
        or not config.middleware.jwt
        or not config.middleware.jwt.validation
        or not config.middleware.jwt.validation.local
    ):
        return JSONResponse(status_code=400, content={"error": "Config incomplete"})
    local_config = config.middleware.jwt.validation.local
    auth_url = (
        f"{local_config.issuer}authorize?"
        f"client_id={config.auth.client_id}&"
        "response_type=code&"
        f"redirect_uri={config.auth.redirect_uri}&"
        "scope=openid profile email&"
        f"audience={local_config.audience}"
    )
    return RedirectResponse(auth_url)


@app.get("/callback")
async def callback(code: str) -> dict[str, Any]:
    """Exchange code for token."""
    if (
        not config
        or not config.auth
        or not config.middleware
        or not config.middleware.jwt
        or not config.middleware.jwt.validation
        or not config.middleware.jwt.validation.local
    ):
        return {"error": "Config incomplete"}
    local_config = config.middleware.jwt.validation.local
    token_url = f"{local_config.issuer}oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": config.auth.client_id,
        "client_secret": config.auth.client_secret,
        "code": code,
        "redirect_uri": config.auth.redirect_uri,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data, timeout=10.0)
    if response.status_code == HTTP_OK:
        token_data = response.json()
        return {"access_token": token_data.get("access_token")}
    return {"error": "Failed to get token", "details": response.text}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}  # pragma: no cover


# Mount MCP servers
sse_app = mcp.sse_app()
sse_app.router.redirect_slashes = False
app.mount("/", sse_app)  # SSE transport


def get_host_and_port() -> tuple[str, int]:
    """Get host and port from configuration or defaults."""
    if config and config.server and config.server.transport and config.server.transport.http:
        http_config = config.server.transport.http
        return http_config.host, http_config.port
    return "127.0.0.1", 8080


def main() -> None:
    """Run the main application."""
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run(transport="stdio")
    else:
        # Default to HTTP
        host, port = get_host_and_port()
        uvicorn.run(app, host=host, port=port)


def main_http() -> None:
    """Run the HTTP server."""
    host, port = get_host_and_port()
    uvicorn.run(app, host=host, port=port)  # pragma: no cover


def main_stdio() -> None:
    """Run the stdio transport."""
    mcp.run(transport="stdio")  # pragma: no cover


# For stdio transport
if __name__ == "__main__":  # pragma: no cover
    main()
