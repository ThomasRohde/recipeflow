from html import escape
from recipeflow.models.layout import TabularLayout


def render_tabular_svg(layout: TabularLayout) -> str:
    w,h=layout.width,layout.height
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-labelledby="title desc">',
         f'<title id="title">{escape(layout.title)} recipe flow</title>',
         '<desc id="desc">Ingredients flow from left to right through preparation operations to final outputs.</desc>',
         '<style>text{font-family:Inter,Segoe UI,Arial,sans-serif;fill:#202124}.title{font-size:27px;font-weight:700}.small{font-size:12px}.label{font-size:14px}.qty{font-size:12px;fill:#666}.op{fill:#f2eadf;stroke:#765f48;stroke-width:1.5}.setup{fill:#f7f4ef;stroke:#b8aa99}.flow{stroke:#5d5146;stroke-width:3;stroke-linecap:round}.guide{stroke:#eee8df}.final{fill:#e9f3e8;stroke:#4e7652;stroke-width:2}</style>',
         f'<rect width="{w}" height="{h}" fill="#fffdf9"/>',f'<text class="title" x="24" y="42">{escape(layout.title)}</text>',
         f'<line class="guide" x1="20" y1="{layout.header_height}" x2="{w-20}" y2="{layout.header_height}"/>']
    for c in layout.setup:
        out.append(f'<rect class="setup" x="{c.x:.1f}" y="{layout.header_height+12:.1f}" width="{c.width:.1f}" height="50" rx="8"/>')
        out.append(f'<text class="label" x="{c.x+10:.1f}" y="{layout.header_height+34:.1f}">{escape(c.label)}</text>')
        if c.detail: out.append(f'<text class="qty" x="{c.x+10:.1f}" y="{layout.header_height+51:.1f}">{escape(c.detail)}</text>')
    for lane in layout.lanes:
        out.append(f'<line class="guide" x1="20" y1="{lane.y:.1f}" x2="{w-20}" y2="{lane.y:.1f}"/>')
    for m in layout.materials:
        out.append(f'<line class="flow" x1="{m.x1:.1f}" y1="{m.y:.1f}" x2="{m.x2:.1f}" y2="{m.y:.1f}"/>')
        if m.show_left_label:
            q=f'{escape(m.quantity)}  ' if m.quantity else ''
            out.append(f'<text class="label" text-anchor="end" x="{layout.label_width:.1f}" y="{m.y-3:.1f}">{q}{escape(m.label)}</text>')
        if m.show_inline_label:
            cls='final' if m.role=='final' else 'setup'
            x=min(m.x1+12,w-170)
            out.append(f'<rect class="{cls}" x="{x:.1f}" y="{m.y-16:.1f}" width="150" height="32" rx="7"/>')
            out.append(f'<text class="small" x="{x+8:.1f}" y="{m.y+4:.1f}">{escape(m.label[:24])}</text>')
    for op in layout.operations:
        hh=max(42,op.y2-op.y1); y=(op.y1+op.y2)/2-hh/2
        out.append(f'<rect class="op" x="{op.x-23:.1f}" y="{y:.1f}" width="46" height="{hh:.1f}" rx="7"/>')
        cy=y+hh/2
        out.append(f'<text class="small" text-anchor="middle" transform="rotate(-90 {op.x:.1f} {cy:.1f})" x="{op.x:.1f}" y="{cy+4:.1f}">{escape(op.action)}</text>')
        detail=' · '.join(x for x in [op.temperature,op.duration] if x)
        if detail: out.append(f'<text class="qty" text-anchor="middle" x="{op.x:.1f}" y="{y-7:.1f}">{escape(detail)}</text>')
    out.append('</svg>')
    return '\n'.join(out)+'\n'


def render_tabular_html(layout: TabularLayout) -> str:
    svg=render_tabular_svg(layout)
    return '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+escape(layout.title)+'</title><style>body{margin:0;padding:24px;background:#f3efe8}main{max-width:100%;overflow:auto;background:white;box-shadow:0 8px 30px #0002;border-radius:12px}svg{display:block;max-width:none}</style></head><body><main>'+svg+'</main></body></html>\n'
