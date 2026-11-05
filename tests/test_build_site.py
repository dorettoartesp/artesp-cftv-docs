"""Tests of the deck -> site/index.html converter."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("build_site", ROOT / "tools" / "build-site.py")
bs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bs)

SLIDE = '<section id="capa" data-transition="fade" style="background:#FFF"><h1>Olá</h1></section>'


class ConvertTest(unittest.TestCase):
    def test_wraps_section_in_reveal_section_and_canvas_div(self):
        out = bs.convert("capa", SLIDE)
        self.assertIn('<section data-transition="fade" data-id="capa">', out)
        self.assertIn('<div class="sl" id="capa" style="background:#FFF"><h1>Olá</h1></div>', out)

    def test_id_must_match_file_name(self):
        with self.assertRaises(SystemExit) as cm:
            bs.convert("agenda", SLIDE)
        self.assertIn("agenda", str(cm.exception))
        self.assertIn("capa", str(cm.exception))

    def test_missing_section_is_an_error(self):
        with self.assertRaises(SystemExit):
            bs.convert("capa", "<div>sem section</div>")

    def test_icon_becomes_inline_svg(self):
        out = bs.convert("capa", SLIDE.replace("<h1>Olá</h1>", '<x-icon name="Check" style="width:30px"></x-icon>'))
        self.assertIn('<svg class="ic"', out)
        self.assertIn("width:30px", out)
        self.assertNotIn("x-icon", out)

    def test_unknown_icon_is_an_error(self):
        with self.assertRaises(SystemExit) as cm:
            bs.convert("capa", SLIDE.replace("<h1>Olá</h1>", '<x-icon name="Nope"></x-icon>'))
        self.assertIn("Nope", str(cm.exception))

    def test_comments_are_removed(self):
        out = bs.convert("capa", SLIDE.replace("<h1>Olá</h1>", "<!-- nota --><h1>Olá</h1>"))
        self.assertNotIn("nota", out)

    def test_unbalanced_tags_are_an_error(self):
        with self.assertRaises(SystemExit) as cm:
            bs.check_balance("capa", "<div><p>x</div>")
        self.assertIn("capa", str(cm.exception))


class BuildTest(unittest.TestCase):
    def test_build_concatenates_in_order_and_fills_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            deck = Path(tmp) / "deck"
            (deck / "slides").mkdir(parents=True)
            site = Path(tmp) / "site"
            site.mkdir()
            (deck / "deck.json").write_text(json.dumps({"title": "T", "order": ["b", "a"]}), encoding="utf-8")
            (deck / "slides" / "a.html").write_text('<section id="a" style=""><p>A</p></section>', encoding="utf-8")
            (deck / "slides" / "b.html").write_text('<section id="b" style=""><p>B</p></section>', encoding="utf-8")
            (site / "template.html").write_text("<title>{{TITLE}}</title>{{SLIDES}}", encoding="utf-8")
            n = bs.build(deck, site / "index.html")
            page = (site / "index.html").read_text(encoding="utf-8")
            self.assertEqual(n, 2)
            self.assertIn("<title>T</title>", page)
            self.assertLess(page.index('id="b"'), page.index('id="a"'))

    def test_missing_slide_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            deck = Path(tmp) / "deck"
            (deck / "slides").mkdir(parents=True)
            site = Path(tmp) / "site"
            site.mkdir()
            (deck / "deck.json").write_text(json.dumps({"title": "T", "order": ["zz"]}), encoding="utf-8")
            (site / "template.html").write_text("{{SLIDES}}", encoding="utf-8")
            with self.assertRaises(SystemExit) as cm:
                bs.build(deck, site / "index.html")
            self.assertIn("zz", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
