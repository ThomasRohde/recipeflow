# PNG black-box evaluation: 2026-07-31-golden-v4

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-j | judge-10: 32/32, judge-12: 32/32 | 2/2 | pass |
| compact | reconstructor-j | judge-10: 32/32, judge-12: 32/32 | 2/2 | pass |
| espresso-brownies | reconstructor-k | judge-10: 32/32, judge-11: 32/32 | 2/2 | pass |
| large | reconstructor-l | judge-11: 32/32, judge-12: 30/32 | 2/2 | pass |
| long-completion-criteria | reconstructor-k | judge-10: 32/32, judge-11: 32/32 | 2/2 | pass |
| long-text | reconstructor-l | judge-11: 29/32, judge-12: 28/32 | 2/2 | pass |
| many-narrow-operations | reconstructor-l | judge-11: 29/32, judge-12: 29/32 | 0/2 | fail |
| measurement-systems | reconstructor-j | judge-10: 32/32, judge-12: 32/32 | 2/2 | pass |
| multiple-outputs | reconstructor-k | judge-10: 32/32, judge-11: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-k | judge-10: 32/32, judge-11: 32/32 | 2/2 | pass |
| split-and-reserve | reconstructor-j | judge-10: 32/32, judge-12: 32/32 | 2/2 | pass |
| unicode | reconstructor-l | judge-11: 32/32, judge-12: 31/32 | 2/2 | pass |

## Aggregate

- Pass: 11
- Review: 0
- Fail: 1
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.88/4
- `ingredients`: 3.92/4
- `setup`: 3.92/4
- `operations`: 3.92/4
- `flow_topology`: 4.00/4
- `temporal_completion`: 3.75/4
- `outputs_roles`: 4.00/4
- `evidence_discipline`: 3.96/4

## Judge findings

- **large / judge-12 / minor:** The oil allocations are retained only in an evidence note. — The original operation inputs allocate 45 mL oil to browning chicken and 30 mL to sautéing aromatics. The candidate points both operations to the divided 75 mL ingredient without input quantities, while its evidence note states the correct 45 mL and 30 mL allocation.
- **large / judge-12 / minor:** The descriptive metadata is not retained. — The original description identifies a large connected graph with setup, parallel branches, and a four-way join; the candidate has no corresponding description.
- **long-text / judge-11 / minor:** Oven stabilization note omitted — The original setup says to allow at least twenty minutes after the thermostat first signals readiness; the candidate preserves the preheat temperature and rack position but not this additional wait.
- **long-text / judge-11 / minor:** Hazelnut label qualifier shortened — The original hazelnut label specifies that no bitter papery fragments remain, while the candidate retains only 'skinned roasted hazelnuts' plus the grinding preparation.
- **long-text / judge-12 / minor:** The oven equilibration instruction is omitted. — The original setup note says to allow at least twenty minutes after the thermostat first signals readiness; the candidate retains the preheat setup and 175 °C temperature but not that timing note.
- **long-text / judge-12 / minor:** One ingredient-label qualifier is lost. — The original hazelnut label includes "with no bitter papery fragments remaining"; the candidate label and preparation omit that qualifier.
- **long-text / judge-12 / minor:** The descriptive metadata is not retained. — The original description says the fixture exercises wrapping without clipping or truncating source language; the candidate has no corresponding description.
- **many-narrow-operations / judge-11 / major:** Boiling duration has a materially incorrect lower bound — The original boil operation requires 5–7 min, while the candidate records 3–7 min, permitting the dumplings to be removed two minutes earlier than specified.
- **many-narrow-operations / judge-11 / minor:** Per-operation water quantities are not structured on the inputs — The original assigns 30 mL water to moistening and 2970 mL to boiling; the candidate's operation inputs reference the undivided water ingredient, although its evidence note does preserve the exact allocation.
- **many-narrow-operations / judge-12 / major:** The boiling duration has a materially incorrect lower bound. — The original boil operation specifies 5..7 min, while the candidate specifies 3–7 min.
- **many-narrow-operations / judge-12 / minor:** Water allocations are preserved only in prose rather than on the operation inputs. — The original assigns 30 mL water to moistening and 2970 mL to boiling. The candidate operation inputs reference the undivided water ingredient, although its evidence note records both correct allocations.
- **unicode / judge-12 / minor:** A few Unicode presentation details are normalized. — The original title uses em dashes and its yield and custard output use full-width ６, while the candidate uses en dashes and ASCII 6; the final Greek label also changes initial case from καραμέλα to Καραμέλα.
