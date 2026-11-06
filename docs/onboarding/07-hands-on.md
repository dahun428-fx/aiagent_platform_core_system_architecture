# 30분 실습: 로컬에서 직접 돌려 보기

> 온보딩 안내서입니다. 모든 명령은 이 저장소의 로컬 mock만 사용합니다. 회사 IdP, 실제 비밀값, 외부 모델에는 접속하지 않습니다.

앞에서 읽은 흐름을 직접 확인해 봅니다. 준비물은 Python 3.11 이상입니다. TypeScript 실습까지 하려면 Node.js 22 이상도 필요합니다.

## 준비 (5분)

저장소 루트에서 가상환경을 만들고 개발 의존성을 설치합니다. 이 단계만 인터넷이 필요합니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

Windows에서는 `.venv/bin/python` 대신 `.venv\Scripts\python`을 쓰고, 한글 출력이 깨지면 `set PYTHONUTF8=1`을 먼저 실행하세요.

## 실습 1. Manifest 검증하기 (5분)

정상 Manifest 네 개를 검증합니다.

```sh
.venv/bin/python scripts/agentctl.py validate examples/manifests/*.json
```

모두 `"valid": true`가 나옵니다. 이번에는 일부러 틀린 Manifest를 넣어 봅니다.

```sh
.venv/bin/python scripts/agentctl.py validate examples/negative/unexpected-secret.json
```

```json
[
  {
    "file": "examples/negative/unexpected-secret.json",
    "valid": false,
    "error": "Invalid or unreadable Agent Manifest"
  }
]
```

이 파일은 정상 Manifest의 `identity`에 `"secret": "should-never-be-here"` 한 줄만 추가한 것입니다. 스키마가 정의되지 않은 필드를 허용하지 않기 때문에 비밀값이 Manifest에 섞여 들어갈 수 없습니다.

해 볼 것: `examples/manifests/tool.json`을 복사해서 `source.revision`을 `main`으로 바꾸고 검증해 보세요. 브랜치 이름처럼 바뀌는 값은 불변 버전이 아니라서 거부됩니다.

## 실습 2. Agent 호출하기 (10분)

터미널을 두 개 엽니다. 첫 번째 터미널에서 로컬 mock 플랫폼을 띄웁니다.

```sh
.venv/bin/python examples/python/platform_ref.py
```

```text
Local synthetic Agent Gateway: http://127.0.0.1:8765 ; Ctrl-C to stop
```

이 mock은 Agent Gateway → Runtime → Model Gateway의 동기 흐름과 Tool Gateway → Credential Broker 흐름을 흉내 냅니다. loopback(127.0.0.1)에만 열리고, 정해진 합성 토큰 `mock-user`만 받습니다.

두 번째 터미널에서 Python 클라이언트로 Agent를 부릅니다.

```sh
.venv/bin/python examples/python/client.py
```

```json
{
  "invocationId": "inv-79b4fa3420244ae4bccb3b4a3473dea6",
  "agentVersion": "0.1.0",
  "status": "succeeded",
  "output": {"type": "message", "content": "mock:hello"},
  "traceparent": "00-1b0f13dcfd2f426a87937b2bb6d7f852-ac2cb29d6d8f4c46-01",
  "routeDecisionId": "route-self-hosted",
  "usage": {"inputTokens": 1, "outputTokens": 1}
}
```

결과를 [요청 하나 따라가기](03-one-request.md)와 맞춰 읽어 보세요.

- `invocationId`: Gateway가 붙인 호출 ID
- `agentVersion`: Registry에서 찾은 불변 버전
- `traceparent`: 요청 전체를 잇는 추적 정보
- `routeDecisionId`: Model Gateway가 고른 경로. 여기서는 자체 호스팅 경로로 갔습니다

`examples/python/client.py`를 열어 보면 요청에 `Authorization: Bearer mock-user`와 `Idempotency-Key` 헤더가 들어 있습니다.

## 실습 3. 일부러 실패시켜 보기 (5분)

