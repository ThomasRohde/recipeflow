# PNG black-box evaluation: 2026-08-02-golden-v7

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reader-alpha | judge-beta: 32/32, judge-gamma: 32/32 | 2/2 | pass |
| espresso-brownies | reader-alpha | judge-beta: 32/32, judge-gamma: 32/32 | 2/2 | pass |
| large | reader-beta | judge-alpha: 32/32, judge-gamma: 32/32 | 2/2 | pass |
| long-text | reader-alpha | judge-beta: 31/32, judge-gamma: 32/32 | 2/2 | pass |
| setup-heavy | reader-delta | judge-alpha: 32/32, judge-beta: 32/32 | 2/2 | pass |
| split-and-reserve | reader-alpha | judge-beta: 32/32, judge-gamma: 32/32 | 2/2 | pass |

## Aggregate

- Pass: 6
- Review: 0
- Fail: 0
- Recorded judgments: 12

Average dimension scores:

- `metadata`: 4.00/4
- `ingredients`: 4.00/4
- `setup`: 4.00/4
- `operations`: 4.00/4
- `flow_topology`: 4.00/4
- `temporal_completion`: 3.92/4
- `outputs_roles`: 4.00/4
- `evidence_discipline`: 4.00/4

## Judge findings

- **long-text / judge-beta / minor:** Pear texture cue is transcribed imprecisely. — The original requires each caramelized pear wedge to remain firm enough to lift intact, while the candidate says tender enough to lift intact. It retains the decisive intactness cue, so this is unlikely to alter execution materially.
