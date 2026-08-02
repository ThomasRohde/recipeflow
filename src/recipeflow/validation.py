from __future__ import annotations

import re
from collections import defaultdict, deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import pairwise

from recipeflow.models.common import (
    Diagnostic,
    DurationSpec,
    PublicModel,
    Quantity,
    Severity,
    TemperatureSpec,
)
from recipeflow.models.document import (
    MaterialRole,
    MaterialUse,
    Operation,
    QuantityValue,
    RecipeDocument,
    duration_text,
    material_use_id,
    subrecipe_document,
    temperature_text,
)
from recipeflow.models.results import ValidationResult

_RESERVED_ID_PREFIXES = ("op:", "edge:")
_DURATION_PATTERN = re.compile(
    r"^\s*\d+(?:\.\d+)?(?:\.\.\d+(?:\.\d+)?)?"
    r"\s*(?:ms|s|sec(?:ond)?s?|m|min(?:ute)?s?|h|hr|hours?|days?)\s*$",
    re.IGNORECASE,
)
_ISO_DURATION_PATTERN = re.compile(
    r"^P(?=.+$)"
    r"(?:\d+(?:\.\d+)?Y)?"
    r"(?:\d+(?:\.\d+)?M)?"
    r"(?:\d+(?:\.\d+)?W)?"
    r"(?:\d+(?:\.\d+)?D)?"
    r"(?:T(?=\d)"
    r"(?:\d+(?:\.\d+)?H)?"
    r"(?:\d+(?:\.\d+)?M)?"
    r"(?:\d+(?:\.\d+)?S)?)?$",
    re.IGNORECASE,
)
_TEMPERATURE_PATTERN = re.compile(
    r"^\s*-?\d+(?:\.\d+)?(?:\.\.-?\d+(?:\.\d+)?)?\s*°?\s*[CFK]\s*$",
    re.IGNORECASE,
)
_NAMED_DURATIONS = {"overnight", "briefly", "until ready", "as needed"}
_NAMED_TEMPERATURES = {
    "room temperature",
    "ambient",
    "chilled",
    "cold",
    "cool",
    "warm",
    "hot",
    "low",
    "medium",
    "high",
}


class ValidationOptions(PublicModel):
    strict: bool = False
    warnings_as_errors: bool = False
    require_provenance: bool | None = None


@dataclass(frozen=True)
class ValidationContext:
    document: RecipeDocument
    options: ValidationOptions

    @property
    def operation_keys(self) -> tuple[str, ...]:
        return tuple(
            operation.id or f"@operation:{index}"
            for index, operation in enumerate(self.document.operations)
        )


ValidationRule = Callable[[ValidationContext], Iterable[Diagnostic]]


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _operation_key(operation: Operation, index: int) -> str:
    return operation.id or f"@operation:{index}"


def _output_declarations(
    document: RecipeDocument,
) -> dict[str, list[tuple[int, str]]]:
    declarations: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for index, operation in enumerate(document.operations):
        for output_id in operation.outputs:
            declarations[output_id].append(
                (index, f"/operations/{index}/outputs/{_escape(output_id)}")
            )
    return declarations


