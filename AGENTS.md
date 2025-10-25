# Agent Guidelines for MCP-Python

## Setup
- Install: `uv sync && uv pip install -e .`

## Commands
- **Test all**: `just test` or `uv run -m pytest`
- **Test single**: `just test tests/test_file.py::test_function_name` or `uv run -m pytest tests/test_file.py::test_function_name`
- **Lint & format**: `just lint` or `uv run ruff check --fix && uv run ruff format`
- **Type check**: `just typing` or `uv run pyright`
- **Coverage**: `just cov` or `uv run -m coverage run -m pytest && uv run -m coverage report`
- **All checks**: `just check-all`
- **Run server**: `uv run http` (HTTP) or `uv run stdio` (stdio)

## Code Style
- **Line length**: 100 chars
- **Imports**: stdlib → third-party → local (alphabetical within groups)
- **Types**: Full type hints required, `from __future__ import annotations`
- **Naming**: snake_case functions/variables, PascalCase classes, UPPER_CASE constants
- **Docstrings**: Google style (Args/Returns/Raises)
- **Error handling**: Specific exceptions, no bare except
- **Paths**: Use `pathlib.Path`, not strings
- **Async**: Use async/await consistently
- **Testing**: pytest with fixtures, descriptive names, no magic numbers
- **Config**: Pydantic models, TOML format
