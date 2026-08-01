from __future__ import annotations

from typing import Literal

from recipeflow.layout import create_tabular_layout, validate_tabular_layout
from recipeflow.models import RecipeGraph, RenderArtifact, ValidationResult
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
    incoming: dict[str, list[str]] = {}
    outgoing: dict[str, list[str]] = {}
    for edge in graph.edges:
        if edge.kind in {
            EdgeKind.CONSUMES,
            EdgeKind.RESERVES,
            EdgeKind.OPTIONALLY_APPLIES,
        }:
            incoming.setdefault(edge.target, []).append(edge.source)
        if edge.kind in {EdgeKind.PRODUCES, EdgeKind.DISCARDS, EdgeKind.RESERVES}:
            outgoing.setdefault(edge.source, []).append(edge.target)

    lines = [graph.title, "=" * len(graph.title)]
    for node in graph.nodes:
        if isinstance(node, OperationNode) and node.operation_kind == "transform":
            inputs = ", ".join(sorted(incoming.get(node.id, []))) or "∅"
            outputs = ", ".join(sorted(outgoing.get(node.id, []))) or "∅"
            details = " · ".join(
                value for value in (node.temperature, node.duration, node.until) if value
            )
            suffix = f" ({details})" if details else ""
            lines.append(f"{inputs} → {node.action}{suffix} → {outputs}")
    return "\n".join(lines) + "\n"


def _safe(value: str) -> str:
    return "n_" + "".join(
        character if character.isalnum() else "_" for character in value
    )
