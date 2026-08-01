# PNG black-box evaluation: 2026-08-01-ledger-v1

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join--1bit | ledger-reconstructor-10 | ledger-judge-a5: 32/32, ledger-judge-b3: 32/32 | 2/2 | pass |
| branch-and-join--color | ledger-reconstructor-02 | ledger-judge-a1: 32/32, ledger-judge-b5: 32/32 | 2/2 | pass |
| branch-and-join--greyscale | ledger-reconstructor-06 | ledger-judge-a3: 32/32, ledger-judge-b1: 32/32 | 2/2 | pass |
| compact--1bit | ledger-reconstructor-08 | ledger-judge-a6: 32/32, ledger-judge-b2: 32/32 | 2/2 | pass |
| compact--color | ledger-reconstructor-12 | ledger-judge-a2: 32/32, ledger-judge-b4: 32/32 | 2/2 | pass |
| compact--greyscale | ledger-reconstructor-04 | ledger-judge-a4: 32/32, ledger-judge-b6: 32/32 | 2/2 | pass |
| espresso-brownies--1bit | ledger-reconstructor-09 | ledger-judge-a5: 32/32, ledger-judge-b3: 32/32 | 2/2 | pass |
| espresso-brownies--color | ledger-reconstructor-01 | ledger-judge-a1: 32/32, ledger-judge-b5: 32/32 | 2/2 | pass |
| espresso-brownies--greyscale | ledger-reconstructor-05 | ledger-judge-a3: 32/32, ledger-judge-b1: 32/32 | 2/2 | pass |
| large--1bit | ledger-reconstructor-04 | ledger-judge-a6: 29/32, ledger-judge-b6: 31/32 | 2/2 | pass |
| large--color | ledger-reconstructor-08 | ledger-judge-a2: 28/32, ledger-judge-b2: 30/32 | 1/2 | review |
| large--greyscale | ledger-reconstructor-12 | ledger-judge-a4: 30/32, ledger-judge-b4: 31/32 | 2/2 | pass |
| long-completion-criteria--1bit | ledger-reconstructor-03 | ledger-judge-a6: 32/32, ledger-judge-b6: 32/32 | 2/2 | pass |
| long-completion-criteria--color | ledger-reconstructor-07 | ledger-judge-a2: 32/32, ledger-judge-b2: 32/32 | 2/2 | pass |
| long-completion-criteria--greyscale | ledger-reconstructor-11 | ledger-judge-a4: 32/32, ledger-judge-b4: 32/32 | 2/2 | pass |
| long-text--1bit | ledger-reconstructor-05 | ledger-judge-a5: 32/32, ledger-judge-b1: 32/32 | 2/2 | pass |
| long-text--color | ledger-reconstructor-09 | ledger-judge-a1: 32/32, ledger-judge-b3: 32/32 | 2/2 | pass |
| long-text--greyscale | ledger-reconstructor-01 | ledger-judge-a3: 32/32, ledger-judge-b5: 32/32 | 2/2 | pass |
| many-narrow-operations--1bit | ledger-reconstructor-07 | ledger-judge-a6: 31/32, ledger-judge-b2: 32/32 | 2/2 | pass |
| many-narrow-operations--color | ledger-reconstructor-11 | ledger-judge-a2: 32/32, ledger-judge-b4: 32/32 | 2/2 | pass |
| many-narrow-operations--greyscale | ledger-reconstructor-03 | ledger-judge-a4: 32/32, ledger-judge-b6: 32/32 | 2/2 | pass |
| measurement-systems--1bit | ledger-reconstructor-01 | ledger-judge-a5: 32/32, ledger-judge-b5: 32/32 | 2/2 | pass |
| measurement-systems--color | ledger-reconstructor-05 | ledger-judge-a1: 32/32, ledger-judge-b1: 32/32 | 2/2 | pass |
| measurement-systems--greyscale | ledger-reconstructor-09 | ledger-judge-a3: 32/32, ledger-judge-b3: 32/32 | 2/2 | pass |
| multiple-outputs--1bit | ledger-reconstructor-02 | ledger-judge-a5: 32/32, ledger-judge-b5: 32/32 | 2/2 | pass |
| multiple-outputs--color | ledger-reconstructor-06 | ledger-judge-a1: 32/32, ledger-judge-b1: 32/32 | 2/2 | pass |
| multiple-outputs--greyscale | ledger-reconstructor-10 | ledger-judge-a3: 32/32, ledger-judge-b3: 32/32 | 2/2 | pass |
| setup-heavy--1bit | ledger-reconstructor-11 | ledger-judge-a6: 32/32, ledger-judge-b4: 32/32 | 2/2 | pass |
| setup-heavy--color | ledger-reconstructor-03 | ledger-judge-a2: 32/32, ledger-judge-b6: 32/32 | 2/2 | pass |
| setup-heavy--greyscale | ledger-reconstructor-07 | ledger-judge-a4: 32/32, ledger-judge-b2: 32/32 | 2/2 | pass |
| split-and-reserve--1bit | ledger-reconstructor-06 | ledger-judge-a5: 32/32, ledger-judge-b1: 32/32 | 2/2 | pass |
| split-and-reserve--color | ledger-reconstructor-10 | ledger-judge-a1: 32/32, ledger-judge-b3: 32/32 | 2/2 | pass |
| split-and-reserve--greyscale | ledger-reconstructor-02 | ledger-judge-a3: 32/32, ledger-judge-b5: 32/32 | 2/2 | pass |
| unicode--1bit | ledger-reconstructor-12 | ledger-judge-a6: 32/32, ledger-judge-b4: 32/32 | 2/2 | pass |
| unicode--color | ledger-reconstructor-04 | ledger-judge-a2: 32/32, ledger-judge-b6: 32/32 | 2/2 | pass |
| unicode--greyscale | ledger-reconstructor-08 | ledger-judge-a4: 32/32, ledger-judge-b2: 32/32 | 2/2 | pass |

