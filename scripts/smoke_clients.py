"""Run real loopback HTTP requests from Python and compiled TypeScript clients."""
import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("platform_ref", ROOT / "examples/python/platform_ref.py")
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
server = ref.make_server()
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
results = []
try:
    for name, command in [
        ("python-http-client", [sys.executable, "examples/python/client.py"]),
        ("typescript-http-client", ["node", "examples/typescript/dist/demo.js"])
    ]:
        p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=15)
        if p.returncode:
            raise RuntimeError(f"{name}: {p.stderr}")
        body = json.loads(p.stdout)
        ref.validate("result", body)
        assert body["output"]["content"] == "mock:hello"
        results.append({"check": name, "passed": True, "result": body})
    print(json.dumps(results, ensure_ascii=False, indent=2))
finally:
    server.shutdown()
    server.server_close()
    thread.join()

