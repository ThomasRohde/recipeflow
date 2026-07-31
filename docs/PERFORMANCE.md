# Performance policy

Correct semantics and legible output take precedence over micro-optimizations. Benchmarks
must not weaken validation, truncate text, or skip collision checks.

## Benchmark cases

Track at least:

- parse and validate for small, medium, and large documents;
- compile and analyze for long chains, wide branches, and many joins;
- tabular layout for long labels, many lanes, and many operations;
- SVG serialization and SVG-derived PNG rasterization;
- multi-recipe scheduling with increasing recipe and resource counts.

Record Python version, operating system, input fixture hash, options, warm-up policy,
iterations, median, high percentile, and peak memory.

Run the reproducible smoke benchmark with:

```powershell
uv run python scripts/benchmark_recipeflow.py --check
```

Use `--output benchmark.json` to retain release evidence. The smoke thresholds are generous
regression alarms, not performance marketing claims.

## Regression policy

A release blocks on:

- unbounded or superlinear behavior where a bounded alternative is expected;
- graph or text limits bypassed by equivalent input forms;
- a material benchmark regression above the recorded tolerance without an accepted reason;
- layout shortcuts that violate visual invariants.

Performance numbers are release evidence, not permanent API guarantees. Unknown durations
in a recipe are not estimated merely to make planning benchmarks easier.

## Determinism

Caching may improve performance but cannot change output order, bytes, diagnostics, or
mutation behavior. Benchmarks run with caches in a documented state.
