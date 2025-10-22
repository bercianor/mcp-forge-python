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

### 1. Modify Tools

Edit `src/mcp_app/tools/router.py`:

```python
from mcp import Tool
from mcp.server import Server

# Remove demo imports
# from mcp_app.tools.hello_world import hello_world_tool
# from mcp_app.tools.whoami import whoami_tool

# Add your tools
from my_app.tools.my_tool import my_tool_function

def register_tools(server: Server) -> None:
    """Register MCP tools with the server."""

    # Remove demo tools
    # server.register_tool(hello_world_tool)
    # server.register_tool(whoami_tool)

    # Register your tools
    server.register_tool(my_tool_function)
```

### 2. Create Your Tools

Create `src/mcp_app/tools/my_tools.py`:

```python
from mcp import Tool
from mcp.server import Server
from mcp_app.config import Configuration

# Get config if needed
config = None  # Will be set during app startup

@server.tool()
async def my_business_logic_tool(param1: str, param2: int) -> dict:
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

### 3. Update Tests

Modify `tests/test_tools.py` to test your new tools instead of the demo ones.

### 4. Update Documentation

Update README.md and DEVELOPMENT.md to document your tools instead of the demo ones.

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