def _rule_identifiers(context: ValidationContext) -> Iterable[Diagnostic]:
    document = context.document
    output_declarations = _output_declarations(document)
    material_paths: dict[str, list[str]] = defaultdict(list)
    for material_id in document.ingredients:
        material_paths[material_id].append(f"/ingredients/{_escape(material_id)}")
    for output_id, declarations in output_declarations.items():
        material_paths[output_id].extend(path for _, path in declarations)

    for material_id, paths in sorted(material_paths.items()):
        if len(paths) > 1:
            yield Diagnostic(
                code="RF101",
                severity=Severity.ERROR,
                path=paths[0],
                related_paths=tuple(paths[1:]),
                message=f"Material id {material_id!r} is declared more than once.",
            )
        if material_id.startswith(_RESERVED_ID_PREFIXES):
            yield Diagnostic(
                code="RF201",
                severity=Severity.ERROR,
                path=paths[0],
                message=(
                    f"Material id {material_id!r} uses a reserved graph namespace."
                ),
                suggestions=(material_id.replace(":", "-", 1),),
            )

    operation_paths: dict[str, list[str]] = defaultdict(list)
    for index, setup in enumerate(document.setup):
        if setup.id:
            operation_paths[setup.id].append(f"/setup/{index}/id")
    for index, operation in enumerate(document.operations):
        if operation.id:
            operation_paths[operation.id].append(f"/operations/{index}/id")
    for operation_id, paths in sorted(operation_paths.items()):
        if len(paths) > 1:
            yield Diagnostic(
                code="RF102",
                severity=Severity.ERROR,
                path=paths[0],
                related_paths=tuple(paths[1:]),
                message=f"Operation id {operation_id!r} is declared more than once.",
            )

    setup_tokens: dict[str, list[str]] = defaultdict(list)
    for index, setup in enumerate(document.setup):
        if setup.produces:
            setup_tokens[setup.produces].append(f"/setup/{index}/produces")
    for token, paths in sorted(setup_tokens.items()):
        if len(paths) > 1:
            yield Diagnostic(
                code="RF202",
                severity=Severity.ERROR,
                path=paths[0],
                related_paths=tuple(paths[1:]),
                message=f"Setup prerequisite token {token!r} has multiple producers.",
            )


def _rule_references(context: ValidationContext) -> Iterable[Diagnostic]:
    document = context.document
    output_ids = set(_output_declarations(document))
    known_materials = set(document.ingredients) | output_ids
    setup_refs = {
        reference
        for setup in document.setup
        for reference in (setup.id, setup.produces)
        if reference
    }
    operation_ids = {
        operation.id for operation in document.operations if operation.id
    }
    prerequisite_refs = setup_refs | operation_ids

    for index, operation in enumerate(document.operations):
        seen_inputs: dict[str, int] = {}
        for input_index, material_use in enumerate(operation.inputs):
            material_id = material_use_id(material_use)
            path = f"/operations/{index}/inputs/{input_index}"
            if material_id not in known_materials:
                yield Diagnostic(
                    code="RF104",
                    severity=Severity.ERROR,
                    path=path,
                    message=f"Unknown material {material_id!r}.",
                    suggestions=tuple(sorted(known_materials)),
                )
            if material_id in seen_inputs:
                yield Diagnostic(
                    code="RF203",
                    severity=Severity.ERROR,
                    path=path,
                    related_paths=(
                        f"/operations/{index}/inputs/{seen_inputs[material_id]}",
                    ),
                    message=(
                        f"Material {material_id!r} is listed more than once; "
                        "use one material-use object with an explicit quantity."
                    ),
                )
            else:
                seen_inputs[material_id] = input_index
        for require_index, prerequisite in enumerate(operation.requires):
            if prerequisite not in prerequisite_refs:
                yield Diagnostic(
                    code="RF105",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/requires/{require_index}",
                    message=f"Unknown prerequisite {prerequisite!r}.",
                    suggestions=tuple(sorted(prerequisite_refs)),
                )
        for precedes_index, successor in enumerate(operation.precedes):
            if successor not in operation_ids:
                yield Diagnostic(
                    code="RF205",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/precedes/{precedes_index}",
                    message=f"Unknown successor operation {successor!r}.",
                    suggestions=tuple(sorted(operation_ids)),
                )
        if operation.subrecipe:
            reference = operation.subrecipe
            subrecipe = document.subrecipes.get(reference.id)
            if subrecipe is None:
                yield Diagnostic(
                    code="RF206",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/subrecipe/id",
                    message=f"Unknown subrecipe {reference.id!r}.",
                    suggestions=tuple(sorted(document.subrecipes)),
                )
                continue
            if (
                reference.output is not None
                and reference.output not in subrecipe.output_ids
            ):
                yield Diagnostic(
                    code="RF207",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/subrecipe/output",
                    message=(
                        f"Subrecipe {subrecipe.id!r} does not expose output "
                        f"{reference.output!r}."
                    ),
                    suggestions=tuple(sorted(subrecipe.output_ids)),
                )
            elif reference.output is None and len(subrecipe.output_ids) > 1:
                yield Diagnostic(
                    code="RF207",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/subrecipe/output",
                    message=(
                        f"Subrecipe {subrecipe.id!r} exposes multiple outputs; "
                        "select one explicitly."
                    ),
                    suggestions=tuple(sorted(subrecipe.output_ids)),
                )

            bound_parent_materials = set(reference.inputs.values())
            listed_parent_materials = {
                material_use_id(item) for item in operation.inputs
            }
            for input_id, material_id in sorted(reference.inputs.items()):
                input_path = (
                    f"/operations/{index}/subrecipe/inputs/{_escape(input_id)}"
                )
                if input_id not in subrecipe.ingredients:
                    yield Diagnostic(
                        code="RF216",
                        severity=Severity.ERROR,
                        path=input_path,
                        message=(
                            f"Subrecipe {subrecipe.id!r} has no input "
                            f"ingredient {input_id!r}."
                        ),
                        suggestions=tuple(sorted(subrecipe.ingredients)),
                    )
                if material_id not in listed_parent_materials:
                    yield Diagnostic(
                        code="RF216",
                        severity=Severity.ERROR,
                        path=input_path,
                        message=(
                            f"Bound parent material {material_id!r} must also "
                            "appear in the invoking operation's inputs."
                        ),
                        suggestions=tuple(sorted(listed_parent_materials)),
                    )
            for input_id, ingredient in sorted(subrecipe.ingredients.items()):
                if input_id not in reference.inputs and not ingredient.optional:
                    yield Diagnostic(
                        code="RF216",
                        severity=Severity.ERROR,
                        path=f"/operations/{index}/subrecipe/inputs",
                        message=(
                            f"Required subrecipe input {input_id!r} has no "
                            "explicit parent-material binding."
                        ),
                        suggestions=(input_id,),
                    )
            if len(bound_parent_materials) != len(reference.inputs):
                yield Diagnostic(
                    code="RF216",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/subrecipe/inputs",
                    message=(
                        "Each subrecipe input must bind to a distinct parent "
                        "material; split portions explicitly before invocation."
                    ),
                )


