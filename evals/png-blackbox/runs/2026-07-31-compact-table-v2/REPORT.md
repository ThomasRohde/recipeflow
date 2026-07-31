# PNG black-box evaluation: 2026-07-31-compact-table-v2

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-s | judge-19: 31/32, judge-21: 31/32 | 2/2 | pass |
| compact | reconstructor-s | judge-19: 31/32, judge-21: 31/32 | 2/2 | pass |
| espresso-brownies | reconstructor-t | judge-19: 32/32, judge-20: 32/32 | 2/2 | pass |
| large | reconstructor-u | judge-20: 32/32, judge-21: 31/32 | 2/2 | pass |
| long-completion-criteria | reconstructor-t | judge-19: 32/32, judge-20: 32/32 | 2/2 | pass |
| long-text | reconstructor-u | judge-20: 27/32, judge-21: 28/32 | 0/2 | fail |
| many-narrow-operations | reconstructor-u | judge-20: 32/32, judge-21: 31/32 | 2/2 | pass |
| measurement-systems | reconstructor-s | judge-19: 31/32, judge-21: 31/32 | 2/2 | pass |
| multiple-outputs | reconstructor-t | judge-19: 32/32, judge-20: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-t | judge-19: 32/32, judge-20: 32/32 | 2/2 | pass |
| split-and-reserve | reconstructor-s | judge-19: 31/32, judge-21: 31/32 | 2/2 | pass |
| unicode | reconstructor-u | judge-20: 29/32, judge-21: 32/32 | 2/2 | pass |

## Aggregate

- Pass: 11
- Review: 0
- Fail: 1
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.62/4
- `ingredients`: 4.00/4
- `setup`: 4.00/4
- `operations`: 3.88/4
- `flow_topology`: 3.83/4
- `temporal_completion`: 4.00/4
- `outputs_roles`: 3.96/4
- `evidence_discipline`: 3.79/4

## Judge findings

- **branch-and-join / judge-19 / minor:** Recipe-level yield omitted — The original declares yield: 4 bowls, while candidate yield_text is null; the final output still states four bowls of roasted tomato rigatoni.
- **branch-and-join / judge-21 / minor:** Top-level yield omitted — The original yield is 4 bowls, while candidate yield_text is null; the final output label still states four bowls.
- **compact / judge-19 / minor:** Recipe-level yield omitted — The original declares yield: 2 slices, while candidate yield_text is null; the same quantity remains present in the final output label as two slices of cinnamon toast.
- **compact / judge-21 / minor:** Top-level yield omitted — The original yield is 2 slices, while candidate yield_text is null; the same amount remains recoverable from the bread quantity and final output label.
- **large / judge-21 / minor:** Divided oil quantities are not structural inputs — The original assigns 45 mL oil to browning and 30 mL to sautéing; the candidate routes the divided oil to both operations and records those exact allocations only in ambiguities and evidence_notes.
- **long-text / judge-20 / major:** Invented brown-butter dependency and split into the pear-caramelizing branch — The original caramelize-pears operation has only pears as input, while the candidate adds out-brown-butter and routes the same brown-butter output to both caramelize-pears and whisk-custard.
- **long-text / judge-21 / major:** False brown-butter dependency into the pear branch — The original caramelize-pears operation takes only pears, while the candidate also consumes out-brown-butter, turning an independent pear branch into a branch downstream of brown-butter and changing material routing.
- **many-narrow-operations / judge-21 / minor:** Per-operation water quantities are not structural inputs — The original assigns 30 mL water to moistening and 2970 mL to boiling; the candidate routes water to both operations and preserves both amounts only in ambiguities and evidence_notes.
- **measurement-systems / judge-19 / minor:** Recipe-level yield omitted — The original declares yield: 10 biscuits, while candidate yield_text is null; the final output still identifies ten biscuits.
- **measurement-systems / judge-21 / minor:** Top-level yield omitted — The original yield is 10 biscuits, while candidate yield_text is null; the final output label still states ten biscuits.
- **split-and-reserve / judge-19 / minor:** Recipe-level yield omitted — The original declares yield: 6 glasses, while candidate yield_text is null; the final output still states six chocolate mousse glasses.
- **split-and-reserve / judge-21 / minor:** Top-level yield omitted — The original yield is 6 glasses, while candidate yield_text is null; the final output label still states six mousse glasses.
- **unicode / judge-20 / minor:** Unicode typography was normalized in two visible strings — The original title uses em dashes and the yield/output text uses full-width ６, while the candidate uses en dashes and ASCII 6. The recipe meaning is unchanged.
