from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field

class GraphModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class MaterialNode(GraphModel):
    kind: Literal["material"] = "material"
    id: str
    label: str
    role: Literal["ingredient", "intermediate", "final", "waste", "garnish"]
    quantity: str | None = None

class OperationNode(GraphModel):
    kind: Literal["operation"] = "operation"
    id: str
    label: str
    operation_kind: Literal["setup", "transform"]
    action: str
    duration: str | None = None
    temperature: str | None = None
    until: str | None = None

Node = Annotated[MaterialNode | OperationNode, Field(discriminator="kind")]

class Edge(GraphModel):
    id: str
    kind: Literal["consumes", "produces", "requires"]
    source: str
    target: str

class RecipeGraph(GraphModel):
    schema_version: Literal["recipeflow.graph/v1"] = "recipeflow.graph/v1"
    recipe_id: str
    title: str
    nodes: list[Node]
    edges: list[Edge]
    final_material_ids: list[str]
