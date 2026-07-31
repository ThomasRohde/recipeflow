from typing import Literal

from recipeflow.models.layout import (
    Insets,
    Rect,
    TextBlock,
    TextRole,
    TextStyle,
    WrappedLine,
)
from recipeflow.typography import MeasuredText, TextMeasurer, wrap_text


def measure_text_block(
    text: str,
    max_width: float,
    style: TextStyle,
    measurer: TextMeasurer,
    *,
    padding: Insets | None = None,
    wrap_mode: Literal["word", "grapheme"] = "word",
) -> tuple[MeasuredText, float, float]:
    insets = padding or Insets()
    inner_width = max(1, max_width - insets.left - insets.right)
    measured = wrap_text(text, inner_width, style, measurer, wrap_mode)
    return (
        measured,
        measured.width + insets.left + insets.right,
        measured.height + insets.top + insets.bottom,
    )


def place_text_block(
    *,
    identifier: str,
    role: TextRole,
    text: str,
    rect: Rect,
    style: TextStyle,
    measurer: TextMeasurer,
    padding: Insets | None = None,
    horizontal_alignment: str = "start",
    vertical_alignment: str = "top",
    rotation: int = 0,
    parent_id: str | None = None,
    wrap_mode: Literal["word", "grapheme"] = "word",
) -> TextBlock:
    insets = padding or Insets()
    inner_width = max(1, rect.width - insets.left - insets.right)
    measured = wrap_text(text, inner_width, style, measurer, wrap_mode)
    content_height = measured.height
    if vertical_alignment == "middle":
        first_top = rect.y + (rect.height - content_height) / 2
    elif vertical_alignment == "bottom":
        first_top = rect.bottom - insets.bottom - content_height
    else:
        first_top = rect.y + insets.top

    lines: list[WrappedLine] = []
    for index, line in enumerate(measured.lines):
        if horizontal_alignment == "center":
            x = rect.x + (rect.width - line.metrics.width) / 2
        elif horizontal_alignment == "end":
            x = rect.right - insets.right - line.metrics.width
        else:
            x = rect.x + insets.left
        line_top = first_top + index * style.line_height
        leading = max(0, style.line_height - line.metrics.height)
        baseline = line_top + leading / 2 + line.metrics.ascent
        lines.append(
            WrappedLine(
                text=line.text,
                width=line.metrics.width,
                x=x,
                baseline_y=baseline,
                ascent=line.metrics.ascent,
                descent=line.metrics.descent,
            )
        )

    fits_height = content_height <= rect.height - insets.top - insets.bottom + 0.01
    return TextBlock(
        id=identifier,
        role=role,
        source_text=text,
        rect=rect,
        padding=insets,
        lines=tuple(lines),
        style=style,
        horizontal_alignment=horizontal_alignment,  # type: ignore[arg-type]
        vertical_alignment=vertical_alignment,  # type: ignore[arg-type]
        rotation=rotation,  # type: ignore[arg-type]
        overflow=measured.overflow or not fits_height,
        parent_id=parent_id,
    )


def place_vertical_text_block(
    *,
    identifier: str,
    role: TextRole,
    text: str,
    rect: Rect,
    style: TextStyle,
    measurer: TextMeasurer,
    parent_id: str | None = None,
) -> TextBlock:
    metrics = measurer.measure(text, style)
    center_x = rect.x + rect.width / 2
    center_y = rect.y + rect.height / 2
    line = WrappedLine(
        text=text,
        width=metrics.width,
        x=center_x - metrics.width / 2,
        baseline_y=center_y + (metrics.ascent - metrics.descent) / 2,
        ascent=metrics.ascent,
        descent=metrics.descent,
    )
    return TextBlock(
        id=identifier,
        role=role,
        source_text=text,
        rect=rect,
        lines=(line,),
        style=style,
        horizontal_alignment="center",
        vertical_alignment="middle",
        rotation=-90,
        overflow=metrics.width > rect.height + 0.01
        or metrics.height > rect.width + 0.01,
        parent_id=parent_id,
    )
