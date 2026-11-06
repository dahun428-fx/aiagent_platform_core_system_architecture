"""Minimal local contract CLI: validate, run and conformance. No registry upload or source upload."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples/python"))
from platform_ref import Fault, validate, serve
import conformance

def main():
    parser = argparse.ArgumentParser(description="Local Agent Manifest contract validation")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("validate", help="Validate local Manifest files without source upload")
    command.add_argument("manifests", nargs="+", type=Path)
    run = commands.add_parser("run", help="Start the local mock with Agents from a folder")
    run.add_argument("--agents-dir", type=Path, help="Folder whose subfolders each hold agent-manifest.json and the adapter")
    run.add_argument("--port", type=int, default=8765)
    check = commands.add_parser("conformance", help="Run conformance checks for one Agent folder")
    check.add_argument("agent_dir", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        serve(args.port, args.agents_dir)
        return 0
    if args.command == "conformance":
        results = conformance.run(args.agent_dir)
        for r in results:
            print(("PASS" if r["passed"] else "FAIL") + "  " + r["id"] + "  " + r["title"] + "  " + r["detail"])
        print(json.dumps({"agentDir": str(args.agent_dir), "passed": all(r["passed"] for r in results), "checks": results},
                         ensure_ascii=False, indent=2))
        return 0 if all(r["passed"] for r in results) else 1
    results = []
    failed = False
    for path in args.manifests:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            validate("agent-manifest", value)
            results.append({"file": str(path), "valid": True})
        except (Fault, ValueError, OSError):
            failed = True
            results.append({"file": str(path), "valid": False, "error": "Invalid or unreadable Agent Manifest"})
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())

