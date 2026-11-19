# AI Platform Applications

> 개발자 가이드 문서입니다. 규범은 [Core Systems](../core-systems.md) 기술 표준 문서와 계약 `agent-gateway.openapi.json`이 기준입니다.

{{journey:11}}

<div class="sofar" markdown="1">
**지금까지** `invoice-summary`는 등록되고, 실행되고, 한 번 틀리고, 고쳐져 `1.3.0`으로 승인됐습니다. 장면 열 개에서 플랫폼 안쪽을 봤습니다. 마지막 장면은 사람들이 그 플랫폼을 어디서 만지는지입니다.
</div>

## 장면

같은 하루를 사람 기준으로 다시 봅니다. 민준은 터미널에서 Manifest를 검증하고 Agent를 띄웠습니다. 서연은 재무팀 업무 앱에서 질문을 보냈습니다. 지훈은 승인함에서 메일 발송과 `1.3.0`의 승격을 승인했습니다. 도구는 셋이 달랐지만, Agent를 부르고 상태를 보고 승인하는 일은 모두 같은 정문의 같은 API로 갑니다. 다만 이 가운데 지금 실제로 해 볼 수 있는 것과 아직 약속만 있는 것이 섞여 있습니다.

<div class="point" markdown="1">
**{{icon:bulb}} AI Platform Applications가 없다면** 팀마다 검증 스크립트와 승인 화면을 따로 만들고, 화면마다 다른 뒷문이 생깁니다.
</div>

## 무슨 일이 일어나나

<ol class="flow">
<li data-say="민준은 DevTools의 명령으로, 서연은 업무 앱으로, 지훈은 승인함으로 일합니다.">{{icon:laptop}}<b>1. 저마다의 도구로 일한다</b><span>DevTools · 업무 앱 · Space</span></li>
<li data-say="어느 도구든 Agent를 부르면 같은 주소로 같은 모양의 요청이 나갑니다. 화면 전용 뒷문은 없습니다." class="hi">{{icon:gateway}}<b>2. 같은 요청이 나간다</b><span>Agent Platform APIs</span></li>
<li data-say="아직 화면이나 구현이 없는 일이 있습니다. 표에서 실행, 계약만, 정의를 먼저 확인합니다.">{{icon:map}}<b>3. 아직 없는 일은 표에서 확인한다</b><span>실행 · 계약만 · 정의</span></li>
</ol>

## 실물 보기

하는 일과 길의 대응표입니다.

<!-- kind: run boundary: local -->

| 하는 일 | 터미널(DevTools) | Space 화면 | API | v0.1 |
|---|---|---|---|---|
| Manifest 검증 | `agentctl validate` | — | 계약에 API 없음 | 실행 |
| Agent 호출 | 클라이언트 예제, curl | 카탈로그에서 실행 | `invokeAgent` | 실행 |
| 실행 상태 보기 | — | 실행 목록 | `getInvocation`, `listEvents` | 계약만(mock은 501) |
| 승인 | — | 승인함 | `submitApproval` | 계약만(mock은 501) |
| 추적 보기 | — | 실행 추적 | 계약에 API 없음 | 정의 |
| 평가 결과 보기 | — | 평가 | 계약에 API 없음 | 정의 |

- **실행**: 내 PC에서 지금 돌아갑니다.
- **계약만**: 요청과 응답의 모양은 정해져 있지만 로컬 mock은 501을 돌려줍니다.
- **정의**: 무엇을 하는 곳인지만 정해져 있습니다. Space의 화면은 모두 여기에 해당합니다.

같은 호출이 두 길로 나가는 모습입니다. 민준이 터미널에서 보낸 요청과, Space 카탈로그가 만들어지면 "실행" 버튼이 보낼 요청은 같은 HTTP 요청입니다.

<!-- kind: example -->

```text
POST /v1/agents/invoice-summary/invocations
Authorization: Bearer <부른 사람의 토큰>
Idempotency-Key: <요청 번호>

{"input": {"type": "message", "content": "청구서 INV-2048 요약해 줘"},
 "context": {"tenantId": "finance", "dataClassification": "confidential"},
 "execution": {"mode": "sync", "timeoutMs": 30000}}
```

- 달라지는 것은 `Authorization`의 토큰, 곧 누가 불렀는지뿐입니다. 하준이 어느 화면에서 누르든 403인 이유입니다.
- 화면이 Agent를 직접 실행하거나 ERP에 직접 닿는 길은 없습니다.

## 직접 해 보기

<div class="sim" data-sim="roles"></div>

<ol class="mission">
<li>Agent 호출을 터미널과 Space로 각각 골라 나가는 요청을 비교하세요.</li>
<li>지훈이 승인을 지금 해 볼 수 있나요. 무엇이 돌아오나요.</li>
</ol>

## 잘못되면

**mock의 501을 장애로 오해하면** 시간을 잃습니다. 민준이 서연의 앱에 실행 상태 조회를 붙이려고 `GET /v1/invocations/{invocationId}`를 불렀더니 501이 왔습니다.

<!-- kind: run boundary: local -->

```json
{"type": "about:blank", "title": "NOT_IMPLEMENTED", "status": 501, "detail": "This target API is contract-only", "code": "NOT_IMPLEMENTED", "traceId": "…"}
```

고장이 아니라 "계약만 있다"는 뜻입니다. 위 표에서 그 일이 "실행"인지 "계약만"인지 먼저 확인합니다. 계약만인 API는 응답 모양에 맞춰 앱을 준비해 둘 수는 있지만 지금 동작을 시험할 수는 없습니다.

