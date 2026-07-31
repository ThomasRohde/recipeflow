from __future__ import annotations

import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal, cast

from pydantic import Field

from recipeflow.graph_index import GraphIndex
from recipeflow.models.common import Diagnostic, PublicModel, Severity
from recipeflow.models.document import MaterialRole
from recipeflow.models.graph import MaterialNode, OperationNode, RecipeGraph


class RecipeInstance(PublicModel):
    id: str
    graph: RecipeGraph
    scale: Decimal = Decimal(1)


class ResourceCapacity(PublicModel):
    id: str
    capacity: int = Field(default=1, ge=1)


class PlanningRequest(PublicModel):
    recipes: tuple[RecipeInstance, ...]
    target_time: datetime
    resources: tuple[ResourceCapacity, ...] = ()
    default_operation_minutes: Decimal = Decimal(5)


class ScheduledOperation(PublicModel):
    id: str
    recipe_instance_id: str
    operation_id: str
    label: str
    start: datetime
    end: datetime
    duration_minutes: Decimal
    resource_ids: tuple[str, ...] = ()


class ShoppingItem(PublicModel):
    id: str
    label: str
    quantity_texts: tuple[str, ...] = ()
    normalized_quantity: Decimal | None = None
    unit: str | None = None
    optional: bool = False
    recipe_instance_ids: tuple[str, ...] = ()


class MiseEnPlaceItem(PublicModel):
    id: str
    kind: Literal["material", "setup"]
    label: str
    recipe_instance_id: str
    material_id: str | None = None
    operation_id: str | None = None
    detail: str | None = None


class PreparationPlan(PublicModel):
    schema_version: Literal["recipeflow.preparation-plan/v1"] = (
        "recipeflow.preparation-plan/v1"
    )
    target_time: datetime
    start_time: datetime
    operations: tuple[ScheduledOperation, ...]
    critical_path_minutes: Decimal
    shopping_list: tuple[ShoppingItem, ...] = ()
    mise_en_place: tuple[MiseEnPlaceItem, ...] = ()


class PlanningResult(PublicModel):
    schema_version: Literal["recipeflow.planning-result/v1"] = (
        "recipeflow.planning-result/v1"
    )
    plan: PreparationPlan | None = None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.plan is not None and not any(
            diagnostic.severity == Severity.ERROR
            for diagnostic in self.diagnostics
        )


def _duration_minutes(
    operation: OperationNode,
    default: Decimal,
) -> tuple[Decimal, bool]:
    if operation.duration_value:
        value = (
            operation.duration_value.maximum_minutes
            or operation.duration_value.minimum_minutes
        )
        if value is not None:
            return value, True
    if operation.duration:
        match = re.search(
            r"(\d+(?:\.\d+)?)(?:\.\.(\d+(?:\.\d+)?))?\s*"
            r"(ms|s|sec(?:ond)?s?|m|min(?:ute)?s?|h|hr|hours?|days?)",
            operation.duration,
            re.IGNORECASE,
        )
        if match:
            value = Decimal(match.group(2) or match.group(1))
            unit = match.group(3).lower()
            if unit == "ms":
                value /= Decimal(60_000)
            elif unit.startswith("s"):
                value /= Decimal(60)
            elif unit.startswith("h"):
                value *= Decimal(60)
            elif unit.startswith("day"):
                value *= Decimal(1_440)
            if operation.repeat and operation.repeat.count:
                value *= operation.repeat.count
            return value, True
    return default, False


def _quantity_projection(
    material: MaterialNode,
    scale: Decimal,
) -> tuple[Decimal | None, str | None, str | None]:
    quantity = material.normalized_quantity
    if quantity and quantity.normalized:
        normalized = quantity.normalized
        value = normalized.value
        if value is None and normalized.minimum == normalized.maximum:
            value = normalized.minimum
        if value is not None:
            return value * scale, normalized.unit or material.unit, quantity.source_text
    if material.quantity:
        suffix = "" if scale == 1 else f" x {scale}"
        return None, material.unit, f"{material.quantity}{suffix}"
    return None, material.unit, None


