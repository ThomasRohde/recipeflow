from __future__ import annotations

import json
from html import unescape
from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PIL import Image, ImageChops

from recipeflow.layout import validate_tabular_layout
from recipeflow.models.layout import Rect, TabularLayout

pytestmark = pytest.mark.visual

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = PROJECT_ROOT / "examples" / "golden"
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
SVG_NAMESPACE = {"svg": "http://www.w3.org/2000/svg"}


def _layout(slug: str) -> TabularLayout:
    return TabularLayout.model_validate_json(
        (GOLDEN_ROOT / f"{slug}.tabular-layout.json").read_text(encoding="utf-8")
    )


def _normalized(value: str) -> str:
    return " ".join(value.split())


def _text_sources(layout: TabularLayout, role: str) -> set[str]:
    return {
        block.source_text
        for block in layout.text_blocks
        if block.role == role
    }


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_every_element_is_inside_the_canvas_without_overflow_or_collisions(
    slug: str,
) -> None:
    layout = _layout(slug)
    canvas = Rect(x=0, y=0, width=layout.width, height=layout.height)
    boxes = {box.id: box for box in layout.boxes}

    assert validate_tabular_layout(layout) == ()
    assert all(canvas.contains(block.rect) for block in layout.text_blocks)
    assert all(not block.overflow for block in layout.text_blocks)
    assert all(canvas.contains(box.rect) for box in layout.boxes)
    for path in layout.paths:
        radius = path.stroke_width / 2
        assert all(
            radius <= point.x <= layout.width - radius
            and radius <= point.y <= layout.height - radius
            for point in path.points
        )

    for block in layout.text_blocks:
        assert "…" not in "".join(line.text for line in block.lines)
        assert _normalized(" ".join(line.text for line in block.lines)) == _normalized(
            block.source_text
        )
        if block.parent_id is not None:
            assert boxes[block.parent_id].rect.contains(block.rect)

    opaque = [box for box in layout.boxes if box.opaque]
    assert all(
        not first.rect.intersects(second.rect)
        for first, second in combinations(opaque, 2)
    )

    operation_boxes = [box for box in layout.boxes if box.kind == "operation"]
    for block in layout.text_blocks:
        unrelated = [
            operation
            for operation in operation_boxes
            if operation.id != block.parent_id
        ]
        assert all(
            not block.rect.intersects(operation.rect) for operation in unrelated
        )


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_setup_and_final_text_stays_in_its_semantic_area(slug: str) -> None:
    layout = _layout(slug)
    boxes = {box.id: box for box in layout.boxes}
    setup_area = Rect(
        x=0,
        y=layout.header_height,
        width=layout.width,
        height=layout.setup_height,
    )

    for card in layout.setup:
        assert card.rect is not None
        assert setup_area.contains(card.rect)
        for text_id in card.text_block_ids:
            block = next(item for item in layout.text_blocks if item.id == text_id)
            assert card.rect.contains(block.rect)

    final_boxes = [box for box in layout.boxes if box.kind == "final-output"]
    assert {box.id for box in final_boxes} == {
        f"box:material:{material_id}" for material_id in layout.final_material_ids
    }
    for final_box in final_boxes:
        for text_id in final_box.text_block_ids:
            block = next(item for item in layout.text_blocks if item.id == text_id)
            assert block.role == "final-label"
            assert final_box.rect.contains(block.rect)
            assert boxes[block.parent_id or ""] == final_box


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_svg_is_valid_encloses_content_and_recovers_complete_source_text(
    slug: str,
) -> None:
    layout = _layout(slug)
    svg_text = (GOLDEN_ROOT / f"{slug}.tabular.svg").read_text(encoding="utf-8")
    root = ElementTree.fromstring(svg_text)

    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert tuple(float(item) for item in root.attrib["viewBox"].split()) == (
        0.0,
        0.0,
        layout.width,
        layout.height,
    )
    assert float(root.attrib["width"]) == layout.width
    assert float(root.attrib["height"]) == layout.height
    assert root.find("svg:title", SVG_NAMESPACE) is not None
    assert root.find("svg:desc", SVG_NAMESPACE) is not None

    metadata_node = root.find("svg:metadata", SVG_NAMESPACE)
    assert metadata_node is not None and metadata_node.text
    metadata = json.loads(metadata_node.text)
    assert tuple(metadata["reading_order"]) == layout.reading_order
    assert metadata["text"] == {
        block.id: block.source_text for block in layout.text_blocks
    }
    rendered_text = {
        node.attrib["id"]: node.attrib["aria-label"]
        for node in root.findall("svg:text", SVG_NAMESPACE)
    }
    assert rendered_text == {
        block.id: block.source_text for block in layout.text_blocks
    }

    html_text = unescape(
        (GOLDEN_ROOT / f"{slug}.tabular.html").read_text(encoding="utf-8")
    )
    assert all(block.source_text in html_text for block in layout.text_blocks)


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_png_dimensions_match_layout_and_image_contains_visible_content(
    slug: str,
) -> None:
    layout = _layout(slug)
    path = GOLDEN_ROOT / f"{slug}.tabular.png"

    with Image.open(path) as image:
        image.load()
        assert image.format == "PNG"
        assert image.size == (round(layout.width * 2), round(layout.height * 2))
        rgb = image.convert("RGB")
        background = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
        assert ImageChops.difference(rgb, background).getbbox() is not None


