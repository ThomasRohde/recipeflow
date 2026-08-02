from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from recipeflow.exceptions import RecipeCompilationError
from recipeflow.models.common import (
    DurationSpec,
    Provenance,
    Quantity,
    TemperatureSpec,
)
from recipeflow.models.document import (
    MaterialRole,
    MaterialUse,
    Operation,
    RecipeDocument,
    SetupAction,
    duration_text,
    material_use_id,
    quantity_text,
    subrecipe_document,
    temperature_text,
)
from recipeflow.models.graph import (
    CompiledSubrecipe,
    Edge,
    EdgeKind,
    MaterialNode,
    Node,
    OperationNode,
    RecipeGraph,
    SubrecipeInputBinding,
)
from recipeflow.models.results import CompileResult
from recipeflow.validation import validate


@dataclass(frozen=True)
class _OperationRecord:
    source_index: int
    graph_id: str
    value: SetupAction | Operation


@dataclass(frozen=True)
class _EdgeSpec:
    kind: EdgeKind
    source: str
    target: str
    quantity: str | None
    source_path: str | None
    provenance: tuple[Provenance, ...]

    @property
    def semantic_key(self) -> tuple[str, str, str, str]:
        return (
            self.kind.value,
            self.source,
            self.target,
            self.quantity or "",
        )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:36] or "operation"


def _fingerprint(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _operation_records(
    values: tuple[SetupAction | Operation, ...],
) -> tuple[_OperationRecord, ...]:
    bases: list[tuple[int, str, SetupAction | Operation]] = []
    for index, value in enumerate(values):
        if value.id:
            base = f"op:{value.id}"
        else:
            data = value.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
                exclude={"id"},
            )
            base = f"op:auto-{_slug(value.action)}-{_fingerprint(data)[:10]}"
        bases.append((index, base, value))

    totals = Counter(base for _, base, _ in bases)
    seen: Counter[str] = Counter()
    records: list[_OperationRecord] = []
    for index, base, value in bases:
        seen[base] += 1
        graph_id = (
            f"{base}-{seen[base]}"
            if totals[base] > 1
            else base
        )
        records.append(
            _OperationRecord(
                source_index=index,
                graph_id=graph_id,
                value=value,
            )
        )
    return tuple(sorted(records, key=lambda item: item.graph_id))


def _structured_quantity(value: object) -> Quantity | None:
    return value if isinstance(value, Quantity) else None


def _structured_duration(value: object) -> DurationSpec | None:
    return value if isinstance(value, DurationSpec) else None


def _structured_temperature(value: object) -> TemperatureSpec | None:
    return value if isinstance(value, TemperatureSpec) else None


def _edge_id(spec: _EdgeSpec) -> str:
    return f"edge:{_fingerprint(spec.semantic_key)[:16]}"


