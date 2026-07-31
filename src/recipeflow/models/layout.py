from typing import Literal

from pydantic import Field

from recipeflow.models.common import Diagnostic, PublicModel


class LayoutModel(PublicModel):
    """Immutable base for the portable tabular-layout contract."""


class Point(LayoutModel):
    x: float
    y: float


class Rect(LayoutModel):
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def contains(self, other: "Rect", tolerance: float = 0.01) -> bool:
        return (
            other.x >= self.x - tolerance
            and other.y >= self.y - tolerance
            and other.right <= self.right + tolerance
            and other.bottom <= self.bottom + tolerance
        )

    def intersects(self, other: "Rect", tolerance: float = 0.01) -> bool:
        return (
            self.x < other.right - tolerance
            and self.right > other.x + tolerance
            and self.y < other.bottom - tolerance
            and self.bottom > other.y + tolerance
        )


class Insets(LayoutModel):
    top: float = Field(default=0, ge=0)
    right: float = Field(default=0, ge=0)
    bottom: float = Field(default=0, ge=0)
    left: float = Field(default=0, ge=0)


class TextStyle(LayoutModel):
    font_family: str = "DejaVu Sans"
    font_fallbacks: tuple[str, ...] = (
        "Inter",
        "Segoe UI",
        "Arial",
        "DejaVu Sans",
        "sans-serif",
    )
    font_size: float = Field(default=14, gt=0)
    font_weight: int = Field(default=400, ge=100, le=900)
    line_height: float = Field(default=18, gt=0)
    fill: str = "#202124"


class WrappedLine(LayoutModel):
    text: str
    width: float = Field(ge=0)
    x: float
    baseline_y: float
    ascent: float = Field(ge=0)
    descent: float = Field(ge=0)


TextRole = Literal[
    "title",
    "recipe-yield",
    "ingredient-quantity",
    "ingredient-label",
    "ingredient-source",
    "ingredient-preparation",
    "ingredient-annotation",
    "ingredient-provenance",
    "setup-label",
    "setup-target",
    "setup-required-by",
    "setup-detail",
    "setup-note",
    "setup-provenance",
    "operation-action",
    "operation-input-quantity",
    "operation-detail",
    "operation-until",
    "material-label",
    "final-label",
    "annotation",
]


class TextBlock(LayoutModel):
    id: str
    role: TextRole
    source_text: str
    rect: Rect
    padding: Insets = Insets()
    lines: tuple[WrappedLine, ...]
    style: TextStyle
    horizontal_alignment: Literal["start", "center", "end"] = "start"
    vertical_alignment: Literal["top", "middle", "bottom"] = "top"
    rotation: Literal[-90, 0] = 0
    overflow: bool = False
    parent_id: str | None = None


LayoutBoxKind = Literal[
    "title",
    "ingredient",
    "setup",
    "operation",
    "material-label",
    "final-output",
    "annotation",
]


class LayoutBox(LayoutModel):
    id: str
    kind: LayoutBoxKind
    rect: Rect
    text_block_ids: tuple[str, ...] = ()
    style_class: str
    opaque: bool = True
    collision_group: str = "content"
    corner_radius: float = Field(default=7, ge=0)


class RoutedPath(LayoutModel):
    id: str
    kind: Literal["material", "setup-dependency", "guide"]
    points: tuple[Point, ...]
    style_class: str
    source_id: str | None = None
    target_ids: tuple[str, ...] = ()
    stroke_width: float = Field(default=1, gt=0)


class Lane(LayoutModel):
    index: int
    y: float
    height: float = 0
    initial_material_id: str | None = None


MaterialSegmentRole = Literal[
    "ingredient",
    "intermediate",
    "final",
    "waste",
    "garnish",
    "reserved",
    "optional",
]


class MaterialSegment(LayoutModel):
    material_id: str
    label: str
    quantity: str | None = None
    role: MaterialSegmentRole
    lane: int
    x1: float
    x2: float
    y: float
    show_left_label: bool = False
    show_inline_label: bool = False
    path_id: str | None = None
    label_box_id: str | None = None


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
    rect: Rect | None = None
    text_block_ids: tuple[str, ...] = ()
    box_ids: tuple[str, ...] = ()
    orientation: Literal["horizontal", "vertical"] = "horizontal"


class SetupCard(LayoutModel):
    operation_id: str
    label: str
    detail: str | None = None
    x: float
    width: float
    y: float = 0
    height: float = 0
    rect: Rect | None = None
    text_block_ids: tuple[str, ...] = ()
    required_by_operation_ids: tuple[str, ...] = ()


class TabularLayout(LayoutModel):
    schema_version: Literal["recipeflow.tabular-layout/v1"] = (
        "recipeflow.tabular-layout/v1"
    )
    title: str
    notation: str = Field(
        default="flow",
        pattern=r"^[a-z][a-z0-9]*(?:[-.:][a-z0-9]+)*$",
    )
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
    safe_margin: float = 20
    theme: Literal["classic", "modern"] = "classic"
    text_blocks: tuple[TextBlock, ...] = ()
    boxes: tuple[LayoutBox, ...] = ()
    paths: tuple[RoutedPath, ...] = ()
    reading_order: tuple[str, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
