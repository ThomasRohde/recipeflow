from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LayoutOptions:
    preferred_width: float | None = None
    theme: Literal["classic", "modern"] = "classic"
    operation_label_orientation: Literal["auto", "horizontal", "vertical"] = "auto"
    safe_margin: float = 24
    ingredient_label_width: float | None = None
    max_ingredient_width: float = 320
    min_setup_card_width: float = 176
    max_setup_card_width: float = 360
    min_operation_width: float = 82
    max_operation_width: float = 176
    max_material_label_width: float = 190
    minimum_row_height: float = 54
    horizontal_gap: float = 16
    minimum_font_size: float = 10
    base_font_size: float = 14
    line_height: float = 1.3
    show_intermediate_labels: bool = True
    show_source_quantities: bool = True
    show_normalized_quantities: bool = False
    show_provenance: bool = False
    wrap_mode: Literal["word", "grapheme"] = "word"
    allow_ellipsis: bool = False
