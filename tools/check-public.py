#!/usr/bin/env python3
"""Fail when text that must never go public appears in the given files or directories.

Usage: python3 tools/check-public.py [--extra-file forbidden.local] PATH...

The built-in pattern covers private IPv4 addresses, RTSP URLs with credentials, publication-key prefixes and
`token=`/`senha:`/`password=` assignments, case-insensitively. Terms that are themselves confidential (internal
host names, domain suffixes) never live in this repository: they come from an ignored file (`forbidden.local`,
one term per line, `#` comments allowed) or from the `FORBIDDEN_EXTRA` environment variable (`|`-separated),
which the CI reads from a repository secret.
"""
import os
import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r"(\b10\.[0-9]+\.[0-9]+\.[0-9]+\b"
    r"|\b192\.168\.[0-9]+\.[0-9]+\b"
    r"|\b172\.(1[6-9]|2[0-9]|3[01])\.[0-9]+\.[0-9]+\b"
    r"|rtsp://[^\s\"]*@"
    r"|cftvpub_"
    r"|token[=:]"
    r"|senha[=:]"
    r"|password[=:])",
    re.IGNORECASE,
)

TEXT_SUFFIXES = {".md", ".html", ".txt", ".json", ".yml", ".yaml", ".css", ".js", ".py", ".svg"}


def pattern_with_extra(extra: str):
    """The built-in pattern plus `|`-separated extra terms, matched case-insensitively."""
    if not extra:
        return PATTERN
    return re.compile("%s|(%s)" % (PATTERN.pattern, extra), re.IGNORECASE)


def load_extra(path: Path) -> list:
    """Terms from an optional file: one per line, blank lines and `#` comments ignored."""
    if not path.is_file():
        return []
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def _files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            yield from (f for f in sorted(p.rglob("*")) if f.is_file() and f.suffix in TEXT_SUFFIXES)
        elif p.is_file():
            yield p


def problems(paths, pattern) -> list:
    """`file:line: matched text` for every line of every file that matches."""
    out = []
    for f in _files(paths):
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = pattern.search(line)
            if m:
                out.append("%s:%d: %s" % (f, n, m.group(0)))
    return out


def main(argv):
    args = list(argv)
    extra_file = Path("forbidden.local")
    if "--extra-file" in args:
        k = args.index("--extra-file")
        extra_file = Path(args[k + 1])
        del args[k:k + 2]
    if not args:
        raise SystemExit(__doc__)
    terms = load_extra(extra_file) + [t for t in os.environ.get("FORBIDDEN_EXTRA", "").split("|") if t]
    pattern = pattern_with_extra("|".join(re.escape(t) for t in terms))
    found = problems(args, pattern)
    for line in found:
        print(line, file=sys.stderr)
    if found:
        raise SystemExit("texto proibido para publicação (%d ocorrência(s))" % len(found))
    print("texto público em ordem (%d termo(s) extra)" % len(terms))


if __name__ == "__main__":
    main(sys.argv[1:])
