# Agent Tools

> 개발자 가이드 문서입니다. 규범은 [Agent Tools](../agent-tools.md), [Agent Identity](../identity-and-credentials.md), [Durable / HITL](../execution.md) 기술 표준 문서가 기준입니다.

{{journey:4}}

<div class="sofar" markdown="1">
**지금까지** 서연이 "청구서 INV-2048 요약해 줘"를 보냈습니다. 정문이 서연을 확인했고, 민준이 등록한 `invoice-summary`의 코드가 실행되기 시작했습니다.
</div>

## 장면

민준의 코드는 이제 ERP에서 청구서를 읽어 와야 합니다. 그런데 코드 어디에도 ERP 주소나 API 키가 없고, Manifest에 `tool-erp-read`라는 이름 하나만 적혀 있습니다. 잠시 뒤 서연이 "이 요약을 한빛상사 담당자에게 메일로 보내 줘"라고 합니다. 보내는 일은 다른 Agent인 `invoice-mailer`가 맡는데, 메일은 바로 나가지 않고 재무팀장 지훈의 승인을 기다립니다. 이 장에서는 읽기는 바로 되는데 보내기는 왜 멈추는지를 봅니다.

<div class="point" markdown="1">
**{{icon:bulb}} Agent Tools가 없다면** Agent마다 ERP 비밀번호를 들고 다니고, 메일은 누구의 확인도 없이 나갑니다.
</div>

## 무슨 일이 일어나나

<ol class="flow">
<li data-say="Agent 코드는 도구의 이름과 버전, 그리고 조회어만 넘깁니다. 주소나 비밀번호를 넣을 자리가 없습니다.">{{icon:runtime}}<b>1. 이름과 조회어를 넘긴다</b><span>Agent 코드<br><strong>주소·자격증명 없음</strong></span></li>
<li data-say="플랫폼이 이 도구가 Manifest에 적혀 있는지, 호출자에게 읽기 권한이 있는지를 봅니다.">{{icon:gateway}}<b>2. 써도 되는 도구인지 본다</b><span>Agent Gateway 도구 경로</span></li>
<li data-say="플랫폼이 이 호출 한 번에만 쓸 수 있는 출입증(lease)을 받아 ERP를 대신 부릅니다. 출입증은 Agent에게 가지 않습니다." class="hi">{{icon:key}}<b>3. 플랫폼이 ERP를 대신 부른다</b><span>Credential Broker의 lease</span></li>
<li data-say="ERP가 돌려준 내용만 Agent에게 돌아옵니다. 응답 어디에도 토큰이나 주소는 없습니다.">{{icon:tools}}<b>4. 결과만 돌아온다</b><span>청구서 내용</span></li>
<li data-say="메일 보내기처럼 바깥을 바꾸는 일은 사람이 승인할 때까지 실행이 멈춥니다.">{{icon:approve}}<b>5. 보내는 일은 승인까지 멈춘다</b><span>쓰기 도구 + 사람 승인</span></li>
</ol>

## 실물 보기

Agent가 도구를 부르는 코드 한 줄입니다.

<!-- kind: example -->

```python
found = ctx.call_tool("tool-erp-read", "1.0.0", {"query": "INV-2048"})
```

- `"tool-erp-read"`: 주소가 아니라 이름입니다. 주소와 자격증명은 플랫폼만 압니다.
- `"1.0.0"`: 도구에도 버전이 있어서, 도구가 바뀌어도 Agent가 모르는 사이에 동작이 달라지지 않습니다.
- `{"query": ...}`: 도구가 받겠다고 선언한 인자만 보낼 수 있으므로 주소를 넣을 자리가 없습니다.

플랫폼이 이 이름으로 찾아보는 도구 등록 정보(descriptor)입니다. 저장소의 `examples/fixtures/tool-descriptor.json`과 같은 필드입니다.

<!-- kind: example -->