def test_measurement_systems_groups_first_operation_inputs_without_false_join() -> None:
    layout = _layout("measurement-systems")
    initial_materials = tuple(
        lane.initial_material_id
        for lane in layout.lanes
        if lane.initial_material_id is not None
    )
    whisk = next(
        cell for cell in layout.operations if cell.operation_id == "op:combine-dry"
    )
    butter_lane = next(
        lane for lane in layout.lanes if lane.initial_material_id == "butter"
    )
    buttermilk_lane = next(
        lane for lane in layout.lanes if lane.initial_material_id == "buttermilk"
    )

    assert initial_materials[:3] == ("baking-powder", "flour", "salt")
    assert whisk.rect is not None
    assert whisk.rect.bottom < butter_lane.y - butter_lane.height / 2
    assert whisk.rect.bottom < buttermilk_lane.y - buttermilk_lane.height / 2


def test_black_box_semantics_are_visible_in_committed_golden_layouts() -> None:
    split = _layout("split-and-reserve")
    assert "Yield: 6 glasses" in _text_sources(split, "recipe-yield")
    assert {
        "250 mL · cream for the mousse base",
        "50 mL · reserved cream for the final rosette",
    } <= _text_sources(split, "material-label")
    assert "Uses: 300 mL cold heavy cream" in _text_sources(
        split,
        "operation-input-quantity",
    )

    narrow = _layout("many-narrow-operations")
    assert {
        "Uses: 30 mL water for sealing and boiling",
        "Uses: 2970 mL water for sealing and boiling",
    } <= _text_sources(narrow, "operation-input-quantity")

    setup = _layout("setup-heavy")
    assert "Target: six 180 mL ramekins" in _text_sources(
        setup,
        "setup-target",
    )
    assert {
        "Required by: fill and level",
        "Required by: transfer and bake",
    } <= _text_sources(setup, "setup-required-by")
    setup_paths = [
        path for path in setup.paths if path.id.startswith("path:setup:")
    ]
    assert len({path.points[1].y for path in setup_paths}) == len(setup_paths)

    large = _layout("large")
    assert {
        "Uses: 30 mL neutral cooking oil",
        "Uses: 45 mL neutral cooking oil",
    } <= _text_sources(large, "operation-input-quantity")
    assert (
        "Uses: 500 mL unsalted chicken stock · 800 g peeled plum tomatoes"
        in _text_sources(large, "operation-input-quantity")
    )

    completion = _layout("long-completion-criteria")
    assert "Yield: 450 mL sauce" in _text_sources(
        completion,
        "recipe-yield",
    )

    compact = _layout("compact")
    compact_operation = next(
        operation
        for operation in compact.operations
        if operation.operation_id == "op:toast"
    )
    assert compact_operation.duration == "3..5 min"
    assert "Time: 3 to 5 min" in _text_sources(compact, "operation-detail")
