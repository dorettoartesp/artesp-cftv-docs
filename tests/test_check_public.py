"""Tests of the public-text guard."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_public", ROOT / "tools" / "check-public.py")
cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cp)


class GuardTest(unittest.TestCase):
    def _tree(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for rel, text in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return root

    def test_clean_tree_has_no_problems(self):
        root = self._tree({"APRESENTACAO.md": "o token de sessão vale para o catálogo e para o vídeo\n"})
        self.assertEqual(cp.problems([root / "APRESENTACAO.md"], cp.PATTERN), [])

    def test_private_ipv4_inside_a_slide_comment_is_caught(self):
        root = self._tree({"deck/slides/x.html": "<section id=\"x\"><!-- edge 10.23.33.26 --></section>\n"})
        found = cp.problems([root / "deck"], cp.PATTERN)
        self.assertEqual(len(found), 1)
        self.assertIn("deck/slides/x.html:1", found[0])

    def test_token_assignment_is_caught_whatever_the_case(self):
        root = self._tree({"README.md": "Token=abc\n", "a.md": "senha: x\n"})
        found = cp.problems([root / "README.md", root / "a.md"], cp.PATTERN)
        self.assertEqual(len(found), 2)

    def test_rtsp_url_with_credentials_is_caught(self):
        root = self._tree({"a.md": "rtsp://user:pw@camera/stream\n"})
        self.assertEqual(len(cp.problems([root / "a.md"], cp.PATTERN)), 1)

    def test_extra_terms_come_from_outside_the_repository(self):
        root = self._tree({"a.md": "fala do servidor exemplo-interno aqui\n"})
        self.assertEqual(cp.problems([root / "a.md"], cp.PATTERN), [])
        pattern = cp.pattern_with_extra("exemplo-interno|outro-nome")
        self.assertEqual(len(cp.problems([root / "a.md"], pattern)), 1)

    def test_extra_terms_file_is_optional_and_ignores_blank_lines(self):
        root = self._tree({"forbidden.local": "um-termo\n\n  \n# comentário\noutro\n"})
        self.assertEqual(cp.load_extra(root / "forbidden.local"), ["um-termo", "outro"])
        self.assertEqual(cp.load_extra(root / "nao-existe.local"), [])


if __name__ == "__main__":
    unittest.main()
