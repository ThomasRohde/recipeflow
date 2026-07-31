from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Literal

import yaml

from recipeflow.compilation import compile_document
from recipeflow.models.common import (
    DOCUMENT_SCHEMA_VERSION,
    Diagnostic,
    Severity,
)
from recipeflow.models.document import RecipeDocument
from recipeflow.models.graph import EdgeKind, MaterialNode, OperationNode, RecipeGraph
from recipeflow.models.results import (
    DiffChange,
    DiffResult,
    FormatResult,
    MigrationResult,
    MigrationStep,
)
from recipeflow.parsing import SourceFormat, parse_document

OutputFormat = Literal["yaml", "json"]
DocumentInput = str | Mapping[str, Any] | RecipeDocument
DiffInput = DocumentInput | RecipeGraph


def _sort_document(document: RecipeDocument) -> dict[str, Any]:
    data = document.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
        exclude_defaults=True,
    )
    data["schema_version"] = DOCUMENT_SCHEMA_VERSION
    data["ingredients"] = {
        key: data["ingredients"][key]
        for key in sorted(data["ingredients"])
    }
    data["setup"] = sorted(
        data.get("setup", []),
        key=lambda item: (
            item.get("id") or "",
            item.get("action") or "",
            item.get("produces") or "",
        ),
    )
    operations = []
    for operation in data["operations"]:
        operation["outputs"] = {
            key: operation["outputs"][key]
            for key in sorted(operation["outputs"])
        }
        operations.append(operation)
    data["operations"] = sorted(
        operations,
        key=lambda item: (
            item.get("id") or "",
            item.get("action") or "",
            ",".join(item["outputs"]),
        ),
    )
    data["subrecipes"] = {
        key: data["subrecipes"][key]
        for key in sorted(data.get("subrecipes", {}))
    }
    ordered_keys = (
        "schema_version",
        "recipeflow",
        "recipe",
        "ingredients",
        "setup",
        "operations",
        "subrecipes",
    )
    return {
        key: data[key]
        for key in ordered_keys
        if key in data
    }


def _serialize(data: Mapping[str, Any], output_format: OutputFormat) -> str:
    if output_format == "json":
        return json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    return yaml.safe_dump(
        dict(data),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )


def format_document(
    source: DocumentInput,
    *,
    source_format: SourceFormat = "yaml",
    output_format: OutputFormat = "yaml",
) -> FormatResult:
    parsed = parse_document(source, source_format)
    if parsed.document is None:
        return FormatResult(
            format=output_format,
            diagnostics=parsed.diagnostics,
        )
    data = _sort_document(parsed.document)
    return FormatResult(
        document=parsed.document,
        content=_serialize(data, output_format),
        format=output_format,
        diagnostics=parsed.diagnostics,
    )


def migrate(
    source: DocumentInput,
    *,
    target_version: str = DOCUMENT_SCHEMA_VERSION,
    source_format: SourceFormat = "yaml",
    output_format: OutputFormat = "yaml",
    dry_run: bool = False,
) -> MigrationResult:
    if target_version != DOCUMENT_SCHEMA_VERSION:
        return MigrationResult(
            dry_run=dry_run,
            diagnostics=(
                Diagnostic(
                    code="RF601",
                    severity=Severity.ERROR,
                    path="/schema_version",
                    message=f"Unsupported migration target {target_version!r}.",
                    suggestions=(DOCUMENT_SCHEMA_VERSION,),
                ),
            ),
        )
    parsed = parse_document(source, source_format)
    if parsed.document is None:
        return MigrationResult(
            dry_run=dry_run,
            diagnostics=parsed.diagnostics,
        )

    changed = parsed.source_version != DOCUMENT_SCHEMA_VERSION
    data = _sort_document(parsed.document)
    data["schema_version"] = DOCUMENT_SCHEMA_VERSION
    if changed:
        data.pop("recipeflow", None)
    steps: tuple[MigrationStep, ...] = ()
    diagnostics = parsed.diagnostics
    if changed:
        steps = (
            MigrationStep(
                source_version=parsed.source_version or "unknown",
                target_version=DOCUMENT_SCHEMA_VERSION,
                description=(
                    "Normalize the legacy numeric version marker to the "
                    "namespaced RecipeFlow document contract."
                ),
            ),
        )
        diagnostics = (
            *diagnostics,
            Diagnostic(
                code="RF610",
                severity=Severity.INFO,
                path="/schema_version",
                message=(
                    f"Migrated {parsed.source_version!r} to "
                    f"{DOCUMENT_SCHEMA_VERSION!r}."
                ),
            ),
        )
    return MigrationResult(
        document=parsed.document,
        content=_serialize(data, output_format),
        changed=changed,
        dry_run=dry_run,
        steps=steps,
        diagnostics=diagnostics,
    )


def _as_graph(
    value: DiffInput,
    source_format: SourceFormat,
) -> tuple[RecipeGraph | None, tuple[Diagnostic, ...]]:
    if isinstance(value, RecipeGraph):
        return value, ()
    parsed = parse_document(value, source_format)
    if parsed.document is None:
        return None, parsed.diagnostics
    compiled = compile_document(parsed.document)
    return compiled.graph, (*parsed.diagnostics, *compiled.diagnostics)


def _material_map(graph: RecipeGraph) -> dict[str, MaterialNode]:
    return {
        node.id: node
        for node in graph.nodes
        if isinstance(node, MaterialNode)
    }


