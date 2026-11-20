"""The guide's code sections quote check.py's output per step; keep the code and the guide in step."""
import subprocess
import sys
import unittest
from pathlib import Path

CHECK = Path(__file__).resolve().parents[1] / "examples/build/check.py"


class BuildAlongTests(unittest.TestCase):
    def test_each_step_passes_exactly_the_checks_its_chapter_claims(self):
        for step, passed in [("step0", ""), ("step1", "12"), ("step2", "1234")]:
            out = subprocess.run([sys.executable, str(CHECK), step], capture_output=True, text=True, encoding="utf-8",
                                 env={"PYTHONUTF8": "1", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")}).stdout
            got = "".join(line.split()[1] for line in out.splitlines() if line.startswith("PASS"))
            self.assertEqual(got, passed, step + "\n" + out)


if __name__ == "__main__":
    unittest.main()