def _rule_operation_shape(context: ValidationContext) -> Iterable[Diagnostic]:
    for index, operation in enumerate(context.document.operations):
        if not operation.outputs:
            yield Diagnostic(
                code="RF103",
                severity=Severity.ERROR,
                path=f"/operations/{index}/outputs",
                message="A transformation must produce at least one material.",
            )
        if not operation.inputs and not operation.requires and operation.subrecipe is None:
            yield Diagnostic(
                code="RF301",
                severity=Severity.ERROR,
                path=f"/operations/{index}",
                message=(
                    "A transformation must consume material, require a prerequisite, "
                    "or invoke a subrecipe."
                ),
            )
        for output_id, output in operation.outputs.items():
            path = f"/operations/{index}/outputs/{_escape(output_id)}"
            if output.role == MaterialRole.INGREDIENT:
                yield Diagnostic(
                    code="RF302",
                    severity=Severity.ERROR,
                    path=f"{path}/role",
                    message="An operation output cannot have the ingredient role.",
                )
            if output.final and output.role in {
                MaterialRole.WASTE,
                MaterialRole.GARNISH,
                MaterialRole.RESERVED,
                MaterialRole.OPTIONAL,
            }:
                yield Diagnostic(
                    code="RF303",
                    severity=Severity.ERROR,
                    path=path,
                    message=(
                        f"Output {output_id!r} cannot be both final and "
                        f"{output.role.value!r}."
                    ),
                )