토큰 없이 부르면 어떻게 될까요? 두 번째 터미널에서 실행합니다.

```sh
curl -i -X POST http://127.0.0.1:8765/v1/agents/agent-demo/invocations \
  -H "Content-Type: application/json" \
  -d '{"input":{"type":"message","content":"hello"},"context":{"tenantId":"tenant-demo","dataClassification":"internal"},"execution":{"mode":"sync","timeoutMs":5000}}'
```

```text
HTTP/1.0 401 Unauthorized
Content-Type: application/problem+json

{"type": "about:blank", "title": "UNAUTHENTICATED", "status": 401, "detail": "Mock token required", "code": "UNAUTHENTICATED", "traceId": "…"}
```

RFC 9457 Problem Details 형식의 오류가 돌아옵니다. 기본은 거부라는 원칙을 눈으로 확인한 것입니다.

이번에는 같은 `Idempotency-Key`로 내용만 바꿔 두 번 보내 봅니다. 첫 번째는 `content`가 `hello`, 두 번째는 `bye`입니다.

```sh
curl -X POST http://127.0.0.1:8765/v1/agents/agent-demo/invocations \
  -H "Content-Type: application/json" -H "Authorization: Bearer mock-user" -H "Idempotency-Key: k1" \
  -d '{"input":{"type":"message","content":"hello"},"context":{"tenantId":"tenant-demo","dataClassification":"internal"},"execution":{"mode":"sync","timeoutMs":5000}}'
curl -X POST http://127.0.0.1:8765/v1/agents/agent-demo/invocations \
  -H "Content-Type: application/json" -H "Authorization: Bearer mock-user" -H "Idempotency-Key: k1" \
  -d '{"input":{"type":"message","content":"bye"},"context":{"tenantId":"tenant-demo","dataClassification":"internal"},"execution":{"mode":"sync","timeoutMs":5000}}'
```

첫 번째는 성공하고, 두 번째는 409로 거부됩니다.

```text
{"type": "about:blank", "title": "CONFLICT", "status": 409, "detail": "Idempotency key reused for different request", "code": "CONFLICT", "traceId": "…"}
```

같은 키로 같은 요청을 다시 보내면 저장된 결과를 돌려주고, 다른 요청을 보내면 거부합니다. 네트워크 문제로 재전송해도 Agent가 두 번 실행되지 않게 하는 장치입니다.

## 실습 4. TypeScript 클라이언트 (선택, 5분)

```sh
npm install
npm run build:client
node examples/typescript/dist/demo.js
```

같은 Agent를 TypeScript로 부릅니다. 계약이 언어 중립이라 클라이언트 언어가 달라도 결과 모양은 같습니다. Python은 참조 구현, TypeScript는 핵심 클라이언트 예제이고, 어느 언어도 강제하지 않습니다.

## 실습 5. 전체 테스트 돌리기 (선택)

```sh
.venv/bin/python -m unittest discover -s tests -v
```

스키마, API, 권한, idempotency, 승인, 모델 정책, 평가, 포털 정합성 테스트가 돕니다. 테스트 이름을 훑어보면 이 플랫폼이 무엇을 지키려는지 목록으로 볼 수 있습니다.

## 이 mock이 하지 않는 것

실습 결과를 production 동작으로 오해하지 않도록 정리합니다.

- 실제 JWT 검증, 회사 IdP·STS 연동을 하지 않습니다. 토큰은 고정된 합성 값입니다.
- 실제 외부·자체 호스팅 모델, REST/MCP 도구 서버, 벡터 DB에 연결하지 않습니다.
- idempotency는 메모리에만 저장해서 재시작하면 사라집니다.
- Agent invoke와 health 외의 API는 501을 돌려줍니다.

자세한 범위는 [제공 범위와 한계](../release-scope.md)에 있습니다.

이전: [내 Agent가 production까지 가는 길](06-lifecycle.md) · 다음: [규격 문서 읽는 법과 자주 묻는 질문](08-reading-the-spec.md)
