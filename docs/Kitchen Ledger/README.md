# Handoff: Kitchen Ledger notation (`ledger`)

## What this is

A specification for RecipeFlow's **third built-in layout notation**, selected from a
six-concept notation study. The Kitchen Ledger renders a `RecipeGraph` as a double-entry
ledger: one numbered entry per transform operation, everything consumed on the left,
everything produced on the right, and durations / temperatures / prerequisites /
completion criteria in a third ruled-off column.

**This is not a web feature.** RecipeFlow is a Python library with a thin CLI adapter, and
this notation is implemented the same way `compact-table` was: a new `LayoutStrategy`
that emits `recipeflow.tabular-layout/v1` geometry, consumed unchanged by the existing
SVG / HTML / PNG renderers.

## About the design references

The visual design was produced as an HTML document (`RecipeFlow Notation Study.dc.html`
in the design project). **Do not port that HTML.** It is a pixel-accurate drawing of the
intended output, used to derive the numbers in `02-GEOMETRY.md`. The implementation
target is Python that resolves the same geometry from measured text.

Fidelity: **high**. Column ratios, line heights, rule weights and band order in
`02-GEOMETRY.md` are the contract. Colours are **theme**, not notation — they come from
`LayoutTheme`, and the notation must be fully legible in greyscale.

## Read in this order

| File | Contents |
| --- | --- |
| `01-NOTATION.md` | Semantics: what each visual device means, the seven invariants, the tag vocabulary. Read first — the geometry is meaningless without it. |
| `02-GEOMETRY.md` | Resolved geometry: bands, columns, line heights, rules, the height algorithm, sheet breaks. |
| `03-LAYOUT-CONTRACT.md` | How to express the ledger in `recipeflow.tabular-layout/v1`: roles, box kinds, style classes, id scheme, and the exact schema impact. |
| `04-IMPLEMENTATION.md` | File-by-file work plan, the strategy skeleton, registry / CLI / corpus wiring, and the phase split. |
| `05-TESTS.md` | Fixtures, invariant assertions, new RF5xx diagnostics, and the black-box PNG probes. |
| `06-WORKED-EXAMPLES.md` | Expected output for espresso-brownies, split-and-reserve, multiple-outputs and large, with numbers to assert against. |
| `07-VISUAL-REVIEW.md` | Release visual inspection and PNG-only human-proxy evaluation evidence. |

## Scope of the change

New notation name: **`ledger`** (built-in, unnamespaced, alongside `flow` and
`compact-table`).

- One new module: `src/recipeflow/layout/ledger.py`.
- Additive registry entry, CLI `--notation ledger`, corpus `--notation ledger`.
- Additive `LayoutTheme` fields (internal dataclass, not a public schema).
- One additive public `TextRole` enum member (`allocation-balance`). See
  `03-LAYOUT-CONTRACT.md` section 4.
- Additive `LayoutOptions.page_height` and `LayoutOptions.print_mode` fields for continuous
  and paginated geometry; `RenderOptions.page_size` maps to the same page dimensions.
- Three new RF5xx layout diagnostic codes.
- No change to `RecipeDocument`, `RecipeGraph`, compilation, or semantic validation.
- No new renderer. PNG stays derived from the same SVG.

## Why this notation

`flow` and `compact-table` both encode participation as **extent** — a line reaching a
cell, a rectangle spanning rows — and extent is what a reader over-reads. The ledger
encodes participation as an **enumerated line**, so "does this ingredient enter this
step?" is answered by the presence of a sentence, not by the interpretation of a shape.
Split allocations become arithmetic rather than geometry. Height is linear in
operations x inputs, so it paginates instead of shrinking.

## Definition of done

Per `AGENTS.md`, in addition to the feature itself:

~~~
make check
uv run python scripts/generate_visual_corpus.py --notation ledger
uv run python scripts/generate_visual_corpus.py --notation ledger --check
uv run pytest tests/visual/test_ledger_corpus.py
~~~

`make check` must pass unchanged, including `schema-check` and `types-check` after
regenerating the tabular-layout schema and TypeScript declarations. Docs updated:
`docs/TABULAR-NOTATION.md`, `docs/LAYOUT-ENGINE.md`, `docs/PUBLIC-API.md`,
`docs/ROADMAP.md`, `CHANGELOG.md`. The 1.2.0 release includes continuous rendering,
safe pagination, print-HTML sheet windows, the complete visual corpus, and the fresh
PNG-only evaluation; pagination is not deferred.

## Non-goals

- No time axis. The study's Kitchen Score concept (which infers start times) is explicitly
  **not** part of this work.
- No row reordering. Unlike `compact-table`, the ledger never reorders authored material
  to make geometry contiguous — it has no spans to keep contiguous.
- No interactivity. Standalone SVG and PNG use one continuous canvas; print HTML windows
  that same geometry into static sheets.