def _rule_material_usage(context: ValidationContext) -> Iterable[Diagnostic]:
    document = context.document
    consumers: dict[str, list[tuple[int, int, str | MaterialUse]]] = defaultdict(list)
    for operation_index, operation in enumerate(document.operations):
        for input_index, material_use in enumerate(operation.inputs):
            consumers[material_use_id(material_use)].append(
                (operation_index, input_index, material_use)
            )

    for ingredient_id, ingredient in sorted(document.ingredients.items()):
        if (
            ingredient_id not in consumers
            and not ingredient.optional
            and ingredient.role != MaterialRole.OPTIONAL
        ):
            yield Diagnostic(
                code="RF211",
                severity=Severity.ERROR,
                path=f"/ingredients/{_escape(ingredient_id)}",
                message=(
                    f"Ingredient {ingredient_id!r} is never consumed or marked optional."
                ),
            )

    finals: list[tuple[str, str]] = []
    for operation_index, operation in enumerate(document.operations):
        for output_id, output in operation.outputs.items():
            path = (
                f"/operations/{operation_index}/outputs/{_escape(output_id)}"
            )
            if output.final or output.role == MaterialRole.FINAL:
                finals.append((output_id, path))
            elif (
                output.role == MaterialRole.INTERMEDIATE
                and output_id not in consumers
                and not output.shareable
            ):
                yield Diagnostic(
                    code="RF304",
                    severity=Severity.WARNING,
                    path=path,
                    message=f"Intermediate material {output_id!r} is never consumed.",
                )

    if not finals:
        yield Diagnostic(
            code="RF212",
            severity=Severity.ERROR,
            path="/operations",
            message="At least one final output is required.",
        )
    elif len(finals) > 1 and not document.recipe.allow_multiple_outputs:
        yield Diagnostic(
            code="RF305",
            severity=Severity.ERROR,
            path=finals[0][1],
            related_paths=tuple(path for _, path in finals[1:]),
            message=(
                "Multiple final outputs require recipe.allow_multiple_outputs=true."
            ),
            context={"final_material_ids": [item for item, _ in finals]},
        )

    output_lookup = {
        output_id: output
        for operation in document.operations
        for output_id, output in operation.outputs.items()
    }
    for material_id, uses in sorted(consumers.items()):
        declaration = output_lookup.get(material_id)
        reserved_ingredient = document.ingredients.get(material_id)
        is_reserved = (
            declaration is not None and declaration.role == MaterialRole.RESERVED
        ) or (
            reserved_ingredient is not None
            and reserved_ingredient.role == MaterialRole.RESERVED
        )
        if is_reserved:
            for operation_index, input_index, material_use in uses:
                if not (
                    isinstance(material_use, MaterialUse)
                    and material_use.from_reserve
                ):
                    yield Diagnostic(
                        code="RF306",
                        severity=Severity.ERROR,
                        path=f"/operations/{operation_index}/inputs/{input_index}",
                        message=(
                            f"Reserved material {material_id!r} must be consumed "
                            "with from_reserve=true."
                        ),
                    )

        if len(uses) > 1:
            explicitly_shareable = bool(declaration and declaration.shareable)
            explicit_split = all(
                isinstance(material_use, MaterialUse)
                and (
                    material_use.reserve
                    or material_use.optional
                    or material_use.quantity is not None
                )
                for _, _, material_use in uses
            )
            if not explicitly_shareable and not explicit_split:
                paths = tuple(
                    f"/operations/{operation_index}/inputs/{input_index}"
                    for operation_index, input_index, _ in uses
                )
                yield Diagnostic(
                    code="RF307",
                    severity=Severity.ERROR,
                    path=paths[0],
                    related_paths=paths[1:],
                    message=(
                        f"Material {material_id!r} feeds multiple operations without "
                        "an explicit split, reservation, quantity, or shareable declaration."
                    ),
                )


