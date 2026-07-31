from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from heapq import heappop, heappush
from typing import Literal

from recipeflow.layout.options import LayoutOptions
from recipeflow.layout.text import (
    measure_text_block,
    place_text_block,
    place_vertical_text_block,
)
from recipeflow.layout.themes import LayoutTheme, get_theme
from recipeflow.layout.validation import validate_tabular_layout
from recipeflow.models.common import Provenance
from recipeflow.models.graph import MaterialNode, OperationNode, RecipeGraph
from recipeflow.models.layout import (
    Insets,
    Lane,
    LayoutBox,
    LayoutBoxKind,
    MaterialSegment,
    OperationCell,
    Point,
    Rect,
    RoutedPath,
    SetupCard,
    TabularLayout,
    TextBlock,
    TextRole,
    TextStyle,
)
from recipeflow.typography import TextMeasurer, default_text_measurer, wrap_text


@dataclass(frozen=True)
class _GraphView:
    materials: dict[str, MaterialNode]
    operations: dict[str, OperationNode]
    transform_order: tuple[str, ...]
    setup_order: tuple[str, ...]
    consumes: dict[str, tuple[str, ...]]
    produces: dict[str, tuple[str, ...]]
    requires: dict[str, tuple[str, ...]]
    producer: dict[str, str]
    consumers: dict[str, tuple[str, ...]]
    input_quantities: dict[str, tuple[tuple[str, str], ...]]


@dataclass(frozen=True)
class _OperationSize:
    width: float
    height: float
    orientation: str
    action_height: float
    input_quantity_height: float
    detail_height: float
    until_height: float


@dataclass(frozen=True)
class _LabelSize:
    width: float
    height: float


@dataclass(frozen=True)
class _TextSpec:
    suffix: str
    role: TextRole
    text: str
    style: TextStyle
    alignment: Literal["start", "center", "end"] = "end"


def create_flow_layout(
    graph: RecipeGraph,
    options: LayoutOptions | None = None,
    *,
    text_measurer: TextMeasurer | None = None,
) -> TabularLayout:
    """Create a complete renderer-neutral tabular layout.

    All text is measured and wrapped here. Renderers consume the resulting
    boxes, paths, and absolute baselines without applying layout policy.
    """
    selected = options or LayoutOptions()
    measurer = text_measurer or default_text_measurer()
    theme = _scaled_theme(get_theme(selected.theme), selected)
    view = _index_graph(graph)
    lane_of, lane_count, ingredient_ids = _allocate_lanes(view)

    label_width = _ingredient_column_width(
        ingredient_ids,
        view,
        selected,
        theme,
        measurer,
    )
    material_sizes = _measure_material_labels(view, selected, theme, measurer)
    operation_sizes = _measure_operations(
        view,
        lane_of,
        selected,
        theme,
        measurer,
    )
    operation_rect_x, canvas_width = _allocate_columns(
        view,
        operation_sizes,
        material_sizes,
        label_width,
        selected,
    )
    canvas_width = max(canvas_width, selected.preferred_width or 0)

    header_blocks, header_height = _place_header(
        graph.title,
        graph.yield_text,
        canvas_width,
        selected,
        theme,
        measurer,
    )
    setup_cards, setup_boxes, setup_text, setup_height = _place_setup_cards(
        view,
        graph,
        canvas_width,
        header_height,
        selected,
        theme,
        measurer,
    )

    row_heights = _measure_rows(
        view,
        lane_of,
        lane_count,
        ingredient_ids,
        label_width,
        material_sizes,
        operation_sizes,
        selected,
        theme,
        measurer,
    )
    lane_top = header_height + setup_height
    lane_y = _lane_centers(row_heights, lane_top)

    operation_cells, operation_boxes, operation_text = _place_operations(
        view,
        lane_of,
        lane_y,
        row_heights,
        operation_rect_x,
        operation_sizes,
        selected,
        theme,
        measurer,
    )
    operation_rects = {
        cell.operation_id: cell.rect
        for cell in operation_cells
        if cell.rect is not None
    }

    (
        material_segments,
        material_boxes,
        material_text,
        material_paths,
    ) = _place_materials(
        view,
        lane_of,
        lane_y,
        ingredient_ids,
        label_width,
        material_sizes,
        operation_rects,
        canvas_width,
        selected,
        theme,
        measurer,
    )
    dependency_paths = _setup_dependency_paths(
        setup_cards,
        view,
        operation_rects,
        lane_top,
    )

    bottom = lane_top + sum(row_heights) + selected.safe_margin
    layout = TabularLayout(
        title=graph.title,
        notation="flow",
        width=round(canvas_width, 3),
        height=round(bottom, 3),
        label_width=round(label_width, 3),
        header_height=round(header_height, 3),
        setup_height=round(setup_height, 3),
        row_height=round(max(row_heights, default=selected.minimum_row_height), 3),
        lanes=tuple(
            Lane(
                index=index,
                y=round(lane_y[index], 3),
                height=round(row_heights[index], 3),
                initial_material_id=(
                    ingredient_ids[index] if index < len(ingredient_ids) else None
                ),
            )
            for index in range(lane_count)
        ),
        materials=tuple(material_segments),
        operations=tuple(operation_cells),
        setup=tuple(setup_cards),
        final_material_ids=tuple(graph.final_material_ids),
        safe_margin=selected.safe_margin,
        theme=selected.theme,
        text_blocks=(
            *header_blocks,
            *setup_text,
            *material_text,
            *operation_text,
        ),
        boxes=(
            LayoutBox(
                id="box:title",
                kind="title",
                rect=_containing_rect(header_blocks),
                text_block_ids=tuple(block.id for block in header_blocks),
                style_class="title",
                opaque=False,
                collision_group="header",
            ),
            *setup_boxes,
            *material_boxes,
            *operation_boxes,
        ),
        paths=(
            *_guide_paths(lane_y, canvas_width, selected),
            *material_paths,
            *dependency_paths,
        ),
        reading_order=(
            *(block.id for block in header_blocks),
            *(block.id for block in setup_text),
            *(block.id for block in material_text),
            *(block.id for block in operation_text),
        ),
    )
    return layout.model_copy(update={"diagnostics": validate_tabular_layout(layout)})


