# Command-line interface

The CLI reads and writes files, selects presentation, and maps public service results to
process conventions. Recipe semantics stay in the library.

## Commands

| Command | Purpose |
| --- | --- |
| `init` | Write a minimal new document, refusing accidental overwrite |
| `validate` | Parse and run semantic validation |
| `compile` | Produce the canonical graph |
| `inspect` | Produce reusable graph analysis |
| `render` | Produce text, Mermaid, JSON, layout, SVG, HTML, or PNG |
| `render-check` | Validate layout bounds, overflow, collisions, and raster metadata |
| `format` | Deterministically format without changing meaning |
| `migrate` | Migrate explicitly between supported document versions |
| `diff` | Report semantic changes between two documents or graphs |
| `schema` | Export a versioned portable contract |
| `examples` | List or copy bundled examples |

Run `recipeflow COMMAND --help` for command-specific arguments.

## Shared options

Where applicable:

- `--json` selects the stable machine envelope;
- `--no-color` disables ANSI styling;
- `--quiet` suppresses non-error human output;
- `--strict` enables strict policy diagnostics;
- `--output` writes the primary artifact to a path;
- `--format` chooses source or render format.

Render options map directly to `RenderOptions`. For example:

```powershell
recipeflow render recipe.flow.yaml `
  --format tabular-png `
  --theme classic `
  --scale 2 `
  --dpi 144 `
  --output recipe.png
```

PNG support requires `recipeflow[png]`. If it is absent, rendering returns RF510 with the
installation hint rather than an import traceback.

## JSON mode

With `--json`, stdout contains exactly one JSON value and no headings, progress bars, or
Rich formatting:

```json
{
  "schema_version": "recipeflow.cli-result/v1",
  "command": "validate",
  "ok": false,
  "data": null,
  "diagnostics": [
    {
      "schema_version": "recipeflow.diagnostic/v1",
      "code": "RF104",
      "severity": "error",
      "path": "/operations/0/inputs/0",
      "message": "Unknown material 'ghost'.",
      "suggestions": [],
      "related_paths": [],
      "context": {}
    }
  ]
}
```

Diagnostics and progress that are not part of the envelope go to stderr. A command that
writes a binary artifact never mixes that artifact with a JSON envelope on stdout: provide
`--output` or choose one output mode.

## Exit codes

| Code | Meaning |
| ---: | --- |
| 0 | Success |
| 2 | Semantic validation failure |
| 3 | Syntax or structural parse failure |
| 4 | Unsupported schema version or migration path |
| 5 | Filesystem or other adapter I/O failure |
| 70 | Unexpected internal failure |

Warnings do not change a zero exit code unless strict policy promotes them to errors.
Typer usage errors follow Typer's own usage exit behavior and are not RecipeFlow document
diagnostics. Unexpected adapter defects are wrapped as an RF900 diagnostic; JSON mode still
emits exactly one stable envelope before exiting 70.

## Output safety

- Commands do not overwrite input unless an explicit in-place option is selected.
- `migrate --dry-run` and `format --check` never write.
- Parent directories are not created implicitly unless the command documents that behavior.
- Errors opening or writing a path map to exit code 5 and a structured diagnostic in JSON
  mode.
- Relative paths are resolved by the CLI adapter, never stored in canonical graphs.
