from io import BytesIO
from xml.etree import ElementTree

import pytest
from PIL import Image
from test_tabular_layout_engine import _compiled_fixture, _graph

from recipeflow.layout import create_tabular_layout
from recipeflow.renderers import (
    PngDependencyError,
    RenderOptions,
    render_tabular_html,
    render_tabular_png,
    render_tabular_svg,
)
from recipeflow.typography import DeterministicTextMeasurer


def _layout():
    return create_tabular_layout(
        _graph(),
        text_measurer=DeterministicTextMeasurer(),
    )


def test_svg_is_deterministic_accessible_and_uses_resolved_tspans() -> None:
    layout = _layout()

    first = render_tabular_svg(layout)
    second = render_tabular_svg(layout)

    assert first == second
    assert "<title id=" in first
    assert "<desc id=" in first
    assert "<metadata id=" in first
    assert "<tspan" in first
    assert "}}." not in first
    assert "no visible dry pockets remain" in first
    assert "finished crème brûlée crêpes" in first
    ElementTree.fromstring(first)


def test_html_has_semantic_fallback_responsive_overflow_and_print_rules() -> None:
    html = render_tabular_html(_layout())

    assert '<html lang="en">' in html
    assert 'class="semantic"' in html
    assert "overflow:auto" in html
    assert "@media print" in html
    assert "finished crème brûlée crêpes" in html


def test_themes_change_rendered_svg_palette() -> None:
    layout = _layout()

    classic = render_tabular_svg(layout, RenderOptions(theme="classic"))
    modern = render_tabular_svg(layout, RenderOptions(theme="modern"))

    assert classic != modern
    assert "#f2eadf" in classic
    assert "#e8eef8" in modern


def test_svg_accessibility_metadata_recovers_authored_detail_and_unicode() -> None:
    long_text = render_tabular_svg(
        create_tabular_layout(_compiled_fixture("long-text"))
    )
    unicode = render_tabular_svg(
        create_tabular_layout(_compiled_fixture("unicode"))
    )

    assert (
        "one 28 cm all-butter sweet pastry shell, blind-baked until deeply "
        "golden at the edges and completely cooled in its fluted tart pan"
    ) in long_text
    assert "completely cooled in its fluted tart pan" in long_text
    assert (
        "Allow at least twenty minutes after the thermostat first signals "
        "readiness so the baking stone and oven walls reach an even temperature."
    ) in long_text
    assert "crème brûlée au café · καραμέλα · コーヒー" in unicode


def test_raster_dimensions_round_both_axes_from_one_uniform_scale() -> None:
    assert RenderOptions(scale=2).raster_dimensions(1527, 367.726) == (3054, 735)
    assert RenderOptions(width=800, scale=2).raster_dimensions(1000, 501) == (
        2000,
        1002,
    )
    assert RenderOptions(width=1200, scale=2).raster_dimensions(1000, 501) == (
        2400,
        1202,
    )


def test_png_missing_dependency_has_precise_rf510_diagnostic(monkeypatch) -> None:
    def missing(name: str):
        assert name == "resvg_py"
        raise ImportError(name)

    monkeypatch.setattr("recipeflow.renderers.png.importlib.import_module", missing)

    with pytest.raises(PngDependencyError) as captured:
        render_tabular_png(_layout())
    assert captured.value.diagnostic.code == "RF510"
    assert "recipeflow[png]" in captured.value.diagnostic.suggestions[0]


def test_png_is_derived_from_svg_with_requested_dimensions(monkeypatch) -> None:
    received: dict[str, object] = {}

    class FakeResvg:
        @staticmethod
        def svg_to_bytes(**kwargs):
            received.update(kwargs)
            output = BytesIO()
            Image.new(
                "RGB",
                (int(kwargs["width"]) - 3, int(kwargs["height"])),
                "#f2eadf",
            ).save(output, format="PNG")
            return output.getvalue()

    monkeypatch.setattr(
        "recipeflow.renderers.png.importlib.import_module",
        lambda name: FakeResvg,
    )
    png = render_tabular_png(
        _layout(),
        RenderOptions(width=800, scale=2, dpi=192, background="#ffffff"),
    )

    assert png.startswith(b"\x89PNG")
    assert received["width"] == round(_layout().width * 2)
    assert received["dpi"] == 192
    assert str(received["svg_string"]).startswith("<svg")
    with Image.open(BytesIO(png)) as image:
        assert image.size == (received["width"], received["height"])


def test_png_accepts_resvg_single_pixel_rounding_overshoot(monkeypatch) -> None:
    class FakeResvg:
        @staticmethod
        def svg_to_bytes(**kwargs):
            output = BytesIO()
            Image.new(
                "RGB",
                (int(kwargs["width"]), int(kwargs["height"]) + 1),
                "#f2eadf",
            ).save(output, format="PNG")
            return output.getvalue()

    monkeypatch.setattr(
        "recipeflow.renderers.png.importlib.import_module",
        lambda name: FakeResvg,
    )
    options = RenderOptions(width=320, scale=2)
    expected = options.raster_dimensions(_layout().width, _layout().height)

    png = render_tabular_png(_layout(), options)

    with Image.open(BytesIO(png)) as image:
        assert image.size == expected
