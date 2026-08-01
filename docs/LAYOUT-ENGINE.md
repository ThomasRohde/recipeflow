# Tabular layout engine

The selected layout strategy converts a validated `RecipeGraph` into
`recipeflow.tabular-layout/v1`. Renderers consume that contract; they do not recalculate
geometry.

The built-in `flow` strategy is the default. `compact-table` projects the same graph into
ingredient rows and nested operation spans. `ledger` projects it into folio-numbered
consumed, produced, and conditions columns. All three produce the same renderer-neutral
public model and pass the same layout validator.

## Stages

1. Measure every visible and accessibility string with deterministic font metrics.
2. Wrap labels within option bounds without losing source text.
3. Assign material lanes and topologically ordered operation columns.
4. Negotiate title/yield, ingredient, setup, operation, metadata, and final-output
   box sizes.
5. Route material lines through branch, join, split, and reservation topology.
6. Resolve disallowed opaque-box and text intersections.
7. Expand canvas bounds by the configured safe margin.
8. Validate every element and return RF5xx diagnostics for unresolved defects.

PNG rasterizes the resulting SVG. It never repeats these stages.

## Typed options

Default `RenderOptions` values:

| Field | Default | Meaning |
| --- | --- | --- |
| `notation` | `"flow"` | Built-in `flow`, `compact-table`, or `ledger`, or an explicitly registered namespaced strategy |
| `theme` | `"classic"` | `classic` or `modern` |
| `operation_label_orientation` | `"auto"` | `auto`, `horizontal`, or `vertical` |
| `width` | `None` | Optional requested canvas width |
| `scale` | `2.0` | Raster scale |
| `dpi` | `144` | PNG density metadata |
| `background` | `None` | Theme background unless overridden |
| `safe_margin` | `24` | Minimum outer canvas margin |
| `minimum_font_size` | `10` | Floor for every resolved text style |
| `base_font_size` | `14` | Base used to scale the theme typography |
| `line_height` | `1.3` | Line-height multiplier |
| `outer_margin` | `None` | Optional override for the safe canvas margin |
| `ingredient_label_width` | `None` | Optional exact ingredient-column width |
| `operation_column_minimum_width` | `82` | Minimum operation width |
| `operation_column_maximum_width` | `176` | Maximum operation width before vertical/reflow policy |
| `setup_card_minimum_width` | `176` | Minimum intrinsic setup-card width |
| `orientation` | `"auto"` | `auto`, `portrait`, or `landscape` preferred width |
| `show_intermediate_labels` | `True` | Include intermediate flow labels |
| `show_source_quantities` | `True` | Display authored quantity strings |
| `show_normalized_quantities` | `False` | Display structured normalized quantities |
| `show_provenance` | `False` | Include compact provenance annotations |
| `wrap_mode` | `"word"` | Word-first or grapheme-first wrapping |
| `allow_ellipsis` | `False` | Permit lossy visual shortening when a bounded layout cannot reflow; complete source text remains in accessibility metadata |
| `page_size` | `"auto"` | `auto`, `A4`, or `letter` preferred print width |
| `print_mode` | `False` | Use print-oriented width and HTML presentation |

The same typed options are accepted by the Python API and the `render` command. Arbitrary
option dictionaries are not a public contract. In addition to the mapped fields above,
`LayoutOptions` publicly exposes `page_height: float | None`; its `print_mode` default is
also `False`. `RenderOptions.page_size` resolves these to A4 794 x 1123
portrait / 1123 x 794 landscape or letter 816 x 1056 portrait / 1056 x 816 landscape.
`print_mode=True` with automatic page size defaults to A4 portrait.

## Layout contract

A layout serializes:

- the selected `notation` identifier;
- canvas width, height, and coordinate system;
- lanes, material segments, operation cells, setup cards, and output boxes;
- measured text boxes and complete source strings;
- recipe yield, setup targets, produced-material quantities, and edge-specific
  consumption quantities when present in the graph;
- line routes and semantic ownership;
- theme-neutral roles;
- raster hints and accessibility descriptions;
- layout diagnostics and explicit allowed-overlap relationships.

`TextRole` includes the public `allocation-balance` value for arithmetic explicitly
licensed by a split. A ledger strategy must not use it for an ordinary transformation.

Coordinates are finite, non-negative, deterministic numbers. The SVG `viewBox` encloses the
layout canvas exactly.

## Validation

`validate_tabular_layout(layout)` checks:

- every text and opaque box is inside the canvas;
- every rendered line is inside the canvas;
- no text box reports overflow;
- unrelated opaque content boxes do not overlap;
- text does not intersect an unrelated operation;
- setup content stays inside the setup area;
- final labels stay inside final-output boxes;
- all display labels preserve complete source text or accessible equivalents.

Strategies may also emit semantic layout diagnostics that the generic geometry validator
cannot derive. `recipeflow render-check` merges `layout.diagnostics` with the generic
validator result and exposes the combined result through the CLI.

Ledger strategy diagnostics are:

| Code | Severity | Meaning |
| --- | --- | --- |
| `RF506` | error | An exact partial draw cannot be printed because its allocation is unavailable. |
| `RF507` | warning | A produced `HELD` portion remains unconsumed at the end of the ledger. |
| `RF508` | error | Safe pagination is impossible, including a semantic leaf taller than the usable page area. Nothing is clipped. |

## Determinism and mutation

Layout never mutates the graph. Repeated layout and render calls with equal graph and options
are byte-identical. Tests cover reordered mapping input, Unicode, arbitrary label lengths,
and generated acyclic graphs.

## Strategy registry

`list_layout_strategies()` and `get_layout_strategy(name)` expose the registry.
Third-party strategies are installed explicitly with
`register_layout_strategy("vendor:name", strategy)`. Names must be namespaced, existing
registrations cannot be replaced, and a strategy must return a `TabularLayout` whose
`notation` matches the selected name. RecipeFlow does not discover or import extensions
implicitly.

## Ledger pagination

Screen-mode ledger layouts have no page height and no sheet-break guides. Paginated
layouts have a canvas height that is an exact multiple of `page_height`; page boundaries
are `guide` paths with `style_class="sheet-break"`, not a separate `sheets` field.

The title and standing conditions appear on page one, column headings repeat on later
pages, and every non-final page ends with the exact material frontier. Entries move intact
when possible. An oversized entry splits only between semantic leaf cells, repeats a
print-only continued head, and exposes its fragments through `OperationCell.box_ids`.
Standalone SVG and PNG retain the full canvas. Print HTML uses uniquely identified SVG
windows per sheet and one accessibility list.

## Semantic visibility

The visual contract includes quantities that affect topology. A divided ingredient can have
different quantities on its produced branches, and an operation can consume only part of a
material. Produced-material labels therefore include their authored quantity, while an
operation with an edge-specific quantity receives a measured `Uses:` block inside its cell.

Setup cards show their target or resource when authored and explicitly name the operations
that require them. Dependency guides also use separate corridors and separate operation
anchors so multiple prerequisites do not collapse into one ambiguous shared line.

Operation cells list direct source-material inputs with quantities. Edge-specific
allocations take precedence over the material's total quantity. This makes a dense span
explicit—for example, stock and tomatoes enter the sauce operation rather than a later
braise. Recipe yield is rendered beneath the title.
