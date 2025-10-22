"""
Handlers module for OAuth endpoints.

This module implements the OAuth-related handlers for the MCP server,
corresponding to the Go handlers.
"""

import httpx
from fastapi import HTTPException

from mcp_app.config import Configuration


class HandlersManager:
    """Manager for OAuth handlers."""

    def __init__(self, config: Configuration) -> None:
        """Initialize the handlers manager."""
        self.config = config

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

        remote_url = (
            f"{self.config.oauth_authorization_server.issuer_uri}/.well-known/openid-configuration"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(remote_url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=500, detail=f"Error fetching OpenID config: {e!s}"
                ) from e

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
