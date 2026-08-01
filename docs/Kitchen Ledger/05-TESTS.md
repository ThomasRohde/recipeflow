# 05 — Tests, diagnostics, and evaluation

## 1. Golden visual corpus

Generate all 12 existing fixtures under the new notation. They are already the right
stress set:

| Fixture | What it proves for the ledger |
| --- | --- |
| `espresso-brownies` | baseline; 5 entries, 2 standing conditions, 1 final |
| `split-and-reserve` | balance line, HELD, from reserve |
| `multiple-outputs` | two FINAL lines from one entry |
| `branch-and-join` | SEPARATE MATERIAL BRANCH and JOIN tags from material ancestry |
| `setup-heavy` | standing-conditions band, many citations |
| `large` | 12 entries, 4 conditions, part draws 45/30 of 75 mL, four-way join, pagination |
| `long-text`, `long-completion-criteria` | entry growth, invariant 7 |
| `many-narrow-operations` | many short entries |
| `measurement-systems` | quantity sub-column alignment across unit systems |
| `unicode` | grapheme wrapping in the label column |
| `compact` | minimal graph; degenerate bands |

~~~
uv run python scripts/generate_visual_corpus.py --notation ledger
uv run python scripts/generate_visual_corpus.py --notation ledger --check
~~~

The generator rejects unexpected layout diagnostics, so a broken ledger cannot be
committed. Fixtures intentionally exercising RF506-RF508 assert their diagnostics
directly rather than entering the clean golden corpus.

## 2. `tests/visual/test_ledger_corpus.py`

Copy `test_compact_table_corpus.py` and keep its structural assertions verbatim
(notation, empty `validate_tabular_layout`, canvas containment with no overflow, no
opaque overlap, parent containment, SVG viewBox equals the canvas, PNG size equals
`layout x scale`). Then add ledger-specific tests:

~~~python
def test_no_material_paths_are_routed():
    """The ledger's whole premise: participation is a line of text, not a line.
    Only sheet-break guides may appear in paths."""
    assert all(p.style_class == "sheet-break" for p in layout.paths)

def test_setup_never_appears_as_a_consumed_line():
    """Invariant 5. For every setup operation and every material it produces,
    assert no MaterialSegment with show_left_label=True references it."""

def test_every_consumed_edge_has_exactly_one_line():
    """Invariants 1 and 6. Build the expected (op, material) set from the graph's
    consumes / reserves / optionally-applies edges and assert it EQUALS the set of
    MaterialSegments with show_left_label=True. Equality, not containment:
    catches both invented inputs and absorbed ones."""

def test_part_draws_carry_the_allocation_and_the_total():
    """Invariant 2, on large. Two segments for the oil material with quantities
    '45 mL' and '30 mL', and both consumed-label source_texts mention '75 mL'."""

def test_split_balance_line_is_present_and_exact():
    """On split-and-reserve: exactly one allocation-balance text block whose
    source_text contains '300 mL', '250 mL' and '50 mL'."""

def test_no_balance_line_on_transformations():
    """Invariant 2's negative half. On espresso-brownies, zero allocation-balance
    blocks: no operation there is a split."""

def test_reserved_portion_is_tagged_and_later_consumed():
    """Invariant 3: a segment with role='reserved', and a later lane consuming it."""

def test_multiple_finals_share_one_entry():
    """On multiple-outputs: two final-label blocks whose parent cells sit in the
    same lane index."""

def test_reading_order_is_entry_order():
    """reading_order restricted to operation-action blocks must equal
    view.transform_order. This is the accessibility contract."""

def test_entry_lines_never_overlap_vertically():
    """Regression for the fixed-height defect: within one column, consecutive line
    cells must not intersect. Cheapest guard against invariant 7 regressing."""

def test_no_opaque_box_encloses_two_leaf_cells():
    """Invariant 1's corollary. For every opaque box, assert it contains no other
    box's rect. Directly prevents the compact-table false-span failure mode."""

def test_carried_forward_band_equals_material_frontier():
    """At every break, list exactly the outputs consumed later plus open HELD portions;
    exclude fully consumed source and intermediate materials."""

def test_page_windows_cover_every_entry_once():
    """Every unsplit entry appears in one window; split entries' leaf fragments cover
    the entry exactly once and are exposed by OperationCell.box_ids."""

def test_print_html_ids_are_unique_and_accessibility_is_single():
    """Repeated sheet furniture never duplicates a DOM id or the ordered fallback."""

def test_png_is_the_full_continuous_canvas():
    """PNG dimensions equal the exact-multiple layout canvas, not one page window."""
~~~

Mark the module `pytestmark = pytest.mark.visual` like its sibling.

## 3. Registry and determinism tests

