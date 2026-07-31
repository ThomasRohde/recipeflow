# Visual review

Inspect the rendered SVG and PNG, not only their markup.

## At ordinary size

- Read every ingredient label and quantity.
- Read every setup instruction.
- Read every operation action, duration, temperature, and completion criterion.
- Read every intermediate and final-output label.
- Confirm no text is clipped, abbreviated without permission, hidden by a box, or outside
  the canvas.
- Confirm operation metadata does not collide with labels or borders.
- Confirm setup stays above the main material flow.
- Confirm final-output boxes contain their complete text.

## Topology

- Follow each material line from producer to consumer.
- Confirm branch paths remain distinct.
- Confirm joins span all intended inputs.
- Confirm split and reserved portions remain visible until their actual use.
- Confirm garnish and waste do not look like the primary final output.

## SVG and PNG parity

- Compare label positions, wrapping, line routing, colors, and bounds.
- Confirm PNG dimensions match the requested scale, width, background, and DPI.
- Look for raster-only missing glyphs or shifted text.
- Inspect Unicode and accented characters at 100% zoom.

## Failure response

Treat clipped, truncated, overlapping, unreadable, or semantically misleading output as a
blocking defect. Correct the document if the topology is wrong; correct renderer options or
report a layout defect if the model is right. Re-render and inspect both formats again.
