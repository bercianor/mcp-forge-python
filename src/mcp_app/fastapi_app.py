"""
FastAPI application setup for the MCP-Forge-Python service.

This module handles FastAPI app configuration, middlewares, and endpoints.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
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
        http_app = self.mcp.streamable_http_app()
        http_app.router.redirect_slashes = False
        app.mount("/mcp", http_app)  # Streamable HTTP transport

        return app

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
        """Application lifespan context manager."""
        _ = app  # Required by FastAPI lifespan signature
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(self.mcp.session_manager.run())
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
        app.get("/callback", response_model=None)(self._callback)
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

    async def _login(self, request: Request) -> Response:
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
            f"redirect_uri={request.base_url}callback&"
            "scope=openid profile email&"
            f"audience={local_config.audience}"
        )
        return RedirectResponse(auth_url)

    async def _callback(
        self,
        request: Request,
        code: str | None = None,
        error: str | None = None,
        error_description: str | None = None,
    ) -> Response:
        """Exchange code for token or handle OAuth errors."""
        if error:
            return JSONResponse(
                {"error": error, "description": error_description or "Unknown OAuth error"}
            )

        if not code:
            return JSONResponse({"error": "Missing authorization code"})

        if (
            not self.config
            or not self.config.auth
            or not self.config.middleware
            or not self.config.middleware.jwt
            or not self.config.middleware.jwt.validation
            or not self.config.middleware.jwt.validation.local
        ):
            return JSONResponse({"error": "Config incomplete"})

        local_config = self.config.middleware.jwt.validation.local
        token_url = f"{local_config.issuer}oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.auth.client_id,
            "client_secret": self.config.auth.client_secret,
            "code": code,
            "redirect_uri": f"{request.base_url}callback",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, timeout=10.0)
        if response.status_code == HTTP_OK:
            token_data = response.json()
            jwt = token_data.get("access_token")
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>JWT Token</title>
    <style>
        body {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
        }}
        h1 {{
            font-size: 2em;
            margin-bottom: 20px;
            color: #333;
        }}
        input {{
            font-size: 1.2em;
            padding: 10px;
            width: 80%;
            max-width: 600px;
            text-align: center;
            border: 2px solid #ccc;
            border-radius: 5px;
            cursor: pointer;
        }}
        p {{
            font-size: 1em;
            color: #666;
            margin-top: 20px;
        }}
        #notification {{
            display: none;
            margin-top: 20px;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            font-size: 1em;
        }}
    </style>
</head>
<body>
    <h1>Tu Token JWT</h1>
    <input type="password" value="{jwt}" onclick="copyToClipboard(this.value)" readonly>
    <p>Haz clic en el cuadro de texto para copiar el token al portapapeles</p>
    <div id="notification">¡Token copiado al portapapeles!</div>
    <script>
        function copyToClipboard(text) {{
            navigator.clipboard.writeText(text).then(function() {{
                showNotification();
            }}, function(err) {{
                console.error('No se pudo copiar el texto: ', err);
                alert('Error al copiar el token.');
            }});
        }}
        function showNotification() {{
            const notification = document.getElementById('notification');
            notification.style.display = 'block';
            setTimeout(function() {{
                notification.style.display = 'none';
            }}, 3000);
        }}
    </script>
</body>
</html>
"""
            return HTMLResponse(content=html_content)
        return JSONResponse({"error": "Failed to get token", "details": response.text})

    async def _health_check(self) -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}  # pragma: no cover
