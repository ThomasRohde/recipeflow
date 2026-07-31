# RecipeFlow repository instructions

## Mission

Build RecipeFlow as a reusable library first. The CLI is a thin adapter. The project must
remain independent of URL retrieval, scraping, OCR, browser automation, and model
invocation.

## Commands

- Install: `uv sync --extra dev --extra png`
- Test: `uv run pytest`
- Coverage: `uv run pytest --cov=recipeflow --cov-report=term-missing --cov-fail-under=90`
- Lint: `uv run ruff check .`
- Type-check: `uv run mypy src`
- Architecture boundaries: `uv run python scripts/check_boundaries.py`
- Performance smoke: `uv run python scripts/benchmark_recipeflow.py --check`
- Schema determinism: `uv run python scripts/check_schemas.py`
- TypeScript declarations: `uv run python scripts/generate_typescript.py --check`
- Documentation links: `uv run python scripts/check_docs.py`
- README examples: `uv run python scripts/check_readme_examples.py`
- Authoring skill: `uv run python scripts/check_skill.py`
- SDK examples: `uv run python scripts/check_sdk_examples.py`
- Build: `uv build`
- CLI smoke test: `uv run recipeflow validate examples/espresso-brownies.recipe.yaml --json`
- Full gate: `make check`

Use the individual `uv run` commands on Windows systems without `make`.

## Invariants

- Business logic never imports from `recipeflow.cli`.
- Core APIs accept strings or in-memory objects; filesystem handling belongs in adapters.
- Expected authoring problems are structured diagnostics, not generic exceptions.
- Schemas are versioned public contracts and regenerate byte-for-byte.
- Preserve source evidence and ambiguity; never invent recipe facts.
- Add semantic fixtures and golden visual artifacts for every new graph feature.
- Do not truncate or clip visible text. Layout defects are validation failures.
- PNG is derived from the same SVG/layout geometry, never a second layout implementation.
- Keep CLI JSON stdout to one stable envelope; send progress and diagnostics to stderr.

## Change discipline

- Treat `GOAL.md` as the product completion contract.
- Version or explicitly migrate breaking public-contract changes.
- Update the relevant documentation, schema fixtures, and executable examples with code.
- Use temporary directories in tests. Never depend on a POSIX shell in Python code.
- Inspect generated SVG and PNG artifacts rather than accepting markup-only assertions.

## Definition of done

A change is complete only when tests, coverage, linting, typing, schema and declaration
checks, documentation checks, skill checks, and the package build pass. Public behavior must
remain backward compatible or be explicitly versioned and documented.