```json
{
  "toolId": "tool-erp-read",
  "version": "1.0.0",
  "protocol": "rest-openapi",
  "effect": "read",
  "allowedScopes": ["tools.read"],
  "inputSchema": "…/tool-input.schema.json",
  "outputSchema": "…/tool-output.schema.json"
}
```

- `effect`: `read`는 읽기만 합니다. 메일 도구 `tool-mail-send`는 여기가 `write`이고, `write`인 도구는 승인이 있어야 실행됩니다.
- `allowedScopes`: 이 도구를 쓰려면 호출자에게 있어야 하는 권한입니다. 서연에게 `tools.read`가 있어서 조회가 됩니다.
- `inputSchema`, `outputSchema`: 들어가는 값과 나오는 값의 형식입니다. 형식에 맞지 않으면 ERP까지 가지 않습니다.

<details class="more" markdown="1"><summary>더 보기: 도구 경로가 실제로 받는 요청과 돌려주는 결과</summary>

Agent 코드의 한 줄이 도구 경로에 도착할 때는 플랫폼이 신원과 정책 정보를 덧붙인 모습입니다. 로컬 fixture `examples/fixtures/tool-invoke.json`의 발췌입니다.

<!-- kind: run boundary: local -->

```json
{
  "invocationId": "inv-demo",
  "toolId": "tool-search",
  "version": "0.1.0",
  "arguments": {"query": "hello"},
  "identity": {"tenantId": "tenant-demo", "mode": "delegated", "principalId": "user-demo", "scopes": ["tools.read", "agents.invoke", "models.invoke"]},
  "policy": {"decisionId": "policy-demo", "allowed": true, "allowedResources": ["tool-search", "model-self-hosted", "model-external"]},
  "idempotencyKey": "fixture-tool"
}
```

`identity`, `policy`, `idempotencyKey`는 Agent 코드가 적은 것이 아니라 Runtime이 붙인 것입니다. 결과(`tool-result.json`)에는 `status`와 `output`만 있고 자격증명은 없습니다.

```json
{"invocationId": "inv-demo", "toolId": "tool-search", "status": "succeeded", "output": {"content": "tool:hello"}}
```
</details>

## 직접 해 보기

<div class="sim" data-sim="tool-call"></div>

<ol class="mission">
<li>코드에서 Manifest에 없는 도구를 불러 보세요. 이것은 등록 실패인가요, 등록한 코드가 실행 중에 거절된 것인가요.</li>
<li>쓰기 도구에 다른 요청에서 받은 승인을 붙여 보세요. 앱은 무엇을 받나요. 승인이 아예 없을 때와 구별할 수 있나요.</li>
</ol>

## 잘못되면

**민준의 코드가 Manifest에 적지 않은 도구를 부르면** 서연의 요청은 실행 중에 403을 받습니다. 로컬 mock의 응답 본문에는 `Tool is not declared in the Agent Manifest`라고 적혀 있습니다. Manifest가 유효했고 등록도 됐고 코드까지 실행된 뒤에 나는 실패입니다. `capabilities.tools`에 도구 이름을 추가하고 새 버전으로 등록하면 고쳐집니다. 도구 목록을 아예 비운 Manifest는 여기까지 오지 못하고 등록 전 검증에서 멈춥니다([Agent Factory와 Manifest](05-agents-and-manifest.md)).

**승인이 붙지 않은 채 메일 도구를 부르면** 앱은 403 `Policy denied`를 받습니다. 평소에는 플랫폼이 승인까지 실행을 멈춰 주지만, 어떤 이유로든 승인 없는 호출이 도구 앞까지 오면 도구 경로가 마지막으로 거절합니다. 운영자가 도구 경로를 직접 보면 이유가 `Write tool requires approval`로 적혀 있습니다. 코드를 고쳐서 풀 일이 아니고, 승인자가 승인해야 풀립니다.

<details class="more" markdown="1"><summary>더 보기: 앱에서는 같아 보이는 거절 셋, 그리고 응답이 끊겼을 때</summary>

