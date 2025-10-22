"""
JWT validation middleware.

Supports local validation with JWKS and CEL expressions, or delegated to external systems.
"""

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

import jwt
import requests
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


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
    ) -> None:
        """Initialize the JWT validation middleware."""
        self.strategy = strategy
        self.forwarded_header = forwarded_header
        self.jwks: JWKSCache | None = None
        self.allow_conditions = allow_conditions or []

        if strategy == "local" and jwks_uri:
            self.jwks = JWKSCache(jwks_uri, cache_interval)

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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT header: {e}"
            ) from e

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
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWK: {e}"
            ) from e

        # Verify and decode JWT
        try:
            payload = jwt.decode(
                token, public_key, algorithms=["RS256"], options={"verify_exp": True}
            )
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT expired"
            ) from e
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT: {e}"
            ) from e

        # Check allow conditions
        for condition in self.allow_conditions:
            if not self._check_condition(condition, payload):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT does not meet conditions"
                )

        # Set forwarded header
        request.headers.__dict__["_list"].append((self.forwarded_header.encode(), token.encode()))

    def _check_condition(self, condition: str, payload: dict[str, Any]) -> bool:
        """Check simple CEL-like conditions."""
        # Basic implementation for common patterns
        try:
            # Replace payload. with payload access
            condition = condition.replace("payload.", "payload_")
            # Simple eval with restricted environment
            allowed_names = {
                "payload": payload,
                "payload_": payload,
                "has": lambda x: x is not None,
                "len": len,
                "str": str,
                "int": int,
                "bool": bool,
            }
            # Add list/dict methods
            allowed_names.update(
                {
                    "exists": lambda iterable, condition: (
                        any(condition(item) for item in iterable)
                        if hasattr(iterable, "__iter__")
                        else False
                    ),
                    "all": all,
                    "any": any,
                }
            )
            return eval(condition, {"__builtins__": {}}, allowed_names)  # noqa: S307
        except Exception:
            logger.exception("Condition evaluation error for '%s'", condition)
            return False
