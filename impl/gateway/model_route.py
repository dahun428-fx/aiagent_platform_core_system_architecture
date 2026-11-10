"""Agent Gateway model route as its own HTTP service (contracts/model-gateway.openapi.json, invokeModel).

POST /v1/model-invocations   model-request -> model-result, or Problem Details
GET  /_audit                 audit records kept by this process (local scenario runner only)
GET  /health/ready

The upstream is the fake model server given by --upstream. Authorization and routing reuse the reference
implementation; this slice (S0) only moves the route behind a network boundary. Timeouts, error mapping and
retries arrive in later slices.
"""
from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import JsonHandler, call_json, load_ref, serve  # noqa: E402

ref = load_ref()
UPSTREAM_TIMEOUT_S = 5.0


class ModelRoute:
    def __init__(self, upstream):
        self.upstream = upstream.rstrip("/")
        self.audit = []
        self.lock = threading.Lock()
        self.router = ref.ModelGateway(self.record)

    def record(self, component, traceparent, fields):
        allowed = {"tenantId", "decisionId", "provider"}
        with self.lock:
            self.audit.append({"component": component, "traceparent": traceparent,
                               **{k: v for k, v in fields.items() if k in allowed}})

    def invoke(self, body, key, traceparent):
        ref.validate("model-request", body)
        if not key or not key.strip():
            raise ref.Fault(422, "VALIDATION_ERROR", "Idempotency-Key is required")
        if traceparent is not None and traceparent != body["traceparent"]:
            raise ref.Fault(422, "VALIDATION_ERROR", "traceparent header and body differ")
        identity, policy, trace = body["identity"], body["policy"], body["traceparent"]
        provider = self.router.route(identity, policy)
        try:
            status, _, out = call_json("POST", self.upstream + "/v1/chat", {"messages": body["messages"]},
                                       timeout=UPSTREAM_TIMEOUT_S)
        except ConnectionError:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Model upstream unreachable") from None
        if status != 200:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Model upstream failed")
        self.record("model-gateway", trace, {"decisionId": policy["decisionId"], "provider": provider,
                                             "tenantId": identity["tenantId"]})
        result = {"content": out["content"], "provider": provider, "routeDecisionId": "route-" + provider,
                  "usage": out["usage"], "traceparent": trace}
        ref.validate("model-result", result)
        return result


def make_server(upstream, port=0):
    route = ModelRoute(upstream)

    class Handler(JsonHandler):
        def do_GET(self):
            if self.path == "/health/ready":
                self.send_json(200, {"status": "ok"})
            elif self.path == "/_audit":
                with route.lock:
                    self.send_json(200, list(route.audit))
            else:
                self.send_json(404, ref.Fault(404, "NOT_FOUND", "Unknown path").problem(), "application/problem+json")

        def do_POST(self):
            trace = self.headers.get("traceparent")
            try:
                if self.path != "/v1/model-invocations":
                    raise ref.Fault(404, "NOT_FOUND", "Unknown path")
                out = route.invoke(self.read_json(), self.headers.get("Idempotency-Key"), trace)
                self.send_json(200, out, headers={"traceparent": out["traceparent"]})
            except ref.Fault as exc:
                self.send_json(exc.status, exc.problem(trace), "application/problem+json")
            except (ValueError, TypeError):
                self.send_json(400, ref.Fault(400, "VALIDATION_ERROR", "Malformed request").problem(trace),
                               "application/problem+json")

    Handler.route = route
    return serve(Handler, port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    server = make_server(args.upstream, args.port)
    print(server.server_address[1], flush=True)
    server.serve_forever()
