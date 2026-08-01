# 06 — Worked examples

Numbers to assert against. All at `RenderOptions(notation="ledger", theme="classic",
page_size="A4", print_mode=True)`, giving `preferred_width=794`, `safe_margin=40`,
`content_width=696`, columns 333 / 187 / 174.

## 1. `espresso-brownies` — the baseline

Standing conditions (2): `S1` preheat the oven, target oven, 170 C, held for entry 5;
`S2` butter and flour an 8 x 8 inch baking pan, held for entry 5.

| # | Action | Consumed | Produced | Conditions |
| --- | --- | --- | --- | --- |
| 1 | melt | `115 g` unsalted butter *(source)* | `M1` melted butter | — |
| 2 | mix | `all` melted butter *(from M1)*; `200 g` granulated sugar; `2.5 mL` vanilla extract; `60 mL` freshly brewed strong espresso | `M2` glossy espresso mixture | — |
| 3 | whisk | `all` glossy espresso mixture *(from M2)*; `2` large eggs | `M3` aerated wet batter | — |
| 4 | fold | `all` aerated wet batter *(from M3)*; `80 g` all-purpose flour; `80 g` Dutch-process cocoa powder; `1.3 g` baking soda; `1.5 g` fine sea salt | `M4` espresso brownie batter | — |
| 5 | bake | `all` espresso brownie batter *(from M4)* | `F1` **FINAL** sixteen fudgy espresso brownies | Time 30 to 40 min; Oven 170 C; S1 heated oven; S2 prepared pan; until a tester emerges with moist crumbs but no raw batter |

Assertions:

- 5 `OperationCell`s, 5 `Lane`s, 2 `SetupCard`s.
- 13 `MaterialSegment`s with `show_left_label=True` (1 + 4 + 2 + 5 + 1), matching the
  graph's 13 consumes edges exactly.
- 9 of those reference source materials; 4 reference intermediates.
- `paths` is empty — no sheet break is needed and no material line is ever routed.
- Entry 4 has the tallest body: 5 consumed lines, so `entry_h = 24 + 5 * 19 = 119` before
  measurement growth.
- Entry 5's conditions column is the tallest single column on the sheet: two mono lines, a
  two-line prerequisite box, and a wrapped criteria sentence.
- `setup_height > 0`; `label_width == 333`.
- Zero `allocation-balance` blocks. No operation here is a split.

## 2. `split-and-reserve` — the allocation case

Entry 1, `divide` (`operation_type: split`):

~~~
consumed:   300 mL   cold heavy cream                          source
            ----------------------------------------
            300 mL = 250 mL + 50 mL    balanced        <- allocation-balance
produced:   M1a  250 mL  cream for the mousse base
            M1b   50 mL  reserved cream for the final rosette   HELD
conditions: -
~~~

Entry 4, `portion and garnish`, consumes `all` airy dark chocolate mousse *(from M3)*
and the held portion *(from reserve)*, producing `F1` **FINAL** six chocolate mousse
glasses with reserved-cream rosettes.

Assertions:

- Exactly one `allocation-balance` text block in the whole layout.
- `MaterialSegment(material_id="reserved-cream")` appears twice: once produced with
  `role="reserved"` and `quantity="50 mL"` in lane 0, once consumed in lane 3.
- No balance line on entries 2, 3 or 4 — `melt`, `whip and fold` and
  `portion and garnish` are transformations, and mass is not conserved.

## 3. `multiple-outputs` — co-products

The `divide and finish` entry produces two lines in one produced column, each with a
boxed `FINAL` tag: churned vanilla bean ice cream, and chilled vanilla creme anglaise for
pouring. Two `final-label` text blocks whose parent cells share one lane index — never
two entries.

## 4. `large` — the scaling case

16 ingredients, 12 operations, 4 standing conditions, four independent branches, a
four-way join, and one source drawn twice.

Sheet 1 carries entries 1 to 7 and closes with:

~~~
OPEN AT THE FOOT OF SHEET 1 - M7 tender spiced chicken braise ;
<every other produced output still needed by an entry on sheet 2>
<every still-open HELD portion>                               CARRIED FORWARD
~~~

The four facts this fixture must prove:

1. **Allocation survives.** `neutral cooking oil` yields two consumed lines — `45 mL`
   in entry 4 and `30 mL` in entry 5 — each with "of 75 mL authored". Read from
   `view.input_quantities`, not from the material's total.
2. **Material independence survives without a scheduling claim.** Entry 3 (`combine
   aromatics`) has materially disjoint ancestry and is tagged `SEPARATE MATERIAL BRANCH`.
   Entry 7 (`braise chicken`) cites `M4` and `M6` from disjoint ancestries and is tagged
   `JOIN · 2 MATERIAL BRANCHES`. Entry 12 (`layer and finish`) cites four materially
   disjoint folios and is tagged `JOIN · 4 MATERIAL BRANCHES`.
3. **Prerequisites stay out of the food.** `S1` (hot skillet) is cited by entries 1, 4
   and 11 and consumed by none. It never appears in a consumed column.
4. **Pagination is honest.** Height at A4 is roughly 1.4 sheets. Entries move intact when
   possible, and the sheet closes with the exact material frontier: produced outputs
   needed later plus still-open `HELD` portions. The fully drawn oil source is excluded.

Entry 12 is the deepest conditions column in the corpus: an `S4` citation plus a
four-clause criteria sentence that wraps to three lines at 174 px. It is the fixture most
likely to expose a fixed-height regression.

## 5. Degenerate cases to check by hand

| Case | Expected |
| --- | --- |
| No setup operations (`compact`) | Standing-conditions band and its double rule are **omitted entirely**; `setup_height == 0`. Do not emit an empty band. |
| A single operation | Title band, column headings, one entry, no carried-forward band. |
| An operation with no consumed lines | Consumed column renders one `annotation` line reading "no direct inputs". Never an empty cell — absence must be stated, per invariant 1's corollary. |
| An operation with no conditions | Conditions column is an empty leaf cell with no text blocks. Legal; the column separators still draw. |
| A material consumed by two operations | Two consumed lines in two entries, each with its own allocation. No line is drawn between them; the folio reference is the whole mechanism. |
| `show_provenance=True` | One muted provenance line under each material that has provenance. Entry grows. |
| `show_source_quantities=False` with `show_normalized_quantities=True` | Quantity cell prints the normalized quantity. `RenderOptions` already rejects both being false. |
| A graph with an empty `transform_order` | Title band, no entries, no carried-forward band, and a single `annotation` line reading "no operations". Must not raise. |
