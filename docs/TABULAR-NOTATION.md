# Tabular recipe notation

RecipeFlow's tabular notation preserves the glanceability of a compact recipe table while
representing an explicit transformation graph.

## Reading the diagram

- Time and dependency generally progress from left to right.
- Ingredient and material lanes run horizontally.
- A transformation cell crosses every lane it consumes or produces.
- Produced intermediate labels continue on material lanes.
- Setup prerequisites occupy a separate area above the material flow.
- Recipe yield appears beneath the title when authored.
- Final, garnish, and waste outputs have distinct semantic styling.
- Branches separate into independent paths; joins converge at a shared operation.

Visual position is derived from the canonical graph. It never changes graph meaning.

## Classic theme

`classic` is the default:

- white or explicitly configured background;
- restrained green or neutral line color;
- plain borders and dense spacing;
- minimal corner radius;
- no decorative shadow;
- readable text at ordinary display size.

It is closest to the motivating compact recipe table.

## Modern theme

`modern` uses softer cards and spacing while preserving identical topology, complete labels,
and accessibility metadata. A theme may change presentation but not hide data or alter
geometry invariants.

## Text rules

Labels wrap at measured boundaries. They are never silently sliced, clipped, scaled below
the requested minimum font size, or hidden behind another box. `allow_ellipsis=False`
preserves that default. Setting it to `True` grants a renderer permission to shorten visual
text only if a bounded layout cannot reflow; the complete source string remains required in
the layout and accessibility metadata.

Long content increases row height, column width, or both. Narrow output negotiates wrapping
rather than shrinking the entire diagram to unreadability. A requested raster width is a
layout preference, not a destructive maximum: output preserves the measured intrinsic
width whenever shrinking it would violate the font floor.

## Operation metadata

Action, duration, temperature, repetition, and completion criteria belong to the operation
cell. Metadata receives its own measured region and cannot overlap the action label or
border. `operation_label_orientation="auto"` chooses horizontal or vertical text based on
the measured fit.

Authored range syntax such as `3..5 min` remains unchanged in the structured layout
contract, while the human-facing text renders it as `Time: 3 to 5 min` in a larger metadata
style so it cannot be mistaken for the decimal value `3.5 min`.

Direct source-material inputs are rendered as `Uses:` metadata in the consuming operation.
An edge-specific allocation takes precedence over the ingredient's total quantity. This
distinguishes, for example, two operations consuming 30 mL and 2970 mL from the same
authored water ingredient, and makes stock entering a dense sauce operation explicit.
Quantities on split or reserved outputs are rendered with their material labels.

## Setup and output areas

Setup cards grow to complete instructions, show authored targets, name the operations that
require them, and remain above the main flow. Separate dependency guides connect the same
prerequisites visually. Final-output boxes size to their full labels and annotations. Both
are included in canvas-bound validation.

## Accessibility

SVG includes a title and meaningful description. HTML adds structured fallback content that
lists setup, ingredients, operations, and outputs in dependency order. See
[ACCESSIBILITY.md](ACCESSIBILITY.md).
