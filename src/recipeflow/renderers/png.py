from __future__ import annotations

import importlib
from io import BytesIO
from typing import Any

from PIL import Image

from recipeflow.layout import get_theme
from recipeflow.models.common import Diagnostic, Severity
from recipeflow.models.layout import TabularLayout
from recipeflow.renderers.options import RenderOptions
from recipeflow.renderers.svg import render_tabular_svg


class PngDependencyError(RuntimeError):
    def __init__(self) -> None:
        self.diagnostic = Diagnostic(
            code="RF510",
            severity=Severity.ERROR,
            path="/render/png",
            message="PNG rendering requires the optional resvg-py dependency.",
            suggestions=("Install RecipeFlow with: pip install 'recipeflow[png]'",),
        )
        super().__init__(self.diagnostic.message)


def render_tabular_png(
    layout: TabularLayout,
    options: RenderOptions | None = None,
) -> bytes:
    selected = options or RenderOptions(theme=layout.theme, notation=layout.notation)
    try:
        resvg_py: Any = importlib.import_module("resvg_py")
    except (ImportError, OSError) as error:
        raise PngDependencyError() from error

    svg = render_tabular_svg(layout, selected)
    output_width, output_height = selected.raster_dimensions(
        layout.width,
        layout.height,
    )
    result = resvg_py.svg_to_bytes(
        svg_string=svg,
        width=output_width,
        height=output_height,
        dpi=selected.dpi,
        background=selected.background,
    )
    if not isinstance(result, bytes):
        raise RuntimeError("resvg-py did not return PNG bytes.")
    return _ensure_dimensions(
        result,
        width=output_width,
        height=output_height,
        background=selected.background
        or (
            get_theme(selected.theme).table_background
            if layout.notation == "compact-table"
            else get_theme(selected.theme).background
        ),
        dpi=selected.dpi,
    )


def _ensure_dimensions(
    png: bytes,
    *,
    width: int,
    height: int,
    background: str,
    dpi: int,
) -> bytes:
    """Pad resvg's aspect-fit result to the exact public raster contract.

    Integer target dimensions cannot always express the layout's floating-point
    aspect ratio exactly. resvg correctly preserves that ratio and may return an
    image a few pixels smaller on one axis. It can also round one axis one pixel
    upward. Padding smaller axes and trimming only that single outer pixel keeps
    the SVG geometry undistorted while making requested dimensions deterministic.
    """

    with Image.open(BytesIO(png)) as source:
        source.load()
        if source.size == (width, height):
            return png
        if source.width > width + 1 or source.height > height + 1:
            raise RuntimeError(
                "resvg-py returned PNG dimensions larger than the requested size: "
                f"{source.width}x{source.height} > {width}x{height}."
            )

        mode = "RGBA" if "A" in source.getbands() else "RGB"
        converted = source.convert(mode)
        crop_left = max((source.width - width) // 2, 0)
        crop_top = max((source.height - height) // 2, 0)
        converted = converted.crop(
            (
                crop_left,
                crop_top,
                crop_left + min(source.width, width),
                crop_top + min(source.height, height),
            )
        )
        canvas = Image.new(mode, (width, height), background)
        offset = (
            (width - converted.width) // 2,
            (height - converted.height) // 2,
        )
        canvas.paste(converted, offset)
        output = BytesIO()
        canvas.save(output, format="PNG", dpi=(dpi, dpi))
        return output.getvalue()