def _compile_validated(
    document: RecipeDocument,
    *,
    include_subrecipes: bool = True,
) -> RecipeGraph:
    setup_records = _operation_records(document.setup)
    operation_records = _operation_records(document.operations)

    operation_refs = {
        record.value.id: record.graph_id
        for record in (*setup_records, *operation_records)
        if record.value.id
    }
    setup_refs: dict[str, str] = {}
    for record in setup_records:
        setup = record.value
        assert isinstance(setup, SetupAction)
        for reference in (setup.id, setup.produces):
            if reference:
                setup_refs[reference] = record.graph_id

    nodes: list[Node] = []
    for material_id, ingredient in sorted(document.ingredients.items()):
        nodes.append(
            MaterialNode(
                id=material_id,
                label=ingredient.label,
                role=ingredient.role,
                quantity=quantity_text(ingredient.quantity),
                normalized_quantity=_structured_quantity(ingredient.quantity),
                unit=ingredient.unit,
                source_text=ingredient.source_text,
                optional=ingredient.optional,
                preparation_state=ingredient.preparation_state,
                temperature_state=ingredient.temperature_state,
                annotations=ingredient.annotations,
                provenance=ingredient.provenance,
                ambiguity=ingredient.ambiguity,
                source_path=f"/ingredients/{material_id}",
            )
        )

    edge_specs: list[_EdgeSpec] = []
    for record in setup_records:
        setup = record.value
        assert isinstance(setup, SetupAction)
        nodes.append(
            OperationNode(
                id=record.graph_id,
                label=setup.label
                or f"{setup.action} {setup.target or ''}".strip(),
                operation_kind="setup",
                action=setup.action,
                target=setup.target,
                duration=duration_text(setup.duration),
                duration_value=_structured_duration(setup.duration),
                temperature=temperature_text(setup.temperature),
                temperature_value=_structured_temperature(setup.temperature),
                equipment=setup.equipment,
                resources=setup.resources,
                notes=setup.notes,
                provenance=setup.provenance,
                ambiguity=setup.ambiguity,
                source_path=f"/setup/{record.source_index}",
            )
        )
        for require_index, prerequisite in enumerate(setup.requires):
            source = setup_refs.get(prerequisite) or operation_refs.get(prerequisite)
            if source:
                edge_specs.append(
                    _EdgeSpec(
                        kind=EdgeKind.REQUIRES,
                        source=source,
                        target=record.graph_id,
                        quantity=None,
                        source_path=(
                            f"/setup/{record.source_index}/requires/{require_index}"
                        ),
                        provenance=(),
                    )
                )

    final_ids: list[str] = []
    for record in operation_records:
        operation = record.value
        assert isinstance(operation, Operation)
        nodes.append(
            OperationNode(
                id=record.graph_id,
                label=operation.label or operation.action,
                operation_kind="transform",
                action=operation.action,
                operation_type=operation.operation_type,
                duration=duration_text(operation.duration),
                duration_value=_structured_duration(operation.duration),
                temperature=temperature_text(operation.temperature),
                temperature_value=_structured_temperature(operation.temperature),
                until=operation.completion_criteria or operation.until,
                repeat=operation.repeat,
                subrecipe_id=(
                    operation.subrecipe.id
                    if operation.subrecipe
                    else None
                ),
                subrecipe_scale=(
                    operation.subrecipe.scale
                    if operation.subrecipe
                    else None
                ),
                subrecipe_output=(
                    operation.subrecipe.output
                    if operation.subrecipe
                    else None
                ),
                subrecipe_inputs=(
                    tuple(
                        SubrecipeInputBinding(
                            input_id=input_id,
                            material_id=material_id,
                            source_path=(
                                f"/operations/{record.source_index}/subrecipe/"
                                f"inputs/{input_id.replace('~', '~0').replace('/', '~1')}"
                            ),
                        )
                        for input_id, material_id in sorted(
                            operation.subrecipe.inputs.items()
                        )
                    )
                    if operation.subrecipe
                    else ()
                ),
                optional=operation.optional,
                equipment=operation.equipment,
                resources=operation.resources,
                notes=operation.notes,
                provenance=operation.provenance,
                ambiguity=operation.ambiguity,
                source_path=f"/operations/{record.source_index}",
            )
        )
        for input_index, material_use in enumerate(operation.inputs):
            material_id = material_use_id(material_use)
            if isinstance(material_use, MaterialUse):
                if material_use.optional:
                    edge_kind = EdgeKind.OPTIONALLY_APPLIES
                elif material_use.reserve:
                    edge_kind = EdgeKind.RESERVES
                else:
                    edge_kind = EdgeKind.CONSUMES
                edge_quantity = quantity_text(material_use.quantity)
                provenance = material_use.provenance
            else:
                edge_kind = EdgeKind.CONSUMES
                edge_quantity = None
                provenance = ()
            edge_specs.append(
                _EdgeSpec(
                    kind=edge_kind,
                    source=material_id,
                    target=record.graph_id,
                    quantity=edge_quantity,
                    source_path=(
                        f"/operations/{record.source_index}/inputs/{input_index}"
                    ),
                    provenance=provenance,
                )
            )
        for require_index, prerequisite in enumerate(operation.requires):
            source = setup_refs.get(prerequisite) or operation_refs.get(prerequisite)
            if source:
                edge_specs.append(
                    _EdgeSpec(
                        kind=EdgeKind.REQUIRES,
                        source=source,
                        target=record.graph_id,
                        quantity=None,
                        source_path=(
                            f"/operations/{record.source_index}/requires/"
                            f"{require_index}"
                        ),
                        provenance=(),
                    )
                )
        for precedes_index, successor in enumerate(operation.precedes):
            target = operation_refs.get(successor)
            if target:
                edge_specs.append(
                    _EdgeSpec(
                        kind=EdgeKind.PRECEDES,
                        source=record.graph_id,
                        target=target,
                        quantity=None,
                        source_path=(
                            f"/operations/{record.source_index}/precedes/"
                            f"{precedes_index}"
                        ),
                        provenance=(),
                    )
                )
        for output_id, output in sorted(operation.outputs.items()):
            role = MaterialRole.FINAL if output.final else output.role
            nodes.append(
                MaterialNode(
                    id=output_id,
                    label=output.label,
                    role=role,
                    quantity=quantity_text(output.quantity),
                    normalized_quantity=_structured_quantity(output.quantity),
                    unit=output.unit,
                    source_text=output.source_text,
                    optional=output.optional,
                    preparation_state=output.preparation_state,
                    temperature_state=output.temperature_state,
                    annotations=output.annotations,
                    provenance=output.provenance,
                    ambiguity=output.ambiguity,
                    source_path=(
                        f"/operations/{record.source_index}/outputs/{output_id}"
                    ),
                )
            )
            if role == MaterialRole.WASTE:
                edge_kind = EdgeKind.DISCARDS
            elif role == MaterialRole.RESERVED:
                edge_kind = EdgeKind.RESERVES
            else:
                edge_kind = EdgeKind.PRODUCES
            edge_specs.append(
                _EdgeSpec(
                    kind=edge_kind,
                    source=record.graph_id,
                    target=output_id,
                    quantity=quantity_text(output.quantity),
                    source_path=(
                        f"/operations/{record.source_index}/outputs/{output_id}"
                    ),
                    provenance=output.provenance,
                )
            )
            if role == MaterialRole.FINAL:
                final_ids.append(output_id)

    unique_specs = {
        spec.semantic_key: spec
        for spec in edge_specs
    }
    sorted_specs = sorted(
        unique_specs.values(),
        key=lambda item: (
            item.kind.value,
            item.source,
            item.target,
            item.quantity or "",
        ),
    )
    edges = [
        Edge(
            id=_edge_id(spec),
            kind=spec.kind,
            source=spec.source,
            target=spec.target,
            quantity=spec.quantity,
            source_path=spec.source_path,
            provenance=spec.provenance,
        )
        for spec in sorted_specs
    ]
    nodes.sort(key=lambda node: (node.kind, node.id))
    recipe_id = document.recipe.id or (
        f"recipe:auto-{_fingerprint({'title': document.recipe.title})[:12]}"
    )
    compiled_subrecipes: dict[str, CompiledSubrecipe] = {}
    if include_subrecipes:
        for key, subrecipe in sorted(document.subrecipes.items()):
            scoped = _compile_validated(
                subrecipe_document(
                    subrecipe,
                    available_subrecipes=document.subrecipes,
                ),
                include_subrecipes=False,
            )
            prefix = f"/subrecipes/{key.replace('~', '~0').replace('/', '~1')}"
            scoped_nodes: tuple[Node, ...] = tuple(
                node.model_copy(
                    update={
                        "source_path": (
                            f"{prefix}{node.source_path}"
                            if node.source_path
                            else prefix
                        )
                    }
                )
                for node in scoped.nodes
            )
            scoped_edges = tuple(
                edge.model_copy(
                    update={
                        "source_path": (
                            f"{prefix}{edge.source_path}"
                            if edge.source_path
                            else prefix
                        )
                    }
                )
                for edge in scoped.edges
            )
            compiled_subrecipes[key] = CompiledSubrecipe(
                id=subrecipe.id,
                title=subrecipe.title,
                nodes=scoped_nodes,
                edges=scoped_edges,
                final_material_ids=subrecipe.output_ids,
            )

    return RecipeGraph(
        recipe_id=recipe_id,
        title=document.recipe.title,
        description=document.recipe.description,
        source=document.recipe.source,
        yield_text=document.recipe.yield_text,
        locale=document.recipe.locale,
        tags=document.recipe.tags,
        notes=document.recipe.notes,
        ambiguity=document.recipe.ambiguity,
        nodes=tuple(nodes),
        edges=tuple(edges),
        final_material_ids=tuple(sorted(final_ids)),
        subrecipes=compiled_subrecipes,
    )


def compile_document(
    document: RecipeDocument,
    *,
    strict: bool = False,
) -> CompileResult:
    validation = validate(document, strict=strict)
    if not validation.ok:
        return CompileResult(
            document=document,
            diagnostics=validation.diagnostics,
        )
    return CompileResult(
        document=document,
        graph=_compile_validated(document),
        diagnostics=validation.diagnostics,
    )


def compile_recipe(document: RecipeDocument) -> RecipeGraph:
    """Compile a validated document, preserving the original graph-returning API."""

    result = compile_document(document)
    if result.graph is None:
        raise RecipeCompilationError(result.diagnostics)
    return result.graph
