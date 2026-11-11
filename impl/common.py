"""impl/ 서비스들이 함께 쓰는 도구: 참조 구현 모듈 로딩, 작은 JSON HTTP 서버와 클라이언트, 내부 구간 서명."""
from __future__ import annotations

import hmac
import importlib.util
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]  # 저장소 루트
KEY_ENV = "IMPL_INTERNAL_KEY"  # 내부 구간 서명에 쓰는 공유 비밀값을 담는 환경 변수 이름
SIGNATURE_HEADER = "X-Internal-Signature"
TIMEOUT_HEADER = "Request-Timeout-Ms"  # 호출자에게 남은 시간(ms). 계약 0.2.0(ADR-038)
MAX_BODY = 65536  # 요청 본문 최대 크기(64KB). 이보다 크면 거부한다.


# examples/ 의 참조 구현을 한 번만 불러와 모두가 공유한다.
# sys.modules 에 등록해 두므로 계약 검증기와 Fault 클래스가 어디서 불러도 같은 객체다.
def load_ref():
    if "platform_ref" in sys.modules:
        return sys.modules["platform_ref"]
    spec = importlib.util.spec_from_file_location("platform_ref", ROOT / "examples/python/platform_ref.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["platform_ref"] = module
    spec.loader.exec_module(module)
    return module


class JsonHandler(BaseHTTPRequestHandler):
    """기본 HTTP 핸들러: 접속 로그를 끄고, 본문 크기를 제한해 JSON을 읽고, JSON으로 응답한다."""

    # 요청마다 찍히는 접속 로그를 끈다.
    def log_message(self, *_):
        pass

    # 요청 본문을 JSON으로 읽는다. 크기가 0이거나 64KB를 넘으면 ValueError.
    def read_json(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0 or size > MAX_BODY:
            raise ValueError("invalid body size")
        return json.loads(self.rfile.read(size))

    # JSON 응답을 보낸다. 브라우저가 내용 형식을 추측하지 않도록 nosniff 헤더를 붙인다.
    def send_json(self, status, payload, content_type="application/json", headers=None):
        raw = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(raw)


# 서버를 127.0.0.1(이 컴퓨터)에만 바인딩한다. port 0이면 OS가 빈 포트를 골라 준다. 요청마다 스레드 하나.
def serve(handler_class, port):
    return ThreadingHTTPServer(("127.0.0.1", port), handler_class)


# 내부 구간 서명: 요청 본문을 키 순서와 공백을 고정한 JSON(참조 구현의 canonical_digest)으로 만든 뒤 HMAC-SHA256으로 서명한다.
# 본문의 identity·policy가 한 글자라도 바뀌면 서명이 맞지 않는다.
# shortcut: 만료 시각이나 nonce가 없어 가로챈 요청을 그대로 다시 보내면 통과한다. 3단계(Identity)에서 워크로드 토큰으로 바꾼다.
def sign(key, body):
    return hmac.new(key.encode(), load_ref().canonical_digest(body).encode(), "sha256").hexdigest()


# JSON HTTP 요청을 보내고 (상태 코드, 헤더, JSON 본문)을 돌려준다.
# 4xx·5xx 응답도 예외 없이 그대로 돌려준다. 시간 안에 답이 없으면 TimeoutError, 연결 자체가 안 되면 ConnectionError.
# shortcut: urllib의 timeout은 소켓 동작 하나(연결, 읽기 한 번)마다 걸린다. 조금씩 흘려 보내는 upstream은 전체로는 더 오래 걸릴 수 있다.
#           실제 upstream을 붙일 때 전체 시간 상한을 따로 둔다.
def call_json(method, url, body=None, headers=None, timeout=5.0):
    data = None if body is None else json.dumps(body).encode()
    req = Request(url, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.status, dict(response.headers), json.loads(response.read() or b"null")
    except HTTPError as exc:
        raw = exc.read()
        return exc.code, dict(exc.headers), json.loads(raw) if raw else None
    except TimeoutError:
        raise  # 읽는 중 시간 초과. 이 함수를 빠져나가면서 연결이 닫히므로 upstream도 끊긴 것을 안다.
    except URLError as exc:
        if isinstance(exc.reason, TimeoutError):  # 연결하는 중 시간 초과
            raise TimeoutError(str(exc)) from exc
        raise ConnectionError(str(exc)) from exc
    except OSError as exc:
        raise ConnectionError(str(exc)) from exc
