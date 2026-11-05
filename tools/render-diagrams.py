#!/usr/bin/env python3
"""Render the Mermaid blocks of a Markdown file into SVG files with the ARTESP theme.

Usage: python3 tools/render-diagrams.py APRESENTACAO.md site/img [--chrome google-chrome]

Each ```mermaid fence must be preceded by a line `<!-- diagrama: <name> -->`; the SVG is written to
`<out dir>/diag-<name>.svg`. The Markdown is never changed: the theme is injected only at render time, so GitHub
keeps rendering the blocks with Mermaid's default theme. Rendering uses the vendored `tools/vendor/mermaid.min.js`
inside headless Chrome; no network access is needed.
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MERMAID_JS = HERE / "vendor" / "mermaid.min.js"
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")

THEME = {
    "theme": "base",
    "themeVariables": {
        "fontFamily": "Arial, Helvetica, sans-serif",
        "fontSize": "16px",
        "primaryColor": "#F4F4F4",
        "primaryTextColor": "#141414",
        "primaryBorderColor": "#141414",
        "secondaryColor": "#FFFFFF",
        "secondaryTextColor": "#141414",
        "secondaryBorderColor": "#6E6E6E",
        "tertiaryColor": "#FFFFFF",
        "tertiaryTextColor": "#141414",
        "tertiaryBorderColor": "#B0B0B0",
        "lineColor": "#141414",
        "textColor": "#141414",
        "background": "#FFFFFF",
        "mainBkg": "#F4F4F4",
        "nodeBorder": "#141414",
        "clusterBkg": "#FFFFFF",
        "clusterBorder": "#B0B0B0",
        "titleColor": "#141414",
        "edgeLabelBackground": "#FFFFFF",
        "actorBkg": "#F4F4F4",
        "actorBorder": "#141414",
        "actorTextColor": "#141414",
        "actorLineColor": "#6E6E6E",
        "signalColor": "#141414",
        "signalTextColor": "#141414",
        "labelBoxBkgColor": "#FFFFFF",
        "labelBoxBorderColor": "#E41C2E",
        "labelTextColor": "#141414",
        "loopTextColor": "#141414",
        "noteBkgColor": "#FFF4F5",
        "noteBorderColor": "#E41C2E",
        "noteTextColor": "#141414",
        "activationBkgColor": "#E2E2E2",
        "activationBorderColor": "#141414",
        "cScale0": "#E41C2E", "cScaleLabel0": "#FFFFFF",
        "cScale1": "#141414", "cScaleLabel1": "#FFFFFF",
        "cScale2": "#6E6E6E", "cScaleLabel2": "#FFFFFF",
        "cScale3": "#B0B0B0", "cScaleLabel3": "#141414",
        "cScale4": "#E2E2E2", "cScaleLabel4": "#141414",
        "cScale5": "#FFFFFF", "cScaleLabel5": "#141414",
        "cScale6": "#E2E2E2", "cScaleLabel6": "#141414",
        "cScale7": "#D6D6D6", "cScaleLabel7": "#141414",
        "cScalePeer0": "#B8101F", "cScalePeer1": "#000000", "cScalePeer2": "#4A4A4A", "cScalePeer3": "#8A8A8A",
        "cScalePeer4": "#B0B0B0", "cScalePeer5": "#6E6E6E", "cScalePeer6": "#B0B0B0", "cScalePeer7": "#B0B0B0",
        "git0": "#E41C2E", "git1": "#141414", "git2": "#6E6E6E", "git3": "#B0B0B0",
        "git4": "#E2E2E2", "git5": "#F4F4F4", "git6": "#F9C8CD", "git7": "#D6D6D6",
    },
    "mindmap": {"padding": 12},
    "flowchart": {"htmlLabels": False, "padding": 12},
    "sequence": {"useMaxWidth": False},
}


def extract(markdown: str):
    """Return [(name, code)] for every ```mermaid fence, each preceded by its marker line."""
    lines = markdown.split("\n")
    blocks, seen, i = [], set(), 0
    while i < len(lines):
        if lines[i].strip() == "```mermaid":
            prev = lines[i - 1].strip() if i > 0 else ""
            m = re.match(r"<!--\s*diagrama:\s*(\S+)\s*-->$", prev)
            if not m:
                raise SystemExit("bloco mermaid sem '<!-- diagrama: nome -->' na linha anterior (linha %d)" % (i + 1))
            name = m.group(1)
            if not NAME_RE.match(name):
                raise SystemExit("nome de diagrama inválido: %r (use letras minúsculas, dígitos e hífen)" % name)
            if name in seen:
                raise SystemExit("nome de diagrama repetido: %s" % name)
            seen.add(name)
            j = i + 1
            code = []
            while j < len(lines) and lines[j].strip() != "```":
                code.append(lines[j])
                j += 1
            if j >= len(lines):
                raise SystemExit("bloco mermaid sem fechamento (linha %d)" % (i + 1))
            blocks.append((name, "\n".join(code) + "\n"))
            i = j
        i += 1
    return blocks


