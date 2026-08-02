from __future__ import annotations

import heapq
import re
from collections import defaultdict
from typing import Literal

from recipeflow.graph_index import GraphIndex
from recipeflow.layout import create_tabular_layout, validate_tabular_layout
from recipeflow.models import RecipeGraph, RenderArtifact, ValidationResult
from recipeflow.models.common import Ambiguity
from recipeflow.models.graph import EdgeKind, MaterialNode, OperationNode
from recipeflow.renderers import (
    RenderOptions,
    render_tabular_html,
    render_tabular_png,
    render_tabular_svg,
)

type RenderFormat = Literal[
    "text",
    "mermaid",
    "json",
    "canonical-json",
    "tabular-layout",
    "tabular-svg",
    "tabular-html",
    "tabular-png",
]


def render(
    graph: RecipeGraph,
    format: RenderFormat = "text",
    options: RenderOptions | None = None,
) -> RenderArtifact:
    """Render a canonical graph without filesystem access."""

    selected = options or RenderOptions()
    if format in {"json", "canonical-json"}:
        content = graph.model_dump_json(indent=2, by_alias=True) + "\n"
        return RenderArtifact(
            format="canonical-json",
            media_type="application/json",
            content=content,
        )

    if format in {
        "tabular-layout",
        "tabular-svg",
        "tabular-html",
        "tabular-png",
    }:
        layout = create_tabular_layout(graph, selected.to_layout_options())
        if format == "tabular-layout":
            return RenderArtifact(
                format=format,
                media_type="application/json",
                content=layout.model_dump_json(indent=2, by_alias=True) + "\n",
                width=round(layout.width),
                height=round(layout.height),
            )
        if format == "tabular-svg":
            return RenderArtifact(
                format=format,
                media_type="image/svg+xml",
                content=render_tabular_svg(layout, selected),
                width=round(layout.width),
                height=round(layout.height),
            )
        if format == "tabular-html":
            return RenderArtifact(
                format=format,
                media_type="text/html",
                content=render_tabular_html(layout, selected),
                width=round(layout.width),
                height=round(layout.height),
            )
        output_width, output_height = selected.raster_dimensions(
            layout.width,
            layout.height,
        )
        return RenderArtifact(
            format=format,
            media_type="image/png",
            content=render_tabular_png(layout, selected),
            width=output_width,
            height=output_height,
        )

    if format == "mermaid":
        return RenderArtifact(
            format=format,
            media_type="text/vnd.mermaid",
            content=_render_mermaid(graph),
        )
    if format == "text":
        return RenderArtifact(
            format=format,
            media_type="text/plain",
            content=_render_text(graph),
        )
    raise ValueError(f"Unsupported render format: {format}")


def render_check(
    graph: RecipeGraph,
    options: RenderOptions | None = None,
) -> ValidationResult:
    """Validate the complete resolved layout and return RF5xx diagnostics."""

    selected = options or RenderOptions()
    layout = create_tabular_layout(graph, selected.to_layout_options())
    generic = validate_tabular_layout(layout)
    diagnostics = tuple(
        {
            (item.code, item.path, item.message): item
            for item in (*layout.diagnostics, *generic)
        }.values()
    )
    return ValidationResult(diagnostics=diagnostics)


def _render_mermaid(graph: RecipeGraph) -> str:
    lines = ["flowchart LR"]
    for node in graph.nodes:
        label = node.label.replace('"', "'")
        if isinstance(node, MaterialNode):
            lines.append(f'  {_safe(node.id)}["{label}"]')
        else:
            lines.append(f'  {_safe(node.id)}{{"{label}"}}')
    for edge in graph.edges:
        style = "-.->" if edge.kind in {EdgeKind.REQUIRES, EdgeKind.PRECEDES} else "-->"
        lines.append(
            f"  {_safe(edge.source)} {style}|{edge.kind.value}| {_safe(edge.target)}"
        )
    return "\n".join(lines) + "\n"


