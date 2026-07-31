# PNG black-box evaluation: 2026-07-31-golden-v1

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-a | judge-1: 32/32, judge-3: 31/32 | 2/2 | pass |
| compact | reconstructor-a | judge-1: 32/32, judge-3: 31/32 | 2/2 | pass |
| espresso-brownies | reconstructor-b | judge-1: 32/32, judge-2: 32/32 | 2/2 | pass |
| large | reconstructor-c | judge-2: 27/32, judge-3: 27/32 | 0/2 | fail |
| long-completion-criteria | reconstructor-b | judge-1: 31/32, judge-2: 30/32 | 1/2 | review |
| long-text | reconstructor-c | judge-2: 31/32, judge-3: 31/32 | 2/2 | pass |
| many-narrow-operations | reconstructor-c | judge-2: 30/32, judge-3: 29/32 | 0/2 | fail |
| measurement-systems | reconstructor-a | judge-1: 32/32, judge-3: 31/32 | 2/2 | pass |
| multiple-outputs | reconstructor-b | judge-1: 32/32, judge-2: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-b | judge-1: 29/32, judge-2: 29/32 | 0/2 | fail |
| split-and-reserve | reconstructor-a | judge-1: 30/32, judge-3: 29/32 | 0/2 | fail |
| unicode | reconstructor-c | judge-2: 32/32, judge-3: 31/32 | 2/2 | pass |

## Aggregate

- Pass: 7
- Review: 1
- Fail: 4
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.46/4
- `ingredients`: 4.00/4
- `setup`: 3.67/4
- `operations`: 3.50/4
- `flow_topology`: 4.00/4
- `temporal_completion`: 4.00/4
- `outputs_roles`: 4.00/4
- `evidence_discipline`: 3.92/4

## Judge findings

- **branch-and-join / judge-3 / minor:** Explicit yield omitted — The original yield is 4 bowls, while candidate yield_text is null, although the count remains in the final output label.
- **compact / judge-3 / minor:** Explicit yield omitted — The original yield is 2 slices, while candidate yield_text is null, although the count remains in the final output label.
- **large / judge-2 / major:** Two hot-skillet prerequisites are missing. — The original requires hot-skillet for toast spices, brown chicken, and toast almonds. The candidate requires its preheated skillet only for brown chicken, leaving both toasting operations without that prerequisite.
- **large / judge-2 / major:** The divided oil quantities at the two consuming operations are lost. — The original assigns 45 mL oil to brown chicken and 30 mL to sauté aromatics. The candidate sends the common 75 mL oil ingredient to both operations without either allocation.
- **large / judge-2 / minor:** The explicit serving yield is imprecise. — The original yield is 8 generous servings. The candidate preserves the eight-person implication only indirectly through the setup for eight shallow bowls and does not preserve the word generous.
- **large / judge-3 / major:** Hot-skillet prerequisites are missing from two operations — The original requires hot-skillet for toast spices, brown chicken, and toast almonds. The candidate routes the skillet setup only to brown chicken.
- **large / judge-3 / major:** Divided oil allocations are lost — The original assigns 45 mL oil to brown chicken and 30 mL to sauté aromatics. The candidate connects the undivided 75 mL oil ingredient to both operations without those quantities.
- **large / judge-3 / minor:** Explicit yield omitted — The original yield is 8 generous servings, while candidate yield_text is null.
- **long-completion-criteria / judge-1 / minor:** The sauce yield is omitted. — The original specifies a yield of 450 mL sauce. The candidate has a null yield and its final output label contains no equivalent volume.
- **long-completion-criteria / judge-2 / major:** The sauce yield is missing. — The original yield is 450 mL sauce, while the candidate has a null yield and contains no other quantity that preserves the 450 mL final yield.
- **long-text / judge-2 / minor:** The serving range is omitted. — The original says the one 28 cm tart serves ten to twelve people. The candidate preserves the one-tart and 28 cm meaning through the pastry-shell material, but does not preserve the ten-to-twelve serving guidance.
- **long-text / judge-3 / minor:** Explicit yield omitted — The original gives a yield of one 28 cm tart serving ten to twelve people, while candidate yield_text is null.
- **many-narrow-operations / judge-2 / major:** The water allocation between sealing and boiling is lost. — The original assigns 30 mL of the 3 L water to moisten and 2970 mL to boil. The candidate references the undivided 3 L water ingredient at both operations without preserving either per-step quantity.
- **many-narrow-operations / judge-3 / major:** Per-operation water allocation is lost — The original assigns 30 mL of water to moisten and 2970 mL to boil. The candidate connects the undivided 3 L water ingredient to both operations without either allocation.
- **many-narrow-operations / judge-3 / minor:** Explicit yield omitted — The original yield is 24 dumplings, while candidate yield_text is null, although the count survives in output labels.
- **measurement-systems / judge-3 / minor:** Explicit yield omitted — The original yield is 10 biscuits, while candidate yield_text is null, although the count remains in the final output label.
- **setup-heavy / judge-1 / major:** The landing-station prerequisite is attached to the wrong operation. — The original requires the arranged landing station for fill and level, together with the prepared ramekins. The candidate omits it from fill and level and instead requires its 'oven-tools-arranged' product for transfer and bake.
- **setup-heavy / judge-1 / minor:** The ramekin capacity is omitted. — The original setup target specifies six 180 mL ramekins, while the candidate states only six ramekins.
- **setup-heavy / judge-2 / major:** The landing-station prerequisite is attached to the wrong operation. — The original requires landing-station for fill and level, together with prepared-ramekins. The candidate omits it from fill and level and instead requires oven-tools-arranged for transfer and bake.
- **setup-heavy / judge-2 / major:** The ramekin capacity is missing. — The original setup targets six 180 mL ramekins. The candidate preserves the count but identifies them only as six ramekins, losing a vessel-size constraint that affects portioning and baking.
- **split-and-reserve / judge-1 / major:** The cream split quantities are missing. — The original divides 300 mL cream into 250 mL mousse cream and 50 mL reserved cream. The candidate retains both branches and their roles but gives neither branch quantity, explicitly marking the allocation as unknown.
- **split-and-reserve / judge-3 / major:** Cream split quantities are omitted — The original divides 300 mL cream into 250 mL mousse cream and 50 mL reserved cream. The candidate recovers both branches and the reserved role but gives neither branch quantity.
- **split-and-reserve / judge-3 / minor:** Explicit yield omitted — The original yield is 6 glasses, while candidate yield_text is null, although the count remains in the final output label.
- **unicode / judge-3 / minor:** Explicit yield omitted — The original yield is 6 ramequins · ６個, while candidate yield_text is null, though the six-custard count is retained in an intermediate label.
