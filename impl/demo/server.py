"""시나리오 화면: 로컬 스택을 띄우고, 정적 HTML 한 장을 제공하고, 브라우저에서 시나리오를 실행하게 한다.

python impl/demo/server.py            http://127.0.0.1:8700 (브라우저를 연다)
python impl/demo/server.py --port 0   빈 포트 사용. --no-open 이면 브라우저를 열지 않는다

GET  /                 화면 (impl/demo/index.html)
GET  /api/scenarios    scenarios.json 의 시나리오 정의와 서비스별 주소
POST /api/run          {"id": "<시나리오 id>"} 는 하나만, {} 는 전부 실행한다. 결과 모양은 run.py --json 과 같다
127.0.0.1 에만 바인딩한다. 시나리오는 가짜 upstream 의 호출 횟수를 초기화하고 읽으므로 한 번에 하나씩만 실행한다.
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


# 화면 서버를 만든다. 이미 떠 있는 stack 을 받아서, 시나리오 실행을 그 스택에 보낸다.
def make_server(stack, port=8700, scenarios_path=run.SCENARIOS):
    lock = threading.Lock()  # 동시에 두 실행이 들어와도 차례로 돌게 한다

    class Handler(JsonHandler):
        # GET: 화면 HTML, 시나리오 목록, 기동 확인.
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

        # POST /api/run: 요청한 시나리오(없으면 전부)를 run.run_scenario 로 실행해 결과를 돌려준다.
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


# make demo 의 진입점: 스택을 띄우고, 화면 서버를 열고, 브라우저를 띄운다. Ctrl-C 로 둘 다 끈다.
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
