"""가짜 도구 서버: Agent Gateway 도구 경로 뒤에 있는 REST 도구(tool-search) 역할. 실제 검색도, 비밀정보도 없다.

POST /v1/search    {"query": "..."} → {"content": "tool:<query>"}
GET  /_stats       → {"calls": n}   /v1/search 가 실제로 실행된 횟수 (멱등성 판정용: 같은 키를 다시 보내도 늘지 않아야 한다)
POST /_reset       → {"calls": 0}   횟수를 0으로 되돌린다
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import JsonHandler, serve  # noqa: E402


# HTTP 서버를 만든다. port 0이면 OS가 빈 포트를 골라 준다.
def make_server(port=0):
    state = {"calls": 0}
    lock = threading.Lock()

    class Handler(JsonHandler):
        # GET: 실행 횟수 조회와 기동 확인.
        def do_GET(self):
            if self.path == "/_stats":
                with lock:
                    self.send_json(200, {"calls": state["calls"]})
            elif self.path == "/health/ready":
                self.send_json(200, {"status": "ok"})
            else:
                self.send_json(404, {"error": "not found"})

        # POST: 횟수 초기화, 또는 검색 한 번(질의 앞에 "tool:"을 붙여 돌려준다).
        def do_POST(self):
            if self.path == "/_reset":
                if int(self.headers.get("Content-Length", "0")):
                    self.read_json()
                with lock:
                    state["calls"] = 0
                self.send_json(200, {"calls": 0})
                return
            if self.path != "/v1/search":
                self.send_json(404, {"error": "not found"})
                return
            try:
                query = self.read_json()["query"]
            except (ValueError, KeyError, TypeError):
                self.send_json(400, {"error": "bad request"})
                return
            with lock:
                state["calls"] += 1
            self.send_json(200, {"content": "tool:" + query})

    return serve(Handler, port)


# 단독 실행: 첫 줄에 포트 번호를 출력한다. stack.py가 이 줄을 읽어 주소를 안다.
if __name__ == "__main__":
    server = make_server(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print(server.server_address[1], flush=True)
    server.serve_forever()