def _operation_dependencies(
    document: RecipeDocument,
) -> tuple[dict[str, set[str]], dict[str, int]]:
    operations = {
        _operation_key(operation, index): operation
        for index, operation in enumerate(document.operations)
    }
    explicit_ids = {
        operation.id: _operation_key(operation, index)
        for index, operation in enumerate(document.operations)
        if operation.id
    }
    producer = {
        output_id: _operation_key(operation, index)
        for index, operation in enumerate(document.operations)
        for output_id in operation.outputs
    }
    setup_refs = {
        reference: f"@setup:{index}"
        for index, setup in enumerate(document.setup)
        for reference in (setup.id, setup.produces)
        if reference
    }
    adjacency: dict[str, set[str]] = defaultdict(set)
    all_nodes = set(operations) | set(setup_refs.values())
    indegree = {operation_id: 0 for operation_id in all_nodes}

    def add(source: str, target: str) -> None:
        if source in indegree and target in indegree and target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1

    for index, operation in enumerate(document.operations):
        operation_id = _operation_key(operation, index)
        for material_use in operation.inputs:
            source = producer.get(material_use_id(material_use))
            if source:
                add(source, operation_id)
        for prerequisite in operation.requires:
            source = setup_refs.get(prerequisite) or explicit_ids.get(prerequisite)
            if source:
                add(source, operation_id)
        for successor in operation.precedes:
            target = explicit_ids.get(successor)
            if target:
                add(operation_id, target)
    return adjacency, indegree


def _rule_cycles(context: ValidationContext) -> Iterable[Diagnostic]:
    adjacency, indegree = _operation_dependencies(context.document)
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited: list[str] = []
    while queue:
        node = queue.popleft()
        visited.append(node)
        for successor in sorted(adjacency[node]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)
    if len(visited) != len(indegree):
        cyclic_nodes = tuple(sorted(node for node, degree in indegree.items() if degree))
        yield Diagnostic(
            code="RF213",
            severity=Severity.ERROR,
            path="/operations",
            message="Material and prerequisite dependencies contain a cycle.",
            context={"operation_ids": list(cyclic_nodes)},
        )


def _valid_duration(value: str | DurationSpec | None) -> bool:
    text = duration_text(value)
    if text is None:
        return True
    normalized = text.strip().lower()
    return (
        normalized in _NAMED_DURATIONS
        or bool(_DURATION_PATTERN.fullmatch(text))
        or bool(_ISO_DURATION_PATTERN.fullmatch(text.strip()))
    )


def _valid_temperature(value: str | TemperatureSpec | None) -> bool:
    text = temperature_text(value)
    if text is None:
        return True
    normalized = text.strip().lower()
    return normalized in _NAMED_TEMPERATURES or bool(
        _TEMPERATURE_PATTERN.fullmatch(text)
    )


def _rule_temporal(context: ValidationContext) -> Iterable[Diagnostic]:
    for index, setup in enumerate(context.document.setup):
        if not _valid_duration(setup.duration):
            yield Diagnostic(
                code="RF401",
                severity=Severity.ERROR,
                path=f"/setup/{index}/duration",
                message=f"Malformed duration {duration_text(setup.duration)!r}.",
            )
        if not _valid_temperature(setup.temperature):
            yield Diagnostic(
                code="RF402",
                severity=Severity.ERROR,
                path=f"/setup/{index}/temperature",
                message=f"Malformed temperature {temperature_text(setup.temperature)!r}.",
            )

    for index, operation in enumerate(context.document.operations):
        if not _valid_duration(operation.duration):
            yield Diagnostic(
                code="RF401",
                severity=Severity.ERROR,
                path=f"/operations/{index}/duration",
                message=f"Malformed duration {duration_text(operation.duration)!r}.",
            )
        if not _valid_temperature(operation.temperature):
            yield Diagnostic(
                code="RF402",
                severity=Severity.ERROR,
                path=f"/operations/{index}/temperature",
                message=(
                    f"Malformed temperature {temperature_text(operation.temperature)!r}."
                ),
            )
        if operation.repeat:
            repeat = operation.repeat
            if repeat.count is not None and repeat.count < 1:
                yield Diagnostic(
                    code="RF403",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/repeat/count",
                    message="Repeat count must be at least one.",
                )
            if repeat.interval is not None and not _valid_duration(repeat.interval):
                yield Diagnostic(
                    code="RF404",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/repeat/interval",
                    message=(
                        f"Malformed repeat interval "
                        f"{duration_text(repeat.interval)!r}."
                    ),
                )
            if (
                repeat.count is None
                and repeat.interval is None
                and not repeat.until
            ):
                yield Diagnostic(
                    code="RF405",
                    severity=Severity.ERROR,
                    path=f"/operations/{index}/repeat",
                    message="A repetition needs a count, interval, or until condition.",
                )


