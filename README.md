# MCP Forge Python - Production-Ready MCP Server Template

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Unlicense-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com)
[![CI](https://img.shields.io/github/actions/workflow/status/bercianor/mcp-forge-python/ci.yml)](https://github.com/bercianor/mcp-forge-python/actions)
[![Coverage](https://bercianor.es/mcp-forge-python/badges/coverage-badge.svg)](https://github.com/bercianor/mcp-forge-python/actions)
[![Template](https://img.shields.io/badge/template-MCP%20Forge%20Python-blue)](https://github.com/bercianor/mcp-forge-python)
[![Contributors](https://img.shields.io/github/contributors/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python)

A comprehensive, production-ready MCP (Model Context Protocol) server template built with Python. This is a Python port of the original MCP Forge Go project, featuring OAuth 2.0 authentication, JWT validation, and seamless deployment options for developers building AI-powered applications.

## Key Features of MCP Forge Python

## MCP Protocol Implementation

- Built with the `mcp[cli]` Python library for full MCP protocol support
- Comprehensive tools, resources, and prompts implementation
- Configurable server initialization with name and version

## Communication Transports

- **Stdio Transport**: Standard input/output communication for local AI clients like Claude Desktop
- **HTTP with SSE**: Server-Sent Events for real-time web-based communication

## Built-in MCP Tools

The server includes several MCP tools registered via the router:

- **hello_world**: Personalized greeting functionality (requires `tool:user` scope in HTTP mode)
- **whoami**: JWT-based user information exposure from the JWT payload

## Security & Middleware

- **Access Logging**: Configurable request logging with header redaction
- **JWT Validation**: Dual strategies for token authentication
  - Local validation using JWKS URI and CEL expressions
  - External proxy delegation (Istio-compatible)
- **CORS**: Configurable Cross-Origin Resource Sharing
- **JWT Context**: Secure sharing of JWT claims between middlewares and MCP tools

## OAuth 2.0 Integration (RFC 8414 & RFC 9728)

- **OAuth Authorization Server**: OpenID Connect configuration proxy
- **Protected Resource Metadata**: Complete OAuth resource discovery endpoints
- **OAuth Flows**: Built-in login and callback endpoints for authorization code flow

## Flexible Configuration

- TOML-based configuration system with dedicated sections for:
  - Server settings (name, version, transport)
  - Middleware configuration (logging, JWT, CORS)
  - OAuth integration (authorization servers, protected resources)
  - Auth settings for OAuth flows (client credentials, redirect URIs)
  - JWT claims exposure configuration

## Additional Endpoints

Beyond MCP protocol endpoints, the server provides:

- **GET /**: Server information
- **GET /health**: Health check endpoint
- **GET /login**: Initiates OAuth authorization code flow (redirects to Auth0/Keycloak)
- **GET /callback**: Handles OAuth callback and exchanges code for token

## Production-Ready Deployment

- Complete Docker containerization with Dockerfile
- Kubernetes Helm chart for cloud deployment
- Integration guides for Keycloak, Istio, and Hashrouter

## System Requirements

### External Dependencies

- **Python**: >= 3.11
- **uv**: Dependency and virtual environment manager (install from [astral.sh/uv](https://astral.sh/uv))
- **just** (optional): Simplified command runner (install from [just.systems](https://just.systems/install.sh))
- **Docker** (optional): For image building

#### Requirements by JWT Strategy

- **"local" strategy**: Requires a **JWKS server** (OAuth provider like Keycloak, Auth0) that provides JWKS endpoint to obtain public keys and validate tokens. Configure in `jwks_uri`.
- **"external" strategy**: Requires an **upstream proxy** (like Istio, Envoy or API gateway) that validates JWTs and forwards claims in headers. Does not need JWKS in MCP, but the proxy must be configured to inject headers (e.g. `X-Forwarded-User`).

### Local Requirements

- **Production dependencies**:
  - `fastapi`: ASGI web framework
  - `uvicorn[standard]`: ASGI server with SSE support
  - `pydantic`: Data validation
  - `pydantic-settings`: Configuration from files
  - `tomli`: TOML parser for Python < 3.11
  - `mcp[cli]`: MCP Python SDK
  - `httpx`: Asynchronous HTTP client
  - `PyJWT`: JWT handling
  - `requests`: Synchronous HTTP client
  - `cryptography`: Cryptographic operations

- **Development dependencies**:
  - `ruff`: Linting and formatting
  - `pyright`: Type checking
  - `pytest`: Testing framework
  - `pytest-asyncio`: Async support for pytest
  - `coverage`: Code coverage
  - `pytest-benchmark`: Performance benchmarking

## Installation & Setup

```bash
# Install dependencies
uv sync

# Install package (enables direct commands)
uv pip install -e .

# Run HTTP server with SSE
uv run http

# Alternative: Run stdio server for local AI clients
uv run stdio
```

## Development Commands

```bash
# Testing & Quality
just test                    # Run all tests
just cov                     # Run tests with coverage report
just bench                   # Run benchmarks
just lint                    # Lint and format code
just typing                  # Type checking
just check-all              # Run all quality checks

# Lifecycle
just install                # Install/update dependencies
just update                 # Update dependencies to latest versions
just clean                  # Remove all temporary files (.venv, caches, dist)
just clean-cache            # Clean caches only (keep .venv)
just fresh                  # Clean + fresh install

# Running
just run                    # Run HTTP server
just run-stdio              # Run stdio mode
just dev-http               # Run HTTP server with MCP Inspector
just dev-stdio              # Run stdio server with MCP Inspector
```

> **Note**: For development, use `uv pip install -e .` for editable installation.

### Supported Transports

- **HTTP + SSE**: For remote clients like Claude Web. Endpoint `/mcp` with SSE. Run with `uv run http`.
- **Stdio**: For local clients like Claude Desktop. Run with `uv run stdio`.

## JWT Configuration

The JWT middleware supports two validation strategies:

### "local" Strategy

- Validates JWTs directly in the MCP server.
- Downloads public keys from a JWKS endpoint (configured in `jwks_uri`).
- Supports configurable cache and CEL conditions for advanced permissions.
- MCP tools check for required scopes (e.g., `tool:user` for hello_world).
- **Requirement**: OAuth server with JWKS endpoint (e.g. Keycloak).

### "external" Strategy

- Delegates validation to an upstream proxy (Istio, Envoy, etc.).
- The JWT is forwarded in a specific header (`forwarded_header`).
- The proxy validates and extracts claims, injecting them into the request.
- **Requirement**: Proxy configured for JWT validation and header forwarding.

Example in `config.toml`.

## Configuration

See `config.toml` for configuration example.

### Auth Configuration

For OAuth flows, configure the auth section:

```toml
[auth]
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8080/callback"
```

### CORS Configuration

Configure Cross-Origin Resource Sharing:

```toml
[middleware.cors]
allow_origins = ["https://yourdomain.com", "http://localhost:3000"]
allow_credentials = true
allow_methods = ["GET", "POST", "PUT", "DELETE"]
allow_headers = ["*"]
```

### JWT Claims Exposure

Control which JWT claims are accessible to MCP tools:

```toml
# Expose all claims (not recommended for production)
jwt_exposed_claims = "all"

# Or expose only specific claims
jwt_exposed_claims = ["user_id", "email", "roles"]
```

Note: `roles` and `scope` claims are always exposed for authorization purposes.

**Security Note**: By default, the server runs on `127.0.0.1` to avoid unwanted exposures. Configure the host and port in `config.toml` under `[server.transport.http]`. Change to `0.0.0.0` only if necessary and with appropriate security measures.

## Security Considerations

This template implements several security measures to protect against common vulnerabilities. As a template, it's designed to be configurable for different deployment scenarios.

### JWT Claims Exposure

To minimize data exposure, configure which JWT claims are accessible to MCP tools:

```toml
jwt_exposed_claims = ["user_id", "roles"]  # Only expose specific claims
# or
jwt_exposed_claims = "all"  # Expose all claims (not recommended for production)
```

Note: `roles` and `scope` claims are always exposed for authorization purposes, regardless of this configuration.

### Access Logging

Sensitive headers are automatically redacted in logs:

```toml
[logging]
redacted_headers = ["Authorization", "X-API-Key", "Cookie"]
max_body_size = 1024  # Limit logged body size
```

### Rate Limiting

Basic rate limiting is implemented for JWT validation to prevent brute force attacks.

### URI Validation

OAuth and JWKS URIs are validated against whitelisted domains to prevent SSRF attacks.

### Secure Dependencies

Dependencies are regularly updated to address known vulnerabilities. Run `uv lock --upgrade` to update to latest secure versions.

### Production Checklist

- Use "external" JWT strategy with a proper proxy (Istio, Envoy)
- Configure minimal exposed claims
- Enable access logging with redaction
- Validate all URIs against trusted domains
- Keep dependencies updated
- Run security tests regularly

## Documentation

- [Full Documentation](docs/index.md) - Complete guide including development, configuration, and contributing.
- [Development Guide](DEVELOPMENT.md) - How to use this as a template.
- [Contributing](CONTRIBUTING.md) - Guidelines for contributors.

## Project Architecture

```
src/mcp_app/
├── main.py          # Application entry point and FastAPI setup
├── config.py        # Pydantic configuration models
├── context.py       # JWT context management for secure claim sharing
├── handlers/        # OAuth endpoints handlers (RFC 8414 & RFC 9728)
├── middlewares/     # Custom middlewares (JWT, access logs, CORS)
└── tools/           # MCP tools and registration router
```

### Core Components

- **main.py**: Initializes FastMCP server, FastAPI app, middlewares, and OAuth endpoints
- **config.py**: TOML-based configuration with Pydantic models
- **context.py**: Async-safe JWT context sharing between middlewares and tools
- **handlers/**: OAuth authorization server and protected resource metadata endpoints
- **middlewares/**: JWT validation, access logging, and CORS handling
- **tools/**: MCP tool implementations and registration system

## Development

For detailed development instructions, including how to use this project as a template for your own MCP servers, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and releases.

## License

This project is licensed under the Unlicense - see the [LICENSE](LICENSE) file for details.

## Credits

This is a Python port of the [MCP Forge](https://github.com/achetronic/mcp-forge) project (Go), extended with additional OAuth flow endpoints and Python-specific implementations while maintaining security standards.