## Aggregate

- Pass: 35
- Review: 1
- Fail: 0
- Recorded judgments: 72

Average dimension scores:

- `metadata`: 3.99/4
- `ingredients`: 3.90/4
- `setup`: 4.00/4
- `operations`: 4.00/4
- `flow_topology`: 4.00/4
- `temporal_completion`: 4.00/4
- `outputs_roles`: 4.00/4
- `evidence_discipline`: 3.92/4

## Judge findings

- **large--1bit / ledger-judge-a6 / minor:** Some ingredient evidence and metadata detail is reduced. — The candidate omits the original description, changes the onion preparation from thinly sliced to finely sliced, omits that the limes contribute zest and juice, and drops 'divided' from the oil source text. The graph and oil allocations still preserve the operational semantics.
- **large--1bit / ledger-judge-b6 / minor:** The lime preparation detail is omitted. — The original identifies the lime source as zest and juice of 3 limes, while the reconstruction records only 3 limes. The herb-sauce input membership and quantity remain correct, so this does not alter the graph or recipe identity.
- **large--color / ledger-judge-a2 / major:** Required lime preparation is lost — The original specifies zest and juice of 3 limes, while the candidate records only 3 limes with no preparation. In the blend-herb-sauce operation this omission leaves whole limes as the apparent input, which can materially change execution and the sauce. The candidate also changes the onion preparation from thinly sliced to finely sliced.
- **large--color / ledger-judge-b2 / minor:** Two ingredient preparation details are not reproduced exactly. — The original lime source text specifies zest and juice of 3 limes, while the candidate records only 3 limes; the original onions are thinly sliced, while the candidate says finely sliced. Quantities, memberships, and downstream operations remain correct.
- **large--greyscale / ledger-judge-a4 / minor:** The lime preparation state is omitted. — The original source evidence specifies zest and juice of 3 limes, whereas candidate I5 records only 3 limes with no preparation state.
- **large--greyscale / ledger-judge-a4 / minor:** The oil source evidence is not faithfully transcribed. — Candidate I8 uses the malformed source_text 'neutral cooking oil · of 75 mL authored' instead of the original evidence '75 mL neutral cooking oil, divided'; its separate label, total quantity, and two allocations remain correct.
- **large--greyscale / ledger-judge-b4 / minor:** The lime preparation is omitted. — The original specifies 'zest and juice of 3 limes'; the reconstruction records '3 limes' with no preparation. The quantity and operation membership remain correct.
- **many-narrow-operations--1bit / ledger-judge-a6 / minor:** The water source text is corrupted even though its usable semantics are preserved. — Candidate I3 says 'water for sealing and boiling · of 3 L authored'; the original source text is '3 L water for sealing and boiling'. The label, total quantity, and 30 mL plus 2970 mL allocations remain correct.

## Ledger semantic probes

- Membership precision: 775/775 (100.0%)
- Membership recall: 775/775 (100.0%)
- `allocation_arithmetic`: 23/23 pass (100.0%); 49 not applicable
- `setup_discrimination`: 42/42 pass (100.0%); 30 not applicable
- `branch_join_interpretation`: 33/33 pass (100.0%); 39 not applicable
- `direct_input_survival`: 71/71 pass (100.0%); 1 not applicable
- `output_inventory`: 72/72 pass (100.0%); 0 not applicable
- `completion_criteria`: 61/61 pass (100.0%); 11 not applicable
- `round_trip_equivalence`: 66/72 pass (91.7%); 0 not applicable

Variant parity:

- `color`: 23/24 equivalence votes; 0 false-positive memberships
- `greyscale`: 24/24 equivalence votes; 0 false-positive memberships
- `1bit`: 24/24 equivalence votes; 0 false-positive memberships
