# Independent critic rubric

Review the source evidence, RecipeFlow YAML, compiled graph, SVG, and PNG without relying on
the author's summary.

## Severity

- **Critical:** invented or omitted safety-relevant fact, invalid final product, lost
  material, wrong dependency, unreadable artifact, or validation bypass.
- **Major:** missing branch/split/reservation, material/setup confusion, incorrect role,
  visible clipping or overlap, or significant source-fidelity loss.
- **Minor:** naming, presentation, or documentation defect that does not change meaning or
  legibility.

## Scorecard

1. Source coverage: every ingredient, instruction, setup fact, and output is accounted for.
2. Evidence discipline: no unsupported quantity, duration, temperature, equipment, or
   dependency.
3. Material conservation: splits and reservations preserve every later-used portion.
4. Graph correctness: producers, consumers, branches, joins, and final outputs match the
   source.
5. Diagnostics: validation and render-check are green; warnings are understood.
6. Visual fidelity: complete labels, legible density, no overlap, and correct topology.
7. Raster parity: PNG matches SVG and preserves all glyphs.
8. Accessibility: complete source strings and a meaningful alternative description exist.

Return findings with severity, evidence, affected ID or visual region, and a concrete repair.
Do not approve while any critical or major finding remains.
