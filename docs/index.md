# MCP Forge Python - Production-Ready MCP Server Template

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Unlicense-blue.svg)](LICENSE.txt)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com)
[![CI](https://img.shields.io/github/actions/workflow/status/bercianor/mcp-forge-python/ci.yml)](https://github.com/bercianor/mcp-forge-python/actions)
[![Coverage](badges/coverage-badge.svg)](https://github.com/bercianor/mcp-forge-python/actions)
[![Template](https://img.shields.io/badge/template-MCP%20Forge%20Python-blue)](https://github.com/bercianor/mcp-forge-python)
[![Contributors](https://img.shields.io/github/contributors/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python)

A comprehensive, production-ready MCP (Model Context Protocol) server template built with Python, featuring OAuth 2.0 authentication, JWT validation, and seamless deployment options for developers building AI-powered applications.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "MCP Forge Python",
  "description": "A production-ready MCP (Model Context Protocol) server template with OAuth support, JWT validation, and deployment options for Python developers.",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Linux, macOS, Windows",
  "programmingLanguage": "Python",
  "softwareVersion": "1.0.0",
  "author": {
    "@type": "Person",
    "name": "Ruben",
    "url": "https://github.com/bercianor"
  },
  "codeRepository": "https://github.com/bercianor/mcp-forge-python",
  "license": "https://bercianor.es/mcp-forge-python/LICENSE",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "featureList": [
    "MCP Protocol Implementation",
    "OAuth 2.0 Authentication",
    "JWT Validation",
    "HTTP with SSE Transport",
    "Docker Deployment",
    "Kubernetes Helm Chart"
  ],
  "url": "https://bercianor.es/mcp-forge-python"
}
</script>

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

## Getting Started with MCP Forge Python

### System Requirements

- **Python Version**: 3.10 or higher
- **Package Manager**: uv for dependency management ([installation guide](https://astral.sh/uv))

### Installation & Setup

```bash
# Install project dependencies
uv sync

# Install the MCP server package
uv pip install -e .

# Start HTTP server with SSE support
uv run http

# Alternative: Run stdio server for local AI clients
uv run stdio
```

## Documentation & Resources

- **[Development Guide](development.html)** - Complete guide for using this template
- **[Contributing Guidelines](contributing-guide.html)** - How to contribute to the project
- **[Configuration Reference](configuration.html)** - Detailed configuration options
- **[Release Notes](https://github.com/bercianor/mcp-forge-python/releases)** - Version history and changelog

## License

This project is licensed under the Unlicense - a public domain dedication. See [LICENSE.txt](LICENSE.txt) for the full license text.