def _render_text(graph: RecipeGraph) -> str:
    lines = [graph.title, "=" * len(graph.title)]
    if graph.description:
        lines.extend(["", graph.description])
    if graph.yield_text:
        lines.append(f"Yield: {graph.yield_text}")
    if graph.source:
        source_parts = [
            value
            for value in (graph.source.author, graph.source.title, graph.source.url)
            if value
        ]
        if source_parts:
            lines.append(f"Source: {' · '.join(dict.fromkeys(source_parts))}")
    if graph.tags:
        lines.append(f"Tags: {', '.join(graph.tags)}")
    for note in graph.notes:
        lines.append(f"Note: {note}")
    if graph.source:
        for note in graph.source.notes:
            lines.append(f"Source note: {note}")
    _append_ambiguities(lines, graph.ambiguity, indent="")

    index = GraphIndex(graph)
    operation_order = _text_operation_order(index)
    transform_ids = tuple(
        operation_id
        for operation_id in operation_order
        if index.operations[operation_id].operation_kind == "transform"
    )
    step_numbers = {
        operation_id: step
        for step, operation_id in enumerate(transform_ids, start=1)
    }

    ingredients = sorted(
        (
            node
            for node in graph.nodes
            if isinstance(node, MaterialNode)
            and (node.source_path or "").startswith("/ingredients/")
        ),
        key=lambda node: node.label.casefold(),
    )
    if ingredients:
        lines.extend(["", "Ingredients", "-----------"])
        for ingredient in ingredients:
            lines.append(f"- {_material_text(ingredient)}")
            _append_material_context(lines, ingredient, indent="  ")

    setup_ids = tuple(
        operation_id
        for operation_id in operation_order
        if index.operations[operation_id].operation_kind == "setup"
    )
    setup_numbers = {
        operation_id: number
        for number, operation_id in enumerate(setup_ids, start=1)
    }
    if setup_ids:
        lines.extend(["", "Standing conditions", "-------------------"])
        for operation_id in setup_ids:
            node = index.operations[operation_id]
            optional = " [optional]" if node.optional else ""
            lines.append(f"{setup_numbers[operation_id]}. {node.action}{optional}")
            _append_operation_conditions(lines, node)
            required_by = []
            for edge in index.outgoing.get(operation_id, ()):
                if edge.kind != EdgeKind.REQUIRES or edge.target not in index.operations:
                    continue
                target = index.operations[edge.target]
                if target.operation_kind == "transform":
                    required_by.append(f"step {step_numbers[edge.target]}")
                else:
                    required_by.append(
                        f"standing condition {setup_numbers[edge.target]}"
                    )
            if required_by:
                lines.append(f"   Required by: {', '.join(required_by)}")
            _append_operation_context(lines, node)

    lines.extend(["", "Method", "------"])
    for operation_id in transform_ids:
        node = index.operations[operation_id]
        optional = " [optional]" if node.optional else ""
        lines.append(f"{step_numbers[operation_id]}. {node.action}{optional}")

        inputs = []
        for edge in index.incoming.get(operation_id, ()):
            if edge.kind not in {
                EdgeKind.CONSUMES,
                EdgeKind.RESERVES,
                EdgeKind.OPTIONALLY_APPLIES,
            } or edge.source not in index.materials:
                continue
            material = index.materials[edge.source]
            quantity = edge.quantity or material.quantity
            qualifiers = []
            if edge.kind == EdgeKind.OPTIONALLY_APPLIES or material.optional:
                qualifiers.append("optional")
            if edge.kind == EdgeKind.RESERVES:
                qualifiers.append("reserve")
            inputs.append(
                _material_text(material, quantity=quantity, qualifiers=qualifiers)
            )
        if inputs:
            lines.append(f"   Uses: {'; '.join(inputs)}")

        outputs = []
        for edge in index.outgoing.get(operation_id, ()):
            if edge.kind not in {
                EdgeKind.PRODUCES,
                EdgeKind.DISCARDS,
                EdgeKind.RESERVES,
            } or edge.target not in index.materials:
                continue
            material = index.materials[edge.target]
            qualifiers = []
            if material.role.value != "intermediate":
                qualifiers.append(material.role.value)
            if material.optional:
                qualifiers.append("optional")
            outputs.append(
                _material_text(
                    material,
                    quantity=edge.quantity or material.quantity,
                    qualifiers=qualifiers,
                )
            )
        if outputs:
            lines.append(f"   Makes: {'; '.join(outputs)}")
        _append_operation_conditions(lines, node)
        _append_operation_context(lines, node)

    finals = [index.materials[item] for item in graph.final_material_ids]
    if finals:
        lines.extend(
            ["", f"Final: {'; '.join(_material_text(item) for item in finals)}"]
        )
    return "\n".join(lines) + "\n"


def _text_operation_order(index: GraphIndex) -> tuple[str, ...]:
    """Topologically order operations, using authored order for valid peers."""

    dependencies = index.operation_dependencies()
    successors: dict[str, set[str]] = defaultdict(set)
    indegree = {
        operation_id: len(prerequisites)
        for operation_id, prerequisites in dependencies.items()
    }
    for operation_id, prerequisites in dependencies.items():
        for prerequisite in prerequisites:
            successors[prerequisite].add(operation_id)

    ready = [
        (_operation_source_key(index.operations[operation_id]), operation_id)
        for operation_id, degree in indegree.items()
        if degree == 0
    ]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        _, operation_id = heapq.heappop(ready)
        ordered.append(operation_id)
        for successor in successors[operation_id]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(
                    ready,
                    (_operation_source_key(index.operations[successor]), successor),
                )
    if len(ordered) != len(index.operations):
        return index.topological_operation_ids()
    return tuple(ordered)