**화면에서 손으로만 확인하고 CI에 넣지 않으면** 다음 버전에서 같은 검증을 빠뜨립니다. 민준이 `1.3.0`을 만들 때 `validate`와 `conformance`를 깜빡하면 형식이 깨진 Manifest가 등록 단계까지 갑니다. 터미널 명령으로 할 수 있는 일은 CI에 넣어 매번 자동으로 돌립니다.

<details class="more" markdown="1"><summary>더 보기: 없는 API를 가정할 때, Space의 세 화면</summary>

**계약에 없는 API가 있다고 가정하고 팀 화면을 설계하면** 붙일 곳이 없어 다시 만듭니다. 추적 보기와 평가 결과 보기는 v0.1 계약에 API가 없습니다. 대응표의 "계약에 API 없음"을 먼저 확인합니다.

Space는 Agent를 찾아 쓰고, 실행을 살피고, 승인하는 공유 작업 공간입니다. 아래 세 화면은 모두 정의 단계이고 구현이 없습니다.

| 화면 | 누가 | 하는 일 | 부르는 API |
|---|---|---|---|
| 카탈로그 | 서연 | 승인된 Agent를 찾아 실행 | `listAgents`, `getAgent`, `invokeAgent` |
| 실행 추적 | 민준 | 호출 번호로 실행 상태와 이벤트 확인 | `getInvocation`, `listEvents` |
| 승인함 | 지훈 | 기다리는 쓰기 작업을 승인하거나 거절 | `submitApproval`, `cancelInvocation` |
</details>

## 내가 할 일

1. DevTools의 첫 명령 세 개를 익힙니다. `validate`, `conformance`, `run`입니다.
2. `validate`와 `conformance`를 CI에 넣습니다.
3. 앱에 기능을 붙이기 전에 대응표에서 그 API의 등급을 확인합니다.

**내 PC에서 해 보기** 저장소 루트에서 실행합니다.

```bash
python scripts/agentctl.py validate examples/agents/invoice-summary/agent-manifest.json
python scripts/agentctl.py conformance examples/agents/invoice-summary
python scripts/agentctl.py run --port 8765 --agents-dir examples/agents
curl -i -H "Authorization: Bearer mock-user" http://127.0.0.1:8765/v1/invocations/x
```

마지막 명령이 위의 501을 돌려줍니다.

<div class="scope" markdown="1">
**제공 범위 (v0.1)**

| 항목 | 등급 | 확인하는 곳 |
|---|---|---|
| DevTools CLI(`agentctl`), 템플릿, 클라이언트 예제 | 실행 | `scripts/agentctl.py`, `templates/agents/`, `examples/` |
| Agent 호출 API | 실행 | 로컬 mock |
| Agent 목록·상태 조회·취소·이벤트·승인 API | 계약 | `contracts/agent-gateway.openapi.json`. 로컬 mock은 501 |
| Space(카탈로그, 실행 추적, 승인함) | 정의 | [Core Systems](../core-systems.md) |
</div>

## 규칙으로 정리

- AI Platform Applications는 DevTools(CLI, SDK, 템플릿)와 Space(공유 작업 공간)로 이루어집니다.
- Applications와 외부 앱은 Agent Platform APIs로만 플랫폼에 들어옵니다. 화면 전용 경로를 두지 않습니다(MUST NOT). 장면 ⑪
- 화면에서 한 일도 API를 지나므로 같은 인증, 인가, 감사가 적용됩니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [AI Platform Applications](09-glossary.md#term-applications) [DevTools](09-glossary.md#term-devtools) [Space](09-glossary.md#term-space) [Agent Platform APIs](09-glossary.md#term-platform-apis) [로컬 mock](09-glossary.md#term-mock) [적합성 검증](09-glossary.md#term-conformance)
</div>

## 한 문장으로

터미널에서 하든 화면에서 하든 결국 같은 정문을 두드립니다.

<div class="check" markdown="1">
**{{icon:question}} 이해 점검**

<details markdown="1"><summary>Q1. 실행 상태 조회나 승인을 지금 어디서 해 볼 수 있나요?</summary>
아직 해 볼 수 없습니다. 두 API는 계약만 있고 로컬 mock은 501을 돌려줍니다. Space의 화면도 정의 단계입니다. 승인 검증 자체는 참조 구현의 도구 경로(S6a)에서만 실행됩니다.
</details>

<details markdown="1"><summary>Q2. 서연이 Space 카탈로그에서 Agent를 실행하는 것과 민준이 curl로 부르는 것은 플랫폼 입장에서 무엇이 다른가요?</summary>
토큰이 가리키는 사람만 다릅니다. 같은 API에 같은 모양의 요청이 도착하고 같은 관문을 지납니다.
</details>

<details markdown="1"><summary>Q3. 민준의 팀이 추적 화면을 직접 만들려고 합니다. 먼저 무엇을 확인해야 하나요?</summary>
대응표에서 추적 보기의 등급입니다. v0.1 계약에는 그 일을 위한 API가 없으므로 붙일 곳이 없습니다.
</details>
</div>

여기까지가 청구서 Agent의 하루입니다. 이어지는 장은 Agent끼리 서로를 찾고 부르는 방법([Agent Card와 Agent 간 통신](13-agent-card.md))과, 내 PC에서 직접 따라 하는 실습입니다.
