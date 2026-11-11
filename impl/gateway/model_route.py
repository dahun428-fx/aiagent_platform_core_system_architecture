"""Agent Gateway 모델 경로를 별도 HTTP 서비스로 띄운다 (contracts/model-gateway.openapi.json 의 invokeModel).

POST /v1/model-invocations   model-request 를 받아 model-result 를 돌려준다. 실패하면 Problem Details.
                             X-Internal-Signature 헤더(Platform이 공유 비밀값으로 만든 서명)가 맞아야 한다.
                             Request-Timeout-Ms 헤더(남은 시간)가 있으면 그 시간과 자체 상한 중 짧은 쪽만 upstream을 기다리고,
                             넘으면 upstream 연결을 끊고 504 UPSTREAM_TIMEOUT.
GET  /_audit                 이 프로세스가 남긴 감사 기록 (로컬 시나리오 확인용)
POST /_reset                 circuit breaker와 rate limit 상태를 처음으로 되돌린다 (로컬 시나리오 확인용, 시나리오마다 호출)
GET  /health/ready           기동 확인

upstream 은 --upstream 으로 받은 가짜 모델 서버다. 권한 검사와 라우팅은 참조 구현을 그대로 쓰고,
서명 키는 환경 변수 IMPL_INTERNAL_KEY 로 받는다(stack.py가 실행마다 새로 만든다).

upstream 실패는 계약 0.2.0(ADR-038)대로 나눈다: 시간 초과 504, 연결 실패 503, 5xx·깨진 응답 502.
모델 호출은 외부에 남는 효과가 없는 읽기 호출이므로, 연결 실패·5xx·깨진 응답은 deadline 안에서 최대 3회까지 시도한다.
오류 응답에는 upstream 주소나 upstream 원문 오류를 넣지 않는다.

보호 장치(S4): upstream이 연속으로 실패하면 circuit을 열어 잠시 upstream을 부르지 않고 바로 503을 준다.
tenant·Agent마다 1초에 받을 수 있는 호출 수를 제한하고, 넘으면 429 RATE_LIMITED. 둘 다 Retry-After(초)를 붙인다.
"""
from __future__ import annotations

import argparse
import hmac
import math
import os
import sys
import threading
import time
from pathlib import Path

# impl/ 를 import 경로에 넣어 공통 모듈(common.py)을 불러온다.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import KEY_ENV, SIGNATURE_HEADER, TIMEOUT_HEADER, JsonHandler, call_json, load_ref, serve, sign  # noqa: E402

# 참조 구현 모듈: 계약 검증(validate), 오류(Fault), 권한·라우팅(ModelGateway)을 여기서 가져다 쓴다.
ref = load_ref()
UPSTREAM_TIMEOUT_S = 5.0  # 모델 경로 자체 상한. 호출자가 남은 시간을 더 길게 보내도 이보다 오래 기다리지 않는다(ADR-038).
MAX_ATTEMPTS = 3  # 첫 시도 포함 최대 시도 횟수
FIRST_BACKOFF_S = 0.05  # 두 번째 시도 전 대기. 그다음은 두 배(0.05초 → 0.1초)
# shortcut: backoff에 jitter가 없고 재시도 예산이 호출마다 따로다. 여러 인스턴스가 한꺼번에 재시도하면 upstream에 몰린다.
#           S4 circuit breaker와 함께 upstream 단위 예산을 둔다.


# Request-Timeout-Ms 헤더 값을 초 단위 대기 시간으로 바꾼다. 없으면 자체 상한, 있으면 둘 중 짧은 쪽.
# 계약상 1 이상의 정수다. 그 밖의 값은 422로 거부한다.
def upstream_budget(header):
    if header is None:
        return UPSTREAM_TIMEOUT_S
    if not (header.isascii() and header.isdigit()) or int(header) < 1:
        raise ref.Fault(422, "VALIDATION_ERROR", TIMEOUT_HEADER + " must be a positive integer")
    return min(int(header) / 1000, UPSTREAM_TIMEOUT_S)


