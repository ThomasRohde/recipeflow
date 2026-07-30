from typing import Literal

from recipeflow.models import RecipeGraph, RenderArtifact
from recipeflow.models.graph import MaterialNode, OperationNode
from recipeflow.layout import create_tabular_layout
from recipeflow.tabular_svg import render_tabular_html, render_tabular_svg


def render(
    graph: RecipeGraph,
    format: Literal["text", "mermaid", "json", "tabular-svg", "tabular-html", "tabular-layout"] = "text",
) -> RenderArtifact:
    if format == "json":
        return RenderArtifact(
            format="json",
            media_type="application/json",
            content=graph.model_dump_json(indent=2),
        )

    if format in {"tabular-svg", "tabular-html", "tabular-layout"}:
        layout = create_tabular_layout(graph)
        if format == "tabular-svg":
            return RenderArtifact(format=format, media_type="image/svg+xml", content=render_tabular_svg(layout))
        if format == "tabular-html":
            return RenderArtifact(format=format, media_type="text/html", content=render_tabular_html(layout))
        return RenderArtifact(format=format, media_type="application/json", content=layout.model_dump_json(indent=2))

    if format == "mermaid":
        lines = ["flowchart LR"]
        for node in graph.nodes:
            label = node.label.replace('"', "'")
            if isinstance(node, MaterialNode):
                lines.append(f'  {safe(node.id)}["{label}"]')
            else:
                lines.append(f'  {safe(node.id)}{{"{label}"}}')
        for edge in graph.edges:
            style = "-.->" if edge.kind == "requires" else "-->"
            lines.append(
                f"  {safe(edge.source)} {style}|{edge.kind}| {safe(edge.target)}"
            )
        return RenderArtifact(
            format="mermaid",
            media_type="text/vnd.mermaid",
            content="\n".join(lines) + "\n",
        )

    incoming: dict[str, list[str]] = {}
    for edge in graph.edges:
        incoming.setdefault(edge.target, []).append(edge.source)

    lines = [graph.title, "=" * len(graph.title)]
    for node in graph.nodes:
        if isinstance(node, OperationNode) and node.operation_kind == "transform":
            inputs = ", ".join(incoming.get(node.id, [])) or "∅"
            outputs = ", ".join(
                edge.target
                for edge in graph.edges
                if edge.source == node.id and edge.kind == "produces"
            )
            lines.append(f"{inputs} → {node.action} → {outputs}")

    return RenderArtifact(
        format="text",
        media_type="text/plain",
        content="\n".join(lines) + "\n",
    )


def safe(value: str) -> str:
    return "n_" + "".join(character if character.isalnum() else "_" for character in value)
