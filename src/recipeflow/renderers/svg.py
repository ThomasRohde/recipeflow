from __future__ import annotations

import hashlib
import json
from html import escape

from recipeflow.layout import get_theme
from recipeflow.models.layout import LayoutBox, RoutedPath, TabularLayout, TextBlock
from recipeflow.renderers.options import RenderOptions


def render_tabular_svg(
    layout: TabularLayout,
    options: RenderOptions | None = None,
) -> str:
    selected = options or RenderOptions(theme=layout.theme, notation=layout.notation)
    return _render_tabular_svg_window(layout, selected)


def _render_tabular_svg_window(
    layout: TabularLayout,
    options: RenderOptions,
    *,
    window_y: float = 0,
    window_height: float | None = None,
    id_suffix: str | None = None,
) -> str:
    """Render the full canvas or a vertical window with isolated DOM identifiers."""

    selected = options
    resolved_height = layout.height if window_height is None else window_height
    theme = get_theme(selected.theme)
    prefix = _document_prefix(layout)
    if id_suffix is not None:
        prefix = f"{prefix}-{id_suffix}"
    title_id = f"{prefix}-title"
    description_id = f"{prefix}-description"
    metadata_id = f"{prefix}-source-text"
    background = selected.background or (
        theme.table_background
        if layout.notation in {"compact-table", "ledger"}
        else theme.background
    )
    description = (
        f"{layout.title}. {len(layout.materials)} material flows through "
        f"{len(layout.operations)} operations in {layout.notation} notation."
    )

    output = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{_number(layout.width)}" height="{_number(resolved_height)}" '
            f'viewBox="0 {_number(window_y)} {_number(layout.width)} '
            f'{_number(resolved_height)}" '
            f'role="img" aria-labelledby="{title_id} {description_id}" '
            f'data-recipeflow-layout="{escape(layout.schema_version, quote=True)}" '
            f'data-recipeflow-notation="{escape(layout.notation, quote=True)}">'
        ),
        f'<title id="{title_id}">{escape(layout.title)} recipe flow</title>',
        f'<desc id="{description_id}">{escape(description)}</desc>',
        (
            f'<metadata id="{metadata_id}">'
            f"{escape(_source_text_json(layout))}</metadata>"
        ),
        _style(layout, selected),
        (
            f'<rect class="canvas" x="0" y="0" '
            f'width="{_number(layout.width)}" height="{_number(layout.height)}" '
            f'fill="{escape(background, quote=True)}"/>'
        ),
    ]

    for path in layout.paths:
        output.append(_render_path(path, id_suffix))
    for box in layout.boxes:
        rendered = _render_box(box, id_suffix)
        if rendered:
            output.append(rendered)
    block_by_id = {block.id: block for block in layout.text_blocks}
    rendered_text_ids: set[str] = set()
    for identifier in layout.reading_order:
        block = block_by_id.get(identifier)
        if block is not None:
            output.append(_render_text(block, id_suffix))
            rendered_text_ids.add(block.id)
    if layout.notation == "ledger":
        for block in layout.text_blocks:
            if block.id not in rendered_text_ids:
                output.append(_render_text(block, id_suffix))
    output.append("</svg>")
    return "\n".join(output) + "\n"


