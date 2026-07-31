from __future__ import annotations

import re
from collections import defaultdict

from recipeflow.graph_index import GraphIndex
from recipeflow.models.analysis import (
    FlowFeature,
    GraphAnalysis,
    MaterialUsage,
    SetupPrerequisite,
)
from recipeflow.models.document import MaterialRole
from recipeflow.models.graph import EdgeKind, OperationNode, RecipeGraph


def _public_operation_id(value: str) -> str:
    return value.removeprefix("op:")


def _duration_minutes(operation: OperationNode) -> float | None:
    if operation.duration_value:
        structured_value = (
            operation.duration_value.maximum_minutes
            or operation.duration_value.minimum_minutes
        )
        return float(structured_value) if structured_value is not None else None
    if not operation.duration:
        return None
    match = re.search(
        r"(\d+(?:\.\d+)?)(?:\.\.(\d+(?:\.\d+)?))?\s*"
        r"(ms|s|sec(?:ond)?s?|m|min(?:ute)?s?|h|hr|hours?|days?)",
        operation.duration,
        re.IGNORECASE,
    )
    if not match:
        return None
    parsed_value = float(match.group(2) or match.group(1))
    unit = match.group(3).lower()
    if unit == "ms":
        return parsed_value / 60_000
    if unit.startswith("s"):
        return parsed_value / 60
    if unit.startswith("h"):
        return parsed_value * 60
    if unit.startswith("day"):
        return parsed_value * 1_440
    return parsed_value


def _critical_path(
    index: GraphIndex,
) -> tuple[tuple[str, ...], float | None]:
    dependencies = index.operation_dependencies()
    best_duration: dict[str, float] = {}
    best_path: dict[str, tuple[str, ...]] = {}
    has_known_duration = False
    for operation_id in index.topological_operation_ids():
        own_duration = _duration_minutes(index.operations[operation_id])
        if own_duration is not None:
            has_known_duration = True
        own = own_duration or 0
        predecessors = dependencies[operation_id]
        if predecessors:
            predecessor = max(
                predecessors,
                key=lambda item: (best_duration[item], item),
            )
            best_duration[operation_id] = best_duration[predecessor] + own
            best_path[operation_id] = (*best_path[predecessor], operation_id)
        else:
            best_duration[operation_id] = own
            best_path[operation_id] = (operation_id,)
    if not best_duration:
        return (), None
    final_operation = max(
        best_duration,
        key=lambda item: (best_duration[item], item),
    )
    return (
        tuple(_public_operation_id(item) for item in best_path[final_operation]),
        best_duration[final_operation] if has_known_duration else None,
    )


def analyze(graph: RecipeGraph) -> GraphAnalysis:
    index = GraphIndex(graph)
    transform_ids = {
        operation_id
        for operation_id, operation in index.operations.items()
        if operation.operation_kind == "transform"
    }
    setup_ids = set(index.operations) - transform_ids
    usage = tuple(
        MaterialUsage(
            material_id=material_id,
            producer_operation_id=(
                _public_operation_id(producer)
                if (producer := index.material_producer(material_id))
                else None
            ),
            consumer_operation_ids=tuple(
                _public_operation_id(item)
                for item in index.material_consumers(material_id)
            ),
        )
        for material_id in sorted(index.materials)
    )
    branches = tuple(
        FlowFeature(
            id=material_id,
            related_ids=tuple(
                _public_operation_id(item)
                for item in index.material_consumers(material_id)
            ),
        )
        for material_id in sorted(index.materials)
        if len(index.material_consumers(material_id)) > 1
    )
    joins = tuple(
        FlowFeature(
            id=_public_operation_id(operation_id),
            related_ids=index.material_inputs(operation_id),
        )
        for operation_id in sorted(transform_ids)
        if len(index.material_inputs(operation_id)) > 1
    )
    splits = tuple(
        FlowFeature(
            id=_public_operation_id(operation_id),
            related_ids=index.material_outputs(operation_id),
        )
        for operation_id in sorted(transform_ids)
        if len(index.material_outputs(operation_id)) > 1
    )
    critical_path, critical_minutes = _critical_path(index)
    setup_required_by: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        if (
            edge.kind == EdgeKind.REQUIRES
            and edge.source in setup_ids
            and edge.target in transform_ids
        ):
            setup_required_by[edge.source].add(edge.target)
    parallel_groups = tuple(
        tuple(
            _public_operation_id(operation_id)
            for operation_id in group
            if operation_id in transform_ids
        )
        for group in index.parallel_operation_groups()
    )
    parallel_groups = tuple(group for group in parallel_groups if group)
    consumed = {
        material_id
        for material_id in index.materials
        if index.material_consumers(material_id)
    }
    materials = index.materials
    return GraphAnalysis(
        ingredient_count=sum(
            1
            for material in materials.values()
            if material.source_path
            and material.source_path.startswith("/ingredients/")
        ),
        material_count=len(materials),
        setup_count=len(setup_ids),
        operation_count=len(transform_ids),
        intermediate_ids=tuple(
            sorted(
                material.id
                for material in materials.values()
                if material.role == MaterialRole.INTERMEDIATE
            )
        ),
        final_ids=tuple(sorted(graph.final_material_ids)),
        waste_ids=tuple(
            sorted(
                material.id
                for material in materials.values()
                if material.role == MaterialRole.WASTE
            )
        ),
        garnish_ids=tuple(
            sorted(
                material.id
                for material in materials.values()
                if material.role == MaterialRole.GARNISH
            )
        ),
        reserved_ids=tuple(
            sorted(
                material.id
                for material in materials.values()
                if material.role == MaterialRole.RESERVED
            )
        ),
        unused_ingredient_ids=tuple(
            sorted(
                material.id
                for material in materials.values()
                if material.source_path
                and material.source_path.startswith("/ingredients/")
                and material.id not in consumed
            )
        ),
        material_usage=usage,
        branches=branches,
        joins=joins,
        splits=splits,
        disconnected_components=index.connected_components(),
        topological_operation_ids=tuple(
            _public_operation_id(operation_id)
            for operation_id in index.topological_operation_ids()
            if operation_id in transform_ids
        ),
        critical_path_operation_ids=critical_path,
        critical_path_minutes=critical_minutes,
        parallel_operation_groups=parallel_groups,
        setup_prerequisites=tuple(
            SetupPrerequisite(
                operation_id=_public_operation_id(setup_id),
                required_by_operation_ids=tuple(
                    _public_operation_id(operation_id)
                    for operation_id in sorted(required_by)
                ),
            )
            for setup_id, required_by in sorted(setup_required_by.items())
        ),
    )
