from __future__ import annotations

from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PIL import Image, ImageChops

from recipeflow.layout import validate_tabular_layout
from recipeflow.models.layout import Rect, TabularLayout

pytestmark = pytest.mark.visual

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPACT_ROOT = PROJECT_ROOT / "examples" / "golden" / "compact-table"
REQUIRED_SLUGS = (
    "espresso-brownies",
    "long-text",
    "measurement-systems",
    "branch-and-join",
    "split-and-reserve",
    "multiple-outputs",
    "setup-heavy",
    "many-narrow-operations",
    "long-completion-criteria",
    "unicode",
    "compact",
    "large",
)


def _layout(slug: str) -> TabularLayout:
    return TabularLayout.model_validate_json(
        (COMPACT_ROOT / f"{slug}.tabular-layout.json").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_compact_table_elements_are_complete_bounded_and_nonoverlapping(
    slug: str,
) -> None:
    layout = _layout(slug)
    canvas = Rect(x=0, y=0, width=layout.width, height=layout.height)
    boxes = {box.id: box for box in layout.boxes}

    assert layout.notation == "compact-table"
    assert validate_tabular_layout(layout) == ()
    assert all(canvas.contains(block.rect) and not block.overflow for block in layout.text_blocks)
    assert all(canvas.contains(box.rect) for box in layout.boxes)
    assert all(
        not first.rect.intersects(second.rect)
        for first, second in combinations(
            (box for box in layout.boxes if box.opaque),
            2,
        )
    )
    assert all(
        boxes[block.parent_id].rect.contains(block.rect)
        for block in layout.text_blocks
        if block.parent_id is not None
    )


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_compact_table_svg_and_png_match_the_resolved_canvas(slug: str) -> None:
    layout = _layout(slug)
    svg = ElementTree.parse(COMPACT_ROOT / f"{slug}.tabular.svg").getroot()
    assert svg.attrib["data-recipeflow-notation"] == "compact-table"
    assert tuple(float(value) for value in svg.attrib["viewBox"].split()) == (
        0.0,
        0.0,
        layout.width,
        layout.height,
    )

    with Image.open(COMPACT_ROOT / f"{slug}.tabular.png") as image:
        image.load()
        assert image.size == (round(layout.width * 2), round(layout.height * 2))
        rgb = image.convert("RGB")
        background = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
        assert ImageChops.difference(rgb, background).getbbox() is not None


def test_measurement_systems_whisk_span_excludes_butter_and_buttermilk() -> None:
    layout = _layout("measurement-systems")
    whisk = next(cell for cell in layout.operations if cell.operation_id == "op:combine-dry")
    lanes = {lane.initial_material_id: lane for lane in layout.lanes}

    assert whisk.rect is not None
    for identifier in ("butter", "buttermilk"):
        lane = lanes[identifier]
        lane_top = lane.y - lane.height / 2
        lane_bottom = lane.y + lane.height / 2
        assert whisk.rect.bottom <= lane_top + 0.01 or whisk.rect.y >= lane_bottom - 0.01
