"""참조 구현의 Agent Platform APIs + Runtime을 그대로 띄우되, 모델·도구 호출을 별도 Agent Gateway 서비스
(모델 경로, 도구 경로)로 HTTP를 거쳐 보내도록 바꾼다.

모델 경로로 가는 요청에는 공유 비밀값(환경 변수 IMPL_INTERNAL_KEY)으로 만든 서명을 붙인다.
Agent 호출마다 deadline을 정한다: 요청 본문의 execution.timeoutMs와 앱이 보낸 Request-Timeout-Ms 중 짧은 쪽.
모델 경로에는 남은 시간을 Request-Timeout-Ms로 넘기고, 시간이 다 되면 504 UPSTREAM_TIMEOUT.
Credential Broker는 아직 도구 경로 프로세스 안에 있다(네트워크 분리는 후속 조각).
GET /_audit 은 이 프로세스의 감사 기록을 돌려준다 (로컬 시나리오 확인용).
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import KEY_ENV, SIGNATURE_HEADER, TIMEOUT_HEADER, call_json, load_ref, sign  # noqa: E402

ref = load_ref()
# 모델 경로가 남은 시간에 맞춰 먼저 504를 돌려줄 수 있도록, 여기서는 그보다 조금 더 기다린다.
ANSWER_MARGIN_S = 0.1
# 모델 경로가 돌려준 upstream 실패 상태와 오류 코드(계약 0.2.0, ADR-038)
UPSTREAM_FAULTS = {429: "RATE_LIMITED", 502: "UPSTREAM_ERROR", 503: "UPSTREAM_UNAVAILABLE", 504: "UPSTREAM_TIMEOUT"}
# 요청 스레드마다 지금 처리 중인 Agent 호출의 deadline(time.monotonic 기준)을 담는다.
# ThreadingHTTPServer는 요청 하나를 스레드 하나가 끝까지 처리하므로, Runtime을 고치지 않고 모델 호출까지 전달된다.
current = threading.local()


# 앱이 보낸 Request-Timeout-Ms 헤더 값을 ms 정수로 읽는다. 없거나 1 이상의 정수가 아니면 None.
# shortcut: 잘못된 값은 422로 거부하지 않고 무시한다(본문의 timeoutMs는 그대로 적용된다). Platform APIs를 직접 구현할 때 422로 바꾼다.
def header_ms(value):
    return int(value) if value and value.isascii() and value.isdigit() and int(value) >= 1 else None


# 본문의 timeoutMs와 헤더 값 중 짧은 쪽으로 이번 호출의 deadline을 정한다. 본문이 계약에 안 맞으면 정하지 않는다(뒤에서 422).
def deadline_for(body, header_value):
    limits = [header_ms(header_value)]
    if isinstance(body, dict) and isinstance(body.get("execution"), dict):
        limits.append(body["execution"].get("timeoutMs"))
    limits = [v for v in limits if isinstance(v, int) and v >= 1]
    return time.monotonic() + min(limits) / 1000 if limits else None


# Gateway의 한 경로(모델·도구)에 서명한 요청을 보내고 (상태, 헤더, 본문)을 돌려준다. 두 경로가 함께 쓰는 부분:
#   남은 시간을 Request-Timeout-Ms로 넘기고(이미 다 썼으면 보내지 않고 504), 연결 실패는 503, 시간 초과는 504.
#   정책 거부 403과 Gateway가 정한 upstream 실패(429·502·503·504)는 같은 상태로 전하고, Retry-After도 앱 응답까지 전한다.
# 재시도는 Gateway가 이미 했으므로 여기서는 다시 시도하지 않는다(단계마다 재시도하면 횟수가 곱해진다).
def post_signed(url, body, key, traceparent, idempotency_key, name):
    # 본문 전체에 서명해서, Gateway가 identity·policy가 중간에 바뀌지 않았음을 확인할 수 있게 한다.
    headers = {"traceparent": traceparent, "Idempotency-Key": idempotency_key, SIGNATURE_HEADER: sign(key, body)}
    deadline = getattr(current, "deadline", None)
    left = None if deadline is None else deadline - time.monotonic()
    if left is not None and left * 1000 < 1:
        raise ref.Fault(504, "UPSTREAM_TIMEOUT", "Invocation deadline exceeded")
    if left is not None:
        headers[TIMEOUT_HEADER] = str(int(left * 1000))
    try:
        # Gateway가 남은 시간에 맞춰 먼저 504를 줄 수 있도록 여기서는 조금 더(ANSWER_MARGIN_S) 기다린다.
        status, resp_headers, out = call_json("POST", url, body, headers,
                                              timeout=(left if left is not None else 5.0) + ANSWER_MARGIN_S)
    except TimeoutError:
        raise ref.Fault(504, "UPSTREAM_TIMEOUT", f"Agent Gateway {name} route timed out") from None
    except ConnectionError:
        raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", f"Agent Gateway {name} route unreachable") from None
    if status == 403:
        raise ref.Fault(403, "FORBIDDEN", "Policy denied")
    if status in UPSTREAM_FAULTS:
        # Gateway가 준 Retry-After(초)를 앱 응답까지 전한다. 아래 Handler.end_headers가 헤더로 붙인다.
        retry_after = {k.lower(): v for k, v in resp_headers.items()}.get("retry-after")
        if retry_after and retry_after.isascii() and retry_after.isdigit():
            current.retry_after = retry_after
        detail = "Rate limit exceeded" if status == 429 else f"{name.capitalize()} upstream failed"
        raise ref.Fault(status, UPSTREAM_FAULTS[status], detail)
    return status, out


class HttpModelRoute:
    """ref.ModelGateway.invoke 와 같은 모양의 함수를 HTTP로 구현한다. 오류 응답은 다시 ref.Fault 로 바꾼다.

    이 클래스로 바꿔 끼우기만 하면 Runtime 코드는 손대지 않고 모델 호출이 네트워크를 넘게 된다.
    """

    def __init__(self, base_url, key):
        self.base_url = base_url.rstrip("/")
        self.key = key  # 모델 경로와 공유하는 서명 키

    # Runtime이 모델을 부를 때마다 실행된다: model-request를 만들어 모델 경로 서비스로 보낸다.
    def invoke(self, content, identity, policy, traceparent):
        body = {"capability": "chat", "messages": [{"role": "user", "content": content}],
                "identity": identity, "policy": policy, "traceparent": traceparent}
        # shortcut: 모델 호출마다 새 키를 만들어서 앱이 재시도해도 여기서는 중복이 걸러지지 않는다.
        #           모델 호출은 외부 효과가 없어 지금은 문제가 없다. 비용 중복을 막아야 할 때 앱 키로부터 만든다.
        status, out = post_signed(self.base_url + "/v1/model-invocations", body, self.key, traceparent,
                                  "model-" + uuid.uuid4().hex, "model")
        # 모델 경로의 그 밖의 응답(4xx, 500, 계약에 안 맞는 200)은 우리 쪽 upstream이 잘못 답한 것이므로 502.
        if status != 200:
            raise ref.Fault(502, "UPSTREAM_ERROR", "Model route failed")
        try:
            ref.validate("model-result", out)
        except ref.Fault:
            raise ref.Fault(502, "UPSTREAM_ERROR", "Model route returned an invalid result") from None
        return out


class HttpToolRoute:
    """ref.ToolGateway.invoke 와 같은 모양의 함수를 HTTP로 구현한다. Runtime이 만든 tool-invoke를 그대로 도구 경로로 보낸다.

    Runtime은 앱의 Idempotency-Key에 ":tool-<순번>"을 붙여 도구 호출 키를 만들므로, 앱이 같은 키로 다시 보내면
    도구 경로의 effect ledger가 같은 키를 보고 도구를 다시 실행하지 않는다.
    """

    def __init__(self, base_url, key):
        self.base_url = base_url.rstrip("/")
        self.key = key  # 도구 경로와 공유하는 서명 키

    def invoke(self, request):
        status, out = post_signed(self.base_url + "/v1/tool-invocations", request, self.key, request["traceparent"],
                                  request["idempotencyKey"], "tool")
        # 같은 키를 다른 인자로 보냈으면 409를 그대로 전한다(호출자 책임).
        if status == 409:
            raise ref.Fault(409, "CONFLICT", "Idempotency key reused for different tool request")
        # 같은 키 요청이 아직 실행 중(202). 동기 호출이라 기다릴 수 없으므로 잠시 뒤 다시 보내라고 알린다.
        if status == 202:
            current.retry_after = "1"
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Same tool request still in progress")
        if status != 200:
            raise ref.Fault(502, "UPSTREAM_ERROR", "Tool route failed")
        try:
            ref.validate("tool-result", out)
        except ref.Fault:
            raise ref.Fault(502, "UPSTREAM_ERROR", "Tool route returned an invalid result") from None
        return out


# 참조 구현 서버를 만들고, 모델·도구 호출 부분만 HttpModelRoute·HttpToolRoute로 교체한다.
# 내장 agent-demo 외에 templates/agents 의 템플릿 Agent(도구를 쓰는 my-tool-agent 포함)도 등록한다.
def make_server(gateway_url, tools_url, key, port=0):
    server = ref.make_server(port, agents_dir=ref.ROOT / "templates/agents")
    platform = ref.platform_of(server)
    route = HttpModelRoute(gateway_url, key)
    # Runtime도 모델·도구 참조를 따로 들고 있으므로 두 곳을 모두 바꿔야 한다.
    platform.model = route
    platform.runtime.model = route
    platform.tools = platform.runtime.tools = HttpToolRoute(tools_url, key)
    base = server.RequestHandlerClass
    invoke = platform.invoke

    # Agent 호출을 감싸서, 시작할 때 deadline을 정하고 끝나면 지운다. 헤더 값은 아래 do_POST가 넣어 둔다.
    def invoke_with_deadline(agent_id, body, *args, **kwargs):
        current.deadline = deadline_for(body, getattr(current, "timeout_header", None))
        try:
            return invoke(agent_id, body, *args, **kwargs)
        finally:
            current.deadline = None

    platform.invoke = invoke_with_deadline

    # 참조 구현 핸들러를 상속해서 GET /_audit 을 추가하고, POST에서 Request-Timeout-Ms 헤더를 꺼내 둔다.
    class Handler(base):
        def do_POST(self):
            current.timeout_header = self.headers.get(TIMEOUT_HEADER)
            current.retry_after = None
            try:
                super().do_POST()
            finally:
                current.timeout_header = current.retry_after = None

        # 참조 구현의 send_json은 헤더를 더 받지 않으므로, 헤더를 닫기 직전에 Retry-After를 끼워 넣는다.
        def end_headers(self):
            if getattr(current, "retry_after", None):
                self.send_header("Retry-After", current.retry_after)
            super().end_headers()

        def do_GET(self):
            if self.path == "/_audit":
                self.send_json(200, list(platform.audit))
            else:
                super().do_GET()

    server.RequestHandlerClass = Handler
    return server


# 단독 실행: 첫 줄에 포트 번호를 출력한다. stack.py가 이 줄을 읽어 주소를 안다.
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway", required=True)
    parser.add_argument("--tools", required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    # 키가 없으면 모델 경로가 모든 요청을 거부하므로 아예 뜨지 않는다.
    if not os.environ.get(KEY_ENV):
        sys.exit(f"{KEY_ENV} is required")
    server = make_server(args.gateway, args.tools, os.environ[KEY_ENV], args.port)
    print(server.server_address[1], flush=True)
    server.serve_forever()