def project_shopping_list(
    recipes: tuple[RecipeInstance, ...],
) -> tuple[ShoppingItem, ...]:
    groups: dict[
        tuple[str, str | None],
        dict[str, object],
    ] = {}
    for instance in recipes:
        index = GraphIndex(instance.graph)
        for material in index.materials.values():
            if index.material_producer(material.id) is not None:
                continue
            if material.role not in {
                MaterialRole.INGREDIENT,
                MaterialRole.OPTIONAL,
                MaterialRole.RESERVED,
            }:
                continue
            amount, unit, source_text = _quantity_projection(
                material,
                instance.scale,
            )
            key = (material.label.casefold(), unit)
            group = groups.setdefault(
                key,
                {
                    "id": material.id,
                    "label": material.label,
                    "amount": Decimal(0),
                    "has_amount": False,
                    "texts": [],
                    "optional": True,
                    "recipes": set(),
                },
            )
            if amount is not None:
                group["amount"] = group["amount"] + amount  # type: ignore[operator]
                group["has_amount"] = True
            if source_text:
                texts = group["texts"]
                assert isinstance(texts, list)
                texts.append(source_text)
            group["optional"] = bool(group["optional"]) and (
                material.optional or material.role == MaterialRole.OPTIONAL
            )
            recipe_ids = group["recipes"]
            assert isinstance(recipe_ids, set)
            recipe_ids.add(instance.id)

    items = []
    for (label_key, unit), group in sorted(groups.items()):
        del label_key
        recipes_set = group["recipes"]
        texts = group["texts"]
        assert isinstance(recipes_set, set)
        assert isinstance(texts, list)
        items.append(
            ShoppingItem(
                id=str(group["id"]),
                label=str(group["label"]),
                quantity_texts=tuple(sorted(set(str(item) for item in texts))),
                normalized_quantity=(
                    cast(Decimal, group["amount"])
                    if bool(group["has_amount"])
                    else None
                ),
                unit=unit,
                optional=bool(group["optional"]),
                recipe_instance_ids=tuple(sorted(str(item) for item in recipes_set)),
            )
        )
    return tuple(items)


def project_mise_en_place(
    recipes: tuple[RecipeInstance, ...],
) -> tuple[MiseEnPlaceItem, ...]:
    items: list[MiseEnPlaceItem] = []
    for instance in sorted(recipes, key=lambda item: item.id):
        index = GraphIndex(instance.graph)
        for material in sorted(index.materials.values(), key=lambda item: item.id):
            if (
                index.material_producer(material.id) is None
                and (
                    material.preparation_state
                    or material.temperature_state
                    or material.annotations
                )
            ):
                detail = " · ".join(
                    item
                    for item in (
                        material.preparation_state,
                        material.temperature_state,
                        *material.annotations,
                    )
                    if item
                )
                items.append(
                    MiseEnPlaceItem(
                        id=f"{instance.id}:material:{material.id}",
                        kind="material",
                        label=material.label,
                        recipe_instance_id=instance.id,
                        material_id=material.id,
                        detail=detail or None,
                    )
                )
        for operation in sorted(
            index.operations.values(),
            key=lambda item: item.id,
        ):
            if operation.operation_kind == "setup":
                detail = " · ".join(
                    item
                    for item in (operation.temperature, operation.duration)
                    if item
                )
                items.append(
                    MiseEnPlaceItem(
                        id=f"{instance.id}:setup:{operation.id}",
                        kind="setup",
                        label=operation.label,
                        recipe_instance_id=instance.id,
                        operation_id=operation.id.removeprefix("op:"),
                        detail=detail or None,
                    )
                )
    return tuple(items)


