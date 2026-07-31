from dataclasses import dataclass
from typing import Literal

from recipeflow.layout import LayoutOptions


@dataclass(frozen=True)
class RenderOptions:
    notation: str = "flow"
    theme: Literal["classic", "modern"] = "classic"
    width: float | None = None
    scale: float = 2.0
    minimum_font_size: float = 10
    base_font_size: float = 14
    line_height: float = 1.3
    outer_margin: float | None = None
    ingredient_label_width: float | None = None
    operation_column_minimum_width: float = 82
    operation_column_maximum_width: float = 176
    setup_card_minimum_width: float = 176
    orientation: Literal["auto", "landscape", "portrait"] = "auto"
    operation_label_orientation: Literal["auto", "horizontal", "vertical"] = "auto"
    show_intermediate_labels: bool = True
    show_source_quantities: bool = True
    show_normalized_quantities: bool = False
    show_provenance: bool = False
    wrap_mode: Literal["word", "grapheme"] = "word"
    allow_ellipsis: bool = False
    dpi: int = 144
    background: str | None = None
    safe_margin: float = 24
    page_size: Literal["auto", "A4", "letter"] = "auto"
    print_mode: bool = False

    def __post_init__(self) -> None:
        if self.width is not None and self.width <= 0:
            raise ValueError("width must be greater than zero")
        if self.scale <= 0:
            raise ValueError("scale must be greater than zero")
        if self.dpi <= 0:
            raise ValueError("dpi must be greater than zero")
        if self.safe_margin < 0:
            raise ValueError("safe_margin cannot be negative")
        if self.outer_margin is not None and self.outer_margin < 0:
            raise ValueError("outer_margin cannot be negative")
        if self.minimum_font_size <= 0:
            raise ValueError("minimum_font_size must be greater than zero")
        if self.base_font_size < self.minimum_font_size:
            raise ValueError("base_font_size cannot be smaller than minimum_font_size")
        if self.line_height < 1:
            raise ValueError("line_height must be at least 1")
        if (
            self.operation_column_minimum_width <= 0
            or self.operation_column_maximum_width
            < self.operation_column_minimum_width
        ):
            raise ValueError("operation column width limits are invalid")
        if self.setup_card_minimum_width <= 0:
            raise ValueError("setup_card_minimum_width must be greater than zero")
        if self.ingredient_label_width is not None and self.ingredient_label_width <= 0:
            raise ValueError("ingredient_label_width must be greater than zero")
        if not self.show_source_quantities and not self.show_normalized_quantities:
            raise ValueError("at least one quantity representation must be visible")
    def to_layout_options(self) -> LayoutOptions:
        preferred_width = self.width
        if preferred_width is None:
            page_widths = {
                "A4": (794.0, 1123.0),
                "letter": (816.0, 1056.0),
            }
            if self.page_size in page_widths:
                portrait_width, landscape_width = page_widths[self.page_size]
                preferred_width = (
                    landscape_width
                    if self.orientation == "landscape"
                    else portrait_width
                )
            elif self.print_mode:
                preferred_width = 794
            elif self.orientation == "portrait":
                preferred_width = 900
            elif self.orientation == "landscape":
                preferred_width = 1400
        return LayoutOptions(
            notation=self.notation,
            preferred_width=preferred_width,
            theme=self.theme,
            operation_label_orientation=self.operation_label_orientation,
            safe_margin=self.outer_margin
            if self.outer_margin is not None
            else self.safe_margin,
            ingredient_label_width=self.ingredient_label_width,
            max_ingredient_width=self.ingredient_label_width or 320,
            min_operation_width=self.operation_column_minimum_width,
            max_operation_width=self.operation_column_maximum_width,
            min_setup_card_width=self.setup_card_minimum_width,
            minimum_font_size=self.minimum_font_size,
            base_font_size=self.base_font_size,
            line_height=self.line_height,
            show_intermediate_labels=self.show_intermediate_labels,
            show_source_quantities=self.show_source_quantities,
            show_normalized_quantities=self.show_normalized_quantities,
            show_provenance=self.show_provenance,
            wrap_mode=self.wrap_mode,
            allow_ellipsis=self.allow_ellipsis,
        )

    def raster_dimensions(
        self,
        layout_width: float,
        layout_height: float,
    ) -> tuple[int, int]:
        """Resolve integer axes without shrinking below the measured layout."""

        target_width = max(self.width or layout_width, layout_width)
        uniform_scale = self.scale * target_width / layout_width
        return (
            round(layout_width * uniform_scale),
            round(layout_height * uniform_scale),
        )
