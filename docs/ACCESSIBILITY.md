# Accessibility

RecipeFlow visual artifacts must communicate the complete recipe without relying on color,
rotation, or sight alone.

## SVG

- Use `role="img"` with unique `title` and `desc` references.
- Describe the recipe title, flow direction, setup, operation count, and final outputs.
- Preserve complete strings even when an explicit display abbreviation is enabled.
- Maintain sufficient text/background and line/background contrast.
- Do not use color as the only distinction among final, garnish, waste, or optional paths.
- Avoid text below the configured minimum font size.

## HTML

HTML works without JavaScript and contains:

- the SVG;
- a structured textual fallback with headings or a table;
- setup prerequisites;
- ingredients with quantities;
- operations in dependency order with inputs, outputs, time, temperature, and completion
  criteria;
- final, garnish, and waste outputs;
- a print stylesheet and document language where known.

Keyboard focus is required only for actual controls. Static diagram shapes are not made
focusable.

## PNG

PNG cannot carry equivalent structure. Applications must provide alt text or an adjacent
structured representation. Raster export uses a crisp default scale and preserves contrast.

## Motion and interaction

Core renderers do not require animation. Optional interactive viewers respect reduced
motion, keyboard navigation, visible focus, and screen-reader labels without changing the
portable layout contract.

## Review gate

Automated checks cover markup structure, labels, contrast tokens, and fallback presence.
Manual review covers reading order, high zoom, narrow width, forced colors, and screen-reader
comprehension. Findings and accepted limitations are recorded with release evidence.
