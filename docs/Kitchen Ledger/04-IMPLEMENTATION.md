# 04 — Implementation plan

## 1. Phases

**Phase 1 — continuous notation.** Strategy, registry, SVG classes, geometry tests, and
the continuous-canvas implementation.

**Phase 2 — print pagination in the same 1.2.0 release.** Sheet-break guides,
frontier-based carried-forward bands, safe entry fragmentation, repeated headings, HTML
per-sheet windowing, and the complete golden corpus.

There is no deferred pagination phase and no `sheets` field. Both phases above ship
together; the continuous implementation is simply the stable base used before adding
page boundaries.

## 2. Files

| Path | Change |
| --- | --- |
| `src/recipeflow/layout/ledger.py` | **new** — `LedgerLayoutStrategy` |
| `src/recipeflow/layout/strategies.py` | add `"ledger"` to `_BUILTIN_NAMES`; extend `_ensure_builtins()` |
| `src/recipeflow/layout/themes.py` | additive `LayoutTheme` fields (section 3) |
| `src/recipeflow/layout/engine.py` | extend `_scaled_theme` for the new styles |
| `src/recipeflow/models/layout.py` | `allocation-balance` in `TextRole` (see 03 section 4) |
| `src/recipeflow/layout/options.py` | public `page_height` and `print_mode` layout options |
| `src/recipeflow/renderers/svg.py` | style classes + notation-aware background |
| `src/recipeflow/renderers/html.py` | print-mode per-sheet windowing with unique ids and one accessibility list |
| `scripts/generate_visual_corpus.py` | `--notation` choices gain `"ledger"` |
| `examples/golden/ledger/` | **new** — 12 fixtures x 4 artifacts + `manifest.json` |
| `tests/visual/test_ledger_corpus.py` | **new** — see 05 |
| `tests/test_layout_strategies.py` | registry assertions |
| `schemas/recipeflow-tabular-layout-v1.schema.json` | regenerated |
| `types/recipeflow-contracts.d.ts` | regenerated |
| `docs/TABULAR-NOTATION.md` | new "Ledger notation" section |
| `docs/LAYOUT-ENGINE.md` | notation list, new role, new RF codes |
| `docs/PUBLIC-API.md` | notation list |
| `CHANGELOG.md` | feature + contract addition |

`scripts/check_docs.py` validates doc links — if you add a doc file, link it from an
existing one.

## 3. Theme additions

`LayoutTheme` is an internal frozen dataclass, so this is not a public-contract change.
Add to **both** `CLASSIC_THEME` and `MODERN_THEME`:

~~~python
mono_style: TextStyle           # DejaVu Sans Mono, size 11, line_height 15, muted fill
ledger_rule: str                # band rule colour        (classic: "#1b1a17")
ledger_hairline: str            # entry separator         (classic: "#ece7db")
ledger_part_draw_fill: str      # part-draw tint          (classic: "#f6f0e2")
~~~

`_scaled_theme` in `engine.py` must scale `mono_style` too, or `base_font_size` and
`minimum_font_size` will silently stop applying to half the sheet. Add it to the
`replace(...)` call alongside the existing five styles.

`TextStyle` has no italic field. Rather than add one (a second additive contract change),
render completion criteria in the muted detail style at the same size and accept upright
text. Its position at the foot of the conditions column is what carries the meaning, and
one contract change is easier to review than two.

## 4. Strategy skeleton

Mirror `compact_table.py` — same imports from `engine`, same `_Piece` pattern, same
`validate_tabular_layout` call at the end.

~~~python
class LedgerLayoutStrategy:
    """Double-entry ledger: consumed, produced, and conditions per operation."""

    def create_layout(self, graph, options, *, text_measurer=None) -> TabularLayout:
        measurer = text_measurer or default_text_measurer()
        theme = _scaled_theme(get_theme(options.theme), options)
        view = _index_graph(graph)

        folio = _folio_map(view, graph)      # material_id -> "M3" | "M3a" | "F1" | None
        entries = tuple(
            _entry_model(view, graph, op_id, index, folio, options, theme)
            for index, op_id in enumerate(view.transform_order, start=1)
        )
        # measure -> place -> emit
        layout = TabularLayout(notation="ledger", ...)
        return layout.model_copy(
            update={"diagnostics": validate_tabular_layout(layout)}
        )
~~~

### Reading the graph

Everything you need is already on `_GraphView`:

- `transform_order` — entry order. Deterministic topological sort. **Use it as-is.**
- `setup_order` — standing conditions, in authored order.
- `consumes[op_id]` — the consumed lines, in edge order. `_index_graph` already folds
  `reserves` and `optionally-applies` edges in where the material is the source, which
  is exactly right.
- `input_quantities[op_id]` — a tuple of `(material_id, quantity)` pairs: the
  **per-edge allocations**. This is the field that makes part draws exact. Do **not** use
  `_operation_input_quantity_text`; it joins everything into one "Uses:" string and
  exists for `flow` and `compact-table`.
