"""참조 구현의 Agent Platform APIs + Runtime을 그대로 띄우되, 모델 호출만 별도 Agent Gateway 모델 경로 서비스로
HTTP를 거쳐 보내도록 바꾼다.

모델 경로로 가는 요청에는 공유 비밀값(환경 변수 IMPL_INTERNAL_KEY)으로 만든 서명을 붙인다.
네트워크 경계를 넘는 것은 아직 모델 경로뿐이다. 도구 경로와 Credential Broker는 아직 같은 프로세스 안에 있다.
GET /_audit 은 이 프로세스의 감사 기록을 돌려준다 (로컬 시나리오 확인용).
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import KEY_ENV, SIGNATURE_HEADER, call_json, load_ref, sign  # noqa: E402

ref = load_ref()
# 모델 경로 쪽 upstream timeout(5초)보다 길게 잡아서, 모델 경로가 먼저 실패를 판단하게 한다.
GATEWAY_TIMEOUT_S = 10.0


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
        try:
            status, _, out = call_json("POST", self.base_url + "/v1/model-invocations", body, headers,
                                       timeout=GATEWAY_TIMEOUT_S)
        except ConnectionError:
            # 모델 경로 서비스에 연결조차 안 되는 경우
            raise ref.Fault(503, "UPSTREAM_UNAVAILABLE", "Agent Gateway model route unreachable") from None
        # 정책 거부(403)만 호출자 책임이다. 그 밖의 실패는 잘못된 결과까지 포함해 우리 쪽 문제이므로 4xx가 아닌 503으로 돌려준다.
        if status == 403:
            raise ref.Fault(403, "FORBIDDEN", "Policy denied")
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

    # 참조 구현 핸들러를 상속해서 GET /_audit 하나만 추가한다.
    class Handler(base):
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
