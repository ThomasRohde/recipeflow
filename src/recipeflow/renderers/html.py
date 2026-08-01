from html import escape
from itertools import pairwise

from recipeflow.models.layout import TabularLayout
from recipeflow.renderers.options import RenderOptions
from recipeflow.renderers.svg import _render_tabular_svg_window, render_tabular_svg


def render_tabular_html(
    layout: TabularLayout,
    options: RenderOptions | None = None,
) -> str:
    selected = options or RenderOptions(theme=layout.theme, notation=layout.notation)
    windows = (
        _sheet_windows(layout) or ((0.0, layout.height),)
        if selected.print_mode
        else ()
    )
    if windows:
        rendered_sheets = []
        for index, (window_y, window_height) in enumerate(windows, start=1):
            svg = _render_tabular_svg_window(
                layout,
                selected,
                window_y=window_y,
                window_height=window_height,
                id_suffix=f"sheet-{index}",
            ).replace(
                'role="img"',
                'role="img" aria-hidden="true" focusable="false"',
                1,
            )
            rendered_sheets.append(
                f'<section class="sheet" data-sheet="{index}">{svg}</section>'
            )
        rendered_canvas = "".join(rendered_sheets)
    else:
        svg = render_tabular_svg(layout, selected).replace(
            'role="img"',
            'role="img" aria-hidden="true" focusable="false"',
            1,
        )
        rendered_canvas = svg
    blocks = {block.id: block for block in layout.text_blocks}
    semantic_items = "".join(
        f'<li data-role="{blocks[identifier].role}">'
        f"{escape(blocks[identifier].source_text)}</li>"
        for identifier in layout.reading_order
        if identifier in blocks
    )
    screen_body = "0" if selected.print_mode else "24px"
    screen_shadow = "none" if selected.print_mode else "0 8px 30px #0002"
    screen_radius = "0" if selected.print_mode else "12px"
    sheet_css = (
        ".sheet{overflow:hidden;background:white}"
        ".sheet+.sheet{break-before:page;page-break-before:always}"
        if windows
        else ""
    )
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(layout.title)} recipe flow</title>"
        "<style>"
        f"html{{background:#f3efe8}}body{{margin:0;padding:{screen_body}}}"
        "main{max-width:100%;overflow:auto;background:white;"
        f"box-shadow:{screen_shadow};border-radius:{screen_radius}}}"
        "svg{display:block;max-width:none}"
        f"{sheet_css}"
        ".semantic{position:absolute;width:1px;height:1px;padding:0;margin:-1px;"
        "overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}"
        "@media print{html{background:white}body{padding:0}"
        "main{box-shadow:none;border-radius:0;overflow:visible}}"
        "</style></head><body>"
        f'<section class="semantic" aria-label="{escape(layout.title, quote=True)}">'
        f"<h1>{escape(layout.title)}</h1><ol>{semantic_items}</ol></section>"
        f"<main>{rendered_canvas}</main></body></html>\n"
    )


def _sheet_windows(layout: TabularLayout) -> tuple[tuple[float, float], ...]:
    breaks: set[float] = set()
    for path in layout.paths:
        if "sheet-break" not in path.style_class.split() or not path.points:
            continue
        y_values = [point.y for point in path.points]
        if max(y_values) - min(y_values) > 0.01:
            continue
        y = y_values[0]
        if 0 < y < layout.height:
            breaks.add(y)
    if not breaks:
        return ()
    boundaries = [0.0, *sorted(breaks), layout.height]
    return tuple(
        (start, end - start)
        for start, end in pairwise(boundaries)
    )