def _numeric_quantity(
    value: QuantityValue | None,
    fallback_unit: str | None = None,
) -> tuple[Decimal, str | None] | None:
    if value is None:
        return None
    if isinstance(value, Quantity) and value.normalized:
        normalized = value.normalized
        number = normalized.value
        if number is None and normalized.minimum == normalized.maximum:
            number = normalized.minimum
        if number is not None:
            return number, normalized.unit or fallback_unit
        text = value.source_text
    else:
        text = value if isinstance(value, str) else value.source_text
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(.*)\s*$", text)
    if not match:
        return None
    try:
        number = Decimal(match.group(1))
    except InvalidOperation:
        return None
    unit = match.group(2).strip() or fallback_unit
    return number, unit


def _rule_split_quantities(context: ValidationContext) -> Iterable[Diagnostic]:
    declared_materials: dict[str, tuple[QuantityValue | None, str | None]] = {
        material_id: (ingredient.quantity, ingredient.unit)
        for material_id, ingredient in context.document.ingredients.items()
    }
    for operation in context.document.operations:
        declared_materials.update(
            {
                output_id: (output.quantity, output.unit)
                for output_id, output in operation.outputs.items()
            }
        )

    for index, operation in enumerate(context.document.operations):
        kind = (operation.operation_type or operation.action).strip().lower()
        if kind not in {"split", "divide", "dividing", "reserve", "reserving"}:
            continue
        inputs = []
        for material_use in operation.inputs:
            material_id = material_use_id(material_use)
            declared_quantity, declared_unit = declared_materials.get(
                material_id,
                (None, None),
            )
            input_quantity = (
                material_use.quantity
                if isinstance(material_use, MaterialUse)
                and material_use.quantity is not None
                else declared_quantity
            )
            inputs.append(_numeric_quantity(input_quantity, declared_unit))
        outputs = [
            _numeric_quantity(output.quantity, output.unit)
            for output in operation.outputs.values()
        ]
        if len(inputs) != 1 or inputs[0] is None or not outputs or any(
            output is None for output in outputs
        ):
            continue
        source_number, source_unit = inputs[0]
        output_values = [output for output in outputs if output is not None]
        if any(unit != source_unit for _, unit in output_values):
            continue
        produced = sum((number for number, _ in output_values), Decimal(0))
        if produced != source_number:
            yield Diagnostic(
                code="RF406",
                severity=Severity.ERROR,
                path=f"/operations/{index}/outputs",
                message=(
                    f"Split quantities total {produced} {source_unit or ''} but "
                    f"the declared input is {source_number} {source_unit or ''}."
                ).strip(),
            )


