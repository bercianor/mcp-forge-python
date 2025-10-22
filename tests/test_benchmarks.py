"""Benchmarks for MCP tools performance."""

from collections.abc import Callable

import pytest

from mcp_app.tools.router import hello_world, whoami


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
        # Mock JWT for testing
        mock_jwt = "mock.jwt.token"

        def run_whoami() -> str:
            return whoami(jwt=mock_jwt)

        benchmark(run_whoami)
