"""Scenario page: start the local stack, serve one static HTML page, and run scenarios from the browser.

python impl/demo/server.py            http://127.0.0.1:8700 (opens the browser)
python impl/demo/server.py --port 0   any free port; --no-open to skip the browser

GET  /                 the page (impl/demo/index.html)
GET  /api/scenarios    scenario definitions from impl/scenarios/scenarios.json and the service URLs
POST /api/run          {"id": "<scenario id>"} runs one scenario, {} runs all; returns the same results as run.py --json
Binds to 127.0.0.1 only. Scenarios run one at a time because they reset and read the shared fake upstream counters.
"""
from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPL = HERE.parent
sys.path.insert(0, str(IMPL))
sys.path.insert(0, str(IMPL / "scenarios"))
from common import JsonHandler, serve  # noqa: E402
import run  # noqa: E402
from stack import Stack  # noqa: E402

PAGE = HERE / "index.html"


def make_server(stack, port=8700, scenarios_path=run.SCENARIOS):
    lock = threading.Lock()

    class Handler(JsonHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                raw = PAGE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(raw)
            elif self.path == "/api/scenarios":
                self.send_json(200, {"scenarios": run.load_scenarios(scenarios_path), "services": stack.urls})
            elif self.path == "/health/ready":
                self.send_json(200, {"status": "ready"})
            else:
                self.send_json(404, {"detail": "not found"})

        def do_POST(self):
            if self.path != "/api/run":
                self.send_json(404, {"detail": "not found"})
                return
            try:
                wanted = (self.read_json() if int(self.headers.get("Content-Length", "0")) else {}).get("id")
            except (ValueError, AttributeError):
                self.send_json(400, {"detail": "body must be a JSON object"})
                return
            scenarios = [s for s in run.load_scenarios(scenarios_path) if wanted in (None, s["id"])]
            if not scenarios:
                self.send_json(404, {"detail": f"unknown scenario: {wanted}"})
                return
            with lock:
                try:
                    results = [run.run_scenario(stack, s) for s in scenarios]
                except ConnectionError as exc:
                    self.send_json(503, {"detail": f"local stack unreachable: {exc}"})
                    return
            self.send_json(200, {"results": results})

    return serve(Handler, port)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8700)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)
    with Stack() as stack:
        server = make_server(stack, args.port)
        url = f"http://127.0.0.1:{server.server_address[1]}"
        for name, service_url in stack.urls.items():
            print(f"{name:14} {service_url}", flush=True)
        print(f"\n시나리오 화면  {url}\nCtrl-C로 종료", flush=True)
        if not args.no_open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
