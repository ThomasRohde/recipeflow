from dataclasses import dataclass
from typing import Literal

from recipeflow.models.layout import TextStyle


@dataclass(frozen=True)
class LayoutTheme:
    name: Literal["classic", "modern"]
    background: str
    guide: str
    flow: str
    text: str
    muted_text: str
    operation_fill: str
    operation_stroke: str
    setup_fill: str
    setup_stroke: str
    material_fill: str
    material_stroke: str
    final_fill: str
    final_stroke: str
    grid: str
    segment_link: str
    table_background: str
    title_style: TextStyle
    label_style: TextStyle
    quantity_style: TextStyle
    operation_style: TextStyle
    detail_style: TextStyle


CLASSIC_THEME = LayoutTheme(
    name="classic",
    background="#fffdf9",
    guide="#eee8df",
    flow="#5d5146",
    text="#202124",
    muted_text="#66615c",
    operation_fill="#f2eadf",
    operation_stroke="#765f48",
    setup_fill="#f7f4ef",
    setup_stroke="#b8aa99",
    material_fill="#fffdf9",
    material_stroke="#b8aa99",
    final_fill="#e9f3e8",
    final_stroke="#4e7652",
    grid="#4f914d",
    segment_link="#36713a",
    table_background="#fbfaf2",
    title_style=TextStyle(font_size=27, font_weight=700, line_height=34),
    label_style=TextStyle(font_size=14, line_height=18),
    quantity_style=TextStyle(font_size=12, line_height=16, fill="#66615c"),
    operation_style=TextStyle(font_size=13, font_weight=600, line_height=17),
    detail_style=TextStyle(font_size=11, line_height=15, fill="#66615c"),
)


MODERN_THEME = LayoutTheme(
    name="modern",
    background="#f8fafc",
    guide="#dfe7ef",
    flow="#41556d",
    text="#162235",
    muted_text="#5f6f82",
    operation_fill="#e8eef8",
    operation_stroke="#526f98",
    setup_fill="#f2f5f9",
    setup_stroke="#9eacbc",
    material_fill="#ffffff",
    material_stroke="#b6c2d0",
    final_fill="#e2f4ec",
    final_stroke="#3e8064",
    grid="#526f98",
    segment_link="#365474",
    table_background="#f8fafc",
    title_style=TextStyle(
        font_family="Segoe UI",
        font_size=28,
        font_weight=700,
        line_height=35,
        fill="#162235",
    ),
    label_style=TextStyle(
        font_family="Segoe UI",
        font_size=14,
        line_height=19,
        fill="#162235",
    ),
    quantity_style=TextStyle(
        font_family="Segoe UI",
        font_size=12,
        font_weight=600,
        line_height=16,
        fill="#5f6f82",
    ),
    operation_style=TextStyle(
        font_family="Segoe UI",
        font_size=13,
        font_weight=700,
        line_height=18,
        fill="#162235",
    ),
    detail_style=TextStyle(
        font_family="Segoe UI",
        font_size=11,
        line_height=15,
        fill="#5f6f82",
    ),
)


def get_theme(name: Literal["classic", "modern"]) -> LayoutTheme:
    return MODERN_THEME if name == "modern" else CLASSIC_THEME
