# 로컬 환경 구성 및 호출 실습

> 개발자 가이드 문서입니다. 모든 명령은 이 저장소의 로컬 mock만 사용하며, 회사 IdP, 실제 시크릿·자격증명, 외부 모델에는 접속하지 않습니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Manifest](09-glossary.md#term-manifest) [멱등성 키](09-glossary.md#term-idempotency) [traceparent](09-glossary.md#term-trace) [routeDecisionId](09-glossary.md#term-route-decision) [Problem Details](09-glossary.md#term-problem) [mock](09-glossary.md#term-mock)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 실습 목표**

- Manifest 검증 도구로 정상·비정상 Manifest의 검증 결과를 확인합니다.
- 로컬 mock 환경에서 Agent를 호출하고 응답 필드를 해석합니다.
- 인증 실패와 멱등성 충돌 시 반환되는 오류 응답을 확인합니다.
</div>

## 사전 요구사항

<div class="cards">
<div class="card">{{icon:code}}<b>Python 3.11 이상</b><p>실습 1~3, 5에 필요합니다.</p></div>
<div class="card">{{icon:code}}<b>Node.js 22 이상</b><p>실습 4(TypeScript 클라이언트)에만 필요합니다.</p></div>
<div class="card">{{icon:laptop}}<b>터미널 2개</b><p>mock 서버 실행용과 클라이언트 실행용</p></div>
</div>

<ol class="flow">
<li>{{icon:manifest}}<b>실습 1</b><span>Manifest 검증<br>예상 소요 5분</span></li>
<li>{{icon:gateway}}<b>실습 2</b><span>Agent 호출<br>예상 소요 10분</span></li>
<li>{{icon:cross}}<b>실습 3</b><span>인증 실패·멱등성 충돌<br>예상 소요 5분</span></li>
<li>{{icon:code}}<b>실습 4</b><span>TypeScript 클라이언트<br>선택</span></li>
<li>{{icon:test}}<b>실습 5</b><span>전체 테스트<br>선택</span></li>
</ol>

## 환경 구성

저장소 루트에서 가상 환경을 생성하고 개발 의존성을 설치합니다. 이 단계에서만 네트워크 연결이 필요합니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

<div class="point" markdown="1">
**{{icon:laptop}} Windows 환경** `.venv/bin/python` 대신 `.venv\Scripts\python`을 사용합니다. 한글 출력이 깨지면 먼저 `set PYTHONUTF8=1`을 실행합니다.
</div>

## 실습 1. Manifest 검증

정상 Manifest 4종을 검증합니다.

```sh
.venv/bin/python scripts/agentctl.py validate examples/manifests/*.json
```

모든 파일에 대해 `"valid": true`가 출력됩니다. 다음으로 검증 실패용 Manifest를 검증합니다.

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

이 파일은 정상 Manifest의 `identity` 블록에 `"secret": "should-never-be-here"`를 추가한 것입니다. JSON Schema가 정의되지 않은 필드를 허용하지 않으므로 이 필드는 거부됩니다. 다만 `metadata.labels`처럼 허용된 문자열 필드에 들어간 값은 스키마가 의미를 검사하지 않습니다. 구조 검증과 시크릿 검사는 별개의 통제이므로, 시크릿 스캔과 코드 리뷰를 함께 적용합니다.

<div class="point" markdown="1">
**{{icon:bulb}} 추가 확인** `examples/manifests/tool.json`을 복사한 뒤 `source.revision`을 `main`으로 변경하고 검증합니다. 브랜치 이름과 같은 가변 참조는 불변 버전이 아니므로 검증에 실패합니다.
</div>

## 실습 2. Agent 호출

첫 번째 터미널에서 로컬 mock 플랫폼을 실행합니다.

```sh
.venv/bin/python examples/python/platform_ref.py
```

```text
Local synthetic Agent Gateway: http://127.0.0.1:8765 ; Ctrl-C to stop
```

이 mock은 Agent Platform APIs(Agent 호출 API) → Runtime → Agent Gateway 모델 경로의 동기 처리 흐름과, Agent Gateway 도구 경로 → Credential Broker 흐름을 모사합니다. 실행 시 표시되는 `Local synthetic Agent Gateway`와 출력·코드의 `agent-gateway`, `model-gateway`는 legacy 이름이며, 각각 Agent Platform APIs의 Agent 호출 API와 Agent Gateway 모델 경로를 가리킵니다. loopback(127.0.0.1)에만 바인딩되며, 고정된 합성 토큰 `mock-user`만 허용합니다.

두 번째 터미널에서 Python 클라이언트로 Agent를 호출합니다.

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

응답 필드를 [Agent 요청 처리 흐름](03-one-request.md)과 대조합니다.

| 필드 | 생성 주체 | 의미 |
|---|---|---|
| {{icon:gateway}} `invocationId` | Agent Platform APIs | 호출 식별자 |
| {{icon:manifest}} `agentVersion` | Registry | 실행된 불변 버전 |
| {{icon:trace}} `traceparent` | 전 구간 | 종단 간 실행 추적 컨텍스트 |
| {{icon:model}} `routeDecisionId` | Agent Gateway 모델 경로 | 모델 라우팅 결정. 이 예시에서는 자체 호스팅 경로 |
| {{icon:eye}} `usage` | Agent Gateway 모델 경로 | 토큰 사용량 |

`examples/python/client.py`의 요청에는 `Authorization: Bearer mock-user`와 `Idempotency-Key` 헤더가 포함되어 있습니다.

## 실습 3. 인증 실패 및 멱등성 충돌 검증

토큰 없이 호출합니다.

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

RFC 9457 Problem Details 형식의 오류가 반환됩니다. 기본 거부(deny by default) 원칙에 따른 동작입니다.

다음으로 동일한 `Idempotency-Key`로 내용이 다른 요청 두 건을 전송합니다. 첫 번째 요청의 `content`는 `hello`, 두 번째는 `bye`입니다.

```sh
curl -X POST http://127.0.0.1:8765/v1/agents/agent-demo/invocations \
  -H "Content-Type: application/json" -H "Authorization: Bearer mock-user" -H "Idempotency-Key: k1" \
  -d '{"input":{"type":"message","content":"hello"},"context":{"tenantId":"tenant-demo","dataClassification":"internal"},"execution":{"mode":"sync","timeoutMs":5000}}'
curl -X POST http://127.0.0.1:8765/v1/agents/agent-demo/invocations \
  -H "Content-Type: application/json" -H "Authorization: Bearer mock-user" -H "Idempotency-Key: k1" \
  -d '{"input":{"type":"message","content":"bye"},"context":{"tenantId":"tenant-demo","dataClassification":"internal"},"execution":{"mode":"sync","timeoutMs":5000}}'
```

첫 번째 요청은 성공하고, 두 번째 요청은 409로 거부됩니다.

```text
{"type": "about:blank", "title": "CONFLICT", "status": 409, "detail": "Idempotency key reused for different request", "code": "CONFLICT", "traceId": "…"}
```

동일한 키로 동일한 요청을 재전송하면 저장된 결과를 반환하고, 다른 요청을 전송하면 거부합니다. 네트워크 오류로 재전송하더라도 Agent가 중복 실행되지 않도록 하는 멱등성(Idempotency) 처리입니다.

## 실습 4. TypeScript 클라이언트 (선택)

```sh
npm install
npm run build:client
node examples/typescript/dist/demo.js
```

동일한 Agent를 TypeScript 클라이언트로 호출합니다. API 계약이 언어 중립적이므로 클라이언트 언어와 관계없이 응답 형식은 동일합니다. Python은 참조 구현, TypeScript는 핵심 클라이언트 예제이며, 특정 언어를 강제하지 않습니다.

## 실습 5. 전체 테스트 실행 (선택)

```sh
.venv/bin/python -m unittest discover -s tests -v
```

JSON Schema, API, 인가, 멱등성, 승인, 모델 정책, 평가, 포털 정합성 테스트가 실행됩니다. 테스트 목록으로 플랫폼이 검증하는 규칙을 확인할 수 있습니다.

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `OSError: [Errno 48/98] Address already in use` 또는 `WinError 10048` | 8765 포트를 다른 프로세스가 사용 중 | 기존 mock 서버를 종료(Ctrl-C)하거나 해당 프로세스를 종료 |
| `ModuleNotFoundError: jsonschema` | 가상 환경이 아닌 다른 Python으로 실행 | `.venv/bin/python`(Windows: `.venv\Scripts\python`)으로 실행 |
| `node: cannot find module .../dist/demo.js` | TypeScript 빌드 누락 | `npm run build:client` 실행 |
| 브라우저 검사 실패 | Chromium 미설치 | `npx playwright install chromium` |
| 401 `UNAUTHENTICATED` | `Authorization: Bearer mock-user` 누락 | 헤더 추가 |
| 409 `CONFLICT` | 같은 `Idempotency-Key`로 다른 요청 전송 | 새 키 사용 |
| 501 `NOT_IMPLEMENTED` | mock이 구현하지 않은 경로·실행 모드(`async`, `durable`) | `sync` 호출만 사용 |
| PowerShell에서 `curl` 옵션 오류 | `curl`이 `Invoke-WebRequest` 별칭 | `curl.exe`로 실행 |
| PowerShell에서 `*.json` 미확장 | 셸 wildcard 차이 | `Get-ChildItem examples/manifests/*.json | % { .venv\Scripts\python scripts/agentctl.py validate $_.FullName }` |

## mock 제공 범위

<div class="compare" markdown="1">
<div class="good" markdown="1">
**{{icon:check}} mock이 모사하는 기능**

- Agent Platform APIs → Runtime → Agent Gateway 모델 경로 동기 처리 흐름
- Agent Gateway 도구 경로 → Credential Broker 흐름
- 토큰 누락, 멱등성 키 재사용 시 거부 동작
</div>
<div class="bad" markdown="1">
**{{icon:cross}} mock이 제공하지 않는 기능**

- 실제 JWT 검증, 회사 IdP·STS 연동 (토큰은 고정된 합성 값)
- 실제 모델, REST/MCP 도구 서버, 벡터 DB 연결
- 재시작 후에도 유지되는 멱등성 저장소 (메모리 저장)
- invoke·health 외 API (501 반환)
</div>
</div>

상세 범위는 [제공 범위와 한계](../release-scope.md)를 참고하십시오.

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. 토큰 없이 호출하면 어떤 상태 코드와 형식이 반환됩니까?</summary>
401과 RFC 9457 Problem Details(<code>application/problem+json</code>)가 반환됩니다.
</details>

<details markdown="1"><summary>Q2. 동일한 Idempotency-Key로 동일한 요청을 재전송하면 Agent가 다시 실행됩니까?</summary>
다시 실행되지 않으며 저장된 결과를 반환합니다. 요청 내용이 다르면 409로 거부합니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- Manifest 검증은 시크릿 포함, 가변 revision, 형식 오류를 실행 전에 차단합니다.
- 응답의 `invocationId`, `traceparent`, `routeDecisionId`로 요청의 처리 경로를 확인할 수 있습니다.
- 기본 거부 원칙에 따라 토큰 누락이나 멱등성 키 재사용 요청은 실행되지 않습니다.
</div>

<nav class="pager"><a href="06-lifecycle.md"><small>이전</small><b>Agent 수명주기·Tuning과 프로덕션 승인</b></a><a class="next" href="14-connect-your-agent.md"><small>다음</small><b>내 Agent 연결과 적합성 검증</b></a></nav>
