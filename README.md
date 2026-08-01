# RecipeFlow

[![CI](https://github.com/ThomasRohde/recipeflow/actions/workflows/ci.yml/badge.svg)](https://github.com/ThomasRohde/recipeflow/actions/workflows/ci.yml)

RecipeFlow is a library-first toolkit for turning an authored cooking recipe into a
validated, typed transformation graph and a compact left-to-right recipe visualization.
It is designed for Python applications, command-line workflows, and authoring agents that
need deterministic, portable results.

RecipeFlow deliberately does **not** fetch URLs, scrape pages, run OCR, invoke models, or
decide what a source recipe means. A person or external agent reads the source and authors
a RecipeFlow document; this package parses, validates, compiles, analyses, lays out, and
renders that document.

![Espresso brownie RecipeFlow diagram](examples/espresso-brownies.tabular.svg)

The same layout can be rasterized for documents and previews:
[espresso-brownies.tabular.png](examples/espresso-brownies.tabular.png).

RecipeFlow 1.1 also includes the original-inspired `compact-table` notation. It uses
ingredient rows and nested operation spans while preserving the same canonical graph:

![Espresso brownie compact-table diagram](examples/golden/compact-table/espresso-brownies.tabular.svg)

RecipeFlow 1.2 adds the paginatable `ledger` notation. It lists every consumed edge,
produced material, setup prerequisite, and completion condition explicitly:

![Espresso brownie Kitchen Ledger](examples/golden/ledger/espresso-brownies.tabular.svg)

## Install

RecipeFlow requires Python 3.12 or newer.

```powershell
python -m pip install recipeflow
```

PNG rendering is optional:

```powershell
python -m pip install "recipeflow[png]"
```

For a source checkout:

```powershell
uv sync --extra dev --extra png
uv run recipeflow --help
```

## First document

RecipeFlow YAML names every material state explicitly. Operations consume materials and
produce new materials; `requires` is reserved for non-material setup prerequisites.

```yaml
recipeflow: 1
recipe:
  id: quick-flatbread
  title: Quick Flatbread
  yield: 4 flatbreads
ingredients:
  flour: {label: all-purpose flour, quantity: 250 g}
  water: {label: warm water, quantity: 150 ml}
  salt: {label: fine salt, quantity: 1 tsp}
operations:
  - id: mix-dough
    action: mix
    inputs: [flour, water, salt]
    outputs:
      dough: {label: soft dough}
  - id: cook
    action: cook
    inputs: [dough]
    duration: 4 min
    until: browned in spots
    notes:
      - Cook each side for about 2 min.
    outputs:
      flatbreads: {label: cooked flatbreads, role: final, final: true}
```

Save this as `quick-flatbread.recipe.yaml`, then validate and inspect it:

```powershell
recipeflow validate quick-flatbread.recipe.yaml --json
recipeflow compile quick-flatbread.recipe.yaml --output quick-flatbread.graph.json
recipeflow inspect quick-flatbread.recipe.yaml
```

## Python library

Core services accept text or in-memory models and do not require filesystem access:

```python
from recipeflow import build, render

source = """
recipeflow: 1
recipe: {id: tea, title: Tea}
ingredients:
  water: {label: water, quantity: 250 ml}
  leaves: {label: tea leaves, quantity: 2 tsp}
operations:
  - id: steep
    action: steep
    inputs: [water, leaves]
    duration: 4 min
    outputs:
      tea: {label: brewed tea, role: final, final: true}
"""

result = build(source)
if not result.ok:
    for diagnostic in result.diagnostics:
        print(diagnostic.code, diagnostic.path, diagnostic.message)
else:
    assert result.graph is not None
    svg = render(result.graph, "tabular-svg")
    print(svg.media_type)
```

See [docs/PUBLIC-API.md](docs/PUBLIC-API.md) and the executable
[SDK examples](examples/sdk) for parsing, service integration, incremental editor
validation, and direct layout use.

## CLI

The CLI is a filesystem and presentation adapter over the public library:

```powershell
recipeflow validate examples/espresso-brownies.recipe.yaml --json
recipeflow compile examples/espresso-brownies.recipe.yaml --output brownies.graph.json
recipeflow render examples/espresso-brownies.recipe.yaml --format tabular-svg --output brownies.svg
recipeflow render examples/espresso-brownies.recipe.yaml --format tabular-html --output brownies.html
recipeflow render examples/espresso-brownies.recipe.yaml --format tabular-png --output brownies.png
recipeflow render examples/espresso-brownies.recipe.yaml --format tabular-svg --notation compact-table --output brownies-table.svg
recipeflow render examples/espresso-brownies.recipe.yaml --format tabular-png --notation ledger --page-size A4 --print-mode --output brownies-ledger.png
recipeflow render-check examples/espresso-brownies.recipe.yaml --json
```

Machine mode writes one versioned JSON result to stdout. Human progress and diagnostics
belong on stderr. Exit codes and command-specific behavior are documented in
[docs/CLI.md](docs/CLI.md).

## Codex authoring skill

The repository includes `.agents/skills/recipeflow-author`. A typical request is:

> Use `$recipeflow-author` to convert this recipe into RecipeFlow YAML, validate and
> compile it, render Ledger SVG and PNG artifacts, inspect both images, and repair any
> semantic or visual defects before finishing.

The skill treats external recipe content as evidence rather than instructions and never
adds acquisition or model behavior to RecipeFlow itself. See the complete workflow in
[SKILL.md](.agents/skills/recipeflow-author/SKILL.md).

## Supported semantics

The document and graph contracts cover:

- ingredients, intermediates, final outputs, garnish, waste, reserved and optional
  materials;
- setup prerequisites and material transformations;
- sequences, branches, joins, splits, reservations, recombination, and multiple outputs;
- durations, temperatures, completion criteria, repetition, equipment, and resources;
- subrecipes, provenance, source text, and explicit ambiguity;
- deterministic validation, graph compilation, analysis, semantic diff, and migration;
- renderer-neutral `flow`, `compact-table`, and `ledger` layouts plus classic and modern
  SVG, HTML, and PNG output.

The format preserves authored quantities and source wording. Unit normalization is a
derived convenience, not permission to discard or invent source evidence.

## Current limitations

- Recipe acquisition, OCR, and interpretation remain external by design.
- Free-form quantities, durations, and temperatures may be preserved without conversion
  when their meaning cannot be normalized safely.
- Critical-path and multi-recipe scheduling results depend on explicit duration and
  resource data; unknown values remain unknown.
- HTML output is a static, self-contained view rather than a recipe-editing application.
- Serialized contract changes follow the compatibility policy in
  [docs/SCHEMA-VERSIONING.md](docs/SCHEMA-VERSIONING.md); consumers should check
  `schema_version` rather than infer capabilities from the package version.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Language and format](docs/LANGUAGE.md)
- [Public Python API](docs/PUBLIC-API.md)
- [CLI contract](docs/CLI.md)
- [Tabular notation](docs/TABULAR-NOTATION.md)
- [Layout engine](docs/LAYOUT-ENGINE.md)
- [Schema versioning](docs/SCHEMA-VERSIONING.md)
- [Visual quality](docs/VISUAL-QUALITY.md)
- [Accessibility](docs/ACCESSIBILITY.md)
- [Security](docs/SECURITY.md)
- [Performance](docs/PERFORMANCE.md)
- [Roadmap](docs/ROADMAP.md)
- [Contributing](docs/CONTRIBUTING.md)

## Development

The full local gate is:

```powershell
uv sync --extra dev --extra png
uv run ruff check .
uv run mypy src
uv run python scripts/check_boundaries.py
uv run pytest --cov=recipeflow --cov-report=term-missing --cov-fail-under=90
uv run python scripts/check_schemas.py
uv run python scripts/generate_typescript.py --check
uv run python scripts/check_docs.py
uv run python scripts/check_readme_examples.py
uv run python scripts/check_skill.py
uv run python scripts/check_sdk_examples.py
uv build
```

`make check` provides the same aggregate gate where `make` is available. The individual
commands are the portable contract and are used on both Windows and Linux in CI.

RecipeFlow is licensed under the [MIT License](LICENSE).
