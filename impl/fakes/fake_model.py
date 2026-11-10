"""Fake model server: the upstream behind the Agent Gateway model route. No real model, no secrets.

POST /v1/chat      {"messages": [...]} -> {"content": "mock:<last user message>", "usage": {...}}
GET  /_stats       -> {"calls": n}
POST /_reset       -> {"calls": 0}
Later slices add fault injection (delay, 5xx, dropped connections, malformed bodies) here.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import JsonHandler, serve  # noqa: E402


class State:
    def __init__(self):
        self.calls = 0
        self.lock = threading.Lock()


def make_server(port=0):
    state = State()

    class Handler(JsonHandler):
        def do_GET(self):
            if self.path == "/_stats":
                self.send_json(200, {"calls": state.calls})
            elif self.path == "/health/ready":
                self.send_json(200, {"status": "ok"})
            else:
                self.send_json(404, {"error": "not found"})

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
            self.send_json(200, {"content": out, "usage": {"inputTokens": len(text.split()), "outputTokens": len(out.split())}})

    Handler.state = state
    return serve(Handler, port)


if __name__ == "__main__":
    server = make_server(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print(server.server_address[1], flush=True)
    server.serve_forever()