| 상황 | 앱이 받은 응답 | 도구 경로의 내부 진단 | 참조 구현 시나리오 |
|---|---|---|---|
| 등록되지 않은 도구를 부름 | 403 `Policy denied` | `Tool not approved` | S5 `tool-not-approved` |
| 승인 없이 쓰기 도구를 부름 | 403 `Policy denied` | `Write tool requires approval` | S6a `write-no-approval` |
| 만료됐거나 다른 요청의 승인을 붙임 | 403 `Policy denied` | `Approval is stale or not bound to this request` | S6a `write-approval-expired`, `write-approval-other-request` |
| 메일 서버의 응답이 오다가 끊김 | 실패 응답 | `unknown_outcome` | S6a `write-response-lost` |
| 다시 실행할 때 같은 키에 다른 인자가 실림 | 409 `CONFLICT` | 같은 키, 다른 내용 | S5 `tool-key-conflict` |

앞의 셋은 앱에서 모두 같은 `Policy denied`로 보입니다. 거절 이유를 바깥에 자세히 알려 주면 공격자에게도 알려 주는 셈이라 일부러 구분하지 않습니다. 어느 경우인지는 호출 번호(`invocationId`)로 운영자에게 묻습니다.

`unknown_outcome`은 메일이 나갔는지 알 수 없는 상태입니다. 자동으로 다시 보내면 두 번 나갈 수 있으므로 다시 보내지 않고 메일 서버의 기록과 대조합니다. 도구 호출의 멱등성 키는 Agent 코드가 아니라 Runtime이 붙입니다.

Agent가 주소를 직접 넘기는 길은 계약에 없습니다. 그런 길이 있다면 문서에 숨은 지시문이 Agent를 시켜 `http://10.0.0.5/admin` 같은 사내망 주소를 찔러 볼 수 있기 때문입니다.
</details>

## 내가 할 일

1. 쓸 도구의 ID와 버전을 확인합니다.
2. Manifest의 `capabilities.tools`에 그 ID를 적고, `identity.requiredScopes`에 도구가 요구하는 scope를 적습니다.
3. 코드에서 `ctx.call_tool(도구 ID, 버전, 인자)`로 부릅니다. 주소와 키는 넣지 않습니다.
4. 로컬에서 실행해 보고 적합성 검사의 C8(선언하지 않은 도구, 자격증명 노출)을 확인합니다.
5. 쓰기 도구가 필요하면 읽기 Agent에 덧붙이지 말고 별도 Agent로 나눕니다.

**내 PC에서 해 보기** 저장소 루트에서 실행합니다. 로컬에서는 이야기 속 이름 대신 아래 대역을 씁니다.

| 이야기 | 내 PC |
|---|---|
| `tool-erp-read` `1.0.0` | `tool-search` `0.1.0` |
| 테넌트 `finance` | `tenant-demo` |
| 서연의 토큰 | `Bearer mock-user` |

```bash
python scripts/agentctl.py run --port 8765 --agents-dir examples/agents
```

다른 터미널에서 요청을 보냅니다.

```bash
curl -s -X POST http://127.0.0.1:8765/v1/agents/invoice-summary/invocations \
  -H "Authorization: Bearer mock-user" -H "Idempotency-Key: demo-a1" -H "Content-Type: application/json" \
  -d '{"input":{"type":"message","content":"청구서 INV-2048 요약해 줘"},"context":{"tenantId":"tenant-demo","dataClassification":"confidential"},"execution":{"mode":"sync","timeoutMs":30000}}'
```

<!-- kind: run boundary: local -->

```json
{"invocationId":"inv-9946215c02f347bd8ba5de71ca079905","agentVersion":"0.1.0","status":"succeeded","output":{"type":"message","content":"mock:Summarize the invoice: tool:청구서 INV-2048 요약해 줘"},"traceparent":"00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01","routeDecisionId":"route-self-hosted","usage":{"inputTokens":7,"outputTokens":7}}
```

