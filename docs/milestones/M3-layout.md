# M3 - Production tabular layout

## Deliverables

- renderer-neutral `recipeflow.tabular-layout/v1`;
- deterministic text measurement and wrapping;
- dynamic lanes, columns, boxes, routing, and canvas bounds;
- collision and overflow diagnostics;
- classic and modern themes;
- SVG, accessible HTML, and SVG-derived PNG.

## Evidence

The twelve fixtures in [VISUAL-QUALITY.md](../VISUAL-QUALITY.md) each produce layout JSON,
SVG, HTML, and PNG. Automated checks prove bounds and string recovery; a reviewer opens the
actual SVG and PNG and records findings.

## Exit

No required text is clipped, truncated, overlapping, unreadable, or outside the viewBox at
supported widths.