def _rule_connectivity(context: ValidationContext) -> Iterable[Diagnostic]:
    document = context.document
    adjacency: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for index, operation in enumerate(document.operations):
        operation_id = _operation_key(operation, index)
        nodes.add(operation_id)
        for output_id in operation.outputs:
            material_id = f"material:{output_id}"
            nodes.add(material_id)
            adjacency[operation_id].add(material_id)
            adjacency[material_id].add(operation_id)
    for ingredient_id in document.ingredients:
        nodes.add(f"material:{ingredient_id}")
    for index, operation in enumerate(document.operations):
        operation_id = _operation_key(operation, index)
        for material_use in operation.inputs:
            material_id = f"material:{material_use_id(material_use)}"
            if material_id in nodes:
                adjacency[operation_id].add(material_id)
                adjacency[material_id].add(operation_id)

    components: list[tuple[str, ...]] = []
    remaining = set(nodes)
    while remaining:
        start = min(remaining)
        queue = [start]
        component: set[str] = set()
        while queue:
            node = queue.pop()
            if node in component:
                continue
            component.add(node)
            queue.extend(sorted(adjacency[node] - component, reverse=True))
        remaining -= component
        components.append(tuple(sorted(component)))
    if len(components) > 1:
        yield Diagnostic(
            code="RF308",
            severity=Severity.WARNING,
            path="/operations",
            message=f"Recipe graph contains {len(components)} disconnected components.",
            context={"components": [list(component) for component in components]},
        )


def _rule_provenance(context: ValidationContext) -> Iterable[Diagnostic]:
    required = (
        context.options.require_provenance
        if context.options.require_provenance is not None
        else context.options.strict
    )
    if not required:
        return
    recipe = context.document.recipe
    source = recipe.source
    has_source = source is not None and any(
        value is not None and value.strip()
        for value in (source.id, source.url, source.title, source.author)
    )
    has_source = has_source or (
        source is not None and any(note.strip() for note in source.notes)
    )
    has_recipe_provenance = any(
        any(
            value is not None and value.strip()
            for value in (
                item.source_id,
                item.path,
                item.source_text,
                item.note,
            )
        )
        for item in recipe.provenance
    )
    if not has_source and not has_recipe_provenance:
        yield Diagnostic(
            code="RF390",
            severity=Severity.ERROR,
            path="/recipe/source",
            message="Strict validation requires recipe-level source provenance.",
        )
    for ingredient_id, ingredient in sorted(context.document.ingredients.items()):
        has_ingredient_provenance = any(
            any(
                value is not None and value.strip()
                for value in (
                    item.source_id,
                    item.path,
                    item.source_text,
                    item.note,
                )
            )
            for item in ingredient.provenance
        )
        if (
            not (ingredient.source_text and ingredient.source_text.strip())
            and not has_ingredient_provenance
        ):
            yield Diagnostic(
                code="RF391",
                severity=Severity.ERROR,
                path=f"/ingredients/{_escape(ingredient_id)}",
                message=(
                    f"Strict validation requires provenance or source_text for "
                    f"ingredient {ingredient_id!r}."
                ),
            )


