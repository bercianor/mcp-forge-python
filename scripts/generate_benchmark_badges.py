"""Generate benchmark badges from pytest-benchmark results."""

import json
from pathlib import Path


def generate_badge(label: str, value: str) -> str:
    """Generate a simple SVG badge."""
    # Simple badge template
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="20">
  <rect width="200" height="20" fill="#555"/>
  <rect x="0" y="0" width="120" height="20" fill="#333"/>
  <text x="60" y="14" font-family="Arial" font-size="11" fill="white"
        text-anchor="middle">{label}</text>
  <text x="160" y="14" font-family="Arial" font-size="11" fill="white"
        text-anchor="middle">{value}</text>
</svg>"""


def main() -> None:
    """Generate badges from benchmark results."""
    benchmark_file = Path("benchmark.json")
    badges_dir = Path(".github/badges")

    if not benchmark_file.exists():
        return

    with benchmark_file.open() as f:
        data = json.load(f)

    # Extract average times for each benchmark
    for benchmark in data.get("benchmarks", []):
        name = benchmark["name"].split("::")[-1]
        mean_time = benchmark["stats"]["mean"]
        value = f"{mean_time * 1e9:.2f} ns"

        badge_svg = generate_badge(name, value)
        badge_path = badges_dir / f"{name}.svg"

        with badge_path.open("w") as f:
            f.write(badge_svg)


if __name__ == "__main__":
    main()
