"""Agent Gateway 도구 경로를 별도 HTTP 서비스로 띄운다 (contracts/tool-gateway.openapi.json 의 invokeTool).

POST /v1/tool-invocations    tool-invoke 를 받아 tool-result 를 돌려준다. 실패하면 Problem Details.
                             X-Internal-Signature 헤더(Platform이 공유 비밀값으로 만든 서명)가 맞아야 한다.
GET  /_audit                 이 프로세스가 남긴 감사 기록 (로컬 시나리오 확인용)
GET  /health/ready           기동 확인

승인된 도구만 실행한다: 등록된 도구(이름·버전)이고, 정책이 그 자원을 허용하고, 읽기 도구여야 한다.
같은 멱등성 키는 PostgreSQL effect ledger(ledger.py)로 한 번만 실행한다. 이 프로세스를 재시작해도 기록이 남는다.
upstream 은 --upstream 으로 받은 가짜 도구 서버, DB 주소는 환경 변수 IMPL_DATABASE_URL, 서명 키는 IMPL_INTERNAL_KEY.
"""
from __future__ import annotations

import argparse
import hmac
import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATABASE_ENV, KEY_ENV, SIGNATURE_HEADER, TIMEOUT_HEADER, JsonHandler, call_json, load_ref, serve, sign  # noqa: E402
from ledger import EffectLedger  # noqa: E402
from model_route import upstream_budget  # noqa: E402

ref = load_ref()
# 이 도구 경로에 등록된 도구. 지금은 예제 fixture의 tool-search 0.1.0(읽기) 하나다.
# shortcut: 도구 목록이 코드에 고정돼 있다. Agent Factory의 도구 Registry가 생기면 거기서 읽는다.
TOOLS = {(d["toolId"], d["version"]): d for d in [ref.load("tool-descriptor")]}


class ToolRoute:
    """도구 경로의 실제 처리 로직. HTTP 처리와 분리해 두어 테스트에서 바로 부를 수 있다."""

    def __init__(self, upstream, key, database_url):
        self.upstream = upstream.rstrip("/")
        self.key = key  # Platform과 공유하는 서명 키
        self.ledger = EffectLedger(database_url)
        self.audit = []
        self.lock = threading.Lock()
        # 자격증명 발급·소비는 참조 구현의 Credential Broker를 이 프로세스 안에서 그대로 쓴다(네트워크 분리는 후속 조각).
        self.broker = ref.CredentialBroker(self.record)

    # 감사 기록 한 줄. 허용한 필드만 남겨서 도구 인자 같은 내용이 기록에 섞이지 않게 한다.
    def record(self, component, traceparent, fields):
        allowed = {"tenantId", "decisionId", "toolId", "outcome"}
        with self.lock:
            self.audit.append({"component": component, "traceparent": traceparent,
                               **{k: v for k, v in fields.items() if k in allowed}})

    # 도구 호출 한 번: 서명 → 입력 검사 → 권한 → 도구 승인 → 멱등성(ledger) → 자격증명 → upstream 실행 → 결과 저장.
    # 결과가 None이면 같은 키 요청이 아직 실행 중이라는 뜻이다(HTTP 202).
    def invoke(self, body, header_key, traceparent, signature, timeout_header=None):
        # 0) 서명 확인. 없거나 틀리면 본문의 identity·policy를 믿을 수 없으므로 아무것도 하지 않고 403.
        if not signature or not hmac.compare_digest(signature, sign(self.key, body)):
            raise ref.Fault(403, "FORBIDDEN", "Internal signature missing or invalid")
        # 1) tool-invoke 계약 검사. 헤더의 Idempotency-Key와 본문의 idempotencyKey가 다르면 어느 쪽을 믿을지 모르므로 거부한다.
        ref.validate("tool-invoke", body)
        if header_key is not None and header_key != body["idempotencyKey"]:
            raise ref.Fault(422, "VALIDATION_ERROR", "Idempotency-Key header and body differ")
        if traceparent is not None and traceparent != body["traceparent"]:
            raise ref.Fault(422, "VALIDATION_ERROR", "traceparent header and body differ")
        budget = upstream_budget(timeout_header)
        identity, policy, trace = body["identity"], body["policy"], body["traceparent"]
        # 2) 호출마다 권한을 다시 검사한다(scope, tenant, 정책 만료).
        ref.authorize(identity, policy, "tools.read")
        # 3) 승인된 도구인가: 등록돼 있고, 정책이 그 자원을 허용하고, 읽기 도구여야 한다.
        tool = TOOLS.get((body["toolId"], body["version"]))
        if tool is None or tool["resource"] not in policy["allowedResources"]:
            raise ref.Fault(403, "FORBIDDEN", "Tool not approved")
        if tool["effect"] != "read":
            raise ref.Fault(403, "FORBIDDEN", "Write tools require approval; not implemented yet")
        # 4) 멱등성. 키는 누가(tenant·principal·Agent) 어떤 도구(이름·버전)를 어떤 키로 불렀는지에 묶는다.
        #    같은 업무 효과인지는 인자와 대상 자원으로 판단한다(trace·정책 증거는 매번 위에서 다시 검사하므로 digest에 넣지 않는다).
        # shortcut: tool-invoke 계약에 Agent 버전이 없어 Agent id로 묶는다. 계약에 버전이 들어오면 키에 더한다.
        ledger_key = (identity["tenantId"], identity.get("principalId", identity["workloadId"]), identity["agentId"],
                      body["toolId"], body["version"], body["idempotencyKey"])
        digest = ref.canonical_digest({"arguments": body["arguments"], "resource": tool["resource"]})
        state, stored = self.ledger.claim(ledger_key, digest)
        if state == "conflict":
            raise ref.Fault(409, "CONFLICT", "Idempotency key reused for different request")
        if state == "done":
            self.record("tool-gateway", trace, {"toolId": body["toolId"], "tenantId": identity["tenantId"], "outcome": "replayed"})
            return {**stored, "traceparent": trace}
        if state == "pending":
            return None
        # 5) 이 요청이 실행 권리를 얻었다. 실패하면 줄을 지워(release) 같은 키로 다시 시도할 수 있게 한다.
        try:
            result = self.execute(body, tool, policy, trace, budget)
        except BaseException:
            self.ledger.release(ledger_key)
            raise
        self.ledger.succeed(ledger_key, result)
        self.record("tool-gateway", trace, {"toolId": body["toolId"], "tenantId": identity["tenantId"], "outcome": "executed"})
        return result

    # 자격증명을 발급·소비하고 가짜 도구 서버를 한 번 부른다. 실패는 계약 0.2.0대로 504·503·502로 나눈다.
    # shortcut: 도구 호출은 재시도하지 않는다. 앱이나 Runtime이 같은 키로 다시 보내면 ledger가 중복을 막아 준다.
    def execute(self, body, tool, policy, trace, budget):
        identity = body["identity"]
        lease = self.broker.issue({"identity": identity, "toolId": body["toolId"], "toolVersion": body["version"],
                                   "resource": tool["resource"], "scopes": ["tools.read"],
                                   "policyDecisionId": policy["decisionId"], "invocationId": body["invocationId"]},
                                  policy, trace)
        self.broker.consume(lease["credentialRef"], identity["workloadId"], body["invocationId"], tool["resource"])
        try:
            status, _, out = call_json("POST", self.upstream + "/v1/search", body["arguments"], timeout=budget)
        except TimeoutError:
            raise ref.Fault(504, "UPSTREAM_TIMEOUT", "Tool upstream timed out") from None
        except ConnectionError:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Tool upstream unreachable") from None
        except ValueError:
            raise ref.Fault(502, "UPSTREAM_ERROR", "Tool upstream returned an invalid response") from None
        try:
            if status != 200:
                raise ref.Fault(502, "UPSTREAM_ERROR", "Tool upstream returned an error")
            output = {"content": out["content"]}
            ref.validate("tool-output", output)
        except (KeyError, TypeError, ref.Fault):
            raise ref.Fault(502, "UPSTREAM_ERROR", "Tool upstream returned an invalid response") from None
        result = {"invocationId": body["invocationId"], "toolId": body["toolId"], "status": "succeeded",
                  "output": output, "traceparent": trace}
        ref.validate("tool-result", result)
        return result


