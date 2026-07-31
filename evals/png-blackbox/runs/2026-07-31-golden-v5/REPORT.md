# PNG black-box evaluation: 2026-07-31-golden-v5

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-m | judge-13: 32/32, judge-15: 31/32 | 2/2 | pass |
| compact | reconstructor-m | judge-13: 32/32, judge-15: 32/32 | 2/2 | pass |
| espresso-brownies | reconstructor-n | judge-13: 32/32, judge-14: 32/32 | 2/2 | pass |
| large | reconstructor-o | judge-14: 29/32, judge-15: 30/32 | 2/2 | pass |
| long-completion-criteria | reconstructor-n | judge-13: 32/32, judge-14: 32/32 | 2/2 | pass |
| long-text | reconstructor-o | judge-14: 32/32, judge-15: 32/32 | 2/2 | pass |
| many-narrow-operations | reconstructor-o | judge-14: 30/32, judge-15: 30/32 | 2/2 | pass |
| measurement-systems | reconstructor-m | judge-13: 32/32, judge-15: 31/32 | 2/2 | pass |
| multiple-outputs | reconstructor-n | judge-13: 32/32, judge-14: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-n | judge-13: 32/32, judge-14: 32/32 | 2/2 | pass |
| split-and-reserve | reconstructor-m | judge-13: 32/32, judge-15: 32/32 | 2/2 | pass |
| unicode | reconstructor-o | judge-14: 28/32, judge-15: 29/32 | 2/2 | pass |

## Aggregate

- Pass: 12
- Review: 0
- Fail: 0
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.92/4
- `ingredients`: 4.00/4
- `setup`: 3.92/4
- `operations`: 3.88/4
- `flow_topology`: 4.00/4
- `temporal_completion`: 3.88/4
- `outputs_roles`: 3.92/4
- `evidence_discipline`: 3.75/4

## Judge findings

- **branch-and-join / judge-15 / minor:** Setup products are represented as direct dependencies rather than named resources. — The original setup produces hot-oven and boiling-water. The candidate leaves both produces arrays empty but links preheat to roast and salted-water setup to boil in both directions, preserving the actual prerequisites.
- **large / judge-14 / minor:** The divided oil allocation is preserved narratively but encoded unevenly in the operation records. — The original assigns 30 mL oil to sauté aromatics and 45 mL to brown chicken. The candidate gives both operations the shared 75 mL ingredient reference, records the 45 mL amount in the brown-chicken repeat, and records the full 30/45 split only in ambiguities.
- **large / judge-14 / minor:** Several output qualities are elevated to inferred completion criteria. — The candidate adds until values such as thoroughly drained, soft and golden, evenly golden, fragrant, and deeply browned where the original conveys those qualities through action or output labels rather than completion_criteria fields.
- **large / judge-15 / minor:** The divided oil allocation is not represented on both structured operation inputs. — The original assigns 30 mL oil to sauté aromatics and 45 mL to brown chicken. The candidate references the undivided oil ingredient in both operations, puts 45 mL in the browning repeat text, and preserves the complete 30/45 split only in an ambiguity note.
- **large / judge-15 / minor:** Some completion fields restate output-label implications. — The candidate promotes soft and golden, evenly golden, fragrant, deeply browned, and thoroughly drained into until fields although the original encodes those ideas in output labels rather than explicit completion criteria.
- **many-narrow-operations / judge-14 / minor:** Batch coverage is promoted to repeat constraints even though the original does not encode repeats. — The candidate adds repeat text to divide, round, flatten, roll, fill, moisten, fold, and pleat. These statements are compatible with the 24-dumpling yield and output labels, but they are inferred rather than explicit repeat fields in the original.
- **many-narrow-operations / judge-14 / minor:** Output descriptions are reused as completion criteria. — The candidate adds until values for boil, drain, and toss based on the labels floating cooked dumplings, thoroughly drained dumplings, and sesame-coated dumplings; the original operations have no completion_criteria fields.
- **many-narrow-operations / judge-15 / minor:** Water allocations are preserved as prose rather than structured operation-input quantities. — The original assigns 30 mL of water to moisten and 2970 mL to boil. The candidate points both operations at the full 3 L ingredient and records the split in repeat and evidence text.
- **many-narrow-operations / judge-15 / minor:** Several procedural repeat and completion statements are inferred from output labels and the yield. — The candidate adds per-24 repetition to the forming operations and adds completion text for boiling, draining, and tossing where the original represents those facts only through operation/output semantics.
- **measurement-systems / judge-15 / minor:** The setup product is replaced by a direct setup-to-operation dependency. — The original preheat setup produces hot-oven and the bake requires that product. The candidate leaves produces empty but links the preheat setup directly to cut and bake through required_by and requires, preserving the practical dependency.
- **unicode / judge-14 / minor:** Two Unicode presentation distinctions are normalized. — The title uses en dashes instead of the original em dashes, while the yield and cooled-custards output use ASCII 6 instead of the original fullwidth ６. The multilingual words, fraction, accents, quantities, and recipe meaning remain intact.
- **unicode / judge-14 / minor:** The final caramelization receives an inferred repeat constraint. — The candidate states repeat: pour chacun des 6 ramequins, but the original has no repeat field for caramelize. This is compatible with the six-ramekin yield and completion wording rather than contradictory.
- **unicode / judge-15 / minor:** Two Unicode presentation details are normalized. — The original title uses em dashes and the yield uses full-width ６個; the candidate uses en dashes and renders the latter as 6 個. The same full-width digit normalization appears in the cooled-custards output label.
- **unicode / judge-15 / minor:** The evidence note overstates exact character preservation. — The candidate claims the visible Unicode is preserved, but the title dash and full-width digit are not byte-for-byte faithful to the original.
