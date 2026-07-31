# PNG black-box evaluation: 2026-07-31-compact-table-v3

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-v | judge-22: 32/32, judge-24: 32/32 | 2/2 | pass |
| compact | reconstructor-v | judge-22: 32/32, judge-24: 32/32 | 2/2 | pass |
| espresso-brownies | reconstructor-w | judge-22: 32/32, judge-23: 32/32 | 2/2 | pass |
| large | reconstructor-x | judge-23: 31/32, judge-24: 29/32 | 1/2 | review |
| long-completion-criteria | reconstructor-w | judge-22: 32/32, judge-23: 32/32 | 2/2 | pass |
| long-text | reconstructor-x | judge-23: 28/32, judge-24: 27/32 | 1/2 | review |
| many-narrow-operations | reconstructor-x | judge-23: 31/32, judge-24: 28/32 | 1/2 | review |
| measurement-systems | reconstructor-v | judge-22: 32/32, judge-24: 32/32 | 2/2 | pass |
| multiple-outputs | reconstructor-w | judge-22: 32/32, judge-23: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-w | judge-22: 32/32, judge-23: 32/32 | 2/2 | pass |
| split-and-reserve | reconstructor-v | judge-22: 32/32, judge-24: 32/32 | 2/2 | pass |
| unicode | reconstructor-x | judge-23: 28/32, judge-24: 29/32 | 2/2 | pass |

## Aggregate

- Pass: 9
- Review: 3
- Fail: 0
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.92/4
- `ingredients`: 3.96/4
- `setup`: 3.88/4
- `operations`: 3.75/4
- `flow_topology`: 3.92/4
- `temporal_completion`: 3.88/4
- `outputs_roles`: 3.92/4
- `evidence_discipline`: 3.75/4

## Judge findings

- **large / judge-23 / minor:** The divided oil quantities are not encoded on their operation inputs. — The original allocates 45 mL of oil to browning and 30 mL to sautéing. The candidate references the single 75 mL ingredient in both operations and records the exact allocation only in ambiguities.
- **large / judge-24 / major:** The divided oil allocation is absent from the structured operation inputs. — The original assigns 45 mL of the 75 mL oil to browning and 30 mL to sauteing. The candidate points both operations at the undivided 75 mL ingredient, which implies full-quantity reuse; the correct split survives only in an ambiguity note.
- **long-text / judge-23 / minor:** The oven stabilization note is omitted. — The original requires allowing at least twenty minutes after the thermostat signals readiness so the stone and walls heat evenly; the candidate retains the preheat setup but not this note or its timing.
- **long-text / judge-23 / minor:** One hazelnut qualification is omitted. — The original ingredient label specifies that no bitter papery fragments remain, while the candidate preserves only the roasted, skinned, and finely ground properties represented in its source text.
- **long-text / judge-24 / major:** The oven setup omits the required stabilization wait. — The original instructs allowing at least twenty minutes after the thermostat first signals readiness so the stone and oven walls heat evenly; the candidate records no setup duration or note and proceeds directly from preheating to baking.
- **many-narrow-operations / judge-23 / minor:** Per-operation water allocations are not represented on the operation inputs. — The original assigns 30 mL of water to moisten and 2970 mL to boil. The candidate references the shared 3 L water ingredient at both operations and preserves the exact split only in ambiguities.
- **many-narrow-operations / judge-24 / major:** The divided water quantities are not represented in the operation inputs. — The original routes 30 mL of water to moisten and 2970 mL to boil, while the candidate gives both operations an undivided input reference to the full 3 L ingredient. The quantities appear only in an ambiguity note, leaving the executable graph with duplicated full-quantity consumption.
- **unicode / judge-23 / minor:** Some Unicode presentation distinctions are normalized. — The original title uses em dashes and its yield and intermediate custard label use the full-width digit ６; the candidate uses en dashes and ASCII 6 with a space.
- **unicode / judge-23 / minor:** The evidence note overstates exact Unicode preservation. — The candidate claims that Unicode punctuation and Japanese text are preserved as visibly rendered, despite the dash and full-width digit normalizations.
- **unicode / judge-24 / minor:** A few Unicode glyph forms are normalized rather than preserved exactly. — The original title uses em dashes and the yield and baked-custard label use fullwidth ６; the candidate uses en dashes and ASCII 6 in those positions. The culinary meaning is unchanged.
