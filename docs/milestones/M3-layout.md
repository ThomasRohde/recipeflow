# M3 — Layout and tabular notation

## Status

A functional vertical slice is included in the scaffold. The project can already generate a self-contained SVG and accessible HTML visualization in the style of the motivating recipe card.

## Implemented baseline

- Renderer-neutral `recipeflow.tabular-layout/v1` contract
- Deterministic lane assignment for ingredients and intermediate materials
- Vertical operation cells spanning all consumed lanes
- Left-to-right material flow
- Setup cards above the main flow
- Quantity, temperature and duration labels
- Highlighted final outputs
- Self-contained SVG renderer
- Responsive HTML wrapper
- CLI formats `tabular-svg`, `tabular-html`, and `tabular-layout`
- Public `create_tabular_layout()` library API
- Automated visualization tests

## Remaining milestone work

- Improve lane compaction for complex branches and split outputs
- Add collision detection and text wrapping
- Add visual themes and print presets
- Add snapshot tests for a broad recipe corpus
- Add accessible structured fallback content to HTML
- Add optional operation icons and richer completion conditions
- Add browser-side interactivity without changing the canonical layout contract

## Exit criterion

Deterministic SVG and accessible HTML match approved visual snapshots across simple chains, joins, branches, splits and setup-heavy recipes.
