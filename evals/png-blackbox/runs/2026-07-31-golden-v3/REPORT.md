# PNG black-box evaluation: 2026-07-31-golden-v3

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-g | judge-7: 32/32, judge-9: 32/32 | 2/2 | pass |
| compact | reconstructor-g | judge-7: 28/32, judge-9: 30/32 | 0/2 | fail |
| espresso-brownies | reconstructor-h | judge-7: 31/32, judge-8: 32/32 | 2/2 | pass |
| large | reconstructor-i | judge-8: 31/32, judge-9: 32/32 | 2/2 | pass |
| long-completion-criteria | reconstructor-h | judge-7: 32/32, judge-8: 32/32 | 2/2 | pass |
| long-text | reconstructor-i | judge-8: 32/32, judge-9: 32/32 | 2/2 | pass |
| many-narrow-operations | reconstructor-i | judge-8: 31/32, judge-9: 32/32 | 2/2 | pass |
| measurement-systems | reconstructor-g | judge-7: 32/32, judge-9: 32/32 | 2/2 | pass |
| multiple-outputs | reconstructor-h | judge-7: 32/32, judge-8: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-h | judge-7: 32/32, judge-8: 32/32 | 2/2 | pass |
| split-and-reserve | reconstructor-g | judge-7: 32/32, judge-9: 32/32 | 2/2 | pass |
| unicode | reconstructor-i | judge-8: 30/32, judge-9: 31/32 | 2/2 | pass |

## Aggregate

- Pass: 11
- Review: 0
- Fail: 1
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.88/4
- `ingredients`: 4.00/4
- `setup`: 4.00/4
- `operations`: 3.92/4
- `flow_topology`: 4.00/4
- `temporal_completion`: 3.83/4
- `outputs_roles`: 3.96/4
- `evidence_discipline`: 3.92/4

## Judge findings

- **compact / judge-7 / major:** The toast duration is changed from a range to a single midpoint-like value. — The original specifies duration "3..5 min", while the candidate specifies "3.5 min". A 3-to-5-minute range is not semantically equivalent to a fixed 3.5-minute duration.
- **compact / judge-9 / major:** The toast duration was changed from a range to an unsupported exact time. — The candidate records "3.5 min", while the original specifies "3..5 min". This removes the original two-minute timing range and asserts a particular duration not present in the recipe.
- **espresso-brownies / judge-7 / minor:** The non-instructional recipe description is omitted. — The original describes the recipe as "A dense compact flow modeled after the original RecipeFlow notation." The candidate retains the title and yield but not this descriptive metadata.
- **large / judge-8 / minor:** The divided oil quantities are not encoded on their operation inputs. — The original assigns 30 mL oil to sauté aromatics and 45 mL to brown chicken. The candidate gives both operations the shared 75 mL oil ingredient, while preserving the exact allocation only in an evidence note.
- **many-narrow-operations / judge-8 / minor:** Per-operation water allocations are relegated to an evidence note. — The original assigns 30 mL water to moisten and 2970 mL to boil. The candidate references the undivided water ingredient in both operation inputs, although its evidence note preserves both exact allocations.
- **unicode / judge-8 / minor:** A few Unicode presentation details are normalized. — The candidate changes the title separators from em dashes to en dashes, renders the full-width ６ as ASCII 6 in the yield and custard label, and capitalizes Greek Καραμέλα in the final label where the original uses lowercase καραμέλα.
- **unicode / judge-9 / minor:** A few Unicode presentation forms were normalized. — The candidate uses an en dash where the original title uses an em dash and ASCII 6 where the original yield and baked-output label use full-width ６; the words, quantities, and multilingual meaning remain unchanged.
