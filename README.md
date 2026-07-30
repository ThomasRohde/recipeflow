# RecipeFlow

RecipeFlow is a reusable Python library and CLI for authoring, validating, compiling, analysing, laying out and rendering recipes as transformation graphs.

The project deliberately does **not** fetch recipe URLs and does **not** invoke an AI model. Codex or another intelligent author reads the source by any available means, writes a `recipe.flow.yaml` document, then uses RecipeFlow as a deterministic compiler and linter.

## Quick start

```powershell
uv sync --extra dev
uv run recipeflow validate examples/espresso-brownies.recipe.yaml
uv run recipeflow inspect examples/espresso-brownies.recipe.yaml
uv run recipeflow render examples/espresso-brownies.recipe.yaml --format tabular-svg -o espresso-brownies.svg
uv run recipeflow render examples/espresso-brownies.recipe.yaml --format tabular-html -o espresso-brownies.html
uv run recipeflow render examples/espresso-brownies.recipe.yaml --format mermaid
uv run pytest
```

Library use:

```python
from recipeflow import build

source = open("examples/espresso-brownies.recipe.yaml", encoding="utf-8").read()
result = build(source, source_format="yaml")
assert result.ok
print(result.graph)
```

## Architecture

```text
Codex skill / CLI / end-user app
              │
              ▼
      recipeflow public API
              │
  parse → validate → compile → analyse → layout → render
              │
              ▼
      versioned portable contracts
```

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for all milestones and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for design constraints.

## Original-style tabular visualization

RecipeFlow includes a first-class tabular layout engine rather than treating the original image as future polish. It assigns material flows to horizontal lanes and renders transformations as vertical join cells, closely matching the compact left-to-right notation that inspired the project.

Supported outputs:

- `tabular-svg`: self-contained, scalable, printable visualization
- `tabular-html`: responsive HTML wrapper around the SVG
- `tabular-layout`: renderer-neutral JSON for web, desktop and mobile applications

The renderer handles ingredient labels and quantities, joins, intermediate states, setup prerequisites, temperatures, durations and final outputs. The layout API is available directly as `recipeflow.create_tabular_layout(graph)`.
