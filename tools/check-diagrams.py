#!/usr/bin/env python3
"""Fail when site/img/diag-*.svg and the script's `<!-- diagrama: -->` markers differ.

Usage: python3 tools/check-diagrams.py APRESENTACAO.md site/img
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("render_diagrams", HERE / "render-diagrams.py")
rd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rd)


def problems(markdown: str, img_dir: Path) -> list:
    wanted = [name for name, _ in rd.extract(markdown)]
    have = sorted(p.name[5:-4] for p in img_dir.glob("diag-*.svg"))
    out = []
    for name in wanted:
        if name not in have:
            out.append("falta site/img/diag-%s.svg (rode make diagrams)" % name)
    for name in have:
        if name not in wanted:
            out.append("sobra diag-%s.svg sem diagrama no roteiro" % name)
    return out


def main(argv):
    md, img_dir = Path(argv[0]), Path(argv[1])
    found = problems(md.read_text(encoding="utf-8"), img_dir)
    for line in found:
        print(line, file=sys.stderr)
    if found:
        raise SystemExit(1)
    print("diagramas em dia")


if __name__ == "__main__":
    main(sys.argv[1:])
