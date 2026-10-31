"""Minimal local contract CLI. No registry upload or source upload."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples/python"))
from platform_ref import Fault, validate

def main():
    parser = argparse.ArgumentParser(description="Local Agent Manifest contract validation")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("validate", help="Validate local Manifest files without source upload")
    command.add_argument("manifests", nargs="+", type=Path)
    args = parser.parse_args()
    results = []
    failed = False
    for path in args.manifests:
        try:
            value = json.loads(path.read_text())
            validate("agent-manifest", value)
            results.append({"file": str(path), "valid": True})
        except (Fault, ValueError, OSError):
            failed = True
            results.append({"file": str(path), "valid": False, "error": "Invalid or unreadable Agent Manifest"})
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())

