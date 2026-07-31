from __future__ import annotations

import importlib
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from recipeflow.models.layout import TextStyle


@dataclass(frozen=True)
class TextMetrics:
    width: float
    ascent: float
    descent: float

    @property
    def height(self) -> float:
        return self.ascent + self.descent


class TextMeasurer(Protocol):
    """Renderer-independent interface for measuring a shaped line of text."""

    def measure(self, text: str, style: TextStyle) -> TextMetrics: ...


class DeterministicTextMeasurer:
    """Portable fallback using per-glyph Unicode metrics.

    This is deliberately not a character-count estimate: each glyph receives a
    width based on its Unicode width class and typographic category. Production
    installs should prefer :class:`PillowTextMeasurer`; this implementation
    keeps layout deterministic when the optional imaging dependency is absent.
    """

    _narrow = frozenset(".,:;!|iIl'`")
    _wide = frozenset("MW@#%&")

    def measure(self, text: str, style: TextStyle) -> TextMetrics:
        em = style.font_size
        width = sum(self._glyph_advance(character, em) for character in text)
        if style.font_weight >= 600:
            width *= 1.025
        return TextMetrics(
            width=round(width, 3),
            ascent=round(em * 0.78, 3),
            descent=round(em * 0.22, 3),
        )

    def _glyph_advance(self, character: str, em: float) -> float:
        if character in "\r\n" or unicodedata.combining(character):
            return 0
        if character.isspace():
            return em * 0.33
        if character in self._narrow:
            return em * 0.29
        if character in self._wide:
            return em * 0.88
        if unicodedata.east_asian_width(character) in {"W", "F"}:
            return em
        category = unicodedata.category(character)
        if category.startswith("P"):
            return em * 0.42
        if category.startswith("N"):
            return em * 0.56
        if category.startswith("S"):
            return em * 0.72
        return em * 0.56


class PillowTextMeasurer:
    """Font-backed measurement using Pillow without bundling font files."""

    def __init__(self, font_path: str | Path | None = None) -> None:
        self._image_font: Any = importlib.import_module("PIL.ImageFont")
        self._font_path = str(font_path) if font_path else self._resolve_font_path()
        self._cache: dict[tuple[str, float, int], Any] = {}

    @classmethod
    def available(cls) -> bool:
        try:
            importlib.import_module("PIL.ImageFont")
        except ImportError:
            return False
        return True

    def measure(self, text: str, style: TextStyle) -> TextMetrics:
        font = self._font(style)
        probe = text or " "
        left, _top, right, _bottom = font.getbbox(probe)
        ascent, descent = font.getmetrics()
        width = 0.0 if not text else float(right - left)
        return TextMetrics(
            width=round(width, 3),
            ascent=float(ascent),
            descent=float(descent),
        )

    def _font(self, style: TextStyle) -> Any:
        key = (self._font_path, style.font_size, style.font_weight)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        font = self._image_font.truetype(
            self._font_path,
            size=max(1, round(style.font_size)),
        )
        self._cache[key] = font
        return font

    @staticmethod
    def _resolve_font_path() -> str:
        windows = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        candidates = (
            windows / "segoeui.ttf",
            windows / "arial.ttf",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
            Path("/Library/Fonts/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        )
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        raise RuntimeError(
            "Pillow is installed, but no supported system font was found. "
            "Install DejaVu Sans, Arial, or Segoe UI."
        )


class UnicodeSafeTextMeasurer:
    """Conservatively cover glyphs that a rasterizer resolves through fallback fonts.

    Pillow measures missing glyphs with the primary font's replacement glyph,
    while SVG rasterizers may substitute a wider script-specific font. Taking
    the greater of the primary-font metrics and a padded Unicode estimate keeps
    CJK, Greek, Cyrillic, Arabic, and symbol runs inside their negotiated boxes.
    """

    def __init__(
        self,
        primary: TextMeasurer,
        *,
        fallback_safety_factor: float = 1.15,
    ) -> None:
        if fallback_safety_factor < 1:
            raise ValueError("fallback_safety_factor must be at least one")
        self._primary = primary
        self._fallback = DeterministicTextMeasurer()
        self._fallback_safety_factor = fallback_safety_factor

    def measure(self, text: str, style: TextStyle) -> TextMetrics:
        primary = self._primary.measure(text, style)
        if not _uses_fallback_sensitive_script(text):
            return primary
        fallback = self._fallback.measure(text, style)
        return TextMetrics(
            width=round(
                max(
                    primary.width,
                    fallback.width * self._fallback_safety_factor,
                ),
                3,
            ),
            ascent=max(primary.ascent, fallback.ascent),
            descent=max(primary.descent, fallback.descent),
        )


def _uses_fallback_sensitive_script(text: str) -> bool:
    for character in text:
        codepoint = ord(character)
        if (
            0x0370 <= codepoint <= 0x052F  # Greek and Cyrillic
            or 0x0590 <= codepoint <= 0x08FF  # Hebrew and Arabic
            or 0x1100 <= codepoint <= 0x11FF  # Hangul Jamo
            or 0x2E80 <= codepoint <= 0x9FFF  # CJK and related blocks
            or 0xAC00 <= codepoint <= 0xD7AF  # Hangul syllables
            or 0xF900 <= codepoint <= 0xFAFF  # CJK compatibility ideographs
            or 0x1F000 <= codepoint <= 0x1FAFF  # Symbols and emoji
            or unicodedata.east_asian_width(character) in {"W", "F"}
        ):
            return True
    return False


def default_text_measurer(*, prefer_pillow: bool = True) -> TextMeasurer:
    if prefer_pillow and PillowTextMeasurer.available():
        try:
            return UnicodeSafeTextMeasurer(PillowTextMeasurer())
        except RuntimeError:
            pass
    fallback = DeterministicTextMeasurer()
    return UnicodeSafeTextMeasurer(fallback)