def _style(layout: TabularLayout, options: RenderOptions) -> str:
    theme = get_theme(options.theme)
    family = layout.text_blocks[0].style.font_fallbacks if layout.text_blocks else ()
    font_stack = ",".join(
        f'"{value}"' if " " in value else value for value in family
    )
    sheet_break_style = (
        ".sheet-break{display:none}"
        if any("sheet-break" in path.style_class.split() for path in layout.paths)
        else ""
    )
    unresolved_source_style = (
        f".unresolved-source{{fill:none;stroke:{theme.setup_stroke};stroke-width:1;"
        "stroke-dasharray:4 3}"
        if any(box.style_class == "unresolved-source" for box in layout.boxes)
        else ""
    )
    ledger_style = (
        f".ledger-entry{{fill:none;stroke:none}}"
        f".ledger-entry-head{{fill:none;stroke:none}}"
        f".ledger-consumed{{fill:none;stroke:none}}"
        f".ledger-consumed-part{{fill:{theme.ledger_part_draw_fill};stroke:none}}"
        f".ledger-produced{{fill:none;stroke:none}}"
        f".ledger-final{{fill:none;stroke:{theme.final_stroke};stroke-width:1}}"
        f".ledger-conditions{{fill:none;stroke:none}}"
        f".ledger-requires{{fill:none;stroke:{theme.ledger_hairline};stroke-width:1}}"
        f".ledger-balance{{fill:none;stroke:{theme.ledger_hairline};stroke-width:1}}"
        f".ledger-standing{{fill:none;stroke:none}}"
        f".ledger-band{{fill:none;stroke:none}}"
        f".ledger-rule{{fill:{theme.ledger_rule};stroke:none}}"
        f".ledger-hairline{{fill:{theme.ledger_hairline};stroke:none}}"
        f".sheet-break{{fill:none;stroke:{theme.setup_stroke};stroke-width:1;"
        "stroke-dasharray:6 4}"
        if layout.notation == "ledger"
        else ""
    )
    return (
        "<style>"
        f"text{{font-family:{font_stack or 'sans-serif'};fill:{theme.text}}}"
        f".guide{{fill:none;stroke:{theme.guide};stroke-width:1}}"
        f".flow{{fill:none;stroke:{theme.flow};stroke-width:3;"
        "stroke-linecap:round;stroke-linejoin:round}"
        f".setup-dependency{{fill:none;stroke:{theme.setup_stroke};"
        "stroke-width:1.5;stroke-dasharray:5 4}"
        f".op{{fill:{theme.operation_fill};stroke:{theme.operation_stroke};"
        "stroke-width:1.5}"
        f".setup{{fill:{theme.setup_fill};stroke:{theme.setup_stroke};"
        "stroke-width:1}"
        f".material-label{{fill:{theme.material_fill};stroke:{theme.material_stroke};"
        "stroke-width:1}"
        f".final-output{{fill:{theme.final_fill};stroke:{theme.final_stroke};"
        "stroke-width:2}"
        f".grid-line{{fill:none;stroke:{theme.grid};stroke-width:1}}"
        f".segment-link{{fill:none;stroke:{theme.segment_link};stroke-width:1.5;"
        "stroke-dasharray:4 3}"
        f"{sheet_break_style}"
        f"{unresolved_source_style}"
        f"{ledger_style}"
        f".grid-ingredient{{fill:{theme.table_background};stroke:{theme.grid};"
        "stroke-width:1}"
        f".grid-operation{{fill:{theme.table_background};stroke:{theme.grid};"
        "stroke-width:1.5}"
        f".grid-setup{{fill:{theme.table_background};stroke:{theme.grid};"
        "stroke-width:1.5}"
        f".grid-final{{fill:{theme.final_fill};stroke:{theme.grid};"
        "stroke-width:1.5}"
        ".ingredient,.title{fill:none;stroke:none}"
        "@media print{.canvas{fill:#fff}.guide{stroke:#ddd}}"
        "</style>"
    )


def _render_path(path: RoutedPath, id_suffix: str | None = None) -> str:
    points = " ".join(
        f"{_number(point.x)},{_number(point.y)}" for point in path.points
    )
    return (
        f'<polyline id="{escape(_windowed_id(path.id, id_suffix), quote=True)}" '
        f'class="{escape(path.style_class, quote=True)}" '
        f'points="{points}" vector-effect="non-scaling-stroke" '
        f'data-kind="{path.kind}"/>'
    )


def _render_box(box: LayoutBox, id_suffix: str | None = None) -> str:
    style_class = "op" if box.style_class == "operation" else box.style_class
    return (
        f'<rect id="{escape(_windowed_id(box.id, id_suffix), quote=True)}" '
        f'class="{escape(style_class, quote=True)}" '
        f'x="{_number(box.rect.x)}" y="{_number(box.rect.y)}" '
        f'width="{_number(box.rect.width)}" height="{_number(box.rect.height)}" '
        f'rx="{_number(box.corner_radius)}" vector-effect="non-scaling-stroke"/>'
    )


def _render_text(block: TextBlock, id_suffix: str | None = None) -> str:
    attributes = [
        f'id="{escape(_windowed_id(block.id, id_suffix), quote=True)}"',
        f'data-role="{block.role}"',
        f'font-size="{_number(block.style.font_size)}"',
        f'font-weight="{block.style.font_weight}"',
        f'fill="{escape(block.style.fill, quote=True)}"',
        'xml:space="preserve"',
        f'aria-label="{escape(block.source_text, quote=True)}"',
    ]
    if block.rotation:
        center_x = block.rect.x + block.rect.width / 2
        center_y = block.rect.y + block.rect.height / 2
        attributes.append(
            f'transform="rotate({block.rotation} '
            f'{_number(center_x)} {_number(center_y)})"'
        )
    lines = "".join(
        (
            f'<tspan x="{_number(line.x)}" dy="0" '
            f'y="{_number(line.baseline_y)}">{escape(line.text)}</tspan>'
        )
        for line in block.lines
    )
    return f"<text {' '.join(attributes)}>{lines}</text>"


def _source_text_json(layout: TabularLayout) -> str:
    payload = {
        "notation": layout.notation,
        "reading_order": list(layout.reading_order),
        "text": {
            block.id: block.source_text
            for block in layout.text_blocks
        },
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _document_prefix(layout: TabularLayout) -> str:
    seed = (
        f"{layout.schema_version}\0{layout.notation}\0{layout.title}\0"
        f"{layout.width:.3f}\0{layout.height:.3f}"
    )
    return f"rf-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _windowed_id(identifier: str, suffix: str | None) -> str:
    return identifier if suffix is None else f"{identifier}-{suffix}"


def _number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