def _rule_subrecipes(context: ValidationContext) -> Iterable[Diagnostic]:
    document = context.document
    dependency_paths: dict[tuple[str, str], str] = {}
    scope_rules: tuple[ValidationRule, ...] = (
        _rule_identifiers,
        _rule_references,
        _rule_operation_shape,
        _rule_material_usage,
        _rule_cycles,
        _rule_temporal,
        _rule_split_quantities,
        _rule_connectivity,
    )

    for key, subrecipe in sorted(document.subrecipes.items()):
        escaped_key = _escape(key)
        prefix = f"/subrecipes/{escaped_key}"
        if key != subrecipe.id:
            yield Diagnostic(
                code="RF214",
                severity=Severity.ERROR,
                path=f"{prefix}/id",
                message=(
                    f"Subrecipe mapping key {key!r} must match its id "
                    f"{subrecipe.id!r}."
                ),
                suggestions=(key,),
            )
        if not subrecipe.output_ids:
            yield Diagnostic(
                code="RF215",
                severity=Severity.ERROR,
                path=f"{prefix}/output_ids",
                message="A subrecipe must explicitly expose at least one output.",
            )
        declared_outputs = {
            output_id
            for operation in subrecipe.operations
            for output_id in operation.outputs
        }
        for output_index, output_id in enumerate(subrecipe.output_ids):
            if output_id not in declared_outputs:
                yield Diagnostic(
                    code="RF215",
                    severity=Severity.ERROR,
                    path=f"{prefix}/output_ids/{output_index}",
                    message=(
                        f"Subrecipe output {output_id!r} is not produced "
                        "inside its graph boundary."
                    ),
                    suggestions=tuple(sorted(declared_outputs)),
                )

        scoped_document = subrecipe_document(
            subrecipe,
            available_subrecipes=document.subrecipes,
        )
        scoped_context = ValidationContext(
            document=scoped_document,
            options=context.options.model_copy(
                update={
                    "strict": False,
                    "require_provenance": False,
                }
            ),
        )
        for rule in scope_rules:
            for diagnostic in rule(scoped_context):
                path = f"{prefix}{diagnostic.path}" if diagnostic.path else prefix
                related_paths = tuple(
                    f"{prefix}{related_path}"
                    for related_path in diagnostic.related_paths
                )
                yield diagnostic.model_copy(
                    update={
                        "path": path,
                        "related_paths": related_paths,
                    }
                )

        for operation_index, operation in enumerate(subrecipe.operations):
            if operation.subrecipe:
                dependency_paths[(key, operation.subrecipe.id)] = (
                    f"{prefix}/operations/{operation_index}/subrecipe/id"
                )

    dependencies = {
        key: {
            target
            for source, target in dependency_paths
            if source == key and target in document.subrecipes
        }
        for key in document.subrecipes
    }
    state: dict[str, int] = {}
    stack: list[str] = []
    reported_cycles: set[tuple[str, ...]] = set()

    def visit(identifier: str) -> None:
        state[identifier] = 1
        stack.append(identifier)
        for dependency in sorted(dependencies[identifier]):
            if state.get(dependency, 0) == 0:
                visit(dependency)
            elif state.get(dependency) == 1:
                cycle_start = stack.index(dependency)
                cycle = (*stack[cycle_start:], dependency)
                reported_cycles.add(cycle)
        stack.pop()
        state[identifier] = 2

    for identifier in sorted(dependencies):
        if state.get(identifier, 0) == 0:
            visit(identifier)
    for cycle in sorted(reported_cycles):
        source, target = cycle[-2:]
        yield Diagnostic(
            code="RF309",
            severity=Severity.ERROR,
            path=dependency_paths[(source, target)],
            message=f"Recursive subrecipe cycle detected: {' -> '.join(cycle)}.",
            related_paths=tuple(
                dependency_paths[(left, right)]
                for left, right in pairwise(cycle)
            ),
        )


DEFAULT_RULES: tuple[ValidationRule, ...] = (
    _rule_identifiers,
    _rule_references,
    _rule_operation_shape,
    _rule_material_usage,
    _rule_cycles,
    _rule_temporal,
    _rule_split_quantities,
    _rule_connectivity,
    _rule_provenance,
    _rule_subrecipes,
)


def validate(
    document: RecipeDocument,
    *,
    strict: bool = False,
    options: ValidationOptions | None = None,
    rules: tuple[ValidationRule, ...] = DEFAULT_RULES,
) -> ValidationResult:
    selected_options = options or ValidationOptions(strict=strict)
    context = ValidationContext(document=document, options=selected_options)
    diagnostics = [
        diagnostic
        for rule in rules
        for diagnostic in rule(context)
    ]
    if selected_options.warnings_as_errors:
        diagnostics = [
            diagnostic.model_copy(
                update={"severity": Severity.ERROR},
            )
            if diagnostic.severity == Severity.WARNING
            else diagnostic
            for diagnostic in diagnostics
        ]
    severity_order = {
        Severity.ERROR: 0,
        Severity.WARNING: 1,
        Severity.INFO: 2,
    }
    diagnostics.sort(
        key=lambda item: (
            severity_order[item.severity],
            item.code,
            item.path,
            item.message,
        )
    )
    return ValidationResult(diagnostics=tuple(diagnostics))
