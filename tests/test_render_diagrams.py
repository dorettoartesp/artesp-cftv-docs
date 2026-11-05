"""Tests of the Mermaid renderer (everything except the Chrome call)."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("render_diagrams", ROOT / "tools" / "render-diagrams.py")
rd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rd)

MD = """# Doc

<!-- diagrama: um -->
```mermaid
flowchart LR
    A --> B
```

text

<!-- diagrama: dois -->
```mermaid
mindmap
  root((X))
    Y
```
"""


class ExtractTest(unittest.TestCase):
    def test_extracts_named_blocks_in_order(self):
        self.assertEqual(rd.extract(MD), [("um", "flowchart LR\n    A --> B\n"), ("dois", "mindmap\n  root((X))\n    Y\n")])

    def test_block_without_marker_is_an_error_naming_the_line(self):
        md = "intro\n\n```mermaid\nflowchart LR\n```\n"
        with self.assertRaises(SystemExit) as cm:
            rd.extract(md)
        self.assertIn("linha 3", str(cm.exception))

    def test_duplicate_name_is_an_error(self):
        md = MD.replace("diagrama: dois", "diagrama: um")
        with self.assertRaises(SystemExit) as cm:
            rd.extract(md)
        self.assertIn("um", str(cm.exception))

    def test_invalid_name_is_an_error(self):
        md = MD.replace("diagrama: dois", "diagrama: Dois")
        with self.assertRaises(SystemExit):
            rd.extract(md)

    def test_unclosed_block_is_an_error(self):
        with self.assertRaises(SystemExit):
            rd.extract("<!-- diagrama: um -->\n```mermaid\nflowchart LR\n")


class PageTest(unittest.TestCase):
    def test_page_embeds_blocks_and_theme(self):
        html = rd.page([("um", "flowchart LR\n A --> B\n")], Path("/x/mermaid.min.js"))
        self.assertIn('src="file:///x/mermaid.min.js"', html)
        self.assertIn('"#E41C2E"', html)
        self.assertIn('"um"', html)
        self.assertIn("flowchart LR", html)


class CleanSvgTest(unittest.TestCase):
    def test_renames_generated_id_and_keeps_namespace(self):
        svg = '<svg id="d0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><style>#d0 .x{fill:red}</style></svg>'
        out = rd.clean_svg("um", svg)
        self.assertIn('id="diag-um"', out)
        self.assertIn("#diag-um .x", out)
        self.assertNotIn('"d0"', out)
        self.assertTrue(out.startswith("<svg"))

    def test_renames_derived_marker_ids_consistently(self):
        svg = ('<svg id="d_um" xmlns="http://www.w3.org/2000/svg"><defs><marker id="d_um_flowchart-v2-pointEnd"/></defs>'
               '<path marker-end="url(#d_um_flowchart-v2-pointEnd)"/></svg>')
        out = rd.clean_svg("um", svg)
        self.assertIn('<marker id="diag-um_flowchart-v2-pointEnd"/>', out)
        self.assertIn('marker-end="url(#diag-um_flowchart-v2-pointEnd)"', out)
        self.assertNotIn("d_um", out)

    def test_adds_namespace_when_missing(self):
        out = rd.clean_svg("um", '<svg id="d0" viewBox="0 0 1 1"></svg>')
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', out)


class CollectTest(unittest.TestCase):
    def test_render_error_names_the_diagram(self):
        dom = '<pre id="result">[{"name":"um","ok":false,"err":"Parse error on line 2"}]</pre>'
        with self.assertRaises(SystemExit) as cm:
            rd.collect(dom)
        self.assertIn("um", str(cm.exception))
        self.assertIn("Parse error", str(cm.exception))

    def test_collect_returns_svgs(self):
        dom = '<pre id="result">[{"name":"um","ok":true,"svg":"&lt;svg id=\\"d0\\"&gt;&lt;/svg&gt;"}]</pre>'
        self.assertEqual(rd.collect(dom), {"um": '<svg id="d0"></svg>'})

    def test_collect_without_result_is_an_error(self):
        with self.assertRaises(SystemExit):
            rd.collect("<html></html>")


if __name__ == "__main__":
    unittest.main()
