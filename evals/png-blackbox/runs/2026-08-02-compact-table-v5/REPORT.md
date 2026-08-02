# PNG black-box evaluation: 2026-08-02-compact-table-v5

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reader-beta | judge-alpha: 32/32, judge-gamma: 32/32 | 2/2 | pass |
| espresso-brownies | reader-beta | judge-alpha: 32/32, judge-gamma: 32/32 | 2/2 | pass |
| large | reader-gamma | judge-alpha: 32/32, judge-beta: 32/32 | 2/2 | pass |
| setup-heavy | reader-gamma | judge-alpha: 26/32, judge-beta: 30/32 | 1/2 | review |
| split-and-reserve | reader-gamma | judge-alpha: 32/32, judge-beta: 32/32 | 2/2 | pass |

## Aggregate

- Pass: 4
- Review: 1
- Fail: 0
- Recorded judgments: 10

Average dimension scores:

- `metadata`: 4.00/4
- `ingredients`: 3.80/4
- `setup`: 4.00/4
- `operations`: 3.70/4
- `flow_topology`: 3.80/4
- `temporal_completion`: 4.00/4
- `outputs_roles`: 4.00/4
- `evidence_discipline`: 3.90/4

## Judge findings

- **setup-heavy / judge-alpha / major:** The fixed butter and sugar quantities are ambiguously diverted from the soufflé mixture to ramekin coating. — The original routes the listed 30 g butter into the fold and the listed 120 g sugar into the whipped whites, while its ramekin setup gives no coating quantities. The candidate instead tells the cook to coat with the listed softened butter and sugar and says an unspecified share must be reserved, leaving the batter with indeterminate and potentially reduced amounts.
- **setup-heavy / judge-alpha / minor:** The fold operation does not explicitly name its three inputs. — The original folds lemon-base, meringue, and butter. The candidate only says 'Fold gently to make an aerated lemon soufflé mixture' and discusses butter allocation without directly instructing the cook to combine all three materials.
- **setup-heavy / judge-beta / minor:** The folding sentence leaves its inputs implicit. — The original explicitly folds the lemon base, meringue, and butter together. The candidate says only to fold gently, although the immediately preceding base and meringue steps plus its butter-at-folding note make the intended three inputs recoverable.
