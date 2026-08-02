from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from recipeflow.layout.engine import (
    _GraphView,
    _index_graph,
    _normalized_quantity_text,
    _provenance_texts,
    _scaled_theme,
)
from recipeflow.layout.options import LayoutOptions
from recipeflow.layout.text import place_text_block
from recipeflow.layout.themes import LayoutTheme, get_theme
from recipeflow.layout.validation import validate_tabular_layout
from recipeflow.models.common import Diagnostic, Severity
from recipeflow.models.graph import MaterialNode, OperationNode, RecipeGraph
from recipeflow.models.layout import (
    Insets,
    Lane,
    LayoutBox,
    MaterialSegment,
    MaterialSegmentRole,
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

_MIN_CONTENT_WIDTH = 640.0
_QUANTITY_WIDTH = 58.0
_CONSUMED_TAG_WIDTH = 88.0
_PRODUCED_FOLIO_WIDTH = 34.0
_PRODUCED_TAG_WIDTH = 44.0
_COLUMN_HEADING_HEIGHT = 22.0
_ENTRY_HEAD_MIN_HEIGHT = 24.0
_ENTRY_HEAD_MARKER_ROW_GAP = 2.0
_ENTRY_HEAD_HORIZONTAL_INSET = 12.0
_LINE_MIN_HEIGHT = 19.0
_PAGE_FRONTIER_RESERVE = 78.0


@dataclass(frozen=True)
class _MeasuredPiece:
    suffix: str
    role: TextRole
    text: str
    style: TextStyle
    rect: Rect
    alignment: Literal["start", "center", "end"] = "start"


@dataclass(frozen=True)
class _Leaf:
    identifier: str
    kind: Literal["consumed", "produced", "condition", "balance", "empty"]
    box_kind: Literal["ingredient", "material-label", "final-output", "annotation"]
    style_class: str
    width: float
    height: float
    pieces: tuple[_MeasuredPiece, ...]
    material_id: str | None = None
    material_label: str | None = None
    material_quantity: str | None = None
    material_role: MaterialSegmentRole | None = None
    consumed: bool = False


@dataclass(frozen=True)
class _Entry:
    operation_id: str
    index: int
    action: str
    marker: str | None
    head_height: float
    head_pieces: tuple[_MeasuredPiece, ...]
    consumed: tuple[_Leaf, ...]
    produced: tuple[_Leaf, ...]
    conditions: tuple[_Leaf, ...]

    @property
    def body_height(self) -> float:
        return max(
            _LINE_MIN_HEIGHT,
            sum(item.height for item in self.consumed),
            sum(item.height for item in self.produced),
            sum(item.height for item in self.conditions),
        )

    @property
    def height(self) -> float:
        return self.head_height + self.body_height


@dataclass(frozen=True)
class _EntryFragment:
    consumed: tuple[_Leaf, ...]
    produced: tuple[_Leaf, ...]
    conditions: tuple[_Leaf, ...]

    @property
    def body_height(self) -> float:
        return max(
            _LINE_MIN_HEIGHT,
            sum(item.height for item in self.consumed),
            sum(item.height for item in self.produced),
            sum(item.height for item in self.conditions),
        )


class LedgerLayoutStrategy:
    """Render a graph as a folio-numbered double-entry kitchen ledger."""

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
        width = max(
            options.preferred_width or 0,
            _MIN_CONTENT_WIDTH + 2 * options.safe_margin,
        )
        content_x = options.safe_margin
        content_width = width - 2 * options.safe_margin
        consumed_width = max(260.0, math.floor(content_width * 0.4785))
        produced_width = max(150.0, math.floor(content_width * 0.2687))
        conditions_width = content_width - consumed_width - produced_width
        if conditions_width < 140:
            shortage = 140 - conditions_width
            consumed_width -= shortage
            conditions_width = 140.0
        folios = _folio_map(view, graph)
        edge_kinds: dict[tuple[str, str], str] = {
            (edge.target, edge.source): edge.kind.value
            for edge in graph.edges
            if edge.kind.value in {"consumes", "reserves", "optionally-applies"}
        }
        output_kinds: dict[tuple[str, str], str] = {
            (edge.source, edge.target): edge.kind.value
            for edge in graph.edges
            if edge.kind.value in {"produces", "reserves", "discards"}
        }
        markers = _material_branch_markers(view)
        setup_folios, setup_references = _setup_reference_maps(view)
        transform_folios = {
            operation_id: index for index, operation_id in enumerate(view.transform_order, start=1)
        }
        precedes = _predecessors(graph)

        strategy_diagnostics = list(_allocation_diagnostics(view))
        strategy_diagnostics.extend(_held_diagnostics(view, output_kinds))
        entries = tuple(
            _entry_model(
                view=view,
                graph=graph,
                operation_id=operation_id,
                index=index,
                marker=markers.get(operation_id),
                folios=folios,
                setup_references=setup_references,
                transform_folios=transform_folios,
                predecessors=precedes.get(operation_id, ()),
                edge_kinds=edge_kinds,
                output_kinds=output_kinds,
                options=options,
                theme=theme,
                measurer=measurer,
                consumed_width=consumed_width,
                produced_width=produced_width,
                conditions_width=conditions_width,
            )
            for index, operation_id in enumerate(view.transform_order, start=1)
        )

        text_blocks: list[TextBlock] = []
        boxes: list[LayoutBox] = []
        paths: list[RoutedPath] = []
        reading_order: list[str] = []
        materials: list[MaterialSegment] = []
        operations: list[OperationCell] = []
        lanes: list[Lane] = []

        y = options.safe_margin
        title_height = _text_height(
            graph.title,
            content_width,
            theme.title_style,
            measurer,
            options,
        )
        title_rect = Rect(x=content_x, y=y, width=content_width, height=title_height)
        title_box_id = "box:ledger:band:title"
        title_block = place_text_block(
            identifier="text:ledger:band:title",
            role="title",
            text=graph.title,
            rect=title_rect,
            style=theme.title_style,
            measurer=measurer,
            parent_id=title_box_id,
            wrap_mode=options.wrap_mode,
        )
        text_blocks.append(title_block)
        reading_order.append(title_block.id)
        boxes.append(
            LayoutBox(
                id=title_box_id,
                kind="title",
                rect=title_rect,
                text_block_ids=(title_block.id,),
                style_class="ledger-band",
                opaque=True,
                collision_group="ledger-leaf",
                corner_radius=0,
            )
        )
        y += title_height + 4
        if graph.yield_text:
            yield_height = _text_height(
                graph.yield_text,
                content_width,
                theme.quantity_style,
                measurer,
                options,
            )
            yield_rect = Rect(
                x=content_x,
                y=y,
                width=content_width,
                height=yield_height,
            )
            yield_box_id = "box:ledger:band:yield"
            yield_block = place_text_block(
                identifier="text:ledger:band:yield",
                role="recipe-yield",
                text=graph.yield_text,
                rect=yield_rect,
                style=theme.quantity_style,
                measurer=measurer,
                parent_id=yield_box_id,
                wrap_mode=options.wrap_mode,
            )
            text_blocks.append(yield_block)
            reading_order.append(yield_block.id)
            boxes.append(
                LayoutBox(
                    id=yield_box_id,
                    kind="annotation",
                    rect=yield_rect,
                    text_block_ids=(yield_block.id,),
                    style_class="ledger-band",
                    opaque=True,
                    collision_group="ledger-leaf",
                    corner_radius=0,
                )
            )
            y += yield_height
        y += 12
        boxes.append(_rule("header", 0, content_x, y, content_width, "ledger-rule"))
        y += 1
        header_height = y

        setup_cards: list[SetupCard] = []
        setup_start = y
        if view.setup_order:
            y += 6
            heading_height = max(18.0, theme.mono_style.line_height)
            heading_id = "box:ledger:band:standing"
            heading_rect = Rect(
                x=content_x,
                y=y,
                width=content_width,
                height=heading_height,
            )
            heading_block = place_text_block(
                identifier="text:ledger:band:standing:heading",
                role="annotation",
                text="STANDING CONDITIONS",
                rect=heading_rect,
                style=theme.mono_style,
                measurer=measurer,
                padding=Insets(left=4, right=4),
                vertical_alignment="middle",
                parent_id=heading_id,
                wrap_mode=options.wrap_mode,
            )
            text_blocks.append(heading_block)
            reading_order.append(heading_block.id)
            boxes.append(
                LayoutBox(
                    id=heading_id,
                    kind="annotation",
                    rect=heading_rect,
                    text_block_ids=(heading_block.id,),
                    style_class="ledger-band",
                    opaque=True,
                    collision_group="ledger-leaf",
                    corner_radius=0,
                )
            )
            y += heading_height
            setup_cards, y = _place_setup_rows(
                view=view,
                setup_folios=setup_folios,
                setup_references=setup_references,
                transform_folios=transform_folios,
                content_x=content_x,
                content_width=content_width,
                start_y=y,
                theme=theme,
                options=options,
                measurer=measurer,
                boxes=boxes,
                text_blocks=text_blocks,
                reading_order=reading_order,
            )
            boxes.append(_rule("standing", 0, content_x, y + 3, content_width))
            boxes.append(_rule("standing", 1, content_x, y + 5, content_width))
            y += 6
        setup_height = y - setup_start if view.setup_order else 0.0

        heading_y = y + 5
        heading_height = _place_column_headings(
            y=heading_y,
            suffix="first",
            content_x=content_x,
            consumed_width=consumed_width,
            produced_width=produced_width,
            conditions_width=conditions_width,
            theme=theme,
            options=options,
            measurer=measurer,
            boxes=boxes,
            text_blocks=text_blocks,
            reading_order=reading_order,
            include_in_reading_order=True,
        )
        y = heading_y + heading_height
        boxes.append(_rule("columns", 0, content_x, y, content_width))
        y += 1

        page_height = options.page_height if options.print_mode else None
        page_index = 0
        page_has_entry = False

        def page_bottom() -> float:
            assert page_height is not None
            return (page_index + 1) * page_height

        def page_limit() -> float:
            assert page_height is not None
            return page_bottom() - options.safe_margin - _PAGE_FRONTIER_RESERVE

        def add_break(completed_entries: int) -> None:
            nonlocal y, page_index, page_has_entry
            assert page_height is not None
            bottom = page_bottom()
            _place_frontier(
                view=view,
                folios=folios,
                completed_entries=completed_entries,
                sheet_number=page_index + 1,
                y=bottom - options.safe_margin - _PAGE_FRONTIER_RESERVE,
                height=_PAGE_FRONTIER_RESERVE,
                content_x=content_x,
                content_width=content_width,
                theme=theme,
                options=options,
                measurer=measurer,
                boxes=boxes,
                text_blocks=text_blocks,
                reading_order=reading_order,
            )
            paths.append(
                RoutedPath(
                    id=f"path:ledger:sheet-break:{page_index + 1}",
                    kind="guide",
                    points=(
                        Point(x=content_x, y=bottom),
                        Point(x=content_x + content_width, y=bottom),
                    ),
                    style_class="sheet-break",
                    stroke_width=1,
                )
            )
            page_index += 1
            page_has_entry = False
            next_page_top = page_index * page_height
            repeated_y = next_page_top + options.safe_margin
            repeated_height = _place_column_headings(
                y=repeated_y,
                suffix=f"sheet:{page_index + 1}",
                content_x=content_x,
                consumed_width=consumed_width,
                produced_width=produced_width,
                conditions_width=conditions_width,
                theme=theme,
                options=options,
                measurer=measurer,
                boxes=boxes,
                text_blocks=text_blocks,
                reading_order=reading_order,
                include_in_reading_order=False,
            )
            y = repeated_y + repeated_height
            boxes.append(
                _rule(
                    "columns",
                    page_index,
                    content_x,
                    y,
                    content_width,
                )
            )
            y += 1

        for entry in entries:
            fragments: tuple[_EntryFragment, ...]
            if page_height is None:
                fragments = (_EntryFragment(entry.consumed, entry.produced, entry.conditions),)
            else:
                fresh_body_capacity = (
                    page_height
                    - 2 * options.safe_margin
                    - _COLUMN_HEADING_HEIGHT
                    - 1
                    - _PAGE_FRONTIER_RESERVE
                    - entry.head_height
                )
                if fresh_body_capacity <= 0:
                    strategy_diagnostics.append(
                        _pagination_diagnostic(
                            entry.operation_id,
                            "The selected page has no usable entry area.",
                        )
                    )
                    fragments = (_EntryFragment(entry.consumed, entry.produced, entry.conditions),)
                elif entry.height <= fresh_body_capacity + entry.head_height:
                    fragments = (_EntryFragment(entry.consumed, entry.produced, entry.conditions),)
                else:
                    too_tall = next(
                        (
                            leaf
                            for leaf in (
                                *entry.consumed,
                                *entry.produced,
                                *entry.conditions,
                            )
                            if leaf.height > fresh_body_capacity + 0.01
                        ),
                        None,
                    )
                    if too_tall is not None:
                        strategy_diagnostics.append(
                            _pagination_diagnostic(
                                entry.operation_id,
                                f"Semantic leaf '{too_tall.identifier}' is taller than "
                                "the usable page area.",
                            )
                        )
                        fragments = (
                            _EntryFragment(entry.consumed, entry.produced, entry.conditions),
                        )
                    else:
                        fragments = _fragment_entry(entry, fresh_body_capacity)

            if page_height is not None:
                first_height = entry.head_height + fragments[0].body_height
                if y + first_height > page_limit() + 0.01:
                    add_break(entry.index - 1)

            first_y: float | None = None
            last_bottom = y
            fragment_box_ids: list[str] = []
            operation_text_ids: list[str] = []
            for fragment_index, fragment in enumerate(fragments):
                if page_height is not None:
                    fragment_height = entry.head_height + fragment.body_height
                    if y + fragment_height > page_limit() + 0.01 and page_has_entry:
                        add_break(entry.index - 1)
                fragment_top = y
                if first_y is None:
                    first_y = fragment_top
                fragment_box_id, fragment_text_ids, fragment_bottom = _place_entry_fragment(
                    entry=entry,
                    fragment=fragment,
                    fragment_index=fragment_index,
                    x=content_x,
                    y=fragment_top,
                    consumed_width=consumed_width,
                    produced_width=produced_width,
                    conditions_width=conditions_width,
                    theme=theme,
                    options=options,
                    measurer=measurer,
                    boxes=boxes,
                    text_blocks=text_blocks,
                    reading_order=reading_order,
                    materials=materials,
                )
                fragment_box_ids.append(fragment_box_id)
                operation_text_ids.extend(fragment_text_ids)
                y = fragment_bottom + 6
                last_bottom = fragment_bottom
                page_has_entry = True
                if page_height is not None and fragment_index < len(fragments) - 1:
                    add_break(entry.index - 1)

            assert first_y is not None
            entry_rect = Rect(
                x=content_x,
                y=first_y,
                width=content_width,
                height=last_bottom - first_y,
            )
            operations.append(
                OperationCell(
                    operation_id=entry.operation_id,
                    label=view.operations[entry.operation_id].label,
                    action=entry.action,
                    x=content_x,
                    y1=first_y,
                    y2=last_bottom,
                    input_material_ids=view.consumes.get(entry.operation_id, ()),
                    output_material_ids=view.produces.get(entry.operation_id, ()),
                    duration=view.operations[entry.operation_id].duration,
                    temperature=view.operations[entry.operation_id].temperature,
                    until=view.operations[entry.operation_id].until,
                    rect=entry_rect,
                    text_block_ids=tuple(operation_text_ids),
                    box_ids=tuple(fragment_box_ids),
                    orientation="horizontal",
                )
            )
            outputs = view.produces.get(entry.operation_id, ())
            lanes.append(
                Lane(
                    index=entry.index - 1,
                    y=first_y + entry.head_height / 2,
                    height=last_bottom - first_y,
                    initial_material_id=outputs[0] if outputs else None,
                )
            )

        if not entries:
            empty_height = max(_LINE_MIN_HEIGHT, theme.detail_style.line_height + 8)
            empty_id = "box:ledger:band:no-operations"
            empty_rect = Rect(
                x=content_x,
                y=y + 6,
                width=content_width,
                height=empty_height,
            )
            empty_block = place_text_block(
                identifier="text:ledger:band:no-operations",
                role="annotation",
                text="no operations",
                rect=empty_rect,
                style=theme.detail_style,
                measurer=measurer,
                padding=Insets(left=4, right=4),
                vertical_alignment="middle",
                parent_id=empty_id,
                wrap_mode=options.wrap_mode,
            )
            boxes.append(
                LayoutBox(
                    id=empty_id,
                    kind="annotation",
                    rect=empty_rect,
                    text_block_ids=(empty_block.id,),
                    style_class="ledger-band",
                    opaque=True,
                    collision_group="ledger-leaf",
                    corner_radius=0,
                )
            )
            text_blocks.append(empty_block)
            reading_order.append(empty_block.id)
            y = empty_rect.bottom + 6

        boxes.append(_rule("footer", 0, content_x, y, content_width))
        boxes.append(_rule("footer", 1, content_x, y + 2, content_width))
        y += 3
        if page_height is None:
            height = y + options.safe_margin
        else:
            height = max(
                page_height, math.ceil((y + options.safe_margin) / page_height) * page_height
            )

        layout = TabularLayout(
            title=graph.title,
            notation="ledger",
            width=_rounded(width),
            height=_rounded(height),
            label_width=_rounded(consumed_width),
            header_height=_rounded(header_height),
            setup_height=_rounded(setup_height),
            row_height=_rounded(max((entry.height for entry in entries), default=_LINE_MIN_HEIGHT)),
            lanes=tuple(lanes),
            materials=tuple(materials),
            operations=tuple(operations),
            setup=tuple(setup_cards),
            final_material_ids=graph.final_material_ids,
            safe_margin=options.safe_margin,
            theme=options.theme,
            text_blocks=tuple(text_blocks),
            boxes=tuple(boxes),
            paths=tuple(paths),
            reading_order=tuple(reading_order),
            diagnostics=tuple(strategy_diagnostics),
        )
        generic = validate_tabular_layout(layout)
        return layout.model_copy(
            update={"diagnostics": _merge_diagnostics(tuple(strategy_diagnostics), generic)}
        )


def _entry_model(
    *,
    view: _GraphView,
    graph: RecipeGraph,
    operation_id: str,
    index: int,
    marker: str | None,
    folios: dict[str, str | None],
    setup_references: dict[str, str],
    transform_folios: dict[str, int],
    predecessors: tuple[str, ...],
    edge_kinds: dict[tuple[str, str], str],
    output_kinds: dict[tuple[str, str], str],
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
    consumed_width: float,
    produced_width: float,
    conditions_width: float,
) -> _Entry:
    node = view.operations[operation_id]
    head_marker = marker
    if node.optional:
        head_marker = f"{head_marker} · optional" if head_marker else "optional"
    head_pieces, head_height = _head_pieces(
        index,
        node.action,
        head_marker,
        consumed_width + produced_width + conditions_width,
        theme,
        measurer,
        options,
    )

    input_quantities: dict[str, list[str]] = defaultdict(list)
    for material_id, quantity in view.input_quantities.get(operation_id, ()):
        input_quantities[material_id].append(quantity)
    occurrences: dict[str, int] = defaultdict(int)
    consumed: list[_Leaf] = []
    for material_id in view.consumes.get(operation_id, ()):
        material = view.materials[material_id]
        occurrence = occurrences[material_id]
        occurrences[material_id] += 1
        allocations = input_quantities.get(material_id, [])
        allocation = allocations[occurrence] if occurrence < len(allocations) else None
        consumed.append(
            _consumed_leaf(
                operation_id=operation_id,
                material=material,
                occurrence=occurrence,
                allocation=allocation,
                producer_folio=folios.get(material_id),
                edge_kind=edge_kinds.get((operation_id, material_id), "consumes"),
                has_multiple_consumers=len(view.consumers.get(material_id, ())) > 1,
                options=options,
                theme=theme,
                measurer=measurer,
                width=consumed_width,
            )
        )
    if not consumed:
        consumed.append(
            _single_text_leaf(
                identifier=f"consumed:{operation_id}:none",
                kind="empty",
                box_kind="ingredient",
                style_class="ledger-consumed",
                width=consumed_width,
                suffix="annotation",
                role="annotation",
                text="no direct inputs",
                style=theme.detail_style,
                measurer=measurer,
                options=options,
            )
        )

    balance = _balance(view, operation_id)
    if balance is not None:
        consumed.append(
            _single_text_leaf(
                identifier=f"balance:{operation_id}",
                kind="balance",
                box_kind="annotation",
                style_class="ledger-balance",
                width=consumed_width,
                suffix="balance",
                role="allocation-balance",
                text=f"{balance}  balanced",
                style=theme.mono_style,
                measurer=measurer,
                options=options,
            )
        )

    produced = tuple(
        _produced_leaf(
            operation_id=operation_id,
            material=view.materials[material_id],
            occurrence=occurrence,
            folio=folios.get(material_id),
            edge_kind=output_kinds.get((operation_id, material_id), "produces"),
            options=options,
            theme=theme,
            measurer=measurer,
            width=produced_width,
        )
        for occurrence, material_id in enumerate(view.produces.get(operation_id, ()))
    )
    conditions = _condition_leaves(
        node=node,
        operation_id=operation_id,
        requires=view.requires.get(operation_id, ()),
        setup_references=setup_references,
        transform_folios=transform_folios,
        predecessors=predecessors,
        options=options,
        theme=theme,
        measurer=measurer,
        width=conditions_width,
    )
    return _Entry(
        operation_id=operation_id,
        index=index,
        action=node.action,
        marker=head_marker,
        head_height=head_height,
        head_pieces=head_pieces,
        consumed=tuple(consumed),
        produced=produced,
        conditions=conditions,
    )


def _head_pieces(
    index: int,
    action: str,
    marker: str | None,
    width: float,
    theme: LayoutTheme,
    measurer: TextMeasurer,
    options: LayoutOptions,
) -> tuple[tuple[_MeasuredPiece, ...], float]:
    action_text = f"{index:02d}  {action}"
    content_width = width - (2 * _ENTRY_HEAD_HORIZONTAL_INSET)
    action_height = _text_height(
        action_text, content_width, theme.operation_style, measurer, options
    )
    marker_height = _text_height(
        marker or "", content_width, theme.mono_style, measurer, options
    )
    action_y = (
        3 + marker_height + _ENTRY_HEAD_MARKER_ROW_GAP
        if marker
        else 3
    )
    height = max(_ENTRY_HEAD_MIN_HEIGHT, action_y + action_height + 3)
    pieces = [
        _MeasuredPiece(
            suffix="action",
            role="operation-action",
            text=action_text,
            style=theme.operation_style,
            rect=Rect(
                x=_ENTRY_HEAD_HORIZONTAL_INSET,
                y=action_y,
                width=content_width,
                height=action_height,
            ),
        )
    ]
    if marker:
        pieces.append(
            _MeasuredPiece(
                suffix="marker",
                role="annotation",
                text=marker,
                style=theme.mono_style,
                rect=Rect(
                    x=_ENTRY_HEAD_HORIZONTAL_INSET,
                    y=3,
                    width=content_width,
                    height=marker_height,
                ),
                alignment="end",
            )
        )
    return tuple(pieces), height


def _consumed_leaf(
    *,
    operation_id: str,
    material: MaterialNode,
    occurrence: int,
    allocation: str | None,
    producer_folio: str | None,
    edge_kind: str,
    has_multiple_consumers: bool,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
    width: float,
) -> _Leaf:
    source = producer_folio is None
    authored_total = _visible_quantity(material, options)
    partial = allocation is not None and (
        has_multiple_consumers
        or (authored_total is not None and allocation.strip() != authored_total.strip())
    )
    quantity: str | None
    if allocation is not None:
        quantity = allocation
    elif source:
        quantity = authored_total
    else:
        quantity = "all"
    authored_source = (
        material.source_text
        if source and options.show_source_quantities and material.source_text
        else None
    )
    label = material.label
    if material.role.value == "reserved":
        tag = "from reserve"
    elif edge_kind == "optionally-applies" or material.optional:
        tag = "optional"
    elif partial:
        tag = "part draw"
    elif source:
        tag = "source"
    else:
        tag = f"from {producer_folio}"

    label_width = max(
        60.0,
        width - _QUANTITY_WIDTH - 8 - _CONSUMED_TAG_WIDTH - 12,
    )
    label_specs: list[tuple[str, TextRole, str, TextStyle]] = [
        (
            "label",
            "ingredient-label" if source else "material-label",
            label,
            _ledger_label_style(theme, options),
        )
    ]
    if authored_source:
        label_specs.append(
            (
                "source",
                "ingredient-source",
                authored_source,
                theme.detail_style,
            )
        )
    if partial and authored_total:
        label_specs.append(
            (
                "authored-total",
                "ingredient-annotation",
                f"{allocation} allocated · {authored_total} authored total",
                theme.detail_style,
            )
        )
    state = " · ".join(
        value for value in (material.preparation_state, material.temperature_state) if value
    )
    if state:
        label_specs.append(("state", "ingredient-preparation", state, theme.detail_style))
    label_specs.extend(
        (f"annotation:{index}", "ingredient-annotation", text, theme.detail_style)
        for index, text in enumerate(material.annotations)
    )
    if options.show_provenance:
        label_specs.extend(
            (f"provenance:{index}", "ingredient-provenance", text, theme.detail_style)
            for index, text in enumerate(_provenance_texts(material.provenance))
        )
    label_pieces, label_height = _stack_pieces(
        label_specs,
        x=_QUANTITY_WIDTH + 8,
        width=label_width,
        measurer=measurer,
        options=options,
    )
    quantity_height = _text_height(
        quantity or "—", _QUANTITY_WIDTH, theme.mono_style, measurer, options
    )
    tag_height = _text_height(tag, _CONSUMED_TAG_WIDTH - 4, theme.mono_style, measurer, options)
    height = max(_LINE_MIN_HEIGHT, label_height + 6, quantity_height + 6, tag_height + 6)
    pieces: list[_MeasuredPiece] = [
        _MeasuredPiece(
            suffix="quantity",
            role="operation-input-quantity",
            text=quantity or "—",
            style=theme.mono_style,
            rect=Rect(x=0, y=3, width=_QUANTITY_WIDTH, height=height - 6),
            alignment="end",
        ),
        *(
            piece.__class__(
                suffix=piece.suffix,
                role=piece.role,
                text=piece.text,
                style=piece.style,
                rect=piece.rect.model_copy(update={"y": piece.rect.y + 3}),
                alignment=piece.alignment,
            )
            for piece in label_pieces
        ),
        _MeasuredPiece(
            suffix="tag",
            role="annotation",
            text=tag,
            style=theme.mono_style,
            rect=Rect(
                x=width - _CONSUMED_TAG_WIDTH - 4,
                y=3,
                width=_CONSUMED_TAG_WIDTH,
                height=height - 6,
            ),
            alignment="end",
        ),
    ]
    identifier = f"consumed:{operation_id}:{material.id}"
    if occurrence:
        identifier += f":{occurrence + 1}"
    return _Leaf(
        identifier=identifier,
        kind="consumed",
        box_kind="ingredient",
        style_class="ledger-consumed-part" if partial else "ledger-consumed",
        width=width,
        height=height,
        pieces=tuple(pieces),
        material_id=material.id,
        material_label=material.label,
        material_quantity=allocation or authored_total,
        material_role=material.role.value,
        consumed=True,
    )


def _produced_leaf(
    *,
    operation_id: str,
    material: MaterialNode,
    occurrence: int,
    folio: str | None,
    edge_kind: str,
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
    width: float,
) -> _Leaf:
    del occurrence
    quantity = _visible_quantity(material, options)
    label = f"{quantity}  {material.label}" if quantity else material.label
    role = material.role.value
    if role == "final":
        tag = "FINAL"
    elif role == "reserved" or edge_kind == "reserves":
        tag = "HELD"
        role = "reserved"
    elif role == "waste" or edge_kind == "discards":
        tag = "WASTE"
        role = "waste"
    elif role == "garnish":
        tag = "GARNISH"
    elif role == "optional" or material.optional:
        tag = "optional"
        role = "optional"
    else:
        tag = ""
    tag_width = (
        min(
            60.0,
            max(
                _PRODUCED_TAG_WIDTH,
                measurer.measure(tag, theme.mono_style).width + 6,
            ),
        )
        if tag
        else 0.0
    )
    label_width = max(45.0, width - _PRODUCED_FOLIO_WIDTH - tag_width - 12)
    label_specs: list[tuple[str, TextRole, str, TextStyle]] = [
        (
            "label",
            "final-label" if role == "final" else "material-label",
            label,
            _ledger_label_style(theme, options),
        )
    ]
    if options.show_provenance:
        label_specs.extend(
            (f"provenance:{index}", "ingredient-provenance", text, theme.detail_style)
            for index, text in enumerate(_provenance_texts(material.provenance))
        )
    label_pieces, label_height = _stack_pieces(
        label_specs,
        x=_PRODUCED_FOLIO_WIDTH + 6,
        width=label_width,
        measurer=measurer,
        options=options,
    )
    folio_height = _text_height(
        folio or "—", _PRODUCED_FOLIO_WIDTH, theme.mono_style, measurer, options
    )
    tag_height = (
        _text_height(tag, tag_width - 4, theme.mono_style, measurer, options)
        if tag
        else 0.0
    )
    height = max(_LINE_MIN_HEIGHT, label_height + 6, folio_height + 6, tag_height + 6)
    pieces: list[_MeasuredPiece] = [
        _MeasuredPiece(
            suffix="folio",
            role="material-label",
            text=folio or "—",
            style=theme.mono_style,
            rect=Rect(x=4, y=3, width=_PRODUCED_FOLIO_WIDTH - 4, height=height - 6),
        ),
        *(
            piece.__class__(
                suffix=piece.suffix,
                role=piece.role,
                text=piece.text,
                style=piece.style,
                rect=piece.rect.model_copy(update={"y": piece.rect.y + 3}),
                alignment=piece.alignment,
            )
            for piece in label_pieces
        ),
    ]
    if tag:
        pieces.append(
            _MeasuredPiece(
                suffix="tag",
                role="annotation",
                text=tag,
                style=theme.mono_style,
                rect=Rect(
                    x=width - tag_width - 4,
                    y=3,
                    width=tag_width,
                    height=height - 6,
                ),
                alignment="end",
            )
        )
    return _Leaf(
        identifier=f"produced:{operation_id}:{material.id}",
        kind="produced",
        box_kind="final-output" if role == "final" else "material-label",
        style_class="ledger-final" if role == "final" else "ledger-produced",
        width=width,
        height=height,
        pieces=tuple(pieces),
        material_id=material.id,
        material_label=material.label,
        material_quantity=quantity,
        material_role=role,  # type: ignore[arg-type]
        consumed=False,
    )


def _condition_leaves(
    *,
    node: OperationNode,
    operation_id: str,
    requires: tuple[str, ...],
    setup_references: dict[str, str],
    transform_folios: dict[str, int],
    predecessors: tuple[str, ...],
    options: LayoutOptions,
    theme: LayoutTheme,
    measurer: TextMeasurer,
    width: float,
) -> tuple[_Leaf, ...]:
    specs: list[tuple[str, TextRole, str, TextStyle, str]] = []
    if node.duration:
        specs.append(
            (
                "duration",
                "operation-detail",
                f"Time {_display_duration(node.duration)}",
                theme.mono_style,
                "detail",
            )
        )
    if node.temperature:
        prefix = "Oven" if "bake" in node.action.lower() else "Heat"
        specs.append(
            (
                "temperature",
                "operation-detail",
                f"{prefix} {node.temperature}",
                theme.mono_style,
                "detail",
            )
        )
    if node.repeat is not None:
        repeat = node.repeat.model_dump(mode="json", exclude_none=True)
        repeat_text = " · ".join(f"{key} {value}" for key, value in repeat.items())
        specs.append(
            ("repeat", "operation-detail", f"Repeat {repeat_text}", theme.mono_style, "detail")
        )
    for requirement in requires:
        if requirement in setup_references:
            text = setup_references[requirement]
        elif requirement in transform_folios:
            text = f"Requires entry {transform_folios[requirement]}"
        else:
            text = f"Requires {requirement}"
        specs.append(
            (f"requires:{requirement}", "setup-required-by", text, theme.mono_style, "requires")
        )
    for predecessor in predecessors:
        if predecessor in transform_folios:
            specs.append(
                (
                    f"after:{predecessor}",
                    "operation-detail",
                    f"After entry {transform_folios[predecessor]}",
                    theme.mono_style,
                    "requires",
                )
            )
    if node.equipment:
        specs.append(
            (
                "equipment",
                "operation-detail",
                f"Equipment: {', '.join(node.equipment)}",
                theme.detail_style,
                "detail",
            )
        )
    if node.resources:
        resources = ", ".join(
            f"{item.quantity} x {item.label or item.id}"
            if item.quantity != 1
            else (item.label or item.id)
            for item in node.resources
        )
        specs.append(
            (
                "resources",
                "operation-detail",
                f"Resources: {resources}",
                theme.detail_style,
                "detail",
            )
        )
    specs.extend(
        (f"note:{index}", "annotation", note, theme.detail_style, "detail")
        for index, note in enumerate(node.notes)
    )
    if node.until:
        specs.append(
            ("until", "operation-until", f"Until {node.until}", theme.detail_style, "until")
        )
    for index, ambiguity in enumerate(node.ambiguity):
        alternatives = (
            f" Alternatives: {'; '.join(ambiguity.alternatives)}" if ambiguity.alternatives else ""
        )
        specs.append(
            (
                f"ambiguity:{index}",
                "annotation",
                f"? {ambiguity.description}{alternatives}",
                theme.detail_style,
                "detail",
            )
        )
    if options.show_provenance:
        specs.extend(
            (f"provenance:{index}", "annotation", text, theme.detail_style, "detail")
            for index, text in enumerate(_provenance_texts(node.provenance))
        )
    if not specs:
        return (
            _Leaf(
                identifier=f"conditions:{operation_id}:empty",
                kind="empty",
                box_kind="annotation",
                style_class="ledger-conditions",
                width=width,
                height=_LINE_MIN_HEIGHT,
                pieces=(),
            ),
        )
    return tuple(
        _single_text_leaf(
            identifier=f"conditions:{operation_id}:{suffix}",
            kind="condition",
            box_kind="annotation",
            style_class=("ledger-requires" if semantic_kind == "requires" else "ledger-conditions"),
            width=width,
            suffix=suffix,
            role=role,
            text=text,
            style=style,
            measurer=measurer,
            options=options,
        )
        for suffix, role, text, style, semantic_kind in specs
    )


def _single_text_leaf(
    *,
    identifier: str,
    kind: Literal["condition", "balance", "empty"],
    box_kind: Literal["ingredient", "annotation"],
    style_class: str,
    width: float,
    suffix: str,
    role: TextRole,
    text: str,
    style: TextStyle,
    measurer: TextMeasurer,
    options: LayoutOptions,
) -> _Leaf:
    content_width = max(1.0, width - 12)
    text_height = _text_height(text, content_width, style, measurer, options)
    height = max(_LINE_MIN_HEIGHT, text_height + 8)
    return _Leaf(
        identifier=identifier,
        kind=kind,
        box_kind=box_kind,
        style_class=style_class,
        width=width,
        height=height,
        pieces=(
            _MeasuredPiece(
                suffix=suffix,
                role=role,
                text=text,
                style=style,
                rect=Rect(x=6, y=4, width=content_width, height=height - 8),
            ),
        ),
    )


def _place_entry_fragment(
    *,
    entry: _Entry,
    fragment: _EntryFragment,
    fragment_index: int,
    x: float,
    y: float,
    consumed_width: float,
    produced_width: float,
    conditions_width: float,
    theme: LayoutTheme,
    options: LayoutOptions,
    measurer: TextMeasurer,
    boxes: list[LayoutBox],
    text_blocks: list[TextBlock],
    reading_order: list[str],
    materials: list[MaterialSegment],
) -> tuple[str, list[str], float]:
    del theme
    content_width = consumed_width + produced_width + conditions_width
    body_height = fragment.body_height
    fragment_height = entry.head_height + body_height
    suffix = "" if fragment_index == 0 else f":fragment:{fragment_index + 1}"
    frame_id = f"box:ledger:entry:{entry.operation_id}{suffix}"
    frame_rect = Rect(x=x, y=y, width=content_width, height=fragment_height)
    boxes.append(
        LayoutBox(
            id=frame_id,
            kind="operation",
            rect=frame_rect,
            style_class="ledger-entry",
            opaque=False,
            collision_group="entry",
            corner_radius=0,
        )
    )
    head_id = f"box:ledger:entry-head:{entry.operation_id}{suffix}"
    head_rect = Rect(x=x, y=y, width=content_width, height=entry.head_height)
    head_block_ids: list[str] = []
    operation_text_ids: list[str] = []
    if fragment_index == 0:
        for piece in entry.head_pieces:
            block_id = f"text:ledger:entry:{entry.operation_id}:{piece.suffix}"
            block = _place_measured_piece(
                block_id=block_id,
                parent_id=head_id,
                piece=piece,
                origin_x=x,
                origin_y=y,
                measurer=measurer,
                options=options,
            )
            text_blocks.append(block)
            head_block_ids.append(block.id)
            operation_text_ids.append(block.id)
            reading_order.append(block.id)
    else:
        continued_piece = _MeasuredPiece(
            suffix="continued",
            role="operation-action",
            text=f"{entry.index:02d}  {entry.action} (continued)",
            style=entry.head_pieces[0].style,
            rect=Rect(
                x=_ENTRY_HEAD_HORIZONTAL_INSET,
                y=3,
                width=content_width - (2 * _ENTRY_HEAD_HORIZONTAL_INSET),
                height=entry.head_height - 6,
            ),
        )
        block_id = f"text:ledger:entry:{entry.operation_id}:continued:{fragment_index + 1}"
        block = _place_measured_piece(
            block_id=block_id,
            parent_id=head_id,
            piece=continued_piece,
            origin_x=x,
            origin_y=y,
            measurer=measurer,
            options=options,
        )
        text_blocks.append(block)
        head_block_ids.append(block.id)
        operation_text_ids.append(block.id)
    boxes.append(
        LayoutBox(
            id=head_id,
            kind="operation",
            rect=head_rect,
            text_block_ids=tuple(head_block_ids),
            style_class="ledger-entry-head",
            opaque=True,
            collision_group="ledger-leaf",
            corner_radius=0,
        )
    )

    body_y = y + entry.head_height
    columns = (
        (fragment.consumed, x),
        (fragment.produced, x + consumed_width),
        (fragment.conditions, x + consumed_width + produced_width),
    )
    for leaves, column_x in columns:
        leaf_y = body_y
        for leaf in leaves:
            block_ids, segment = _place_leaf(
                leaf=leaf,
                operation_id=entry.operation_id,
                lane=entry.index - 1,
                x=column_x,
                y=leaf_y,
                options=options,
                measurer=measurer,
                boxes=boxes,
                text_blocks=text_blocks,
                reading_order=reading_order,
            )
            operation_text_ids.extend(block_ids)
            if segment is not None:
                materials.append(segment)
            leaf_y += leaf.height
    for rule_index, rule_x in enumerate((x + consumed_width, x + consumed_width + produced_width)):
        boxes.append(
            LayoutBox(
                id=f"box:ledger:rule:column:{entry.operation_id}:{fragment_index + 1}:{rule_index}",
                kind="annotation",
                rect=Rect(x=rule_x, y=body_y, width=1, height=body_height),
                style_class="ledger-hairline",
                opaque=False,
                collision_group="rule",
                corner_radius=0,
            )
        )
    boxes.append(
        LayoutBox(
            id=f"box:ledger:rule:entry:{entry.operation_id}:{fragment_index + 1}",
            kind="annotation",
            rect=Rect(x=x, y=frame_rect.bottom, width=content_width, height=1),
            style_class="ledger-hairline",
            opaque=False,
            collision_group="rule",
            corner_radius=0,
        )
    )
    return frame_id, operation_text_ids, frame_rect.bottom


def _place_leaf(
    *,
    leaf: _Leaf,
    operation_id: str,
    lane: int,
    x: float,
    y: float,
    options: LayoutOptions,
    measurer: TextMeasurer,
    boxes: list[LayoutBox],
    text_blocks: list[TextBlock],
    reading_order: list[str],
) -> tuple[list[str], MaterialSegment | None]:
    box_id = f"box:ledger:{leaf.identifier}"
    rect = Rect(x=x, y=y, width=leaf.width, height=leaf.height)
    block_ids: list[str] = []
    for piece in leaf.pieces:
        block_id = f"text:ledger:{leaf.identifier}:{piece.suffix}"
        block = _place_measured_piece(
            block_id=block_id,
            parent_id=box_id,
            piece=piece,
            origin_x=x,
            origin_y=y,
            measurer=measurer,
            options=options,
        )
        text_blocks.append(block)
        block_ids.append(block.id)
        reading_order.append(block.id)
    boxes.append(
        LayoutBox(
            id=box_id,
            kind=leaf.box_kind,
            rect=rect,
            text_block_ids=tuple(block_ids),
            style_class=leaf.style_class,
            opaque=True,
            collision_group="ledger-leaf",
            corner_radius=0,
        )
    )
    segment = None
    if leaf.material_id and leaf.material_label and leaf.material_role:
        segment = MaterialSegment(
            material_id=leaf.material_id,
            label=leaf.material_label,
            quantity=leaf.material_quantity,
            role=leaf.material_role,
            lane=lane,
            x1=x,
            x2=x + leaf.width,
            y=y + leaf.height / 2,
            show_left_label=leaf.consumed,
            show_inline_label=not leaf.consumed,
            label_box_id=box_id,
        )
    return block_ids, segment


def _place_measured_piece(
    *,
    block_id: str,
    parent_id: str,
    piece: _MeasuredPiece,
    origin_x: float,
    origin_y: float,
    measurer: TextMeasurer,
    options: LayoutOptions,
) -> TextBlock:
    return place_text_block(
        identifier=block_id,
        role=piece.role,
        text=piece.text,
        rect=Rect(
            x=origin_x + piece.rect.x,
            y=origin_y + piece.rect.y,
            width=piece.rect.width,
            height=piece.rect.height,
        ),
        style=piece.style,
        measurer=measurer,
        horizontal_alignment=piece.alignment,
        vertical_alignment="middle",
        parent_id=parent_id,
        wrap_mode=options.wrap_mode,
    )


def _place_column_headings(
    *,
    y: float,
    suffix: str,
    content_x: float,
    consumed_width: float,
    produced_width: float,
    conditions_width: float,
    theme: LayoutTheme,
    options: LayoutOptions,
    measurer: TextMeasurer,
    boxes: list[LayoutBox],
    text_blocks: list[TextBlock],
    reading_order: list[str],
    include_in_reading_order: bool,
) -> float:
    height = _COLUMN_HEADING_HEIGHT
    box_id = f"box:ledger:band:columns:{suffix}"
    rect = Rect(
        x=content_x,
        y=y,
        width=consumed_width + produced_width + conditions_width,
        height=height,
    )
    labels = (
        ("consumed", "CONSUMED", content_x, consumed_width),
        ("produced", "PRODUCED", content_x + consumed_width, produced_width),
        (
            "conditions",
            "CONDITIONS",
            content_x + consumed_width + produced_width,
            conditions_width,
        ),
    )
    ids: list[str] = []
    for name, label, label_x, label_width in labels:
        block = place_text_block(
            identifier=f"text:ledger:band:columns:{suffix}:{name}",
            role="annotation",
            text=label,
            rect=Rect(x=label_x, y=y, width=label_width, height=height),
            style=theme.mono_style,
            measurer=measurer,
            padding=Insets(left=6, right=6),
            vertical_alignment="middle",
            parent_id=box_id,
            wrap_mode=options.wrap_mode,
        )
        text_blocks.append(block)
        ids.append(block.id)
        if include_in_reading_order:
            reading_order.append(block.id)
    boxes.append(
        LayoutBox(
            id=box_id,
            kind="annotation",
            rect=rect,
            text_block_ids=tuple(ids),
            style_class="ledger-band",
            opaque=True,
            collision_group="ledger-leaf",
            corner_radius=0,
        )
    )
    return height


def _place_setup_rows(
    *,
    view: _GraphView,
    setup_folios: dict[str, str],
    setup_references: dict[str, str],
    transform_folios: dict[str, int],
    content_x: float,
    content_width: float,
    start_y: float,
    theme: LayoutTheme,
    options: LayoutOptions,
    measurer: TextMeasurer,
    boxes: list[LayoutBox],
    text_blocks: list[TextBlock],
    reading_order: list[str],
) -> tuple[list[SetupCard], float]:
    cards: list[SetupCard] = []
    y = start_y
    required_by_map: dict[str, list[str]] = defaultdict(list)
    for target, sources in view.requires.items():
        for source in sources:
            setup_id = next(
                (
                    candidate
                    for candidate in view.setup_order
                    if source == candidate or source in view.produces.get(candidate, ())
                ),
                None,
            )
            if setup_id and target in transform_folios:
                required_by_map[setup_id].append(target)

    folio_width = 42.0
    label_width = min(300.0, content_width * 0.43)
    target_width = min(150.0, content_width * 0.22)
    detail_width = content_width - folio_width - label_width - target_width
    for row_index, operation_id in enumerate(view.setup_order):
        node = view.operations[operation_id]
        required_by = tuple(required_by_map.get(operation_id, ()))
        detail_parts = [
            value
            for value in (
                f"Time {_display_duration(node.duration)}" if node.duration else None,
                f"Temperature {node.temperature}" if node.temperature else None,
                (
                    "Required by entries "
                    + ", ".join(str(transform_folios[item]) for item in required_by)
                    if required_by
                    else None
                ),
            )
            if value
        ]
        setup_dependencies = [
            setup_references[item]
            for item in view.requires.get(operation_id, ())
            if item in setup_references
        ]
        if setup_dependencies:
            detail_parts.append(f"Requires {', '.join(setup_dependencies)}")
        if node.notes:
            detail_parts.extend(node.notes)
        detail_text = " · ".join(detail_parts) or "standing condition"
        label_text = node.label or node.action
        target_text = node.target or "—"
        heights = (
            _text_height(label_text, label_width - 8, theme.label_style, measurer, options),
            _text_height(target_text, target_width - 8, theme.detail_style, measurer, options),
            _text_height(detail_text, detail_width - 8, theme.detail_style, measurer, options),
        )
        row_height = max(24.0, max(heights) + 8)
        box_id = f"box:ledger:standing:{operation_id}"
        row_rect = Rect(x=content_x, y=y, width=content_width, height=row_height)
        column_specs = (
            (
                "label",
                "setup-label",
                setup_folios[operation_id],
                theme.mono_style,
                content_x,
                folio_width,
            ),
            (
                "action",
                "setup-label",
                label_text,
                theme.label_style,
                content_x + folio_width,
                label_width,
            ),
            (
                "target",
                "setup-target",
                target_text,
                theme.detail_style,
                content_x + folio_width + label_width,
                target_width,
            ),
            (
                "detail",
                "setup-detail",
                detail_text,
                theme.detail_style,
                content_x + folio_width + label_width + target_width,
                detail_width,
            ),
        )
        ids: list[str] = []
        for suffix, role, text, style, block_x, block_width in column_specs:
            block = place_text_block(
                identifier=f"text:ledger:standing:{operation_id}:{suffix}",
                role=role,  # type: ignore[arg-type]
                text=text,
                rect=Rect(x=block_x, y=y, width=block_width, height=row_height),
                style=style,
                measurer=measurer,
                padding=Insets(left=4, right=4),
                vertical_alignment="middle",
                parent_id=box_id,
                wrap_mode=options.wrap_mode,
            )
            text_blocks.append(block)
            ids.append(block.id)
            reading_order.append(block.id)
        boxes.append(
            LayoutBox(
                id=box_id,
                kind="setup",
                rect=row_rect,
                text_block_ids=tuple(ids),
                style_class="ledger-standing",
                opaque=True,
                collision_group="ledger-leaf",
                corner_radius=0,
            )
        )
        cards.append(
            SetupCard(
                operation_id=operation_id,
                label=label_text,
                detail=detail_text,
                x=content_x,
                width=content_width,
                y=y,
                height=row_height,
                rect=row_rect,
                text_block_ids=tuple(ids),
                required_by_operation_ids=required_by,
            )
        )
        y += row_height
        if row_index < len(view.setup_order) - 1:
            boxes.append(
                _rule("standing-row", row_index, content_x, y, content_width, "ledger-hairline")
            )
    return cards, y


def _place_frontier(
    *,
    view: _GraphView,
    folios: dict[str, str | None],
    completed_entries: int,
    sheet_number: int,
    y: float,
    height: float,
    content_x: float,
    content_width: float,
    theme: LayoutTheme,
    options: LayoutOptions,
    measurer: TextMeasurer,
    boxes: list[LayoutBox],
    text_blocks: list[TextBlock],
    reading_order: list[str],
) -> None:
    rank = {identifier: index for index, identifier in enumerate(view.transform_order)}
    open_materials: list[str] = []
    for material_id, producer in view.producer.items():
        producer_rank = rank.get(producer)
        if producer_rank is None or producer_rank >= completed_entries:
            continue
        consumer_ranks = [
            rank[item] for item in view.consumers.get(material_id, ()) if item in rank
        ]
        material = view.materials[material_id]
        needed_later = any(item >= completed_entries for item in consumer_ranks)
        held_open = material.role.value == "reserved" and (
            not consumer_ranks or any(item >= completed_entries for item in consumer_ranks)
        )
        if needed_later or held_open:
            folio = folios.get(material_id) or "—"
            open_materials.append(f"{folio} {material.label}")
    inventory = "; ".join(open_materials) if open_materials else "no open materials"
    text = f"OPEN AT THE FOOT OF SHEET {sheet_number} · {inventory} · CARRIED FORWARD"
    box_id = f"box:ledger:band:carried:{sheet_number}"
    rect = Rect(x=content_x, y=y, width=content_width, height=height)
    block = place_text_block(
        identifier=f"text:ledger:band:carried:{sheet_number}",
        role="annotation",
        text=text,
        rect=rect,
        style=theme.mono_style,
        measurer=measurer,
        padding=Insets(top=7, right=6, bottom=7, left=6),
        vertical_alignment="middle",
        parent_id=box_id,
        wrap_mode=options.wrap_mode,
    )
    text_blocks.append(block)
    reading_order.append(block.id)
    boxes.append(
        LayoutBox(
            id=box_id,
            kind="annotation",
            rect=rect,
            text_block_ids=(block.id,),
            style_class="ledger-band",
            opaque=True,
            collision_group="ledger-leaf",
            corner_radius=0,
        )
    )


def _fragment_entry(entry: _Entry, capacity: float) -> tuple[_EntryFragment, ...]:
    consumed = _chunks(entry.consumed, capacity)
    produced = _chunks(entry.produced, capacity)
    conditions = _chunks(entry.conditions, capacity)
    count = max(len(consumed), len(produced), len(conditions))
    return tuple(
        _EntryFragment(
            consumed[index] if index < len(consumed) else (),
            produced[index] if index < len(produced) else (),
            conditions[index] if index < len(conditions) else (),
        )
        for index in range(count)
    )


def _chunks(leaves: tuple[_Leaf, ...], capacity: float) -> tuple[tuple[_Leaf, ...], ...]:
    if not leaves:
        return ((),)
    chunks: list[list[_Leaf]] = [[]]
    used = 0.0
    for leaf in leaves:
        if chunks[-1] and used + leaf.height > capacity + 0.01:
            chunks.append([])
            used = 0.0
        chunks[-1].append(leaf)
        used += leaf.height
    return tuple(tuple(chunk) for chunk in chunks)


def _folio_map(view: _GraphView, graph: RecipeGraph) -> dict[str, str | None]:
    finals = {
        material_id: f"F{index}"
        for index, material_id in enumerate(graph.final_material_ids, start=1)
    }
    folios: dict[str, str | None] = {identifier: None for identifier in view.materials}
    for index, operation_id in enumerate(view.transform_order, start=1):
        outputs = [
            material_id
            for material_id in view.produces.get(operation_id, ())
            if material_id not in finals
        ]
        suffixes = len(outputs) > 1
        for output_index, material_id in enumerate(outputs):
            suffix = _alpha_suffix(output_index) if suffixes else ""
            folios[material_id] = f"M{index}{suffix}"
    folios.update(finals)
    return folios


def _alpha_suffix(index: int) -> str:
    output = ""
    value = index
    while True:
        output = chr(ord("a") + value % 26) + output
        value = value // 26 - 1
        if value < 0:
            return output


def _material_branch_markers(view: _GraphView) -> dict[str, str | None]:
    rank = {identifier: index for index, identifier in enumerate(view.transform_order)}
    operation_ancestry: dict[str, frozenset[str]] = {}
    source_ancestry: dict[str, frozenset[str]] = {}

    def material_operations(material_id: str, seen: frozenset[str] = frozenset()) -> frozenset[str]:
        producer = view.producer.get(material_id)
        if producer is None or producer in seen or producer not in rank:
            return frozenset()
        if producer in operation_ancestry:
            return operation_ancestry[producer]
        ancestry = {producer}
        for input_id in view.consumes.get(producer, ()):
            ancestry.update(material_operations(input_id, seen | {producer}))
        resolved = frozenset(ancestry)
        operation_ancestry[producer] = resolved
        return resolved

    def material_sources(material_id: str, seen: frozenset[str] = frozenset()) -> frozenset[str]:
        if material_id in source_ancestry:
            return source_ancestry[material_id]
        if material_id in seen:
            return frozenset()
        producer = view.producer.get(material_id)
        if producer is None or producer not in rank:
            resolved = frozenset({material_id})
        else:
            values: set[str] = set()
            for input_id in view.consumes.get(producer, ()):
                values.update(material_sources(input_id, seen | {material_id}))
            resolved = frozenset(values)
        source_ancestry[material_id] = resolved
        return resolved

    markers: dict[str, str | None] = {}
    previous_sources: set[str] = set()
    for operation_id in view.transform_order:
        inputs = view.consumes.get(operation_id, ())
        produced_inputs = [item for item in inputs if view.producer.get(item) in rank]
        branches = [material_operations(item) for item in produced_inputs]
        components: list[set[str]] = []
        for branch in branches:
            touching = [component for component in components if component.intersection(branch)]
            if not touching:
                components.append(set(branch))
            else:
                merged = set(branch)
                for component in touching:
                    merged.update(component)
                    components.remove(component)
                components.append(merged)
        if len(components) >= 2:
            markers[operation_id] = f"JOIN · {len(components)} MATERIAL BRANCHES"
        else:
            current_sources: set[str] = set()
            for material_id in inputs:
                current_sources.update(material_sources(material_id))
            starts_branch = (
                bool(previous_sources)
                and not produced_inputs
                and bool(current_sources)
                and current_sources.isdisjoint(previous_sources)
            )
            markers[operation_id] = "SEPARATE MATERIAL BRANCH" if starts_branch else None
        for output_id in view.produces.get(operation_id, ()):
            previous_sources.update(material_sources(output_id))
    return markers


def _setup_reference_maps(view: _GraphView) -> tuple[dict[str, str], dict[str, str]]:
    setup_folios = {
        operation_id: f"S{index}" for index, operation_id in enumerate(view.setup_order, start=1)
    }
    references: dict[str, str] = {}
    for operation_id, folio in setup_folios.items():
        references[operation_id] = folio
        for material_id in view.produces.get(operation_id, ()):
            references[material_id] = folio
    return setup_folios, references


def _predecessors(graph: RecipeGraph) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        if edge.kind.value == "precedes":
            values[edge.target].append(edge.source)
    return {key: tuple(value) for key, value in values.items()}


def _balance(view: _GraphView, operation_id: str) -> str | None:
    node = view.operations[operation_id]
    if node.operation_type != "split":
        return None
    inputs = view.consumes.get(operation_id, ())
    outputs = view.produces.get(operation_id, ())
    if len(inputs) != 1 or len(outputs) < 2:
        return None
    allocations = dict(view.input_quantities.get(operation_id, ()))
    input_text = allocations.get(inputs[0]) or view.materials[inputs[0]].quantity
    output_texts = [view.materials[item].quantity for item in outputs]
    if input_text is None or any(item is None for item in output_texts):
        return None
    parsed_input = _parse_quantity(input_text)
    parsed_outputs = [_parse_quantity(item or "") for item in output_texts]
    if parsed_input is None or any(item is None for item in parsed_outputs):
        return None
    input_value, input_unit = parsed_input
    resolved_outputs = [item for item in parsed_outputs if item is not None]
    if any(unit != input_unit for _, unit in resolved_outputs):
        return None
    if sum(value for value, _ in resolved_outputs) != input_value:
        return None
    return f"{input_text} = {' + '.join(item or '' for item in output_texts)}"


_QUANTITY_PATTERN = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*(.*?)\s*$")


def _parse_quantity(value: str) -> tuple[Decimal, str] | None:
    match = _QUANTITY_PATTERN.fullmatch(value)
    if match is None:
        return None
    try:
        number = Decimal(match.group(1))
    except InvalidOperation:
        return None
    return number, match.group(2)


def _display_duration(value: str) -> str:
    return re.sub(r"(?<=\d)\.\.(?=\d)", " to ", value)


def _allocation_diagnostics(view: _GraphView) -> tuple[Diagnostic, ...]:
    allocated = {
        (operation_id, material_id)
        for operation_id, quantities in view.input_quantities.items()
        for material_id, _ in quantities
    }
    diagnostics: list[Diagnostic] = []
    for material_id, consumers in view.consumers.items():
        if len(consumers) <= 1:
            continue
        for operation_id in consumers:
            if (operation_id, material_id) not in allocated:
                diagnostics.append(
                    Diagnostic(
                        code="RF506",
                        severity=Severity.ERROR,
                        path=f"/operations/{operation_id}/inputs/{material_id}",
                        message=(
                            f"Partial draw of '{material_id}' has no allocation quantity "
                            "to print alongside its authored total."
                        ),
                        suggestions=("Author an exact quantity on every partial input edge.",),
                    )
                )
    return tuple(diagnostics)


def _held_diagnostics(
    view: _GraphView,
    output_kinds: dict[tuple[str, str], str],
) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    for material_id, material in view.materials.items():
        producer = view.producer.get(material_id)
        held = material.role.value == "reserved" or (
            producer is not None and output_kinds.get((producer, material_id)) == "reserves"
        )
        if held and not view.consumers.get(material_id):
            diagnostics.append(
                Diagnostic(
                    code="RF507",
                    severity=Severity.WARNING,
                    path=f"/materials/{material_id}",
                    message=f"Held output '{material_id}' remains unconsumed.",
                    suggestions=("Consume the held portion or document its intended disposition.",),
                )
            )
    return tuple(diagnostics)


def _pagination_diagnostic(operation_id: str, detail: str) -> Diagnostic:
    return Diagnostic(
        code="RF508",
        severity=Severity.ERROR,
        path=f"/operations/{operation_id}",
        message=f"Safe ledger pagination is impossible. {detail}",
        suggestions=(
            "Increase the page size, reduce the safe margin, or shorten the semantic leaf.",
        ),
    )


def _visible_quantity(material: MaterialNode, options: LayoutOptions) -> str | None:
    if options.show_source_quantities and material.quantity:
        return material.quantity
    if options.show_normalized_quantities:
        return _normalized_quantity_text(material)
    return None


def _stack_pieces(
    specs: list[tuple[str, TextRole, str, TextStyle]],
    *,
    x: float,
    width: float,
    measurer: TextMeasurer,
    options: LayoutOptions,
) -> tuple[tuple[_MeasuredPiece, ...], float]:
    pieces: list[_MeasuredPiece] = []
    y = 0.0
    for index, (suffix, role, text, style) in enumerate(specs):
        if index:
            y += 2
        height = _text_height(text, width, style, measurer, options)
        pieces.append(
            _MeasuredPiece(
                suffix=suffix,
                role=role,
                text=text,
                style=style,
                rect=Rect(x=x, y=y, width=width, height=height),
            )
        )
        y += height
    return tuple(pieces), y


def _text_height(
    text: str,
    width: float,
    style: TextStyle,
    measurer: TextMeasurer,
    options: LayoutOptions,
) -> float:
    return wrap_text(
        text,
        max(1.0, width),
        style,
        measurer,
        options.wrap_mode,
    ).height


def _ledger_label_style(theme: LayoutTheme, options: LayoutOptions) -> TextStyle:
    font_size = max(options.minimum_font_size, theme.label_style.font_size * 0.9)
    return theme.label_style.model_copy(
        update={
            "font_size": font_size,
            "line_height": font_size * options.line_height,
        }
    )


def _rule(
    band: str,
    ordinal: int,
    x: float,
    y: float,
    width: float,
    style_class: str = "ledger-rule",
) -> LayoutBox:
    return LayoutBox(
        id=f"box:ledger:rule:{band}:{ordinal}",
        kind="annotation",
        rect=Rect(x=x, y=y, width=width, height=1),
        style_class=style_class,
        opaque=False,
        collision_group="rule",
        corner_radius=0,
    )


def _rounded(value: float) -> float:
    return round(value, 3)


def _merge_diagnostics(
    first: tuple[Diagnostic, ...],
    second: tuple[Diagnostic, ...],
) -> tuple[Diagnostic, ...]:
    output: list[Diagnostic] = []
    seen: set[tuple[str, str, str]] = set()
    for diagnostic in (*first, *second):
        key = (diagnostic.code, diagnostic.path, diagnostic.message)
        if key not in seen:
            seen.add(key)
            output.append(diagnostic)
    return tuple(output)
