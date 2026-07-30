from typing import Literal

from pydantic import BaseModel, ConfigDict


class LayoutModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Lane(LayoutModel):
    index: int
    y: float
    initial_material_id: str | None = None


class MaterialSegment(LayoutModel):
    material_id: str
    label: str
    quantity: str | None = None
    role: Literal["ingredient", "intermediate", "final", "waste", "garnish"]
    lane: int
    x1: float
    x2: float
    y: float
    show_left_label: bool = False
    show_inline_label: bool = False


class OperationCell(LayoutModel):
    operation_id: str
    label: str
    action: str
    x: float
    y1: float
    y2: float
    input_material_ids: tuple[str, ...] = ()
    output_material_ids: tuple[str, ...] = ()
    duration: str | None = None
    temperature: str | None = None
    until: str | None = None


class SetupCard(LayoutModel):
    operation_id: str
    label: str
    detail: str | None = None
    x: float
    width: float


class TabularLayout(LayoutModel):
    schema_version: Literal["recipeflow.tabular-layout/v1"] = (
        "recipeflow.tabular-layout/v1"
    )
    title: str
    width: float
    height: float
    label_width: float
    header_height: float
    setup_height: float
    row_height: float
    lanes: tuple[Lane, ...]
    materials: tuple[MaterialSegment, ...]
    operations: tuple[OperationCell, ...]
    setup: tuple[SetupCard, ...] = ()
    final_material_ids: tuple[str, ...] = ()
