"""
FastAPI application setup for the MCP-Forge-Python service.

This module handles FastAPI app configuration, middlewares, and endpoints.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from mcp.server import FastMCP

from mcp_app.config import Configuration
from mcp_app.context import set_exposed_claims
from mcp_app.handlers.handlers import HandlersManager
from mcp_app.middlewares.access_logs import AccessLogsMiddleware
from mcp_app.middlewares.jwt_validation import JWTValidationMiddleware

logger = logging.getLogger(__name__)

# HTTP status constants
HTTP_OK = 200


class FastAPIApp:
    """Handles FastAPI application setup and configuration."""

    def __init__(self, config: Configuration | None, mcp: FastMCP) -> None:
        """Initialize FastAPI app with config and MCP server."""
        self.config = config
        self.mcp = mcp
        self.app = self._create_app()
        self.handlers_manager = HandlersManager(config) if config else None

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title="MCP-Forge-Python",
            description="A Python port of the MCP Forge Go project.",
            lifespan=self._lifespan,
            redirect_slashes=False,
        )

        # Add CORS middleware
        self._add_cors_middleware(app)

        # Add other middlewares
        self._add_middlewares(app)

        # Add endpoints
        self._add_endpoints(app)

        # Mount MCP servers
        sse_app = self.mcp.sse_app()
        sse_app.router.redirect_slashes = False
        app.mount("/", sse_app)  # SSE transport

        return app

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
        """Application lifespan context manager."""
        _ = app  # Required by FastAPI lifespan signature
        # Set JWT exposed claims configuration if config is loaded
        if self.config:
            set_exposed_claims(self.config.jwt_exposed_claims)

        yield

        logger.info("Application shutting down.")

    def _add_cors_middleware(self, app: FastAPI) -> None:
        """Add CORS middleware to the app."""
        cors_config = (
            self.config.middleware.cors
            if self.config and self.config.middleware and self.config.middleware.cors
            else None
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

    def _add_middlewares(self, app: FastAPI) -> None:
        """Add custom middlewares to the app."""
        if self.config and self.config.middleware:  # pragma: no cover
            if self.config.middleware.access_logs:
                app.add_middleware(
                    AccessLogsMiddleware,
                    excluded_headers=self.config.middleware.access_logs.excluded_headers,
                    redacted_headers=self.config.middleware.access_logs.redacted_headers,
                )

            if self.config.middleware.jwt and self.config.middleware.jwt.enabled:
                jwt_config = self.config.middleware.jwt
                validation = jwt_config.validation
                local_config = validation.local if validation else None

                app.add_middleware(
                    JWTValidationMiddleware,
                    strategy=validation.strategy if validation else "external",
                    forwarded_header=(
                        validation.forwarded_header
                        if validation and validation.forwarded_header
                        else "X-Validated-Jwt"
                    ),
                    jwks_uri=local_config.jwks_uri if local_config else None,
                    cache_interval=(
                        int(local_config.cache_interval.total_seconds()) if local_config else 300
                    ),
                    allow_conditions=[
                        c.expression
                        for c in (local_config.allow_conditions if local_config else [])
                    ],
                    issuer=local_config.issuer if local_config else None,
                    audience=local_config.audience if local_config else None,
                )

    def _add_endpoints(self, app: FastAPI) -> None:
        """Add API endpoints to the app."""
        app.get("/.well-known/oauth-authorization-server")(self._oauth_authorization_server)
        app.get("/.well-known/oauth-protected-resource")(self._oauth_protected_resource)
        app.get("/")(self._read_root)
        app.get("/login")(self._login)
        app.get("/callback")(self._callback)
        app.get("/health")(self._health_check)

    async def _oauth_authorization_server(self) -> dict[str, Any]:
        """Handle OAuth authorization server metadata endpoint."""
        if not self.handlers_manager:  # pragma: no cover
            return {"error": "Configuration not loaded"}  # pragma: no cover
        return await self.handlers_manager.handle_oauth_authorization_server()  # pragma: no cover

    async def _oauth_protected_resource(self) -> dict[str, Any]:
        """Handle OAuth protected resource metadata endpoint."""
        if not self.handlers_manager:  # pragma: no cover
            return {"error": "Configuration not loaded"}  # pragma: no cover
        return await self.handlers_manager.handle_oauth_protected_resources()  # pragma: no cover

    async def _read_root(self) -> dict[str, str]:
        """Root endpoint returning server information."""
        server_name = (
            self.config.server.name if self.config and self.config.server else "Unknown"
        )  # pragma: no cover
        return {"message": f"Hello from {server_name}"}  # pragma: no cover

    async def _login(self) -> Response:
        """Redirect to Auth0 login."""
        if (
            not self.config
            or not self.config.auth
            or not self.config.middleware
            or not self.config.middleware.jwt
            or not self.config.middleware.jwt.validation
            or not self.config.middleware.jwt.validation.local
        ):
            return JSONResponse(status_code=400, content={"error": "Config incomplete"})
        local_config = self.config.middleware.jwt.validation.local
        auth_url = (
            f"{local_config.issuer}authorize?"
            f"client_id={self.config.auth.client_id}&"
            "response_type=code&"
            f"redirect_uri={self.config.auth.redirect_uri}&"
            "scope=openid profile email&"
            f"audience={local_config.audience}"
        )
        return RedirectResponse(auth_url)

    async def _callback(self, code: str) -> dict[str, Any]:
        """Exchange code for token."""
        if (
            not self.config
            or not self.config.auth
            or not self.config.middleware
            or not self.config.middleware.jwt
            or not self.config.middleware.jwt.validation
            or not self.config.middleware.jwt.validation.local
        ):
            return {"error": "Config incomplete"}
        local_config = self.config.middleware.jwt.validation.local
        token_url = f"{local_config.issuer}oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.auth.client_id,
            "client_secret": self.config.auth.client_secret,
            "code": code,
            "redirect_uri": self.config.auth.redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, timeout=10.0)
        if response.status_code == HTTP_OK:
            token_data = response.json()
            return {"access_token": token_data.get("access_token")}
        return {"error": "Failed to get token", "details": response.text}

    async def _health_check(self) -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}  # pragma: no cover
