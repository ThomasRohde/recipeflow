from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from recipeflow.models.layout import TextStyle
from recipeflow.typography.measurement import TextMeasurer, TextMetrics


@dataclass(frozen=True)
class MeasuredLine:
    text: str
    metrics: TextMetrics


@dataclass(frozen=True)
class MeasuredText:
    source_text: str
    lines: tuple[MeasuredLine, ...]
    width: float
    height: float
    overflow: bool = False


def wrap_text(
    text: str,
    max_width: float,
    style: TextStyle,
    measurer: TextMeasurer,
    mode: Literal["word", "grapheme"] = "word",
) -> MeasuredText:
    """Wrap text without truncation, preserving explicit line breaks."""
    if max_width <= 0:
        raise ValueError("max_width must be greater than zero")

    output: list[MeasuredLine] = []
    for paragraph in text.split("\n"):
        if mode == "grapheme":
            output.extend(_wrap_graphemes(paragraph, max_width, style, measurer))
        else:
            output.extend(_wrap_paragraph(paragraph, max_width, style, measurer))

    if not output:
        output.append(_line("", style, measurer))
    width = max((line.metrics.width for line in output), default=0)
    return MeasuredText(
        source_text=text,
        lines=tuple(output),
        width=width,
        height=len(output) * style.line_height,
        overflow=any(line.metrics.width > max_width + 0.01 for line in output),
    )


def _wrap_graphemes(
    paragraph: str,
    max_width: float,
    style: TextStyle,
    measurer: TextMeasurer,
) -> list[MeasuredLine]:
    if not paragraph:
        return [_line("", style, measurer)]
    fragments = _break_token(paragraph, max_width, style, measurer)
    return [_line(fragment, style, measurer) for fragment in fragments]


def _wrap_paragraph(
    paragraph: str,
    max_width: float,
    style: TextStyle,
    measurer: TextMeasurer,
) -> list[MeasuredLine]:
    if not paragraph:
        return [_line("", style, measurer)]

    words = re.findall(r"\S+", paragraph)
    if not words:
        return [_line("", style, measurer)]

    lines: list[MeasuredLine] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if measurer.measure(candidate, style).width <= max_width:
            current = candidate
            continue
        if current:
            lines.append(_line(current, style, measurer))
            current = ""
        if measurer.measure(word, style).width <= max_width:
            current = word
            continue
        fragments = _break_token(word, max_width, style, measurer)
        lines.extend(_line(fragment, style, measurer) for fragment in fragments[:-1])
        current = fragments[-1]
    if current or not lines:
        lines.append(_line(current, style, measurer))
    return lines


def _break_token(
    token: str,
    max_width: float,
    style: TextStyle,
    measurer: TextMeasurer,
) -> list[str]:
    fragments: list[str] = []
    current = ""
    for cluster in grapheme_clusters(token):
        candidate = current + cluster
        if current and measurer.measure(candidate, style).width > max_width:
            fragments.append(current)
            current = cluster
        else:
            current = candidate
    if current:
        fragments.append(current)
    return fragments or [""]


def grapheme_clusters(text: str) -> tuple[str, ...]:
    """Small dependency-free grapheme approximation for safe fallback breaks."""
    clusters: list[str] = []
    join_next = False
    for character in text:
        variation_selector = "\ufe00" <= character <= "\ufe0f"
        if (
            not clusters
            or (
                not unicodedata.combining(character)
                and not variation_selector
                and character != "\u200d"
                and not join_next
            )
        ):
            clusters.append(character)
        else:
            clusters[-1] += character
        join_next = character == "\u200d"
    return tuple(clusters)


def _line(
    text: str,
    style: TextStyle,
    measurer: TextMeasurer,
) -> MeasuredLine:
    return MeasuredLine(text=text, metrics=measurer.measure(text, style))