In `tests/test_layout_strategies.py`:

- `"ledger" in list_layout_strategies()`
- `get_layout_strategy("ledger")` returns a `LedgerLayoutStrategy`
- `register_layout_strategy("ledger", ...)` raises — built-ins are not replaceable
- `create_tabular_layout(graph, LayoutOptions(notation="ledger")).notation == "ledger"`
- byte-identical layout JSON across two calls
- a graph built from reordered mapping input produces identical output
- layout does not mutate the graph (compare a serialised copy before and after)

## 4. New diagnostics

RF5xx is the layout family; RF500 to RF505 are taken.

| Code | Severity | Condition |
| --- | --- | --- |
| `RF506` | error | A consumed line is a partial draw but no allocation quantity is available to print. Violates invariant 2. |
| `RF507` | warning | A material tagged `HELD` is produced but remains unconsumed at the end of the ledger. |
| `RF508` | error | Safe pagination is impossible, including when one semantic leaf is taller than the usable page area. The renderer must not clip it. |

These are **strategy diagnostics** emitted into `TabularLayout.diagnostics` by the ledger
strategy. `render_check` merges them with generic geometry diagnostics. Document them in
`docs/LAYOUT-ENGINE.md` and `CHANGELOG.md`.

## 5. Black-box PNG reconstruction probes

Extend `evals/png-blackbox`. A viewer sees only the PNG and reconstructs the graph; each
probe is written so a specific wrong answer indicts a specific visual device.

| Probe | Ask | A wrong answer proves |
| --- | --- | --- |
| Membership census | "List every material entering fold, and nothing else." | A false positive means something was read as an enclosure — the highest-severity failure. Score precision separately from recall. |
| Negative membership | "Does vanilla extract enter fold? yes / no / cannot tell." Six near-miss pairs per fixture. | "Cannot tell" is a defect: the notation is obliged to state absence. |
| Allocation arithmetic | "How much of the 75 mL of oil enters each of the two operations, and how much remains?" | Returning the total instead of the draw means the part-draw form failed. A correct total with wrong parts is the exact failure mode of today's compact-table. |
| Setup discrimination | "Name every physical ingredient." | A skillet in the list means the standing-conditions band is not separate enough. |
| Material branch and join | "Which entries begin separate material branches, and which entry first consumes results from more than one branch?" | A join named too early means materially disjoint ancestry was shown as merged; the probe makes no scheduling claim. |
| Direct-input survival | "How many separate things go into this step?" on fold (5) and layer-and-finish (4). | An undercount means an intermediate absorbed the direct sources. |
| Output inventory | "How many finished things does this recipe produce, and name each." on multiple-outputs. | One output means co-products collapsed; two operations means the co-product form was read as sequence. |
| Termination criterion | "How do you know when bake is finished?" | A time-only answer means the criterion is subordinate to the duration in the visual hierarchy. |
| Round-trip re-emission | "Write this back as RecipeFlow YAML." Diff node sets, edge sets, quantities, requires-edges, durations, criteria, finals. | The aggregate score, and machine-checkable — it can gate a release rather than inform one. |
| Greyscale and 1-bit parity | Run the whole suite on the same layout rasterised full-theme, desaturated, and thresholded at 300 dpi. Scores must be statistically indistinguishable. | Any gap is a colour dependency the theme smuggled into the notation. Cheap: same SVG, three rasterisations. |
| Truncation and tiling audit | Mechanical, not a viewer probe: every authored string appears in full in the SVG text layer; a paginated render reproduces every entry exactly once. | Catches what a viewer cannot report — silent ellipsis, or an entry lost at a sheet boundary. |

**Report per-probe rates, never one number.** A notation at 95% round-trip fidelity with a
20% membership false-positive rate is worse than one at 85% and 2% — over-reading is the
failure that puts raw flour in a batter.

Add adversarial fixtures for: an intermediate plus six direct sources; multiple non-final
outputs from one entry (`M1a`, `M1b`); an explicit `precedes` edge; resolution of a
setup-produced token to `S#`; an oversized entry that can split between leaf cells; and a
single unsplittable leaf that must emit RF508.

Run the 12 A4 portrait PNGs in color, greyscale, and 1-bit 300-DPI variants: 36 fresh
PNG-only reconstructions and two independent judgments per image. Report separate rates
for membership precision/recall, allocation arithmetic, setup discrimination,
branch/join interpretation, direct-input survival, output inventory, completion criteria,
and round-trip equivalence. The release gate requires zero false-positive memberships,
exact targeted allocations and outputs, 2/2 equivalence votes for every image, and no
degradation in greyscale or 1-bit output. Preserve failed runs; a reproducible semantic
failure drives a renderer fix and an entirely fresh run.
