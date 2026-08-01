# 02 — Resolved geometry

All values are CSS px in the layout coordinate system, matching how `flow` and
`compact-table` already work. The reference drawing was made at A4 portrait
(794 x 1123, `safe_margin` 40) — those are the numbers below. Everything is expressed as
a ratio or an option so other widths resolve deterministically.

## 1. Canvas

~~~
canvas_width    = max(preferred_width or intrinsic_width, intrinsic_width)
intrinsic_width = LEDGER_MIN_CONTENT_WIDTH + 2 * safe_margin      # 640 + 2m
content_width   = canvas_width - 2 * safe_margin
content_x       = safe_margin
content_height  = last_band_bottom + safe_margin
canvas_height   = content_height                                  # screen mode
canvas_height   = ceil(content_height / page_height) * page_height # print mode
~~~

`RenderOptions(page_size="A4", print_mode=True)` already yields `preferred_width=794`.
With `safe_margin=40`, `content_width = 696`.

Unlike `flow`, ledger width does **not** grow with operation count. A requested width
narrower than `intrinsic_width` is ignored (same policy as the other strategies: a
requested width is a preference, not a destructive maximum).

## 2. Three columns

Fractions of `content_width`, then floored:

| Column | Fraction | At 696 | Minimum |
| --- | --- | --- | --- |
| consumed | 0.4785 | 333 | 260 |
| produced | 0.2687 | 187 | 150 |
| conditions | 0.2500 | 174 | 140 |

~~~
consumed_x   = content_x
produced_x   = consumed_x + consumed_w
conditions_x = produced_x + produced_w
~~~

Separators: 1 px vertical hairline at `produced_x` and `conditions_x`, drawn for the
height of the entry body only (not the entry head). Inner padding 12 px on the produced
and conditions columns; the consumed column pads 12 px on the right only.

**Quantity sub-column** inside `consumed`: fixed 58 px, right-aligned, mono, followed by
an 8 px gap. It must not shrink — it is what makes the quantities scannable as a column.
Label width = `consumed_w - 58 - 8 - 12 - tag_width`.

## 3. Vertical band order

~~~
y = safe_margin
 |- title band              title (measured) + 4 + yield (measured) + 12
 |- rule                    1 px full content width, theme.text
 |- standing-conditions band    (omitted entirely when setup_order is empty)
 |     heading              12 px mono label + 6
 |     n rows               24 px each, 1 px hairline between
 |- double rule             1 + 1 px with a 1 px gap  (3 px)
 |- column-heading band     16 px mono labels + 4
 |- rule                    1 px
 |- entries                 see section 4; 1 px hairline between, 6 px gap
 |- double rule             3 px
 |- carried-forward band    7 + 11 + 4 + 11
 |- canvas bottom           + safe_margin
~~~

Row heights grow if measured text needs it; the constants are minima.

## 4. Entry height

~~~
entry_head_h = 24                       # number chip 17px + baseline slack
line_h       = 19                       # one consumed or produced line, MINIMUM
entry_body_h = max(consumed_h, produced_h, conditions_h)
entry_h      = entry_head_h + entry_body_h
~~~

Each column's height is the sum of its own measured line heights — the three columns flow
**independently**, they are not a grid:

~~~
consumed_h   = sum(max(line_h, measured(line)) for line in consumed_lines)
             + (balance_line_h if split else 0)
produced_h   = sum(measured(line) for line in produced_lines) + 6 * (n - 1)
conditions_h = duration_h + temperature_h + repeat_h
             + (prereq_box_h if requires else 0)
             + criteria_h
             + gaps
~~~

**Critical:** a consumed line's height is `max(19, measured_height)`, never a fixed 19.
A wrapping label must grow its line, per invariant 7. This was the single defect found
when the reference drawing was validated — a fixed-height row let a wrapped label overlap
the line below.

Prerequisite sub-region inside `conditions`: 1 px rule above and below, 4 px padding,
one 16 px line per citation.