- `produces[op_id]` — the produced lines. `reserves` and `discards` edges are
  already folded in, so held and discarded portions appear here.
- `producer[material_id]` — the folio back-reference.
- `requires[op_id]` — the standing-condition citations.
- `consumers[material_id]` — needed to detect an unclosed HELD portion.

Resolve a setup-produced dependency token through its setup producer and print the
producer's `S#` citation; do not emit a consumed material line for that token.
Setup-to-setup requirements stay in the standing-conditions band. For non-material
transform requirements and explicit `precedes` edges, derive `Requires entry n` and
`After entry n` citations from the corresponding operation folios.

### Derived facts to compute

~~~python
def _folio_map(view, graph):
    """material_id -> 'M<n>' or 'M<n><suffix>' for intermediates,
    globally numbered 'F<n>' for finals, and None for sources."""

def _ancestry(view, material_id) -> frozenset[str]:
    """Transitive source-material closure. Cycle-guarded, memoised.
    Copy the shape of compact_table._material_ancestry."""

def _material_branch_marker(view, entries) -> dict[str, str | None]:
    """'SEPARATE MATERIAL BRANCH' for disjoint material ancestry;
    'JOIN · n MATERIAL BRANCHES' when disjoint produced ancestries meet.
    This does not infer scheduling or concurrency. Never emit both."""

def _balance(view, op_id) -> str | None:
    """'300 mL = 250 mL + 50 mL' plus a checkmark when the parts sum to the total.
    Return None unless: exactly one consumed material with a quantity, two or more
    produced materials that ALL carry quantities, and all units are equal.
    Never guess, never convert units, never print a balance for a transformation."""

def _line_tag(view, op_id, material_id) -> tuple[str, str | None]:
    """(tag, allocation): ('source', None) | ('from M3', None) |
    ('part draw', '45 mL') | ('from reserve', None) | ('optional', None)"""
~~~

`_balance` is the function most likely to violate invariant 2 by being too clever. Unit
equality is a string comparison on the authored unit, not a conversion. If in doubt,
return `None` — a missing balance line is a lost nicety; a wrong one is a lie.

## 5. Registry and CLI

`strategies.py`:

~~~python
_BUILTIN_NAMES = frozenset({"flow", "compact-table", "ledger"})

def _ensure_builtins() -> None:
    if "compact-table" in _STRATEGIES and "ledger" in _STRATEGIES:
        return
    from recipeflow.layout.compact_table import CompactTableLayoutStrategy
    from recipeflow.layout.ledger import LedgerLayoutStrategy
    _STRATEGIES.setdefault("compact-table", CompactTableLayoutStrategy())
    _STRATEGIES.setdefault("ledger", LedgerLayoutStrategy())
~~~

The CLI needs **no change**: `--notation` is already typed `str`, resolved through the
registry, and an unknown name already maps to an RF512 diagnostic. Verify with:

~~~
uv run recipeflow render examples/golden/espresso-brownies.recipe.yaml \
  --notation ledger --format tabular-svg --page-size A4 --print-mode -o /tmp/l.svg

uv run recipeflow render-check examples/golden/large.recipe.yaml \
  --notation ledger --json
~~~

## 6. Print HTML per-sheet windowing

For `print_mode` with sheet breaks, emit one `section` per sheet, each containing an SVG
with the same width and a `viewBox` windowed to that sheet's y-range. Rewrite fragment ids
so every DOM id remains unique, and add a print rule that breaks after each sheet. The
accessibility ordered list stays single and complete outside the sheets. Standalone SVG
and PNG remain the **full**, continuous canvas; PNG is one image, not one per sheet.

The layout height is an exact multiple of `page_height`. The title and standing
conditions appear only on page one, column headings repeat on later pages, and each
non-final page ends with the exact material frontier. An entry moves intact when it fits;
an oversized entry splits between leaf cells, repeats a print-only continued head, and
exposes all fragment ids through `OperationCell.box_ids`. If a leaf cannot fit, record
RF508 and do not clip it.

## 7. Strategy diagnostics

The ledger strategy appends RF506-RF508 directly to `TabularLayout.diagnostics`.
`render_check` merges those diagnostics with the generic diagnostics returned by
`validate_tabular_layout`; the generic validator does not attempt to reconstruct ledger
semantics.

## 7. Things not to do

- Do not reorder materials or entries to make geometry work. The ledger has no spans;
  `compact-table`'s `_source_material_ids` reordering has no analogue here and would
  break dependency reading order.
- Do not add a second measurement pass. Height is a running sum; if you find yourself
  negotiating, the model is wrong.
- Do not put layout logic in the renderers.
- Do not let PNG compute anything.
- Do not print a balance line the graph does not license.
- Do not turn a materially separate branch into a concurrency claim.
