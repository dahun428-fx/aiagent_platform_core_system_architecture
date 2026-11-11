"""Agent Gateway 모델 경로를 별도 HTTP 서비스로 띄운다 (contracts/model-gateway.openapi.json 의 invokeModel).

POST /v1/model-invocations   model-request 를 받아 model-result 를 돌려준다. 실패하면 Problem Details.
GET  /_audit                 이 프로세스가 남긴 감사 기록 (로컬 시나리오 확인용)
GET  /health/ready           기동 확인

upstream 은 --upstream 으로 받은 가짜 모델 서버다. 권한 검사와 라우팅은 참조 구현을 그대로 쓰고,
이 조각(S0)은 모델 경로를 네트워크 경계 뒤로 옮기기만 한다. timeout 구분, 오류 매핑, 재시도는 다음 조각에서 다룬다.
"""
from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

# impl/ 를 import 경로에 넣어 공통 모듈(common.py)을 불러온다.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import JsonHandler, call_json, load_ref, serve  # noqa: E402

# 참조 구현 모듈: 계약 검증(validate), 오류(Fault), 권한·라우팅(ModelGateway)을 여기서 가져다 쓴다.
ref = load_ref()
UPSTREAM_TIMEOUT_S = 5.0  # shortcut: 모든 호출에 고정 timeout, S2에서 전달받은 deadline으로 바꾼다.


class ModelRoute:
    """모델 경로의 실제 처리 로직. HTTP 처리와 분리해 두어 테스트에서 바로 부를 수 있다."""

    def __init__(self, upstream):
        self.upstream = upstream.rstrip("/")
        self.audit = []  # 감사 기록. 여러 요청 스레드가 동시에 쓰므로 lock으로 보호한다.
        self.lock = threading.Lock()
        # 참조 구현의 ModelGateway를 라우터로 재사용한다. 감사 기록은 이 객체의 record로 모은다.
        self.router = ref.ModelGateway(self.record)

    # 감사 기록 한 줄을 남긴다. 허용한 필드만 남겨서 프롬프트 같은 내용이 기록에 섞이지 않게 한다.
    def record(self, component, traceparent, fields):
        allowed = {"tenantId", "decisionId", "provider"}
        with self.lock:
            self.audit.append({"component": component, "traceparent": traceparent,
                               **{k: v for k, v in fields.items() if k in allowed}})

    # 모델 호출 한 번: 입력 검사 → 권한·provider 선택 → upstream 호출 → 감사 기록 → 결과 검증.
    def invoke(self, body, key, traceparent):
        # 1) 요청 본문이 model-request 계약과 맞는지 검사한다. 안 맞으면 422.
        ref.validate("model-request", body)
        # shortcut: 키를 필수로 받지만 저장하지 않아서, 재시도하면 모델이 다시 호출된다. S5에서 effect ledger를 붙인다.
        if not key or not key.strip():
            raise ref.Fault(422, "VALIDATION_ERROR", "Idempotency-Key is required")
        # 2) 헤더와 본문의 traceparent가 다르면 추적이 갈라지므로 거부한다.
        if traceparent is not None and traceparent != body["traceparent"]:
            raise ref.Fault(422, "VALIDATION_ERROR", "traceparent header and body differ")
        # shortcut: identity와 policy를 요청 본문 그대로 믿는다. S1에서 내부 구간에 서명을 붙인다.
        identity, policy, trace = body["identity"], body["policy"], body["traceparent"]
        # 3) 권한 검사 + 데이터 분류에 맞는 provider 선택. 거부되면 403, 갈 곳이 없으면 503.
        provider = self.router.route(identity, policy)
        # 4) upstream(가짜 모델) 호출. 연결 실패나 200이 아닌 응답은 모두 503으로 돌려준다.
        try:
            status, _, out = call_json("POST", self.upstream + "/v1/chat", {"messages": body["messages"]},
                                       timeout=UPSTREAM_TIMEOUT_S)
        except ConnectionError:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Model upstream unreachable") from None
        if status != 200:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Model upstream failed")
        # 5) 성공한 호출만 감사 기록에 남기고, 결과를 model-result 계약으로 검증한 뒤 돌려준다.
        self.record("model-gateway", trace, {"decisionId": policy["decisionId"], "provider": provider,
                                             "tenantId": identity["tenantId"]})
        result = {"content": out["content"], "provider": provider, "routeDecisionId": "route-" + provider,
                  "usage": out["usage"], "traceparent": trace}
        ref.validate("model-result", result)
        return result


# HTTP 서버를 만든다. port 0이면 OS가 빈 포트를 골라 준다.
def make_server(upstream, port=0):
    route = ModelRoute(upstream)

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

        # POST: 모델 호출. 모든 오류는 Problem Details 형식으로, 요청의 trace id를 담아 돌려준다.
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
                # JSON이 깨졌거나 본문 크기가 잘못된 요청
                self.send_json(400, ref.Fault(400, "VALIDATION_ERROR", "Malformed request").problem(trace),
                               "application/problem+json")

    return serve(Handler, port)


# 단독 실행: 첫 줄에 포트 번호를 출력한다. stack.py가 이 줄을 읽어 주소를 안다.
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    server = make_server(args.upstream, args.port)
    print(server.server_address[1], flush=True)
    server.serve_forever()
