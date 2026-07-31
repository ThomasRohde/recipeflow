"""Run a reproducible RecipeFlow build and SVG-render smoke benchmark."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path
from typing import Any

from recipeflow import build, render


def chain_document(operation_count: int) -> str:
    operations: list[dict[str, Any]] = []
    for index in range(operation_count):
        output = f"material-{index + 1}"
        declaration: dict[str, Any] = {"label": f"prepared material {index + 1}"}
        if index == operation_count - 1:
            declaration.update({"role": "final", "final": True})
        operations.append(
            {
                "id": f"operation-{index + 1}",
                "action": f"prepare stage {index + 1}",
                "inputs": [f"material-{index}"],
                "outputs": {output: declaration},
            }
        )
    document = {
        "recipeflow": 1,
        "recipe": {"id": "benchmark-chain", "title": "Benchmark Chain"},
        "ingredients": {"material-0": {"label": "starting material"}},
        "operations": operations,
    }
    return json.dumps(document, separators=(",", ":"), sort_keys=True)


def measure(action: Callable[[], object], iterations: int) -> dict[str, float]:
    action()
    samples: list[float] = []
    tracemalloc.start()
    for _ in range(iterations):
        started = time.perf_counter()
        action()
        samples.append(time.perf_counter() - started)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    ordered = sorted(samples)
    percentile_index = min(len(ordered) - 1, max(0, round(0.95 * len(ordered)) - 1))
    return {
        "median_seconds": statistics.median(samples),
        "p95_seconds": ordered[percentile_index],
        "peak_bytes": float(peak),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operations", type=int, default=40)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.operations < 1 or arguments.iterations < 1:
        parser.error("operations and iterations must be positive")

    source = chain_document(arguments.operations)

    def build_case() -> object:
        result = build(source, source_format="json")
        if not result.ok:
            raise RuntimeError(result.diagnostics)
        return result

    compiled = build_case()
    assert compiled.graph is not None

    def render_case() -> object:
        return render(compiled.graph, "tabular-svg")

    report = {
        "schema_version": "recipeflow.benchmark/v1",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "operations": arguments.operations,
        "iterations": arguments.iterations,
        "build": measure(build_case, arguments.iterations),
        "tabular_svg": measure(render_case, arguments.iterations),
    }
    content = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.write_text(content, encoding="utf-8", newline="\n")
    else:
        print(content, end="")

    if arguments.check:
        limits = {"build": 2.0, "tabular_svg": 5.0}
        failed = [
            name
            for name, maximum in limits.items()
            if report[name]["median_seconds"] > maximum
        ]
        if failed:
            print(f"Performance smoke threshold exceeded: {', '.join(failed)}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
