from __future__ import annotations

import re
from collections import Counter
from itertools import combinations, pairwise
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from recipeflow.api import compile_document, parse_yaml
from recipeflow.layout import create_tabular_layout, validate_tabular_layout
from recipeflow.models import MaterialNode, OperationNode, RecipeGraph, TabularLayout
from recipeflow.models.layout import Rect
from recipeflow.renderers import RenderOptions, render_tabular_html

pytestmark = pytest.mark.visual

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = PROJECT_ROOT / "examples" / "golden"
LEDGER_ROOT = GOLDEN_ROOT / "ledger"
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
MATERIAL_INPUT_KINDS = {"consumes", "reserves", "optionally-applies"}


def _graph(slug: str) -> RecipeGraph:
    parsed = parse_yaml(
        (GOLDEN_ROOT / f"{slug}.recipe.yaml").read_text(encoding="utf-8")
    )
    assert parsed.document is not None, parsed.diagnostics
    compiled = compile_document(parsed.document, strict=True)
    assert compiled.graph is not None, compiled.diagnostics
    assert compiled.diagnostics == ()
    return compiled.graph


def _layout(slug: str) -> TabularLayout:
    return TabularLayout.model_validate_json(
        (LEDGER_ROOT / f"{slug}.tabular-layout.json").read_text(encoding="utf-8")
    )


def _blocks(layout: TabularLayout, role: str) -> tuple[str, ...]:
    return tuple(block.source_text for block in layout.text_blocks if block.role == role)


def _operation_by_lane(layout: TabularLayout) -> dict[int, str]:
    return {
        lane.index: operation.operation_id
        for lane, operation in zip(layout.lanes, layout.operations, strict=True)
    }


def _input_edges(graph: RecipeGraph) -> tuple[tuple[str, str], ...]:
    operations = {
        node.id: node
        for node in graph.nodes
        if isinstance(node, OperationNode) and node.operation_kind == "transform"
    }
    materials = {
        node.id for node in graph.nodes if isinstance(node, MaterialNode)
    }
    return tuple(
        (edge.target, edge.source)
        for edge in graph.edges
        if edge.kind.value in MATERIAL_INPUT_KINDS
        and edge.source in materials
        and edge.target in operations
    )


def _sheet_windows(layout: TabularLayout) -> tuple[Rect, ...]:
    breaks = sorted(
        path.points[0].y
        for path in layout.paths
        if "sheet-break" in path.style_class.split()
    )
    boundaries = (0.0, *breaks, layout.height)
    return tuple(
        Rect(x=0, y=start, width=layout.width, height=end - start)
        for start, end in pairwise(boundaries)
    )


def _produced_folios(layout: TabularLayout) -> dict[str, str]:
    boxes = {box.id: box for box in layout.boxes}
    blocks = {block.id: block for block in layout.text_blocks}
    folios: dict[str, str] = {}
    for material in layout.materials:
        if material.show_left_label or material.label_box_id is None:
            continue
        box = boxes[material.label_box_id]
        folio_blocks = [
            blocks[identifier]
            for identifier in box.text_block_ids
            if identifier.endswith(":folio")
        ]
        assert len(folio_blocks) == 1
        folios[material.material_id] = folio_blocks[0].source_text
    return folios


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_ledger_a4_print_corpus_is_complete_and_geometry_clean(slug: str) -> None:
    layout = _layout(slug)
    canvas = Rect(x=0, y=0, width=layout.width, height=layout.height)
    boxes = {box.id: box for box in layout.boxes}

    assert layout.notation == "ledger"
    assert layout.width == 794
    assert layout.height >= 1123 and layout.height % 1123 == 0
    assert layout.safe_margin == 40
    assert layout.diagnostics == ()
    assert validate_tabular_layout(layout) == ()
    assert all(canvas.contains(block.rect) and not block.overflow for block in layout.text_blocks)
    assert all(canvas.contains(box.rect) for box in layout.boxes)
    assert all(
        boxes[block.parent_id].rect.contains(block.rect)
        for block in layout.text_blocks
        if block.parent_id is not None
    )

    opaque = [box for box in layout.boxes if box.opaque]
    assert all(
        not first.rect.intersects(second.rect)
        for first, second in combinations(opaque, 2)
    )
    assert all(
        not first.rect.contains(second.rect)
        for first, second in combinations(opaque, 2)
    )
    assert all(
        not box.opaque
        for box in layout.boxes
        if box.style_class == "ledger-entry"
    )


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_every_graph_material_input_edge_has_exactly_one_consumed_line(slug: str) -> None:
    graph = _graph(slug)
    layout = _layout(slug)
    operation_by_lane = _operation_by_lane(layout)
    rendered = Counter(
        (operation_by_lane[material.lane], material.material_id)
        for material in layout.materials
        if material.show_left_label
    )

    assert rendered == Counter(_input_edges(graph))
    assert sum(len(operation.input_material_ids) for operation in layout.operations) == sum(
        rendered.values()
    )


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_setup_requirements_never_become_consumed_food(slug: str) -> None:
    graph = _graph(slug)
    layout = _layout(slug)
    setup_ids = {
        node.id
        for node in graph.nodes
        if isinstance(node, OperationNode) and node.operation_kind == "setup"
    }
    setup_tokens = {
        edge.target
        for edge in graph.edges
        if edge.source in setup_ids and edge.kind.value in {"produces", "reserves"}
    }
    consumed_material_ids = {
        segment.material_id for segment in layout.materials if segment.show_left_label
    }

    assert setup_ids.isdisjoint(consumed_material_ids)
    assert setup_tokens.isdisjoint(consumed_material_ids)
    assert all(card.operation_id in setup_ids for card in layout.setup)