class ModelRoute:
    """모델 경로의 실제 처리 로직. HTTP 처리와 분리해 두어 테스트에서 바로 부를 수 있다."""

    def __init__(self, upstream, key):
        self.upstream = upstream.rstrip("/")
        self.key = key  # Platform과 공유하는 서명 키
        self.audit = []  # 감사 기록. 여러 요청 스레드가 동시에 쓰므로 lock으로 보호한다.
        self.lock = threading.Lock()
        # 참조 구현의 ModelGateway를 라우터로 재사용한다. 감사 기록은 이 객체의 record로 모은다.
        self.router = ref.ModelGateway(self.record)
        self.breaker = CircuitBreaker()  # upstream이 하나라 circuit도 하나다. upstream이 늘면 upstream마다 둔다.
        self.limiter = RateLimiter()

    # 감사 기록 한 줄을 남긴다. 허용한 필드만 남겨서 프롬프트 같은 내용이 기록에 섞이지 않게 한다.
    def record(self, component, traceparent, fields):
        allowed = {"tenantId", "decisionId", "provider", "classification"}
        with self.lock:
            self.audit.append({"component": component, "traceparent": traceparent,
                               **{k: v for k, v in fields.items() if k in allowed}})

    # 모델 호출 한 번: 서명 확인 → 입력 검사 → 권한·provider 선택 → upstream 호출 → 감사 기록 → 결과 검증.
    def invoke(self, body, key, traceparent, signature, timeout_header=None):
        # 0) 서명 확인. 없거나 틀리면 본문의 identity·policy를 믿을 수 없으므로 아무것도 하지 않고 403.
        #    compare_digest는 비교 시간이 일정해서, 응답 시간으로 서명을 한 글자씩 맞춰 보는 공격을 막는다.
        if not signature or not hmac.compare_digest(signature, sign(self.key, body)):
            raise ref.Fault(403, "FORBIDDEN", "Internal signature missing or invalid")
        # 1) 요청 본문이 model-request 계약과 맞는지 검사한다. 안 맞으면 422.
        ref.validate("model-request", body)
        # shortcut: 키를 필수로 받지만 저장하지 않아서, 재시도하면 모델이 다시 호출된다. S5에서 effect ledger를 붙인다.
        if not key or not key.strip():
            raise ref.Fault(422, "VALIDATION_ERROR", "Idempotency-Key is required")
        budget = upstream_budget(timeout_header)
        # 2) 헤더와 본문의 traceparent가 다르면 추적이 갈라지므로 거부한다.
        if traceparent is not None and traceparent != body["traceparent"]:
            raise ref.Fault(422, "VALIDATION_ERROR", "traceparent header and body differ")
        # 서명이 맞았으므로 identity·policy는 Platform이 보낸 그대로다. 그래도 호출마다 권한을 다시 검사한다(아래 3).
        identity, policy, trace = body["identity"], body["policy"], body["traceparent"]
        # 3) 권한 검사 + 데이터 분류에 맞는 provider 선택. 거부되면 403, 갈 곳이 없으면 503.
        provider = self.router.route(identity, policy)
        # 4) tenant·Agent별 호출 한도. 권한 검사 뒤에 세어서, 거부된 요청이 남의 한도를 쓰지 못하게 한다.
        self.limiter.take(identity["tenantId"], identity["agentId"])
        # 5) circuit이 열려 있으면 upstream을 부르지 않고 바로 503. 아니면 부르고(실패하면 deadline 안에서 재시도) 결과를 circuit에 반영한다.
        self.breaker.before_call()
        try:
            result = self.call_upstream(body["messages"], provider, trace, time.monotonic() + budget)
        except Exception:  # 예상 밖의 예외도 실패로 반영해야 시험 호출 표시가 남아 circuit이 계속 열려 있지 않다
            self.breaker.after_call(ok=False)
            raise
        self.breaker.after_call(ok=True)
        # 6) 성공한 호출만 감사 기록에 남긴다.
        #    라우팅을 결정한 데이터 분류도 남겨서, 앱이 분류를 낮춰 보냈을 때 서버 분류가 쓰였는지 확인할 수 있게 한다.
        self.record("model-gateway", trace, {"decisionId": policy["decisionId"], "provider": provider,
                                             "tenantId": identity["tenantId"], "classification": policy["classification"]})
        return result

    # upstream을 deadline까지 최대 MAX_ATTEMPTS번 부른다. 계약에 맞는 결과를 얻으면 돌려주고, 못 얻으면 마지막 실패를 Fault로 던진다.
    #   시간 초과        → 504, 다시 시도하지 않는다(남은 시간을 이미 다 썼다)
    #   연결 실패        → 503, 다시 시도
    #   5xx·깨진 응답    → 502, 다시 시도
    #   그 밖의 4xx      → 502, 다시 시도해도 같으므로 바로 끝낸다
    def call_upstream(self, messages, provider, trace, deadline):
        backoff = FIRST_BACKOFF_S
        for attempt in range(1, MAX_ATTEMPTS + 1):
            status = None
            try:
                status, _, out = call_json("POST", self.upstream + "/v1/chat", {"messages": messages},
                                           timeout=max(deadline - time.monotonic(), 0.001))
            except TimeoutError:
                raise ref.Fault(504, "UPSTREAM_TIMEOUT", "Model upstream timed out") from None
            except ConnectionError:
                fault = ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Model upstream unreachable")
            except ValueError:  # 본문이 JSON이 아니다
                fault = ref.Fault(502, "UPSTREAM_ERROR", "Model upstream returned an invalid response")
            if status == 200:
                try:
                    result = {"content": out["content"], "provider": provider, "routeDecisionId": "route-" + provider,
                              "usage": out["usage"], "traceparent": trace}
                    ref.validate("model-result", result)
                    return result
                except (KeyError, TypeError, ref.Fault):  # 필드가 없거나 계약에 안 맞는 200
                    fault = ref.Fault(502, "UPSTREAM_ERROR", "Model upstream returned an invalid response")
            elif status is not None:
                fault = ref.Fault(502, "UPSTREAM_ERROR", "Model upstream returned an error")
                if status < 500:
                    raise fault
            # 마지막 시도였거나, 기다린 뒤 다시 시도할 시간이 없으면 지금 실패로 끝낸다.
            if attempt == MAX_ATTEMPTS or time.monotonic() + backoff >= deadline:
                raise fault
            time.sleep(backoff)
            backoff *= 2


