#!/usr/bin/env python3
"""Concatenate the deck's slides into `site/index.html` on top of `site/template.html`.

Usage: python3 tools/build-site.py <deck dir> [site/index.html]

A slide is `deck/slides/<id>.html`: one `<section id="<id>" data-transition="fade" style="...">` of 1920×1080
with inline styles. `<x-icon name="..." style="..."></x-icon>` becomes an inline Feather-style SVG. HTML comments
are dropped. The order comes from `deck/deck.json`.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ICONS = {
    "Database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    "Chart": '<path d="M18 20V10M12 20V4M6 20v-6"/>',
    "Link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "Settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1l2.1-2.1M17 7l2.1-2.1"/>',
    "Lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "Clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "Users": '<circle cx="9" cy="7" r="4"/><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "Activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "Verified": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>',
    "Road": '<path d="M4 21 9 3M20 21 15 3M12 7v2M12 12v3M12 18v3"/>',
    "Code": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    "Play": '<polygon points="5 3 19 12 5 21"/>',
    "Book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    "Check": '<polyline points="20 6 9 17 4 12"/>',
    "Warning": '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "Camera": '<path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2"/>',
    "Map": '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>',
    "Mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    "Server": '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
    "Eye": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    "EyeOff": '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>',
    "Key": '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
    "Globe": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "Shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "Calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "Message": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "Layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
}


def attr(tag, name, default=None):
    m = re.search(r'\b%s="([^"]*)"' % name, tag)
    return m.group(1) if m else default


def icon(tag):
    name = attr(tag, "name", "")
    style = attr(tag, "style", "")
    body = ICONS.get(name)
    if body is None:
        raise SystemExit("ícone sem desenho: %s (acrescente em tools/build-site.py ICONS)" % name)
    return ('<svg class="ic" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="%s;flex:none">%s</svg>'
            % (style, body))


class _Balance(HTMLParser):
    """Checks that a slide's tags close in the order they open."""
    VOID = {"img", "br", "hr", "meta", "link", "line", "path", "polygon", "polyline", "circle", "ellipse", "rect"}

    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(tag)


def check_balance(sid, html):
    p = _Balance()
    p.feed(html)
    if p.stack or p.errors:
        raise SystemExit("slide %s: tags desbalanceadas — abertas sem fechar %s; fechadas fora de ordem %s"
                         % (sid, p.stack, p.errors))


def _clean_label(text):
    """Strip Mermaid shape markers: ((root)), (rounded), [square]."""
    text = text.strip()
    m = re.match(r"^[\w-]*(?:\(\((.*)\)\)|\((.*)\)|\[(.*)\])$", text)
    if m:
        return next(g for g in m.groups() if g is not None).strip()
    return text


def parse_mindmap(code):
    """A Mermaid mind map -> (root label, [(branch, [leaves])]). Depth comes from indentation."""
    lines = [line for line in code.split("\n") if line.strip()]
    if not lines or lines[0].strip() != "mindmap":
        raise SystemExit("x-groups: o bloco não é um mindmap")
    root, groups = None, []
    indents = []
    for line in lines[1:]:
        indent = len(line) - len(line.lstrip(" "))
        label = _clean_label(line)
        if root is None:
            root, indents = label, [indent]
            continue
        if indent not in indents:
            indents.append(indent)
            indents.sort()
        depth = indents.index(indent)
        if depth == 1:
            groups.append((label, []))
        elif depth >= 2 and groups:
            groups[-1][1].append(label)
    return root, groups


