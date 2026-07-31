from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from recipeflow.models.common import (
    DOCUMENT_SCHEMA_VERSION,
    Ambiguity,
    DurationSpec,
    Provenance,
    PublicModel,
    Quantity,
    ResourceRequirement,
    TemperatureSpec,
)


class StrictModel(PublicModel):
    """Backward-compatible name for the original strict document base."""


class MaterialRole(StrEnum):
    INGREDIENT = "ingredient"
    INTERMEDIATE = "intermediate"
    FINAL = "final"
    GARNISH = "garnish"
    WASTE = "waste"
    RESERVED = "reserved"
    OPTIONAL = "optional"


class SourceRef(StrictModel):
    id: str | None = None
    url: str | None = None
    title: str | None = None
    author: str | None = None
    retrieved_at: str | None = None
    notes: tuple[str, ...] = ()


class RecipeMetadata(StrictModel):
    id: str | None = None
    title: str
    description: str | None = None
    source: SourceRef | None = None
    author: str | None = None
    yield_text: str | None = Field(default=None, alias="yield")
    locale: str | None = None
    notes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    allow_multiple_outputs: bool = False
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()


QuantityValue = str | Quantity
DurationValue = str | DurationSpec
TemperatureValue = str | TemperatureSpec


class Ingredient(StrictModel):
    label: str
    quantity: QuantityValue | None = None
    unit: str | None = None
    source_text: str | None = None
    role: MaterialRole = MaterialRole.INGREDIENT
    optional: bool = False
    preparation_state: str | None = None
    temperature_state: str | None = None
    annotations: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()


class MaterialUse(StrictModel):
    material: str
    quantity: QuantityValue | None = None
    optional: bool = False
    reserve: bool = False
    from_reserve: bool = False
    source_text: str | None = None
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()


class SetupAction(StrictModel):
    id: str | None = None
    action: str
    label: str | None = None
    target: str | None = None
    temperature: TemperatureValue | None = None
    duration: DurationValue | None = None
    produces: str | None = None
    requires: tuple[str, ...] = ()
    equipment: tuple[str, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    notes: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()


class OutputDeclaration(StrictModel):
    label: str
    final: bool = False
    role: MaterialRole = MaterialRole.INTERMEDIATE
    quantity: QuantityValue | None = None
    unit: str | None = None
    source_text: str | None = None
    optional: bool = False
    shareable: bool = False
    preparation_state: str | None = None
    temperature_state: str | None = None
    annotations: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()


class RepeatSpec(StrictModel):
    count: int | None = None
    interval: DurationValue | None = None
    until: str | None = None


class SubrecipeRef(StrictModel):
    id: str
    scale: str | None = None
    output: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict)


class Operation(StrictModel):
    id: str | None = None
    action: str
    label: str | None = None
    operation_type: str | None = None
    inputs: tuple[str | MaterialUse, ...] = ()
    requires: tuple[str, ...] = ()
    precedes: tuple[str, ...] = ()
    outputs: dict[str, OutputDeclaration]
    equipment: tuple[str, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    duration: DurationValue | None = None
    temperature: TemperatureValue | None = None
    until: str | None = None
    completion_criteria: str | None = None
    repeat: RepeatSpec | None = None
    optional: bool = False
    subrecipe: SubrecipeRef | None = None
    notes: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()


class Subrecipe(StrictModel):
    id: str
    title: str
    ingredients: dict[str, Ingredient] = Field(default_factory=dict)
    setup: tuple[SetupAction, ...] = ()
    operations: tuple[Operation, ...] = ()
    output_ids: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


class RecipeDocument(StrictModel):
    schema_version: Literal["recipeflow.document/v1"] = DOCUMENT_SCHEMA_VERSION
    recipeflow: Literal[1] = 1
    recipe: RecipeMetadata
    ingredients: dict[str, Ingredient]
    setup: tuple[SetupAction, ...] = ()
    operations: tuple[Operation, ...]
    subrecipes: dict[str, Subrecipe] = Field(default_factory=dict)


def material_use_id(value: str | MaterialUse) -> str:
    return value if isinstance(value, str) else value.material


def quantity_text(value: QuantityValue | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return value.source_text


def duration_text(value: DurationValue | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return value.source_text


def temperature_text(value: TemperatureValue | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return value.source_text


def subrecipe_document(
    subrecipe: Subrecipe,
    *,
    available_subrecipes: dict[str, Subrecipe] | None = None,
) -> RecipeDocument:
    """Project one reusable component into an independently valid recipe scope."""

    exposed = set(subrecipe.output_ids)
    operations = tuple(
        operation.model_copy(
            update={
                "outputs": {
                    output_id: (
                        output.model_copy(
                            update={
                                "final": True,
                                "role": MaterialRole.FINAL,
                            }
                        )
                        if output_id in exposed
                        else output
                    )
                    for output_id, output in operation.outputs.items()
                }
            }
        )
        for operation in subrecipe.operations
    )
    return RecipeDocument(
        recipe=RecipeMetadata(
            id=subrecipe.id,
            title=subrecipe.title,
            notes=subrecipe.notes,
            allow_multiple_outputs=len(exposed) > 1,
        ),
        ingredients=subrecipe.ingredients,
        setup=subrecipe.setup,
        operations=operations,
        subrecipes=available_subrecipes or {},
    )
