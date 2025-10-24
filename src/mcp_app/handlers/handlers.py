"""
Handlers module for OAuth endpoints.

This module implements the OAuth-related handlers for the MCP server,
corresponding to the Go handlers.
"""

import logging
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from mcp_app.config import Configuration

logger = logging.getLogger(__name__)


class HandlersManager:
    """Manager for OAuth handlers."""

    def __init__(self, config: Configuration) -> None:
        """Initialize the handlers manager."""
        self.config = config

    def _is_uri_allowed(self, uri: str) -> bool:
        """Check if URI domain is in OAuth whitelist."""
        if not self.config.oauth_whitelist_domains:
            return True  # Allow all if no whitelist
        parsed = urlparse(uri)
        domain = parsed.netloc
        return any(domain.endswith(allowed) for allowed in self.config.oauth_whitelist_domains)

    def _sanitize_openid_config(self, data: dict) -> dict:
        """Sanitize OpenID configuration response."""
        # Remove potentially sensitive fields like private keys, secrets, etc.
        sensitive_fields = {
            "private_key_jwt",
            "client_secret",
            "registration_access_token",
            "introspection_endpoint_auth_signing_alg_values_supported",
            # Add more as needed
        }
        sanitized = {}
        for key, value in data.items():
            if key not in sensitive_fields:
                sanitized[key] = value
            else:
                logger.warning("Removed sensitive field from OpenID config: %s", key)
        return sanitized

    async def handle_oauth_authorization_server(self) -> dict:
        """
        Handle requests for /.well-known/oauth-authorization-server endpoint.

        Proxies to the OpenID configuration from the issuer URI.
        """
        if (
            not self.config.oauth_authorization_server
            or not self.config.oauth_authorization_server.enabled
        ):
            raise HTTPException(status_code=404, detail="OAuth authorization server not enabled")

        issuer_uri = self.config.oauth_authorization_server.issuer_uri
        if not self._is_uri_allowed(issuer_uri):
            raise HTTPException(status_code=403, detail="Issuer URI not in allowed domains")

        remote_url = f"{issuer_uri}/.well-known/openid-configuration"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(remote_url)
                response.raise_for_status()
                data = response.json()
                # Sanitize response: remove potentially sensitive fields
                return self._sanitize_openid_config(data)
            except httpx.HTTPError as e:
                logger.exception("Error fetching OpenID config from %s", remote_url)
                raise HTTPException(status_code=500, detail="Error fetching OpenID config") from e

    async def handle_oauth_protected_resources(self) -> dict:
        """
        Handle requests for /.well-known/oauth-protected-resource endpoint.

        Returns the protected resource metadata according to RFC9728.
        """
        if (
            not self.config.oauth_protected_resource
            or not self.config.oauth_protected_resource.enabled
        ):
            raise HTTPException(status_code=404, detail="OAuth protected resource not enabled")

        pr = self.config.oauth_protected_resource

        # Validate URIs
        for auth_server in pr.auth_servers:
            if not self._is_uri_allowed(auth_server):
                raise HTTPException(
                    status_code=403, detail=f"Auth server URI not allowed: {auth_server}"
                )
        if not self._is_uri_allowed(pr.jwks_uri):
            raise HTTPException(status_code=403, detail="JWKS URI not allowed")

        response = {
            "resource": pr.resource,
            "authorization_servers": pr.auth_servers,
            "jwks_uri": pr.jwks_uri,
            "scopes_supported": pr.scopes_supported,
            "bearer_methods_supported": pr.bearer_methods_supported,
            "resource_signing_alg_values_supported": pr.resource_signing_alg_values_supported,
        }

        # Optional fields
        if pr.resource_name:
            response["resource_name"] = pr.resource_name
        if pr.resource_documentation:
            response["resource_documentation"] = pr.resource_documentation
        if pr.resource_policy_uri:
            response["resource_policy_uri"] = pr.resource_policy_uri
        if pr.resource_tos_uri:
            response["resource_tos_uri"] = pr.resource_tos_uri

        # Advanced security
        if pr.tls_client_certificate_bound_access_tokens:
            response["tls_client_certificate_bound_access_tokens"] = (
                pr.tls_client_certificate_bound_access_tokens
            )
        if pr.authorization_details_types_supported:
            response["authorization_details_types_supported"] = (
                pr.authorization_details_types_supported
            )
        if pr.dpop_signing_alg_values_supported:
            response["dpop_signing_alg_values_supported"] = pr.dpop_signing_alg_values_supported
        if pr.dpop_bound_access_tokens_required:
            response["dpop_bound_access_tokens_required"] = pr.dpop_bound_access_tokens_required

        return response
