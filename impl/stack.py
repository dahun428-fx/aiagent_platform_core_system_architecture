"""Start the local stack as separate processes: fake model -> Agent Gateway model route -> Platform APIs.

Each service binds to 127.0.0.1 on a free port and prints it on its first stdout line.
Run directly to keep the stack up: python impl/stack.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import call_json  # noqa: E402


class Stack:
    def __init__(self):
        self.procs = []
        self.urls = {}

    def _start(self, name, script, *args):
        proc = subprocess.Popen([sys.executable, str(HERE / script), *args], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding="utf-8")
        self.procs.append(proc)
        line = proc.stdout.readline().strip()
        if not line.isdigit():
            raise RuntimeError(f"{name} failed to start: {proc.stderr.read() if proc.poll() is not None else line}")
        url = f"http://127.0.0.1:{line}"
        deadline = time.monotonic() + 10
        while True:
            try:
                if call_json("GET", url + "/health/ready", timeout=1)[0] == 200:
                    break
            except ConnectionError:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError(f"{name} did not become ready")
            time.sleep(0.05)
        self.urls[name] = url
        return url

    def __enter__(self):
        try:
            model = self._start("fake-model", "fakes/fake_model.py")
            gateway = self._start("model-route", "gateway/model_route.py", "--upstream", model)
            self._start("platform-api", "platform_api.py", "--gateway", gateway)
        except Exception:
            self.close()
            raise
        return self

    def close(self):
        for proc in reversed(self.procs):
            proc.terminate()
        for proc in self.procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            for stream in (proc.stdout, proc.stderr):
                if stream:
                    stream.close()
        self.procs = []

    def __exit__(self, *_):
        self.close()


if __name__ == "__main__":
    with Stack() as stack:
        for name, url in stack.urls.items():
            print(f"{name:14} {url}", flush=True)
        print("Ctrl-C to stop", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
