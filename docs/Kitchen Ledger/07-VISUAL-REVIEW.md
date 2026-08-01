# Kitchen Ledger release visual review

- Review date: 2026-08-01
- Release: RecipeFlow 1.2.0
- Notation: `ledger`

## Corpus and geometry

The committed corpus contains 12 A4 portrait ledger fixtures rendered in print mode with a
40 px margin. The same resolved `TabularLayout` produces layout JSON, standalone SVG,
windowed print HTML, and full-canvas PNG.

Visual and executable review covered:

- `espresso-brownies`: setup prerequisites and the complete mix/fold/bake chain;
- `measurement-systems`: the dry whisk consumes only flour, baking powder, and salt;
- `branch-and-join`: three material branches survive and meet only at the final toss;
- `split-and-reserve`: both allocations, the held portion, and later consumption remain
  explicit;
- `multiple-outputs`: deterministic same-entry folios and final/useful output roles;
- `setup-heavy`: standing conditions stay separate from food flow;
- `many-narrow-operations`: repeated compact entries remain readable;
- `long-text` and `long-completion-criteria`: wrapping preserves every visible word;
- `unicode`: multilingual text survives SVG and PNG;
- `compact`: numeric ranges render as words (`3 to 5 min`), including 1-bit output;
- `large`: page headings repeat, entries move intact where possible, and carried-forward
  bands match the later material frontier.

Automated geometry checks confirm no clipped text, overlapping leaf cells, or opaque box
enclosure of another leaf cell. Every graph input edge has one consumed line; setup is not
rendered as food; page windows cover each entry exactly once; PNG height is the full
multi-sheet canvas.

## Failed runs and fixes

All failures remain preserved under `evals/png-blackbox/runs/`.

- v1 exposed lost ingredient preparation evidence in the consumed column. Ledger now shows
  the canonical label and authored source line together.
- v2 exposed weak setup parameter labeling and a schema-shaped reconstruction harness.
  Setup values now say `Time` and `Temperature`; readers now write ordinary recipes.
- v3 exposed `3..5 min` being read as `3.5 min` in 1-bit output. Ledger writes ranges as
  unambiguous words.
- v4 exposed a synthetic source that used butter and sugar in setup while modeling them as
  fully consumed later. The authoring skill now forbids that construction. The corrected
  semantic evaluation fixture is isolated through a pinned source override, preserving
  historical `flow` and `compact-table` bytes for unchanged canonical inputs.

Serialization and boundary-envelope variations encountered during orchestration were
treated as harness issues. They did not trigger renderer changes or alter reconstruction
semantics.

## Final fresh gate

[`2026-08-01-ledger-v5`](../../evals/png-blackbox/runs/2026-08-01-ledger-v5/REPORT.md)
contains 36 fresh PNG-only reconstructions and 72 independent judgments.

- Semantic equivalence: 36/36 images, 2/2 votes each.
- Membership precision: 1083/1083; recall: 1083/1083.
- Allocation arithmetic, branch/join meaning, direct-input survival, output inventory, and
  completion-criteria probes: no failures.
- Variant parity: 24/24 equivalence votes and zero false-positive memberships in color,
  greyscale, and 1-bit.

The release visual gate passes with no semantic degradation across variants.
