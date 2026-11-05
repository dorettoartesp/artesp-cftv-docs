"""Tests of <x-groups>: a Mermaid mind map of the script rendered as columns of cards."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("build_site", ROOT / "tools" / "build-site.py")
bs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bs)

MINDMAP = """mindmap
  root((Situação anterior))
    Inventário
      Planilhas em formatos distintos
      Credenciais em texto puro
    Acesso ao vídeo
      Operador conecta direto
"""

MD = "<!-- diagrama: situacao -->\n```mermaid\n" + MINDMAP + "```\n<!-- diagrama: fluxo -->\n```mermaid\nflowchart LR\n A --> B\n```\n"


class ParseTest(unittest.TestCase):
    def test_mindmap_becomes_root_and_groups(self):
        root, groups = bs.parse_mindmap(MINDMAP)
        self.assertEqual(root, "Situação anterior")
        self.assertEqual(groups, [
            ("Inventário", ["Planilhas em formatos distintos", "Credenciais em texto puro"]),
            ("Acesso ao vídeo", ["Operador conecta direto"]),
        ])

    def test_non_mindmap_block_is_an_error(self):
        with self.assertRaises(SystemExit) as cm:
            bs.parse_mindmap("flowchart LR\n A --> B\n")
        self.assertIn("mindmap", str(cm.exception))


class RenderTest(unittest.TestCase):
    def test_groups_render_as_one_card_per_branch(self):
        html = bs.groups_html([("Inventário", ["a", "b"]), ("Acesso", ["c"])], 'width:100px')
        self.assertEqual(html.count('class="grupo"'), 2)
        self.assertIn("<h3", html)
        self.assertIn("<li>a</li>", html)
        self.assertIn("grid-template-columns:repeat(2, 1fr)", html)
        self.assertIn("width:100px", html)

    def test_more_than_four_branches_wrap_into_three_columns(self):
        html = bs.groups_html([("g%d" % i, ["x"]) for i in range(5)], "")
        self.assertIn("grid-template-columns:repeat(3, 1fr)", html)


class ConvertTest(unittest.TestCase):
    def test_x_groups_reads_the_named_block_of_the_script(self):
        slide = '<section id="s" style=""><x-groups src="situacao" style="flex:1"></x-groups></section>'
        out = bs.convert("s", slide, script=MD)
        self.assertIn("Credenciais em texto puro", out)
        self.assertNotIn("x-groups", out)

    def test_x_groups_with_unknown_name_is_an_error(self):
        slide = '<section id="s" style=""><x-groups src="nope"></x-groups></section>'
        with self.assertRaises(SystemExit) as cm:
            bs.convert("s", slide, script=MD)
        self.assertIn("nope", str(cm.exception))

    def test_x_groups_on_a_flowchart_is_an_error(self):
        slide = '<section id="s" style=""><x-groups src="fluxo"></x-groups></section>'
        with self.assertRaises(SystemExit):
            bs.convert("s", slide, script=MD)


if __name__ == "__main__":
    unittest.main()
