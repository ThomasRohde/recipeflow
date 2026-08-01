# 01 — Notation semantics

Read this before the geometry. Every number in `02-GEOMETRY.md` exists to serve one of
the rules here.

## 1. Premise

The recipe is a double-entry ledger. Each transform operation is a numbered **entry**.
Everything the entry consumes is enumerated on the left; everything it produces is
enumerated on the right; the conditions under which it happens are in a third column,
ruled off from both.

## 2. Reading direction

Top to bottom in dependency order (`_GraphView.transform_order`, which is already a
deterministic topological order). Within an entry: left (consumed) then right (produced),
with conditions last. There is no other reading direction, and the visual order **is** the
accessibility reading order — `reading_order` and the HTML ordered-list fallback are the
same sequence a sighted reader follows.

## 3. Semantic mapping

| Graph fact | Visual expression |
| --- | --- |
| Source ingredient (`MaterialNode` with no producer) | A consumed line: right-aligned quantity in a fixed mono sub-column, then label, then preparation / temperature state, tagged `source`. |
| Setup prerequisite (`operation_kind == "setup"`) | A row in the **standing-conditions band** above the entries, lettered `S1..Sn`, showing target, temperature, duration, and the entries that require it. Cited inside an entry only as `S1`, `S2`, and so on in the conditions column, inside a hairline-boxed sub-region. A token produced by a setup operation resolves back to that `S#`; it is never rendered as food or as a consumed line. |
| Setup-to-setup requirement | A standing-condition row names the earlier `S#` it requires; the relationship stays in the standing-conditions band. |
| Transform operation | One numbered entry. The number is the **folio** every later reference uses. |
| Transform requirement | A non-material requirement on another transform is printed `Requires entry n` in the conditions column. An explicit `precedes` edge is printed `After entry n` on the later entry. Neither relationship is rendered as consumed material. |
| Intermediate material | A produced line whose folio is derived from its producing entry. A single output from entry 1 is `M1`; multiple non-final outputs from that entry are `M1a`, `M1b`, and so on in deterministic graph order. |
| Direct input | Its own consumed line. An operation consuming one intermediate and four sources shows **five** lines. |
| Full consumption | The quantity cell reads `all`. |
| Partial draw (`consumes` edge with `quantity`) | The quantity cell reads the allocation; the label is followed by `of <authored total> authored`. Both numbers are always present. |
| Split (one input, several outputs with quantities) | One consumed line, several produced lines each carrying its authored quantity, plus a **balance line** under the consumed column. |
| Reserved portion (`role: reserved` / `reserves` edge) | A produced line tagged `HELD`. It stays open until an entry cites it `from reserve`. |
| Separate material branch | An entry whose produced-material ancestry is disjoint from the earlier open material branch is marked `SEPARATE MATERIAL BRANCH`. This states graph ancestry only; it makes no claim that the operations can run concurrently. Source-only entries are compared by source ancestry as well as folio references. |
| Join | A single entry citing two or more produced folios from disjoint material ancestries is marked `JOIN · n MATERIAL BRANCHES`. |
| Duration (`OperationNode.duration`) | `Time <range>` in the conditions column, mono, authored range preserved (30 to 40 min, never 35 min). |
| Temperature | `Oven <value>` / `Heat <value>` in the conditions column, mono. |
| Repetition (`RepeatSpec`) | `Repeat <k v>` in the conditions column, after temperature. |
| Completion criteria (`until`) | Sentence at the foot of the conditions column, always complete, wrapping freely — the entry grows. |
| Final output | A produced line with a boxed `FINAL` tag and folio `F1, F2`. Several finals from one entry are several boxed lines in the same produced column. |
| Waste / garnish | Produced lines tagged `WASTE` / `GARNISH`. |
| Ambiguity (`Ambiguity`) | A footnoted line under the entry, prefixed with a question mark, carrying the description and any alternatives. |
| Provenance | Only when `show_provenance`; a muted line under the material it belongs to. |

## 4. The seven invariants

These are the acceptance criteria. Each maps to a test in `05-TESTS.md`.

1. **No implied membership.** An ingredient appears in an entry only if a `consumes` /
   `reserves` / `optionally-applies` edge connects it to that operation. There is no
   device in this notation that spans rows, so there is nothing that *can* imply
   membership — but the corollary is binding: **never draw an opaque box that encloses
   more than one leaf cell.** See `03-LAYOUT-CONTRACT.md` section 3.
2. **Exact allocations.** A partial draw prints the allocation and the authored total.
   A split prints every portion and a balance line. Nothing is rounded, summed, or
   inferred.
3. **Reserves stay open.** A reserved portion is tagged `HELD` and the sheet's
   carried-forward band names it until an entry consumes it.
4. **Material branches stay separate.** No entry implies a material dependency it does
   not have; `SEPARATE MATERIAL BRANCH` and `JOIN · n MATERIAL BRANCHES` are computed
   from transitive material ancestry, not from adjacency, authored position, or possible
   concurrency.
5. **Setup is not material.** A setup prerequisite can only ever appear in the
   standing-conditions band or as a bracketed citation in the conditions column. It never
   receives a quantity cell and never appears in the consumed column, at any size. Any
   material token emitted solely to carry a setup dependency resolves back to its `S#`.
6. **Direct inputs survive.** An operation consuming an intermediate still enumerates its
   source ingredients as separate lines. Nothing is absorbed.
7. **No truncation.** `allow_ellipsis` defaults `False`; long text increases entry
   height. A `TextBlock.overflow` is a layout failure (RF501), not a styling choice.

## 5. Tag vocabulary

Tags are short mono strings in the muted style, right-aligned in their column. They are
part of the notation, not the theme, and must render identically in greyscale.

| Tag | Column | Meaning |
| --- | --- | --- |
| `source` | consumed | this line is an authored source ingredient |
| `from Mn` | consumed | this line is the intermediate produced by entry n |
| `part draw` | consumed | this line consumes only part of the material |
| `from reserve` | consumed | this line consumes a previously held portion |
| `optional` | consumed | `optionally-applies` edge or `MaterialNode.optional` |
| `HELD` | produced | reserved portion, not yet consumed |
| `FINAL` | produced | final output (boxed) |
| `WASTE` / `GARNISH` | produced | `discards` edge / garnish role |
| `S1` citation | conditions | standing condition required by this entry; setup-produced tokens resolve to this citation |
| `balanced` | consumed | the split's portions sum to the authored total |

## 6. What the notation deliberately cannot show

State these in `docs/TABULAR-NOTATION.md` so nobody expects them:

- **Scheduling or concurrency.** The material-branch tags describe ancestry only. They do
  not assert that two operations can overlap in time or that resources permit parallel
  execution.
- **Elapsed time.** Durations are per-entry facts, not positions on an axis.
- **Mass conservation across transformation.** A balance line is printed **only** for
  splits and allocations, where the graph authorises the arithmetic. Baking does not
  conserve mass; the renderer must never print a balance line where the graph does not
  license one.

## 7. Theme vs notation

The notation owns: column order and widths, line heights, rule weights, the quantity
sub-column, band order, the tag vocabulary, and every glyph. A theme may change type
family, ink, paper, rule colour, and the optional tint behind a part-draw line — the tint
is decoration; the "of 75 mL authored" text is the meaning and is present with or without
it.
