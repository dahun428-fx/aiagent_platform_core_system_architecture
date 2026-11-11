"""참조 구현의 Agent Platform APIs + Runtime을 그대로 띄우되, 모델 호출만 별도 Agent Gateway 모델 경로 서비스로
HTTP를 거쳐 보내도록 바꾼다.

모델 경로로 가는 요청에는 공유 비밀값(환경 변수 IMPL_INTERNAL_KEY)으로 만든 서명을 붙인다.
Agent 호출마다 deadline을 정한다: 요청 본문의 execution.timeoutMs와 앱이 보낸 Request-Timeout-Ms 중 짧은 쪽.
모델 경로에는 남은 시간을 Request-Timeout-Ms로 넘기고, 시간이 다 되면 504 UPSTREAM_TIMEOUT.
네트워크 경계를 넘는 것은 아직 모델 경로뿐이다. 도구 경로와 Credential Broker는 아직 같은 프로세스 안에 있다.
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
        # shortcut: 모델 호출마다 새 키를 만들어서 앱이 재시도해도 여기서는 중복이 걸러지지 않는다. S5에서 앱 키로부터 만든다.
        # 본문 전체에 서명해서, 모델 경로가 identity·policy가 중간에 바뀌지 않았음을 확인할 수 있게 한다.
        headers = {"traceparent": traceparent, "Idempotency-Key": "model-" + uuid.uuid4().hex,
                   SIGNATURE_HEADER: sign(self.key, body)}
        # 남은 시간을 계산해 모델 경로에 넘긴다. 이미 다 썼으면 모델 경로를 부르지 않고 바로 504.
        deadline = getattr(current, "deadline", None)
        left = None if deadline is None else deadline - time.monotonic()
        if left is not None and left * 1000 < 1:
            raise ref.Fault(504, "UPSTREAM_TIMEOUT", "Invocation deadline exceeded")
        if left is not None:
            headers[TIMEOUT_HEADER] = str(int(left * 1000))
        try:
            status, _, out = call_json("POST", self.base_url + "/v1/model-invocations", body, headers,
                                       timeout=(left if left is not None else 5.0) + ANSWER_MARGIN_S)
        except TimeoutError:
            # 모델 경로마저 시간 안에 답하지 않은 경우. 연결은 여기서 끊긴다.
            raise ref.Fault(504, "UPSTREAM_TIMEOUT", "Agent Gateway model route timed out") from None
        except ConnectionError:
            # 모델 경로 서비스에 연결조차 안 되는 경우
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Agent Gateway model route unreachable") from None
        # 정책 거부(403)만 호출자 책임이다. 시간 초과(504)는 그대로 전한다.
        # 그 밖의 실패는 잘못된 결과까지 포함해 우리 쪽 문제이므로 4xx가 아닌 503으로 돌려준다.
        if status == 403:
            raise ref.Fault(403, "FORBIDDEN", "Policy denied")
        if status == 504:
            raise ref.Fault(504, "UPSTREAM_TIMEOUT", "Model upstream timed out")
        if status != 200:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Model route failed")
        try:
            ref.validate("model-result", out)
        except ref.Fault:
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Model route returned an invalid result") from None
        return out


# 참조 구현 서버를 만들고, 모델 호출 부분만 HttpModelRoute로 교체한다.
def make_server(gateway_url, key, port=0):
    server = ref.make_server(port)
    platform = ref.platform_of(server)
    route = HttpModelRoute(gateway_url, key)
    # Runtime도 모델 참조를 따로 들고 있으므로 두 곳을 모두 바꿔야 한다.
    platform.model = route
    platform.runtime.model = route
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
            try:
                super().do_POST()
            finally:
                current.timeout_header = None

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
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    # 키가 없으면 모델 경로가 모든 요청을 거부하므로 아예 뜨지 않는다.
    if not os.environ.get(KEY_ENV):
        sys.exit(f"{KEY_ENV} is required")
    server = make_server(args.gateway, os.environ[KEY_ENV], args.port)
    print(server.server_address[1], flush=True)
    server.serve_forever()
