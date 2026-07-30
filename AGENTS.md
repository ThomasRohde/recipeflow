# RecipeFlow repository instructions

## Mission
Build RecipeFlow as a reusable library first. The CLI is a thin adapter. The project must remain independent of URL retrieval and model invocation.

## Commands
- Install: `uv sync --extra dev`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Type-check: `uv run mypy src`
- CLI smoke test: `uv run recipeflow validate examples/espresso-brownies.recipe.yaml`

## Invariants
- Business logic never imports from `recipeflow.cli`.
- Core APIs accept strings or in-memory objects; filesystem handling belongs in adapters.
- Expected authoring problems are structured diagnostics, not generic exceptions.
- Schemas are versioned public contracts.
- Preserve source evidence and ambiguity; never invent recipe facts.
- Add golden fixtures for every new graph feature.

## Definition of done
A change is complete only when tests, linting and typing pass, documentation is updated, and the public contract remains backward compatible or is explicitly versioned.
