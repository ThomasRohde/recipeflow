# Public Python API

Supported application imports originate from `recipeflow`. Importing internal modules is
not a compatibility promise. Core calls accept strings, mappings, or typed in-memory models
and do not require filesystem access.

`recipeflow.__version__` reports the installed package version. Serialized contract versions
remain independent and must be read from each object's `schema_version`.

## Parse

```python
parse(source, source_format="yaml") -> ParseResult
parse_yaml(source) -> ParseResult
parse_json(source) -> ParseResult
parse_document(source_or_mapping, source_format="yaml") -> ParseResult
```

`ParseResult` contains either a `RecipeDocument` or structured diagnostics. Syntax errors,
structural errors, and unsupported document versions remain distinguishable.

## Validate and compile

```python
validate(document, strict=False, options=None) -> ValidationResult
validate_source(source_or_document, source_format="yaml", strict=False) -> ValidationResult
incremental_validate(source_or_document, source_format="yaml", strict=False) -> ValidationResult
compile_recipe(document) -> RecipeGraph
compile_document(document, strict=False) -> CompileResult
```

`compile_recipe` is the compatibility convenience for already validated typed documents.
Applications handling authored or incremental input should prefer `compile_document`,
which returns diagnostics instead of throwing for expected authoring problems.

`RecipeGraph` collection fields are immutable tuples or read-only mappings. Its
`subrecipes` mapping contains `CompiledSubrecipe` boundaries; invoking
`OperationNode.subrecipe_inputs` contains typed `SubrecipeInputBinding` records with source
paths.

Strict validation enables policy checks such as required provenance. It never turns an
ambiguous claim into an invented value.

## Analyze

```python
analyze(graph) -> GraphAnalysis
```

Analysis reports counts, usage, branches, joins, splits, reservations, disconnected
components, topological order, setup prerequisites, possible parallel operations, and
critical path when duration data permits it.

## Layout and rendering

```python
create_tabular_layout(graph, layout_options=None) -> TabularLayout
validate_tabular_layout(layout) -> tuple[Diagnostic, ...]
list_layout_strategies() -> tuple[str, ...]
get_layout_strategy(name) -> LayoutStrategy
register_layout_strategy(name, strategy) -> None
render(graph, format="text", options=None) -> RenderArtifact
render_check(graph, options=None) -> ValidationResult
```

`LayoutOptions` configures direct geometry creation. `RenderOptions` is the public
rendering convenience and maps its layout fields into `LayoutOptions`. The default notation
is backward-compatible `flow`; `compact-table` provides an original-inspired nested grid.
`ledger` provides a folio-numbered, double-entry notation with continuous and paginated
output. The default theme is `classic`, independently of notation. Third-party strategies
require explicit, namespaced registration and are never auto-discovered. Available formats
include `text`, `mermaid`, `json`, `tabular-layout`, `tabular-svg`, `tabular-html`, and
`tabular-png`. PNG content is binary and is derived from the same SVG geometry.

`LayoutOptions.page_height` and `LayoutOptions.print_mode` control renderer-neutral page
geometry. In screen mode `page_height` remains `None`; in print mode automatic page size
defaults to A4 portrait. Page boundaries are sheet-break guides in the existing layout
contract, not a separate sheets collection. `TextRole` includes the public
`allocation-balance` value for split arithmetic. Strategy diagnostics are retained on the
layout, and `render_check` merges them with generic geometry diagnostics.

See [LAYOUT-ENGINE.md](LAYOUT-ENGINE.md) for option defaults and invariants.

## End-to-end build

```python
build(source, source_format="yaml", strict=False) -> BuildResult
```

Build composes parsing, validation, compilation, and analysis. It does not write files.
Callers serialize `model_dump(mode="json")` or use the result's JSON method when crossing a
process boundary.

## Format, migrate, and compare

```python
format_document(
    source_or_document,
    source_format="yaml",
    output_format="yaml",
) -> FormatResult

migrate(
    source_or_document,
    target_version="recipeflow.document/v1",
    source_format="yaml",
    output_format="yaml",
    dry_run=False,
) -> MigrationResult

semantic_diff(before, after) -> DiffResult
```

Formatting is deterministic and semantic-preserving. Migration is explicit, reports RF6xx
diagnostics, preserves source evidence, and supports a no-write dry run. Semantic diff
compares meaning rather than YAML formatting.

## Multi-recipe planning

```python
plan_recipes(request: PlanningRequest) -> PlanningResult
project_shopping_list(...)
project_mise_en_place(...)
```

Planning composes canonical single-recipe graphs without adding scheduling concepts to the
single-recipe document contract.

## Result contract

Portable result models share these properties:

- an explicit `schema_version` where serialized across languages;
- an `ok` state derived from diagnostics, not an unrelated boolean source of truth;
- stable diagnostic ordering;
- JSON-compatible `model_dump(mode="json")` output;
- no filesystem paths unless an adapter explicitly adds them;
- no CLI presentation fields in domain results.

Expected authoring errors return results. Unexpected programmer or invariant failures may
raise a typed RecipeFlow exception.

## Executable examples

- [Basic in-memory build](../examples/sdk/basic.py)
- [FastAPI-style service boundary](../examples/sdk/fastapi_style.py)
- [Incremental editor validation](../examples/sdk/incremental_editor.py)
- [Direct layout use](../examples/sdk/direct_layout.py)

Run all examples with:

```powershell
uv run python scripts/check_sdk_examples.py
```
