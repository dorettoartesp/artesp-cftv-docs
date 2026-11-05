#!/usr/bin/env python3
"""Fail when site/img/diag-*.svg and the script's `<!-- diagrama: -->` markers differ.

Usage: python3 tools/check-diagrams.py APRESENTACAO.md [RESUMO.md ...] site/img
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("render_diagrams", HERE / "render-diagrams.py")
rd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rd)


def problems(markdown, img_dir: Path) -> list:
    """`markdown`: one script or a list of scripts; a name used in two scripts must carry the same code."""
    scripts = [markdown] if isinstance(markdown, str) else list(markdown)
    code = {}
    out = []
    for text in scripts:
        for name, block in rd.extract(text):
            if name in code and code[name].strip() != block.strip():
                out.append("diagrama %s difere entre os roteiros (mesmo nome, código diferente)" % name)
            code.setdefault(name, block)
    wanted = list(code)
    have = sorted(p.name[5:-4] for p in img_dir.glob("diag-*.svg"))
    for name in wanted:
        if name not in have:
            out.append("falta site/img/diag-%s.svg (rode make diagrams)" % name)
    for name in have:
        if name not in wanted:
            out.append("sobra diag-%s.svg sem diagrama no roteiro" % name)
    return out


def main(argv):
    """check-diagrams.py ROTEIRO.md [OUTRO.md ...] site/img"""
    img_dir = Path(argv[-1])
    texts = [Path(a).read_text(encoding="utf-8") for a in argv[:-1]]
    found = problems(texts, img_dir)
    for line in found:
        print(line, file=sys.stderr)
    if found:
        raise SystemExit(1)
    print("diagramas em dia")


if __name__ == "__main__":
    main(sys.argv[1:])
