# PNG black-box evaluation: 2026-07-31-compact-table-v1

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-p | judge-16: 32/32, judge-18: 32/32 | 2/2 | pass |
| compact | reconstructor-p | judge-16: 32/32, judge-18: 32/32 | 2/2 | pass |
| espresso-brownies | reconstructor-q | judge-16: 32/32, judge-17: 32/32 | 2/2 | pass |
| large | reconstructor-r | judge-17: 31/32, judge-18: 30/32 | 2/2 | pass |
| long-completion-criteria | reconstructor-q | judge-16: 32/32, judge-17: 32/32 | 2/2 | pass |
| long-text | reconstructor-r | judge-17: 31/32, judge-18: 31/32 | 2/2 | pass |
| many-narrow-operations | reconstructor-r | judge-17: 31/32, judge-18: 30/32 | 2/2 | pass |
| measurement-systems | reconstructor-p | judge-16: 32/32, judge-18: 32/32 | 2/2 | pass |
| multiple-outputs | reconstructor-q | judge-16: 32/32, judge-17: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-q | judge-16: 30/32, judge-17: 30/32 | 0/2 | fail |
| split-and-reserve | reconstructor-p | judge-16: 32/32, judge-18: 32/32 | 2/2 | pass |
| unicode | reconstructor-r | judge-17: 31/32, judge-18: 32/32 | 2/2 | pass |

## Aggregate

- Pass: 11
- Review: 0
- Fail: 1
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.96/4
- `ingredients`: 3.92/4
- `setup`: 4.00/4
- `operations`: 3.75/4
- `flow_topology`: 3.92/4
- `temporal_completion`: 4.00/4
- `outputs_roles`: 4.00/4
- `evidence_discipline`: 3.92/4

## Judge findings

- **large / judge-17 / minor:** Divided oil quantities are encoded as repeat text — The original places 30 mL and 45 mL directly on the sauté and brown operation inputs. The candidate preserves the exact allocations and associated operations, but puts them in repeat text while listing oil as an unquantified input.
- **large / judge-18 / minor:** Divided oil quantities are represented as operation notes rather than input quantities. — The candidate consumes the shared oil ingredient in both relevant operations and states 30 mL for sautéing and 45 mL for browning in repeat text, whereas the original attaches each amount directly to its material input.
- **large / judge-18 / minor:** The almond output receives a more specific role annotation. — The candidate marks toasted almonds as garnish; the original leaves that intermediate role implicit before the final four-way join.
- **long-text / judge-17 / minor:** A hazelnut quality qualifier is omitted — The original ingredient label says the skinned roasted hazelnuts have no bitter papery fragments remaining; the candidate retains skinned, roasted, quantity, grinding state, and the exact source_text but omits that extra label qualifier.
- **long-text / judge-18 / minor:** One descriptive hazelnut-selection detail is omitted. — The original hazelnut label specifies that no bitter papery fragments remain; the candidate preserves the quantity, roasting, skinning, and grinding state but not that label detail.
- **many-narrow-operations / judge-17 / minor:** Water allocations are stored as repeat text — The original represents 30 mL and 2970 mL as per-operation input quantities. The candidate preserves both exact allocations and their operations, but records them in repeat rather than on the water inputs.
- **many-narrow-operations / judge-18 / minor:** Water allocations are preserved in an awkward field and wording. — The candidate records the 30 mL sealing allocation and 2970 mL boiling allocation in each operation's repeat text as 'water for sealing and boiling' rather than as per-input quantities. The amounts and consuming operations remain recoverable and sum to 3 L.
- **setup-heavy / judge-16 / major:** Butter is not consumed by the reconstructed flow — The original fold operation inputs include butter, while the candidate lists 30 g butter as an ingredient but omits it from fold-gently and every other operation input.
- **setup-heavy / judge-17 / major:** Butter is disconnected from the operation flow — The original fold operation consumes lemon-base, meringue, and butter, while the candidate fold-gently operation consumes only lemon-custard-base and soft-peak-meringue. The candidate lists the 30 g butter and mentions its setup use, but never connects it to any operation.
- **unicode / judge-17 / minor:** Unicode typography is normalized in metadata — The original title uses em dashes and the yield uses a full-width ６, while the candidate uses en dashes and an ASCII 6. The numerical and linguistic meaning is unchanged.
- **unicode / judge-18 / minor:** Unicode typography differs without changing meaning. — The candidate uses an en dash instead of the original em dash in the title and ASCII 6 instead of full-width ６ in two Japanese-adjacent count strings.
