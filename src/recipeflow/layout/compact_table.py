from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from recipeflow.layout.engine import (
    _GraphView,
    _index_graph,
    _material_label_text,
    _normalized_quantity_text,
    _operation_detail,
    _operation_input_quantity_text,
    _provenance_texts,
    _scaled_theme,
)
from recipeflow.layout.options import LayoutOptions
from recipeflow.layout.text import place_text_block
from recipeflow.layout.themes import LayoutTheme, get_theme
from recipeflow.layout.validation import validate_tabular_layout
from recipeflow.models.graph import MaterialNode, OperationNode, RecipeGraph
from recipeflow.models.layout import (
    Insets,
    Lane,
    LayoutBox,
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
class _Piece:
    suffix: str
    role: TextRole
    text: str
    style: TextStyle
    align: str = "start"


@dataclass(frozen=True)
class _Column:
    operation_ids: tuple[str, ...]
    width: float


class CompactTableLayoutStrategy:
    """Original-inspired ingredient grid with nested operation spans."""

    def create_layout(
        self,
        graph: RecipeGraph,
        options: LayoutOptions,
        *,
        text_measurer: TextMeasurer | None = None,
    ) -> TabularLayout:
        measurer = text_measurer or default_text_measurer()
        theme = _scaled_theme(get_theme(options.theme), options)
        view = _index_graph(graph)
        source_ids = _source_material_ids(graph, view)
        if not source_ids:
            source_ids = ("__empty__",)

        ancestry = _material_ancestry(view, source_ids)
        rows_by_operation = {
            operation_id: _operation_rows(
                view,
                operation_id,
                source_ids,
                ancestry,
            )
            for operation_id in view.transform_order
        }
        columns = _pack_columns(view, rows_by_operation, options)
        final_ids = tuple(
            identifier
            for identifier in graph.final_material_ids
            if identifier in view.materials
        )

        label_width = _label_width(
            source_ids,
            view,
            options,
            theme,
            measurer,
        )
        final_widths = tuple(
            _final_width(view.materials[identifier], options)
            for identifier in final_ids
        )
        table_width = label_width + sum(column.width for column in columns) + sum(
            final_widths
        )
        canvas_width = max(
            table_width + options.safe_margin * 2,
            options.preferred_width or 0,
        )
        table_x = options.safe_margin

        header_blocks, header_height = _header(
            graph,
            canvas_width,
            options,
            theme,
            measurer,
        )
        setup_cards, setup_boxes, setup_blocks, setup_height = _setup_rows(
            graph,
            view,
            table_x,
            table_width,
            header_height,
            options,
            theme,
            measurer,
        )
        table_top = header_height + setup_height

        row_heights = _initial_row_heights(
            source_ids,
            view,
            label_width,
            options,
            theme,
            measurer,
        )
        operation_pieces = {
            identifier: _operation_pieces(
                view,
                identifier,
                options,
                theme,
            )
            for identifier in view.transform_order
        }
        column_by_operation = {
            operation_id: column
            for column in columns
            for operation_id in column.operation_ids
        }
        for operation_id in view.transform_order:
            runs = _contiguous_runs(rows_by_operation[operation_id])
            primary = _primary_run(runs)
            required = _stack_height(
                operation_pieces[operation_id],
                column_by_operation[operation_id].width - 16,
                measurer,
                options,
            ) + 16
            _ensure_run_height(row_heights, primary, required)

        final_pieces = {
            identifier: _final_pieces(view.materials[identifier], theme)
            for identifier in final_ids
        }
        for identifier, width in zip(final_ids, final_widths, strict=True):
            rows = _rows_for_material(identifier, source_ids, ancestry)
            primary = _primary_run(_contiguous_runs(rows))
            required = _stack_height(
                final_pieces[identifier],
                width - 16,
                measurer,
                options,
            ) + 16
            _ensure_run_height(row_heights, primary, required)

        row_tops = _row_tops(table_top, row_heights)
        lane_y = [
            top + height / 2
            for top, height in zip(row_tops, row_heights, strict=True)
        ]
        table_bottom = table_top + sum(row_heights)

        ingredient_boxes: list[LayoutBox] = []
        ingredient_blocks: list[TextBlock] = []
        materials: list[MaterialSegment] = []
        for row, identifier in enumerate(source_ids):
            rect = Rect(
                x=table_x,
                y=row_tops[row],
                width=label_width,
                height=row_heights[row],
            )
            if identifier == "__empty__":
                pieces: tuple[_Piece, ...] = (
                    _Piece(
                        suffix="label",
                        role="annotation",
                        text="No source material",
                        style=theme.detail_style,
                    ),
                )
                material = None
            else:
                material = view.materials[identifier]
                pieces = _ingredient_pieces(material, options, theme)
            box_id = f"box:table:ingredient:{identifier}"
            row_blocks = _place_stack(
                box_id,
                f"text:table:ingredient:{identifier}",
                rect,
                pieces,
                measurer,
                options,
            )
            ingredient_boxes.append(
                LayoutBox(
                    id=box_id,
                    kind="ingredient",
                    rect=rect,
                    text_block_ids=tuple(block.id for block in row_blocks),
                    style_class="grid-ingredient",
                    collision_group="table",
                    corner_radius=0,
                )
            )
            ingredient_blocks.extend(row_blocks)
            if material is not None:
                materials.append(
                    MaterialSegment(
                        material_id=identifier,
                        label=material.label,
                        quantity=material.quantity,
                        role=material.role.value,
                        lane=row,
                        x1=table_x,
                        x2=table_x + table_width,
                        y=lane_y[row],
                        show_left_label=True,
                    )
                )

        operation_cells: list[OperationCell] = []
        operation_boxes: list[LayoutBox] = []
        operation_blocks: list[TextBlock] = []
        paths: list[RoutedPath] = _grid_paths(
            table_x,
            table_x + table_width,
            table_top,
            table_bottom,
            row_tops,
            row_heights,
        )
        operation_x = table_x + label_width
        for column in columns:
            for operation_id in column.operation_ids:
                runs = _contiguous_runs(rows_by_operation[operation_id])
                primary = _primary_run(runs)
                box_ids: list[str] = []
                text_ids: list[str] = []
                segment_rects: list[Rect] = []
                for segment_index, run in enumerate(runs):
                    rect = _run_rect(run, operation_x, column.width, row_tops, row_heights)
                    segment_rects.append(rect)
                    box_id = f"box:table:operation:{operation_id}:{segment_index}"
                    cell_blocks: tuple[TextBlock, ...] = ()
                    if run == primary:
                        cell_blocks = _place_stack(
                            box_id,
                            f"text:table:operation:{operation_id}",
                            rect,
                            operation_pieces[operation_id],
                            measurer,
                            options,
                            center=True,
                        )
                        operation_blocks.extend(cell_blocks)
                        text_ids.extend(block.id for block in cell_blocks)
                    operation_boxes.append(
                        LayoutBox(
                            id=box_id,
                            kind="operation",
                            rect=rect,
                            text_block_ids=tuple(block.id for block in cell_blocks),
                            style_class="grid-operation",
                            collision_group="table",
                            corner_radius=0,
                        )
                    )
                    box_ids.append(box_id)
                if len(segment_rects) > 1:
                    center_x = operation_x + column.width / 2
                    paths.append(
                        RoutedPath(
                            id=f"path:table:segments:{operation_id}",
                            kind="guide",
                            points=(
                                Point(x=center_x, y=segment_rects[0].bottom),
                                Point(x=center_x, y=segment_rects[-1].y),
                            ),
                            style_class="segment-link",
                            source_id=operation_id,
                            target_ids=(operation_id,),
                            stroke_width=1.5,
                        )
                    )
                bounds = Rect(
                    x=operation_x,
                    y=min(rect.y for rect in segment_rects),
                    width=column.width,
                    height=max(rect.bottom for rect in segment_rects)
                    - min(rect.y for rect in segment_rects),
                )
                node = view.operations[operation_id]
                operation_cells.append(
                    OperationCell(
                        operation_id=operation_id,
                        label=node.label,
                        action=node.action,
                        x=operation_x,
                        y1=bounds.y,
                        y2=bounds.bottom,
                        input_material_ids=view.consumes.get(operation_id, ()),
                        output_material_ids=view.produces.get(operation_id, ()),
                        duration=node.duration,
                        temperature=node.temperature,
                        until=node.until,
                        rect=bounds,
                        text_block_ids=tuple(text_ids),
                        box_ids=tuple(box_ids),
                    )
                )
            operation_x += column.width

        final_boxes: list[LayoutBox] = []
        final_blocks: list[TextBlock] = []
        final_x = operation_x
        for identifier, width in zip(final_ids, final_widths, strict=True):
            rows = _rows_for_material(identifier, source_ids, ancestry)
            runs = _contiguous_runs(rows)
            primary = _primary_run(runs)
            for segment_index, run in enumerate(runs):
                rect = _run_rect(run, final_x, width, row_tops, row_heights)
                box_id = f"box:table:final:{identifier}:{segment_index}"
                output_blocks: tuple[TextBlock, ...] = ()
                if run == primary:
                    output_blocks = _place_stack(
                        box_id,
                        f"text:table:final:{identifier}",
                        rect,
                        final_pieces[identifier],
                        measurer,
                        options,
                        center=True,
                    )
                    final_blocks.extend(output_blocks)
                final_boxes.append(
                    LayoutBox(
                        id=box_id,
                        kind="final-output",
                        rect=rect,
                        text_block_ids=tuple(block.id for block in output_blocks),
                        style_class="grid-final",
                        collision_group="table",
                        corner_radius=0,
                    )
                )
            final_x += width

        all_blocks = (
            *header_blocks,
            *setup_blocks,
            *ingredient_blocks,
            *operation_blocks,
            *final_blocks,
        )
        layout = TabularLayout(
            title=graph.title,
            notation="compact-table",
            width=round(canvas_width, 3),
            height=round(table_bottom + options.safe_margin, 3),
            label_width=round(label_width, 3),
            header_height=round(header_height, 3),
            setup_height=round(setup_height, 3),
            row_height=round(max(row_heights), 3),
            lanes=tuple(
                Lane(
                    index=index,
                    y=round(y, 3),
                    height=round(row_heights[index], 3),
                    initial_material_id=(
                        None if identifier == "__empty__" else identifier
                    ),
                )
                for index, (identifier, y) in enumerate(zip(source_ids, lane_y, strict=True))
            ),
            materials=tuple(materials),
            operations=tuple(operation_cells),
            setup=tuple(setup_cards),
            final_material_ids=final_ids,
            safe_margin=options.safe_margin,
            theme=options.theme,
            text_blocks=all_blocks,
            boxes=(
                LayoutBox(
                    id="box:table:title",
                    kind="title",
                    rect=_blocks_rect(header_blocks),
                    text_block_ids=tuple(block.id for block in header_blocks),
                    style_class="title",
                    opaque=False,
                    collision_group="header",
                    corner_radius=0,
                ),
                *setup_boxes,
                *ingredient_boxes,
                *operation_boxes,
                *final_boxes,
            ),
            paths=tuple(paths),
            reading_order=tuple(block.id for block in all_blocks),
        )
        return layout.model_copy(update={"diagnostics": validate_tabular_layout(layout)})


def _source_material_ids(graph: RecipeGraph, view: _GraphView) -> tuple[str, ...]:
    identifiers = tuple(
        node.id
        for node in graph.nodes
        if isinstance(node, MaterialNode)
        and node.id not in view.producer
        and not node.id.startswith("req:")
        and node.role != "final"
    )
    source_set = set(identifiers)
    ordered: list[str] = []

    def append_sources(material_id: str, active: frozenset[str] = frozenset()) -> None:
        if material_id in source_set:
            if material_id not in ordered:
                ordered.append(material_id)
            return
        if material_id in active:
            return
        producer = view.producer.get(material_id)
        if producer is None:
            return
        for input_id in view.consumes.get(producer, ()):
            append_sources(input_id, active | {material_id})

    # Trace backward from final outputs first. This keeps a complete dependency branch
    # together instead of interleaving an unrelated root operation between a producer
    # and its consumer. Shared sources can still require linked segments.
    for material_id in graph.final_material_ids:
        append_sources(material_id)
    for operation_id in view.transform_order:
        for input_id in view.consumes.get(operation_id, ()):
            append_sources(input_id)
    for identifier in identifiers:
        append_sources(identifier)
    return tuple(ordered)


def _material_ancestry(
    view: _GraphView,
    source_ids: tuple[str, ...],
) -> dict[str, frozenset[str]]:
    sources = set(source_ids)
    cache: dict[str, frozenset[str]] = {}

    def ancestry(material_id: str, active: frozenset[str] = frozenset()) -> frozenset[str]:
        if material_id in cache:
            return cache[material_id]
        if material_id in sources:
            result = frozenset({material_id})
        elif material_id in active:
            result = frozenset()
        else:
            producer = view.producer.get(material_id)
            if producer is None:
                result = frozenset()
            else:
                result = frozenset().union(
                    *(
                        ancestry(input_id, active | {material_id})
                        for input_id in view.consumes.get(producer, ())
                    )
                )
        cache[material_id] = result
        return result

    for identifier in view.materials:
        ancestry(identifier)
    return cache


def _operation_rows(
    view: _GraphView,
    operation_id: str,
    source_ids: tuple[str, ...],
    ancestry: dict[str, frozenset[str]],
) -> tuple[int, ...]:
    source_set = frozenset().union(
        *(
            ancestry.get(identifier, frozenset())
            for identifier in view.consumes.get(operation_id, ())
        )
    )
    rows = tuple(
        index
        for index, identifier in enumerate(source_ids)
        if identifier in source_set
    )
    return rows or (0,)


def _rows_for_material(
    material_id: str,
    source_ids: tuple[str, ...],
    ancestry: dict[str, frozenset[str]],
) -> tuple[int, ...]:
    material_sources = ancestry.get(material_id, frozenset())
    rows = tuple(
        index
        for index, identifier in enumerate(source_ids)
        if identifier in material_sources
    )
    return rows or (0,)


def _operation_levels(view: _GraphView) -> dict[str, int]:
    level: dict[str, int] = {}
    for operation_id in view.transform_order:
        dependencies = {
            view.producer[material_id]
            for material_id in view.consumes.get(operation_id, ())
            if material_id in view.producer
            and view.producer[material_id] in view.transform_order
        }
        level[operation_id] = max((level.get(item, 0) + 1 for item in dependencies), default=0)
    return level


def _pack_columns(
    view: _GraphView,
    rows_by_operation: dict[str, tuple[int, ...]],
    options: LayoutOptions,
) -> tuple[_Column, ...]:
    levels = _operation_levels(view)
    by_level: dict[int, list[str]] = defaultdict(list)
    for operation_id in view.transform_order:
        by_level[levels[operation_id]].append(operation_id)
    columns: list[_Column] = []
    width = max(options.min_operation_width, min(112.0, options.max_operation_width))
    for level in sorted(by_level):
        slots: list[list[str]] = []
        occupied: list[set[int]] = []
        for operation_id in by_level[level]:
            rows = set(rows_by_operation[operation_id])
            target = next(
                (index for index, used in enumerate(occupied) if used.isdisjoint(rows)),
                None,
            )
            if target is None:
                slots.append([operation_id])
                occupied.append(set(rows))
            else:
                slots[target].append(operation_id)
                occupied[target].update(rows)
        columns.extend(_Column(tuple(slot), width) for slot in slots)
    return tuple(columns)


def _label_width(
    source_ids: tuple[str, ...],
    view: _GraphView,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> float:
    if options.ingredient_label_width is not None:
        return options.ingredient_label_width
    widths = []
    for identifier in source_ids:
        if identifier == "__empty__":
            continue
        for piece in _ingredient_pieces(view.materials[identifier], options, theme):
            widths.append(measurer.measure(piece.text, piece.style).width + 18)
    return max(220.0, min(max(widths, default=280.0), options.max_ingredient_width))


def _final_width(material: MaterialNode, options: LayoutOptions) -> float:
    return max(options.min_operation_width, min(options.max_material_label_width, 150.0))


def _header(
    graph: RecipeGraph,
    canvas_width: float,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> tuple[tuple[TextBlock, ...], float]:
    x = options.safe_margin
    width = canvas_width - options.safe_margin * 2
    title_height = wrap_text(
        graph.title,
        width,
        theme.title_style,
        measurer,
        options.wrap_mode,
    ).height
    title_rect = Rect(x=x, y=options.safe_margin, width=width, height=title_height)
    title = place_text_block(
        identifier="text:table:title",
        role="title",
        text=graph.title,
        rect=title_rect,
        style=theme.title_style,
        measurer=measurer,
        wrap_mode=options.wrap_mode,
    )
    blocks = [title]
    bottom = title_rect.bottom
    if graph.yield_text:
        yield_height = wrap_text(
            graph.yield_text,
            width,
            theme.quantity_style,
            measurer,
            options.wrap_mode,
        ).height
        yield_rect = Rect(x=x, y=bottom + 4, width=width, height=yield_height)
        blocks.append(
            place_text_block(
                identifier="text:table:yield",
                role="recipe-yield",
                text=f"Yield: {graph.yield_text}",
                rect=yield_rect,
                style=theme.quantity_style,
                measurer=measurer,
                wrap_mode=options.wrap_mode,
            )
        )
        bottom = yield_rect.bottom
    return tuple(blocks), bottom + 18


def _setup_rows(
    graph: RecipeGraph,
    view: _GraphView,
    x: float,
    width: float,
    y: float,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> tuple[list[SetupCard], list[LayoutBox], list[TextBlock], float]:
    cards: list[SetupCard] = []
    boxes: list[LayoutBox] = []
    blocks: list[TextBlock] = []
    cursor = y
    for operation_id in view.setup_order:
        node = view.operations[operation_id]
        required_by = _setup_required_by(operation_id, view)
        pieces = _setup_pieces(node, required_by, view, theme)
        height = _stack_height(pieces, width - 20, measurer, options) + 12
        rect = Rect(x=x, y=cursor, width=width, height=height)
        box_id = f"box:table:setup:{operation_id}"
        row_blocks = _place_stack(
            box_id,
            f"text:table:setup:{operation_id}",
            rect,
            pieces,
            measurer,
            options,
            center=True,
        )
        boxes.append(
            LayoutBox(
                id=box_id,
                kind="setup",
                rect=rect,
                text_block_ids=tuple(block.id for block in row_blocks),
                style_class="grid-setup",
                collision_group="setup",
                corner_radius=0,
            )
        )
        blocks.extend(row_blocks)
        cards.append(
            SetupCard(
                operation_id=operation_id,
                label=node.label,
                detail=_operation_detail(node) or None,
                x=x,
                width=width,
                y=cursor,
                height=height,
                rect=rect,
                text_block_ids=tuple(block.id for block in row_blocks),
                required_by_operation_ids=required_by,
            )
        )
        cursor += height
    return cards, boxes, blocks, cursor - y


def _setup_required_by(operation_id: str, view: _GraphView) -> tuple[str, ...]:
    products = set(view.produces.get(operation_id, ())) | {operation_id}
    return tuple(
        transform_id
        for transform_id in view.transform_order
        if products.intersection(view.requires.get(transform_id, ()))
    )


def _setup_pieces(
    node: OperationNode,
    required_by: tuple[str, ...],
    view: _GraphView,
    theme: LayoutTheme,
) -> tuple[_Piece, ...]:
    pieces = [
        _Piece("label", "setup-label", node.label, theme.label_style, "center")
    ]
    if node.target:
        pieces.append(
            _Piece(
                "target",
                "setup-target",
                f"Target: {node.target}",
                theme.detail_style,
                "center",
            )
        )
    detail = _operation_detail(node)
    if detail:
        pieces.append(_Piece("detail", "setup-detail", detail, theme.detail_style, "center"))
    if required_by:
        actions = ", ".join(view.operations[item].action for item in required_by)
        pieces.append(
            _Piece(
                "required",
                "setup-required-by",
                f"Required by: {actions}",
                theme.detail_style,
                "center",
            )
        )
    pieces.extend(
        _Piece(
            f"note:{index}",
            "setup-note",
            f"Note: {note}",
            theme.detail_style,
            "center",
        )
        for index, note in enumerate(node.notes)
    )
    return tuple(pieces)


def _initial_row_heights(
    source_ids: tuple[str, ...],
    view: _GraphView,
    width: float,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
) -> list[float]:
    heights: list[float] = []
    for identifier in source_ids:
        pieces = (
            (_Piece("label", "annotation", "No source material", theme.detail_style),)
            if identifier == "__empty__"
            else _ingredient_pieces(view.materials[identifier], options, theme)
        )
        heights.append(
            max(
                options.minimum_row_height,
                _stack_height(pieces, width - 16, measurer, options) + 12,
            )
        )
    return heights


def _ingredient_pieces(
    material: MaterialNode,
    options: LayoutOptions,
    theme: LayoutTheme,
) -> tuple[_Piece, ...]:
    if options.show_source_quantities and material.source_text:
        primary = material.source_text
        role: TextRole = "ingredient-source"
    elif options.show_source_quantities and material.quantity:
        primary = f"{material.quantity} {material.label}"
        role = "ingredient-label"
    else:
        primary = material.label
        role = "ingredient-label"
    if material.optional and "optional" not in primary.casefold():
        primary = f"{primary} (optional)"
    pieces = [_Piece("primary", role, primary, theme.label_style)]
    if options.show_normalized_quantities:
        normalized = _normalized_quantity_text(material)
        if normalized and normalized not in primary:
            pieces.append(
                _Piece(
                    "normalized",
                    "ingredient-quantity",
                    normalized,
                    theme.quantity_style,
                )
            )
    for suffix, value in (
        ("preparation", material.preparation_state),
        ("temperature", material.temperature_state),
    ):
        if value:
            pieces.append(_Piece(suffix, "ingredient-preparation", value, theme.detail_style))
    pieces.extend(
        _Piece(f"annotation:{index}", "ingredient-annotation", value, theme.detail_style)
        for index, value in enumerate(material.annotations)
    )
    if options.show_provenance:
        pieces.extend(
            _Piece(f"provenance:{index}", "ingredient-provenance", value, theme.detail_style)
            for index, value in enumerate(_provenance_texts(material.provenance))
        )
    return tuple(pieces)


def _operation_pieces(
    view: _GraphView,
    operation_id: str,
    options: LayoutOptions,
    theme: LayoutTheme,
) -> tuple[_Piece, ...]:
    node = view.operations[operation_id]
    pieces = [_Piece("action", "operation-action", node.action, theme.operation_style, "center")]
    direct_inputs = _operation_input_quantity_text(view, operation_id)
    if direct_inputs:
        pieces.append(
            _Piece(
                "uses",
                "operation-input-quantity",
                direct_inputs,
                theme.quantity_style,
                "center",
            )
        )
    detail = _operation_detail(node)
    if detail:
        pieces.append(_Piece("detail", "operation-detail", detail, theme.quantity_style, "center"))
    if node.repeat is not None:
        repeat = node.repeat.model_dump(mode="json", exclude_none=True)
        text = "Repeat: " + " · ".join(f"{key} {value}" for key, value in repeat.items())
        pieces.append(_Piece("repeat", "operation-detail", text, theme.detail_style, "center"))
    if node.until:
        pieces.append(
            _Piece(
                "until",
                "operation-until",
                f"Until {node.until}",
                theme.detail_style,
                "center",
            )
        )
    if options.show_intermediate_labels:
        outputs = [
            _material_label_text(view.materials[material_id])
            for material_id in view.produces.get(operation_id, ())
            if material_id in view.materials and view.materials[material_id].role != "final"
        ]
        if outputs:
            pieces.append(
                _Piece(
                    "outputs",
                    "material-label",
                    f"Makes: {' · '.join(outputs)}",
                    theme.detail_style,
                    "center",
                )
            )
    return tuple(pieces)


def _final_pieces(material: MaterialNode, theme: LayoutTheme) -> tuple[_Piece, ...]:
    return (
        _Piece("label", "final-label", _material_label_text(material), theme.label_style, "center"),
    )


def _stack_height(
    pieces: tuple[_Piece, ...],
    width: float,
    measurer: TextMeasurer,
    options: LayoutOptions,
) -> float:
    heights = [
        wrap_text(piece.text, max(1, width), piece.style, measurer, options.wrap_mode).height
        for piece in pieces
    ]
    return sum(heights) + 4 * max(0, len(heights) - 1)


def _place_stack(
    parent_id: str,
    prefix: str,
    rect: Rect,
    pieces: tuple[_Piece, ...],
    measurer: TextMeasurer,
    options: LayoutOptions,
    *,
    center: bool = False,
) -> tuple[TextBlock, ...]:
    inner_width = max(1, rect.width - 16)
    heights = [
        wrap_text(piece.text, inner_width, piece.style, measurer, options.wrap_mode).height
        for piece in pieces
    ]
    content_height = sum(heights) + 4 * max(0, len(heights) - 1)
    cursor = rect.y + max(6, (rect.height - content_height) / 2 if center else 6)
    blocks: list[TextBlock] = []
    for piece, height in zip(pieces, heights, strict=True):
        text_rect = Rect(x=rect.x + 8, y=cursor, width=inner_width, height=height)
        blocks.append(
            place_text_block(
                identifier=f"{prefix}:{piece.suffix}",
                role=piece.role,
                text=piece.text,
                rect=text_rect,
                style=piece.style,
                measurer=measurer,
                padding=Insets(),
                horizontal_alignment=("center" if center else piece.align),
                vertical_alignment="middle",
                parent_id=parent_id,
                wrap_mode=options.wrap_mode,
            )
        )
        cursor += height + 4
    return tuple(blocks)


def _ensure_run_height(row_heights: list[float], run: tuple[int, int], required: float) -> None:
    start, end = run
    current = sum(row_heights[start : end + 1])
    if current + 0.01 >= required:
        return
    addition = (required - current) / (end - start + 1)
    for index in range(start, end + 1):
        row_heights[index] += addition


def _contiguous_runs(rows: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    ordered = tuple(sorted(set(rows))) or (0,)
    runs: list[tuple[int, int]] = []
    start = previous = ordered[0]
    for row in ordered[1:]:
        if row != previous + 1:
            runs.append((start, previous))
            start = row
        previous = row
    runs.append((start, previous))
    return tuple(runs)


def _primary_run(runs: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(runs, key=lambda run: (run[1] - run[0] + 1, -run[0]))


def _row_tops(table_top: float, heights: list[float]) -> list[float]:
    output: list[float] = []
    cursor = table_top
    for height in heights:
        output.append(cursor)
        cursor += height
    return output


def _run_rect(
    run: tuple[int, int],
    x: float,
    width: float,
    row_tops: list[float],
    row_heights: list[float],
) -> Rect:
    start, end = run
    return Rect(
        x=x,
        y=row_tops[start],
        width=width,
        height=sum(row_heights[start : end + 1]),
    )


def _grid_paths(
    left: float,
    right: float,
    top: float,
    bottom: float,
    row_tops: list[float],
    row_heights: list[float],
) -> list[RoutedPath]:
    boundaries = [top, *(row_tops[index] + row_heights[index] for index in range(len(row_tops)))]
    paths = [
        RoutedPath(
            id=f"path:table:grid:{index}",
            kind="guide",
            points=(Point(x=left, y=y), Point(x=right, y=y)),
            style_class="grid-line",
            stroke_width=1,
        )
        for index, y in enumerate(boundaries)
    ]
    paths.extend(
        (
            RoutedPath(
                id="path:table:border:left",
                kind="guide",
                points=(Point(x=left, y=top), Point(x=left, y=bottom)),
                style_class="grid-line",
                stroke_width=1,
            ),
            RoutedPath(
                id="path:table:border:right",
                kind="guide",
                points=(Point(x=right, y=top), Point(x=right, y=bottom)),
                style_class="grid-line",
                stroke_width=1,
            ),
        )
    )
    return paths


def _blocks_rect(blocks: tuple[TextBlock, ...]) -> Rect:
    left = min(block.rect.x for block in blocks)
    top = min(block.rect.y for block in blocks)
    right = max(block.rect.right for block in blocks)
    bottom = max(block.rect.bottom for block in blocks)
    return Rect(x=left, y=top, width=right - left, height=bottom - top)
