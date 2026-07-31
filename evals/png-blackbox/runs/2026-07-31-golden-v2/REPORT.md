# PNG black-box evaluation: 2026-07-31-golden-v2

Fresh reconstruction agents received PNGs only. Separate fresh judges compared
the neutral reconstructions with the original RecipeFlow YAML. Each fixture has
two independent judgments.

| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |
| --- | --- | --- | --- | --- |
| branch-and-join | reconstructor-d | judge-4: 32/32, judge-6: 31/32 | 2/2 | pass |
| compact | reconstructor-d | judge-4: 32/32, judge-6: 31/32 | 2/2 | pass |
| espresso-brownies | reconstructor-e | judge-4: 31/32, judge-5: 32/32 | 2/2 | pass |
| large | reconstructor-f | judge-5: 26/32, judge-6: 24/32 | 0/2 | fail |
| long-completion-criteria | reconstructor-e | judge-4: 32/32, judge-5: 32/32 | 2/2 | pass |
| long-text | reconstructor-f | judge-5: 32/32, judge-6: 31/32 | 2/2 | pass |
| many-narrow-operations | reconstructor-f | judge-5: 31/32, judge-6: 28/32 | 2/2 | pass |
| measurement-systems | reconstructor-d | judge-4: 32/32, judge-6: 31/32 | 2/2 | pass |
| multiple-outputs | reconstructor-e | judge-4: 32/32, judge-5: 32/32 | 2/2 | pass |
| setup-heavy | reconstructor-e | judge-4: 29/32, judge-5: 27/32 | 0/2 | fail |
| split-and-reserve | reconstructor-d | judge-4: 32/32, judge-6: 31/32 | 2/2 | pass |
| unicode | reconstructor-f | judge-5: 29/32, judge-6: 31/32 | 2/2 | pass |

## Aggregate

- Pass: 10
- Review: 0
- Fail: 2
- Recorded judgments: 24

Average dimension scores:

- `metadata`: 3.58/4
- `ingredients`: 4.00/4
- `setup`: 3.92/4
- `operations`: 3.83/4
- `flow_topology`: 3.67/4
- `temporal_completion`: 3.92/4
- `outputs_roles`: 3.96/4
- `evidence_discipline`: 3.58/4

## Judge findings

- **branch-and-join / judge-6 / minor:** Nonessential source and locale metadata are omitted. — The original includes the visual-regression source and locale en; the candidate preserves title and yield but omits those fields.
- **compact / judge-6 / minor:** Nonessential source and locale metadata are omitted. — The original records the visual-regression source and locale en; the candidate preserves title and yield but omits those fields.
- **espresso-brownies / judge-4 / minor:** The non-procedural recipe description is omitted. — The YAML describes the recipe as a dense compact flow modeled after the original RecipeFlow notation; the candidate retains title and yield but has no description field.
- **large / judge-5 / critical:** Chicken stock is introduced at the wrong stage of the sauce and braise flow. — The original adds stock with tomatoes to simmer the sauce and then braises browned chicken with that completed sauce. The candidate omits stock from simmer sauce and adds it only when the sauce joins browned chicken in the braise.
- **large / judge-6 / critical:** Chicken stock is routed to the wrong operation. — The original builds the sauce from softened aromatics, tomatoes, and stock, then braises browned chicken in that completed tomato sauce. The candidate omits stock from simmer-sauce and instead adds it directly to braise-chicken, changing the material dependency and sauce-building procedure.
- **large / judge-6 / minor:** Several output descriptions are promoted to unevidenced completion criteria. — The candidate adds until values such as thoroughly drained, evenly golden, fragrant, and deeply browned where the original supplies those concepts only in output labels.
- **large / judge-6 / minor:** Nonessential source, description, and locale metadata are omitted. — The original includes a description, visual-regression source, and locale en; the candidate retains title and yield but omits those fields.
- **long-text / judge-6 / minor:** Nonessential source and locale metadata are omitted. — The original identifies the visual-regression source and locale en; the candidate preserves the title and yield but has no corresponding source or locale fields.
- **many-narrow-operations / judge-5 / minor:** The candidate adds inferred repetition and completion fields that are not explicit in the original. — Per-wrapper repeat values and the boil/drain until fields are inferred from plural intermediate labels such as twenty-four portions, floating cooked dumplings, and thoroughly drained dumplings; the original does not encode those as repeat or completion fields.
- **many-narrow-operations / judge-6 / minor:** The candidate promotes output wording into completion criteria. — The original labels the boil output as floating cooked dumplings and the drain output as thoroughly drained dumplings, but does not state explicit completion criteria; the candidate adds until values for both.
- **many-narrow-operations / judge-6 / minor:** Per-piece repetition is inferred rather than explicitly evidenced. — The candidate adds repeat instructions for rounding through pleating, while the original specifies the twenty-four portions and plural intermediate chain without repeat fields on those operations.
- **many-narrow-operations / judge-6 / minor:** Nonessential source and locale metadata are omitted. — The original includes the visual-regression source and locale en; the candidate preserves title and yield but omits those fields.
- **measurement-systems / judge-6 / minor:** Nonessential source and locale metadata are omitted. — The original includes the visual-regression source and locale en; the candidate retains title and yield but omits those fields.
- **setup-heavy / judge-4 / critical:** The landing-station prerequisite is attached to the wrong operation. — The YAML requires landing-station for fill and level, while the candidate omits it there and instead requires arranged-landing-station for transfer and bake. This permits arranging the station only after filling, introducing delay into the immediate soufflé transfer workflow.
- **setup-heavy / judge-4 / minor:** The ramekin capacity is omitted. — The YAML setup target is six 180 mL ramekins; the candidate says only six ramekins.
- **setup-heavy / judge-5 / major:** The landing-station prerequisite is attached to the wrong operation. — The original makes landing-station a requirement of fill and level, while the candidate omits it there and instead requires arranged-landing-station for transfer and bake.
- **split-and-reserve / judge-6 / minor:** Nonessential source and locale metadata are omitted. — The original includes the visual-regression source and locale en; the candidate preserves title and yield but omits those fields.
- **unicode / judge-5 / minor:** Several Unicode details are not transcribed exactly, although their meaning is unchanged. — The candidate substitutes en dashes for the original em dashes, uses an ASCII 6 instead of full-width ６ in the yield, and changes the cooked-custard Greek label from έξι κρέμες to the semantically equivalent polytonic ἕξι κρέμες.
- **unicode / judge-6 / minor:** A few Unicode forms are not transcribed exactly. — The candidate uses en dashes rather than the original em dashes in the title, ASCII 6 rather than full-width ６ in the yield, and ἕξι rather than έξι in the cooked-custard label.
- **unicode / judge-6 / minor:** Nonessential source and locale metadata are omitted. — The original records the visual-regression source and locale fr; the candidate preserves the multilingual title and yield but omits source and locale fields.