## 5. Rules and weights

| Element | Weight | Theme token |
| --- | --- | --- |
| Band rule | 1 px | `theme.text` |
| Double rule | 1 + 1 px, 1 px gap | `theme.text` |
| Entry separator | 1 px | `theme.guide` |
| Column separator | 1 px | `theme.material_stroke` |
| Standing-condition row separator | 1 px | `theme.guide` |
| Sheet break | 1 px, dashed 6 4 | `theme.setup_stroke` |

Corner radius is **0** everywhere. `FINAL` / `HELD` / `WASTE` tag boxes are 1 px
rectangles with 3 px horizontal padding.

## 6. Typography

Resolved from `_scaled_theme(get_theme(theme), options)`, so `base_font_size` and
`minimum_font_size` keep working:

| Slot | Style |
| --- | --- |
| Title | `theme.title_style` |
| Yield | `theme.quantity_style` |
| Entry action | `theme.label_style` at weight 600, size x 1.07 |
| Entry number chip | `theme.detail_style`, mono, in a 17 px 1 px-bordered square |
| Consumed / produced label | `theme.label_style` x 0.9 |
| Quantity cell, tags, folio ids, mono metadata | `theme.detail_style`, mono family |
| Completion criteria | `theme.detail_style` |
| Band headings | `theme.detail_style`, mono, letter-spacing 0.13em, uppercase |

Mono family: add `mono_style` to `LayoutTheme` (see `04-IMPLEMENTATION.md` section 3)
with `font_family="DejaVu Sans Mono"` and the same fallback discipline as `TextStyle`.
Do not hard-code a family in the strategy.

## 7. Sheet breaks (pagination)

Height is unbounded, so a long recipe exceeds one printed page. The rule:

~~~
sheet_h  = page_height
usable_h = sheet_h - 2 * safe_margin - repeated_header_h - carried_forward_h
~~~

The page dimensions are fixed: A4 is 794 x 1123 portrait or 1123 x 794 landscape;
letter is 816 x 1056 portrait or 1056 x 816 landscape. `print_mode=True` with automatic
page size defaults to A4 portrait. The continuous layout height is an exact multiple of
`page_height`. Screen mode passes no page height and emits no sheet breaks.

Entries are **atomic when they fit**: an entry that would cross a sheet boundary moves
whole to the next sheet. An oversized entry splits only between semantic leaf cells,
repeats its head as "n (continued)", and records every fragment in the associated
`OperationCell.box_ids`. If one leaf cell is itself taller than the usable page area,
pagination reports RF508 rather than clipping it.

Each break emits:

1. a `RoutedPath` of kind `guide`, `style_class="sheet-break"`, two points spanning
   `content_width`;
2. a **carried-forward band** above the break naming the material frontier: every produced
   output needed by a later entry plus every still-open `HELD` portion, so the next sheet
   reads without the previous one in hand. A fully consumed source or intermediate is not
   carried forward;
3. a repeat of the column-heading band below the break.

The layout stays **one continuous canvas** and does not add a `sheets` field. Standalone
SVG and PNG cover that entire multi-sheet canvas. The HTML renderer in `print_mode`
windows it into one SVG section per sheet, with unique DOM ids, a single accessibility
list, and print page-break CSS (see `04-IMPLEMENTATION.md` section 6). This keeps PNG
derived from the same geometry.

`LayoutOptions.page_height` is either passed directly or derived by `RenderOptions` from
`page_size` and `orientation`. When `print_mode` is false, `page_height` is `None` and the
ledger emits no sheet breaks.

## 8. Determinism

Every `y` is a running sum of measured text heights. There is no routing, no overlap
resolution, no centring of one object on another, and **no iteration** — unlike
`compact-table`, which negotiates run heights in a second pass. Given the same graph,
font metrics and options, the layout JSON and SVG bytes are identical. Round every emitted
coordinate with `round(value, 3)`, matching the other strategies.
