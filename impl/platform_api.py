"""Agent Platform APIs + Runtime from the reference implementation, with the model route replaced by an HTTP
client to the separate Agent Gateway model route service.

Only the model route crosses a network boundary in S0. The tool route and Credential Broker stay in-process.
GET /_audit returns this process's audit records (local scenario runner only).
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import call_json, load_ref  # noqa: E402

ref = load_ref()
GATEWAY_TIMEOUT_S = 10.0


class HttpModelRoute:
    """Same interface as ref.ModelGateway.invoke, over HTTP. Problem Details come back as ref.Fault."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def invoke(self, content, identity, policy, traceparent):
        body = {"capability": "chat", "messages": [{"role": "user", "content": content}],
                "identity": identity, "policy": policy, "traceparent": traceparent}
        headers = {"traceparent": traceparent, "Idempotency-Key": "model-" + uuid.uuid4().hex}
        try:
            status, _, out = call_json("POST", self.base_url + "/v1/model-invocations", body, headers,
                                       timeout=GATEWAY_TIMEOUT_S)
        except ConnectionError:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Agent Gateway model route unreachable") from None
        if status != 200:
            code = out.get("code", "UPSTREAM_UNAVAILABLE") if isinstance(out, dict) else "UPSTREAM_UNAVAILABLE"
            raise ref.Fault(status, code, out.get("detail", "Model route failed") if isinstance(out, dict) else "Model route failed")
        ref.validate("model-result", out)
        return out


def make_server(gateway_url, port=0):
    server = ref.make_server(port)
    platform = ref.platform_of(server)
    route = HttpModelRoute(gateway_url)
    platform.model = route
    platform.runtime.model = route
    base = server.RequestHandlerClass

    class Handler(base):
        def do_GET(self):
            if self.path == "/_audit":
                self.send_json(200, list(platform.audit))
            else:
                super().do_GET()

    server.RequestHandlerClass = Handler
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway", required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    server = make_server(args.gateway, args.port)
    print(server.server_address[1], flush=True)
    server.serve_forever()