def page(blocks, mermaid_js_path: Path) -> str:
    """The HTML page that renders every block and leaves the results in <pre id="result">."""
    return "\n".join([
        '<!doctype html><html><head><meta charset="utf-8"><title>render</title></head><body>',
        '<script src="file://%s"></script>' % mermaid_js_path,
        "<script>",
        "const CONFIG = %s;" % json.dumps(THEME),
        "const BLOCKS = %s;" % json.dumps(blocks),
        "(async () => {",
        "  mermaid.initialize(Object.assign({startOnLoad: false, securityLevel: 'loose'}, CONFIG));",
        "  const out = [];",
        "  for (const [name, code] of BLOCKS) {",
        "    try { const r = await mermaid.render('d_' + name.replace(/-/g, '_'), code); out.push({name, ok: true, svg: r.svg}); }",
        "    catch (e) { out.push({name, ok: false, err: String(e && e.message || e)}); }",
        "  }",
        "  const pre = document.createElement('pre'); pre.id = 'result'; pre.textContent = JSON.stringify(out);",
        "  document.body.appendChild(pre); document.title = 'DONE';",
        "})();",
        "</script></body></html>",
    ])


def collect(dom: str) -> dict:
    """Read the results out of the dumped DOM; stop on the first diagram that failed."""
    m = re.search(r'<pre id="result">(.*?)</pre>', dom, re.S)
    if not m:
        raise SystemExit("o Chrome não concluiu a renderização (sem <pre id=\"result\">); "
                         "confira o mermaid.min.js ou aumente o orçamento de tempo")
    results = json.loads(html.unescape(m.group(1)))
    svgs = {}
    for r in results:
        if not r["ok"]:
            raise SystemExit("diagrama %s: %s" % (r["name"], r["err"]))
        svgs[r["name"]] = r["svg"]
    return svgs


def clean_svg(name: str, svg: str) -> str:
    """Give the SVG a stable id and the XML namespace so it works as a standalone <img> source."""
    m = re.match(r'<svg[^>]*\bid="([^"]+)"', svg)
    if m:
        # The generated id prefixes every derived id (markers, clip paths) and every reference to them.
        old = m.group(1)
        svg = re.sub(r'(?<![\w-])%s(?=[\w-]*)' % re.escape(old), "diag-%s" % name, svg)
    if 'xmlns="http://www.w3.org/2000/svg"' not in svg:
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg.strip()


def render(blocks, mermaid_js_path=MERMAID_JS, chrome="google-chrome", budget_ms=30000) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "render.html"
        src.write_text(page(blocks, mermaid_js_path), encoding="utf-8")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
               "--virtual-time-budget=%d" % budget_ms, "--dump-dom", "file://%s" % src]
        try:
            dom = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180).stdout
        except FileNotFoundError:
            raise SystemExit("%s não encontrado; instale o Google Chrome ou passe --chrome <binário>" % chrome)
        except subprocess.CalledProcessError as e:
            raise SystemExit("o Chrome falhou (%d): %s" % (e.returncode, e.stderr[-500:]))
    return {name: clean_svg(name, svg) for name, svg in collect(dom).items()}


def main(argv):
    chrome = "google-chrome"
    args = list(argv)
    if "--chrome" in args:
        k = args.index("--chrome")
        chrome = args[k + 1]
        del args[k:k + 2]
    if len(args) != 2:
        raise SystemExit(__doc__)
    md, out_dir = Path(args[0]), Path(args[1])
    blocks = extract(md.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, svg in render(blocks, chrome=chrome).items():
        (out_dir / ("diag-%s.svg" % name)).write_text(svg + "\n", encoding="utf-8")
        print("diag-%s.svg" % name)
    print("%d diagramas em %s" % (len(blocks), out_dir))


if __name__ == "__main__":
    main(sys.argv[1:])