def groups_html(groups, style):
    """Columns of cards, one per branch, with its leaves as a list."""
    cols = len(groups) if len(groups) <= 4 else 3
    cards = []
    for title, leaves in groups:
        items = "".join("<li>%s</li>" % leaf for leaf in leaves)
        cards.append(
            '<div class="grupo" style="background:#FFFFFF;border:1px solid #E2E2E2;border-top:6px solid #E41C2E;'
            'border-radius:12px;padding:22px 26px;display:flex;flex-direction:column;gap:12px">'
            '<h3 style="font-family:\'Montserrat\', Arial, sans-serif;font-size:28px;font-weight:700">%s</h3>'
            '<ul style="font-size:23px;line-height:1.35;color:#3C3C3C;padding-left:1.1em;margin:0">%s</ul></div>'
            % (title, items))
    return ('<div class="grupos" style="%s;display:grid;grid-template-columns:repeat(%d, 1fr);gap:24px;'
            'align-content:center">%s</div>' % (style, cols, "".join(cards)))


def _script_blocks(script):
    """{name: code} for the marked ```mermaid fences of the script (same contract as render-diagrams.py)."""
    out = {}
    for m in re.finditer(r"<!--\s*diagrama:\s*(\S+)\s*-->\n```mermaid\n(.*?)```", script, re.S):
        out[m.group(1)] = m.group(2)
    return out


def groups(tag, script):
    name = attr(tag, "src", "")
    style = attr(tag, "style", "")
    blocks = _script_blocks(script or "")
    if name not in blocks:
        raise SystemExit("x-groups: não há diagrama %r no roteiro" % name)
    _root, parsed = parse_mindmap(blocks[name])
    return groups_html(parsed, style)


def convert(sid, html, script=""):
    """One slide file -> one reveal.js <section> wrapping the 1920×1080 canvas div."""
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'<x-icon\b[^>]*>\s*</x-icon>', lambda m: icon(m.group(0)), html)
    html = re.sub(r'<x-groups\b[^>]*>\s*</x-groups>', lambda m: groups(m.group(0), script), html)
    html = html.replace('<svg style="position:absolute;left:0;top:0" width="1920" height="1080"',
                        '<svg class="bg" aria-hidden="true" style="position:absolute;left:0;top:0;z-index:-1" width="1920" height="1080"')
    m = re.match(r'\s*<section\b([^>]*)>(.*)</section>\s*$', html, flags=re.S)
    if not m:
        raise SystemExit("slide %s: o arquivo deve conter um único <section> raiz" % sid)
    head, body = m.group(1), m.group(2)
    found = attr(head, "id")
    if found != sid:
        raise SystemExit("slide %s: o id da <section> é %r; deve ser igual ao nome do arquivo" % (sid, found))
    style = attr(head, "style", "")
    trans = {"push": "slide", "fade": "fade"}.get(attr(head, "data-transition", "fade"), "fade")
    return ('<section data-transition="%s" data-id="%s">\n<div class="sl" id="%s" style="%s">%s</div>\n</section>\n'
            % (trans, sid, sid, style, body.strip()))


def build(deck_dir: Path, out: Path) -> int:
    deck = json.loads((deck_dir / "deck.json").read_text(encoding="utf-8"))
    title = deck.get("title", "Apresentação")
    script_file = deck_dir.resolve().parent / "APRESENTACAO.md"
    script = script_file.read_text(encoding="utf-8") if script_file.is_file() else ""
    slides = []
    for sid in deck["order"]:
        f = deck_dir / "slides" / ("%s.html" % sid)
        if not f.is_file():
            raise SystemExit("slide %s: arquivo %s não existe" % (sid, f))
        src = f.read_text(encoding="utf-8")
        check_balance(sid, src)
        slides.append(convert(sid, src, script))
    tpl = (out.parent / "template.html").read_text(encoding="utf-8")
    page = tpl.replace("{{TITLE}}", title).replace("{{SLIDES}}", "".join(slides))
    out.write_text(page, encoding="utf-8")
    return len(slides)


def main(argv):
    deck_dir = Path(argv[0]) if argv else Path("deck")
    out = Path(argv[1]) if len(argv) > 1 else Path("site/index.html")
    n = build(deck_dir, out)
    print("%s: %d slides, %d KB" % (out, n, out.stat().st_size // 1024))


if __name__ == "__main__":
    main(sys.argv[1:])