def test_partial_draws_show_the_allocation_and_the_authored_total() -> None:
    for slug in ("many-narrow-operations", "large"):
        graph = _graph(slug)
        layout = _layout(slug)
        materials = {
            node.id: node for node in graph.nodes if isinstance(node, MaterialNode)
        }
        consumers = Counter(material_id for _, material_id in _input_edges(graph))
        blocks = {block.id: block.source_text for block in layout.text_blocks}

        for edge in graph.edges:
            if (
                edge.kind.value not in MATERIAL_INPUT_KINDS
                or edge.quantity is None
                or consumers[edge.source] < 2
            ):
                continue
            material = materials[edge.source]
            operation = next(
                cell for cell in layout.operations if cell.operation_id == edge.target
            )
            visible = {
                blocks[identifier]
                for identifier in operation.text_block_ids
                if identifier in blocks
            }
            assert edge.quantity in visible
            assert material.source_text in visible
            assert f"{edge.quantity} allocated · {material.quantity} authored total" in visible


def test_source_rows_preserve_authored_evidence() -> None:
    layout = _layout("large")
    visible_sources = _blocks(layout, "ingredient-source")
    visible_labels = _blocks(layout, "ingredient-label")

    assert "zest and juice of 3 limes" in visible_sources
    assert "75 mL neutral cooking oil, divided" in visible_sources
    assert "limes" in visible_labels

    long_text_labels = _blocks(_layout("long-text"), "ingredient-label")
    assert "skinned roasted hazelnuts with no bitter papery fragments remaining" in (
        long_text_labels
    )


def test_setup_parameters_are_explicitly_labeled() -> None:
    details = _blocks(_layout("setup-heavy"), "setup-detail")

    assert any("Time 15 min" in detail for detail in details)
    assert any("Temperature 200 °C" in detail for detail in details)


def test_duration_ranges_are_written_as_unambiguous_words() -> None:
    details = _blocks(_layout("compact"), "operation-detail")

    assert "Time 3 to 5 min" in details
    assert not any(".." in detail for detail in details)


def test_only_a_licensed_split_emits_an_allocation_balance() -> None:
    for slug in REQUIRED_SLUGS:
        graph = _graph(slug)
        layout = _layout(slug)
        split_ids = {
            node.id
            for node in graph.nodes
            if isinstance(node, OperationNode) and node.operation_type == "split"
        }
        balance_blocks = [
            block for block in layout.text_blocks if block.role == "allocation-balance"
        ]

        assert all(
            any(f":{operation_id}:" in block.id for operation_id in split_ids)
            for block in balance_blocks
        )
        if slug == "split-and-reserve":
            assert len(balance_blocks) == 1
            assert balance_blocks[0].source_text.startswith("300 mL = 250 mL + 50 mL")


def test_reserved_output_is_held_then_consumed() -> None:
    layout = _layout("split-and-reserve")
    blocks = {block.id: block.source_text for block in layout.text_blocks}
    produced = next(
        item
        for item in layout.materials
        if item.material_id == "reserved-cream" and not item.show_left_label
    )
    consumed = next(
        item
        for item in layout.materials
        if item.material_id == "reserved-cream" and item.show_left_label
    )

    assert produced.role == consumed.role == "reserved"
    assert produced.label_box_id is not None and consumed.label_box_id is not None
    assert "HELD" in {
        blocks[identifier]
        for identifier in next(
            box for box in layout.boxes if box.id == produced.label_box_id
        ).text_block_ids
    }
    assert "from reserve" in {
        blocks[identifier]
        for identifier in next(
            box for box in layout.boxes if box.id == consumed.label_box_id
        ).text_block_ids
    }


