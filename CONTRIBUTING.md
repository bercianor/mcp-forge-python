# Contributing to MCP-Forge-Python

Thank you for your interest in contributing to MCP-Forge-Python! This document provides guidelines and information for contributors.

## Development Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/bercianor/mcp-forge-python.git
   cd mcp-forge-python
   ```

2. **Install dependencies**:

   ```bash
   uv sync
   ```

3. **Install in development mode**:
   ```bash
   uv pip install -e .
   ```

## Development Workflow

### Code Quality

We use several tools to maintain code quality:

- **Linting & Formatting**: `just lint` (uses ruff)
- **Type Checking**: `just typing` (uses pyright)
- **Testing**: `just test` (uses pytest)
- **Coverage**: `just cov` (uses coverage)
- **All Checks**: `just check-all`

### Running Tests

```bash
# Run all tests
just test

# Run a specific test
just test tests/test_file.py::test_function_name

# Run tests with coverage
just cov
```

### Code Style Guidelines

- **Line length**: 100 characters
- **Imports**: stdlib → third-party → local (alphabetical within groups)
- **Types**: Full type hints required, use `from __future__ import annotations`
- **Naming**: snake_case functions/variables, PascalCase classes, UPPER_CASE constants
- **Docstrings**: Google style with Args/Returns/Raises sections
- **Error handling**: Specific exceptions, avoid bare except
- **Paths**: Use `pathlib.Path` instead of strings
- **Async**: Use async/await consistently for async operations
- **Testing**: pytest with fixtures, descriptive test names, avoid magic numbers in assertions

### Commit Messages

We follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Project Structure

```
src/mcp_app/
├── main.py          # Application entry point
├── config.py        # Configuration models
├── handlers/        # OAuth handlers
├── middlewares/     # Custom middlewares
└── tools/           # MCP tools

tests/               # Test files
chart/               # Kubernetes Helm chart
```

## Adding New Tools

To add a new MCP tool:

1. Create the tool function in `src/mcp_app/tools/router.py`
2. Register it in the `register_tools()` function
3. Add tests in `tests/test_tools.py`
4. Update documentation

Example tool:

```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description.

    Args:
        param: Parameter description

    Returns:
        Result description
    """
    return f"Processed: {param}"
```

## Pull Request Process

1. **Fork** the repository
2. **Create a feature branch** from `main`
3. **Make your changes** following the code style guidelines
4. **Add tests** for new functionality
5. **Run all checks**: `just check-all`
6. **Update documentation** if needed
7. **Commit** with conventional commit messages
8. **Push** to your fork
9. **Create a Pull Request** with a clear description

## Reporting Issues

When reporting bugs or requesting features:

- **Use the issue templates** when available
- **Provide clear steps to reproduce** for bugs
- **Include environment information** (Python version, OS, etc.)
- **Attach logs or error messages** when relevant

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (Unlicense).
