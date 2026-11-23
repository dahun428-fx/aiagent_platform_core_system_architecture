"""가짜 도구 서버: Agent Gateway 도구 경로 뒤에 있는 REST 도구 역할. 실제 검색·티켓 시스템도, 비밀정보도 없다.

POST /v1/search    읽기 도구 tool-search.  {"query": "..."} → {"content": "tool:<query>"}
POST /v1/tickets   쓰기 도구 tool-ticket.  {"query": "..."} → {"content": "ticket:<query>"} (티켓을 하나 만든 셈)
GET  /_stats       → {"calls": n}   두 도구가 실제로 실행된 횟수 (멱등성 판정용: 같은 키를 다시 보내도 늘지 않아야 한다)
POST /_reset       → {"calls": 0}   횟수를 0으로 되돌리고, 본문에 고장이 있으면 심는다

고장 필드 (시나리오의 fault."fake-tool")
  delayMs: n     실행은 하고(횟수가 는다) n ms 뒤에 답한다. 그사이 같은 키의 요청이 오면 pending을 보게 된다
  drop: true     실행은 하고(횟수가 는다) 답 없이 연결을 닫는다. 쓰기라면 티켓은 만들어졌는데 호출자는 결과를 모른다
  status: n      실행하지 않고 그 상태 코드로 답한다
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import JsonHandler, serve  # noqa: E402

# 경로 → 결과 앞에 붙일 말
TOOLS = {"/v1/search": "tool:", "/v1/tickets": "ticket:"}


# HTTP 서버를 만든다. port 0이면 OS가 빈 포트를 골라 준다.
def make_server(port=0):
    state = {"calls": 0, "fault": {}}
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

        # POST: 횟수 초기화·고장 심기, 또는 도구 실행 한 번.
        def do_POST(self):
            if self.path == "/_reset":
                fault = self.read_json() if int(self.headers.get("Content-Length", "0")) else {}
                with lock:
                    state["calls"], state["fault"] = 0, fault or {}
                self.send_json(200, {"calls": 0})
                return
            if self.path not in TOOLS:
                self.send_json(404, {"error": "not found"})
                return
            try:
                query = self.read_json()["query"]
            except (ValueError, KeyError, TypeError):
                self.send_json(400, {"error": "bad request"})
                return
            with lock:
                fault = state["fault"]
                if "status" in fault:  # 실행하지 않고 실패로 답한다
                    self.send_json(fault["status"], {"error": "injected failure"})
                    return
                state["calls"] += 1
            time.sleep(fault.get("delayMs", 0) / 1000)
            if fault.get("drop"):  # 실행은 했지만 답을 보내지 않고 연결을 닫는다
                self.close_connection = True
                return
            try:
                self.send_json(200, {"content": TOOLS[self.path] + query})
            except OSError:  # 기다리는 사이 호출자(도구 경로)가 죽었다
                pass

    return serve(Handler, port)


# 단독 실행: 첫 줄에 포트 번호를 출력한다. stack.py가 이 줄을 읽어 주소를 안다.
if __name__ == "__main__":
    server = make_server(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print(server.server_address[1], flush=True)
    server.serve_forever()
