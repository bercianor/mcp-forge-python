# Development Guide

This guide explains how to use this MCP-Forge-Python project as a template for developing your own MCP servers.

## Using This Template

This project serves as a production-ready template for building MCP (Model Context Protocol) servers with OAuth support. The current tools are demo examples - replace them with your own functionality.

### Quick Start

1. **Fork or clone this repository**
2. **Configure placeholders** (see below)
3. **Replace demo tools** with your own
4. **Customize configuration** for your needs

### Project Structure Overview

```
src/mcp_app/
├── main.py          # FastAPI app, MCP server setup, middlewares
├── config.py        # Pydantic configuration models
├── handlers/        # OAuth endpoint handlers
├── middlewares/     # JWT validation, access logs
└── tools/router.py  # MCP tools registration

tests/               # Comprehensive test suite
chart/               # Kubernetes deployment
config.toml          # Configuration example
```

## Replacing Demo Tools

The current tools (`hello_world`, `whoami`) are examples. Here's how to replace them:

### 1. Create Your Tools

Create `src/mcp_app/tools/my_tools.py`:

```python
def my_business_logic_tool(param1: str, param2: int) -> dict:
    """Execute your business logic.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2

    Returns:
        Dictionary with results
    """
    # Your tool implementation here
    result = {
        "status": "success",
        "data": f"Processed {param1} with {param2}"
    }
    return result
```

#### Register Your Tools

Edit `src/mcp_app/tools/router.py`:

```python
from mcp.server import FastMCP

# Remove demo imports
# from mcp_app.tools.hello_world import hello_world
# from mcp_app.tools.whoami import whoami

# Add your tools
from my_app.tools.my_tools import my_business_logic_tool

def register_tools(mcp: FastMCP) -> None:
    """Register MCP tools with the server."""

    # Remove demo tools
    # mcp.tool()(hello_world)
    # mcp.tool()(whoami)

    # Register your tools
    mcp.tool()(my_business_logic_tool)
```

### 3. Update Tests

Modify `tests/test_tools.py` to test your new tools instead of the demo ones.

### 4. Update Documentation

Update README.md and DEVELOPMENT.md to document your tools instead of the demo ones.

## JWT Validation Configuration

The project includes JWT validation middleware for securing tools. By default, it's configured for local validation using a JWKS endpoint.

### Using Keycloak

To enable JWT validation with Keycloak:

1. **Run Keycloak locally** (e.g., via Docker: `docker run -p 8080:8080 quay.io/keycloak/keycloak:latest start-dev`).
2. **Create a realm and client** in Keycloak admin console.
3. **Update `config.toml`**:
   - Set `jwks_uri = "http://localhost:8080/realms/your-realm/protocol/openid-connect/certs"`
   - Adjust `allow_conditions` to match your email domain, e.g., `payload.email.endswith("@yourdomain.com")`
4. **Enable OAuth endpoints** if needed by setting `oauth_authorization_server.enabled = true` and `oauth_protected_resource.enabled = true`, updating issuer_uri and auth_servers accordingly.

### Using Auth0

To use Auth0 as your identity provider:

1. **Get your Auth0 tenant details** (tenant name, client ID, etc.).
2. **Update `config.toml`**:
   - Set `jwks_uri = "https://your-tenant.auth0.com/.well-known/jwks.json"`
   - Set `allow_conditions` to validate claims, e.g., `payload.iss == "https://your-tenant.auth0.com/" and payload.aud == "your-client-id"`
3. **Ensure Auth0 is configured** to issue JWTs with the required claims.

For external validation (e.g., via a proxy), set `strategy = "external"` and configure your proxy to forward validated JWTs in the `X-Validated-Jwt` header.

### Configuring Exposed JWT Claims

As a template, this project allows configuring which JWT claims are exposed to MCP tools via the `context` module. This is crucial for security, as JWT payloads may contain sensitive information (PII) that should not be accessible to tools.

- **Default**: `jwt_exposed_claims = "all"` - Exposes all claims in the JWT payload.
- **Secure Option**: `jwt_exposed_claims = ["user_id", "roles"]` - Only exposes specific claims.

**Important**: The `permissions` claim is always included automatically for authorization purposes, regardless of the `jwt_exposed_claims` configuration. Review your JWT structure and set `jwt_exposed_claims` to only the claims your tools need. Avoid exposing sensitive data like emails, personal info, or internal IDs unless necessary. Update this in `config.toml` and test that tools receive only expected data.

Example in `config.toml`:
```toml
jwt_exposed_claims = ["user_id", "roles"]
```
Note: `permissions` is always included automatically for authorization.

### Permissions for Tool Authorization

This project implements a basic permission-based access control system using OAuth permissions to restrict tool execution. Permissions are issued by the identity provider (e.g., Keycloak, Auth0, or other OAuth providers) and validated in tools at runtime.

#### Defining Your Own Permissions

You can define custom permissions based on your application's needs. Permissions control access to specific tools or features.

