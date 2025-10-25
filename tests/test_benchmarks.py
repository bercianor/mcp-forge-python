"""Benchmarks for MCP tools performance."""

from collections.abc import Callable
from typing import Any

import pytest

from mcp_app.context import jwt_payload
from mcp_app.mcp_components.tools.hello_world import hello_world
from mcp_app.mcp_components.tools.whoami import whoami


class TestBenchmarks:
    """Benchmark tests for MCP tools."""

    @pytest.mark.benchmark
    def test_hello_world_benchmark(self, benchmark: Callable[[Callable], None]) -> None:  # type: ignore[PGH003]
        """Benchmark hello_world tool performance."""

        def run_hello_world() -> str:
            return hello_world(name="Test User")

        benchmark(run_hello_world)

    @pytest.mark.benchmark
    def test_whoami_benchmark(self, benchmark: Callable[[Callable], None]) -> None:  # type: ignore[PGH003]
        """Benchmark whoami tool performance."""
        # Mock payload for testing
        mock_payload = {"sub": "user123", "roles": ["admin"], "permissions": ["tool:admin"]}
        jwt_payload.set(mock_payload)

        def run_whoami() -> dict[str, Any] | str:
            return whoami()

        benchmark(run_whoami)
