# 03 — Expressing the ledger in `recipeflow.tabular-layout/v1`

The renderers must not learn anything new about the ledger beyond CSS. Everything is
carried by the existing contract.

## 1. `TabularLayout` field usage

| Field | Ledger meaning |
| --- | --- |
| `notation` | `"ledger"` |
| `width` / `height` | resolved canvas |
| `label_width` | consumed column width (closest existing analogue) |
| `header_height` | title band + rule |
| `setup_height` | standing-conditions band + double rule; `0` when absent |
| `row_height` | `max(entry_h)` — reported for parity, not used for layout |
| `lanes` | one `Lane` per **entry**: `index` = entry ordinal, `y` = entry-head centre, `height` = `entry_h`, `initial_material_id` = the entry's first produced material |
| `materials` | one `MaterialSegment` per material occurrence; see section 2 |
| `operations` | one `OperationCell` per transform entry, `rect` = the whole entry, `y1`/`y2` = entry top/bottom, `x` = `content_x`, `orientation="horizontal"` |
| `setup` | one `SetupCard` per standing-conditions row, full content width |
| `final_material_ids` | unchanged from the graph |
| `reading_order` | see section 5 |
| `paths` | sheet breaks only (`kind="guide"`, `style_class="sheet-break"`). **The ledger routes no material lines** — `paths` is otherwise empty, which is the point of the notation. Page boundaries remain self-contained in these guides; there is no `sheets` field. |

## 2. `MaterialSegment`

Reuse it as the machine-readable record of each occurrence:

