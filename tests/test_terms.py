"""terms.json stays usable: every term is complete, glossary names exist, the review script runs."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Terms(unittest.TestCase):
    def test_terms_are_complete_and_glossary_names_exist(self):
        terms = json.loads((ROOT / "terms.json").read_text(encoding="utf-8"))["terms"]
        glossary = set(re.findall(r'<div class="term" id="term-[^"]+">.*?<b>(.*?) <small>', (ROOT / "docs/onboarding/09-glossary.md").read_text(encoding="utf-8")))
        for term in terms:
            with self.subTest(term=term["id"]):
                self.assertTrue(term["canonical"] and term["definition"])
                self.assertIsInstance(term["discouraged"], list)
                if term["glossary"]:
                    self.assertIn(term["glossary"], {re.sub(r"\{\{icon:\w+\}\}", "", g).strip() for g in glossary})

    def test_review_script_runs(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts/check_terms.py")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
