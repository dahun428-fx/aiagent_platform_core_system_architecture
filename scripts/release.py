"""Fail-closed validation and reproducible ZIP packaging of authored and generated artifacts."""
import hashlib
import importlib.metadata
import json
import os
import platform
import posixpath
import shutil
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "verification"
DIST = ROOT / "dist"
TSC = os.environ.get("TSC_PATH") or str(ROOT / "node_modules/typescript/bin/tsc")
checks = []


def run(name, command):
    p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
    checks.append({"check": name, "command": command, "exitCode": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    if p.returncode:
        raise RuntimeError(name + " failed")


def files_to_package():
    excluded = {".venv", "node_modules", "__pycache__", ".git", "dist", ".impeccable"}
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if path.is_file() and not any(part in excluded for part in relative.parts) and path.name != "checksums.sha256" and path.suffix != ".pyc":
            yield path


def main():
    VERIFY.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    try:
        run("portal-rebuild", [sys.executable, "scripts/build_portal.py", "--write"])
        run("contract-and-runtime-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
        run("typescript-typecheck", ["node", TSC, "--noEmit", "-p", "examples/typescript/tsconfig.json"])
        run("typescript-build", ["node", TSC, "-p", "examples/typescript/tsconfig.json"])
        run("python-typescript-http-smoke", [sys.executable, "scripts/smoke_clients.py"])
        # A fresh browser check is mandatory; stale cached evidence does not pass a release.
        run("browser-offline", ["node", "scripts/browser-check.cjs"])
        status = "passed"
    except Exception as exc:
        checks.append({"check": "release", "exitCode": 1, "error": str(exc)})
        status = "failed"
    report = {"packageVersion": "0.1.0", "status": status, "date": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
              "runtime": {"python": sys.version, "node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
                          "jsonschema": importlib.metadata.version("jsonschema"),
                          "openapi-spec-validator": importlib.metadata.version("openapi-spec-validator")},
              "checks": checks,
              "scope": "Standards and local mock validation only; production integrations / numeric company SLOs TBD."}
    (VERIFY / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if status != "passed":
        print(json.dumps({"status": status, "failed": [c["check"] for c in checks if c.get("exitCode")]}))
        return 1
    # Freeze file list; exclude the packaging result to avoid a recursive hash.
    package_files = [p for p in files_to_package() if p.name != "archive-verification.json"]
    sums = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in package_files}
    manifest = "".join(f"{digest}  {name}\n" for name, digest in sums.items())
    (ROOT / "checksums.sha256").write_text(manifest)
    target = DIST / "enterprise-ai-agent-platform-v0.1.zip"
    def write_zip():
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for p in package_files + [ROOT / "checksums.sha256"]:
                info = zipfile.ZipInfo("enterprise-ai-agent-platform-v0.1/" + str(p.relative_to(ROOT)), date_time=(2026, 10, 30, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, p.read_bytes())
    write_zip()
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None, "ZIP CRC failure"
        prefix = "enterprise-ai-agent-platform-v0.1/"
        assert len(archive.namelist()) == len(package_files) + 1
        for name, digest in sums.items():
            assert hashlib.sha256(archive.read(prefix + name)).hexdigest() == digest, name
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.targets = []
            def handle_starttag(self, tag, attrs):
                for attr, value in attrs:
                    if attr in ("href", "src") and value:
                        self.targets.append(value)
        names = set(archive.namelist())
        checked_links = 0
        for name in names:
            if name.endswith(".html"):
                parser = Links()
                parser.feed(archive.read(name).decode())
                for value in parser.targets:
                    parts = urlsplit(value)
                    if not parts.scheme and parts.path:
                        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parts.path)))
                        assert resolved in names, f"Archive link missing: {name} -> {value}"
                        checked_links += 1
    evidence = {"status": "passed", "archive": target.name, "files": len(package_files) + 1,
                "bytes": target.stat().st_size, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "checks": ["zip CRC", "every archived file SHA256", "expected entry count", "all archive HTML local links"],
                "checkedHtmlLinks": checked_links,
                "note": "This report is external to ZIP to avoid self-referential archive hashes."}
    (VERIFY / "archive-verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (DIST / (target.name + ".sha256")).write_text(evidence["sha256"] + "  " + target.name + "\n")
    print(json.dumps(evidence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