~~~
material_id       the material
label             its label
quantity          the ALLOCATION for this occurrence (edge quantity if present,
                  else the material's authored quantity) - not always the total
role              MaterialNode.role, or "reserved" for a held portion
lane              the entry ordinal it occurs in
x1, x2            the leaf cell's left and right edge
y                 the line's vertical centre
show_left_label   True for a consumed line, False for a produced line
~~~

A part-drawn material therefore produces two `MaterialSegment` entries with different
`quantity` values and different `lane`s. That is what makes the allocation black-box
probe machine-checkable.

## 3. Boxes — the invariant that matters most

`validate_tabular_layout` raises **RF505** when two `opaque` boxes intersect, and the
visual corpus test asserts every text block is contained by its `parent_id` box. So:

- **Leaf cells are the only opaque boxes.** One per consumed line, per produced line, per
  conditions block, per standing-conditions row, per band heading.
- **The entry box is `opaque=False`**, `collision_group="entry"`, and exists only to
  give `OperationCell.rect` something to point at — exactly how `compact-table` treats
  its title box.
- Every `TextBlock.parent_id` is the **leaf cell** it sits in, and its rect is fully
  inside that cell.

Emitting the entry box as opaque *and* the cells as opaque is the one mistake that will
fail the corpus test on every fixture.

### Box kinds — no new values needed

| Ledger element | `LayoutBoxKind` | `style_class` |
| --- | --- | --- |
| entry frame (non-opaque) | `operation` | `ledger-entry` |
| consumed line cell | `ingredient` | `ledger-consumed` |
| consumed line cell, part draw | `ingredient` | `ledger-consumed-part` |
| produced line cell | `material-label` | `ledger-produced` |
| produced line cell, final | `final-output` | `ledger-final` |
| conditions block | `annotation` | `ledger-conditions` |
| standing-conditions row | `setup` | `ledger-standing` |
| band heading / carried-forward | `annotation` | `ledger-band` |

## 4. Text roles — the one schema decision

Map onto existing `TextRole` values wherever they already mean the right thing:

| Ledger text | `TextRole` |
| --- | --- |
| recipe title | `title` |
| yield | `recipe-yield` |
| entry number + action | `operation-action` |
| consumed quantity cell | `operation-input-quantity` |
| consumed label, source ingredient | `ingredient-label`, or `ingredient-source` when `show_source_quantities` and `source_text` exists |
| consumed label, intermediate | `material-label` |
| preparation / temperature state | `ingredient-preparation` |
| produced folio + label | `material-label` |
| produced label, final | `final-label` |
| duration / temperature / repeat | `operation-detail` |
| completion criteria | `operation-until` |
| standing-condition citation | `setup-required-by` |
| standing-conditions row parts | `setup-label`, `setup-target`, `setup-detail`, `setup-note` |
| provenance | `ingredient-provenance` / `setup-provenance` |
| tags, band headings, carried-forward, ambiguity footnote | `annotation` |

**One new public role: `allocation-balance`** for the split balance line. It makes the
black-box allocation-arithmetic probe machine-checkable. Per
`docs/SCHEMA-VERSIONING.md`, this additive enum member is permitted inside the existing
contract major version: it removes no field and changes no existing meaning. It must be:

1. added to `TextRole` in `models/layout.py`;
2. regenerated: `make schemas`, then `make schema-check` and `make types-check`;
3. recorded in `CHANGELOG.md` as a backward-compatible contract addition;
4. documented in `docs/LAYOUT-ENGINE.md`.

## 5. `reading_order`

This doubles as the accessibility linearisation and the HTML ordered list. Order:

~~~
title, yield,
standing-conditions heading, then per condition:
    label, target, detail, required-by, notes
column headings (consumed, produced, conditions),
then per entry in transform_order:
    entry number + action, separate-material-branch/join tag,
    each consumed line: quantity, label, state, tag,
    balance line (if any),
    each produced line: folio, label, tag,
    conditions: duration, temperature, repeat, citations, criteria,
    ambiguity footnotes
carried-forward band
~~~

Repeated headings after a sheet break are **excluded** from `reading_order` — they are
print furniture, and repeating them would make a screen reader read the recipe's structure
twice.

## 6. Identifier scheme

Follow the `compact-table` convention exactly; ids must be unique or RF500 fires.

~~~
box:ledger:entry:<op_id>
box:ledger:consumed:<op_id>:<material_id>
box:ledger:produced:<op_id>:<material_id>
box:ledger:conditions:<op_id>
box:ledger:standing:<setup_op_id>
box:ledger:band:<band_name>
box:ledger:rule:<band_name>:<ordinal>

text:ledger:entry:<op_id>:action
text:ledger:consumed:<op_id>:<material_id>:{quantity|label|state|tag}
text:ledger:produced:<op_id>:<material_id>:{folio|label|tag}
text:ledger:conditions:<op_id>:{duration|temperature|repeat|requires:<n>|until}
text:ledger:balance:<op_id>
text:ledger:standing:<setup_op_id>:{label|target|detail|required|note:<n>}
text:ledger:band:<band_name>:<slot>

path:ledger:sheet-break:<ordinal>
~~~

## 7. SVG style classes

Add to `_style()` in `renderers/svg.py`. Greyscale-safe: distinctions are weight and
rule presence, never hue alone.

~~~
.ledger-entry         { fill:none; stroke:none }
.ledger-consumed      { fill:none; stroke:none }
.ledger-consumed-part { fill:<theme.setup_fill>; stroke:none }
.ledger-produced      { fill:none; stroke:none }
.ledger-final         { fill:none; stroke:<theme.final_stroke>; stroke-width:1 }
.ledger-conditions    { fill:none; stroke:none }
.ledger-standing      { fill:none; stroke:none }
.ledger-band          { fill:none; stroke:none }
.ledger-rule          { fill:<theme.text>; stroke:none }
.sheet-break          { fill:none; stroke:<theme.setup_stroke>; stroke-width:1;
                        stroke-dasharray:6 4 }
~~~

Draw rules and separators as thin filled `LayoutBox` rects with `opaque=False` and
`style_class="ledger-rule"` rather than as paths. Paths are validated against the canvas
including `stroke_width / 2` (RF504) and would need inset special-casing at the margins;
a 1 px-high rect does not.

Also extend the notation-aware background in `render_tabular_svg`:

~~~python
background = selected.background or (
    theme.table_background
    if layout.notation in {"compact-table", "ledger"}
    else theme.background
)
~~~
