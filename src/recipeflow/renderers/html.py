from html import escape

from recipeflow.models.layout import TabularLayout
from recipeflow.renderers.options import RenderOptions
from recipeflow.renderers.svg import render_tabular_svg


def render_tabular_html(
    layout: TabularLayout,
    options: RenderOptions | None = None,
) -> str:
    selected = options or RenderOptions(theme=layout.theme)
    svg = render_tabular_svg(layout, selected).replace(
        'role="img"',
        'role="img" aria-hidden="true" focusable="false"',
        1,
    )
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
        ".semantic{position:absolute;width:1px;height:1px;padding:0;margin:-1px;"
        "overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}"
        "@media print{html{background:white}body{padding:0}"
        "main{box-shadow:none;border-radius:0;overflow:visible}}"
        "</style></head><body>"
        f'<section class="semantic" aria-label="{escape(layout.title, quote=True)}">'
        f"<h1>{escape(layout.title)}</h1><ol>{semantic_items}</ol></section>"
        f"<main>{svg}</main></body></html>\n"
    )