def _operation_map(graph: RecipeGraph) -> dict[str, OperationNode]:
    return {
        node.id: node
        for node in graph.nodes
        if isinstance(node, OperationNode)
    }


def semantic_diff(
    before: DiffInput,
    after: DiffInput,
    *,
    source_format: SourceFormat = "yaml",
) -> DiffResult:
    before_graph, before_diagnostics = _as_graph(before, source_format)
    after_graph, after_diagnostics = _as_graph(after, source_format)
    diagnostics = (*before_diagnostics, *after_diagnostics)
    if before_graph is None or after_graph is None:
        return DiffResult(diagnostics=diagnostics)

    changes: list[DiffChange] = []
    before_materials = _material_map(before_graph)
    after_materials = _material_map(after_graph)
    for material_id in sorted(before_materials.keys() - after_materials.keys()):
        material = before_materials[material_id]
        changes.append(
            DiffChange(
                kind="ingredient-removed"
                if material.role.value == "ingredient"
                else "material-removed",
                path=f"/materials/{material_id}",
                before=material.model_dump(mode="json"),
            )
        )
    for material_id in sorted(after_materials.keys() - before_materials.keys()):
        material = after_materials[material_id]
        changes.append(
            DiffChange(
                kind="ingredient-added"
                if material.role.value == "ingredient"
                else "material-added",
                path=f"/materials/{material_id}",
                after=material.model_dump(mode="json"),
            )
        )
    for material_id in sorted(before_materials.keys() & after_materials.keys()):
        old_material = before_materials[material_id]
        new_material = after_materials[material_id]
        if (old_material.quantity, old_material.unit) != (
            new_material.quantity,
            new_material.unit,
        ):
            changes.append(
                DiffChange(
                    kind="quantity-changed",
                    path=f"/materials/{material_id}/quantity",
                    before={
                        "quantity": old_material.quantity,
                        "unit": old_material.unit,
                    },
                    after={
                        "quantity": new_material.quantity,
                        "unit": new_material.unit,
                    },
                )
            )
        if old_material.label != new_material.label:
            changes.append(
                DiffChange(
                    kind="intermediate-renamed"
                    if old_material.role.value != "ingredient"
                    else "ingredient-renamed",
                    path=f"/materials/{material_id}/label",
                    before=old_material.label,
                    after=new_material.label,
                )
            )
        if old_material.role != new_material.role:
            changes.append(
                DiffChange(
                    kind="material-role-changed",
                    path=f"/materials/{material_id}/role",
                    before=old_material.role.value,
                    after=new_material.role.value,
                )
            )

    before_operations = _operation_map(before_graph)
    after_operations = _operation_map(after_graph)
    for operation_id in sorted(before_operations.keys() - after_operations.keys()):
        changes.append(
            DiffChange(
                kind="operation-removed",
                path=f"/operations/{operation_id}",
                before=before_operations[operation_id].model_dump(mode="json"),
            )
        )
    for operation_id in sorted(after_operations.keys() - before_operations.keys()):
        changes.append(
            DiffChange(
                kind="operation-added",
                path=f"/operations/{operation_id}",
                after=after_operations[operation_id].model_dump(mode="json"),
            )
        )
    for operation_id in sorted(
        before_operations.keys() & after_operations.keys()
    ):
        old_operation = before_operations[operation_id]
        new_operation = after_operations[operation_id]
        if old_operation.model_dump(mode="json") != new_operation.model_dump(
            mode="json"
        ):
            changes.append(
                DiffChange(
                    kind="operation-changed",
                    path=f"/operations/{operation_id}",
                    before=old_operation.model_dump(mode="json"),
                    after=new_operation.model_dump(mode="json"),
                )
            )

    if set(before_graph.final_material_ids) != set(after_graph.final_material_ids):
        changes.append(
            DiffChange(
                kind="final-output-changed",
                path="/final_material_ids",
                before=sorted(before_graph.final_material_ids),
                after=sorted(after_graph.final_material_ids),
            )
        )

    def edge_key(graph: RecipeGraph) -> set[tuple[str, str, str, str | None]]:
        return {
            (edge.kind.value, edge.source, edge.target, edge.quantity)
            for edge in graph.edges
        }

    old_edges = edge_key(before_graph)
    new_edges = edge_key(after_graph)
    for edge in sorted(old_edges - new_edges):
        kind = (
            "reservation-altered"
            if edge[0] == EdgeKind.RESERVES.value
            else "setup-requirement-changed"
            if edge[0] == EdgeKind.REQUIRES.value
            else "dependency-changed"
        )
        changes.append(
            DiffChange(
                kind=kind,
                path="/edges",
                before={
                    "kind": edge[0],
                    "source": edge[1],
                    "target": edge[2],
                    "quantity": edge[3],
                },
            )
        )
    for edge in sorted(new_edges - old_edges):
        kind = (
            "reservation-altered"
            if edge[0] == EdgeKind.RESERVES.value
            else "setup-requirement-changed"
            if edge[0] == EdgeKind.REQUIRES.value
            else "dependency-changed"
        )
        changes.append(
            DiffChange(
                kind=kind,
                path="/edges",
                after={
                    "kind": edge[0],
                    "source": edge[1],
                    "target": edge[2],
                    "quantity": edge[3],
                },
            )
        )
    changes.sort(key=lambda item: (item.kind, item.path))
    return DiffResult(
        changes=tuple(changes),
        diagnostics=diagnostics,
    )
