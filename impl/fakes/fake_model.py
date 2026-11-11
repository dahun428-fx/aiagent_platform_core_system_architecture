"""가짜 모델 서버: Agent Gateway 모델 경로 뒤에 있는 upstream 역할. 실제 모델도, 비밀정보도 없다.

POST /v1/chat      {"messages": [...]} → {"content": "mock:<마지막 메시지>", "usage": {...}}
GET  /_stats       → {"calls": n, "disconnects": n}   /v1/chat 호출 횟수, 답하기 전에 호출자가 연결을 끊은 횟수 (시나리오 판정용)
POST /_reset       {고장}(선택) → 횟수를 0으로 되돌리고, 이번 시나리오의 고장을 정한다. 본문이 비면 고장 없음

고장 필드 (시나리오의 fault."fake-model")
  delayMs: n     답하기 전에 n ms 기다린다
  status: 500    그 상태 코드로 답한다
  drop: true     아무 답 없이 연결을 닫는다
  garbage: true  200에 JSON이 아닌 본문을 보낸다
  failTimes: n   status·drop·garbage를 처음 n번 호출에만 적용한다(일시 장애). 없으면 매번
"""
from __future__ import annotations

import select
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import JsonHandler, serve  # noqa: E402


class State:
    """호출 횟수, 끊긴 횟수, 주입할 고장. 요청 스레드 여러 개가 동시에 쓰므로 lock으로 보호한다."""

    def __init__(self):
        self.calls = 0
        self.disconnects = 0
        self.fault = {}
        self.lock = threading.Lock()


# HTTP 서버를 만든다. port 0이면 OS가 빈 포트를 골라 준다.
def make_server(port=0):
    state = State()

    class Handler(JsonHandler):
        # GET: 호출 횟수 조회와 기동 확인.
        def do_GET(self):
            if self.path == "/_stats":
                with state.lock:
                    self.send_json(200, {"calls": state.calls, "disconnects": state.disconnects})
            elif self.path == "/health/ready":
                self.send_json(200, {"status": "ok"})
            else:
                self.send_json(404, {"error": "not found"})

        # POST: 횟수 초기화, 또는 채팅 호출 한 번(마지막 메시지 앞에 "mock:"을 붙여 돌려준다).
        def do_POST(self):
            if self.path == "/_reset":
                fault = self.read_json() if int(self.headers.get("Content-Length", "0")) else {}
                with state.lock:
                    state.calls = state.disconnects = 0
                    state.fault = fault
                self.send_json(200, {"calls": 0})
                return
            if self.path != "/v1/chat":
                self.send_json(404, {"error": "not found"})
                return
            try:
                body = self.read_json()
                text = body["messages"][-1]["content"]
            except (ValueError, KeyError, IndexError, TypeError):
                self.send_json(400, {"error": "bad request"})
                return
            with state.lock:
                state.calls += 1
                call, fault = state.calls, state.fault
                delay = fault.get("delayMs", 0) / 1000
            # 지연 고장: 답하기 전에 기다린다. 그 사이 호출자가 연결을 끊으면 세어 두고 답하지 않는다.
            if delay and self.caller_hung_up_within(delay):
                with state.lock:
                    state.disconnects += 1
                return
            # 실패 고장: failTimes가 있으면 그 횟수까지만, 없으면 매번 실패한다.
            if call <= fault.get("failTimes", call):
                if fault.get("drop"):
                    self.close_connection = True  # 아무것도 쓰지 않고 돌아가면 연결이 닫힌다
                    return
                if "status" in fault:
                    self.send_json(fault["status"], {"error": "injected failure"})
                    return
                if fault.get("garbage"):
                    self.send_raw(200, b"<html>not json</html>")
                    return
            out = "mock:" + text
            # 토큰 수는 단어 수로 흉내 낸다.
            self.send_json(200, {"content": out, "usage": {"inputTokens": len(text.split()), "outputTokens": len(out.split())}})

        # JSON이 아닌 본문을 그대로 보낸다(깨진 응답 고장).
        def send_raw(self, status, raw):
            self.send_response(status)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        # seconds 동안 기다리며, 그 사이 호출자가 연결을 닫았는지 본다. 닫힌 연결은 읽을 수 있게 되고 0바이트를 돌려준다.
        def caller_hung_up_within(self, seconds):
            end = time.monotonic() + seconds
            while (left := end - time.monotonic()) > 0:
                readable, _, _ = select.select([self.connection], [], [], left)
                if readable:
                    try:
                        return self.connection.recv(1, socket.MSG_PEEK) == b""
                    except OSError:  # Windows는 닫힌 연결을 오류(연결 재설정)로 알리기도 한다
                        return True
            return False

    return serve(Handler, port)


# 단독 실행: 첫 줄에 포트 번호를 출력한다. stack.py가 이 줄을 읽어 주소를 안다.
if __name__ == "__main__":
    server = make_server(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print(server.server_address[1], flush=True)
    server.serve_forever()