**Example Permissions** (define in your OAuth provider's API/client configuration):
- `tool:read`: Access to read-only tools.
- `tool:write`: Access to tools that modify data.
- `tool:admin`: Administrative access to sensitive tools.

Permissions are included in JWT claims as a `permissions` array via your OAuth provider's rules/actions/policies. Configure your provider to include the appropriate permissions in tokens based on user roles.

#### Checking Permissions in Tools

To restrict a tool based on permissions, add authorization checks inside the tool function. Use `get_jwt_payload()` from `mcp_app.context` to access claims. Note that `permissions` is always included in the filtered payload for authorization purposes.

Example for a tool requiring `tool:user` permission:

```python
from mcp_app.context import get_jwt_payload

def my_tool(param: str) -> str:
    """My tool description. Requires tool:user permission.

    Args:
        param: Parameter description.

    Returns:
        Result description.

    Raises:
        PermissionError: If user lacks required permission.
    """
    payload = get_jwt_payload()
    if payload:  # Only check in HTTP mode (with JWT)
        permissions = payload.get("permissions", [])
        if "tool:user" not in permissions:
            raise PermissionError("Insufficient permissions: tool:user permission required")

    # Tool logic here
    return f"Processed: {param}"
```

- **In HTTP mode**: Validates permissions from JWT; raises `PermissionError` if unauthorized.
- **In stdio mode**: Allows execution without checks (for development).
- **Always include permission checks** for sensitive tools to prevent unauthorized access.

Configure your OAuth provider to issue tokens with the appropriate permissions based on user roles.

## Configuration Placeholders

Before using this template, you must replace all placeholders with your actual values:

### Files to Modify

1. **`pyproject.toml`**:
   - Change `YOUR_NAME` and `your.email@example.com` to your real name and email

2. **`chart/values.yaml`**:
   - Change `ghcr.io/YOUR_USERNAME/YOUR_REPO` to your real container repository
   - Update all example URLs (`your-keycloak.example.com`, `your-mcp-domain.example.com`) according to your infrastructure

3. **`config.toml`**:
    - Configure Keycloak URLs, JWKS, etc. for your specific environment
    - Change `your-keycloak.example.com` and `yourdomain.com` to your real values
    - Set environment variables for secrets: `MCP_CLIENT_ID` and `MCP_CLIENT_SECRET`

4. **README files**:
   - Replace `bercianor/mcp-forge-python` in badges with your actual GitHub username/repo

5. **`.github/CODEOWNERS`**:
   - Change `@YOUR_USERNAME` to your GitHub username

6. **`.github/dependabot.yml`**:
   - Change `YOUR_USERNAME` to your GitHub username

### All Placeholders Found

- `YOUR_NAME` (pyproject.toml)
- `your.email@example.com` (pyproject.toml)
- `ghcr.io/YOUR_USERNAME/YOUR_REPO` (chart/values.yaml)
- `your-keycloak.example.com` (config.toml, chart/values.yaml)
- `your-mcp-domain.example.com` (chart/values.yaml)
- `yourdomain.com` (config.toml)
- `your-realm` (config.toml, chart/values.yaml)
- `PLACEHOLDER` (chart/values.yaml - secret key)
- `your-kv/applications/mcp-forge-python/credentials` (chart/values.yaml - Vault path)
- `@YOUR_USERNAME` (.github/CODEOWNERS)
- `YOUR_USERNAME` (.github/dependabot.yml)
- `YOUR_CLIENT_ID` (config.toml)
- `YOUR_CLIENT_SECRET` (config.toml)

### Example URLs to Replace

- `your-keycloak.example.com` → Your real Keycloak server
- `your-mcp-domain.example.com` → Your real domain
- `@yourdomain.com` → Your email domain

## Customization Options

### Adding New Middlewares

Add custom middlewares in `src/mcp_app/middlewares/` and register them in `main.py`.

### Modifying OAuth Configuration

The OAuth implementation follows RFC 8414 and RFC 9728. Modify handlers in `src/mcp_app/handlers/` if needed.

### Database Integration

Add database connections, ORMs, or other data sources as needed for your tools.

### Environment-Specific Configs

Create multiple `config.*.toml` files for different environments (dev, staging, prod).

## Deployment

### Docker

```bash
# Build image
docker build -t your-mcp-server .

# Run container
docker run -p 8080:8080 -v $(pwd)/config.toml:/data/config.toml your-mcp-server
```

### Kubernetes

Use the provided Helm chart in `chart/` directory. Update `chart/values.yaml` with your configuration.

### Local Development

```bash
# Install dependencies
uv sync

# Run in development mode
uv run http  # or uv run stdio
```

## Testing Your Changes

```bash
# Run all tests
just test

# Run with coverage
just cov

# Run all quality checks
just check-all
```

## Next Steps

1. Replace demo tools with your business logic
2. Configure OAuth providers (Keycloak, Auth0, etc.)
3. Set up your deployment infrastructure
4. Add comprehensive tests for your tools
5. Update documentation for your specific use case

For more information, see [Contributing](CONTRIBUTING.md) for contribution guidelines.
