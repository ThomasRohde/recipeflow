# PNG black-box evaluation: 2026-08-01-ledger-v4

Status: **failed early and superseded**.

All 36 corrected PNG-only reconstructions were completed and preserved. Twenty-four
first-pass judgments were written before the run was stopped; a second judgment pass was
not started because the release gate already had a reproducible semantic failure.

## Finding

The `setup-heavy` source graph told the cook to butter and sugar the ramekins in setup,
while the same butter and sugar ingredient records were modeled as fully consumed by later
transform operations. A color reader reasonably reconstructed two additional unspecified
supplies. The judge recorded two false-positive memberships and rejected round-trip
equivalence.

This is an authoring/modeling defect in the shared synthetic fixture, not a notation-reading
or prompt defect. The renderer faithfully exposed the contradiction.

## Corrective action

The authoring skill already forbids hiding material consumption in setup prose. The v5
semantic evaluation source is consistent with that rule: its setup action stages clean
ramekins without claiming an unmodeled food draw. It is pinned as an evaluation-only source
override so the shared geometry fixture and historical `flow` and `compact-table` artifacts
remain byte-stable.

No v4 rate is presented as a release claim. The corrected fixture and all three image
variants require fresh PNG-only readers and two fresh judgments per image.
