import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CLITests(unittest.TestCase):
    def test_four_manifests_validate_locally(self):
        p = subprocess.run([sys.executable, "scripts/agentctl.py", "validate",
                            *[str(x) for x in sorted((ROOT / "examples/manifests").glob("*.json"))]],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(len(result), 4)
        self.assertTrue(all(x["valid"] for x in result))

    def test_invalid_manifest_and_missing_file_return_nonzero(self):
        p = subprocess.run([sys.executable, "scripts/agentctl.py", "validate",
                            "examples/negative/missing-owner.json", "no-such-file.json"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertTrue(all(not x["valid"] for x in json.loads(p.stdout)))

