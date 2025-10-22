set dotenv-load

ARGS_TEST := env("_UV_RUN_ARGS_TEST", "")


@_:
    just --list


# Run tests
[group('qa')]
test *args:
    uv run {{ ARGS_TEST }} -m pytest {{ args }}

_cov *args:
    uv run -m coverage {{ args }}

# Run tests and measure coverage
[group('qa')]
@cov *args:
    just _cov erase
    just _cov run -m pytest {{ args }}
    just _cov combine
    just _cov report
    # just _cov html

# Run benchmarks
[group('qa')]
@bench *args:
    uv run -m pytest tests/test_benchmarks.py --benchmark-only {{ args }}

# Run linters
[group('qa')]
lint *args:
    uv run ruff check {{ args }} --fix
    uv run ruff format {{ args }}

# Check types
[group('qa')]
typing *args:
    uv run pyright {{ args }}

# Perform all checks
[group('qa')]
check-all: cov lint typing


# Update dependencies
[group('lifecycle')]
update:
    uv sync --upgrade

# Ensure project virtualenv is up to date
[group('lifecycle')]
install:
    uv sync

# Remove temporary files
[group('lifecycle')]
clean: clean-cache
    rm -rf .venv dist build

# Clean caches and temporary files (keep .venv)
[group('lifecycle')]
clean-cache:
    rm -rf .pytest_cache .mypy_cache .ruff_cache .uv .coverage* htmlcov .benchmarks .github/badges
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type d -name "*.egg-info" -exec rm -r {} +

# Recreate project virtualenv from nothing
[group('lifecycle')]
fresh: clean install


# Run MCP service (HTTP)
[group('run')]
run:
    uv run http

# Run MCP service (stdio)
[group('run')]
run-stdio:
    uv run stdio