# shortcut: 아래 수치는 로컬 시나리오가 몇 초 안에 끝나도록 고른 값이다. 운영 값은 upstream·tenant별 설정으로 받는다(TBD).
BREAKER_THRESHOLD = 3  # 연속 실패 몇 번에 circuit을 여는가 (호출 한 번 = 재시도까지 포함한 결과 하나)
BREAKER_COOLDOWN_S = 1.0  # circuit을 연 뒤 다시 시험해 볼 때까지 기다리는 시간
RATE_LIMIT = 5  # tenant·Agent마다 RATE_WINDOW_S 동안 받을 수 있는 호출 수
RATE_WINDOW_S = 1.0


# 오류에 Retry-After(초)를 붙여 던진다. 0.2초가 남았어도 1초로 올려서, 0초라 바로 다시 보내는 일이 없게 한다.
def retry_later(status, code, detail, seconds):
    fault = ref.Fault(status, code, detail)
    fault.retry_after = max(1, math.ceil(seconds))
    return fault


class CircuitBreaker:
    """upstream 하나의 circuit. 닫힘(정상) → 연속 실패 THRESHOLD번 → 열림(바로 503) → COOLDOWN 뒤 반열림(시험 호출 1번)
    → 성공하면 닫힘, 실패하면 다시 열림."""

    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    # 처음 상태(닫힘)로 되돌린다.
    def reset(self):
        with self.lock:
            self.failures = 0
            self.opened_at = None  # 열린 시각. None이면 닫힘
            self.trial = False  # 반열림에서 시험 호출이 진행 중인가

    # upstream을 부르기 전에 확인한다. 열려 있으면 503, 반열림이면 이 호출 하나만 시험으로 보낸다.
    def before_call(self):
        with self.lock:
            if self.opened_at is None:
                return
            left = self.opened_at + BREAKER_COOLDOWN_S - time.monotonic()
            if left > 0 or self.trial:
                raise retry_later(503, "UPSTREAM_UNAVAILABLE", "Model upstream circuit open", left)
            self.trial = True

    # upstream 호출 결과를 반영한다. 성공이면 닫고, 실패가 쌓이거나 시험 호출이 실패하면 (다시) 연다.
    def after_call(self, ok):
        with self.lock:
            was_trial, self.trial = self.trial, False
            if ok:
                self.failures, self.opened_at = 0, None
                return
            self.failures += 1
            if was_trial or self.failures >= BREAKER_THRESHOLD:
                self.opened_at = time.monotonic()


