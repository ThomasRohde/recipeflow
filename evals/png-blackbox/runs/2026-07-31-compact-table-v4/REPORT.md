# PNG black-box evaluation: 2026-07-31-compact-table-v4

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-y | judge-25: 31/32, judge-27: 32/32 | 2/2 | pass |
| compact | reconstructor-y | judge-25: 32/32, judge-27: 32/32 | 2/2 | pass |
| espresso-brownies | reconstructor-z | judge-25: 31/32, judge-26: 32/32 | 2/2 | pass |
| large | reconstructor-aa | judge-26: 32/32, judge-27: 32/32 | 2/2 | pass |
| long-completion-criteria | reconstructor-z | judge-25: 32/32, judge-26: 32/32 | 2/2 | pass |
| long-text | reconstructor-aa | judge-26: 31/32, judge-27: 31/32 | 2/2 | pass |
| many-narrow-operations | reconstructor-aa | judge-26: 32/32, judge-27: 32/32 | 2/2 | pass |
| measurement-systems | reconstructor-y | judge-25: 31/32, judge-27: 32/32 | 2/2 | pass |
| multiple-outputs | reconstructor-z | judge-25: 32/32, judge-26: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-z | judge-25: 30/32, judge-26: 32/32 | 2/2 | pass |
| split-and-reserve | reconstructor-y | judge-25: 31/32, judge-27: 32/32 | 2/2 | pass |
| unicode | reconstructor-aa | judge-26: 31/32, judge-27: 31/32 | 2/2 | pass |

## Aggregate

- Pass: 12
- Review: 0
- Fail: 0
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.96/4
- `ingredients`: 3.92/4
- `setup`: 3.83/4
- `operations`: 4.00/4
- `flow_topology`: 4.00/4
- `temporal_completion`: 4.00/4
- `outputs_roles`: 4.00/4
- `evidence_discipline`: 3.88/4

## Judge findings

- **branch-and-join / judge-25 / minor:** Setup products use setup IDs — Required-by links and operation requirements retain the hot-oven and boiling-water dependencies.
- **espresso-brownies / judge-25 / minor:** Setup products use setup IDs — The pan and oven entries are directly linked to bake through required_by and requires.
- **long-text / judge-26 / minor:** Hazelnut label loses one descriptive clause — The candidate omits the original label's phrase that no bitter papery fragments remain, although 'skinned' and the exact source text retain the practical ingredient meaning.
- **long-text / judge-27 / minor:** Hazelnut label omits a descriptive qualifier — The original label says no bitter papery fragments remain, while the candidate omits that phrase; quantity, preparation state, and source text are otherwise preserved.
- **measurement-systems / judge-25 / minor:** Preheat product uses its setup ID — Required_by and the bake requirement preserve the prerequisite relationship.
- **setup-heavy / judge-25 / minor:** Setup products use setup IDs — The setup IDs remain linked through required_by.
- **setup-heavy / judge-25 / minor:** Ramekin allocations remain ambiguous — Butter and sugar used in ramekin preparation are not quantitatively allocated, and the candidate preserves this ambiguity in its notes.
- **split-and-reserve / judge-25 / minor:** Split allocations are label-encoded — The ingredient and output labels retain the 300 mL input and 250 mL/50 mL split.
- **unicode / judge-26 / minor:** Evidence note overstates exact Unicode preservation — The title's em dashes became en dashes and full-width ６ became ASCII 6 in the yield and custard label. The recipe meaning is unchanged.
- **unicode / judge-27 / minor:** Unicode punctuation and digit forms differ — The title substitutes en dashes for the original em dashes, and the yield and custard output substitute ASCII 6 for the original fullwidth ６.
