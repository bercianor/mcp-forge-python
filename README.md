# MCP Forge Python - Production-Ready MCP Server Template

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Unlicense-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com)
[![CI](https://img.shields.io/github/actions/workflow/status/bercianor/mcp-forge-python/ci.yml)](https://github.com/bercianor/mcp-forge-python/actions)
[![Coverage](docs/badges/coverage-badge.svg)](https://github.com/bercianor/mcp-forge-python/actions)
[![Template](https://img.shields.io/badge/template-MCP%20Forge%20Python-blue)](https://github.com/bercianor/mcp-forge-python)
[![Contributors](https://img.shields.io/github/contributors/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python)

A comprehensive, production-ready MCP (Model Context Protocol) server template built with Python, featuring OAuth 2.0 authentication, JWT validation, and seamless deployment options for developers building AI-powered applications.

## Key Features of MCP Forge Python

## MCP Protocol Implementation

- Built with the `mcp[cli]` Python library for full MCP protocol support
- Comprehensive tools, resources, and prompts implementation
- Configurable server initialization with name and version

## Communication Transports

- **Stdio Transport**: Standard input/output communication for local AI clients like Claude Desktop
- **HTTP with SSE**: Server-Sent Events for real-time web-based communication

## Built-in MCP Tools

- **hello_world**: Personalized greeting functionality
- **whoami**: JWT-based user information exposure

## Security & Middleware

- **Access Logging**: Configurable request logging with header redaction
- **JWT Validation**: Dual strategies for token authentication
  - Local validation using JWKS URI and CEL expressions
  - External proxy delegation (Istio-compatible)

## OAuth 2.0 Integration (RFC 8414 & RFC 9728)

- **OAuth Authorization Server**: OpenID Connect configuration proxy
- **Protected Resource Metadata**: Complete OAuth resource discovery endpoints

## Flexible Configuration

- TOML-based configuration system with dedicated sections for:
  - Server settings (name, version, transport)
  - Middleware configuration (logging, JWT)
  - OAuth integration (authorization servers, protected resources)

## Production-Ready Deployment

- Complete Docker containerization with Dockerfile
- Kubernetes Helm chart for cloud deployment
- Integration guides for Keycloak, Istio, and Hashrouter

## System Requirements

### External Dependencies

- **Python**: >= 3.10
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

- **Development dependencies**:
  - `ruff`: Linting and formatting
  - `pyright`: Type checking
  - `pytest`: Testing framework
  - `pytest-asyncio`: Async support for pytest
  - `coverage`: Code coverage

## Installation & Setup

```bash
# Install dependencies
uv sync

# Install package (enables direct commands)
uv pip install .

# Run HTTP server with SSE
uv run http
```

## Development Commands

```bash
# Testing & Quality
just test                    # Run all tests
just cov                     # Run tests with coverage report
just lint                    # Lint and format code
just typing                  # Type checking
just check-all              # Run all quality checks

# Lifecycle
just install                # Install/update dependencies
just clean                  # Remove all temporary files (.venv, caches, dist)
just clean-cache            # Clean caches only (keep .venv)
just fresh                  # Clean + fresh install

# Running
just run                    # Run HTTP server
just run-stdio              # Run stdio mode

# Run stdio server

uv run stdio

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
- **Requirement**: OAuth server with JWKS endpoint (e.g. Keycloak).

### "external" Strategy

- Delegates validation to an upstream proxy (Istio, Envoy, etc.).
- The JWT is forwarded in a specific header (`forwarded_header`).
- The proxy validates and extracts claims, injecting them into the request.
- **Requirement**: Proxy configured for JWT validation and header forwarding.

Example in `config.toml`.

## Configuration

See `config.toml` for configuration example.

**Security Note**: By default, the server runs on `127.0.0.1` to avoid unwanted exposures. Change to `0.0.0.0` only if necessary and with appropriate security measures.

## Documentation

- [Full Documentation](docs/index.md) - Complete guide including development, configuration, and contributing.
- [Development Guide](DEVELOPMENT.md) - How to use this as a template.
- [Contributing](CONTRIBUTING.md) - Guidelines for contributors.

## Development

For detailed development instructions, including how to use this project as a template for your own MCP servers, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and releases.

## License

This project is licensed under the Unlicense - see the [LICENSE](LICENSE) file for details.

## Credits

Complete translation to Python of the [MCP Forge](https://github.com/achetronic/mcp-forge) project (Go), maintaining all functionalities and security level of the original.

```

```