def _scaled_theme(theme: LayoutTheme, options: LayoutOptions) -> LayoutTheme:
    def style(source: TextStyle, size: float) -> TextStyle:
        resolved_size = max(options.minimum_font_size, size)
        return source.model_copy(
            update={
                "font_size": resolved_size,
                "line_height": resolved_size * options.line_height,
            }
        )

    base = options.base_font_size
    return replace(
        theme,
        title_style=style(theme.title_style, base * 1.93),
        label_style=style(theme.label_style, base),
        quantity_style=style(theme.quantity_style, base - 2),
        operation_style=style(theme.operation_style, base - 1),
        detail_style=style(theme.detail_style, base - 3),
    )


def _index_graph(graph: RecipeGraph) -> _GraphView:
    materials = {
        node.id: node for node in graph.nodes if isinstance(node, MaterialNode)
    }
    operations = {
        node.id: node for node in graph.nodes if isinstance(node, OperationNode)
    }
    consumes_lists: dict[str, list[str]] = defaultdict(list)
    produces_lists: dict[str, list[str]] = defaultdict(list)
    requires_lists: dict[str, list[str]] = defaultdict(list)
    producer: dict[str, str] = {}
    consumers_lists: dict[str, list[str]] = defaultdict(list)
    input_quantities_lists: dict[str, list[tuple[str, str]]] = defaultdict(list)
    precedes_lists: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        if edge.kind == "consumes":
            consumes_lists[edge.target].append(edge.source)
            consumers_lists[edge.source].append(edge.target)
            if edge.quantity:
                input_quantities_lists[edge.target].append(
                    (edge.source, edge.quantity)
                )
        elif edge.kind == "produces":
            produces_lists[edge.source].append(edge.target)
            producer[edge.target] = edge.source
        elif (
            edge.kind in {"reserves", "discards"}
            and edge.source in operations
            and edge.target in materials
        ):
            produces_lists[edge.source].append(edge.target)
            producer[edge.target] = edge.source
        elif (
            edge.kind in {"reserves", "optionally-applies"}
            and edge.source in materials
            and edge.target in operations
        ):
            consumes_lists[edge.target].append(edge.source)
            consumers_lists[edge.source].append(edge.target)
            if edge.quantity:
                input_quantities_lists[edge.target].append(
                    (edge.source, edge.quantity)
                )
        elif edge.kind == "requires":
            requires_lists[edge.target].append(edge.source)
        elif edge.kind == "precedes":
            precedes_lists[edge.source].append(edge.target)

    transform_ids = tuple(
        node.id
        for node in graph.nodes
        if isinstance(node, OperationNode) and node.operation_kind == "transform"
    )
    order_index = {identifier: index for index, identifier in enumerate(transform_ids)}
    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = {identifier: 0 for identifier in transform_ids}
    for operation_id in transform_ids:
        for material_id in consumes_lists.get(operation_id, []):
            source = producer.get(material_id)
            if (
                source in indegree
                and source is not None
                and operation_id not in adjacency[source]
            ):
                adjacency[source].add(operation_id)
                indegree[operation_id] += 1
    for source, targets in precedes_lists.items():
        if source not in indegree:
            continue
        for target in targets:
            if target in indegree and target not in adjacency[source]:
                adjacency[source].add(target)
                indegree[target] += 1

    queue: list[tuple[int, str]] = []
    for identifier, degree in indegree.items():
        if degree == 0:
            heappush(queue, (order_index[identifier], identifier))
    ordered: list[str] = []
    while queue:
        _, identifier = heappop(queue)
        ordered.append(identifier)
        for target in sorted(adjacency[identifier], key=order_index.__getitem__):
            indegree[target] -= 1
            if indegree[target] == 0:
                heappush(queue, (order_index[target], target))
    if len(ordered) != len(transform_ids):
        ordered = list(transform_ids)

    setup_order = tuple(
        node.id
        for node in graph.nodes
        if isinstance(node, OperationNode) and node.operation_kind == "setup"
    )
    return _GraphView(
        materials=materials,
        operations=operations,
        transform_order=tuple(ordered),
        setup_order=setup_order,
        consumes={key: tuple(value) for key, value in consumes_lists.items()},
        produces={key: tuple(value) for key, value in produces_lists.items()},
        requires={key: tuple(value) for key, value in requires_lists.items()},
        producer=producer,
        consumers={key: tuple(value) for key, value in consumers_lists.items()},
        input_quantities={
            key: tuple(value) for key, value in input_quantities_lists.items()
        },
    )


