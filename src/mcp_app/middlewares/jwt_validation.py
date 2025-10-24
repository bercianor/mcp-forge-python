"""
JWT validation middleware.

Supports local validation with JWKS and CEL expressions, or delegated to external systems.
"""

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

import jwt
import requests
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from mcp_app.context import set_jwt_context

logger = logging.getLogger(__name__)

# Constants
MAX_RATE_LIMIT_REQUESTS = 10
TOKEN_MASK_LENGTH = 10
ENDSWITH_PARTS_COUNT = 2


class JWKSCache:
    """JWKS cache with TTL."""

    def __init__(self, uri: str, cache_interval: int = 300) -> None:
        """Initialize the JWKS cache."""
        self.uri = uri
        self.cache_interval = cache_interval
        self.keys: dict[str, Any] = {}
        self.last_updated = 0

    def get_key(self, kid: str) -> dict[str, Any] | None:
        """Get key by kid, refreshing cache if needed."""
        now = time.time()
        if now - self.last_updated > self.cache_interval:
            self._refresh_keys()
        return self.keys.get(kid)

    def _refresh_keys(self) -> None:
        """Refresh JWKS from URI."""
        try:
            response = requests.get(self.uri, timeout=10)
            response.raise_for_status()
            jwks = response.json()
            self.keys = {key["kid"]: key for key in jwks.get("keys", []) if "kid" in key}
            self.last_updated = time.time()
            logger.info("Refreshed JWKS with %s keys", len(self.keys))
        except Exception:
            logger.exception("Failed to refresh JWKS")


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT validation."""

    def __init__(
        self,
        app: ASGIApp,  # noqa: ARG002
        strategy: str = "external",
        forwarded_header: str = "X-Validated-Jwt",
        jwks_uri: str | None = None,
        cache_interval: int = 300,
        allow_conditions: list[str] | None = None,
        whitelist_domains: list[str] | None = None,
    ) -> None:
        """Initialize the JWT validation middleware."""
        self.strategy = strategy
        self.forwarded_header = forwarded_header
        self.jwks: JWKSCache | None = None
        self.allow_conditions = allow_conditions or []
        self.whitelist_domains = whitelist_domains or []
        self.rate_limit: dict[str, int] = {}  # Simple rate limit by IP

        if strategy == "local" and jwks_uri:
            if not self._is_uri_allowed(jwks_uri):
                msg = f"JWKS URI {jwks_uri} not in whitelist"
                raise ValueError(msg)
            self.jwks = JWKSCache(jwks_uri, cache_interval)

    def _is_uri_allowed(self, uri: str) -> bool:
        """Check if URI domain is in whitelist."""
        if not self.whitelist_domains:
            return True  # Allow all if no whitelist
        parsed = urlparse(uri)
        domain = parsed.netloc
        return any(domain.endswith(allowed) for allowed in self.whitelist_domains)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and validate JWT if configured."""
        if self.strategy == "local":
            await self._validate_local(request)
        # For external strategy, assume JWT is already validated by upstream proxy

        return await call_next(request)

    async def _validate_local(self, request: Request) -> None:
        """Validate JWT locally."""
        # Simple rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if self.rate_limit.get(client_ip, 0) > MAX_RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        self.rate_limit[client_ip] = self.rate_limit.get(client_ip, 0) + 1

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header"
            )

        token = auth_header[7:]  # Remove "Bearer "

        # Decode header to get kid
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise HTTPException(  # noqa: TRY301
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT missing kid"
                )
        except Exception as e:
            detail = f"Invalid JWT header: {type(e).__name__}"
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail) from e

        # Get key from JWKS
        if not self.jwks:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="JWKS not configured"
            )

        key_data = self.jwks.get_key(kid)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Key not found in JWKS"
            )

        # Convert JWK to PEM
        try:
            jwk = jwt.PyJWK(key_data)
            public_key = jwk.key
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWK: {type(e).__name__}"
            ) from e

        # Verify and decode JWT
        try:
            payload = jwt.decode(
                token, public_key, algorithms=["RS256"], options={"verify_exp": True}
            )
        except jwt.ExpiredSignatureError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT expired"
            ) from err
        except jwt.InvalidTokenError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT"
            ) from err

        # Check allow conditions
        for condition in self.allow_conditions:
            if not self._check_condition(condition, payload):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT does not meet conditions"
                )

        # Set forwarded header (mask token for logging)
        masked_token = (
            token[:TOKEN_MASK_LENGTH] + "..." if len(token) > TOKEN_MASK_LENGTH else token
        )
        request.headers.__dict__["_list"].append(
            (self.forwarded_header.encode(), masked_token.encode())
        )

        # Set JWT in shared context for MCP tools
        set_jwt_context(token, payload)

    def _check_condition(self, condition: str, payload: dict[str, Any]) -> bool:
        """Check simple conditions safely without eval."""
        # Simple parser for common patterns: payload.field == value or payload_['field'] == value
        if " == " in condition:
            field, value = condition.split(" == ", 1)
            field = field.strip()
            value = value.strip().strip('"').strip("'")
            if field.startswith("payload."):
                key = field[8:]  # Remove "payload."
                return payload.get(key) == value
            if field.startswith("payload_['") and field.endswith("']"):
                key = field[10:-2]  # Remove "payload_['" and "']"
                return payload.get(key) == value
        elif ".endswith(" in condition and condition.endswith(")"):
            parts = condition.split(".endswith(", 1)
            if len(parts) == ENDSWITH_PARTS_COUNT and parts[0].startswith("payload."):
                key = parts[0][8:]
                suffix = parts[1].rstrip(")").strip('"').strip("'")
                field_value = payload.get(key)
                return isinstance(field_value, str) and field_value.endswith(suffix)
        # Add more patterns as needed
        logger.warning("Unsupported condition: %s", condition)
        return False