def _operation_source_key(node: OperationNode) -> tuple[int, int, str]:
    source_path = node.source_path or ""
    prefix = "/setup/" if node.operation_kind == "setup" else "/operations/"
    try:
        source_index = int(source_path.removeprefix(prefix).split("/", 1)[0])
    except ValueError:
        source_index = 10**9
    return (0 if node.operation_kind == "setup" else 1, source_index, node.id)


def _material_text(
    material: MaterialNode,
    *,
    quantity: str | None = None,
    qualifiers: list[str] | None = None,
) -> str:
    quantity = quantity if quantity is not None else material.quantity
    prefix = (
        f"{quantity} "
        if quantity and not _label_includes_quantity(material.label, quantity)
        else ""
    )
    all_qualifiers = list(dict.fromkeys(qualifiers or ()))
    if material.optional and "optional" not in all_qualifiers:
        all_qualifiers.append("optional")
    suffix = f" [{', '.join(all_qualifiers)}]" if all_qualifiers else ""
    return f"{prefix}{material.label}{suffix}"


_COUNT_WORDS = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
    20: "twenty",
    30: "thirty",
    40: "forty",
    50: "fifty",
    60: "sixty",
    70: "seventy",
    80: "eighty",
    90: "ninety",
    100: "one hundred",
}


def _label_includes_quantity(label: str, quantity: str) -> bool:
    normalized_label = label.strip().casefold()
    normalized_quantity = quantity.strip().casefold()
    if normalized_label.startswith(f"{normalized_quantity} "):
        return True
    match = re.match(r"^(\d+)\b", normalized_quantity)
    if not match:
        return False
    count_word = _COUNT_WORDS.get(int(match.group(1)))
    return bool(count_word and normalized_label.startswith(f"{count_word} "))


def _append_material_context(
    lines: list[str],
    material: MaterialNode,
    *,
    indent: str,
) -> None:
    states = [
        value
        for value in (material.preparation_state, material.temperature_state)
        if value
    ]
    if states:
        lines.append(f"{indent}State: {', '.join(states)}")
    if material.source_text and material.source_text not in {
        material.label,
        material.quantity,
    }:
        lines.append(f"{indent}Source wording: {material.source_text}")
    for annotation in material.annotations:
        lines.append(f"{indent}Note: {annotation}")
    _append_ambiguities(lines, material.ambiguity, indent=indent)


def _append_operation_conditions(lines: list[str], node: OperationNode) -> None:
    if node.duration:
        lines.append(f"   Time: {node.duration}")
    if node.temperature:
        lines.append(f"   Temperature: {node.temperature}")
    if node.until:
        lines.append(f"   Until: {node.until}")
    if node.repeat:
        repeat_parts = []
        if node.repeat.count is not None:
            repeat_parts.append(f"{node.repeat.count} times")
        if node.repeat.interval is not None:
            interval = getattr(node.repeat.interval, "source_text", node.repeat.interval)
            repeat_parts.append(f"every {interval}")
        if node.repeat.until:
            repeat_parts.append(f"until {node.repeat.until}")
        if repeat_parts:
            lines.append(f"   Repeat: {', '.join(str(item) for item in repeat_parts)}")


def _append_operation_context(lines: list[str], node: OperationNode) -> None:
    if node.target:
        lines.append(f"   Target: {node.target}")
    if node.equipment:
        lines.append(f"   Equipment: {', '.join(node.equipment)}")
    if node.resources:
        resources = [
            f"{item.quantity} x {item.label or item.id}"
            for item in node.resources
        ]
        lines.append(f"   Resources: {', '.join(resources)}")
    for note in node.notes:
        lines.append(f"   Note: {note}")
    _append_ambiguities(lines, node.ambiguity, indent="   ")


def _append_ambiguities(
    lines: list[str],
    ambiguities: tuple[Ambiguity, ...],
    *,
    indent: str,
) -> None:
    for ambiguity in ambiguities:
        detail = ambiguity.description
        if ambiguity.alternatives:
            detail += f" Alternatives: {'; '.join(ambiguity.alternatives)}."
        if ambiguity.resolution:
            detail += f" Resolution: {ambiguity.resolution}."
        lines.append(f"{indent}Ambiguity: {detail}")


def _safe(value: str) -> str:
    return "n_" + "".join(
        character if character.isalnum() else "_" for character in value
    )
