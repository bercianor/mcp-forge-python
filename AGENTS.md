# MCP-Python Agent Guidelines

## Setup

- **Install dependencies**: `uv sync`
- **Install package**: `uv pip install -e .`

## Commands

- **Test all**: `just test` or `uv run -m pytest`
- **Test single**: `just test tests/test_file.py::test_function_name` or `uv run -m pytest tests/test_file.py::test_function_name`
- **Lint & format**: `just lint` or `uv run ruff check --fix && uv run ruff format`
- **Type check**: `just typing` or `uv run pyright`
- **Coverage**: `just cov` or `uv run -m coverage run -m pytest && uv run -m coverage report`
- **Benchmarks**: `just bench` or `uv run -m pytest tests/test_benchmarks.py --benchmark-only`
- **All checks**: `just check-all`
- **Run HTTP server**: `uv run http`
- **Run stdio**: `uv run stdio`

## Code Style

- **Line length**: 100 characters
- **Imports**: stdlib → third-party → local (alphabetical within groups)
- **Types**: Full type hints required, use `from __future__ import annotations`
- **Naming**: snake_case functions/variables, PascalCase classes, UPPER_CASE constants
- **Docstrings**: Google style with Args/Returns/Raises sections
- **Error handling**: Specific exceptions, avoid bare except
- **Paths**: Use `pathlib.Path` instead of strings
- **Async**: Use async/await consistently for async operations
- **Testing**: pytest with fixtures, descriptive test names, avoid magic numbers in assertions
- **Config**: Use Pydantic models for configuration, TOML format