def _allocate_lanes(
    view: _GraphView,
) -> tuple[dict[str, int], int, tuple[str, ...]]:
    operation_rank = {
        identifier: index
        for index, identifier in enumerate(view.transform_order)
    }

    def ingredient_order(identifier: str) -> tuple[int, str]:
        consumer_ranks = (
            operation_rank[consumer]
            for consumer in view.consumers.get(identifier, ())
            if consumer in operation_rank
        )
        return (min(consumer_ranks, default=len(operation_rank)), identifier)

    ingredient_ids = tuple(
        sorted(
            (
                identifier
                for identifier, material in view.materials.items()
                if material.role == "ingredient"
            ),
            key=ingredient_order,
        )
    )
    lane_of = {identifier: index for index, identifier in enumerate(ingredient_ids)}
    next_lane = len(ingredient_ids)
    for operation_id in view.transform_order:
        input_lanes = [
            lane_of[identifier]
            for identifier in view.consumes.get(operation_id, ())
            if identifier in lane_of
        ]
        primary = min(input_lanes) if input_lanes else next_lane
        if not input_lanes:
            next_lane += 1
        for index, material_id in enumerate(view.produces.get(operation_id, ())):
            if material_id.startswith("req:"):
                continue
            lane_of[material_id] = primary if index == 0 else next_lane
            if index > 0:
                next_lane += 1
    return lane_of, max(1, next_lane), ingredient_ids


