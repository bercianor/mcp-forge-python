# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of MCP-Python template
- Full MCP server implementation with OAuth support
- Docker and Helm deployment configurations
- Comprehensive test suite with 100% coverage
- Benchmarking for performance monitoring
- GitHub Pages documentation site
- Automated CI/CD with badges

### Changed

- Migrated from Go (MCP Forge) to Python implementation

### Technical Details

- Python 3.11+ support
- FastAPI-based HTTP server with SSE
- JWT validation with local/external strategies
- TOML configuration
- Ruff linting and Pyright type checking
