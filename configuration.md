# Configuration

This document explains how to configure the MCP-Forge-Python server for different environments and use cases.

## Configuration File

The server uses a TOML configuration file (`config.toml`) with the following structure:

```toml
[server]
name = "MCP Forge Python"
version = "0.1.0"

[server.transport]
type = "http"

[server.transport.http]
host = "0.0.0.0"

[middleware.access_logs]
excluded_headers = ["authorization"]
redacted_headers = ["x-api-key"]

[middleware.cors]
allow_origins = ["*"]
allow_credentials = true
allow_methods = ["*"]
allow_headers = ["*"]

[middleware.jwt]
enabled = true

[middleware.jwt.validation]
strategy = "local"
forwarded_header = "X-Validated-Jwt"

[middleware.jwt.validation.local]
jwks_uri = "https://your-keycloak.example.com/realms/your-realm/protocol/openid-connect/certs"
cache_interval = 10
whitelist_domains = ["your-keycloak.example.com"]
issuer = "https://your.keycloak.example.com/"
audience = "your-client-id"

[[middleware.jwt.validation.local.allow_conditions]]
expression = 'has(payload.email) && payload.email.endswith("@yourdomain.com")'

jwt_exposed_claims = "all"

[oauth_authorization_server]
enabled = false
issuer_uri = "http://localhost:8080/auth/realms/master"

[oauth_protected_resource]
enabled = false
resource = "mcp-resource"
auth_servers = ["http://localhost:8080/auth/realms/master"]
jwks_uri = "http://localhost:8080/auth/realms/master/protocol/openid-connect/certs"
scopes_supported = ["openid", "profile", "email"]

oauth_whitelist_domains = ["localhost", "yourdomain.com"]

[auth]
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
redirect_uri = "http://localhost:8080/callback"
```

## Server Configuration

- `name`: Server name for MCP protocol
- `version`: Server version
- `transport.type`: Transport type ("http" or "stdio")
- `transport.http.host`: Bind address for HTTP transport (use "0.0.0.0" for external access)

## Middleware Configuration

### Access Logs

- `excluded_headers`: Headers to completely exclude from logs
- `redacted_headers`: Headers to redact (show as "[REDACTED]")

### CORS

- `allow_origins`: Allowed origins for CORS
- `allow_credentials`: Allow credentials in CORS
- `allow_methods`: Allowed HTTP methods
- `allow_headers`: Allowed headers

### JWT Validation

- `enabled`: Enable/disable JWT middleware
- `validation.strategy`: "local" (validate in server) or "external" (delegate to proxy)
- `validation.forwarded_header`: Header containing JWT for external strategy
- `validation.local.jwks_uri`: JWKS endpoint for public keys (local strategy)
- `validation.local.cache_interval`: Cache interval for JWKS in seconds
- `validation.local.whitelist_domains`: Allowed domains for JWKS URI
- `validation.local.issuer`: Expected JWT issuer
- `validation.local.audience`: Expected JWT audience
- `validation.local.allow_conditions`: List of CEL expressions for claim validation

### JWT Claims Exposure

- `jwt_exposed_claims`: Claims to expose in context ("all" or list of claim names)

## OAuth Configuration

The OAuth configuration implements RFC 8414 (OAuth 2.0 Authorization Server Metadata) and RFC 9728 (OAuth 2.0 Protected Resource Metadata).

### Authorization Server

- `enabled`: Enable/disable OAuth authorization server proxy
- `issuer_uri`: Base URI of the OAuth issuer

### Protected Resource

- `enabled`: Enable/disable protected resource metadata
- `resource`: Resource identifier
- `auth_servers`: List of authorization server URIs
- `jwks_uri`: JWKS endpoint URI
- `scopes_supported`: Supported OAuth scopes

### OAuth Whitelist Domains

- `oauth_whitelist_domains`: Allowed domains for OAuth URIs to prevent SSRF

## Auth Configuration

For OAuth authorization code flows:

- `client_id`: OAuth client ID
- `client_secret`: OAuth client secret
- `redirect_uri`: Redirect URI after authorization

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

## Additional Endpoints

The server provides these endpoints beyond MCP protocol:

- `GET /`: Returns server information
- `GET /health`: Health check
- `GET /login`: Initiates OAuth login flow
- `GET /callback`: Handles OAuth callback

## Security Notes

- Default host is `127.0.0.1` to prevent accidental exposure
- Always use HTTPS in production
- Configure appropriate CORS if needed
- Validate all configuration values in production
- Limit `jwt_exposed_claims` to prevent PII leakage
