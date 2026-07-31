from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import Field, field_serializer, field_validator

from recipeflow.models.common import (
    GRAPH_SCHEMA_VERSION,
    Ambiguity,
    DurationSpec,
    Provenance,
    PublicModel,
    Quantity,
    ResourceRequirement,
    TemperatureSpec,
)
from recipeflow.models.document import MaterialRole, RepeatSpec, SourceRef


class GraphModel(PublicModel):
    pass


class MaterialNode(GraphModel):
    kind: Literal["material"] = "material"
    id: str
    label: str
    role: MaterialRole
    quantity: str | None = None
    normalized_quantity: Quantity | None = None
    unit: str | None = None
    source_text: str | None = None
    optional: bool = False
    preparation_state: str | None = None
    temperature_state: str | None = None
    annotations: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()
    source_path: str | None = None


class SubrecipeInputBinding(GraphModel):
    input_id: str
    material_id: str
    source_path: str


class OperationNode(GraphModel):
    kind: Literal["operation"] = "operation"
    id: str
    label: str
    operation_kind: Literal["setup", "transform"]
    action: str
    target: str | None = None
    operation_type: str | None = None
    duration: str | None = None
    duration_value: DurationSpec | None = None
    temperature: str | None = None
    temperature_value: TemperatureSpec | None = None
    until: str | None = None
    repeat: RepeatSpec | None = None
    subrecipe_id: str | None = None
    subrecipe_scale: str | None = None
    subrecipe_output: str | None = None
    subrecipe_inputs: tuple[SubrecipeInputBinding, ...] = ()
    optional: bool = False
    equipment: tuple[str, ...] = ()
    resources: tuple[ResourceRequirement, ...] = ()
    notes: tuple[str, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    ambiguity: tuple[Ambiguity, ...] = ()
    source_path: str | None = None


Node = Annotated[MaterialNode | OperationNode, Field(discriminator="kind")]


class EdgeKind(StrEnum):
    CONSUMES = "consumes"
    PRODUCES = "produces"
    PRECEDES = "precedes"
    REQUIRES = "requires"
    RESERVES = "reserves"
    DISCARDS = "discards"
    OPTIONALLY_APPLIES = "optionally-applies"


class Edge(GraphModel):
    id: str
    kind: EdgeKind
    source: str
    target: str
    quantity: str | None = None
    source_path: str | None = None
    provenance: tuple[Provenance, ...] = ()


class CompiledSubrecipe(GraphModel):
    """Canonical graph boundary for one reusable recipe component."""

    id: str
    title: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    final_material_ids: tuple[str, ...]


class RecipeGraph(GraphModel):
    schema_version: Literal["recipeflow.graph/v1"] = GRAPH_SCHEMA_VERSION
    recipe_id: str
    title: str
    description: str | None = None
    source: SourceRef | None = None
    yield_text: str | None = None
    locale: str | None = None
    tags: tuple[str, ...] = ()
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    final_material_ids: tuple[str, ...]
    subrecipes: Mapping[str, CompiledSubrecipe] = Field(
        default_factory=lambda: MappingProxyType({})
    )

    @field_validator("subrecipes", mode="after")
    @classmethod
    def _freeze_subrecipes(
        cls,
        value: Mapping[str, CompiledSubrecipe],
    ) -> Mapping[str, CompiledSubrecipe]:
        return MappingProxyType(dict(value))

    @field_serializer("subrecipes")
    def _serialize_subrecipes(
        self,
        value: Mapping[str, CompiledSubrecipe],
    ) -> dict[str, CompiledSubrecipe]:
        return dict(value)