`output.content` 안의 `tool:청구서 INV-2048 요약해 줘`가 도구가 돌려준 값입니다. 로컬 도구는 받은 조회어 앞에 `tool:`을, 로컬 모델은 받은 글 앞에 `mock:`을 붙여 돌려주는 대역이라 실제 요약은 나오지 않습니다. 호출 번호와 추적 번호는 실행할 때마다 달라집니다. 쓰기와 승인은 `make scenarios`의 S5, S6a 줄에서 확인합니다(PostgreSQL이 필요합니다. [로컬 환경 구성](07-hands-on.md)).

<div class="scope" markdown="1">
**제공 범위 (v0.1)**

| 항목 | 등급 | 확인하는 곳 |
|---|---|---|
| 읽기 도구 호출, 선언하지 않은 도구 거절 | 실행 | 로컬 mock, 적합성 C8 |
| 쓰기 도구의 승인 검증, `unknown_outcome` | 실행 | 참조 구현 S5, S6a |
| 승인을 기다리며 멈추는 실행(`waiting_approval`) | 계약 | `contracts/execution.schema.json` |
| MCP 서버 연결, 새 도구 등록 절차 | 정의 | [Agent Tools](../agent-tools.md) |
</div>

## 규칙으로 정리

- Agent는 도구의 ID, 버전, 인자만 넘깁니다. 주소와 자격증명은 넘길 수 없습니다(MUST NOT). 장면 ④
- Manifest의 `capabilities.tools`에 없는 도구 호출은 거절합니다(MUST). 장면 ④
- 쓰기 도구는 그 요청에 묶인 유효한 승인이 있어야 실행합니다(MUST). 장면 ④ 뒷부분
- 쓰기의 성공 여부를 알 수 없으면 자동으로 다시 실행하지 않고 `unknown_outcome`으로 기록합니다(MUST).
- MCP 서버는 도구를 제공하는 방식 가운데 하나이며 같은 도구 경로를 지납니다. 토큰을 그대로 넘겨주는 방식(token passthrough)은 쓰지 않습니다(MUST NOT).

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Tools](09-glossary.md#term-agent-tools) [도구 경로](09-glossary.md#term-tool-gateway) [Credential Broker](09-glossary.md#term-credential-broker) [Lease](09-glossary.md#term-lease) [scope](09-glossary.md#term-scope) [HITL](09-glossary.md#term-hitl) [unknown_outcome](09-glossary.md#term-unknown) [MCP](09-glossary.md#term-mcp)
</div>

## 한 문장으로

Agent는 도구의 이름만 알고, 주소와 비밀번호는 플랫폼이 쥐고 대신 불러 줍니다.

<div class="check" markdown="1">
**{{icon:question}} 이해 점검**

<details markdown="1"><summary>Q1. 민준의 코드가 Manifest에 적지 않은 tool-mail-send를 부릅니다. 등록은 통과했습니다. 서연이 요청을 보내면 어떻게 되나요?</summary>
코드는 실행되지만 그 도구를 부르는 순간 403으로 거절됩니다. 등록에 실패한 것이 아니라 실행 중에 거절된 것이므로, Manifest에 도구를 추가해 새 버전으로 등록해야 합니다.
</details>

<details markdown="1"><summary>Q2. 서연의 앱이 403 Policy denied를 받았습니다. 승인이 없어서인지 승인이 만료돼서인지 앱이 구별할 수 있나요?</summary>
앱이 받는 응답이 같아서 구별할 수 없습니다. 호출 번호를 운영자에게 전달하면 도구 경로의 기록에서 이유를 확인해 줍니다.
</details>

<details markdown="1"><summary>Q3. 메일 도구를 부른 뒤 응답이 끊겼습니다. Agent가 한 번 더 보내면 안 되는 이유는 무엇인가요?</summary>
메일이 이미 나갔을 수 있기 때문입니다. 성공했는지 알 수 없는 쓰기는 다시 실행하지 않고 대상 시스템의 기록과 대조해 확정합니다.
</details>
</div>

다음 장면은 ⑤입니다. 같은 Agent인데 왜 서연이 부르면 되고 인턴 하준이 부르면 안 되는지를 봅니다.
