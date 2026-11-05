"""Tests of the guard that keeps site/img/diag-*.svg in step with the script's markers."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_diagrams", ROOT / "tools" / "check-diagrams.py")
cd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cd)

MD = "<!-- diagrama: um -->\n```mermaid\nflowchart LR\n```\n<!-- diagrama: dois -->\n```mermaid\nflowchart LR\n```\n"


class CheckTest(unittest.TestCase):
    def _dir(self, names):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        for n in names:
            (d / ("diag-%s.svg" % n)).write_text("<svg/>")
        return d

    def test_in_step_returns_no_problems(self):
        self.assertEqual(cd.problems(MD, self._dir(["um", "dois"])), [])

    def test_missing_file_is_reported(self):
        self.assertEqual(cd.problems(MD, self._dir(["um"])), ["falta site/img/diag-dois.svg (rode make diagrams)"])

    def test_stale_file_is_reported(self):
        self.assertEqual(cd.problems(MD, self._dir(["um", "dois", "tres"])), ["sobra diag-tres.svg sem diagrama no roteiro"])

    def test_two_scripts_share_the_image_set(self):
        other = "<!-- diagrama: dois -->\n```mermaid\nflowchart LR\n```\n<!-- diagrama: tres -->\n```mermaid\nflowchart LR\n```\n"
        self.assertEqual(cd.problems([MD, other], self._dir(["um", "dois", "tres"])), [])

    def test_same_name_with_different_code_in_two_scripts_is_reported(self):
        other = "<!-- diagrama: dois -->\n```mermaid\nflowchart TB\n```\n"
        self.assertEqual(cd.problems([MD, other], self._dir(["um", "dois"])),
                         ["diagrama dois difere entre os roteiros (mesmo nome, código diferente)"])


if __name__ == "__main__":
    unittest.main()
