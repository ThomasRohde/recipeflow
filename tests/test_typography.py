from recipeflow.models.layout import TextStyle
from recipeflow.typography import (
    DeterministicTextMeasurer,
    TextMetrics,
    UnicodeSafeTextMeasurer,
    grapheme_clusters,
    wrap_text,
)


def test_measurement_uses_glyph_metrics_instead_of_character_count() -> None:
    measurer = DeterministicTextMeasurer()
    style = TextStyle(font_size=14)

    assert measurer.measure("WWW", style).width > measurer.measure("iii", style).width


def test_wrapping_preserves_complete_source_and_breaks_long_tokens() -> None:
    measurer = DeterministicTextMeasurer()
    style = TextStyle(font_size=14, line_height=18)
    source = "crème brûlée\nsupercalifragilisticexpialidocious"

    measured = wrap_text(source, 72, style, measurer)

    assert measured.source_text == source
    assert len(measured.lines) >= 4
    assert not measured.overflow
    assert all(line.metrics.width <= 72.01 for line in measured.lines)


def test_grapheme_breaking_keeps_combining_marks_and_emoji_joiners_together() -> None:
    clusters = grapheme_clusters("e\u0301👩\u200d🍳")

    assert clusters == ("e\u0301", "👩\u200d🍳")


def test_unicode_safe_measurement_covers_wider_rasterizer_fallback_glyphs() -> None:
    class UnderMeasuringFont:
        def measure(self, text: str, style: TextStyle) -> TextMetrics:
            return TextMetrics(width=len(text) * 3, ascent=8, descent=2)

    style = TextStyle(font_size=14)
    safe = UnicodeSafeTextMeasurer(UnderMeasuringFont())
    plain = safe.measure("cafe", style)
    fallback = safe.measure("καραμέλα · コーヒー", style)

    assert plain.width == 12
    assert fallback.width > len("καραμέλα · コーヒー") * 3
    assert fallback.height >= 14


def test_wrap_mode_switches_between_word_and_grapheme_boundaries() -> None:
    class FixedWidthMeasurer:
        def measure(self, text: str, style: TextStyle) -> TextMetrics:
            return TextMetrics(width=len(text), ascent=8, descent=2)

    style = TextStyle(font_size=14, line_height=12)
    word = wrap_text(
        "alpha beta",
        5,
        style,
        FixedWidthMeasurer(),
        mode="word",
    )
    grapheme = wrap_text(
        "alpha beta",
        5,
        style,
        FixedWidthMeasurer(),
        mode="grapheme",
    )

    assert [line.text for line in word.lines] == ["alpha", "beta"]
    assert [line.text for line in grapheme.lines] == ["alpha", " beta"]