def _ingredient_column_width(
    ingredient_ids: tuple[str, ...],
    view: _GraphView,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> float:
    if options.ingredient_label_width is not None:
        return options.ingredient_label_width
    maximum = options.max_ingredient_width
    if options.preferred_width is not None:
        maximum = min(maximum, max(150, options.preferred_width * 0.32))
    natural = 150.0
    for identifier in ingredient_ids:
        material = view.materials[identifier]
        for spec in _ingredient_text_specs(material, options, theme):
            natural = max(natural, measurer.measure(spec.text, spec.style).width + 20)
    return min(maximum, natural)


def _measure_material_labels(
    view: _GraphView,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> dict[str, _LabelSize]:
    sizes: dict[str, _LabelSize] = {}
    padding = Insets(top=7, right=9, bottom=7, left=9)
    for identifier, material in view.materials.items():
        if (
            material.role == "ingredient"
            or identifier.startswith("req:")
            or (
                material.role != "final"
                and not options.show_intermediate_labels
            )
        ):
            continue
        style = theme.label_style if material.role == "final" else theme.detail_style
        label_text = _material_label_text(material)
        measured, width, height = measure_text_block(
            label_text,
            options.max_material_label_width,
            style,
            measurer,
            padding=padding,
            wrap_mode=options.wrap_mode,
        )
        final_width = max(64, min(options.max_material_label_width, width))
        _, _, final_height = measure_text_block(
            label_text,
            final_width,
            style,
            measurer,
            padding=padding,
            wrap_mode=options.wrap_mode,
        )
        sizes[identifier] = _LabelSize(
            width=final_width,
            height=max(30, final_height if not measured.overflow else height),
        )
    return sizes


def _measure_operations(
    view: _GraphView,
    lane_of: dict[str, int],
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> dict[str, _OperationSize]:
    sizes: dict[str, _OperationSize] = {}
    many_operations = len(view.transform_order) >= 7
    for operation_id in view.transform_order:
        node = view.operations[operation_id]
        detail = _operation_detail(node)
        input_quantities = _operation_input_quantity_text(view, operation_id)
        until = f"Until {node.until}" if node.until else ""
        action_width = measurer.measure(node.action, theme.operation_style).width
        input_lanes = [
            lane_of[identifier]
            for identifier in (
                *view.consumes.get(operation_id, ()),
                *view.produces.get(operation_id, ()),
            )
            if identifier in lane_of
        ]
        lane_span = max(input_lanes) - min(input_lanes) + 1 if input_lanes else 1
        requested = options.operation_label_orientation
        if requested == "auto":
            orientation = (
                "vertical"
                if many_operations and lane_span >= 2 and action_width <= 120
                else "horizontal"
            )
        else:
            orientation = requested

        natural_detail = (
            measurer.measure(detail, theme.quantity_style).width if detail else 0
        )
        natural_input_quantities = (
            measurer.measure(input_quantities, theme.quantity_style).width
            if input_quantities
            else 0
        )
        natural_until = (
            measurer.measure(until, theme.detail_style).width if until else 0
        )
        if orientation == "vertical":
            width = min(
                options.max_operation_width,
                max(
                    options.min_operation_width,
                    min(
                        max(
                            natural_input_quantities,
                            natural_detail,
                            natural_until,
                        )
                        + 16,
                        132,
                    ),
                ),
            )
            action_height = action_width + 12
        else:
            width = min(
                options.max_operation_width,
                max(
                    options.min_operation_width,
                    min(
                        max(
                            action_width,
                            natural_input_quantities,
                            natural_detail,
                            natural_until,
                        )
                        + 16,
                        options.max_operation_width,
                    ),
                ),
            )
            action_height = wrap_text_height(
                node.action,
                width - 16,
                theme.operation_style,
                measurer,
                options.wrap_mode,
            )
        detail_height = (
            wrap_text_height(
                detail,
                width - 16,
                theme.quantity_style,
                measurer,
                options.wrap_mode,
            )
            if detail
            else 0
        )
        input_quantity_height = (
            wrap_text_height(
                input_quantities,
                width - 16,
                theme.quantity_style,
                measurer,
                options.wrap_mode,
            )
            if input_quantities
            else 0
        )
        until_height = (
            wrap_text_height(
                until,
                width - 16,
                theme.detail_style,
                measurer,
                options.wrap_mode,
            )
            if until
            else 0
        )
        gaps = 4 * sum(
            value > 0
            for value in (
                input_quantity_height,
                detail_height,
                until_height,
            )
        )
        height = max(
            42,
            16
            + action_height
            + input_quantity_height
            + detail_height
            + until_height
            + gaps,
        )
        sizes[operation_id] = _OperationSize(
            width=width,
            height=height,
            orientation=orientation,
            action_height=action_height,
            input_quantity_height=input_quantity_height,
            detail_height=detail_height,
            until_height=until_height,
        )
    return sizes


def wrap_text_height(
    text: str,
    width: float,
    style: TextStyle,
    measurer: TextMeasurer,
    wrap_mode: Literal["word", "grapheme"] = "word",
) -> float:
    return wrap_text(text, max(1, width), style, measurer, wrap_mode).height


def _allocate_columns(
    view: _GraphView,
    operation_sizes: dict[str, _OperationSize],
    material_sizes: dict[str, _LabelSize],
    label_width: float,
    options: LayoutOptions,
) -> tuple[dict[str, float], float]:
    cursor = options.safe_margin + label_width + 34
    positions: dict[str, float] = {}
    for operation_id in view.transform_order:
        positions[operation_id] = cursor
        size = operation_sizes[operation_id]
        output_width = max(
            (
                material_sizes[identifier].width
                for identifier in view.produces.get(operation_id, ())
                if identifier in material_sizes
            ),
            default=0,
        )
        cursor += size.width + options.horizontal_gap
        if output_width:
            cursor += output_width + options.horizontal_gap
    return positions, cursor + options.safe_margin


def _place_header(
    title: str,
    yield_text: str | None,
    canvas_width: float,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> tuple[tuple[TextBlock, ...], float]:
    padding = Insets(top=0, right=0, bottom=0, left=0)
    measured, _, _ = measure_text_block(
        title,
        canvas_width - options.safe_margin * 2,
        theme.title_style,
        measurer,
        padding=padding,
        wrap_mode=options.wrap_mode,
    )
    rect = Rect(
        x=options.safe_margin,
        y=options.safe_margin,
        width=canvas_width - options.safe_margin * 2,
        height=measured.height,
    )
    title_block = place_text_block(
        identifier="text:title",
        role="title",
        text=title,
        rect=rect,
        style=theme.title_style,
        measurer=measurer,
        padding=padding,
        wrap_mode=options.wrap_mode,
    )
    blocks = [title_block]
    cursor = rect.bottom
    if yield_text:
        yield_source = f"Yield: {yield_text}"
        yield_height = wrap_text_height(
            yield_source,
            rect.width,
            theme.quantity_style,
            measurer,
            options.wrap_mode,
        )
        yield_rect = Rect(
            x=options.safe_margin,
            y=cursor + 4,
            width=rect.width,
            height=yield_height,
        )
        blocks.append(
            place_text_block(
                identifier="text:yield",
                role="recipe-yield",
                text=yield_source,
                rect=yield_rect,
                style=theme.quantity_style,
                measurer=measurer,
                wrap_mode=options.wrap_mode,
            )
        )
        cursor = yield_rect.bottom
    return tuple(blocks), cursor + 18


def _containing_rect(blocks: tuple[TextBlock, ...]) -> Rect:
    left = min(block.rect.x for block in blocks)
    top = min(block.rect.y for block in blocks)
    right = max(block.rect.right for block in blocks)
    bottom = max(block.rect.bottom for block in blocks)
    return Rect(x=left, y=top, width=right - left, height=bottom - top)


def _place_setup_cards(
    view: _GraphView,
    graph: RecipeGraph,
    canvas_width: float,
    header_height: float,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> tuple[
    list[SetupCard],
    list[LayoutBox],
    list[TextBlock],
    float,
]:
    del graph
    cards: list[SetupCard] = []
    boxes: list[LayoutBox] = []
    blocks: list[TextBlock] = []
    if not view.setup_order:
        return cards, boxes, blocks, 18

    available = canvas_width - options.safe_margin * 2
    cursor_x = options.safe_margin
    cursor_y = header_height + 8
    row_height = 0.0
    for operation_id in view.setup_order:
        node = view.operations[operation_id]
        detail = _operation_detail(node)
        produced_requirements = set(view.produces.get(operation_id, ()))
        required_by = tuple(
            target
            for target in view.transform_order
            if operation_id in view.requires.get(target, ())
            or produced_requirements.intersection(view.requires.get(target, ()))
        )
        required_by_labels = tuple(
            view.operations[target].label for target in required_by
        )
        specs = _setup_text_specs(
            node,
            options,
            theme,
            required_by_labels=required_by_labels,
        )
        maximum_inner_width = max(1, options.max_setup_card_width - 22)
        natural_width = max(
            (
                measurer.measure(spec.text, spec.style).width
                for spec in specs
            ),
            default=0,
        )
        width = min(
            options.max_setup_card_width,
            max(options.min_setup_card_width, natural_width + 22),
            available,
        )
        inner_width = min(maximum_inner_width, max(1, width - 22))
        measured_heights = [
            wrap_text_height(
                spec.text,
                inner_width,
                spec.style,
                measurer,
                options.wrap_mode,
            )
            for spec in specs
        ]
        height = sum(measured_heights) + 4 * max(0, len(specs) - 1) + 18
        if cursor_x > options.safe_margin and cursor_x + width > options.safe_margin + available:
            cursor_x = options.safe_margin
            cursor_y += row_height + 10
            row_height = 0
        rect = Rect(x=cursor_x, y=cursor_y, width=width, height=height)
        box_id = f"box:setup:{operation_id}"
        text_ids: list[str] = []
        text_cursor = rect.y + 9
        for spec, text_height in zip(specs, measured_heights, strict=True):
            text_rect = Rect(
                x=rect.x + 11,
                y=text_cursor,
                width=inner_width,
                height=text_height,
            )
            block = place_text_block(
                identifier=f"text:setup:{operation_id}:{spec.suffix}",
                role=spec.role,
                text=spec.text,
                rect=text_rect,
                style=spec.style,
                measurer=measurer,
                wrap_mode=options.wrap_mode,
                parent_id=box_id,
            )
            blocks.append(block)
            text_ids.append(block.id)
            text_cursor += text_height + 4

        cards.append(
            SetupCard(
                operation_id=operation_id,
                label=node.label,
                detail=detail or None,
                x=rect.x,
                width=rect.width,
                y=rect.y,
                height=rect.height,
                rect=rect,
                text_block_ids=tuple(text_ids),
                required_by_operation_ids=required_by,
            )
        )
        boxes.append(
            LayoutBox(
                id=box_id,
                kind="setup",
                rect=rect,
                text_block_ids=tuple(text_ids),
                style_class="setup",
                collision_group="setup",
            )
        )
        cursor_x += width + 10
        row_height = max(row_height, height)
    dependency_count = sum(len(card.required_by_operation_ids) for card in cards)
    setup_bottom = cursor_y + row_height + 18 + dependency_count * 7
    return cards, boxes, blocks, setup_bottom - header_height


def _setup_text_specs(
    node: OperationNode,
    options: LayoutOptions,
    theme: LayoutTheme,
    *,
    required_by_labels: tuple[str, ...],
) -> tuple[_TextSpec, ...]:
    specs = [
        _TextSpec(
            suffix="label",
            role="setup-label",
            text=node.label,
            style=theme.label_style,
            alignment="start",
        )
    ]
    if node.target:
        specs.append(
            _TextSpec(
                suffix="target",
                role="setup-target",
                text=f"Target: {node.target}",
                style=theme.quantity_style,
                alignment="start",
            )
        )
    if required_by_labels:
        specs.append(
            _TextSpec(
                suffix="required-by",
                role="setup-required-by",
                text=f"Required by: {'; '.join(required_by_labels)}",
                style=theme.quantity_style,
                alignment="start",
            )
        )
    detail = _operation_detail(node)
    if detail:
        specs.append(
            _TextSpec(
                suffix="detail",
                role="setup-detail",
                text=detail,
                style=theme.quantity_style,
                alignment="start",
            )
        )
    specs.extend(
        _TextSpec(
            suffix=f"note:{index}",
            role="setup-note",
            text=note,
            style=theme.detail_style,
            alignment="start",
        )
        for index, note in enumerate(node.notes)
    )
    if options.show_provenance:
        specs.extend(
            _TextSpec(
                suffix=f"provenance:{index}",
                role="setup-provenance",
                text=text,
                style=theme.detail_style,
                alignment="start",
            )
            for index, text in enumerate(_provenance_texts(node.provenance))
        )
    return tuple(specs)


def _measure_rows(
    view: _GraphView,
    lane_of: dict[str, int],
    lane_count: int,
    ingredient_ids: tuple[str, ...],
    label_width: float,
    material_sizes: dict[str, _LabelSize],
    operation_sizes: dict[str, _OperationSize],
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> list[float]:
    rows = [options.minimum_row_height for _ in range(lane_count)]
    for identifier in ingredient_ids:
        lane = lane_of[identifier]
        material = view.materials[identifier]
        specs = _ingredient_text_specs(material, options, theme)
        content_height = _text_stack_height(
            specs,
            label_width - 16,
            measurer,
            options.wrap_mode,
        )
        rows[lane] = max(rows[lane], content_height + 18)
    for identifier, material_size in material_sizes.items():
        if identifier in lane_of:
            rows[lane_of[identifier]] = max(
                rows[lane_of[identifier]],
                material_size.height + 18,
            )

    for operation_id, operation_size in operation_sizes.items():
        lanes = [
            lane_of[identifier]
            for identifier in (
                *view.consumes.get(operation_id, ()),
                *view.produces.get(operation_id, ()),
            )
            if identifier in lane_of
        ]
        if not lanes:
            continue
        low, high = min(lanes), max(lanes)
        needed = operation_size.height + 16
        current = sum(rows[low : high + 1])
        if current < needed:
            increment = (needed - current) / (high - low + 1)
            for lane in range(low, high + 1):
                rows[lane] += increment
    return rows


def _lane_centers(rows: list[float], top: float) -> list[float]:
    centers: list[float] = []
    cursor = top
    for height in rows:
        centers.append(cursor + height / 2)
        cursor += height
    return centers


def _place_operations(
    view: _GraphView,
    lane_of: dict[str, int],
    lane_y: list[float],
    row_heights: list[float],
    operation_x: dict[str, float],
    operation_sizes: dict[str, _OperationSize],
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> tuple[list[OperationCell], list[LayoutBox], list[TextBlock]]:
    cells: list[OperationCell] = []
    boxes: list[LayoutBox] = []
    blocks: list[TextBlock] = []
    for operation_id in view.transform_order:
        node = view.operations[operation_id]
        size = operation_sizes[operation_id]
        lanes = [
            lane_of[identifier]
            for identifier in (
                *view.consumes.get(operation_id, ()),
                *view.produces.get(operation_id, ()),
            )
            if identifier in lane_of
        ]
        low = min(lanes) if lanes else 0
        high = max(lanes) if lanes else low
        top = lane_y[low] - row_heights[low] / 2 + 8
        bottom = lane_y[high] + row_heights[high] / 2 - 8
        rect = Rect(
            x=operation_x[operation_id],
            y=top,
            width=size.width,
            height=max(size.height, bottom - top),
        )
        box_id = f"box:operation:{operation_id}"
        operation_blocks = _operation_text_blocks(
            node,
            _operation_input_quantity_text(view, operation_id),
            size,
            rect,
            box_id,
            options,
            theme,
            measurer,
        )
        blocks.extend(operation_blocks)
        boxes.append(
            LayoutBox(
                id=box_id,
                kind="operation",
                rect=rect,
                text_block_ids=tuple(block.id for block in operation_blocks),
                style_class="operation",
                collision_group="graph",
            )
        )
        cells.append(
            OperationCell(
                operation_id=operation_id,
                label=node.label,
                action=node.action,
                x=rect.x + rect.width / 2,
                y1=rect.y,
                y2=rect.bottom,
                input_material_ids=view.consumes.get(operation_id, ()),
                output_material_ids=view.produces.get(operation_id, ()),
                duration=node.duration,
                temperature=node.temperature,
                until=node.until,
                rect=rect,
                text_block_ids=tuple(block.id for block in operation_blocks),
                orientation=size.orientation,  # type: ignore[arg-type]
            )
        )
    return cells, boxes, blocks


def _operation_text_blocks(
    node: OperationNode,
    input_quantities: str,
    size: _OperationSize,
    rect: Rect,
    parent_id: str,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> list[TextBlock]:
    detail = _operation_detail(node)
    until = f"Until {node.until}" if node.until else ""
    total = (
        size.action_height
        + size.input_quantity_height
        + size.detail_height
        + size.until_height
    )
    total += 4 * sum(
        value > 0
        for value in (
            size.input_quantity_height,
            size.detail_height,
            size.until_height,
        )
    )
    cursor = rect.y + max(8, (rect.height - total) / 2)
    blocks: list[TextBlock] = []
    if size.orientation == "vertical":
        action_metrics = measurer.measure(node.action, theme.operation_style)
        action_cross_axis = max(
            theme.operation_style.line_height,
            action_metrics.height,
        ) + 2
        action_rect = Rect(
            x=rect.x + (rect.width - action_cross_axis) / 2,
            y=cursor,
            width=action_cross_axis,
            height=size.action_height,
        )
        action = place_vertical_text_block(
            identifier=f"text:operation:{node.id}:action",
            role="operation-action",
            text=node.action,
            rect=action_rect,
            style=theme.operation_style,
            measurer=measurer,
            parent_id=parent_id,
        )
    else:
        action_rect = Rect(
            x=rect.x + 8,
            y=cursor,
            width=rect.width - 16,
            height=size.action_height,
        )
        action = place_text_block(
            identifier=f"text:operation:{node.id}:action",
            role="operation-action",
            text=node.action,
            rect=action_rect,
            style=theme.operation_style,
            measurer=measurer,
            horizontal_alignment="center",
            vertical_alignment="middle",
            parent_id=parent_id,
            wrap_mode=options.wrap_mode,
        )
    blocks.append(action)
    cursor += size.action_height
    if input_quantities:
        cursor += 4
        input_quantity_rect = Rect(
            x=rect.x + 8,
            y=cursor,
            width=rect.width - 16,
            height=size.input_quantity_height,
        )
        blocks.append(
            place_text_block(
                identifier=f"text:operation:{node.id}:input-quantities",
                role="operation-input-quantity",
                text=input_quantities,
                rect=input_quantity_rect,
                style=theme.quantity_style,
                measurer=measurer,
                horizontal_alignment="center",
                parent_id=parent_id,
                wrap_mode=options.wrap_mode,
            )
        )
        cursor += size.input_quantity_height
    if detail:
        cursor += 4
        detail_rect = Rect(
            x=rect.x + 8,
            y=cursor,
            width=rect.width - 16,
            height=size.detail_height,
        )
        blocks.append(
            place_text_block(
                identifier=f"text:operation:{node.id}:detail",
                role="operation-detail",
                text=detail,
                rect=detail_rect,
                style=theme.quantity_style,
                measurer=measurer,
                horizontal_alignment="center",
                parent_id=parent_id,
                wrap_mode=options.wrap_mode,
            )
        )
        cursor += size.detail_height
    if until:
        cursor += 4
        until_rect = Rect(
            x=rect.x + 8,
            y=cursor,
            width=rect.width - 16,
            height=size.until_height,
        )
        blocks.append(
            place_text_block(
                identifier=f"text:operation:{node.id}:until",
                role="operation-until",
                text=until,
                rect=until_rect,
                style=theme.detail_style,
                measurer=measurer,
                horizontal_alignment="center",
                parent_id=parent_id,
                wrap_mode=options.wrap_mode,
            )
        )
    return blocks


def _place_materials(
    view: _GraphView,
    lane_of: dict[str, int],
    lane_y: list[float],
    ingredient_ids: tuple[str, ...],
    label_width: float,
    material_sizes: dict[str, _LabelSize],
    operation_rects: dict[str, Rect],
    canvas_width: float,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> tuple[
    list[MaterialSegment],
    list[LayoutBox],
    list[TextBlock],
    list[RoutedPath],
]:
    del ingredient_ids
    segments: list[MaterialSegment] = []
    boxes: list[LayoutBox] = []
    blocks: list[TextBlock] = []
    paths: list[RoutedPath] = []
    graph_start = options.safe_margin + label_width + 10
    for identifier, material in view.materials.items():
        if identifier.startswith("req:") or identifier not in lane_of:
            continue
        lane = lane_of[identifier]
        y = lane_y[lane]
        label_box_id: str | None = None
        if material.role == "ingredient":
            ingredient_box, ingredient_blocks = _ingredient_box(
                material,
                y,
                label_width,
                options,
                theme,
                measurer,
            )
            boxes.append(ingredient_box)
            blocks.extend(ingredient_blocks)
            source_x = graph_start
        else:
            producer_id = view.producer.get(identifier)
            producer_rect = operation_rects.get(producer_id or "")
            source_x = producer_rect.right if producer_rect else graph_start
            size = material_sizes.get(identifier)
            if size is not None:
                label_rect = Rect(
                    x=source_x + options.horizontal_gap,
                    y=y - size.height / 2,
                    width=size.width,
                    height=size.height,
                )
                label_box_id = f"box:material:{identifier}"
                role: TextRole = (
                    "final-label" if material.role == "final" else "material-label"
                )
                style = (
                    theme.label_style
                    if material.role == "final"
                    else theme.detail_style
                )
                label_text = _material_label_text(material)
                block = place_text_block(
                    identifier=f"text:material:{identifier}",
                    role=role,
                    text=label_text,
                    rect=label_rect,
                    style=style,
                    measurer=measurer,
                    padding=Insets(top=7, right=9, bottom=7, left=9),
                    vertical_alignment="middle",
                    parent_id=label_box_id,
                    wrap_mode=options.wrap_mode,
                )
                block_kind: LayoutBoxKind = (
                    "final-output"
                    if material.role == "final"
                    else "material-label"
                )
                boxes.append(
                    LayoutBox(
                        id=label_box_id,
                        kind=block_kind,
                        rect=label_rect,
                        text_block_ids=(block.id,),
                        style_class=(
                            "final-output"
                            if material.role == "final"
                            else "material-label"
                        ),
                        collision_group="graph",
                    )
                )
                blocks.append(block)

        consumer_rects = [
            operation_rects[operation_id]
            for operation_id in view.consumers.get(identifier, ())
            if operation_id in operation_rects
        ]
        target_x = (
            max(rect.x for rect in consumer_rects)
            if consumer_rects
            else min(canvas_width - options.safe_margin, source_x + 220)
        )
        target_x = max(source_x, target_x)
        path_id = f"path:material:{identifier}"
        paths.append(
            RoutedPath(
                id=path_id,
                kind="material",
                points=(
                    Point(x=round(source_x, 3), y=round(y, 3)),
                    Point(x=round(target_x, 3), y=round(y, 3)),
                ),
                style_class="flow",
                source_id=identifier,
                target_ids=tuple(view.consumers.get(identifier, ())),
                stroke_width=3,
            )
        )
        segments.append(
            MaterialSegment(
                material_id=identifier,
                label=material.label,
                quantity=material.quantity,
                role=material.role.value,
                lane=lane,
                x1=source_x,
                x2=target_x,
                y=y,
                show_left_label=material.role == "ingredient",
                show_inline_label=(
                    material.role != "ingredient"
                    and (
                        material.role == "final"
                        or options.show_intermediate_labels
                    )
                ),
                path_id=path_id,
                label_box_id=label_box_id,
            )
        )
    return segments, boxes, blocks, paths


def _ingredient_box(
    material: MaterialNode,
    lane_y: float,
    label_width: float,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> tuple[LayoutBox, list[TextBlock]]:
    inner_width = label_width - 16
    specs = _ingredient_text_specs(material, options, theme)
    measured_heights = [
        wrap_text_height(
            spec.text,
            inner_width,
            spec.style,
            measurer,
            options.wrap_mode,
        )
        for spec in specs
    ]
    gap = 3
    height = sum(measured_heights) + gap * max(0, len(specs) - 1) + 12
    rect = Rect(
        x=options.safe_margin,
        y=lane_y - height / 2,
        width=label_width,
        height=height,
    )
    box_id = f"box:ingredient:{material.id}"
    blocks: list[TextBlock] = []
    cursor = rect.y + 6
    for spec, text_height in zip(specs, measured_heights, strict=True):
        text_rect = Rect(
            x=rect.x + 8,
            y=cursor,
            width=inner_width,
            height=text_height,
        )
        blocks.append(
            place_text_block(
                identifier=f"text:ingredient:{material.id}:{spec.suffix}",
                role=spec.role,
                text=spec.text,
                rect=text_rect,
                style=spec.style,
                measurer=measurer,
                horizontal_alignment=spec.alignment,
                parent_id=box_id,
                wrap_mode=options.wrap_mode,
            )
        )
        cursor += text_height + gap
    return (
        LayoutBox(
            id=box_id,
            kind="ingredient",
            rect=rect,
            text_block_ids=tuple(block.id for block in blocks),
            style_class="ingredient",
            opaque=False,
            collision_group="labels",
        ),
        blocks,
    )


def _ingredient_text_specs(
    material: MaterialNode,
    options: LayoutOptions,
    theme: LayoutTheme,
) -> tuple[_TextSpec, ...]:
    specs: list[_TextSpec] = []
    if options.show_source_quantities and material.quantity:
        specs.append(
            _TextSpec(
                suffix="quantity",
                role="ingredient-quantity",
                text=material.quantity,
                style=theme.quantity_style,
            )
        )
    if options.show_normalized_quantities:
        normalized = _normalized_quantity_text(material)
        if normalized and normalized != material.quantity:
            specs.append(
                _TextSpec(
                    suffix="normalized-quantity",
                    role="ingredient-quantity",
                    text=normalized,
                    style=theme.quantity_style,
                )
            )
    specs.append(
        _TextSpec(
            suffix="label",
            role="ingredient-label",
            text=material.label,
            style=theme.label_style,
        )
    )
    if options.show_source_quantities and material.source_text:
        specs.append(
            _TextSpec(
                suffix="source",
                role="ingredient-source",
                text=material.source_text,
                style=theme.detail_style,
            )
        )
    for suffix, text in (
        ("preparation", material.preparation_state),
        ("temperature-state", material.temperature_state),
    ):
        if text:
            specs.append(
                _TextSpec(
                    suffix=suffix,
                    role="ingredient-preparation",
                    text=text,
                    style=theme.detail_style,
                )
            )
    specs.extend(
        _TextSpec(
            suffix=f"annotation:{index}",
            role="ingredient-annotation",
            text=annotation,
            style=theme.detail_style,
        )
        for index, annotation in enumerate(material.annotations)
    )
    if options.show_provenance:
        specs.extend(
            _TextSpec(
                suffix=f"provenance:{index}",
                role="ingredient-provenance",
                text=text,
                style=theme.detail_style,
            )
            for index, text in enumerate(_provenance_texts(material.provenance))
        )
    return tuple(specs)


def _normalized_quantity_text(material: MaterialNode) -> str | None:
    quantity = material.normalized_quantity
    if quantity is None or quantity.normalized is None:
        return None
    normalized = quantity.normalized
    if normalized.value is not None:
        number = str(normalized.value)
    elif normalized.minimum is not None or normalized.maximum is not None:
        minimum = "" if normalized.minimum is None else str(normalized.minimum)
        maximum = "" if normalized.maximum is None else str(normalized.maximum)
        number = f"{minimum}..{maximum}"
    else:
        return None
    return f"{number} {normalized.unit}".strip() if normalized.unit else number


def _provenance_texts(provenance: tuple[Provenance, ...]) -> tuple[str, ...]:
    output: list[str] = []
    for item in provenance:
        if item.source_text:
            output.append(item.source_text)
        elif item.note:
            output.append(item.note)
        else:
            reference = " · ".join(
                value for value in (item.source_id, item.path) if value
            )
            if reference:
                output.append(reference)
    return tuple(output)


def _text_stack_height(
    specs: tuple[_TextSpec, ...],
    width: float,
    measurer: TextMeasurer,
    wrap_mode: Literal["word", "grapheme"],
) -> float:
    heights = [
        wrap_text_height(spec.text, width, spec.style, measurer, wrap_mode)
        for spec in specs
    ]
    return sum(heights) + 3 * max(0, len(heights) - 1)


def _setup_dependency_paths(
    cards: list[SetupCard],
    view: _GraphView,
    operation_rects: dict[str, Rect],
    lane_top: float,
) -> list[RoutedPath]:
    paths: list[RoutedPath] = []
    dependencies = [
        (card, operation_id)
        for card in cards
        if card.rect is not None
        for operation_id in card.required_by_operation_ids
        if operation_id in operation_rects
    ]
    target_counts: dict[str, int] = defaultdict(int)
    for _, operation_id in dependencies:
        target_counts[operation_id] += 1
    target_indexes: dict[str, int] = defaultdict(int)
    for route_index, (card, operation_id) in enumerate(dependencies):
        if card.rect is None:
            continue
        target = operation_rects.get(operation_id)
        if target is None:
            continue
        target_index = target_indexes[operation_id]
        target_indexes[operation_id] += 1
        target_x = target.x + target.width * (target_index + 1) / (
            target_counts[operation_id] + 1
        )
        corridor_y = lane_top - 8 - route_index * 7
        paths.append(
            RoutedPath(
                id=f"path:setup:{card.operation_id}:{operation_id}",
                kind="setup-dependency",
                points=(
                    Point(x=card.rect.x + card.rect.width / 2, y=card.rect.bottom),
                    Point(
                        x=card.rect.x + card.rect.width / 2,
                        y=corridor_y,
                    ),
                    Point(x=target_x, y=corridor_y),
                    Point(x=target_x, y=target.y),
                ),
                style_class="setup-dependency",
                source_id=card.operation_id,
                target_ids=(operation_id,),
                stroke_width=1.5,
            )
        )
    return paths


def _guide_paths(
    lane_y: list[float],
    canvas_width: float,
    options: LayoutOptions,
) -> list[RoutedPath]:
    return [
        RoutedPath(
            id=f"path:guide:{index}",
            kind="guide",
            points=(
                Point(x=options.safe_margin, y=y),
                Point(x=canvas_width - options.safe_margin, y=y),
            ),
            style_class="guide",
            stroke_width=1,
        )
        for index, y in enumerate(lane_y)
    ]


def _operation_detail(node: OperationNode) -> str:
    parts: list[str] = []
    if node.temperature:
        parts.append(f"Temperature: {node.temperature}")
    if node.duration:
        parts.append(f"Time: {node.duration.replace('..', ' to ')}")
    return " · ".join(parts)


def _operation_input_quantity_text(
    view: _GraphView,
    operation_id: str,
) -> str:
    quantity_by_material = dict(view.input_quantities.get(operation_id, ()))
    portions: list[str] = []
    for material_id in view.consumes.get(operation_id, ()):
        material = view.materials.get(material_id)
        if material is None:
            continue
        quantity = quantity_by_material.get(material_id)
        if quantity is None and view.producer.get(material_id):
            continue
        quantity = quantity or material.quantity
        portions.append(
            f"{quantity} {material.label}" if quantity else material.label
        )
    return f"Uses: {' · '.join(portions)}" if portions else ""


def _material_label_text(material: MaterialNode) -> str:
    return (
        f"{material.quantity} · {material.label}"
        if material.quantity
        else material.label
    )