class RateLimiter:
    """tenant·Agent마다 고정 창(window) 하나: 창이 시작된 뒤 RATE_WINDOW_S 동안 RATE_LIMIT번까지 받는다."""

    def __init__(self):
        self.lock = threading.Lock()
        self.windows = {}  # (tenantId, agentId) → [창 시작 시각, 받은 횟수]

    def reset(self):
        with self.lock:
            self.windows.clear()

    # 한 번 쓴다. 한도를 넘으면 429와 창이 끝날 때까지 남은 시간.
    # shortcut: 프로세스 메모리에만 세므로 모델 경로를 여러 개 띄우면 한도가 그 수만큼 늘어난다. 수평 확장 때 공유 저장소로 옮긴다.
    def take(self, tenant_id, agent_id):
        now = time.monotonic()
        with self.lock:
            window = self.windows.get((tenant_id, agent_id))
            if window is None or now - window[0] >= RATE_WINDOW_S:
                window = self.windows[(tenant_id, agent_id)] = [now, 0]
            if window[1] >= RATE_LIMIT:
                raise retry_later(429, "RATE_LIMITED", "Rate limit exceeded for this tenant and Agent",
                                  window[0] + RATE_WINDOW_S - now)
            window[1] += 1


# HTTP 서버를 만든다. port 0이면 OS가 빈 포트를 골라 준다.
def make_server(upstream, key, port=0):
    route = ModelRoute(upstream, key)

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
            if self.path == "/_reset":
                route.breaker.reset()
                route.limiter.reset()
                self.send_json(200, {"status": "reset"})
                return
            try:
                if self.path != "/v1/model-invocations":
                    raise ref.Fault(404, "NOT_FOUND", "Unknown path")
                out = route.invoke(self.read_json(), self.headers.get("Idempotency-Key"), trace,
                                   self.headers.get(SIGNATURE_HEADER), self.headers.get(TIMEOUT_HEADER))
                self.send_json(200, out, headers={"traceparent": out["traceparent"]})
            except ref.Fault as exc:
                # circuit open·rate limit 오류에는 다시 시도할 시점(Retry-After)을 붙인다.
                extra = {"Retry-After": str(exc.retry_after)} if hasattr(exc, "retry_after") else None
                self.send_json(exc.status, exc.problem(trace), "application/problem+json", extra)
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
    # 키가 없으면 서명을 확인할 수 없으므로 아예 뜨지 않는다.
    if not os.environ.get(KEY_ENV):
        sys.exit(f"{KEY_ENV} is required")
    server = make_server(args.upstream, os.environ[KEY_ENV], args.port)
    print(server.server_address[1], flush=True)
    server.serve_forever()
