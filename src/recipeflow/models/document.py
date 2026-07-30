from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class SourceRef(StrictModel):
    url: str | None = None
    title: str | None = None

class RecipeMetadata(StrictModel):
    id: str
    title: str
    source: SourceRef | None = None
    yield_text: str | None = Field(default=None, alias="yield")
    notes: list[str] = Field(default_factory=list)

class Ingredient(StrictModel):
    label: str
    quantity: str | None = None
    source_text: str | None = None
    optional: bool = False

class SetupAction(StrictModel):
    id: str
    action: str
    target: str | None = None
    temperature: str | None = None
    duration: str | None = None
    produces: str
    notes: list[str] = Field(default_factory=list)

class OutputDeclaration(StrictModel):
    label: str
    final: bool = False
    role: Literal["intermediate", "final", "waste", "garnish"] = "intermediate"

class RepeatSpec(StrictModel):
    count: int | None = None
    interval: str | None = None
    until: str | None = None

class Operation(StrictModel):
    id: str
    action: str
    inputs: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    outputs: dict[str, OutputDeclaration]
    duration: str | None = None
    temperature: str | None = None
    until: str | None = None
    repeat: RepeatSpec | None = None
    notes: list[str] = Field(default_factory=list)

class RecipeDocument(StrictModel):
    recipeflow: Literal[1] = 1
    recipe: RecipeMetadata
    ingredients: dict[str, Ingredient]
    setup: list[SetupAction] = Field(default_factory=list)
    operations: list[Operation]