# HTTP 서버를 만든다. port 0이면 OS가 빈 포트를 골라 준다.
def make_server(upstream, key, database_url, port=0):
    route = ToolRoute(upstream, key, database_url)

    class Handler(JsonHandler):
        # GET: 기동 확인과 감사 기록 조회만 있다.
        def do_GET(self):
            if self.path == "/health/ready":
                self.send_json(200, {"status": "ok"})
            elif self.path == "/_audit":
                with route.lock:
                    self.send_json(200, list(route.audit))
            else:
                self.send_json(404, ref.Fault(404, "NOT_FOUND", "Unknown path").problem(), "application/problem+json")

        # POST: 도구 호출. 같은 키가 실행 중이면 본문 없는 202와 Retry-After, 오류는 Problem Details.
        def do_POST(self):
            trace = self.headers.get("traceparent")
            try:
                if self.path != "/v1/tool-invocations":
                    raise ref.Fault(404, "NOT_FOUND", "Unknown path")
                out = route.invoke(self.read_json(), self.headers.get("Idempotency-Key"), trace,
                                   self.headers.get(SIGNATURE_HEADER), self.headers.get(TIMEOUT_HEADER))
                if out is None:
                    self.send_response(202)
                    self.send_header("Retry-After", "1")
                    self.send_header("Content-Length", "0")
                    if trace:
                        self.send_header("traceparent", trace)
                    self.end_headers()
                    return
                self.send_json(200, out, headers={"traceparent": out["traceparent"]})
            except ref.Fault as exc:
                self.send_json(exc.status, exc.problem(trace), "application/problem+json")
            except (ValueError, TypeError):
                self.send_json(400, ref.Fault(400, "VALIDATION_ERROR", "Malformed request").problem(trace),
                               "application/problem+json")

    return serve(Handler, port)


# 단독 실행: 첫 줄에 포트 번호를 출력한다. stack.py가 이 줄을 읽어 주소를 안다.
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    # 서명 키와 DB 주소가 없으면 안전하게 동작할 수 없으므로 아예 뜨지 않는다.
    for name in (KEY_ENV, DATABASE_ENV):
        if not os.environ.get(name):
            sys.exit(f"{name} is required")
    server = make_server(args.upstream, os.environ[KEY_ENV], os.environ[DATABASE_ENV], args.port)
    print(server.server_address[1], flush=True)
    server.serve_forever()
