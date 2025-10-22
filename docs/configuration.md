# Configuration

This document explains how to configure the MCP-Forge-Python server for different environments and use cases.

## Configuration File

The server uses a TOML configuration file (`config.toml`) with the following structure:

```toml
[server]
name = "mcp-forge-python"
version = "0.1.0"
host = "127.0.0.1"
port = 8080
transport = "http"  # or "stdio"

[middleware.access_log]
enabled = true
exclude_headers = ["authorization", "cookie"]
redact_headers = ["x-forwarded-user"]

[middleware.jwt]
strategy = "local"  # or "external"
jwks_uri = "https://your-keycloak.example.com/realms/your-realm/protocol/openid-connect/certs"
cel_condition = "claims.sub != null"
forwarded_header = "x-forwarded-user"

[oauth.authorization_server]
issuer = "https://your-keycloak.example.com/realms/your-realm"
authorization_endpoint = "https://your-keycloak.example.com/realms/your-realm/protocol/openid-connect/auth"
token_endpoint = "https://your-keycloak.example.com/realms/your-realm/protocol/openid-connect/token"
jwks_uri = "https://your-keycloak.example.com/realms/your-realm/protocol/openid-connect/certs"

[oauth.protected_resource]
audience = "mcp-forge-python"
scopes_supported = ["read", "write"]
```

## Server Configuration

- `name`: Server name for MCP protocol
- `version`: Server version
- `host`: Bind address (use "0.0.0.0" for external access)
- `port`: Port to listen on
- `transport`: "http" for HTTP+SSE or "stdio" for standard I/O

## Middleware Configuration

### Access Logs

- `enabled`: Enable/disable access logging
- `exclude_headers`: Headers to completely exclude from logs
- `redact_headers`: Headers to redact (show as "[REDACTED]")

### JWT Validation

- `strategy`: "local" (validate in server) or "external" (delegate to proxy)
- `jwks_uri`: JWKS endpoint for public keys (local strategy)
- `cel_condition`: CEL expression for claim validation
- `forwarded_header`: Header containing JWT for external strategy

## OAuth Configuration

The OAuth configuration implements RFC 8414 (OAuth 2.0 Authorization Server Metadata) and RFC 9728 (OAuth 2.0 Protected Resource Metadata).

### Authorization Server

Metadata about the OAuth provider (Keycloak, Auth0, etc.).

### Protected Resource

Metadata about this MCP server as a protected resource.

## Environment-Specific Configuration

Create multiple configuration files for different environments:

- `config.dev.toml` - Development settings
- `config.staging.toml` - Staging environment
- `config.prod.toml` - Production settings

Load them by setting the `CONFIG_FILE` environment variable:

```bash
export CONFIG_FILE=config.prod.toml
uv run http
```

## Security Notes

- Default host is `127.0.0.1` to prevent accidental exposure
- Always use HTTPS in production
- Configure appropriate CORS if needed
- Validate all configuration values in production