def plan_recipes(request: PlanningRequest) -> PlanningResult:
    diagnostics: list[Diagnostic] = []
    capacities = {
        resource.id: resource.capacity
        for resource in request.resources
    }
    resource_slots: dict[str, list[Decimal]] = {}
    operation_records: dict[str, tuple[RecipeInstance, OperationNode]] = {}
    dependencies: dict[str, set[str]] = {}
    for instance in sorted(request.recipes, key=lambda item: item.id):
        index = GraphIndex(instance.graph)
        local_dependencies = index.operation_dependencies()
        for operation_id, operation in index.operations.items():
            composite_id = f"{instance.id}::{operation_id}"
            operation_records[composite_id] = (instance, operation)
            dependencies[composite_id] = {
                f"{instance.id}::{dependency}"
                for dependency in local_dependencies[operation_id]
            }
            requirement_totals: dict[str, int] = {}
            for requirement in operation.resources:
                requirement_totals[requirement.id] = (
                    requirement_totals.get(requirement.id, 0)
                    + requirement.quantity
                )
            for resource_id, quantity in sorted(requirement_totals.items()):
                capacity = capacities.get(resource_id, 1)
                if quantity > capacity:
                    diagnostics.append(
                        Diagnostic(
                            code="RF702",
                            severity=Severity.ERROR,
                            path=operation.source_path or "",
                            message=(
                                f"Operation {operation.id!r} requires "
                                f"{quantity} units of {resource_id!r}, "
                                f"but capacity is {capacity}."
                            ),
                        )
                    )
                resource_slots.setdefault(
                    resource_id,
                    [Decimal(0)] * capacity,
                )
            for equipment in operation.equipment:
                resource_slots.setdefault(
                    equipment,
                    [Decimal(0)] * capacities.get(equipment, 1),
                )
    if any(item.severity == Severity.ERROR for item in diagnostics):
        return PlanningResult(diagnostics=tuple(diagnostics))

    remaining = set(operation_records)
    completed: dict[str, Decimal] = {}
    schedule: dict[str, tuple[Decimal, Decimal, Decimal, tuple[str, ...]]] = {}
    while remaining:
        ready = sorted(
            operation_id
            for operation_id in remaining
            if dependencies[operation_id] <= completed.keys()
        )
        if not ready:
            return PlanningResult(
                diagnostics=(
                    *diagnostics,
                    Diagnostic(
                        code="RF701",
                        severity=Severity.ERROR,
                        path="/recipes",
                        message="Combined recipe dependencies contain a cycle.",
                    ),
                )
            )
        for composite_id in ready:
            instance, operation = operation_records[composite_id]
            earliest = max(
                (completed[item] for item in dependencies[composite_id]),
                default=Decimal(0),
            )
            duration, known_duration = _duration_minutes(
                operation,
                request.default_operation_minutes,
            )
            if not known_duration:
                diagnostics.append(
                    Diagnostic(
                        code="RF710",
                        severity=Severity.WARNING,
                        path=operation.source_path or "",
                        message=(
                            f"Operation {operation.id!r} has no parseable duration; "
                            f"using {request.default_operation_minutes} minutes."
                        ),
                    )
                )
            requirements: dict[str, int] = {}
            for requirement in operation.resources:
                requirements[requirement.id] = (
                    requirements.get(requirement.id, 0)
                    + requirement.quantity
                )
            for equipment in operation.equipment:
                requirements[equipment] = max(requirements.get(equipment, 0), 1)
            changed = True
            while changed:
                changed = False
                for resource_id, quantity in sorted(requirements.items()):
                    slots = sorted(resource_slots[resource_id])
                    available = slots[quantity - 1]
                    if available > earliest:
                        earliest = available
                        changed = True
            end = earliest + duration
            for resource_id, quantity in sorted(requirements.items()):
                slots = resource_slots[resource_id]
                selected = sorted(range(len(slots)), key=lambda index: slots[index])[
                    :quantity
                ]
                for slot_index in selected:
                    slots[slot_index] = end
            resource_ids = tuple(
                resource_id
                for resource_id, quantity in sorted(requirements.items())
                for _ in range(quantity)
            )
            schedule[composite_id] = (
                earliest,
                end,
                duration,
                resource_ids,
            )
            completed[composite_id] = end
            remaining.remove(composite_id)

    makespan = max(completed.values(), default=Decimal(0))
    plan_start = request.target_time - timedelta(minutes=float(makespan))
    operations: list[ScheduledOperation] = []
    for composite_id, (start, end, duration, resources) in sorted(
        schedule.items(),
        key=lambda item: (item[1][0], item[0]),
    ):
        instance, operation = operation_records[composite_id]
        operations.append(
            ScheduledOperation(
                id=composite_id,
                recipe_instance_id=instance.id,
                operation_id=operation.id.removeprefix("op:"),
                label=operation.label,
                start=plan_start + timedelta(minutes=float(start)),
                end=plan_start + timedelta(minutes=float(end)),
                duration_minutes=duration,
                resource_ids=resources,
            )
        )
    return PlanningResult(
        plan=PreparationPlan(
            target_time=request.target_time,
            start_time=plan_start,
            operations=tuple(operations),
            critical_path_minutes=makespan,
            shopping_list=project_shopping_list(request.recipes),
            mise_en_place=project_mise_en_place(request.recipes),
        ),
        diagnostics=tuple(
            sorted(
                diagnostics,
                key=lambda item: (item.code, item.path, item.message),
            )
        ),
    )
