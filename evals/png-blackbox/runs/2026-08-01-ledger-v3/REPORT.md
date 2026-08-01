# PNG black-box evaluation: 2026-08-01-ledger-v3

Status: **failed early and superseded**.

This was the first run to use ordinary Markdown recipes as human-proxy reconstructions.
All 36 PNG-only reconstructions and the first 36 independent judgments were completed and
preserved. The second judgment pass was stopped once a reproducible renderer defect was
confirmed; partial second-pass artifacts are retained unchanged.

## Finding

In the 1-bit `compact` fixture, the Ledger rendered the authored duration `3..5 min`
verbatim. The reader transcribed that as `3.5 minutes`. The first judge correctly classified
the loss of range semantics as a fidelity defect.

## Corrective action

Ledger duration ranges now use explicit wording (`3 to 5 min`) instead of two adjacent dots.
This is more legible in color, greyscale, and thresholded 1-bit output.

The same pass observed that the setup-heavy fixture's prose mentions butter and sugar for
ramekin preparation while its fully quantified ingredients are consumed later by transform
operations. That legacy shared fixture remains locked to preserve existing `flow` and
`compact-table` outputs. The authoring skill now explicitly forbids hiding material
consumption in setup prose, preventing the ambiguity in newly authored recipes.

No v3 rate is presented as a release claim. The corrected image corpus requires fresh
readers and two fresh judgments per image.
