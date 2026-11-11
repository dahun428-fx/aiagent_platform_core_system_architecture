"""가짜 모델 서버: Agent Gateway 모델 경로 뒤에 있는 upstream 역할. 실제 모델도, 비밀정보도 없다.

POST /v1/chat      {"messages": [...]} → {"content": "mock:<마지막 메시지>", "usage": {...}}
GET  /_stats       → {"calls": n}   지금까지 /v1/chat 이 불린 횟수 (시나리오 판정용)
POST /_reset       → {"calls": 0}   횟수를 0으로 되돌린다
다음 조각부터 여기에 실패 주입(지연, 5xx, 연결 끊김, 깨진 응답)을 넣는다.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import JsonHandler, serve  # noqa: E402


class State:
    """호출 횟수. 요청 스레드 여러 개가 동시에 올리므로 lock으로 보호한다."""

    def __init__(self):
        self.calls = 0
        self.lock = threading.Lock()


# HTTP 서버를 만든다. port 0이면 OS가 빈 포트를 골라 준다.
def make_server(port=0):
    state = State()

    class Handler(JsonHandler):
        # GET: 호출 횟수 조회와 기동 확인.
        def do_GET(self):
            if self.path == "/_stats":
                self.send_json(200, {"calls": state.calls})
            elif self.path == "/health/ready":
                self.send_json(200, {"status": "ok"})
            else:
                self.send_json(404, {"error": "not found"})

        # POST: 횟수 초기화, 또는 채팅 호출 한 번(마지막 메시지 앞에 "mock:"을 붙여 돌려준다).
        def do_POST(self):
            if self.path == "/_reset":
                with state.lock:
                    state.calls = 0
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
            out = "mock:" + text
            # 토큰 수는 단어 수로 흉내 낸다.
            self.send_json(200, {"content": out, "usage": {"inputTokens": len(text.split()), "outputTokens": len(out.split())}})

    return serve(Handler, port)


# 단독 실행: 첫 줄에 포트 번호를 출력한다. stack.py가 이 줄을 읽어 주소를 안다.
if __name__ == "__main__":
    server = make_server(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print(server.server_address[1], flush=True)
    server.serve_forever()