def test_multiple_finals_share_one_entry_and_all_folios_are_unique() -> None:
    layout = _layout("multiple-outputs")
    folios = _produced_folios(layout)
    final_entry = next(
        operation
        for operation in layout.operations
        if set(layout.final_material_ids) <= set(operation.output_material_ids)
    )

    assert set(final_entry.output_material_ids) == set(layout.final_material_ids)
    assert {folios[identifier] for identifier in layout.final_material_ids} == {"F1", "F2"}
    assert len(folios.values()) == len(set(folios.values()))


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_folios_and_dependency_reading_order_are_unique_and_deterministic(slug: str) -> None:
    graph = _graph(slug)
    layout = _layout(slug)
    folios = _produced_folios(layout)
    action_positions = {
        operation.operation_id: layout.reading_order.index(
            next(
                identifier
                for identifier in operation.text_block_ids
                if identifier.endswith(":action")
            )
        )
        for operation in layout.operations
    }
    producer = {
        edge.target: edge.source
        for edge in graph.edges
        if edge.kind.value in {"produces", "reserves", "discards"}
    }

    assert len(folios) == len(set(folios.values()))
    assert layout.reading_order == tuple(dict.fromkeys(layout.reading_order))
    for edge in graph.edges:
        if edge.kind.value in MATERIAL_INPUT_KINDS and edge.source in producer:
            source_operation = producer[edge.source]
            if source_operation in action_positions and edge.target in action_positions:
                assert action_positions[source_operation] < action_positions[edge.target]
        elif edge.kind.value == "precedes":
            if edge.source in action_positions and edge.target in action_positions:
                assert action_positions[edge.source] < action_positions[edge.target]

    options = RenderOptions(
        notation="ledger",
        theme="classic",
        page_size="A4",
        orientation="portrait",
        print_mode=True,
        outer_margin=40,
        scale=2,
        dpi=144,
    )
    regenerated = create_tabular_layout(graph, options.to_layout_options())
    assert _produced_folios(regenerated) == folios


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_screen_layout_has_clean_continuous_geometry_without_sheet_artifacts(
    slug: str,
) -> None:
    layout = create_tabular_layout(
        _graph(slug),
        RenderOptions(
            notation="ledger",
            theme="classic",
            width=794,
            print_mode=False,
            outer_margin=40,
        ).to_layout_options(),
    )

    assert layout.notation == "ledger"
    assert layout.width == 794
    assert layout.diagnostics == ()
    assert validate_tabular_layout(layout) == ()
    assert not any("sheet-break" in path.style_class.split() for path in layout.paths)
    assert not any(box.id.startswith("box:ledger:band:carried:") for box in layout.boxes)


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_carried_forward_band_is_exactly_the_later_material_frontier(slug: str) -> None:
    graph = _graph(slug)
    layout = _layout(slug)
    nodes = {node.id: node for node in graph.nodes}
    operation_rects = {
        operation.operation_id: operation.rect for operation in layout.operations
    }
    produced_by = {
        edge.target: edge.source
        for edge in graph.edges
        if edge.kind.value in {"produces", "reserves", "discards"}
    }
    consumers: dict[str, list[str]] = {}
    for operation_id, material_id in _input_edges(graph):
        consumers.setdefault(material_id, []).append(operation_id)
    folios = _produced_folios(layout)
    blocks = {block.id: block.source_text for block in layout.text_blocks}

    for sheet_number, break_path in enumerate(
        (
            path
            for path in layout.paths
            if "sheet-break" in path.style_class.split()
        ),
        start=1,
    ):
        break_y = break_path.points[0].y
        expected: list[str] = []
        for material_id, producer_id in produced_by.items():
            producer_rect = operation_rects.get(producer_id)
            if producer_rect is None or producer_rect.bottom > break_y:
                continue
            later_consumers = [
                identifier
                for identifier in consumers.get(material_id, ())
                if operation_rects[identifier].y >= break_y
            ]
            material = nodes[material_id]
            assert isinstance(material, MaterialNode)
            held_open = material.role.value == "reserved" and (
                not consumers.get(material_id) or later_consumers
            )
            if later_consumers or held_open:
                expected.append(f"{folios[material_id]} {material.label}")

        band_box = next(
            box
            for box in layout.boxes
            if box.id == f"box:ledger:band:carried:{sheet_number}"
        )
        assert len(band_box.text_block_ids) == 1
        text = blocks[band_box.text_block_ids[0]]
        inventory = text.split(" · ", maxsplit=1)[1].rsplit(" · ", maxsplit=1)[0]
        rendered = [] if inventory == "no open materials" else inventory.split("; ")

        assert rendered == expected


@pytest.mark.parametrize("slug", REQUIRED_SLUGS)
def test_print_html_has_one_unique_window_per_sheet_and_png_is_full_canvas(slug: str) -> None:
    layout = _layout(slug)
    windows = _sheet_windows(layout)
    boxes = {box.id: box for box in layout.boxes}
    options = RenderOptions(
        notation="ledger",
        theme="classic",
        page_size="A4",
        orientation="portrait",
        print_mode=True,
        outer_margin=40,
        scale=2,
        dpi=144,
    )
    html = render_tabular_html(layout, options)
    sheet_count = html.count('<section class="sheet"')
    identifiers = re.findall(r'\bid="([^"]+)"', html)

    assert len(windows) == round(layout.height / 1123)
    assert sheet_count == len(windows)
    assert len(identifiers) == len(set(identifiers))
    assert html.count('<section class="semantic"') == 1
    for operation in layout.operations:
        assert operation.box_ids
        for box_id in operation.box_ids:
            box = boxes[box_id]
            assert sum(window.contains(box.rect) for window in windows) == 1

    with Image.open(LEDGER_ROOT / f"{slug}.tabular.png") as image:
        image.load()
        assert image.format == "PNG"
        assert image.size == (round(layout.width * 2), round(layout.height * 2))
        rgb = image.convert("RGB")
        background = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
        assert ImageChops.difference(rgb, background).getbbox() is not None
